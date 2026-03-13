# webtest-mcp-server

让 AI 根据 Excel 手工用例执行 Web UI 自动化测试的 MCP Server。

## 功能

- **Excel 驱动**：用例写在 Excel，语义 target 映射到 selectors.yaml
- **MCP 工具**：list_projects、validate_suite、run_excel_suite
- **报告**：Allure + result.json（供 AI/CI 消费）
- **项目配置**：project.yaml（base_url、登录）、selectors.yaml

## 安装

```bash
pip install -e .
playwright install chromium
```

## 配置

在 `projects/<project_key>/` 下创建：
- `project.yaml`：base_url、登录配置
- `selectors.yaml`：语义 key → locator 映射
- Excel 用例文件

## 使用

```bash
# MCP 服务
webtest-mcp

# 或
python -m webtest_mcp.server
```

## 开发与验证

```bash
pip install -e ".[dev]"
playwright install chromium

# 单元测试（不需要浏览器）
PYTHONPATH=src pytest tests/test_config.py tests/test_loader.py tests/test_validator.py -v

# Runner 集成测试（需 WEBTEST_RUN_INTEGRATION=1，且系统有 Playwright 依赖如 libgbm）
WEBTEST_RUN_INTEGRATION=1 PYTHONPATH=src pytest tests/test_runner.py -v

# 全量测试
PYTHONPATH=src pytest tests/ -v
```

## 平台支持

- **Windows**：支持。截图文件名已做非法字符过滤（`: * ? " < > |` 等）
- **macOS**：支持
- **Linux**：支持

首次使用需执行 `playwright install chromium`，Playwright 会自动下载对应平台浏览器。

## 快速测试（登录用例）

项目自带 `projects/demo/login_cases.xlsx`，使用 [the-internet.herokuapp.com](https://the-internet.herokuapp.com/login) 公开登录页。

```bash
cd webtest-mcp-server
pip install -e .
playwright install chromium

# 运行登录用例
PYTHONPATH=src python scripts/run_demo.py
```

或直接用 Python 调用：

```bash
cd webtest-mcp-server
PYTHONPATH=src python -c "
import asyncio
from pathlib import Path
from webtest_mcp.loader import load_excel
from webtest_mcp.runner import run_cases

cases = load_excel('projects/demo/login_cases.xlsx')
r, s = asyncio.run(run_cases('demo', cases, base_url_override='https://the-internet.herokuapp.com'))
print(s)
"
```

## Docker（macOS / Linux）

```bash
# 构建
docker build -t webtest-mcp-server .

# 运行 MCP 服务
docker run --rm webtest-mcp-server

# 运行登录用例测试
docker run --rm webtest-mcp-server run-test

# 若需走代理（如公司网络）
docker run --rm -e https_proxy=http://proxy:port -e http_proxy=http://proxy:port webtest-mcp-server run-test
```

## Jenkins

项目包含 `Jenkinsfile`，可在 Jenkins 中创建 Pipeline 任务并指向本仓库。

- **Unit Tests**：无需浏览器
- **Integration Tests**：需设置环境变量 `WEBTEST_RUN_INTEGRATION=1` 且 Jenkins Agent 具备 Playwright 依赖
