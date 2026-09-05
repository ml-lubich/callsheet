import json

from callgen.build import build, external_refs, template_path
from callgen.cli import main
from callgen.parse import metrics, parse_transcript

from .conftest import FIXTURES, embedded, html_errors


def test_transcript_to_finished_page(content):
    t = parse_transcript((FIXTURES / "bracket_hms.txt").read_text())
    out = build(
        template_path().read_text(),
        content,
        t.turns,
        metrics(t),
        diagrams=(FIXTURES / "diagrams.html").read_text(),
    )
    turns = embedded(out, "TURNS")
    assert len(turns) == 6
    assert turns[-1]["ts"] == "01:07:15"
    assert embedded(out, "METRICS")["duration_s"] == 4035
    assert out.count('<figure class="dg"') == 2
    assert external_refs(out) == []
    assert html_errors(out) == []
    assert "Ada Sterling" in out and "Bo Marek" in out


def test_cli_parse_chunk_and_build(tmp_path, capsys):
    work = tmp_path / "work"
    assert main(["parse", str(FIXTURES / "bracket_hms.txt"), "-o", str(work)]) == 0
    turns = json.loads((work / "turns.json").read_text())
    mets = json.loads((work / "metrics.json").read_text())
    assert len(turns) == 6
    assert mets["turns"] == 6

    assert main(["chunk", str(work / "turns.json"), "-n", "2", "-o", str(work)]) == 0
    assert (work / "chunk1.txt").exists()
    assert (work / "chunk2.txt").exists()
    assert not (work / "chunk3.txt").exists()

    page = tmp_path / "index.html"
    code = main([
        "build",
        "--content", str(FIXTURES / "content.json"),
        "--turns", str(work / "turns.json"),
        "--metrics", str(work / "metrics.json"),
        "--diagrams", str(FIXTURES / "diagrams.html"),
        "-o", str(page),
    ])
    assert code == 0
    html = page.read_text()
    assert len(embedded(html, "TURNS")) == 6
    assert html.count('<figure class="dg"') == 2
    capsys.readouterr()


def test_cli_seal_and_compare(tmp_path, capsys):
    sealed = tmp_path / "sealed"
    sealed.mkdir()
    (sealed / "reference.html").write_text("<p>alpha bravo charlie delta echo foxtrot</p>")
    assert main(["seal", str(sealed)]) == 0
    assert (tmp_path / "sealed.sha256").exists()

    mine = tmp_path / "mine.html"
    mine.write_text("<p>kilo lima mike november oscar papa quebec</p>")
    assert main(["compare", str(mine), str(sealed)]) == 0
    out = capsys.readouterr().out
    assert "reference.html" in out
    assert "0.0%" in out


def test_cli_reports_a_bad_content_file(tmp_path, capsys):
    broken = tmp_path / "content.json"
    broken.write_text(json.dumps({"meta": {}}))
    code = main([
        "build",
        "--content", str(broken),
        "--turns", str(FIXTURES / "content.json"),
        "--metrics", str(FIXTURES / "content.json"),
        "-o", str(tmp_path / "x.html"),
    ])
    assert code == 1
    assert "meta.title" in capsys.readouterr().err
