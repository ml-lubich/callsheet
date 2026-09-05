"""Transcript text -> speaker turns, call metrics, and equal-time chunks.

Four input shapes are recognised, all by inspection:

    [HH:MM:SS] Speaker:      block, text on following indented lines
    [MM:SS] Speaker: text    one line per turn (minutes may exceed 59)
    WEBVTT                   cues, speaker from ``<v Name>`` or a ``Name:`` prefix
    Speaker: text            no timing at all; turn times are estimated

Anything that looks like a timestamp header but is not one raises, rather than
being folded into the previous turn where a dropped turn would go unnoticed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

WORDS_PER_MINUTE = 150  # ponytail: flat rate for untimed transcripts; good enough to order turns

_STAMP = r"\d{1,3}:\d{2}(?::\d{2})?(?:[.,]\d+)?"
_HEAD = re.compile(rf"^\[\s*({_STAMP})\s*\]\s*(?:([^:\[\]]{{1,80}}?)\s*:)?\s*(.*)$")
_CUE = re.compile(rf"^({_STAMP})\s*-->\s*({_STAMP})")
_VOICE = re.compile(r"^<v\s+([^>]+)>\s*(.*)$")
_NAMED = re.compile(r"^([^:]{1,80}):\s+(.*)$")


class ParseError(ValueError):
    """The transcript could not be read without losing a turn."""


@dataclass
class Transcript:
    turns: list[dict]
    speakers: dict[str, str]
    duration_s: int = 0
    header: str = ""
    estimated_timing: bool = False


@dataclass
class Chunk:
    index: int
    start_s: int
    end_s: int
    turns: list[dict] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "".join(
            f"[{t['ts']}] {t.get('name', t['spk'])}:\n    {t['t']}\n\n" for t in self.turns
        )


def ts_to_seconds(ts: str) -> int:
    parts = ts.replace(",", ".").split(":")
    if len(parts) == 2:
        h, m, s = 0, parts[0], parts[1]
    elif len(parts) == 3:
        h, m, s = parts
    else:
        raise ParseError(f"not a timestamp: {ts!r}")
    return int(h) * 3600 + int(m) * 60 + int(float(s))


def seconds_to_ts(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec // 60 % 60:02d}:{sec % 60:02d}"


def parse_transcript(text: str) -> Transcript:
    """Read any supported transcript shape into a :class:`Transcript`."""
    if text.lstrip().startswith("WEBVTT"):
        raw, header, estimated = _parse_vtt(text)
    elif re.search(rf"^\[\s*{_STAMP}\s*\]", text, re.M):
        raw, header, estimated = _parse_bracketed(text)
    else:
        raw, header, estimated = _parse_plain(text)

    if not raw:
        raise ParseError("no turns found in the transcript")
    return _finish(raw, header, estimated)


def _parse_bracketed(text: str) -> tuple[list[dict], str, bool]:
    turns: list[dict] = []
    header: list[str] = []
    para: list[str] = []
    last_s = -1

    def flush():
        if turns and para:
            turns[-1]["parts"].append(" ".join(para))
        para.clear()

    for n, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("["):
            m = _HEAD.match(stripped)
            if not m:
                raise ParseError(f"line {n}: malformed timestamp header: {stripped!r}")
            flush()
            sec = ts_to_seconds(m.group(1))
            if sec < last_s:
                raise ParseError(
                    f"line {n}: timestamp {m.group(1)} goes backwards "
                    f"(previous turn was at {seconds_to_ts(last_s)})"
                )
            last_s = sec
            turns.append({"s": sec, "name": (m.group(2) or "").strip(), "parts": []})
            if m.group(3).strip():
                turns[-1]["parts"].append(m.group(3).strip())
            continue
        if not turns:
            header.append(stripped)
            continue
        para.append(stripped)
    flush()
    return turns, "\n".join(header), False


def _parse_vtt(text: str) -> tuple[list[dict], str, bool]:
    turns: list[dict] = []
    cue: dict | None = None
    for line in text.splitlines():
        stripped = line.strip()
        m = _CUE.match(stripped)
        if m:
            cue = {"s": ts_to_seconds(m.group(1)), "end": ts_to_seconds(m.group(2)), "parts": []}
            turns.append(cue)
            continue
        if cue is None or not stripped or stripped.isdigit():
            continue
        v = _VOICE.match(stripped)
        if v:
            cue["name"] = v.group(1).strip()
            stripped = v.group(2).strip()
        elif "name" not in cue:
            named = _NAMED.match(stripped)
            if named:
                cue["name"] = named.group(1).strip()
                stripped = named.group(2).strip()
        if stripped:
            cue["parts"].append(stripped)
    for t in turns:
        t.setdefault("name", "")
    return turns, "", False


def _parse_plain(text: str) -> tuple[list[dict], str, bool]:
    turns: list[dict] = []
    header: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = _NAMED.match(stripped)
        if m:
            turns.append({"s": 0, "name": m.group(1).strip(), "parts": [m.group(2).strip()]})
        elif turns:
            turns[-1]["parts"].append(stripped)
        else:
            header.append(stripped)
    at = 0.0
    for t in turns:
        t["s"] = int(at)
        at += len(" ".join(t["parts"]).split()) / WORDS_PER_MINUTE * 60
    if turns:
        turns[-1]["end"] = int(at)
    return turns, "\n".join(header), True


def _finish(raw: list[dict], header: str, estimated: bool) -> Transcript:
    named = any(t["name"] for t in raw)
    merged: list[dict] = []
    for t in raw:
        if named and merged and merged[-1]["name"] == t["name"]:
            merged[-1]["parts"] += t["parts"]
            merged[-1]["end"] = t.get("end", merged[-1].get("end"))
            continue
        merged.append(dict(t))

    keys = _assign_keys([t["name"] for t in merged])
    turns = []
    for i, t in enumerate(merged):
        body = " ".join(p for p in t["parts"] if p)
        turns.append(
            {
                "i": i,
                "ts": seconds_to_ts(t["s"]),
                "s": t["s"],
                "spk": keys[t["name"]],
                "name": t["name"] or "Speaker",
                "w": len(body.split()),
                "t": body,
            }
        )
    last = merged[-1]
    duration = int(last.get("end") or last["s"])
    speakers = {keys[name]: (name or "Speaker") for name in keys}
    return Transcript(turns, speakers, duration, header, estimated)


def _assign_keys(names: list[str]) -> dict[str, str]:
    keys: dict[str, str] = {}
    for name in names:
        if name in keys:
            continue
        initial = next((c for c in name.upper() if c.isalpha()), "")
        keys[name] = initial if initial and initial not in keys.values() else f"S{len(keys) + 1}"
    return keys


def metrics(t: Transcript) -> dict:
    """Per-speaker totals plus the full timeline the strip chart is drawn from."""
    speakers: dict[str, dict[str, int]] = {}
    timeline = []
    for turn in t.turns:
        name = t.speakers.get(turn["spk"], turn["spk"])
        row = speakers.setdefault(name, {"words": 0, "turns": 0})
        row["words"] += turn["w"]
        row["turns"] += 1
        timeline.append({"ts": turn["ts"], "s": turn["s"], "spk": name, "words": turn["w"]})
    return {
        "duration_s": t.duration_s,
        "turns": len(t.turns),
        "estimated_timing": t.estimated_timing,
        "speakers": speakers,
        "timeline": timeline,
    }


def chunks(t: Transcript, n: int) -> list[Chunk]:
    """Split the call into ``n`` slices that tile the whole duration exactly once.

    Equal time slices by default. If that would starve a slice of every turn, the
    boundaries fall back to equal turn counts — an empty slice is an analyst with
    nothing to read.
    """
    if n < 1:
        raise ValueError("chunk count must be at least 1")
    if not t.turns:
        raise ValueError("nothing to chunk: the transcript has no turns")
    n = min(n, len(t.turns))
    dur = t.duration_s

    out = _slice_by_time(t.turns, n, dur)
    if any(not c.turns for c in out):
        out = _slice_by_count(t.turns, n, dur)
    return out


def _slice_by_time(turns: list[dict], n: int, dur: int) -> list[Chunk]:
    edges = [round(dur * i / n) for i in range(n + 1)]
    edges[0], edges[-1] = 0, dur
    out = [Chunk(i + 1, edges[i], edges[i + 1]) for i in range(n)]
    for turn in turns:
        slot = min(n - 1, max(0, sum(1 for e in edges[1:-1] if turn["s"] >= e)))
        out[slot].turns.append(turn)
    return out


def _slice_by_count(turns: list[dict], n: int, dur: int) -> list[Chunk]:
    out = []
    for i in range(n):
        lo = round(len(turns) * i / n)
        hi = round(len(turns) * (i + 1) / n)
        out.append(
            Chunk(
                i + 1,
                0 if i == 0 else turns[lo]["s"],
                dur if i == n - 1 else turns[hi]["s"],
                turns[lo:hi],
            )
        )
    return out


def transcript_from_turns(turns: list[dict], duration_s: int | None = None) -> Transcript:
    """Rebuild a :class:`Transcript` from a turns.json that was written earlier."""
    if not turns:
        raise ParseError("turns.json is empty")
    speakers = {t["spk"]: t.get("name", t["spk"]) for t in turns}
    return Transcript(turns, speakers, duration_s if duration_s is not None else turns[-1]["s"])
