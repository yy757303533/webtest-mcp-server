# webtest-mcp-server 卸载（Windows PowerShell）
# 移除 Skill，并从 MCP 配置中删除 webtest/playwright 条目

$ErrorActionPreference = "Stop"
$Python = if (Get-Command python -EA 0) { "python" } else { "py" }

Write-Host ""
Write-Host "  webtest-mcp-server 卸载" -ForegroundColor Cyan
Write-Host "  将移除: Skill、mcp.json 中的 webtest/playwright"
Write-Host ""
$confirm = Read-Host "  继续? [y/N]"
if ($confirm -notmatch "^[Yy]") { Write-Host "已取消"; exit 0 }

foreach ($d in @(
    (Join-Path $env:USERPROFILE ".cursor\skills\web-test-runner"),
    (Join-Path $env:USERPROFILE ".claude\skills\web-test-runner")
)) {
    if (Test-Path $d) { Remove-Item -Path $d -Recurse -Force; Write-Host "  已移除 $d" }
}

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
foreach ($f in @(
    (Join-Path $env:USERPROFILE ".cursor\mcp.json"),
    (Join-Path $env:USERPROFILE ".mcp.json")
)) {
    if (Test-Path $f) {
        & $Python "$ProjectRoot\scripts\remove_mcp_config.py" $f
        Write-Host "  已从 $f 移除 webtest/playwright"
    }
}

Write-Host ""
Write-Host "卸载完成。重启 Cursor/Claude Code 生效。" -ForegroundColor Green
Write-Host "Python 包需手动卸载: pip uninstall webtest-mcp-server"
