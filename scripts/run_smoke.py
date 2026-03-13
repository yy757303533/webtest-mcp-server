#!/usr/bin/env python3
"""冒烟测试 - 使用 data: URL，无需外网，验证流水线可用"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from webtest_mcp.loader import load_excel
from webtest_mcp.runner import run_cases


def main():
    excel_path = Path(__file__).resolve().parent.parent / "projects" / "demo" / "smoke_cases.xlsx"
    cases = load_excel(excel_path)
    print(f"加载 {len(cases)} 个用例（无需外网）: {[c.case_id for c in cases]}")

    results, summary = asyncio.run(run_cases(
        project_key="demo",
        cases=cases,
        base_url_override="about:blank",
        headless=True,
        artifacts_dir=Path("artifacts") / "demo",
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
