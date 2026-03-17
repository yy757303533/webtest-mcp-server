#!/usr/bin/env sh
# webtest-mcp-server 卸载（macOS / Linux）
# 移除 Skill，并从 MCP 配置中删除 webtest/playwright 条目

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
PYTHON="${PYTHON:-python3}"
command -v python3 >/dev/null 2>&1 || PYTHON=python

echo ""
echo "  webtest-mcp-server 卸载"
echo "  将移除: Skill、~/.cursor/mcp.json 和 ~/.mcp.json 中的 webtest/playwright"
echo ""
read -r -p "  继续? [y/N] " CONFIRM
case "$CONFIRM" in [Yy]*) ;; *) echo "已取消"; exit 0 ;; esac

# 移除 Skill
for d in "$HOME/.cursor/skills/web-test-runner" "$HOME/.claude/skills/web-test-runner"; do
  [ -d "$d" ] && rm -rf "$d" && echo "  已移除 $d"
done

# 从 MCP 配置中移除 webtest、playwright
for f in "$HOME/.cursor/mcp.json" "$HOME/.mcp.json"; do
  [ -f "$f" ] && "$PYTHON" "$PROJECT_ROOT/scripts/remove_mcp_config.py" "$f" && echo "  已从 $f 移除 webtest/playwright" || true
done

echo ""
echo "卸载完成。重启 Cursor/Claude Code 生效。"
echo "Python 包需手动卸载: pip uninstall webtest-mcp-server"
echo ""
