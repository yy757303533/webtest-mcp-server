# webtest-mcp-server 测试步骤

项目支持 **Windows、macOS、Linux**。本文档说明如何在本机完成验证，测试通过后可对接你的 Web 项目。

---

## 一、环境准备

### 1.1 前置条件

- **Python 3.10 ~ 3.12**（项目要求 `>=3.10`）
- **pip**（随 Python 安装）
- 终端：CMD / PowerShell（Windows）或 Terminal（macOS/Linux）

### 1.2 安装项目

```bash
cd webtest-mcp-server
pip install -e .
```

> 所有平台命令相同。

---

## 二、设置 PYTHONPATH

每次新开终端都需要执行，或保持该终端不关。

| 平台 | 命令 |
|------|------|
| **Windows CMD** | `set PYTHONPATH=src` |
| **Windows PowerShell** | `$env:PYTHONPATH = "src"` |
| **macOS / Linux (bash/zsh)** | `export PYTHONPATH=src` |

---

## 三、测试步骤

### 步骤 1：创建示例 Excel

```bash
python scripts/create_demo_excel.py
```

预期：`已创建: projects/demo/cases.xlsx`（Windows 下可能显示 `projects\demo\cases.xlsx`）

### 步骤 2：单元测试（config、loader）

```bash
python -m pytest tests/test_config.py tests/test_loader.py -v
```

预期：`2 passed` 或 `4 passed`（视 cases.xlsx 是否存在）

### 步骤 3：列出用例

```bash
python scripts/list_cases.py demo cases.xlsx
```

预期：输出 JSON，含 `project`、`base_url`、`cases` 列表。

### 步骤 4：启动 MCP 服务

```bash
webtest-mcp
```

或：

```bash
python -m webtest_mcp.server
```

预期：服务启动，等待 MCP 客户端连接（无报错即成功）。

> 按 `Ctrl+C`（所有平台）停止服务。

### 步骤 5：保存结果接口（可选）

```bash
python scripts/test_save_results.py
```

> 需已安装 mcp（`pip install -e .`）

预期：输出 `"success": true`，并生成 `artifacts/demo/result.json`、`artifacts/demo/report.md`。

---

## 四、全量测试

先设置 PYTHONPATH，再执行：

```bash
python -m pytest tests/ -v
```

**macOS / Linux：**
```bash
export PYTHONPATH=src
python -m pytest tests/ -v
```

**Windows CMD：**
```cmd
set PYTHONPATH=src
python -m pytest tests/ -v
```

**Windows PowerShell：**
```powershell
$env:PYTHONPATH = "src"
python -m pytest tests/ -v
```

预期：`test_config`、`test_loader` 通过；`test_save_test_results` 在已安装 `mcp` 时通过，否则跳过。

---

## 五、对接你的 Web 项目

测试通过后，按以下步骤接入：

1. **新建项目目录**：`projects/<你的项目名>/`
2. **创建 project.yaml**（含 `base_url`）
3. **准备 Excel 用例**，放入 `projects/<你的项目名>/xxx.xlsx`
4. **配置 Cursor MCP**：webtest-mcp + playwright-mcp
5. **在 Cursor 中执行**：对 AI 说「执行 `<项目名>` 的 `xxx.xlsx`」

---

## 六、常见问题

| 问题 | 处理 |
|------|------|
| `ModuleNotFoundError: No module named 'mcp'` | 执行 `pip install -e .` |
| `FileNotFoundError: Excel 文件不存在` | 先运行 `python scripts/create_demo_excel.py` |
| `项目 demo 不存在` | 确保 `projects/demo/project.yaml` 存在 |
| Windows CMD 中 `python` 不存在 | 使用 `py -3` 或配置 Python 到 PATH |
| macOS/Linux 中 `python` 指向 2.x | 使用 `python3` |
