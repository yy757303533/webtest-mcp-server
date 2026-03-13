# Phase 2：页面爬取（extract_page_elements）

半自动从页面提取可交互元素，生成 selectors 候选并合并进 `selectors.yaml`。

---

## Windows 验证步骤

### 前置

- Phase 1 已通过（单元测试、冒烟、Playwright 可用）
- 需外网访问 `https://the-internet.herokuapp.com`

### 1. 单元测试

```cmd
set PYTHONPATH=src
python -m pytest tests/test_crawler.py -v
```

**预期**：4 passed

### 2. 仅爬取（不写入）

```cmd
set PYTHONPATH=src
python scripts/extract_elements.py -p demo -u https://the-internet.herokuapp.com/login
```

**预期**：输出若干候选元素，如 `input_username`, `input_password`, `btn_登录` 等，无报错

### 3. 爬取并合并

```cmd
set PYTHONPATH=src
python scripts/extract_elements.py -p demo -u https://the-internet.herokuapp.com/login --merge
```

**预期**：打印候选 + `已合并到: ...\projects\demo\selectors.yaml`，打开该文件可见新增 key

### 4. 合并后验证

```cmd
set PYTHONPATH=src
python scripts/extract_elements.py -p demo -u https://the-internet.herokuapp.com/login --merge --verify --excel login_cases.xlsx
```

**预期**：`valid: True` 或仅有 warnings，无 errors

### 5. MCP 工具（可选）

在 Cursor/Claude 中请求：「用 webtest-mcp 的 extract_page_elements 爬取 demo 的 https://the-internet.herokuapp.com/login」

**预期**：AI 调用工具并返回 elements 列表

---

## 使用方式

### 1. CLI

```bash
# 仅爬取，打印候选（不写入文件）
python scripts/extract_elements.py -p demo -u https://the-internet.herokuapp.com/login

# 爬取并合并到 selectors.yaml
python scripts/extract_elements.py -p demo -u https://the-internet.herokuapp.com/login --merge

# 合并后运行 validate 验证
python scripts/extract_elements.py -p demo -u https://the-internet.herokuapp.com/login --merge --verify --excel login_cases.xlsx
```

Windows CMD：

```cmd
set PYTHONPATH=src
python scripts/extract_elements.py -p demo -u https://the-internet.herokuapp.com/login --merge
```

### 2. MCP 工具

在 Cursor/Claude 中调用 `extract_page_elements`：

- `project`: 项目 key
- `url`: 页面 URL
- `merge`: 是否合并到 selectors.yaml（默认 false）
- `merge_mode`: `append`（追加）或 `overwrite`（覆盖）
- `verify`: 合并后是否运行 validate_suite
- `excel_path`: 验证时使用的 Excel 路径

## 提取规则

按以下优先级生成 locator：

1. `data-testid`（最稳定）
2. `id`
3. `name`（表单元素）
4. `placeholder`（输入框）
5. `aria-label`
6. 按钮/链接文本
7. 链接 `href`

提取元素类型：`input`、`button`、`select`、`textarea`、`a[href]`、`[role=button]`、`[role=link]`。

## 合并模式

- **append**：保留已有 selectors，只追加新 key
- **overwrite**：用本次爬取结果覆盖整个 selectors.yaml

## 验证

`--verify` 会爬取并合并后，用 `validate_suite` 检查指定 Excel 中的 target 是否都在 selectors 中定义。

---

## 最简验证

至少跑通 **步骤 1 + 步骤 2** 即可认为 Phase 2 基本正常：

1. 单元测试全部通过 → crawler 逻辑正确  
2. 爬取成功并打印候选 → Playwright 提取链路正常
