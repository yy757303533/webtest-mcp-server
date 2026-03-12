"""Session Manager - Suite 启动时登录，复用 storage_state"""

from pathlib import Path
from typing import Any, Optional

from playwright.async_api import BrowserContext, Page

from .config import load_project_config
from .resolver import resolve_locator


async def perform_login(
    page: Page,
    project_key: str,
) -> bool:
    """
    根据 project.yaml 的 login 配置执行登录，成功返回 True
    """
    config = load_project_config(project_key)
    login_cfg = config.get("login")
    if not login_cfg or not isinstance(login_cfg, dict):
        return False

    url = login_cfg.get("url") or config.get("base_url", "")
    if not url:
        return False

    await page.goto(url)

    username_key = login_cfg.get("username") or "username"
    password_key = login_cfg.get("password") or "password"
    submit_key = login_cfg.get("submit") or "submit"
    account = login_cfg.get("account", "")
    password = login_cfg.get("password_value", "") or login_cfg.get("password_val", "")

    # 从环境变量覆盖
    import os
    account = os.environ.get("WEBTEST_ACCOUNT", account)
    password = os.environ.get("WEBTEST_PASSWORD", password)

    if not account or not password:
        return False

    # 解析 locator 并填写
    base_url = config.get("base_url", "")
    project_dir = config.get("_project_dir", "")
    # 使用项目目录加载 selectors（通过 project_key）
    user_loc = resolve_locator(project_key, username_key) or f"[name={username_key}]"
    pass_loc = resolve_locator(project_key, password_key) or f"[name={password_key}]"
    sub_loc = resolve_locator(project_key, submit_key) or f"button:has-text('登录')"

    try:
        await page.fill(user_loc, account)
        await page.fill(pass_loc, password)
        await page.click(sub_loc)
        # 简单等待导航
        await page.wait_for_load_state("networkidle", timeout=10000)
        return True
    except Exception:
        return False


async def ensure_logged_in(
    context: BrowserContext,
    project_key: str,
    base_url: str,
) -> None:
    """
    确保已登录。若 project 配置了 login，则打开登录页执行登录。
    后续用例复用同一 context，无需重复登录。
    """
    config = load_project_config(project_key)
    login_cfg = config.get("login")
    if not login_cfg:
        return

    page = await context.new_page()
    try:
        await perform_login(page, project_key)
    finally:
        await page.close()
