import json
import re
from pathlib import Path

import pytest

from callsheet.diagrams import html_errors  # noqa: F401  (re-exported for the page tests)

FIXTURES = Path(__file__).parent / "fixtures"


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
