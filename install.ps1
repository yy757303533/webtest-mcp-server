# webtest-mcp-server 一键安装（Windows PowerShell）
# Skill 自动部署，MCP 合并到全局

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir
$CursorMcp = Join-Path $env:USERPROFILE ".cursor\mcp.json"
$ClaudeMcp = Join-Path $env:USERPROFILE ".mcp.json"

# 检测 Python
$Python = $null
if (Get-Command python -ErrorAction SilentlyContinue) { $Python = "python" }
elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $Python = "python3" }
elseif (Get-Command py -ErrorAction SilentlyContinue) { $Python = "py" }
if (-not $Python) {
    Write-Host "错误: 未找到 python、python3 或 py" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  webtest-mcp-server x Cursor / Claude Code" -ForegroundColor White
Write-Host "  Skill + MCP 一键安装" -ForegroundColor White
Write-Host ""
Write-Host "  将安装:"
Write-Host "    * web-test-runner Skill  -> ~/.cursor/skills、~/.claude/skills"
Write-Host "    * webtest + playwright   -> 合并到 ~/.cursor/mcp.json、~/.mcp.json"
Write-Host ""

# 1. 安装 Python 包
Write-Host "[1/4] 安装 Python 依赖..." -ForegroundColor Yellow
Set-Location $ProjectRoot
& $Python -m pip install -e . -q
Write-Host "  ok" -ForegroundColor Green

# 2. 安装 Skill（自动部署，无需手动配置）
Write-Host "[2/4] 安装 Skill..." -ForegroundColor Yellow
$CursorSkills = Join-Path $env:USERPROFILE ".cursor\skills"
$ClaudeSkills = Join-Path $env:USERPROFILE ".claude\skills"
New-Item -ItemType Directory -Force -Path $CursorSkills | Out-Null
New-Item -ItemType Directory -Force -Path $ClaudeSkills | Out-Null
foreach ($skill in @("web-test-runner", "case-generator", "case-executor")) {
    Copy-Item -Path "$ProjectRoot\.cursor\skills\$skill" -Destination $CursorSkills -Recurse -Force
    Copy-Item -Path "$ProjectRoot\.claude\skills\$skill" -Destination $ClaudeSkills -Recurse -Force
    Write-Host "  Cursor: ~/.cursor/skills/$skill"
    Write-Host "  Claude: ~/.claude/skills/$skill"
}

# 3. 合并 MCP 到全局配置
Write-Host "[3/4] 注册 MCP（合并到全局配置）..." -ForegroundColor Yellow
foreach ($mcpFile in @($CursorMcp, $ClaudeMcp)) {
    $dir = Split-Path -Parent $mcpFile
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    & $Python "$ProjectRoot\scripts\merge_mcp_config.py" $mcpFile
    Write-Host "  已配置 $mcpFile"
}

# 4. 项目级配置
Write-Host "[4/4] 项目级配置..." -ForegroundColor Yellow
$CursorDir = Join-Path $ProjectRoot ".cursor"
New-Item -ItemType Directory -Force -Path $CursorDir | Out-Null
Copy-Item -Path "$ProjectRoot\mcp-config.json" -Destination "$CursorDir\mcp.json" -Force
Write-Host "  已创建 $CursorDir\mcp.json"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  安装完成！Skill 和 MCP 已就绪，无需手动配置" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  1. 重启 Cursor / Claude Code 使 MCP 生效"
Write-Host "  2. 确保已安装 Node.js（playwright-mcp 需要 npx）"
Write-Host "  3. 使用: 对 AI 说「执行 demo 的 cases.xlsx」"
Write-Host ""
