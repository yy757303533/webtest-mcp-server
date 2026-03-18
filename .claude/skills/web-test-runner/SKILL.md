---
name: web-test-runner
description: 根据 Excel 自然语言测试用例，使用 webtest-mcp 读取用例、playwright-mcp 操作浏览器，自动执行 Web UI 测试。当用户要求执行测试用例、跑自动化测试、验证 Web 功能、执行 Excel 用例时触发。
---

# Web 测试用例执行

AI 作为决策者，读取自然语言用例后，实时调用 playwright-mcp 操作浏览器执行测试。

## 前置条件

- **webtest-mcp**：读取 Excel 用例（list_projects, get_excel_cases, get_grouped_cases, save_test_results）
- **playwright-mcp**：操作浏览器（browser_navigate, browser_snapshot, browser_click, browser_type, browser_fill_form 等）

## 执行流程

```
1. 查看分组概要 → 2. 按模块逐批获取用例 → 3. 逐条执行 → 4. 汇总报告
```

### Step 1：查看分组概要（推荐）

先调用 **get_grouped_cases** 了解全貌：

```
get_grouped_cases(project="xxx", excel_path="xxx.xls")
```

返回按模块分组的用例数量，例如：
- AM模拟器: 65 条
- SPE模拟器: 53 条
- Garde d'enfant模拟器: 41 条

据此决定执行顺序。如用户未指定，从用例最少的模块开始。

### Step 2：按模块获取用例

调用 **get_excel_cases** 获取某模块的完整用例：

```
get_excel_cases(project="xxx", excel_path="xxx.xls", module="SPE模拟器")
```

支持的过滤参数：
- `module`：按模块，如 "SPE模拟器"
- `tags`：按标签，如 ["导航", "CTA"]
- `priorities`：按优先级，如 ["高"]

返回每条用例包含：
- `case_id`、`title`
- `module`：功能模块
- `precondition`：预置条件（P1. P2. 格式）—— **执行前必须先满足**
- `steps`：[{step_no, description, expected}]
- `tags`、`priority`

### Step 3：逐条执行

对每个用例，执行顺序是：**预置条件 → 全部 S 步骤 → 统一验证所有 E**。

S 和 E 不是一一对应的。S 是操作动作，E 是最终验证。先把所有 S 做完，再逐条检查 E。

#### 3a. 处理预置条件（precondition）

预置条件描述了执行前需要满足的状态。格式为 `P1. xxx\nP2. xxx`。

处理策略：
- **页面状态**（如 "P1. 用户在Espace页面"）→ 先导航到对应页面
- **数据前提**（如 "P1. 用户已有至少3个模拟记录"）→ 记录为假设条件，无法操作时标注 `SKIP: 需要预置数据`
- **流程前提**（如 "P1. 完成模拟器并到达结果页"）→ 如果之前的用例已完成该流程，可复用浏览器状态；否则需要先执行该流程
- **时间前提**（如 "P1. 3天内未提出面试邀请"）→ 标注 `SKIP: 时间条件无法模拟`

#### 3b. 执行全部 S 步骤

按 step_no 顺序依次执行所有 S 步骤。**执行期间不做 E 验证**。

对每一步：
1. **先 snapshot**：调用 **browser_snapshot** 查看当前页面
2. **理解操作**：从 description 判断操作类型
3. **执行操作**：

   | 描述中的关键词 | playwright-mcp 操作 |
   |---|---|
   | 点击「xxx」/ 点击 xxx 按钮 | browser_click（用 snapshot 中的 ref 或 accessibleName） |
   | 输入 / 填写 / 在 xxx 中输入 | browser_type 或 browser_fill_form |
   | 打开 / 进入 / 跳转到 xxx 页面 | browser_navigate（base_url + 路径） |
   | 选择 xxx 单选/下拉 | browser_click 对应选项 |
   | 等待 | browser_snapshot 轮询（最多 3 次，间隔 2 秒） |
   | 检查 / 查看 xxx | browser_snapshot（仅观察，不验证，验证在 E 阶段做） |

4. 如果某个 S 步骤执行报错（元素找不到、超时等），记录 `passed: false`，跳过后续 S 和 E

#### 3c. 统一验证所有 E 预期

全部 S 步骤执行成功后，做一次 **browser_snapshot**，然后逐条验证 E：

- **文本校验**（如 "E1. 显示 xxx"）→ 检查页面是否包含该文本
- **状态校验**（如 "E2. 按钮保持禁用状态"）→ 检查元素的 disabled 属性
- **选中校验**（如 "E1. 选项被选中"）→ 检查元素的 checked / aria-selected
- **导航校验**（如 "E1. 跳转到 xxx 页面"）→ 检查当前 URL 或页面标题
- **视觉校验**（如 "布局符合设计"）→ 标注 `SKIP: 需人工视觉验证`
- **颜色校验**（如 "CTA按钮变为绿色"）→ 标注 `SKIP: 需人工颜色验证`

所有 E 都通过 → `passed: true`
任一 E 不通过 → `passed: false, error: "E2 失败: xxx"`

#### 3d. 记录结果

每条用例记录：
- `passed: true` — 所有 S 执行成功 + 所有 E 验证通过
- `passed: false, error: "原因"` — S 执行失败或 E 验证不通过
- `passed: null, error: "SKIP: 原因"` — 无法自动执行，说明原因

### Step 4：汇总报告

每个模块执行完后，调用 **save_test_results** 保存结果：

```
save_test_results(project="xxx", results=[...], excel_path="xxx.xls")
```

向用户输出汇总：

```markdown
## SPE模拟器 - 执行结果

| 用例ID | 标题 | 结果 |
|--------|------|------|
| T0029 | Etape1-选择Métropole | ✅ PASS |
| T0030 | Etape1-未选择时禁用 | ✅ PASS |
| T0031 | UI显示校验 | ⏭️ SKIP（需人工视觉验证）|

**总计**: 53 条，通过 45，失败 3，跳过 5
```

## 关键规则

1. **每次操作前必须 snapshot** — 用 snapshot 的 ref 定位元素，不要猜测 selector
2. **按模块分批执行** — 不要一次加载 198 条用例，按模块逐批获取和执行
3. **预置条件优先处理** — 执行步骤前先确保 precondition 满足
4. **不可执行的标注 SKIP** — 时间条件、视觉验证、数据依赖等无法自动化的，不要硬跑，标注跳过
5. **失败时截图留证** — 调用 browser_screenshot 保存失败现场
6. **法语文本照搬** — 页面上的法语按钮名、提示语照原文匹配，不要翻译

## 示例

用户说："执行 simulator 项目的 Simulator.xls，只跑 SPE模拟器 模块"

1. `get_excel_cases(project="simulator", excel_path="Simulator.xls", module="SPE模拟器")`
2. 获得 53 条用例，每条含 precondition、steps、expected
3. 对 T0029（选择Métropole）：
   - precondition: "用户在通知页面且职位已确定" → 先 navigate 到通知页面
   - **执行 S 步骤**：S1. "点击「Métropole」单选按钮" → snapshot → 找到 Métropole 元素 → click
   - **S 全部完成，开始验证 E**：snapshot 当前页面
   - E1. "选项被选中" → 检查 Métropole 是否处于选中状态 ✅
   - E2. "其他选项取消选中" → 检查其他选项是否未选中 ✅
4. 记录 passed: true
5. 完成后 `save_test_results(...)` 保存
