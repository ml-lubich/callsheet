"""callsheet command line: transcribe / parse / chunk / build / lint-diagrams / seal / compare."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .build import BuildError, build, external_refs, template_path
from .diagrams import (
    check_svg_fragment,
    extract_timestamps,
    figure_ids,
    unresolved_timestamps,
)
from .holdout import HoldoutError, ngram_overlap, seal, strip_html, verify
from .parse import ParseError, chunks, metrics, parse_transcript, transcript_from_turns
from .schema import SchemaError
from .transcribe import DEFAULT_BINARY, TranscribeError, transcribe

ERRORS = (ParseError, SchemaError, BuildError, HoldoutError, TranscribeError, OSError)


def _load(path) -> object:
    return json.loads(Path(path).read_text())


def _dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False))


def cmd_transcribe(a) -> int:
    out = transcribe(a.media, a.model, a.out, threads=a.threads, fmt=a.format, binary=a.binary)
    print(f"wrote {out}")
    return 0


def cmd_parse(a) -> int:
    t = parse_transcript(Path(a.transcript).read_text())
    work = Path(a.out)
    _dump(work / "turns.json", t.turns)
    _dump(work / "metrics.json", metrics(t))
    est = " (timing estimated)" if t.estimated_timing else ""
    print(f"{len(t.turns)} turns, {t.duration_s}s, {len(t.speakers)} speakers{est} -> {work}")
    return 0


def cmd_chunk(a) -> int:
    duration = _load(a.metrics)["duration_s"] if a.metrics else None
    t = transcript_from_turns(_load(a.turns), duration)
    work = Path(a.out)
    work.mkdir(parents=True, exist_ok=True)
    for c in chunks(t, a.n):
        path = work / f"chunk{c.index}.txt"
        path.write_text(c.text)
        print(f"{path}  {c.start_s}-{c.end_s}s  {len(c.turns)} turns")
    return 0


def cmd_build(a) -> int:
    diagrams = Path(a.diagrams).read_text() if a.diagrams else None
    page = build(
        Path(a.template or template_path()).read_text(),
        _load(a.content),
        _load(a.turns),
        _load(a.metrics),
        diagrams,
    )
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    refs = external_refs(page)
    print(f"wrote {out} — {len(page) / 1024:.0f} KB, {len(refs) or 'no'} external requests")
    return 1 if refs else 0


def cmd_lint_diagrams(a) -> int:
    text = Path(a.fragment).read_text()
    problems = check_svg_fragment(text)
    unresolved = unresolved_timestamps(text, _load(a.turns)) if a.turns else []
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    for ts in unresolved:
        print(f"  unresolved-timestamp: {ts} starts no turn in the transcript", file=sys.stderr)
    if problems or unresolved:
        n = len(problems) + len(unresolved)
        print(f"callsheet: {n} problem(s) in {a.fragment}", file=sys.stderr)
        return 1
    ids = figure_ids(text)
    checked = " checked" if a.turns else ""
    print(
        f"{a.fragment}: {len(ids)} figures, "
        f"{len(extract_timestamps(text))} timestamps{checked} — {', '.join(ids)}"
    )
    return 0


def cmd_seal(a) -> int:
    digests = seal(a.directory)
    print(f"sealed {len(digests)} files read-only under {a.directory}")
    return 0


def cmd_compare(a) -> int:
    mine = strip_html(Path(a.page).read_text(errors="ignore"))
    directory = Path(a.directory)
    verify(directory)
    for ref in sorted(p for p in directory.rglob("*") if p.is_file()):
        theirs = strip_html(ref.read_text(errors="ignore"))
        shares = "  ".join(
            f"{n}-gram {100 * ngram_overlap(mine, theirs, n):.1f}%" for n in (6, 10)
        )
        print(f"{ref.relative_to(directory)}: {shares}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="callsheet", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("transcribe", help="run whisper.cpp locally over a recording")
    t.add_argument("media")
    t.add_argument("-m", "--model", required=True, help="path to a ggml whisper model")
    t.add_argument("-o", "--out", required=True, help="output path without extension")
    t.add_argument("-t", "--threads", type=int, default=8)
    t.add_argument("--format", default="txt", help="txt, vtt, srt, json or csv")
    t.add_argument("--binary", default=DEFAULT_BINARY)
    t.set_defaults(fn=cmd_transcribe)

    q = sub.add_parser("parse", help="transcript -> turns.json and metrics.json")
    q.add_argument("transcript")
    q.add_argument("-o", "--out", default="work")
    q.set_defaults(fn=cmd_parse)

    c = sub.add_parser("chunk", help="turns.json -> chunk1.txt … chunkN.txt")
    c.add_argument("turns")
    c.add_argument("-n", type=int, default=4, help="number of segment analysts")
    c.add_argument("-o", "--out", default="work")
    c.add_argument("--metrics", help="metrics.json, for the true duration")
    c.set_defaults(fn=cmd_chunk)

    b = sub.add_parser("build", help="data + template -> one self-contained page")
    b.add_argument("--content", required=True)
    b.add_argument("--turns", required=True)
    b.add_argument("--metrics", required=True)
    b.add_argument("--diagrams", help="optional inline SVG fragment")
    b.add_argument("--template", help="defaults to the packaged template")
    b.add_argument("-o", "--out", default="out/index.html")
    b.set_defaults(fn=cmd_build)

    d = sub.add_parser("lint-diagrams", help="house-style checks on an inline SVG fragment")
    d.add_argument("fragment")
    d.add_argument("--turns", help="turns.json, to prove every cited timestamp was said")
    d.set_defaults(fn=cmd_lint_diagrams)

    s = sub.add_parser("seal", help="make a reference answer read-only and hash it")
    s.add_argument("directory")
    s.set_defaults(fn=cmd_seal)

    m = sub.add_parser("compare", help="n-gram overlap between the page and sealed references")
    m.add_argument("page")
    m.add_argument("directory")
    m.set_defaults(fn=cmd_compare)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except ERRORS as e:
        print(f"callsheet: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
