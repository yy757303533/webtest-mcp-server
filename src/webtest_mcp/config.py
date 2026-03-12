"""项目配置加载 - project.yaml, selectors.yaml"""

from pathlib import Path
from typing import Any, Optional

import yaml


def get_projects_dir() -> Path:
    """获取 projects 目录"""
    current = Path(__file__).resolve().parent.parent.parent
    candidates = [
        current / "projects",
        Path.cwd() / "projects",
        Path.cwd() / "webtest-mcp-server" / "projects",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


def load_project_config(project_key: str) -> dict[str, Any]:
    """加载 project.yaml"""
    projects_dir = get_projects_dir()
    project_dir = projects_dir / project_key
    config_path = project_dir / "project.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"项目 {project_key} 的 project.yaml 不存在: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("project.yaml 必须是 YAML 对象")
    data["_project_dir"] = str(project_dir)
    return data


def load_selectors(project_key: str) -> dict[str, list[str]]:
    """加载 selectors.yaml，返回 key -> [locator, ...]"""
    projects_dir = get_projects_dir()
    project_dir = projects_dir / project_key
    selectors_path = project_dir / "selectors.yaml"
    if not selectors_path.exists():
        return {}
    with open(selectors_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return {}
    result: dict[str, list[str]] = {}
    for key, val in data.items():
        if isinstance(val, str):
            result[str(key)] = [val.strip()]
        elif isinstance(val, list):
            result[str(key)] = [str(v).strip() for v in val if v]
        else:
            result[str(key)] = []
    return result


def list_projects() -> list[str]:
    """列出所有已配置的项目"""
    projects_dir = get_projects_dir()
    if not projects_dir.exists():
        return []
    result = []
    for item in projects_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            if (item / "project.yaml").exists():
                result.append(item.name)
    return sorted(result)
