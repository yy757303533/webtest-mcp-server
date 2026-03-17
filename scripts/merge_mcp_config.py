#!/usr/bin/env python3
"""合并 webtest + playwright 到 MCP 配置文件"""
import json
import sys

def main():
    path = sys.argv[1]
    entry = {
        "webtest": {"command": "webtest-mcp"},
        "playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]},
    }
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data.setdefault("mcpServers", {})
    data["mcpServers"].update(entry)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
