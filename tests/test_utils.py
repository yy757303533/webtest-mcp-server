"""测试跨平台工具函数"""

import pytest
from webtest_mcp.utils import sanitize_filename


def test_sanitize_filename_normal():
    assert sanitize_filename("tc001") == "tc001"
    assert sanitize_filename("login_test") == "login_test"


def test_sanitize_filename_windows_invalid():
    # Windows 非法字符
    assert sanitize_filename("tc:001") == "tc_001"
    assert sanitize_filename("a*b?c") == "a_b_c"
    assert sanitize_filename('test"file') == "test_file"
    assert sanitize_filename("a<b>c") == "a_b_c"
    assert sanitize_filename("a|b") == "a_b"


def test_sanitize_filename_path_sep():
    assert "\\" not in sanitize_filename("a\\b")
    assert "/" not in sanitize_filename("a/b")
    assert sanitize_filename("path/to/file") == "path_to_file"


def test_sanitize_filename_empty():
    assert sanitize_filename("") == "unnamed"
