"""Excel 用例加载 - 支持自然语言步骤"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Union

from openpyxl import load_workbook

# 表头别名（支持中英文）
HEADERS = {
    "case_id": ("case_id", "用例id", "用例ID", "编号"),
    "title": ("title", "标题", "用例名", "用例标题"),
    "step_no": ("step_no", "step_no", "步骤", "步骤号"),
    "description": ("description", "步骤描述", "操作步骤", "描述", "步骤说明"),
    "expected": ("expected", "期望结果", "预期结果", "预期"),
    "action": ("action", "action", "动作", "操作"),
    "target": ("target", "target", "目标", "元素"),
    "value": ("value", "value", "值", "输入值"),
    "tags": ("tags", "tags", "标签"),
}


@dataclass
class CaseStep:
    """单步（自然语言）"""
    step_no: int
    description: str  # 自然语言描述
    expected: str = ""


@dataclass
class ExcelCase:
    """用例（供 AI 消费）"""
    case_id: str
    title: str
    steps: List[CaseStep]
    tags: str = ""


def _normalize_header(cell_value: Any) -> str:
    s = str(cell_value).strip().lower() if cell_value is not None else ""
    return s


def _find_header_cols(row: list) -> dict[str, int]:
    """精确匹配表头（忽略大小写），避免「步骤」误匹配「步骤描述」"""
    cols: dict[str, int] = {}
    alias_set = {a.lower(): key for key, aliases in HEADERS.items() for a in aliases}
    for idx, cell in enumerate(row):
        v = _normalize_header(cell)
        if v and v in alias_set:
            key = alias_set[v]
            if key not in cols:  # 首次命中
                cols[key] = idx
    return cols


def _get_cell(row: tuple, cols: dict[str, int], key: str) -> Any:
    if key not in cols:
        return None
    idx = cols[key]
    if idx >= len(row):
        return None
    return row[idx]


def load_excel_cases(excel_path: Union[str, Path]) -> List[ExcelCase]:
    """
    从 Excel 加载用例，返回自然语言格式。
    支持两种格式：
    1. 自然语言：步骤描述 + 期望结果
    2. 结构化：action + target + value（会拼接成自然语言描述）
    """
    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel 文件不存在: {path}")

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    if ws is None:
        raise ValueError("Excel 没有活动工作表")

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Excel 为空")

    header_cols = _find_header_cols(rows[0])
    has_desc = "description" in header_cols
    has_action = "action" in header_cols
    if not has_desc and not has_action:
        raise ValueError("Excel 需包含「步骤描述」或「action」列")

    cases_map: dict[str, ExcelCase] = {}
    for row in rows[1:]:
        if not row or all(cell is None or (isinstance(cell, str) and not str(cell).strip()) for cell in row):
            continue

        # 自然语言格式
        desc = str(_get_cell(row, header_cols, "description") or "").strip()
        expected = str(_get_cell(row, header_cols, "expected") or "").strip()

        # 结构化格式 -> 拼接为自然语言
        if not desc and has_action:
            action = str(_get_cell(row, header_cols, "action") or "").strip()
            target = str(_get_cell(row, header_cols, "target") or "").strip()
            value = str(_get_cell(row, header_cols, "value") or "").strip()
            if action:
                parts = [a for a in [action, target, value] if a]
                desc = " ".join(parts)

        if not desc:
            continue

        case_id = str(_get_cell(row, header_cols, "case_id") or "").strip() or "default"
        title = str(_get_cell(row, header_cols, "title") or "").strip()
        tags = str(_get_cell(row, header_cols, "tags") or "").strip()
        step_no_val = _get_cell(row, header_cols, "step_no")
        try:
            step_no = int(step_no_val) if step_no_val is not None else 0
        except (TypeError, ValueError):
            step_no = 0

        step = CaseStep(step_no=step_no, description=desc, expected=expected)
        if case_id not in cases_map:
            cases_map[case_id] = ExcelCase(case_id=case_id, title=title, steps=[], tags=tags)
        cases_map[case_id].steps.append(step)

    wb.close()

    for case in cases_map.values():
        case.steps.sort(key=lambda s: s.step_no)

    return list(cases_map.values())


def filter_cases_by_tags(cases: List[ExcelCase], tags: Optional[List[str]]) -> List[ExcelCase]:
    """按 tags 过滤用例，只保留至少包含一个指定 tag 的用例"""
    if not tags:
        return cases
    tag_set = set(t.strip().lower() for t in tags if t)
    return [c for c in cases if tag_set & set(t.strip().lower() for t in c.tags.split(",") if t.strip())]
