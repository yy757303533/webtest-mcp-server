#!/usr/bin/env python3
"""冒烟测试 - 使用 data: URL，无需外网，可指定项目"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# 支持指定项目，默认 demo
project = os.environ.get("WEBTEST_PROJECT") or (sys.argv[1] if len(sys.argv) > 1 else "demo")

from webtest_mcp.loader import load_excel
from webtest_mcp.runner import run_cases


def main():
    root = Path(__file__).resolve().parent.parent
    excel_path = root / "projects" / project / "smoke_cases.xlsx"
    if not excel_path.exists():
        print(f"错误: 项目 '{project}' 下不存在 smoke_cases.xlsx")
        sys.exit(1)
    cases = load_excel(excel_path)
    print(f"项目: {project}, 加载 {len(cases)} 个用例（无需外网）: {[c.case_id for c in cases]}")

    import asyncio
    results, summary = asyncio.run(run_cases(
        project_key=project,
        cases=cases,
        base_url_override="about:blank",
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


if __name__ == "__main__":
    main()
