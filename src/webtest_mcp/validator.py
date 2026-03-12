"""validate_suite - 预检 Excel、selectors、环境连通性"""

import json
from pathlib import Path
from typing import Any, List, Optional, Union

from .config import load_project_config, load_selectors, list_projects
from .loader import load_excel, VALID_ACTIONS, filter_cases_by_tags


def validate_suite(
    project_key: str,
    excel_path: Union[str, Path],
    tags: Optional[List[str]] = None,
) -> dict:
    """
    预检验证：Excel 格式、selectors 完整性、项目配置。
    返回 { "valid": bool, "errors": [...], "warnings": [...] }
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. 项目存在
    projects = list_projects()
    if project_key not in projects:
        errors.append(f"项目 {project_key} 不存在，可用项目: {', '.join(projects)}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # 2. project.yaml
    try:
        config = load_project_config(project_key)
    except Exception as e:
        errors.append(f"加载 project.yaml 失败: {e}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    base_url = config.get("base_url")
    if not base_url:
        warnings.append("project.yaml 未配置 base_url")

    # 3. Excel
    excel_path = Path(excel_path)
    if not excel_path.is_absolute():
        project_dir = Path(config.get("_project_dir", "."))
        excel_path = project_dir / excel_path
    if not excel_path.exists():
        errors.append(f"Excel 文件不存在: {excel_path}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    try:
        cases = load_excel(excel_path)
    except Exception as e:
        errors.append(f"加载 Excel 失败: {e}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    if tags:
        cases = filter_cases_by_tags(cases, tags)
    if not cases:
        warnings.append("过滤后无用例")

    # 4. selectors 完整性
    selectors = load_selectors(project_key)
    for case in cases:
        for step in case.steps:
            if step.target and step.action in ("click", "fill", "type", "select", "wait_visible", "assert_visible"):
                # 若 target 像是语义 key（不含 = 或特殊符号），检查是否在 selectors 中
                t = step.target.strip()
                if "=" not in t and ">" not in t and t not in selectors:
                    warnings.append(f"用例 {case.case_id} 步骤 {step.step_no}: target '{t}' 未在 selectors.yaml 中定义")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "cases_count": len(cases),
        "project": project_key,
    }
