#!/usr/bin/env sh
# webtest-mcp-server 一键安装（macOS / Linux）
# Skill 自动部署，MCP 合并到全局配置

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
CURSOR_MCP="$HOME/.cursor/mcp.json"
CLAUDE_MCP="$HOME/.mcp.json"

# 检测 Python
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "错误: 未找到 python 或 python3"
  exit 1
fi

echo ""
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║     webtest-mcp-server × Cursor / Claude Code        ║"
echo "  ║     Skill + MCP 一键安装                              ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo ""
echo "  将安装："
echo "    • web-test-runner Skill  → ~/.cursor/skills、~/.claude/skills"
echo "    • webtest + playwright   → 合并到 ~/.cursor/mcp.json、~/.mcp.json"
echo ""

# 1. 安装 Python 包
echo "[1/4] 安装 Python 依赖..."
cd "$PROJECT_ROOT"
"$PYTHON" -m pip install -e . -q
echo "  ok"

# 2. 安装 Skill（用户级，所有项目可用，无需手动配置）
echo "[2/4] 安装 Skill（自动部署）..."
mkdir -p "$HOME/.cursor/skills" "$HOME/.claude/skills"
cp -r "$PROJECT_ROOT/.cursor/skills/web-test-runner" "$HOME/.cursor/skills/"
cp -r "$PROJECT_ROOT/.claude/skills/web-test-runner" "$HOME/.claude/skills/"
echo "  Cursor: ~/.cursor/skills/web-test-runner"
echo "  Claude: ~/.claude/skills/web-test-runner"

# 3. 合并 MCP 到全局配置（保留已有，仅添加 webtest + playwright）
echo "[3/4] 注册 MCP（合并到全局配置）..."
for mcp_file in "$CURSOR_MCP" "$CLAUDE_MCP"; do
  mkdir -p "$(dirname "$mcp_file")"
  "$PYTHON" "$PROJECT_ROOT/scripts/merge_mcp_config.py" "$mcp_file"
  echo "  已配置 $mcp_file"
done

# 4. 项目级 .cursor/mcp.json（便于 git 共享）
echo "[4/4] 项目级配置..."
mkdir -p "$PROJECT_ROOT/.cursor"
cp "$PROJECT_ROOT/mcp-config.json" "$PROJECT_ROOT/.cursor/mcp.json"
echo "  已创建 $PROJECT_ROOT/.cursor/mcp.json（可选，团队共享）"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  安装完成！Skill 和 MCP 已就绪，无需手动配置"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "  1. 重启 Cursor / Claude Code 使 MCP 生效"
echo "  2. 确保已安装 Node.js（playwright-mcp 需要 npx）"
echo "  3. 使用：对 AI 说「执行 demo 的 cases.xlsx」"
echo ""
