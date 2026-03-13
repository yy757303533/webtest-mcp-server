"""crawler 模块单元测试（不启动浏览器）"""

import pytest

# 测试 _pick_locator 逻辑（通过间接调用）
from webtest_mcp.crawler import _pick_locator, _make_key


def test_make_key():
    assert _make_key("input", "username") == "input_username"
    assert _make_key("button", "submit") == "button_submit"
    assert _make_key("input", "login-email") == "input_login_email"
    assert _make_key("a", "首页") != ""


def test_pick_locator_data_testid():
    row = {"tag": "input", "dataTestid": "email", "id": "", "name": "", "placeholder": ""}
    loc, key, hint = _pick_locator(row, 0)
    assert "data-testid" in loc
    assert "email" in loc
    assert key


def test_pick_locator_name():
    row = {"tag": "input", "dataTestid": "", "id": "", "name": "username", "placeholder": ""}
    loc, key, hint = _pick_locator(row, 0)
    assert "name=" in loc
    assert "username" in loc
    assert "input" in loc


def test_pick_locator_button_text():
    row = {"tag": "button", "dataTestid": "", "id": "", "name": "", "text": "登录"}
    loc, key, hint = _pick_locator(row, 0)
    assert "has-text" in loc or "登录" in loc
