"""The worked examples under ``examples/`` stay runnable, honest and invented.

These are the files a stranger copies, so they are held to the same gates the
pipeline holds a real run to: the runner is valid shell, the transcript parses to
the turn count its README advertises, the shipped ``content.json`` validates, and
the shipped figures survive ``lint-diagrams`` against the transcript they cite.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from callsheet.diagrams import check_svg_fragment, unresolved_timestamps
from callsheet.parse import parse_transcript
from callsheet.schema import validate

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
RUNNERS = sorted(EXAMPLES.glob("*/run.sh"))
AGENTS = EXAMPLES / "agents"
GENERATED = {"work", "out", "sealed"}

# The examples are invented. Nothing from a real call, client or person may leak in.
FORBIDDEN = ("echostar", "dish", "dmitry", "michael", "misha", "lubich", "brio", "briopedia")
TURNS_CLAIM = re.compile(r"\*\*Turns:\*\*\s*(\d+)")
PROMPT_REF = re.compile(r"prompts/([A-Za-z0-9_-]+\.md)")


@pytest.fixture(params=RUNNERS, ids=[p.parent.name for p in RUNNERS])
def example(request) -> Path:
    return request.param.parent


def committed_files() -> list[Path]:
    return [
        p
        for p in sorted(EXAMPLES.rglob("*"))
        if p.is_file() and not GENERATED & set(p.relative_to(EXAMPLES).parts)
    ]


def test_the_three_examples_are_present():
    assert [p.parent.name for p in RUNNERS] == [
        "customer-discovery",
        "incident-postmortem",
        "product-review",
    ]


def test_runner_is_executable_and_parses(example):
    runner = example / "run.sh"
    assert runner.stat().st_mode & 0o111, f"{runner} is not executable"
    assert subprocess.run(["bash", "-n", str(runner)]).returncode == 0


def test_transcript_parses_to_the_turn_count_the_readme_claims(example):
    claim = TURNS_CLAIM.search((example / "README.md").read_text())
    assert claim, f"{example.name}/README.md does not state a '**Turns:** N' count"
    turns = parse_transcript((example / "transcript.txt").read_text()).turns
    assert len(turns) == int(claim.group(1))
    assert 40 <= len(turns) <= 120


def test_expected_content_validates(example):
    validate(json.loads((example / "expected" / "content.json").read_text()))


def test_expected_diagrams_are_lint_clean(example):
    fragment = (example / "expected" / "diagrams.html").read_text()
    turns = parse_transcript((example / "transcript.txt").read_text()).turns
    assert check_svg_fragment(fragment) == []
    assert unresolved_timestamps(fragment, turns) == []


def test_fanout_script_parses_and_its_prompts_exist():
    fanout = AGENTS / "fanout.sh"
    assert fanout.stat().st_mode & 0o111, f"{fanout} is not executable"
    assert subprocess.run(["bash", "-n", str(fanout)]).returncode == 0
    referenced = set(PROMPT_REF.findall(fanout.read_text()))
    assert referenced, "fanout.sh reads no prompt files"
    for name in sorted(referenced):
        assert (AGENTS / "prompts" / name).is_file(), f"fanout.sh reads a missing prompts/{name}"


@pytest.mark.parametrize("word", FORBIDDEN)
def test_no_real_name_leaks_into_the_examples(word):
    guilty = [
        p.relative_to(EXAMPLES).as_posix()
        for p in committed_files()
        if word in p.read_text(errors="ignore").lower()
    ]
    assert guilty == []
