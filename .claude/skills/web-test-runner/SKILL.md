---
name: web-test-runner
description: 根据 Excel 自然语言测试用例，使用 webtest-mcp 读取用例、playwright-mcp 操作浏览器，自动执行 Web UI 测试。当用户要求执行测试用例、跑自动化测试、验证 Web 功能、执行 Excel 用例时触发。
---

# Web 测试用例执行

AI 作为决策者，读取自然语言用例后，实时调用 playwright-mcp 操作浏览器执行测试。

## 前置条件

- **webtest-mcp**：读取 Excel 用例（list_projects, get_excel_cases）
- **playwright-mcp**：操作浏览器（browser_navigate, browser_snapshot, browser_click, browser_type, browser_fill_form 等）

两个 MCP 需在 Claude Code 中已配置。

## 执行流程

```
1. 获取用例 → 2. 逐条执行 → 3. 汇总报告
```

### Step 1：获取用例

调用 webtest-mcp 的 **get_excel_cases**：

- `project`：项目 key（可先调用 list_projects 查看）
- `excel_path`：Excel 文件路径，如 `login_cases.xlsx`
- `tags`（可选）：按标签过滤，如 `["smoke"]`

返回：`base_url`、`cases`（含 case_id, title, steps: [{step_no, description, expected}]）

### Step 2：逐条执行

对每个用例的每个步骤：

1. **解析自然语言**：理解 description 中的操作（打开页面、输入、点击、验证等）
2. **操作前先 snapshot**：调用 **browser_snapshot** 查看当前页面结构，确定元素 ref 或 selector
3. **执行操作**：
   - 打开/跳转页面 → **browser_navigate**（url 用 base_url 拼接相对路径）
   - 点击 → **browser_click**（ref 或 selector）
   - 输入 → **browser_type** 或 **browser_fill_form**
   - 验证 → 先 **browser_snapshot** 再判断 expected 是否满足

4. **遇到意外**：弹窗、加载慢、元素找不到 → 自行判断处理

### Step 3：汇总报告并持久化

调用 **save_test_results**（project, results, excel_path），保存到 artifacts/project/。输出汇总表格给用户。

## 关键规则

- 每次操作前 snapshot，用 ref 或 role/accessibleName 定位
- expected 校验：执行后 snapshot 检查页面是否包含预期内容
- 失败时可 browser_screenshot 留证
