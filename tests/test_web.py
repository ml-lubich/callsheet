"""The --web branch: the same data through the React front end instead of the template.

Only the subprocess boundary is faked. Everything else — locating the front end, the
environment it is handed, the file it leaves behind — is real.
"""

import subprocess

import pytest

from callgen.build import BuildError, build_web, web_path
from callgen.cli import main


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


def test_a_missing_front_end_says_so(tmp_path):
    with pytest.raises(BuildError, match="no web front end"):
        build_web(tmp_path, tmp_path / "out.html", web=tmp_path / "nowhere")


def test_missing_npm_is_named_rather_than_a_stack_trace(tmp_path, web, monkeypatch):
    monkeypatch.setattr("callgen.build.shutil.which", lambda _: None)
    with pytest.raises(BuildError, match="npm is not on PATH"):
        build_web(tmp_path / "work", tmp_path / "out.html", web=web)


def test_cli_web_branch_writes_the_page(tmp_path, web, monkeypatch, capsys):
    out = tmp_path / "out" / "index.html"
    runner = Runner(web)
    monkeypatch.setattr("callgen.build.web_path", lambda: web)
    monkeypatch.setattr("callgen.build.subprocess.run", runner)

    assert main(["build", "--web", str(tmp_path / "work"), "-o", str(out)]) == 0
    assert out.is_file()
    assert "one file" in capsys.readouterr().out


def test_cli_still_demands_the_data_when_there_is_no_web_flag(tmp_path, capsys):
    assert main(["build", "-o", str(tmp_path / "out.html")]) == 1
    assert "--content" in capsys.readouterr().err
