"""页面爬取 - 提取可交互元素，生成 selectors 候选"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import async_playwright

from .config import get_projects_dir, load_selectors


# 页面内执行的 JS：提取可交互元素
_EXTRACT_SCRIPT = """
() => {
  const sel = 'input, button, select, textarea, a[href], [role="button"], [role="link"]';
  const els = document.querySelectorAll(sel);
  const results = [];
  for (const el of els) {
    const tag = el.tagName.toLowerCase();
    const id = el.id || '';
    const name = el.getAttribute('name') || '';
    const type = el.getAttribute('type') || '';
    const placeholder = (el.getAttribute('placeholder') || '').slice(0, 50);
    const dataTestid = el.getAttribute('data-testid') || '';
    const ariaLabel = (el.getAttribute('aria-label') || '').slice(0, 80);
    const text = (el.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 50);
    const href = el.getAttribute('href') || '';
    if (tag === 'a' && !href && !text) continue;
    results.push({
      tag, id, name, type, placeholder, dataTestid, ariaLabel, text, href
    });
  }
  return results;
}
"""


@dataclass
class ElementCandidate:
    """单个元素的候选 selector"""
    key: str
    locator: str
    tag: str
    hint: str = ""


def _make_key(tag: str, name: str, base: str = "") -> str:
    """生成语义 key，避免重复和非法字符"""
    s = (base or f"{tag}_{name}").strip()
    s = re.sub(r"[^a-zA-Z0-9_\u4e00-\u9fa5]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "element"


def _escape_attr(v: str) -> str:
    """属性值转义，用于 CSS/Playwright"""
    return v.replace('\\', '\\\\').replace('"', '\\"')


def _pick_locator(row: dict[str, Any], index: int) -> tuple[str, str, str]:
    """
    按优先级选择 locator 和 key
    返回 (locator, key, hint)
    """
    tag = row.get("tag", "div")
    tid = (row.get("id") or "").strip()
    name = (row.get("name") or "").strip()
    placeholder = (row.get("placeholder") or "").strip()
    data_testid = (row.get("dataTestid") or "").strip()
    aria_label = (row.get("ariaLabel") or "").strip()
    text = (row.get("text") or "").strip()
    href = (row.get("href") or "").strip()

    suffix = f"_{index}" if index > 0 else ""

    # 1. data-testid（最稳定）
    if data_testid:
        loc = f'[data-testid="{_escape_attr(data_testid)}"]'
        key = _make_key(tag, data_testid, data_testid) + suffix
        return loc, key, f"data-testid={data_testid}"

    # 2. id（避免纯数字开头）
    if tid and not re.match(r"^[0-9]", tid):
        loc = f"#{tid}" if re.match(r"^[a-zA-Z_][\w-]*$", tid) else f'[id="{_escape_attr(tid)}"]'
        key = _make_key(tag, tid, f"{tag}_{tid}") + suffix
        return loc, key, f"id={tid}"

    # 3. name（表单元素）
    if name and tag in ("input", "select", "textarea"):
        loc = f'{tag}[name="{_escape_attr(name)}"]'
        key = _make_key(tag, name, f"{tag}_{name}") + suffix
        return loc, key, f"name={name}"

    # 4. placeholder（输入框）
    if placeholder and tag == "input":
        loc = f'input[placeholder="{_escape_attr(placeholder)}"]'
        key = _make_key(tag, placeholder[:20], f"input_{placeholder[:15]}") + suffix
        return loc, key, f"placeholder={placeholder[:30]}"

    # 5. aria-label
    if aria_label:
        loc = f'[aria-label="{_escape_attr(aria_label)}"]'
        key = _make_key(tag, aria_label[:25], f"aria_{aria_label[:20]}") + suffix
        return loc, key, f"aria-label={aria_label[:40]}"

    # 6. 按钮/链接的文本
    if text and tag in ("button", "a"):
        short = text[:30].replace('"', "'")
        loc = f'{tag}:has-text("{_escape_attr(short)}")'
        key = _make_key(tag, text[:15], f"btn_{text[:15]}") + suffix
        return loc, key, f"text={short}"

    # 7. 链接 href
    if href and tag == "a":
        short = href[:50]
        loc = f'a[href*="{_escape_attr(short[:40])}"]'
        key = _make_key(tag, short[:20], "link") + suffix
        return loc, key, f"href={short}"

    return "", "", ""


async def extract_elements(
    url: str,
    wait_until: str = "domcontentloaded",
    timeout_ms: int = 15000,
) -> list[ElementCandidate]:
    """
    打开 URL，提取可交互元素，返回候选 selectors
    """
    results: list[ElementCandidate] = []
    seen_keys: set[str] = set()
    key_count: dict[str, int] = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            rows = await page.evaluate(_EXTRACT_SCRIPT)
        finally:
            await browser.close()

    for i, row in enumerate(rows):
        loc, key, hint = _pick_locator(row, 0)
        if not loc:
            continue
        # 去重 key
        if key in seen_keys:
            key_count[key] = key_count.get(key, 0) + 1
            key = f"{key}_{key_count[key]}"
        seen_keys.add(key)
        results.append(ElementCandidate(key=key, locator=loc, tag=row.get("tag", ""), hint=hint))

    return results


def merge_into_selectors(
    project_key: str,
    candidates: list[ElementCandidate],
    merge_mode: str = "append",
) -> Path:
    """
    将候选合并进 selectors.yaml
    merge_mode: "append" 追加不覆盖, "overwrite" 全量覆盖
    """
    from .config import get_projects_dir

    projects_dir = get_projects_dir()
    project_dir = projects_dir / project_key
    project_dir.mkdir(parents=True, exist_ok=True)
    selectors_path = project_dir / "selectors.yaml"

    existing = load_selectors(project_key) if selectors_path.exists() else {}
    merged: dict[str, str] = {}
    if merge_mode == "append":
        merged = {k: (v[0] if v else "") for k, v in existing.items() if v}
    for c in candidates:
        merged[c.key] = c.locator

    import yaml
    with open(selectors_path, "w", encoding="utf-8") as f:
        f.write("# 语义 key -> locator 映射（由 extract_page_elements 生成）\n")
        yaml.dump(merged, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return selectors_path
