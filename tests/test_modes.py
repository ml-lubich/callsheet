"""Output modes change the shape and the register of the page, never the facts."""

from __future__ import annotations

import json

import pytest

from callgen.build import build, template_path
from callgen.cli import main
from callgen.modes import (
    MODES,
    REGISTER_RULES,
    SECTIONS,
    TRANSCRIPT,
    ModeError,
    all_modes,
    apply,
    caps,
    enforce,
    get,
    layout_violations,
    prompt_guidance,
    prose_violations,
    section_order,
)
from callgen.parse import metrics, parse_transcript

from .conftest import FIXTURES, embedded, html_errors

NINE = [
    "professional",
    "concise",
    "formal",
    "casual",
    "interesting",
    "summarized",
    "compact",
    "creative",
    "diagrams-only",
]

# Which content keys a mode is allowed to keep, derived from the section map.
def kept_keys(mode: str) -> set[str]:
    keys: set[str] = set()
    for section in section_order(mode):
        keys.update(SECTIONS[section])
    return keys


def owned_keys() -> set[str]:
    return {k for ids in SECTIONS.values() for k in ids}


def words(value) -> int:
    if isinstance(value, str):
        return len(value.split())
    if isinstance(value, list):
        return sum(words(v) for v in value)
    if isinstance(value, dict):
        return sum(words(v) for k, v in value.items() if not k.startswith("_"))
    return 0


def within_budget(content, mode: str) -> dict:
    """The fixture abstract, cut to whatever this mode allows, so shape tests test shape."""
    cap = caps(mode)
    room = min(cap["abstract"], cap["paragraph"])
    return dict(content, abstract=" ".join(content["abstract"].split()[:room]))


def page(content, mode: str) -> str:
    t = parse_transcript((FIXTURES / "bracket_hms.txt").read_text())
    return build(
        template_path().read_text(),
        within_budget(content, mode),
        t.turns,
        metrics(t),
        diagrams=(FIXTURES / "diagrams.html").read_text(),
        mode=mode,
    )


def test_the_nine_modes_ship():
    assert list(MODES) == NINE


@pytest.mark.parametrize("name", NINE)
def test_every_builtin_mode_has_a_valid_shape(name):
    m = get(name)
    assert m.name == name
    assert m.sections, "a mode with no sections renders nothing"
    assert len(set(m.sections)) == len(m.sections), "a section is listed twice"
    for section in m.sections:
        assert section in SECTIONS, f"{section!r} is not a known section id"
    for section, budget in m.budgets.items():
        assert section in SECTIONS, f"budget for unknown section {section!r}"
        assert isinstance(budget, int) and budget > 0
    assert isinstance(m.figures, int) and m.figures >= 0
    assert m.transcript in TRANSCRIPT
    assert ("transcript" in m.sections) == (m.transcript != "omit")
    assert m.register.strip() and m.emphasis.strip() and m.summary.strip()


@pytest.mark.parametrize("name", NINE)
def test_apply_removes_exactly_the_sections_the_mode_drops(content, name):
    out = apply(content, name)
    dropped = owned_keys() - kept_keys(name)
    for key in dropped:
        assert key not in out, f"{name} should not carry {key}"
    for key in set(content) & kept_keys(name):
        assert key in out


@pytest.mark.parametrize("name", NINE)
def test_apply_never_alters_a_fact(content, name):
    out = apply(content, name)
    for key, value in out.items():
        if key in ("_mode", "highlights"):
            continue
        assert value == content[key], f"{name} changed {key}"


@pytest.mark.parametrize("name", NINE)
def test_apply_carries_the_mode_block(content, name):
    block = apply(content, name)["_mode"]
    m = get(name)
    assert block == {
        "name": name,
        "sections": list(m.sections),
        "budgets": dict(m.budgets),
        "figures": m.figures,
        "transcript": m.transcript,
    }


def test_apply_leaves_the_input_untouched(content):
    before = json.dumps(content, sort_keys=True)
    apply(content, "summarized")
    assert json.dumps(content, sort_keys=True) == before


def test_concise_halves_every_budget(content):
    full, short = get("professional"), get("concise")
    for section, budget in short.budgets.items():
        assert budget == max(1, full.budgets[section] // 2)
    assert short.figures == 6
    assert short.transcript == "collapsed"


def test_summarized_is_five_highlights_and_under_four_hundred_words(content):
    out = apply(content, "summarized")
    assert 0 < len(out["highlights"]) <= 5
    assert all(isinstance(h, str) and h.strip() for h in out["highlights"])
    assert words(out) < 400


def test_diagrams_only_keeps_figures_numbers_and_the_strip_chart(content):
    order = section_order("diagrams-only")
    assert order == ["strip", "figures", "numbers"]
    out = apply(content, "diagrams-only")
    assert out["numbers"] == content["numbers"]
    for key in ("acts", "threads", "evidence", "quotes", "abstract", "next_steps"):
        assert key not in out


def test_unknown_mode_names_the_valid_ones():
    with pytest.raises(ModeError) as e:
        apply({}, "punchy")
    assert "punchy" in str(e.value)
    for name in NINE:
        assert name in str(e.value)


def test_prompt_guidance_carries_register_and_emphasis():
    m = get("formal")
    text = prompt_guidance("formal")
    assert m.register in text and m.emphasis in text
    assert "formal" in text
    assert "never changes a fact" in text


def test_section_order_is_the_modes_order():
    assert section_order("formal").index("evidence") < section_order("formal").index("figures")
    assert section_order("professional").index("figures") < section_order("professional").index(
        "evidence"
    )


def _write_project_modes(root, payload) -> None:
    (root / ".callgen").mkdir(parents=True, exist_ok=True)
    (root / ".callgen" / "modes.json").write_text(
        payload if isinstance(payload, str) else json.dumps(payload)
    )


def test_project_modes_merge_over_the_builtins(tmp_path, content):
    _write_project_modes(
        tmp_path,
        {
            "concise": {"figures": 2},
            "brief": {"sections": ["abstract"], "transcript": "omit"},
        },
    )
    merged = all_modes(tmp_path)
    assert merged["concise"].figures == 2
    assert merged["concise"].register == get("concise").register, "unstated fields are inherited"
    assert merged["brief"].sections == ("abstract",)
    assert merged["concise"].sections[-1] == "transcript", "an open transcript is kept last"
    assert apply(content, "brief", tmp_path)["_mode"]["name"] == "brief"
    assert get("concise").figures == 6, "the built-in is not mutated"


def test_malformed_project_mode_is_rejected_with_a_clear_message(tmp_path):
    _write_project_modes(tmp_path, {"odd": {"sections": ["nowhere"]}})
    with pytest.raises(ModeError) as e:
        all_modes(tmp_path)
    assert "odd" in str(e.value) and "nowhere" in str(e.value)
    assert "abstract" in str(e.value), "the message lists the section ids that do exist"


def test_project_modes_that_are_not_json_say_so(tmp_path):
    _write_project_modes(tmp_path, "{not json")
    with pytest.raises(ModeError) as e:
        all_modes(tmp_path)
    assert "modes.json" in str(e.value)


def test_negative_figure_budget_is_rejected(tmp_path):
    _write_project_modes(tmp_path, {"odd": {"figures": -1}})
    with pytest.raises(ModeError) as e:
        all_modes(tmp_path)
    assert "figures" in str(e.value)


def test_page_honours_diagrams_only(content):
    out = page(content, "diagrams-only")
    assert 'id="evbody"' not in out
    assert 'id="tlist"' not in out
    assert 'id="threads"' not in out
    assert 'id="diagrams"' in out and 'id="numbers"' in out and 'id="chart"' in out
    assert html_errors(out) == []


def test_page_honours_summarized(content):
    out = page(content, "summarized")
    assert 'id="highlights"' in out
    assert 'id="tlist"' not in out
    assert 'id="acts"' not in out and 'id="actlist"' not in out
    assert embedded(out, "CONTENT")["highlights"]
    assert html_errors(out) == []


def test_page_reorders_sections_for_formal(content):
    out = page(content, "formal")
    assert out.index('id="evbody"') < out.index('id="diagrams"')
    assert html_errors(out) == []


def test_page_collapses_the_transcript_for_concise(content):
    out = page(content, "concise")
    assert 'id="tlist"' in out
    assert "data-collapsed" in out
    assert 'id="threads"' not in out, "concise folds threads into the abstract"


def test_professional_is_the_default_and_keeps_every_section(content):
    default, explicit = page(content, "professional"), page(content, "professional")
    assert default == explicit
    for anchor in ("evbody", "tlist", "threads", "diagrams", "quotes", "next"):
        assert f'id="{anchor}"' in default


def test_cli_modes_lists_all_nine(capsys):
    assert main(["modes"]) == 0
    printed = capsys.readouterr().out
    for name in NINE:
        assert name in printed
        assert get(name).summary in printed


def test_cli_build_accepts_a_mode(tmp_path, capsys):
    work = tmp_path / "work"
    assert main(["parse", str(FIXTURES / "bracket_hms.txt"), "-o", str(work)]) == 0
    out = tmp_path / "index.html"
    code = main([
        "build",
        "--content", str(FIXTURES / "content.json"),
        "--turns", str(work / "turns.json"),
        "--metrics", str(work / "metrics.json"),
        "--diagrams", str(FIXTURES / "diagrams.html"),
        "--mode", "diagrams-only",
        "-o", str(out),
    ])
    assert code == 0
    assert 'id="evbody"' not in out.read_text()
    capsys.readouterr()


def test_cli_build_rejects_an_unknown_mode(tmp_path, capsys):
    work = tmp_path / "work"
    assert main(["parse", str(FIXTURES / "bracket_hms.txt"), "-o", str(work)]) == 0
    code = main([
        "build",
        "--content", str(FIXTURES / "content.json"),
        "--turns", str(work / "turns.json"),
        "--metrics", str(work / "metrics.json"),
        "--mode", "punchy",
        "-o", str(tmp_path / "index.html"),
    ])
    assert code == 1
    assert "punchy" in capsys.readouterr().err


# --- hard caps -------------------------------------------------------------


def over(content, **fields):
    return {**content, **fields}


def test_an_in_budget_content_passes_every_mode(content):
    for name in NINE:
        enforce(within_budget(content, name), name)


def test_an_over_budget_abstract_fails_and_names_the_field(content):
    long_abstract = " ".join(["word"] * 200)
    with pytest.raises(ModeError) as e:
        enforce(over(content, abstract=long_abstract), "professional")
    assert "abstract" in str(e.value)
    assert "200 words" in str(e.value) and "120" in str(e.value) and "80 over" in str(e.value)


def test_a_long_paragraph_fails_even_when_the_field_fits(content):
    body = " ".join(["word"] * 71) + "\n\n" + "tail."
    bad = prose_violations(over(content, abstract=body), "professional")
    assert any("paragraph 1" in v and "71 words" in v for v in bad)


def test_each_kind_of_field_has_its_own_cap(content):
    acts = [dict(content["acts"][0], summary=" ".join(["word"] * 61))]
    bad = prose_violations(over(content, acts=acts), "professional")
    assert any("acts[0].summary" in v and "60" in v for v in bad)

    threads = [dict(content["threads"][0], what=" ".join(["word"] * 56))]
    bad = prose_violations(over(content, threads=threads), "professional")
    assert any("threads[0].what" in v and "55" in v for v in bad)

    signals = [dict(content["signals"][0], signal=" ".join(["word"] * 31))]
    bad = prose_violations(over(content, signals=signals), "professional")
    assert any("signals[0].signal" in v and "30" in v for v in bad)


def test_a_quote_is_never_capped(content):
    quotes = [dict(content["quotes"][0], text=" ".join(["word"] * 200))]
    assert prose_violations(over(content, quotes=quotes), "professional") == []


@pytest.mark.parametrize("name", NINE)
def test_every_mode_carries_its_own_caps(name):
    cap = caps(name)
    assert cap["abstract"] == get(name).budgets.get("abstract", 120)
    for kind in ("paragraph", "act_summary", "thread_what", "list_item"):
        assert cap[kind] > 0
    if name in ("compact", "summarized"):
        assert cap["list_item"] < caps("professional")["list_item"]
    if name == "creative":
        assert cap["list_item"] > caps("professional")["list_item"]


def test_the_build_refuses_an_over_budget_page(content):
    t = parse_transcript((FIXTURES / "bracket_hms.txt").read_text())
    with pytest.raises(ModeError) as e:
        build(
            template_path().read_text(),
            over(content, abstract=" ".join(["word"] * 300)),
            t.turns,
            metrics(t),
            mode="professional",
        )
    assert "abstract" in str(e.value)


# --- register rules and wall-of-text ---------------------------------------


@pytest.mark.parametrize("name", NINE)
def test_every_mode_states_the_register_rules(name):
    text = prompt_guidance(name)
    assert REGISTER_RULES in text
    for rule in ("metaphors", "scare quotes", "essentially", "shapes"):
        assert rule in text


@pytest.mark.parametrize("name", NINE)
def test_no_builtin_mode_stacks_three_prose_sections(content, name):
    assert layout_violations(content, name) == []


def test_three_prose_sections_in_a_row_are_flagged(content, tmp_path):
    _write_project_modes(
        tmp_path,
        {"wall": {"sections": ["abstract", "acts", "threads", "quotes"], "transcript": "omit"}},
    )
    bad = layout_violations(content, "wall", tmp_path)
    assert len(bad) == 1
    assert "abstract, acts, threads" in bad[0] and "figure" in bad[0]


def test_an_empty_section_does_not_count_toward_a_wall(content, tmp_path):
    _write_project_modes(
        tmp_path,
        {"three": {"sections": ["abstract", "acts", "threads"], "transcript": "omit"}},
    )
    assert layout_violations(content, "three", tmp_path)
    assert layout_violations({**content, "acts": []}, "three", tmp_path) == []


def test_cli_lint_prose_passes_and_fails(tmp_path, capsys):
    assert main(["lint-prose", str(FIXTURES / "content.json")]) == 0
    assert "within every professional budget" in capsys.readouterr().out

    bad = tmp_path / "content.json"
    payload = json.loads((FIXTURES / "content.json").read_text())
    payload["abstract"] = " ".join(["word"] * 300)
    bad.write_text(json.dumps(payload))
    assert main(["lint-prose", str(bad), "--mode", "concise"]) == 1
    err = capsys.readouterr().err
    assert "abstract" in err and "300 words" in err and "concise" in err


# --- verdict and lands travel with the sections that own them -----------------
# The page renders the verdict as the abstract's first block and "where it lands"
# as the acts' conclusion. apply() must not strip either when its owner survives.

def test_verdict_travels_with_abstract_and_lands_with_acts(content):
    content = dict(content)
    content["verdict"] = {"position": "p", "for": ["a"], "against": ["b"], "decides_it": "c"}
    content["lands"] = [{"observation": "o", "transfers_to": "t", "ts": "00:00:05", "s": 5}]
    kept = apply(content, "professional")
    assert kept["verdict"] == content["verdict"]
    assert kept["lands"] == content["lands"]
    dropped = apply(content, "diagrams-only")
    assert "verdict" not in dropped and "lands" not in dropped
    summarized = apply(content, "summarized")
    assert "verdict" in summarized          # abstract survives, so its verdict does
    assert "lands" not in summarized        # acts do not
