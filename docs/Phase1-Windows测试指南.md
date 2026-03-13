# Phase 1 Windows 测试指南

在 Windows 上验证 webtest-mcp-server 第一阶段功能。

## 前置条件

- Python 3.10 ~ 3.12（建议 3.10 或 3.11，项目要求 `>=3.10`。3.14 等过新版本可能存在兼容问题，若遇错可尝试 3.11）
- 能访问外网（Playwright 需下载 Chromium，登录用例需访问 the-internet.herokuapp.com）

## 1. 安装

```cmd
cd webtest-mcp-server
pip install -e .
playwright install chromium
```

若 `playwright install chromium` 失败，可尝试：

```cmd
playwright install
```

或指定系统代理（如有）：

```cmd
set HTTPS_PROXY=http://代理地址:端口
playwright install chromium
```

## 2. 设置 PYTHONPATH（Windows CMD）

```cmd
set PYTHONPATH=src
```

每次新开 CMD 窗口都需要执行，或在当前窗口执行后保持该窗口不关。

## 3. Phase 1 测试项

### 测试 1：单元测试（不需要浏览器）

```cmd
set PYTHONPATH=src
python -m pytest tests/test_config.py tests/test_loader.py tests/test_validator.py tests/test_utils.py -v
```

> 使用 `python -m pytest` 确保使用当前 Python 环境执行，避免多 Python 安装时用错版本（如误用 3.7 的 pytest）。

**预期**：全部通过。

### 测试 2：冒烟测试（需要浏览器，无需外网）

```cmd
set PYTHONPATH=src
python scripts/run_smoke.py
```

**预期**：输出类似 `项目: demo, 加载 1 个用例...`，`总数: 1, 通过: 1, 失败: 0`。

### 测试 3：登录用例（需要浏览器 + 外网）

```cmd
set PYTHONPATH=src
python scripts/run_suite.py demo login_cases.xlsx
```

**预期**：能访问 the-internet.herokuapp.com 并完成用例，输出执行结果。

### 测试 4：MCP 工具（可选）

启动 MCP 服务，在 Cursor 中配置 webtest-mcp 后调用：

- `list_projects`：应返回 demo 项目
- `validate_suite`：project=demo, excel_path=login_cases.xlsx
- `run_excel_suite`：project=demo, excel_path=smoke_cases.xlsx

---

## 最简验证

若时间有限，至少跑通 **测试 1** 和 **测试 2** 即可认为 Phase 1 基本正常：

1. 单元测试全部通过 → loader、config、validator 正常  
2. 冒烟测试通过 → Playwright 执行链路正常
