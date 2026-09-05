"""Keep a reference answer sealed while the artifact is written, then measure overlap.

The point is a claim you can check: the sealed material was read-only and unread
during the build, so any resemblance in the finished page is convergence rather
than copying.
"""

from __future__ import annotations

import collections
import hashlib
import html as _html
import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path

READ_ONLY = 0o444
_GUARDED: list[str] = []
_HOOK_INSTALLED = False


class HoldoutError(RuntimeError):
    """A sealed file was missing, altered, or read when it should not have been."""


def manifest_path(directory: Path) -> Path:
    """Where the hashes live — beside the sealed directory, never inside it."""
    directory = Path(directory)
    return directory.parent / (directory.name + ".sha256")


def _files(directory: Path) -> list[Path]:
    return sorted(p for p in Path(directory).rglob("*") if p.is_file())


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def seal(directory) -> dict[str, str]:
    """Make every file under ``directory`` read-only and record its hash."""
    directory = Path(directory)
    if not directory.is_dir():
        raise HoldoutError(f"nothing to seal: {directory} is not a directory")
    files = _files(directory)
    if not files:
        raise HoldoutError(f"nothing to seal: {directory} is empty")
    digests = {}
    for p in files:
        digests[p.relative_to(directory).as_posix()] = _sha256(p)
        p.chmod(READ_ONLY)
    manifest_path(directory).write_text(
        "".join(f"{d}  {name}\n" for name, d in sorted(digests.items()))
    )
    return digests


def read_manifest(directory) -> dict[str, str]:
    path = manifest_path(Path(directory))
    if not path.exists():
        raise HoldoutError(f"no manifest at {path}; seal the directory first")
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            digest, name = line.split("  ", 1)
            out[name] = digest
    return out


def verify(directory) -> dict[str, str]:
    """Raise if any sealed file has been removed or altered since sealing."""
    directory = Path(directory)
    recorded = read_manifest(directory)
    problems = []
    for name, digest in recorded.items():
        p = directory / name
        if not p.is_file():
            problems.append(f"{name}: sealed file is missing")
        elif _sha256(p) != digest:
            problems.append(f"{name}: sealed file has been modified since sealing")
    extra = {p.relative_to(directory).as_posix() for p in _files(directory)} - set(recorded)
    problems += [f"{name}: appeared after sealing" for name in sorted(extra)]
    if problems:
        raise HoldoutError("sealed material failed verification:\n  - " + "\n  - ".join(problems))
    return recorded


def _audit(event: str, args) -> None:
    if event != "open" or not _GUARDED:
        return
    target = args[0]
    if isinstance(target, int):
        return
    try:
        path = os.path.realpath(os.fsdecode(target))
    except (TypeError, ValueError):
        return
    for root in _GUARDED:
        if path == root or path.startswith(root + os.sep):
            raise HoldoutError(
                f"{os.path.relpath(path, root)} is sealed and must not be read during the build"
            )


@contextmanager
def sealed_guard(directory):
    """Inside this block, opening anything under ``directory`` raises."""
    global _HOOK_INSTALLED
    if not _HOOK_INSTALLED:
        sys.addaudithook(_audit)
        _HOOK_INSTALLED = True
    root = os.path.realpath(Path(directory))
    _GUARDED.append(root)
    try:
        yield
    finally:
        _GUARDED.remove(root)


def strip_html(markup: str) -> str:
    """Visible text only — script and style contents are not prose."""
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", markup, flags=re.S | re.I)
    return _html.unescape(re.sub(r"<[^>]+>", " ", text))


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9'.-]*", text.lower())


def ngram_overlap(mine: str, reference: str, n: int = 6) -> float:
    """Share of the reference's distinct n-grams that also appear in mine, 0.0 to 1.0."""
    theirs = _ngrams(tokens(reference), n)
    if not theirs:
        return 0.0
    return len(set(_ngrams(tokens(mine), n)) & set(theirs)) / len(set(theirs))


def _ngrams(words: list[str], n: int) -> collections.Counter:
    return collections.Counter(tuple(words[i : i + n]) for i in range(len(words) - n + 1))
