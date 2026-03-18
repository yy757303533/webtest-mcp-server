"""
webtest-mcp-server - MCP 入口

工具:
- list_projects_tool: 列出可用项目
- get_excel_cases: 读取 Excel 自然语言用例（支持按模块、标签、优先级过滤）
- get_grouped_cases: 按模块分组返回用例概要，用于分批执行
- save_test_results: 保存执行结果到 result.json 和 report.md
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .config import get_projects_dir, list_projects, load_project_config
from .loader import (
    ExcelCase,
    filter_cases_by_module,
    filter_cases_by_priority,
    filter_cases_by_tags,
    group_cases_by_module,
    load_excel_cases,
)

mcp = FastMCP("webtest_mcp_server")


def _get_excel_path(project_key: str, excel_path: str) -> Path:
    """解析 Excel 路径：相对则基于项目目录"""
    p = Path(excel_path)
    if p.is_absolute():
        return p
    config = load_project_config(project_key)
    project_dir = Path(config.get("_project_dir", "."))
    return project_dir / excel_path


def _case_to_dict(c: ExcelCase) -> dict:
    """ExcelCase → 供 AI 消费的 dict（steps 和 expected 独立）"""
    d: dict[str, Any] = {
        "case_id": c.case_id,
        "title": c.title,
        "steps": [
            {"step_no": s.step_no, "description": s.description}
            for s in c.steps
        ],
        "expected": [
            {"expect_no": e.expect_no, "description": e.description}
            for e in c.expected
        ],
    }
    if c.module:
        d["module"] = c.module
    if c.precondition:
        d["precondition"] = c.precondition
    if c.priority:
        d["priority"] = c.priority
    if c.tags:
        d["tags"] = c.tags
    if c.test_type:
        d["test_type"] = c.test_type
    return d


def _load_and_filter(
    project: str,
    excel_path: str,
    tags: Optional[list[str]] = None,
    module: Optional[str] = None,
    priorities: Optional[list[str]] = None,
) -> tuple[list[ExcelCase], str]:
    """加载 + 过滤，返回 (cases, base_url)"""
    full_path = _get_excel_path(project, excel_path)
    if not full_path.exists():
        raise FileNotFoundError(f"Excel 不存在: {full_path}")
    cases = load_excel_cases(full_path)
    if tags:
        cases = filter_cases_by_tags(cases, tags)
    if module:
        cases = filter_cases_by_module(cases, module)
    if priorities:
        cases = filter_cases_by_priority(cases, priorities)
    config = load_project_config(project)
    base_url = config.get("base_url", "")
    return cases, base_url


# ───────────────────────────────────────────────────────────────────────────
# MCP 工具
# ───────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def list_projects_tool() -> str:
    """
    列出所有已配置的 Web 测试项目
    Returns: JSON 格式的项目列表（含 projects、projects_dir）
    """
    projects = list_projects()
    projects_dir = get_projects_dir()
    return json.dumps(
        {"success": True, "projects": projects, "projects_dir": str(projects_dir)},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def get_excel_cases(
    project: str,
    excel_path: str,
    tags: Optional[list[str]] = None,
    module: Optional[str] = None,
    priorities: Optional[list[str]] = None,
) -> str:
    """
    读取 Excel 中的自然语言测试用例，供 AI 配合 playwright-mcp 执行。
    支持 .xls 和 .xlsx 格式。

    Args:
        project: 项目 key
        excel_path: Excel 文件路径（相对项目目录或绝对路径）
        tags: 可选，按标签过滤，如 ["导航", "CTA"]
        module: 可选，按模块过滤，如 "SPE模拟器"
        priorities: 可选，按优先级过滤，如 ["高", "中"]
    Returns:
        用例列表 JSON，每条含 case_id, title, module, precondition,
        steps: [{step_no, description, expected}], tags, priority
    """
    try:
        if project not in list_projects():
            return json.dumps(
                {"success": False, "error": f"项目 {project} 不存在"},
                ensure_ascii=False,
                indent=2,
            )
        cases, base_url = _load_and_filter(project, excel_path, tags, module, priorities)
        out = [_case_to_dict(c) for c in cases]
        return json.dumps(
            {
                "success": True,
                "project": project,
                "base_url": base_url,
                "excel_path": str(excel_path),
                "count": len(out),
                "cases": out,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"success": False, "error": str(e)},
            ensure_ascii=False,
            indent=2,
        )


@mcp.tool()
async def get_grouped_cases(
    project: str,
    excel_path: str,
    tags: Optional[list[str]] = None,
    priorities: Optional[list[str]] = None,
) -> str:
    """
    按模块分组返回用例概要，用于规划分批执行。
    不返回完整步骤，只返回每个模块的用例数量和 case_id 列表。

    AI 可据此决定先执行哪个模块，再调用 get_excel_cases(module=...) 获取详细步骤。

    Args:
        project: 项目 key
        excel_path: Excel 文件路径
        tags: 可选，按标签过滤
        priorities: 可选，按优先级过滤
    Returns:
        按模块分组的用例概要 JSON
    """
    try:
        if project not in list_projects():
            return json.dumps(
                {"success": False, "error": f"项目 {project} 不存在"},
                ensure_ascii=False,
                indent=2,
            )
        cases, base_url = _load_and_filter(
            project, excel_path, tags=tags, priorities=priorities
        )
        groups = group_cases_by_module(cases)
        out = []
        for mod, mod_cases in groups.items():
            out.append(
                {
                    "module": mod,
                    "count": len(mod_cases),
                    "case_ids": [c.case_id for c in mod_cases],
                    "priorities": list(set(c.priority for c in mod_cases if c.priority)),
                }
            )
        # 按用例数降序
        out.sort(key=lambda g: g["count"], reverse=True)
        return json.dumps(
            {
                "success": True,
                "project": project,
                "base_url": base_url,
                "excel_path": str(excel_path),
                "total_cases": len(cases),
                "total_modules": len(out),
                "groups": out,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"success": False, "error": str(e)},
            ensure_ascii=False,
            indent=2,
        )


@mcp.tool()
async def save_test_results(
    project: str,
    results: list[dict[str, Any]],
    excel_path: Optional[str] = None,
) -> str:
    """
    保存测试执行结果到 artifacts/project/ 目录
    Args:
        project: 项目 key
        results: 结果列表，每项含 case_id, title, passed (bool), error (可选)
        excel_path: 可选，用例文件路径（便于追溯）
    Returns: 保存路径 JSON
    """
    try:
        if project not in list_projects():
            return json.dumps(
                {"success": False, "error": f"项目 {project} 不存在"},
                ensure_ascii=False,
                indent=2,
            )
        artifacts_dir = Path.cwd() / "artifacts" / project
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        passed = sum(1 for r in results if r.get("passed", False))
        failed = len(results) - passed
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": project,
            "excel_path": excel_path,
            "summary": {"total": len(results), "passed": passed, "failed": failed},
            "results": results,
        }
        result_path = artifacts_dir / "result.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        report_lines = [
            "# 测试结果",
            "",
            f"**项目**: {project}",
            f"**时间**: {payload['timestamp']}",
            f"**用例文件**: {excel_path or '-'}",
            "",
            f"**总计**: {len(results)} 条，通过 {passed}，失败 {failed}",
            "",
            "| 用例ID | 标题 | 结果 |",
            "|--------|------|------|",
        ]
        for r in results:
            status = "✅ PASS" if r.get("passed", False) else "❌ FAIL"
            err = r.get("error", "")
            title = str(r.get("title", "")).replace("|", "\\|")
            report_lines.append(f"| {r.get('case_id', '')} | {title} | {status} {err} |")
        report_path = artifacts_dir / "report.md"
        report_path.write_text("\n".join(report_lines), encoding="utf-8")

        return json.dumps(
            {
                "success": True,
                "result_path": str(result_path),
                "report_path": str(report_path),
                "summary": payload["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"success": False, "error": str(e)},
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    """MCP 入口"""
    mcp.run()


if __name__ == "__main__":
    main()
