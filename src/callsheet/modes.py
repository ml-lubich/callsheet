"""Output modes — the same call, rendered in a different register and shape.

A mode decides three things and nothing else: the **register** the synthesizer
writes in, the **shape** of the page (which sections appear, in what order, and
how long each may run), and what the verdict, the evidence and the figures
**emphasise**. It never decides what is true. Dropping a section removes it from
the document; it does not remove it from the transcript, and no fact is edited,
softened or invented on the way through.

The prose budgets are not enforced here. Truncating a paragraph to a word count
produces a mutilated paragraph, so the budgets travel to the synthesizer as
instructions and travel to the page as a record of what was asked for.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path

PROJECT_MODES = Path(".callsheet") / "modes.json"

TRANSCRIPT = ("open", "collapsed", "omit")

# section id -> the content keys it renders. A section with no keys is drawn from
# something other than content.json: the metrics (the strip chart), the injected
# figure fragment, or turns.json (the transcript).
SECTIONS: dict[str, tuple[str, ...]] = {
    "strip": (),
    "abstract": ("abstract",),
    "highlights": ("highlights",),
    "figures": (),
    "acts": ("acts",),
    "threads": ("threads",),
    "evidence": ("evidence",),
    "signals": ("signals",),
    "numbers": ("numbers",),
    "tech": ("tech",),
    "friction": ("tensions", "diarization"),
    "quotes": ("quotes",),
    "fit": ("fit",),
    "next": ("next_steps",),
    "transcript": (),
}

ALL = tuple(SECTIONS)

# Words. A budget is a ceiling handed to the writer, not a knife held to the page.
BUDGETS = {
    "abstract": 120,
    "highlights": 25,
    "figures": 40,
    "acts": 60,
    "threads": 40,
    "evidence": 30,
    "signals": 20,
    "numbers": 20,
    "tech": 12,
    "friction": 40,
    "quotes": 60,
    "fit": 40,
    "next": 30,
}

MAX_HIGHLIGHTS = 5

_SECTION = re.compile(r"[ \t]*<section\b[^>]*\bdata-sec=\"([^\"]+)\"[^>]*>.*?</section>\n?", re.S)


class ModeError(ValueError):
    """The requested mode does not exist, or a project mode is malformed."""


@dataclass(frozen=True)
class Mode:
    """One named preset: how to write it, what to show, and what to optimise for."""

    name: str
    register: str
    sections: tuple[str, ...]
    budgets: dict[str, int]
    figures: int
    emphasis: str
    transcript: str
    summary: str


def _halved(budgets: dict[str, int]) -> dict[str, int]:
    return {k: max(1, v // 2) for k, v in budgets.items()}


def _without(*dropped: str) -> tuple[str, ...]:
    return tuple(s for s in ALL if s not in dropped and s != "highlights")


def _order(*first: str) -> tuple[str, ...]:
    rest = tuple(s for s in ALL if s not in first and s != "highlights")
    return first + rest


_BUILT_INS = (
    Mode(
        name="professional",
        register=(
            "Neutral, unhurried, third person where it reads naturally and first person where "
            "quoting. Contractions are fine. No adjectives doing an argument's work. Write so a "
            "reader who was not on the call can check every sentence against a timestamp."
        ),
        sections=_without(),
        budgets=dict(BUDGETS),
        figures=12,
        emphasis=(
            "The verdict states what was decided and what remains open, in that order. Evidence "
            "is ranked by strength, not by order of appearance. Figures cover the whole call "
            "rather than its most quotable minute."
        ),
        transcript="open",
        summary="the default — neutral register, every section, 8-12 figures",
    ),
    Mode(
        name="concise",
        register=(
            "The professional register with every sentence paid for. One clause where two were "
            "used. The threads and the signals are not their own sections here: fold what they "
            "carry into the abstract in a sentence each, and let the figures do the rest."
        ),
        sections=_without("threads", "signals"),
        budgets=_halved(BUDGETS),
        figures=6,
        emphasis=(
            "The verdict comes first and fits in two sentences. Keep only evidence a reader "
            "would ask for; drop what merely corroborates. Figures are chosen for coverage per "
            "square inch."
        ),
        transcript="collapsed",
        summary="every budget halved, threads and signals folded into the abstract, 6 figures",
    ),
    Mode(
        name="formal",
        register=(
            "Third person throughout. No contractions, no quoted slang, no rhetorical questions. "
            "Participants are named by role on first mention. The verdict is written as numbered "
            "findings rather than as a recommendation."
        ),
        sections=_order("strip", "abstract", "evidence", "figures"),
        budgets=dict(BUDGETS),
        figures=10,
        emphasis=(
            "Findings before interpretation. The evidence table leads the document and the "
            "figures support it. Every figure caption cites the timestamps it was built from."
        ),
        transcript="open",
        summary="third person, no contractions, findings not recommendations, evidence first",
    ),
    Mode(
        name="casual",
        register=(
            "Second person, contractions, short sentences. Address the reader directly. Let the "
            "quotes carry the voice of the call and keep your own commentary between them brief. "
            "The verdict reads as a note to a friend who asked how it went."
        ),
        sections=_order("strip", "abstract", "quotes", "figures"),
        budgets=dict(BUDGETS),
        figures=6,
        emphasis=(
            "Quotes lead; the analysis follows them. Evidence is mentioned in passing rather "
            "than tabulated at length. A lighter figure set — the few that are actually fun to "
            "look at."
        ),
        transcript="open",
        summary="second person, contractions, quotes lead, a lighter figure set",
    ),
    Mode(
        name="interesting",
        register=(
            "Open on the three most surprising moments of the call and say why each was "
            "surprising. Reframe every thread as the thing nobody said out loud: what the "
            "participants were circling, in the words they avoided. Never manufacture a tension "
            "that the transcript does not support."
        ),
        sections=_order("strip", "abstract", "friction", "figures", "threads"),
        budgets=dict(BUDGETS),
        figures=8,
        emphasis=(
            "Tensions and turning points before summary. The verdict names what changed during "
            "the call rather than what was concluded. Figures are chosen for surprise, not for "
            "completeness — a figure that confirms the obvious is cut."
        ),
        transcript="open",
        summary="leads with the surprises, threads reframed as what nobody said out loud",
    ),
    Mode(
        name="summarized",
        register=(
            "One reader, two minutes, no scrolling. Abstract, verdict, one composite figure and "
            "the numbers. Under 400 words of prose in total. Nothing is hedged to save space — "
            "a claim that will not fit is cut, not softened."
        ),
        sections=("abstract", "highlights", "figures", "numbers"),
        budgets={"abstract": 120, "highlights": 25, "figures": 40, "numbers": 20},
        figures=1,
        emphasis=(
            "The verdict is the document. The highlights are the at most five things that would "
            "change a reader's mind. One composite figure carries the shape of the whole call."
        ),
        transcript="omit",
        summary="abstract, verdict, one composite figure and the numbers — under 400 words",
    ),
    Mode(
        name="compact",
        register=(
            "Everything, densely. One line per item, no bridging sentences between them, tables "
            "wherever a table will do. Sentence fragments are allowed where they stay "
            "unambiguous. The whole document should fit on two screens."
        ),
        sections=_without(),
        budgets=_halved(BUDGETS),
        figures=12,
        emphasis=(
            "Nothing is dropped, everything is shortened. Evidence and numbers go in tables. "
            "Figures are drawn at half height and captioned in one line."
        ),
        transcript="collapsed",
        summary="everything, but dense — one-line items, tables over prose, two screens",
    ),
    Mode(
        name="creative",
        register=(
            "The editorial register turned up. Open with a titled essay paragraph that earns the "
            "reader's attention without overstating the call. Figures get narrative captions that "
            "carry the argument forward. Quotes are set large and used as beats. The verdict is a "
            "closing paragraph, not a box."
        ),
        sections=_order("strip", "abstract", "figures", "acts", "threads", "evidence", "quotes"),
        budgets={**BUDGETS, "abstract": 200, "figures": 70, "quotes": 90},
        figures=12,
        emphasis=(
            "The argument is a piece of writing with figures inside it. Evidence supports the "
            "essay rather than interrupting it. Nothing is dramatised past what was said."
        ),
        transcript="open",
        summary="a titled essay opening, narrative captions, quotes set large",
    ),
    Mode(
        name="diagrams-only",
        register=(
            "No prose beyond the figure lead-in, the bridges between consecutive figures and the "
            "captions. The figure set is the document, so the bridges have to carry the argument "
            "from one figure to the next."
        ),
        sections=("strip", "figures", "numbers"),
        budgets={"figures": 60, "numbers": 20},
        figures=12,
        emphasis=(
            "Every claim lives in a figure or in a number. The strip chart supplies the shape of "
            "the call; the figures supply everything else."
        ),
        transcript="omit",
        summary="the figure set, the strip chart and the numbers — no prose sections",
    ),
)

MODES: dict[str, Mode] = {m.name: m for m in _BUILT_INS}


def _normalise(m: Mode, where: str) -> Mode:
    """Check a mode is renderable, and keep the transcript flag and section list agreeing."""
    bad = [s for s in m.sections if s not in SECTIONS]
    if bad:
        raise ModeError(
            f"{where}: unknown section {', '.join(repr(s) for s in bad)} — "
            f"the section ids are {', '.join(ALL)}"
        )
    if len(set(m.sections)) != len(m.sections):
        raise ModeError(f"{where}: a section is listed twice in {list(m.sections)}")
    if not m.sections:
        raise ModeError(f"{where}: sections is empty, so the mode would render nothing")
    for section, budget in m.budgets.items():
        if section not in SECTIONS:
            raise ModeError(
                f"{where}: budget for unknown section {section!r} — "
                f"the section ids are {', '.join(ALL)}"
            )
        if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
            raise ModeError(f"{where}: budget for {section!r} must be a positive whole number "
                            f"of words, got {budget!r}")
    if not isinstance(m.figures, int) or isinstance(m.figures, bool) or m.figures < 0:
        raise ModeError(f"{where}: figures must be a whole number of figures, got {m.figures!r}")
    if m.transcript not in TRANSCRIPT:
        raise ModeError(
            f"{where}: transcript {m.transcript!r} is not one of {', '.join(TRANSCRIPT)}"
        )
    sections = tuple(s for s in m.sections if s != "transcript")
    if m.transcript != "omit":
        sections += ("transcript",)
    return replace(m, sections=sections)


def _from_dict(name: str, spec, where: str) -> Mode:
    """A project mode: the named built-in (or ``professional``) with fields overridden."""
    if not isinstance(spec, dict):
        raise ModeError(f"{where}: mode {name!r} must be an object, got {type(spec).__name__}")
    base = MODES.get(name, MODES["professional"])
    unknown = set(spec) - {f for f in Mode.__dataclass_fields__ if f != "name"}
    if unknown:
        raise ModeError(
            f"{where}: mode {name!r} has unknown field(s) {', '.join(sorted(unknown))} — "
            f"a mode carries register, sections, budgets, figures, emphasis, transcript, summary"
        )
    merged = replace(
        base,
        name=name,
        register=str(spec.get("register", base.register)),
        sections=tuple(spec.get("sections", base.sections)),
        budgets=dict(spec.get("budgets", base.budgets)),
        figures=spec.get("figures", base.figures),
        emphasis=str(spec.get("emphasis", base.emphasis)),
        transcript=spec.get("transcript", base.transcript),
        summary=str(spec.get("summary", base.summary)),
    )
    return _normalise(merged, f"{where}: mode {name!r}")


def project_modes(root=None) -> dict[str, Mode]:
    """Modes declared in ``.callsheet/modes.json`` under *root*, validated."""
    path = Path(root or ".") / PROJECT_MODES
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ModeError(f"{path}: is not valid JSON — {e}") from e
    if not isinstance(raw, dict):
        raise ModeError(f"{path}: must be an object mapping a mode name to its definition")
    return {name: _from_dict(name, spec, str(path)) for name, spec in raw.items()}


def all_modes(root=None) -> dict[str, Mode]:
    """The built-ins, with any project modes merged over them."""
    return {**MODES, **project_modes(root)}


def get(name: str, root=None) -> Mode:
    """The named mode. Raises :class:`ModeError` listing the valid names."""
    known = all_modes(root)
    if name not in known:
        raise ModeError(f"unknown mode {name!r} — the modes are {', '.join(known)}")
    return known[name]


def section_order(mode: str, root=None) -> list[str]:
    """The section ids the mode renders, in the order it renders them."""
    return list(get(mode, root).sections)


def prompt_guidance(mode: str, root=None) -> str:
    """The register and emphasis text, for injection into the synthesizer prompt."""
    m = get(mode, root)
    budgets = ", ".join(f"{k} ≤ {v} words" for k, v in m.budgets.items())
    return "\n".join([
        f"Output mode: {m.name} — {m.summary}.",
        "",
        f"Register. {m.register}",
        f"Emphasis. {m.emphasis}",
        "",
        f"Sections, in this order: {', '.join(m.sections)}.",
        f"Budgets: {budgets}.",
        f"Figures: at most {m.figures}. Transcript: {m.transcript}.",
        "",
        REGISTER_RULES,
        "A mode changes the shape and the register of the document. It never changes a fact:",
        "do not add, drop, soften or reweight a claim to fit it.",
    ])


def _highlights(content: dict, limit: int = MAX_HIGHLIGHTS) -> list[str]:
    """Threads, signals and tensions collapsed into one short list."""
    out = []
    for t in content.get("threads") or []:
        name, what = str(t.get("name", "")).strip(), str(t.get("what", "")).strip()
        out.append(f"{name} — {what}" if name and what else name or what)
    out += [str(s.get("signal", "")) for s in content.get("signals") or []]
    out += [str(t.get("note", "")) for t in content.get("tensions") or []]
    return [h.strip() for h in out if h.strip()][:limit]


def apply(content: dict, mode: str, root=None) -> dict:
    """A new content dict shaped for *mode*. Facts are copied through untouched."""
    m = get(mode, root)
    keep = {key for section in m.sections for key in SECTIONS[section]}
    owned = {key for keys in SECTIONS.values() for key in keys}
    out = {k: v for k, v in content.items() if k not in owned or k in keep}
    if "highlights" in m.sections:
        out["highlights"] = _highlights(content)
    out["_mode"] = {
        "name": m.name,
        "sections": list(m.sections),
        "budgets": dict(m.budgets),
        "figures": m.figures,
        "transcript": m.transcript,
    }
    return out


def shape_template(template: str, block: dict) -> str:
    """Keep, reorder and mark the ``<section data-sec=…>`` blocks the mode asked for."""
    found = list(_SECTION.finditer(template))
    if not found:
        return template
    wanted = list(block.get("sections") or ALL)
    keep: list[tuple[tuple[int, int], str]] = []
    for i, match in enumerate(found):
        ids = match.group(1).split()
        ranks = [wanted.index(s) for s in ids if s in wanted]
        if not ranks:
            continue
        html = match.group(0)
        if "transcript" in ids and block.get("transcript") == "collapsed":
            html = html.replace("<section", "<section data-collapsed", 1)
        keep.append(((min(ranks), i), html))
    keep.sort(key=lambda pair: pair[0])
    return template[: found[0].start()] + "".join(h for _, h in keep) + template[found[-1].end() :]


REGISTER_RULES = """Register rules, in every mode:
- No analogies and no metaphors. Say the thing.
- No scare quotes around ordinary words.
- No "essentially", "basically", "simply".
- No sentence that restates the sentence before it.
- Every paragraph opens with the fact, not the framing.
- Concepts over words: a sentence describing a structure — an order, a fan-out,
  a comparison, a magnitude, a position in time — is a figure you have not drawn
  yet. Put it in a `shapes` entry for the diagram agent instead of writing it out."""

# Hard caps in words, enforced at build time. These are the professional defaults;
# each mode scales them. The abstract's cap is the mode's own abstract budget.
PROSE_CAPS = {"paragraph": 70, "act_summary": 60, "thread_what": 55, "list_item": 30}
_CAP_SCALE = {"summarized": 0.6, "compact": 0.6, "concise": 0.75, "creative": 1.3}

# Rows whose one prose field is a list item on the page. Quote text is verbatim
# and is never capped — trimming a quote to a word count falsifies it.
_LIST_FIELDS = (
    ("evidence", "claim"),
    ("evidence", "evidence"),
    ("signals", "signal"),
    ("numbers", "means"),
    ("tensions", "note"),
    ("diarization", "why"),
    ("next_steps", "commitment"),
)

# Sections that render as running prose. Three in a row is a wall of text.
_PROSE_SECTIONS = ("abstract", "acts", "threads", "quotes", "fit")


def caps(mode: str, root=None) -> dict[str, int]:
    """The word caps this mode enforces, keyed by the kind of field."""
    m = get(mode, root)
    scale = _CAP_SCALE.get(m.name, 1.0)
    out = {kind: max(5, round(cap * scale)) for kind, cap in PROSE_CAPS.items()}
    out["abstract"] = m.budgets.get("abstract", BUDGETS["abstract"])
    return out


def _prose_fields(content: dict):
    """(where, text, cap kind) for every prose field a mode caps."""
    yield "abstract", content.get("abstract", ""), "abstract"
    for i, a in enumerate(content.get("acts") or []):
        yield f"acts[{i}].summary", a.get("summary", ""), "act_summary"
        point = a.get("turning_point") or {}
        yield f"acts[{i}].turning_point.text", point.get("text", ""), "list_item"
    for i, t in enumerate(content.get("threads") or []):
        yield f"threads[{i}].what", t.get("what", ""), "thread_what"
        yield f"threads[{i}].why_it_matters", t.get("why_it_matters", ""), "thread_what"
    for section, field in _LIST_FIELDS:
        for i, row in enumerate(content.get(section) or []):
            yield f"{section}[{i}].{field}", row.get(field, ""), "list_item"
    fit = content.get("fit") or {}
    for key in ("aligned_on", "unresolved"):
        for i, item in enumerate(fit.get(key) or []):
            yield f"fit.{key}[{i}]", item, "list_item"
    for i, risk in enumerate(fit.get("risks") or []):
        yield f"fit.risks[{i}].note", risk.get("note", ""), "list_item"


def prose_violations(content: dict, mode: str, root=None) -> list[str]:
    """Every field that is over its cap, with the count and the excess."""
    cap = caps(mode, root)
    out = []
    for where, text, kind in _prose_fields(content):
        text = str(text or "")
        if not text.strip():
            continue
        total = len(text.split())
        if total > cap[kind]:
            out.append(
                f"{where}: {total} words, {mode} allows {cap[kind]} ({total - cap[kind]} over)"
            )
        paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
        if len(paragraphs) < 2:
            continue
        for i, paragraph in enumerate(paragraphs, 1):
            count = len(paragraph.split())
            if count > cap["paragraph"]:
                out.append(
                    f"{where} paragraph {i}: {count} words, {mode} allows "
                    f"{cap['paragraph']} ({count - cap['paragraph']} over)"
                )
    return out


def _renders(content: dict, section: str) -> bool:
    keys = SECTIONS[section]
    return not keys or any(content.get(k) for k in keys)


def layout_violations(content: dict, mode: str, root=None) -> list[str]:
    """Runs of three prose sections with no figure, table or list to break them."""
    out, run = [], []
    for section in section_order(mode, root):
        if not _renders(content, section):
            continue
        if section not in _PROSE_SECTIONS:
            run = []
            continue
        run.append(section)
        if len(run) == 3:
            out.append(
                f"layout: {', '.join(run)} run together with no figure, table or list "
                "between them — break the run with a figure"
            )
            run = []
    return out


def enforce(content: dict, mode: str, root=None) -> None:
    """Raise :class:`ModeError` naming every field that is over its word cap."""
    bad = prose_violations(content, mode, root)
    if bad:
        raise ModeError(
            f"content.json is over budget for mode {mode!r}:\n  - " + "\n  - ".join(bad)
        )
