---
name: case-generator
description: 分析需求文档，生成结构化手工测试用例并写入 Excel 文件。工具：generate_cases（webtest-mcp）。
---

# 子流程 A：需求文档 → Excel 用例

## 工具
- `list_projects_tool` — 确认项目存在
- `generate_cases` — 写入 Excel（webtest-mcp 提供）

---

## 步骤

### Step 1：确认项目

```
list_projects_tool()
```

找到目标项目 key（如 `huudi`）。若不存在，提示用户先在 `projects/` 下创建项目目录和 `project.yaml`。

### Step 2：分析需求文档，构建用例列表

逐章节阅读需求文档，按以下 5 种类型拆解用例：

| 类型 | 说明 | 典型场景 |
|------|------|----------|
| 功能测试 | 主流程正向验证 | 用户能正常注册、登录、投资 |
| 输入校验 | 必填、格式、长度 | 邮箱格式错误、密码太短 |
| 边界值 | 最小/最大/刚好超出 | 输入 1 字符、50 字符、51 字符 |
| 状态机 | 状态转换和权限控制 | KYC 各状态下按钮行为 |
| 安全性 | XSS、SQL 注入、越权 | 注入脚本、DROP TABLE |

**用例字段规范**：

```
case_id:       项目前缀-T四位编号，如 HUUDI-T0001（全局唯一，连续递增）
module:        对应需求章节，如"用户注册和登录"
test_type:     功能测试 / 输入校验 / 边界值 / 状态机 / 安全性测试
title:         模块-场景-条件，如"Email-格式无效拒绝"
precondition:  P1. xxx\nP2. xxx（用 \n 分隔，没有则留空）
steps:         S1. xxx\nS2. xxx（具体操作，动词开头）
expected:      E1. xxx\nE2. xxx（可验证的结果，不写"应该"）
priority:      高（核心流程）/ 中（常规功能）/ 低（边界/安全）
tags:          逗号分隔，如"输入校验,必填,邮箱"
```

**覆盖要点**（以 Huudi 类投资平台为例）：
- 注册：每个必填字段的空值/边界/格式/特殊字符
- 登录：正向、错误密码、第三方登录（Google/Facebook）
- KYC：5 种状态（未处理/已上传待审/已批准/已拒绝/IBAN 已填）下的按钮行为
- 投资：触发 KYC 弹窗、最小投资金额、过额认购
- 项目页：Tab 访问权限（未登录 vs 已登录）

### Step 3：调用 generate_cases

```python
generate_cases(
    project="huudi",
    cases=[
        {
            "case_id": "HUUDI-T0001",
            "module": "用户注册和登录",
            "test_type": "输入校验",
            "title": "First Name-空值拒绝",
            "precondition": "P1. 用户在注册页面\nP2. 页面已完全加载",
            "steps": "S1. 将「First Name」留空\nS2. 点击提交按钮",
            "expected": "E1. 空值输入被拒绝\nE2. 显示错误提示：\"该字段为必填项\"\nE3. 无法提交表单",
            "priority": "高",
            "tags": "输入校验,必填,空值"
        },
        # ... 更多用例
    ],
    output_filename="huudi_cases_v1.xlsx"
)
```

### Step 4：输出摘要

生成成功后，向用户报告：

```
已生成 XX 条用例 → projects/huudi/huudi_cases_v1.xlsx

模块分布：
  用户注册和登录：XX 条（高 X / 中 X / 低 X）
  KYC验证：XX 条
  投资流程：XX 条

下一步：说"执行 huudi_cases_v1.xlsx"即可开始自动化测试。
```

---

## 质量检查清单

生成前自检：
- [ ] case_id 全局唯一、连续
- [ ] steps 每步以动词开头（点击、输入、留空、跳转）
- [ ] expected 每条可客观验证（不写"界面友好"）
- [ ] 每个模块至少有 1 条高优先级的主流程用例
- [ ] 状态机场景：KYC 5 种状态都覆盖
