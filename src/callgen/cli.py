"""callgen command line: transcribe / parse / chunk / build / lint-diagrams / lexicon /
seal / compare."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .build import BuildError, build, build_web, external_refs, template_path
from .diagrams import (
    check_svg_fragment,
    extract_timestamps,
    figure_ids,
    unresolved_timestamps,
)
from .holdout import HoldoutError, ngram_overlap, seal, strip_html, verify
from .lexicon import (
    LexiconError,
    apply_corrections,
    build_profile,
    flag_unlike_speaker,
    load_profile,
    suggest_corrections,
)
from .modes import ModeError, all_modes, layout_violations, prose_violations
from .parse import ParseError, chunks, metrics, parse_transcript, transcript_from_turns
from .schema import SchemaError
from .transcribe import DEFAULT_BINARY, TranscribeError, transcribe

ERRORS = (
    ParseError,
    SchemaError,
    BuildError,
    HoldoutError,
    TranscribeError,
    LexiconError,
    ModeError,
    OSError,
)


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
    if a.web:
        out = build_web(Path(a.web), Path(a.out))
        size = out.stat().st_size / 1024
        print(f"wrote {out} — {size:.0f} KB, one file, no external requests")
        return 0
    missing = [f"--{f}" for f in ("content", "turns", "metrics") if not getattr(a, f)]
    if missing:
        raise BuildError(f"build needs {', '.join(missing)} (or --web WORKDIR)")
    diagrams = Path(a.diagrams).read_text() if a.diagrams else None
    page = build(
        Path(a.template or template_path()).read_text(),
        _load(a.content),
        _load(a.turns),
        _load(a.metrics),
        diagrams,
        mode=a.mode,
    )
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    refs = external_refs(page)
    print(f"wrote {out} — {len(page) / 1024:.0f} KB, {len(refs) or 'no'} external requests")
    return 1 if refs else 0


def cmd_modes(a) -> int:
    for name, mode in all_modes().items():
        print(f"{name:<14} {mode.summary}")
    return 0


def cmd_lint_prose(a) -> int:
    content = _load(a.content)
    bad = prose_violations(content, a.mode) + layout_violations(content, a.mode)
    for line in bad:
        print(f"  {line}", file=sys.stderr)
    if bad:
        print(f"callgen: {len(bad)} problem(s) in {a.content} for mode {a.mode}", file=sys.stderr)
        return 1
    print(f"{a.content}: within every {a.mode} budget")
    return 0


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
        print(f"callgen: {n} problem(s) in {a.fragment}", file=sys.stderr)
        return 1
    ids = figure_ids(text)
    checked = " checked" if a.turns else ""
    print(
        f"{a.fragment}: {len(ids)} figures, "
        f"{len(extract_timestamps(text))} timestamps{checked} — {', '.join(ids)}"
    )
    return 0


def _documents(sources) -> list[tuple[Path, str]]:
    """Files, globs and directories in, readable text out. Binaries are skipped."""
    paths: list[Path] = []
    for source in sources:
        if any(c in source for c in "*?["):
            paths += [Path(p) for p in sorted(glob.glob(source, recursive=True))]
        elif Path(source).is_dir():
            paths += sorted(p for p in Path(source).rglob("*") if p.is_file())
        else:
            paths.append(Path(source))
    documents = []
    for path in paths:
        try:
            text = path.read_text()
        except (UnicodeDecodeError, ValueError):
            continue
        if "\x00" not in text and text.strip():
            documents.append((path, text))
    return documents


def cmd_lexicon_build(a) -> int:
    documents = _documents(a.sources)
    if not documents:
        raise LexiconError(f"no readable documents in {' '.join(a.sources)}")
    seeds = []
    if a.terms:
        seeds = [line.strip() for line in Path(a.terms).read_text().splitlines() if line.strip()]
    profile = build_profile([text for _, text in documents], name=a.name, terms=seeds)
    _dump(Path(a.out), profile)
    print(
        f"{len(documents)} documents, {len(profile['terms'])} terms, "
        f"{len(profile['ngrams'])} phrasings -> {a.out}"
    )
    return 0


def _correction_lines(corrections) -> list[str]:
    return [
        f"  {c.start_char}-{c.end_char}  {c.span!r} -> {c.suggestion}  {c.score:.2f}"
        f"{f'  x{c.count}' if c.count > 1 else ''}  {c.reason}"
        for c in corrections
    ]


def _flag_lines(flags) -> list[str]:
    return [
        f"  {f.start_char}-{f.end_char}  {f.span!r}  {f.confidence:.2f}  {f.why}" for f in flags
    ]


def cmd_lexicon_check(a) -> int:
    text = Path(a.transcript).read_text()
    profile = load_profile(a.profile)
    corrections = suggest_corrections(text, profile, threshold=a.threshold)
    flags = flag_unlike_speaker(text, profile)
    if not corrections and not flags:
        print(f"{a.transcript}: no corrections, no suspicion flags against {profile['name']}")
        return 0
    occurrences = sum(c.count for c in corrections)
    print(
        f"{a.transcript}: {len(corrections)} correction(s) over {occurrences} occurrence(s), "
        f"{len(flags)} suspicion flag(s)"
    )
    shown = corrections[: a.max] if a.max else corrections
    for line in _correction_lines(shown) + _flag_lines(flags):
        print(line)
    if len(shown) < len(corrections):
        print(f"  … {len(corrections) - len(shown)} more withheld; raise --max to see them")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(_review(a.transcript, profile, corrections, flags))
        print(f"review written to {a.out}")
    return 1


def _review(name, profile, corrections, flags) -> str:
    out = [f"# lexicon review — {name}", "", f"Profile: `{profile['name']}`", ""]
    out += ["## Proposed corrections", ""]
    out += ["_none_"] if not corrections else [
        "| chars | heard | proposed | score | why |",
        "|---|---|---|---|---|",
        *(
            f"| {c.start_char}-{c.end_char} | `{c.span}` | **{c.suggestion}** | "
            f"{c.score:.2f} | {c.reason} |"
            for c in corrections
        ),
    ]
    out += ["", "## Unlike the speaker", ""]
    out += ["_none_"] if not flags else [
        f"- `{f.start_char}-{f.end_char}` ({f.confidence:.2f}) {f.span}\n  - {f.why}"
        for f in flags
    ]
    out += ["", "Nothing here is applied automatically. Accept a correction by hand, or run",
            "`callgen lexicon apply … --write` once you have read the list.", ""]
    return "\n".join(out)


def cmd_lexicon_apply(a) -> int:
    source = Path(a.transcript)
    text = source.read_text()
    profile = load_profile(a.profile)
    corrections = suggest_corrections(text, profile, threshold=a.threshold)
    for line in _correction_lines(corrections):
        print(line)
    if not a.write:
        print(f"{len(corrections)} correction(s) above {a.threshold}; pass --write to apply")
        return 1
    out = Path(a.out or source)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(apply_corrections(text, corrections))
    audit = Path(str(out) + ".corrections.json")
    _dump(
        audit,
        {
            "profile": profile["name"],
            "transcript": str(source),
            "threshold": a.threshold,
            "corrections": [asdict(c) for c in corrections],
        },
    )
    print(f"applied {len(corrections)} correction(s) to {out}; audit at {audit}")
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
    p = argparse.ArgumentParser(prog="callgen", description=__doc__)
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
    b.add_argument("--content")
    b.add_argument("--turns")
    b.add_argument("--metrics")
    b.add_argument(
        "--web",
        metavar="WORKDIR",
        help="build the React front end over WORKDIR instead of the vanilla template",
    )
    b.add_argument("--diagrams", help="optional inline SVG fragment")
    b.add_argument("--template", help="defaults to the packaged template")
    b.add_argument("--mode", default="professional",
                   help="output mode; see `callgen modes`")
    b.add_argument("-o", "--out", default="out/index.html")
    b.set_defaults(fn=cmd_build)

    n = sub.add_parser("modes", help="list the output modes a build can be rendered in")
    n.set_defaults(fn=cmd_modes)

    r = sub.add_parser("lint-prose", help="word caps and wall-of-text checks on content.json")
    r.add_argument("content")
    r.add_argument("--mode", default="professional")
    r.set_defaults(fn=cmd_lint_prose)

    d = sub.add_parser("lint-diagrams", help="house-style checks on an inline SVG fragment")
    d.add_argument("fragment")
    d.add_argument("--turns", help="turns.json, to prove every cited timestamp was said")
    d.set_defaults(fn=cmd_lint_diagrams)

    x = sub.add_parser("lexicon", help="build a speaker profile and check a transcript against it")
    xs = x.add_subparsers(dest="lexicon_cmd", required=True)

    xb = xs.add_parser("build", help="a person's own writing -> a profile of their vocabulary")
    xb.add_argument("--from", dest="sources", nargs="+", required=True,
                    help="files, globs or directories of that person's writing")
    xb.add_argument("--name", required=True)
    xb.add_argument("--terms", help="extra vocabulary, one term per line")
    xb.add_argument("-o", "--out", default="profile.json")
    xb.set_defaults(fn=cmd_lexicon_build)

    xc = xs.add_parser("check", help="propose corrections and flag phrasing unlike the speaker")
    xc.add_argument("transcript")
    xc.add_argument("--profile", required=True)
    xc.add_argument("--threshold", type=float, default=0.72)
    xc.add_argument("--max", type=int, default=40, help="rows to print; 0 for all")
    xc.add_argument("-o", "--out", help="write a review file")
    xc.set_defaults(fn=cmd_lexicon_check)

    xa = xs.add_parser("apply", help="rewrite a transcript, leaving an audit beside it")
    xa.add_argument("transcript")
    xa.add_argument("--profile", required=True)
    xa.add_argument("--threshold", type=float, default=0.72)
    xa.add_argument("--write", action="store_true", help="required; without it nothing is written")
    xa.add_argument("-o", "--out", help="defaults to rewriting the transcript in place")
    xa.set_defaults(fn=cmd_lexicon_apply)

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
        print(f"callgen: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
