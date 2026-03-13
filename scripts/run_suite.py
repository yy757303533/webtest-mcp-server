#!/usr/bin/env python3
"""执行指定项目的 Excel 用例，支持多项目"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from webtest_mcp.loader import load_excel
from webtest_mcp.runner import run_cases
from webtest_mcp.config import load_project_config, list_projects


def main():
    # 从环境变量或命令行获取：项目、Excel、base_url
    project = os.environ.get("WEBTEST_PROJECT") or (sys.argv[1] if len(sys.argv) > 1 else "demo")
    excel_name = os.environ.get("WEBTEST_EXCEL") or (sys.argv[2] if len(sys.argv) > 2 else "login_cases.xlsx")
    base_url_override = os.environ.get("WEBTEST_BASE_URL")

    root = Path(__file__).resolve().parent.parent
    excel_path = root / "projects" / project / excel_name

    if not excel_path.exists():
        projects = list_projects()
        print(f"错误: 项目 '{project}' 下不存在 {excel_name}")
        print(f"可用项目: {projects}")
        sys.exit(1)

    cases = load_excel(excel_path)
    print(f"项目: {project}, 用例文件: {excel_name}")
    print(f"加载 {len(cases)} 个用例: {[c.case_id for c in cases]}")

    if not base_url_override:
        try:
            config = load_project_config(project)
            base_url_override = config.get("base_url", "about:blank")
        except Exception:
            base_url_override = "about:blank"

    results, summary = asyncio.run(run_cases(
        project_key=project,
        cases=cases,
        base_url_override=base_url_override,
        headless=True,
        artifacts_dir=root / "artifacts" / project,
    ))

    print("\n=== 执行结果 ===")
    print(f"总数: {summary['total']}, 通过: {summary['passed']}, 失败: {summary['failed']}")
    for r in summary["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['case_id']} - {r['title']}")
        if not r["passed"] and r.get("error"):
            print(f"      错误: {r['error']}")

    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
