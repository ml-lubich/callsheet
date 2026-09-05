import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class _Balance(HTMLParser):
    """Minimal well-formedness check: every non-void tag closes, in order."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

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
    p = _Balance()
    p.feed(markup)
    p.close()
    return p.errors + [f"<{t}> never closed" for t in p.stack]


def embedded(markup: str, name: str):
    """Pull an injected JSON payload back out of a built page."""
    m = re.search(rf"^const {name}\s*=\s*(.+);$", markup, re.M)
    assert m, f"no embedded {name} payload"
    return json.loads(m.group(1))


@pytest.fixture
def fixtures():
    return FIXTURES


@pytest.fixture
def content():
    return json.loads((FIXTURES / "content.json").read_text())
