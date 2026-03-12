"""
webtest-mcp-server - MCP 入口

工具:
- list_projects: 列出可用项目
- validate_suite: 预检验证
- run_excel_suite: 执行 Excel 用例
"""

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .config import get_projects_dir, list_projects, load_project_config
from .loader import filter_cases_by_tags, load_excel
from .runner import run_cases
from .validator import validate_suite

mcp = FastMCP("webtest_mcp_server")


def _get_excel_path(project_key: str, excel_path: str) -> Path:
    """解析 Excel 路径：相对则基于项目目录"""
    p = Path(excel_path)
    if p.is_absolute():
        return p
    config = load_project_config(project_key)
    project_dir = Path(config.get("_project_dir", "."))
    return project_dir / excel_path


@mcp.tool()
async def list_projects_tool() -> str:
    """
    列出所有已配置的 Web 测试项目
    Returns: JSON 格式的项目列表
    """
    projects = list_projects()
    projects_dir = get_projects_dir()
    return json.dumps(
        {
            "success": True,
            "projects": projects,
            "projects_dir": str(projects_dir),
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def validate_suite_tool(
    project: str,
    excel_path: str,
    tags: Optional[list[str]] = None,
) -> str:
    """
    预检验证测试套件：Excel 格式、selectors 完整性、项目配置
    Args:
        project: 项目 key
        excel_path: Excel 文件路径（相对项目目录或绝对路径）
        tags: 可选，按标签过滤用例
    Returns: 验证结果 JSON
    """
    try:
        full_path = _get_excel_path(project, excel_path)
        result = validate_suite(project, full_path, tags)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps(
            {"valid": False, "errors": [str(e)], "warnings": []},
            ensure_ascii=False,
            indent=2,
        )


@mcp.tool()
async def run_excel_suite(
    project: str,
    excel_path: str,
    tags: Optional[list[str]] = None,
    headless: bool = True,
    base_url_override: Optional[str] = None,
) -> str:
    """
    执行 Excel 测试套件
    Args:
        project: 项目 key
        excel_path: Excel 文件路径（相对项目目录或绝对路径）
        tags: 可选，按标签过滤用例
        headless: 是否无头模式，默认 True
        base_url_override: 可选，覆盖 base_url
    Returns: 执行结果摘要与 result.json 路径
    """
    try:
        full_path = _get_excel_path(project, excel_path)
        cases = load_excel(full_path)
        if tags:
            cases = filter_cases_by_tags(cases, tags)
        if not cases:
            return json.dumps(
                {"success": False, "error": "无可用用例"},
                ensure_ascii=False,
                indent=2,
            )

        config = load_project_config(project)
        base_url = base_url_override or config.get("base_url", "")
        artifacts_dir = Path("artifacts") / project
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        case_results, summary = await run_cases(
            project_key=project,
            cases=cases,
            base_url_override=base_url_override,
            headless=headless,
            artifacts_dir=artifacts_dir,
        )

        # 写入 result.json
        result_path = artifacts_dir / "result.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "project": project,
                    "excel_path": str(excel_path),
                    "summary": summary,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        return json.dumps(
            {
                "success": True,
                "summary": summary,
                "result_path": str(result_path),
                "artifacts_dir": str(artifacts_dir),
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
