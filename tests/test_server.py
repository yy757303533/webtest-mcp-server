"""测试 MCP 工具（save_test_results）"""

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

try:
    from webtest_mcp.server import save_test_results
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


@pytest.mark.skipif(
    not (PROJECT_ROOT / "projects" / "demo" / "project.yaml").exists(),
    reason="projects/demo 不存在",
)
@pytest.mark.skipif(not HAS_MCP, reason="mcp 未安装，需 pip install -e .")
def test_save_test_results():
    """测试 save_test_results 保存结果"""
    import asyncio

    async def _run():
        return await save_test_results(
            project="demo",
            results=[
                {"case_id": "TC001", "title": "登录", "passed": True},
                {"case_id": "TC002", "title": "失败用例", "passed": False, "error": "元素未找到"},
            ],
            excel_path="login.xlsx",
        )

    result = asyncio.run(_run())
    out = json.loads(result)
    assert out["success"] is True
    assert "run_id" in out
    assert "run_dir" in out
    assert "artifacts_root" in out
    assert "result_path" in out
    assert "report_path" in out
    assert "latest_result_path" in out
    assert "latest_report_path" in out
    assert out["summary"]["total"] == 2
    assert out["summary"]["passed"] == 1
    assert out["summary"]["failed"] == 1
    assert Path(out["result_path"]).exists()
    assert Path(out["report_path"]).exists()
    assert Path(out["latest_result_path"]).exists()
    assert Path(out["latest_report_path"]).exists()
