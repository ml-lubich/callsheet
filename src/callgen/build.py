"""Inject the data into the page template, producing one self-contained file."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import modes as _modes
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


def web_path() -> Path:
    """The React front end. It lives in the source tree, beside src/, not in the wheel."""
    return Path(__file__).resolve().parents[2] / "web"


def web_content(work: Path) -> dict:
    """content.json for the --web build: WORKDIR itself, or WORKDIR/work — the same
    rule `vite.config.ts`'s `workDir()` uses to locate it."""
    work = Path(work)
    for candidate in (work, work / "work"):
        found = candidate / "content.json"
        if found.is_file():
            return json.loads(found.read_text())
    raise BuildError(f"no content.json under {work} (looked in {work} and {work}/work)")


def stage_web(work: Path, mode: str = "professional", root=None) -> Path:
    """Write the mode-applied content — carrying ``_mode`` — plus turns, metrics and the
    diagram fragment into a fresh directory for the vite build to read.

    The vanilla template runs ``apply`` before rendering; the web build reads files off
    disk, so without this it would render the raw content.json and never see the mode's
    section order, transcript setting, figure cap or the sections it folds.
    """
    work = Path(work)
    src = work / "content.json"
    base = work if src.is_file() else work / "work"
    content = json.loads((base / "content.json").read_text())
    validate(content)
    content = _modes.apply(content, mode, root)
    _modes.enforce(content, mode, root)

    staged = Path(tempfile.mkdtemp(prefix="callgen-web-"))
    (staged / "content.json").write_text(json.dumps(content, ensure_ascii=False))
    for name in ("turns.json", "metrics.json", "diagrams.html"):
        found = base / name
        if found.is_file():
            (staged / name).write_text(found.read_text())
    # the fragment can also sit in a sibling out/ dir, as it does for the reference call
    if not (staged / "diagrams.html").is_file():
        sibling = base / ".." / "out" / "diagrams.html"
        if sibling.is_file():
            (staged / "diagrams.html").write_text(sibling.read_text())
    return staged


def build_web(
    work: Path,
    out: Path,
    web: Path | None = None,
    runner=None,
    theme: str = "auto",
    mode: str = "professional",
) -> Path:
    """Run the Vite build over `work` and copy the one file it produces to `out`.

    The vanilla template stays the default; this is the other way of building the same
    data. `runner` is the only seam — everything else here is real filesystem work.
    """
    web = web or web_path()
    runner = runner or subprocess.run
    if not (web / "package.json").is_file():
        raise BuildError(
            f"no web front end at {web} — it ships with the source tree, not the package"
        )
    npm = shutil.which("npm")
    if not npm:
        raise BuildError("npm is not on PATH; the web front end needs node and npm to build")

    env = {
        **os.environ,
        "CALLGEN_WORK": str(Path(work).resolve()),
        "CALLGEN_THEME": theme,
        "CALLGEN_MODE": mode,
    }
    steps = [] if (web / "node_modules").is_dir() else [[npm, "install"]]
    steps.append([npm, "run", "build"])
    for step in steps:
        done = runner(step, cwd=str(web), env=env, capture_output=True, text=True)
        if done.returncode:
            tail = (done.stderr or done.stdout or "").strip().splitlines()[-12:]
            raise BuildError(
                f"{' '.join(step)} failed in {web}:\n  " + "\n  ".join(tail)
            )

    page = web / "dist" / "index.html"
    if not page.is_file():
        raise BuildError(f"the web build wrote no page at {page}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page.read_text())
    return out


def build(
    template: str,
    content: dict,
    turns: list,
    metrics: dict,
    diagrams: str | None = None,
    mode: str = "professional",
    theme: str = "auto",
    root=None,
) -> str:
    """Return the finished page. Raises if the template is not shaped as expected."""
    validate(content)
    content = _modes.apply(content, mode, root)
    content["_theme"] = theme
    _modes.enforce(content, mode, root)
    page = _modes.shape_template(template, content["_mode"])
    for marker, payload in (
        (CONTENT_MARKER, content),
        (TURNS_MARKER, turns),
        (METRICS_MARKER, metrics),
    ):
        page = _substitute(page, marker, _encode(payload))
    page = _substitute(page, DIAGRAMS_MARKER, diagrams or "")
    return _pin_theme(page, theme)


_HTML_OPEN = re.compile(r"<html\b([^>]*)>", re.I)


def _pin_theme(page: str, theme: str) -> str:
    """Bake a light/dark theme into the page and hide the toggle. `auto` is a no-op."""
    if theme not in ("light", "dark"):
        return page
    return _HTML_OPEN.sub(
        lambda m: f'<html{m.group(1)} data-theme="{theme}" data-theme-pin="{theme}">',
        page,
        count=1,
    )


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
