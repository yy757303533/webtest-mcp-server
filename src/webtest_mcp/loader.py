"""Excel 用例加载 - Excel → DSL"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Union

from openpyxl import load_workbook

# Excel 表头（支持中英文）
HEADERS = {
    "case_id": ("case_id", "用例id", "用例ID"),
    "title": ("title", "标题", "用例名"),
    "step_no": ("step_no", "step_no", "步骤", "步骤号"),
    "action": ("action", "action", "动作", "操作"),
    "target": ("target", "target", "目标", "元素"),
    "value": ("value", "value", "值", "输入值"),
    "tags": ("tags", "tags", "标签"),
    "timeout_ms": ("timeout_ms", "timeout", "超时"),
}

VALID_ACTIONS = {
    "go", "click", "fill", "type", "select", "press",
    "wait_visible", "sleep",
    "assert_text", "assert_visible", "assert_url",
    "screenshot",
}


@dataclass
class Step:
    case_id: str
    title: str
    step_no: int
    action: str
    target: str
    value: str
    tags: str
    timeout_ms: Optional[int]


@dataclass
class Case:
    case_id: str
    title: str
    steps: list[Step]


def _normalize_header(cell_value: Any) -> str:
    s = str(cell_value).strip().lower() if cell_value is not None else ""
    return s


def _find_header_cols(row: list[Any]) -> dict[str, int]:
    cols: dict[str, int] = {}
    for idx, cell in enumerate(row):
        v = _normalize_header(cell)
        for key, aliases in HEADERS.items():
            if key in cols:
                continue
            for alias in aliases:
                if v == alias.lower() or (alias.lower() in v and len(v) < 20):
                    cols[key] = idx
                    break
    return cols


def load_excel(excel_path: Union[str, Path]) -> List[Case]:
    """从 Excel 加载用例，返回 Case 列表"""
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
    if "action" not in header_cols or "target" not in header_cols:
        raise ValueError("Excel 必须包含 action 和 target 列")

    cases_map: dict[str, Case] = {}
    for row in rows[1:]:
        if not row:
            continue
        action_val = _get_cell(row, header_cols, "action")
        if not action_val:
            continue
        action_val = str(action_val).strip().lower()
        if action_val not in VALID_ACTIONS:
            continue

        case_id = str(_get_cell(row, header_cols, "case_id") or "").strip() or "default"
        title = str(_get_cell(row, header_cols, "title") or "").strip()
        step_no_val = _get_cell(row, header_cols, "step_no")
        try:
            step_no = int(step_no_val) if step_no_val is not None else 0
        except (TypeError, ValueError):
            step_no = 0
        target = str(_get_cell(row, header_cols, "target") or "").strip()
        value = str(_get_cell(row, header_cols, "value") or "").strip()
        tags = str(_get_cell(row, header_cols, "tags") or "").strip()
        timeout_val = _get_cell(row, header_cols, "timeout_ms")
        timeout_ms: Optional[int] = None
        if timeout_val is not None:
            try:
                timeout_ms = int(timeout_val)
            except (TypeError, ValueError):
                pass

        step = Step(
            case_id=case_id,
            title=title,
            step_no=step_no,
            action=action_val,
            target=target,
            value=value,
            tags=tags,
            timeout_ms=timeout_ms,
        )

        if case_id not in cases_map:
            cases_map[case_id] = Case(case_id=case_id, title=title, steps=[])
        cases_map[case_id].steps.append(step)

    wb.close()

    # 按 step_no 排序
    for case in cases_map.values():
        case.steps.sort(key=lambda s: s.step_no)

    return list(cases_map.values())


def _get_cell(row: tuple, cols: dict[str, int], key: str) -> Any:
    if key not in cols:
        return None
    idx = cols[key]
    if idx >= len(row):
        return None
    return row[idx]


def filter_cases_by_tags(cases: List[Case], tags: Optional[List[str]]) -> List[Case]:
    """按 tags 过滤用例"""
    if not tags:
        return cases
    tag_set = set(t.strip().lower() for t in tags if t)
    result = []
    for case in cases:
        for step in case.steps:
            step_tags = set(s.strip().lower() for s in step.tags.split(",") if s.strip())
            if tag_set & step_tags or not step.tags:
                result.append(case)
                break
    return result
