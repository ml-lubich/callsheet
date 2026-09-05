"""Static checks for a hand-authored inline-SVG diagram fragment.

The figures in ``out/diagrams.html`` are written by an agent, not generated, so
the things that go wrong are the things a careful hand still gets wrong at two in
the morning: a hex colour that stops following the page theme, a marker id reused
between two figures so every arrowhead on the page turns one colour, a figure
with no accessible name, a timestamp that was never said.

Nothing here judges whether a diagram is any good — see ``skills/diagrams`` for
that. These are the mechanical faults that can be caught for free.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser

from .parse import ts_to_seconds

MIN_FONT_PX = 10.0

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# ``#abc`` inside url(...) or an href is a fragment reference, not a colour.
_NOT_A_COLOR = re.compile(r"""url\([^)]*\)|href\s*=\s*["']#[^"']*["']""", re.I)
_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
_MONO = re.compile(r"\bmonospace\b", re.I)
_NAMED = re.compile(r"""fill\s*(?:=\s*["']|:\s*)(white|black)\b""", re.I)
_FONT = re.compile(r"""font-size\s*[:=]\s*["']?\s*(\d+(?:\.\d+)?(?:px)?)""", re.I)
_FIGURE = re.compile(r"<figure\b.*?</figure>", re.I | re.S)
_ID = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""", re.I)
_MARKER = re.compile(r"""<marker\b[^>]*?\bid\s*=\s*["']([^"']+)["']""", re.I | re.S)
_KEY = re.compile(r"""<ol\b[^>]*class\s*=\s*["'][^"']*\bdg-key\b[^"']*["'][^>]*>(.*?)</ol>""",
                  re.I | re.S)
_ROLE_IMG = re.compile(r"""\brole\s*=\s*["']img["']""", re.I)
_TS = re.compile(r"\b\d{1,3}:\d{2}(?::\d{2})?\b")


@dataclass(frozen=True)
class Problem:
    """One mechanical fault, located at a figure id or at the fragment itself."""

    kind: str
    where: str
    detail: str

    def __str__(self) -> str:
        return f"{self.where}: {self.kind}: {self.detail}"


class _Balance(HTMLParser):
    """Minimal well-formedness check: every non-void tag closes, in order."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"</{tag}> with nothing open")
        elif self.stack[-1] != tag:
            self.errors.append(f"</{tag}> closes <{self.stack[-1]}>")
        else:
            self.stack.pop()


def html_errors(markup: str) -> list[str]:
    """Every unbalanced tag in ``markup``, in the order they were met."""
    p = _Balance()
    p.feed(markup)
    p.close()
    return p.errors + [f"<{t}> never closed" for t in p.stack]


def figure_ids(text: str) -> list[str]:
    """The id of every ``<figure>`` in the fragment, in document order."""
    return [id for _, _, id, _ in _figures(text)]


def extract_timestamps(text: str) -> list[str]:
    """Every distinct HH:MM:SS (or MM:SS) cited in the fragment, in document order."""
    seen: dict[str, None] = {}
    for m in _TS.finditer(text):
        seen.setdefault(m.group(0), None)
    return list(seen)


def unresolved_timestamps(fragment: str, turns: list[dict]) -> list[str]:
    """Timestamps cited in the fragment that do not start any parsed turn."""
    said = {ts_to_seconds(t["ts"]) if "ts" in t else int(t["s"]) for t in turns}
    return [ts for ts in extract_timestamps(fragment) if ts_to_seconds(ts) not in said]


def check_svg_fragment(text: str) -> list[Problem]:
    """Every mechanical fault in the fragment, in document order.

    Well-formedness is checked first and on its own: once the tags do not nest,
    figure boundaries are guesswork and every later check reports noise.
    """
    broken = html_errors(text)
    if broken:
        return [Problem("not-well-formed", "fragment", b) for b in broken]

    figures = _figures(text)
    found: list[tuple[int, Problem]] = []
    scannable = _NOT_A_COLOR.sub(lambda m: " " * len(m.group(0)), text)

    for pattern, kind, describe in (
        (_HEX, "hex-color", lambda v: f"literal colour {v}, use a var(--pen-a) style token"),
        (_MONO, "monospace", lambda v: f"{v} font family; the house style has none"),
        (_NAMED, "named-color", lambda v: f"literal fill {v}, use var(--paper-2) or a pen"),
    ):
        for m in pattern.finditer(scannable):
            at = m.start()
            found.append((at, Problem(kind, _locate(figures, at), describe(m.group(0)))))

    for m in _FONT.finditer(scannable):
        raw = m.group(1)
        if float(raw.removesuffix("px")) < MIN_FONT_PX:
            found.append((m.start(), Problem(
                "tiny-text", _locate(figures, m.start()),
                f"font-size {raw} is below the {MIN_FONT_PX:g}px floor",
            )))

    owner: dict[str, str] = {}
    for start, body, fig_id, _ in figures:
        missing = [
            what for what, present in (
                ('role="img"', _ROLE_IMG.search(body)),
                ("<title>", "<title" in body.lower()),
                ("<desc>", "<desc" in body.lower()),
            ) if not present
        ]
        if missing:
            found.append((start, Problem(
                "missing-a11y", fig_id, f"figure has no {', '.join(missing)}"
            )))

        key = _KEY.search(body)
        if not key or "<li" not in key.group(1).lower():
            found.append((start, Problem(
                "no-key", fig_id, "figure has no numbered <ol class=\"dg-key\"> with entries"
            )))

        for marker in _MARKER.findall(body):
            if marker in owner and owner[marker] != fig_id:
                found.append((start, Problem(
                    "duplicate-marker-id", fig_id,
                    f"marker id {marker} is already used by {owner[marker]}; prefix it per figure",
                )))
            owner.setdefault(marker, fig_id)

    return [p for _, p in sorted(found, key=lambda pair: pair[0])]


def _figures(text: str) -> list[tuple[int, str, str, int]]:
    """(start, markup, id, end) for each figure, in document order."""
    out = []
    for n, m in enumerate(_FIGURE.finditer(text), 1):
        head = m.group(0)[: m.group(0).find(">") + 1]
        found = _ID.search(head)
        out.append((m.start(), m.group(0), found.group(1) if found else f"figure {n}", m.end()))
    return out


def _locate(figures: list[tuple[int, str, str, int]], pos: int) -> str:
    for start, _, fig_id, end in figures:
        if start <= pos < end:
            return fig_id
    return "fragment"
