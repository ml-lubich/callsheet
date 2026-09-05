import json

import pytest

from callgen.build import MARKERS, BuildError, build, external_refs, template_path

from .conftest import FIXTURES, embedded, html_errors

MIN_TPL = (
    "<!doctype html><html><head><script>\n"
    "const CONTENT = /*__CONTENT__*/null;\n"
    "const TURNS   = /*__TURNS__*/null;\n"
    "const METRICS = /*__METRICS__*/null;\n"
    "</script></head><body><div><!--__DIAGRAMS__--></div></body></html>"
)

TURNS = [{"i": 0, "ts": "00:00:00", "s": 0, "spk": "A", "w": 2, "t": "hello there"}]
METRICS = {"duration_s": 10, "turns": 1, "speakers": {}, "timeline": []}


def test_every_marker_is_substituted_exactly_once(content):
    out = build(MIN_TPL, content, TURNS, METRICS, diagrams="<figure></figure>")
    for marker in MARKERS:
        assert marker not in out
    assert embedded(out, "TURNS") == TURNS
    assert embedded(out, "METRICS") == METRICS
    assert embedded(out, "CONTENT")["meta"]["title"] == content["meta"]["title"]


def test_missing_marker_raises_naming_it(content):
    tpl = MIN_TPL.replace("/*__TURNS__*/null", "null")
    with pytest.raises(BuildError) as e:
        build(tpl, content, TURNS, METRICS)
    assert "__TURNS__" in str(e.value)
    assert "0 times" in str(e.value)


def test_duplicated_marker_raises(content):
    tpl = MIN_TPL.replace(
        "const METRICS = /*__METRICS__*/null;",
        "const METRICS = /*__METRICS__*/null;\nconst AGAIN = /*__METRICS__*/null;",
    )
    with pytest.raises(BuildError) as e:
        build(tpl, content, TURNS, METRICS)
    assert "__METRICS__" in str(e.value)
    assert "2 times" in str(e.value)


def test_script_close_in_data_cannot_break_out(content):
    hostile = [dict(TURNS[0], t="</script><img src=x onerror=alert(1)>")]
    out = build(MIN_TPL, content, hostile, METRICS)
    assert out.count("</script>") == 1
    assert "<\\/script>" in out
    assert embedded(out, "TURNS")[0]["t"] == hostile[0]["t"]


def test_missing_diagram_fragment_is_tolerated(content):
    out = build(MIN_TPL, content, TURNS, METRICS, diagrams=None)
    assert "<!--__DIAGRAMS__-->" not in out
    assert "<div></div>" in out


def test_diagram_fragment_is_inlined(content):
    frag = (FIXTURES / "diagrams.html").read_text()
    out = build(MIN_TPL, content, TURNS, METRICS, diagrams=frag)
    assert out.count('<figure class="dg"') == 2


def test_shipped_template_builds_and_is_self_contained(content):
    tpl = template_path().read_text()
    frag = (FIXTURES / "diagrams.html").read_text()
    out = build(tpl, content, TURNS, METRICS, diagrams=frag)
    assert external_refs(out) == []
    for bad in ("http://", "https://", "//cdn", 'src="/', "<link rel=\"stylesheet\""):
        assert bad not in out
    assert html_errors(out) == []


def test_external_refs_finds_what_it_should():
    assert external_refs('<img src="https://x/a.png">')
    assert external_refs("<link rel=stylesheet href='//cdn.example/x.css'>")
    assert external_refs("<style>@import url(http://x/y.css);</style>")
    assert external_refs('<script src="//example.com/a.js"></script>')
    assert external_refs('<a href="#t-3">local</a>') == []
    assert external_refs('<img src="data:image/png;base64,AAA">') == []


def test_content_is_validated_before_injection(content):
    from callgen.schema import SchemaError

    broken = json.loads(json.dumps(content))
    del broken["meta"]["title"]
    with pytest.raises(SchemaError):
        build(MIN_TPL, broken, TURNS, METRICS)
