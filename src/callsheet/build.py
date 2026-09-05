"""Inject the data into the page template, producing one self-contained file."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .schema import validate

CONTENT_MARKER = "/*__CONTENT__*/null"
TURNS_MARKER = "/*__TURNS__*/null"
METRICS_MARKER = "/*__METRICS__*/null"
DIAGRAMS_MARKER = "<!--__DIAGRAMS__-->"
MARKERS = (CONTENT_MARKER, TURNS_MARKER, METRICS_MARKER, DIAGRAMS_MARKER)

# src/href/@import/url() pointing at another host. data: and #fragments are fine.
_EXTERNAL = re.compile(
    r"""(?:\b(?:src|href)\s*=\s*|@import\s+|url\(\s*)['"]?\s*(?:https?:)?//[^'")\s>]+""",
    re.I,
)


class BuildError(RuntimeError):
    """The template and the data could not be combined."""


def template_path() -> Path:
    """The page template shipped with the package."""
    return Path(__file__).parent / "templates" / "page.html"


def build(
    template: str, content: dict, turns: list, metrics: dict, diagrams: str | None = None
) -> str:
    """Return the finished page. Raises if the template is not shaped as expected."""
    validate(content)
    page = template
    for marker, payload in (
        (CONTENT_MARKER, content),
        (TURNS_MARKER, turns),
        (METRICS_MARKER, metrics),
    ):
        page = _substitute(page, marker, _encode(payload))
    return _substitute(page, DIAGRAMS_MARKER, diagrams or "")


def _substitute(page: str, marker: str, payload: str) -> str:
    found = page.count(marker)
    if found != 1:
        name = marker.strip("/*<!->").strip()
        raise BuildError(f"marker {name} appears {found} times in the template, expected exactly 1")
    return page.replace(marker, payload)


def _encode(obj) -> str:
    """JSON that cannot terminate the script element it is embedded in."""
    return (
        json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
        .replace("</", "<\\/")
        .replace("<!--", "<\\u0021--")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def external_refs(page: str) -> list[str]:
    """Every reference in the page that would cause a network request."""
    return _EXTERNAL.findall(page)
