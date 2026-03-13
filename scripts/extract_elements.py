#!/usr/bin/env python3
"""页面爬取：提取可交互元素，生成/合并 selectors.yaml"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from webtest_mcp.config import get_projects_dir
from webtest_mcp.crawler import extract_elements, merge_into_selectors, ElementCandidate
from webtest_mcp.validator import validate_suite


def main():
    parser = argparse.ArgumentParser(description="从页面提取可交互元素，生成 selectors 候选")
    parser.add_argument("--project", "-p", required=True, help="项目 key")
    parser.add_argument("--url", "-u", required=True, help="要爬取的页面 URL")
    parser.add_argument("--merge", "-m", action="store_true", help="合并到项目的 selectors.yaml")
    parser.add_argument("--merge-mode", choices=["append", "overwrite"], default="append",
                        help="append=追加不覆盖已有, overwrite=全量覆盖")
    parser.add_argument("--verify", "-v", action="store_true",
                        help="合并后运行 validate_suite 验证（需指定 excel）")
    parser.add_argument("--excel", "-e", help="验证时使用的 Excel 路径，如 login_cases.xlsx")
    parser.add_argument("--timeout", "-t", type=int, default=15000, help="页面加载超时(ms)")
    args = parser.parse_args()

    # 检查项目存在
    projects_dir = get_projects_dir()
    project_dir = projects_dir / args.project
    if not (project_dir / "project.yaml").exists():
        print(f"错误: 项目 '{args.project}' 不存在或缺少 project.yaml")
        sys.exit(1)

    async def run():
        print(f"爬取: {args.url}")
        candidates = await extract_elements(args.url, timeout_ms=args.timeout)
        print(f"提取 {len(candidates)} 个候选元素:")
        for c in candidates:
            print(f"  {c.key}: {c.locator}  ({c.hint})")

        if args.merge:
            path = merge_into_selectors(args.project, candidates, args.merge_mode)
            print(f"\n已合并到: {path}")

        if args.verify and args.excel:
            from webtest_mcp.config import load_project_config
            config = load_project_config(args.project)
            project_dir_path = Path(config.get("_project_dir", "."))
            excel_path = project_dir_path / args.excel
            if not excel_path.exists():
                print(f"错误: Excel 不存在 {excel_path}")
                return
            result = validate_suite(args.project, excel_path)
            print("\n=== validate_suite 结果 ===")
            print(f"valid: {result['valid']}, errors: {result.get('errors', [])}")
            if result.get("warnings"):
                for w in result["warnings"]:
                    print(f"  warning: {w}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
