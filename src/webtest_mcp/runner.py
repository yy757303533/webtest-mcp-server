"""Runner - Playwright 执行步骤"""

import asyncio
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .config import load_project_config
from .loader import Case, Step
from .resolver import resolve_locator
from .session import ensure_logged_in
from .utils import sanitize_filename


class StepResult:
    def __init__(self, step: Step, passed: bool, error: Optional[str] = None, screenshot_path: Optional[str] = None):
        self.step = step
        self.passed = passed
        self.error = error
        self.screenshot_path = screenshot_path


class CaseResult:
    def __init__(self, case: Case, passed: bool, step_results: list[StepResult], error: Optional[str] = None):
        self.case = case
        self.passed = passed
        self.step_results = step_results
        self.error = error


async def run_cases(
    project_key: str,
    cases: list[Case],
    base_url_override: Optional[str] = None,
    headless: bool = True,
    artifacts_dir: Optional[Path] = None,
) -> tuple[list[CaseResult], dict[str, Any]]:
    """
    执行用例列表，返回 (CaseResult 列表, result 摘要 dict)
    """
    config = load_project_config(project_key)
    base_url = base_url_override or config.get("base_url", "")
    if not base_url:
        base_url = "about:blank"

    artifacts_dir = artifacts_dir or Path("artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    case_results: list[CaseResult] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        try:
            context = await browser.new_context(base_url=base_url)
            # Suite 级登录
            await ensure_logged_in(context, project_key, base_url)

            for case in cases:
                result = await _run_case(context, project_key, base_url, case, artifacts_dir)
                case_results.append(result)
        finally:
            await browser.close()

    summary = {
        "total": len(case_results),
        "passed": sum(1 for r in case_results if r.passed),
        "failed": sum(1 for r in case_results if not r.passed),
        "results": [
            {
                "case_id": r.case.case_id,
                "title": r.case.title,
                "passed": r.passed,
                "error": r.error,
                "steps": [
                    {
                        "step_no": sr.step.step_no,
                        "action": sr.step.action,
                        "passed": sr.passed,
                        "error": sr.error,
                        "screenshot": sr.screenshot_path,
                    }
                    for sr in r.step_results
                ],
            }
            for r in case_results
        ],
    }
    return case_results, summary


async def _run_case(
    context: BrowserContext,
    project_key: str,
    base_url: str,
    case: Case,
    artifacts_dir: Path,
) -> CaseResult:
    page = await context.new_page()
    step_results: list[StepResult] = []
    passed = True
    err_msg: Optional[str] = None

    try:
        for step in case.steps:
            sr, stop = await _run_step(page, project_key, base_url, step, case.case_id, artifacts_dir)
            step_results.append(sr)
            if not sr.passed:
                passed = False
                err_msg = sr.error
                break
    finally:
        await page.close()

    return CaseResult(case=case, passed=passed, step_results=step_results, error=err_msg)


async def _run_step(
    page: Page,
    project_key: str,
    base_url: str,
    step: Step,
    case_id: str,
    artifacts_dir: Path,
) -> tuple[StepResult, bool]:
    """执行单步，返回 (StepResult, 是否应停止后续步骤)"""
    timeout_ms = step.timeout_ms or 10000

    async def _screenshot_async() -> Optional[str]:
        try:
            subdir = artifacts_dir / "screenshots"
            subdir.mkdir(parents=True, exist_ok=True)
            safe_id = sanitize_filename(case_id)
            path = subdir / f"{safe_id}_step{step.step_no}.png"
            await page.screenshot(path=path)
            return str(path)
        except Exception:
            return None

    try:
        loc = resolve_locator(project_key, step.target) if step.target else None

        if step.action == "go":
            url = step.value or step.target
            if url and not url.startswith("http"):
                url = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
            await page.goto(url or base_url, timeout=timeout_ms)
            return StepResult(step, True), False

        if step.action == "click":
            if not loc:
                return StepResult(step, False, "click 需要 target"), True
            await page.locator(loc).first.click(timeout=timeout_ms)
            return StepResult(step, True), False

        if step.action == "fill":
            if not loc:
                return StepResult(step, False, "fill 需要 target"), True
            await page.locator(loc).first.fill(step.value, timeout=timeout_ms)
            return StepResult(step, True), False

        if step.action == "type":
            if not loc:
                return StepResult(step, False, "type 需要 target"), True
            await page.locator(loc).first.press_sequentially(step.value or "", timeout=timeout_ms)
            return StepResult(step, True), False

        if step.action == "select":
            if not loc:
                return StepResult(step, False, "select 需要 target"), True
            await page.locator(loc).first.select_option(step.value, timeout=timeout_ms)
            return StepResult(step, True), False

        if step.action == "press":
            key = step.value or step.target or "Enter"
            await page.keyboard.press(key)
            return StepResult(step, True), False

        if step.action == "wait_visible":
            if not loc:
                return StepResult(step, False, "wait_visible 需要 target"), True
            await page.locator(loc).first.wait_for(state="visible", timeout=timeout_ms)
            return StepResult(step, True), False

        if step.action == "sleep":
            try:
                sec = float(step.value or step.target or "1")
            except ValueError:
                sec = 1
            await asyncio.sleep(sec)
            return StepResult(step, True), False

        if step.action == "assert_text":
            if step.value:
                # 断言页面包含某文本
                content = await page.content()
                if step.value not in content:
                    shot = await _screenshot_async()
                    return StepResult(step, False, f"页面不包含文本: {step.value}", shot), True
            elif loc:
                # 断言某元素包含某文本 (target 为元素, value 为期望文本 - 这里 value 可能为空，用 target 作 fallback)
                text = await page.locator(loc).first.text_content()
                # 若 value 为空，仅检查元素存在
                if step.value and step.value not in (text or ""):
                    shot = await _screenshot_async()
                    return StepResult(step, False, f"元素文本不包含: {step.value}", shot), True
            else:
                return StepResult(step, False, "assert_text 需要 target 或 value"), True
            return StepResult(step, True), False

        if step.action == "assert_visible":
            if not loc:
                return StepResult(step, False, "assert_visible 需要 target"), True
            try:
                await page.locator(loc).first.wait_for(state="visible", timeout=timeout_ms)
            except Exception as e:
                shot = await _screenshot_async()
                return StepResult(step, False, str(e), shot), True
            return StepResult(step, True), False

        if step.action == "assert_url":
            current = page.url
            if step.value and step.value not in current:
                shot = await _screenshot_async()
                return StepResult(step, False, f"URL 不包含: {step.value}，当前: {current}", shot), True
            return StepResult(step, True), False

        if step.action == "screenshot":
            shot = await _screenshot_async()
            return StepResult(step, True, screenshot_path=shot), False

        return StepResult(step, False, f"未知 action: {step.action}"), True

    except Exception as e:
        shot = await _screenshot_async()
        return StepResult(step, False, str(e), shot), True
