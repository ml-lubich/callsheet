"""The --web branch: the same data through the React front end instead of the template.

Only the subprocess boundary is faked. Everything else — locating the front end, the
environment it is handed, the file it leaves behind — is real.
"""

import json
import subprocess

import pytest

from callgen.build import BuildError, build_web, web_path
from callgen.cli import main

from .conftest import FIXTURES


class Runner:
    """Stands in for subprocess.run, recording the calls and writing what npm would."""

    def __init__(self, web, page="<!doctype html><html>built</html>", code=0, err=""):
        self.web = web
        self.page = page
        self.code = code
        self.err = err
        self.calls = []

    def __call__(self, argv, **kw):
        self.calls.append((argv, kw))
        if self.code == 0 and argv[-1] == "build":
            dist = self.web / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            (dist / "index.html").write_text(self.page)
        return subprocess.CompletedProcess(argv, self.code, stdout="", stderr=self.err)


@pytest.fixture
def web(tmp_path):
    directory = tmp_path / "web"
    (directory / "node_modules").mkdir(parents=True)
    (directory / "package.json").write_text('{"name":"callgen-web"}')
    return directory


@pytest.fixture
def valid_work(tmp_path):
    """A WORKDIR the CLI's schema and mode gates will let through."""
    work = tmp_path / "work"
    work.mkdir()
    (work / "content.json").write_text((FIXTURES / "content.json").read_text())
    return work


def _valid_min_content():
    """The smallest content.json that clears validate() and the professional caps."""
    return {
        "meta": {"title": "T", "date": "2026-01-01", "duration_label": "1 min",
                 "duration_s": 60, "turns": 1, "words": 1,
                 "participants": [{"key": "A", "name": "A", "role": "one"},
                                  {"key": "B", "name": "B", "role": "two"}]},
        "abstract": "One short line.",
        "acts": [{"n": 1, "title": "T", "span": "00:00:00-00:01:00", "start_s": 0,
                  "end_s": 60, "summary": "One line.",
                  "turning_point": {"ts": "00:00:05", "s": 5, "text": "x"}}],
        "evidence": [{"ts": "00:00:05", "s": 5, "claim": "c",
                      "evidence": "e", "strength": "strong"}],
        "signals": [{"ts": "00:00:05", "s": 5, "signal": "s"}],
    }

def test_the_front_end_ships_beside_the_source_tree():
    assert web_path().name == "web"
    assert (web_path() / "package.json").is_file()


def test_it_runs_the_vite_build_over_the_work_dir(tmp_path, web):
    out = tmp_path / "out" / "index.html"
    runner = Runner(web)

    assert build_web(tmp_path / "work", out, web=web, runner=runner) == out
    assert out.read_text() == runner.page

    (argv, kw) = runner.calls[-1]
    assert argv[1:] == ["run", "build"]
    assert kw["cwd"] == str(web)
    assert kw["env"]["CALLGEN_WORK"] == str((tmp_path / "work").resolve())


def test_dependencies_are_installed_only_when_they_are_missing(tmp_path, web):
    runner = Runner(web)
    build_web(tmp_path / "work", tmp_path / "a.html", web=web, runner=runner)
    assert [argv[1] for argv, _ in runner.calls] == ["run"]

    (web / "node_modules").rmdir()
    runner = Runner(web)
    build_web(tmp_path / "work", tmp_path / "b.html", web=web, runner=runner)
    assert [argv[1] for argv, _ in runner.calls] == ["install", "run"]


def test_a_failed_build_reports_what_npm_said(tmp_path, web):
    runner = Runner(web, code=1, err="line one\nthe real error")
    with pytest.raises(BuildError, match="the real error"):
        build_web(tmp_path / "work", tmp_path / "out.html", web=web, runner=runner)


def test_a_build_that_wrote_nothing_is_an_error_not_a_success(tmp_path, web):
    runner = Runner(web)
    runner.page = None

    def silent(argv, **kw):
        runner.calls.append((argv, kw))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    with pytest.raises(BuildError, match="wrote no page"):
        build_web(tmp_path / "work", tmp_path / "out.html", web=web, runner=silent)


def test_the_theme_reaches_the_web_build_as_an_env_var(tmp_path, web):
    runner = Runner(web)
    build_web(tmp_path / "work", tmp_path / "out.html", web=web, runner=runner, theme="dark")
    (argv, kw) = runner.calls[-1]
    assert kw["env"]["CALLGEN_THEME"] == "dark"


def test_the_theme_defaults_to_auto(tmp_path, web):
    runner = Runner(web)
    build_web(tmp_path / "work", tmp_path / "out.html", web=web, runner=runner)
    (argv, kw) = runner.calls[-1]
    assert kw["env"]["CALLGEN_THEME"] == "auto"


def test_cli_web_branch_passes_the_theme_flag(valid_work, web, monkeypatch, tmp_path, capsys):
    runner = Runner(web)
    monkeypatch.setattr("callgen.build.web_path", lambda: web)
    monkeypatch.setattr("callgen.build.subprocess.run", runner)

    assert main([
        "build", "--web", str(valid_work), "--theme", "light",
        "-o", str(tmp_path / "out" / "index.html"),
    ]) == 0
    capsys.readouterr()
    (argv, kw) = runner.calls[-1]
    assert kw["env"]["CALLGEN_THEME"] == "light"
    assert kw["env"]["CALLGEN_MODE"] == "professional"


def test_a_missing_front_end_says_so(tmp_path):
    with pytest.raises(BuildError, match="no web front end"):
        build_web(tmp_path, tmp_path / "out.html", web=tmp_path / "nowhere")


def test_missing_npm_is_named_rather_than_a_stack_trace(tmp_path, web, monkeypatch):
    monkeypatch.setattr("callgen.build.shutil.which", lambda _: None)
    with pytest.raises(BuildError, match="npm is not on PATH"):
        build_web(tmp_path / "work", tmp_path / "out.html", web=web)


def test_cli_web_branch_writes_the_page(valid_work, web, monkeypatch, tmp_path, capsys):
    out = tmp_path / "out" / "index.html"
    runner = Runner(web)
    monkeypatch.setattr("callgen.build.web_path", lambda: web)
    monkeypatch.setattr("callgen.build.subprocess.run", runner)

    assert main(["build", "--web", str(valid_work), "-o", str(out)]) == 0
    assert out.is_file()
    assert "one file" in capsys.readouterr().out


def test_cli_web_branch_refuses_content_that_breaks_its_mode(tmp_path, web, monkeypatch, capsys):
    work = tmp_path / "work"
    work.mkdir()
    payload = json.loads((FIXTURES / "content.json").read_text())
    payload["abstract"] = " ".join(["word"] * 300)
    (work / "content.json").write_text(json.dumps(payload))
    runner = Runner(web)
    monkeypatch.setattr("callgen.build.web_path", lambda: web)
    monkeypatch.setattr("callgen.build.subprocess.run", runner)

    code = main(["build", "--web", str(work), "-o", str(tmp_path / "out" / "index.html")])
    assert code == 1
    assert "abstract" in capsys.readouterr().err
    assert runner.calls == []


def test_web_content_finds_content_json_in_workdir_or_its_work_subdir(tmp_path):
    from callgen.build import web_content

    direct = tmp_path / "direct"
    direct.mkdir()
    (direct / "content.json").write_text('{"a": 1}')
    assert web_content(direct) == {"a": 1}

    nested = tmp_path / "nested"
    (nested / "work").mkdir(parents=True)
    (nested / "work" / "content.json").write_text('{"b": 2}')
    assert web_content(nested) == {"b": 2}

    with pytest.raises(BuildError, match="no content.json"):
        web_content(tmp_path / "empty")


def test_cli_still_demands_the_data_when_there_is_no_web_flag(tmp_path, capsys):
    assert main(["build", "-o", str(tmp_path / "out.html")]) == 1
    assert "--content" in capsys.readouterr().err


def test_stage_web_writes_applied_content_with_the_mode_block(tmp_path):
    from callgen.build import stage_web
    work = tmp_path / "work"
    work.mkdir()
    (work / "content.json").write_text(json.dumps(_valid_min_content()))
    (work / "turns.json").write_text("[]")
    (work / "metrics.json").write_text("{}")
    (work / "diagrams.html").write_text("<figure></figure>")

    staged = stage_web(work, "professional")
    applied = json.loads((staged / "content.json").read_text())
    assert "_mode" in applied
    assert "collapsed" in applied["_mode"]
    # the other inputs are carried across so vite finds them beside content.json
    assert (staged / "turns.json").is_file()
    assert (staged / "metrics.json").is_file()
    assert (staged / "diagrams.html").read_text() == "<figure></figure>"
