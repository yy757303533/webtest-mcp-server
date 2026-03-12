"""测试 Runner 执行（需要网络 + Playwright 浏览器，CI 环境可能缺少 libgbm 等依赖）"""

import asyncio
import os
from pathlib import Path

import pytest

from webtest_mcp.loader import load_excel
from webtest_mcp.runner import run_cases

FIXTURES = Path(__file__).parent.parent / "projects" / "demo"

# 仅当设置 WEBTEST_RUN_INTEGRATION=1 时执行（需完整 Playwright 环境）
RUN_INTEGRATION = os.environ.get("WEBTEST_RUN_INTEGRATION", "").lower() in ("1", "true", "yes")


@pytest.mark.skipif(not RUN_INTEGRATION, reason="需要 WEBTEST_RUN_INTEGRATION=1 且完整 Playwright 环境")
def test_run_cases_example_com():
    """执行 demo 用例：访问 example.com 并断言标题"""
    cases = load_excel(FIXTURES / "cases.xlsx")
    assert cases
    results, summary = asyncio.run(run_cases(
        project_key="demo",
        cases=cases,
        base_url_override="https://example.com",
        headless=True,
        artifacts_dir=Path("artifacts") / "demo",
    ))
    assert summary["total"] >= 1
    assert summary["passed"] >= 1 or summary["failed"] >= 1  # 至少跑完
    assert "results" in summary
