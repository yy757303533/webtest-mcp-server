"""语义 target → Playwright Locator 解析"""

from typing import Optional

from .config import load_selectors


def resolve_locator(project_key: str, target: str) -> Optional[str]:
    """
    将语义 target 解析为 Playwright 可用的 locator 字符串。
    优先从 selectors.yaml 查找，若不存在则把 target 当作原始 locator（支持 role=, text=, css=, #id 等）
    """
    if not target or not target.strip():
        return None
    target = target.strip()
    selectors = load_selectors(project_key)
    if target in selectors:
        cands = selectors[target]
        return cands[0] if cands else None
    # 直接当作原始 locator
    return target


def _parse_locator(loc: str) -> tuple[str, str]:
    """解析 locator 类型和值，返回 (type, value)"""
    loc = loc.strip()
    if not loc:
        return ("text", "")
    if loc.startswith("role="):
        return ("role", loc[5:].strip())
    if loc.startswith("text="):
        return ("text", loc[5:].strip())
    if loc.startswith("css="):
        return ("css", loc[4:].strip())
    if loc.startswith("xpath="):
        return ("xpath", loc[6:].strip())
    if loc.startswith("#"):
        return ("css", loc)
    if loc.startswith("."):
        return ("css", loc)
    # 默认为 text
    return ("text", loc)
