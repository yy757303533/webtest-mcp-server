# webtest-mcp-server

读取 Excel 中的自然语言手工测试用例，供 AI Agent 配合 [@playwright/mcp](https://github.com/microsoft/playwright-mcp) 执行。

## 功能

- **list_projects_tool**：列出已配置项目
- **get_excel_cases**：读取 Excel 自然语言用例，返回供 AI 消费的 JSON
- **save_test_results**：保存执行结果到 `artifacts/<project>/result.json` 和 `report.md`

执行由 AI + playwright-mcp 完成；AI 执行完成后调用 save_test_results 持久化结果。

## 安装

**一键安装**（Skill + MCP 全自动，无需手动配置）：

| 平台 | 命令 |
|------|------|
| macOS / Linux | `sh install.sh` |
| Windows (PowerShell) | `.\install.ps1` |

安装脚本会：1）`pip install -e .` 2）复制 Skill 到 `~/.cursor/skills`、`~/.claude/skills` 3）将 webtest + playwright 合并到 `~/.cursor/mcp.json`、`~/.mcp.json`（不覆盖已有 MCP）4）创建项目级 `.cursor/mcp.json`。  
**Skill 和 MCP 自动生效，无需手动配置。** 重启 Cursor/Claude Code 即可。

**手动安装**：

```bash
pip install -e .
```

## 项目配置

在 `projects/<project_key>/` 下创建：

- **project.yaml**：`base_url` 等
- Excel 用例文件（支持「步骤描述」「期望结果」或「action」「target」「value」列）

### Excel 格式

**自然语言格式**（推荐）：

| 用例ID | 标题 | 步骤描述 | 期望结果 |
|--------|------|----------|----------|
| TC001 | 登录 | 输入 admin，密码 123456，点击登录 | 跳转首页 |
| TC002 | 登录失败 | 输入错误密码，点击登录 | 提示密码错误 |

**结构化格式**（兼容）：

| 用例ID | 标题 | action | target | value |
|--------|------|--------|--------|-------|
| TC001 | 登录 | fill | 用户名 | admin |
| TC001 | 登录 | click | 登录按钮 | |

## 使用

### 1. 启动 MCP 服务

```bash
webtest-mcp
# 或
python -m webtest_mcp.server
```

### 2. 配置双 MCP（Cursor / Claude Code）

运行 `install.sh` 或 `install.ps1` 后，会自动创建 `.cursor/mcp.json`，包含 webtest-mcp 和 playwright-mcp。  
在 Cursor 中打开本项目作为工作区即可加载。

**手动配置**：Settings → MCP → 添加 webtest（command: `webtest-mcp`）和 playwright（command: `npx`, args: `@playwright/mcp@latest`）

### 3. Skill（Phase 2）

项目已包含 **web-test-runner** Skill：

- Cursor：`.cursor/skills/web-test-runner/SKILL.md`
- Claude Code：`.claude/skills/web-test-runner/SKILL.md`

当用户说「执行 demo 的登录用例」「跑 Excel 测试」时，AI 会命中 Skill，按流程执行：

1. 调用 `get_excel_cases` 获取用例
2. 调用 playwright-mcp 的 browser_navigate、browser_snapshot、browser_click、browser_type 等操作
3. 汇总 PASS/FAIL 报告

## 本地验证

```bash
# 创建示例 Excel
python scripts/create_demo_excel.py

# 列出用例
python scripts/list_cases.py demo cases.xlsx
```

**PYTHONPATH**：Windows CMD `set PYTHONPATH=src`；PowerShell `$env:PYTHONPATH="src"`；macOS/Linux `export PYTHONPATH=src`。  
完整测试步骤见 [docs/TESTING.md](docs/TESTING.md)。项目支持 **Windows、macOS、Linux**。

## 测试

```bash
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/ -v
```

项目路径可通过环境变量 `WEBTEST_PROJECTS_DIR` 覆盖。

## 打包

- **PyPI**：`sh scripts/build-dist.sh`（先执行 `clean.sh` 再 `python -m build`，输出在 `dist/`）
- **源码 zip**：`git archive -o webtest-mcp-server.zip HEAD`  
  `.gitattributes` 已设置 `export-ignore`，自动排除 `__pycache__`、`.pytest_cache`、`artifacts`
- 避免双层嵌套：打包时务必在**项目根目录**执行，勿在上层目录对 `webtest-mcp-server` 文件夹整体打 zip

## Docker

```bash
docker build -t webtest-mcp-server .
docker run --rm webtest-mcp-server
```
