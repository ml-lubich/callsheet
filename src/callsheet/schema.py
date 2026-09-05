"""Validation for content.json — the JSON an analysis agent hands back.

Every failure names the field that caused it, because the thing being validated
was written by a language model and the error is going straight back to one.
"""

from __future__ import annotations

from .parse import seconds_to_ts

STRENGTHS = ("strong", "medium", "weak")

# section -> (required keys, optional keys). Every row may also carry ts/s.
ROWS = {
    "threads": (("name", "what", "why_it_matters"), ()),
    "evidence": (("ts", "s", "claim", "evidence", "strength"), ()),
    "signals": (("ts", "s", "signal"), ()),
    "numbers": (("ts", "s", "value", "means"), ()),
    "quotes": (("ts", "s", "speaker", "text"), ()),
    "tensions": (("ts", "s", "note"), ()),
    "diarization": (("ts", "s", "why"), ()),
    "next_steps": (("ts", "s", "commitment"), ()),
}


class SchemaError(ValueError):
    """content.json does not match the contract the page consumes."""


def validate(content) -> None:
    """Raise :class:`SchemaError` listing every problem found, or return None."""
    bad: list[str] = []
    if not isinstance(content, dict):
        raise SchemaError(f"content must be a JSON object, got {type(content).__name__}")

    for key in ("meta", "abstract", "acts"):
        if key not in content:
            bad.append(f"{key}: required key is missing")

    keys = _check_meta(content.get("meta"), bad)
    _check_acts(content.get("acts"), bad)

    for section, (required, _) in ROWS.items():
        rows = content.get(section)
        if rows is None:
            continue
        if not isinstance(rows, list):
            bad.append(f"{section}: must be a list")
            continue
        for i, row in enumerate(rows):
            where = f"{section}[{i}]"
            if not isinstance(row, dict):
                bad.append(f"{where}: must be an object")
                continue
            for f in required:
                if not str(row.get(f, "")).strip():
                    bad.append(f"{where}.{f}: required field is missing or empty")
            _check_stamp(where, row, bad)
            if section == "evidence" and row.get("strength") not in STRENGTHS:
                bad.append(
                    f"{where}.strength: {row.get('strength')!r} is not one of "
                    + ", ".join(STRENGTHS)
                )
            if section == "quotes" and keys and row.get("speaker") not in keys:
                if row.get("speaker"):
                    bad.append(
                        f"{where}.speaker: {row['speaker']!r} is not a participant key "
                        f"({', '.join(keys)})"
                    )
            if section == "threads":
                for j, mark in enumerate(row.get("marks") or []):
                    _check_stamp(f"{where}.marks[{j}]", mark, bad)

    if bad:
        raise SchemaError("content.json is not valid:\n  - " + "\n  - ".join(bad))


def _check_meta(meta, bad: list[str]) -> list[str]:
    if meta is None:
        return []
    if not isinstance(meta, dict):
        bad.append("meta: must be an object")
        return []
    for f in ("title", "participants"):
        if not meta.get(f):
            bad.append(f"meta.{f}: required field is missing or empty")
    keys = []
    for i, p in enumerate(meta.get("participants") or []):
        if not isinstance(p, dict):
            bad.append(f"meta.participants[{i}]: must be an object")
            continue
        for f in ("key", "name"):
            if not str(p.get(f, "")).strip():
                bad.append(f"meta.participants[{i}].{f}: required field is missing or empty")
        if p.get("key"):
            keys.append(p["key"])
    return keys


def _check_acts(acts, bad: list[str]) -> None:
    if acts is None:
        return
    if not isinstance(acts, list) or not acts:
        bad.append("acts: must be a non-empty list")
        return
    prev = 0
    for i, a in enumerate(acts):
        where = f"acts[{i}]"
        if not isinstance(a, dict):
            bad.append(f"{where}: must be an object")
            return
        for f in ("n", "title", "span", "start_s", "end_s", "summary"):
            if a.get(f) in (None, ""):
                bad.append(f"{where}.{f}: required field is missing or empty")
        start, end = a.get("start_s"), a.get("end_s")
        if not isinstance(start, int) or not isinstance(end, int):
            continue
        if end <= start:
            bad.append(f"{where}: end_s {end} is not after start_s {start}")
        if start > prev:
            bad.append(
                f"{where}: gap in the timeline — act starts at {start}s but the previous "
                f"act ended at {prev}s"
            )
        elif start < prev:
            bad.append(
                f"{where}: acts overlap — act starts at {start}s but the previous act "
                f"ran to {prev}s"
            )
        want = f"{seconds_to_ts(start)}-{seconds_to_ts(end)}"
        if a.get("span") != want:
            bad.append(f"{where}.span: {a.get('span')!r} disagrees with start_s/end_s ({want})")
        if a.get("turning_point"):
            _check_stamp(f"{where}.turning_point", a["turning_point"], bad)
            if not str(a["turning_point"].get("text", "")).strip():
                bad.append(f"{where}.turning_point.text: required field is missing or empty")
        prev = end


def _check_stamp(where: str, row, bad: list[str]) -> None:
    if not isinstance(row, dict) or "ts" not in row or "s" not in row:
        return
    if not isinstance(row["s"], int):
        bad.append(f"{where}.s: must be an integer number of seconds")
        return
    want = seconds_to_ts(row["s"])
    if row["ts"] != want:
        bad.append(f"{where}: ts {row['ts']!r} disagrees with s={row['s']} (which is {want})")
