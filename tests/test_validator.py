"""测试 validate_suite"""

import pytest
from pathlib import Path

from webtest_mcp.validator import validate_suite

FIXTURES = Path(__file__).parent.parent / "projects" / "demo"


def test_validate_suite_ok():
    result = validate_suite("demo", FIXTURES / "cases.xlsx")
    assert result["valid"] is True
    assert result["cases_count"] >= 1


def test_validate_suite_invalid_project():
    result = validate_suite("nonexistent", "cases.xlsx")
    assert result["valid"] is False
    assert len(result["errors"]) >= 1
