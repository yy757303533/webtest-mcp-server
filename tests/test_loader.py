"""测试 Excel loader"""

import pytest
from pathlib import Path

from webtest_mcp.loader import load_excel, filter_cases_by_tags, Case, Step

FIXTURES = Path(__file__).parent.parent / "projects" / "demo"


def test_load_excel():
    excel_path = FIXTURES / "cases.xlsx"
    assert excel_path.exists()
    cases = load_excel(excel_path)
    assert len(cases) >= 1
    c = cases[0]
    assert c.case_id == "tc001"
    assert len(c.steps) >= 2
    assert c.steps[0].action == "go"
    assert c.steps[1].action == "assert_text"


def test_filter_by_tags():
    excel_path = FIXTURES / "cases.xlsx"
    cases = load_excel(excel_path)
    filtered = filter_cases_by_tags(cases, ["smoke"])
    assert len(filtered) >= 1
    empty = filter_cases_by_tags(cases, ["nonexistent"])
    assert len(empty) == 0
