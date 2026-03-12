"""跨平台工具函数 - 支持 Windows、macOS、Linux"""

import re


# Windows 文件名非法字符: \ / : * ? " < > |
# macOS/Linux 仅不允许 /
_RE_INVALID_FILENAME = re.compile(r'[<>:"/\\|?*]')


def sanitize_filename(name: str) -> str:
    """
    将字符串转为安全的文件名（跨 Windows/macOS/Linux）
    非法字符替换为下划线
    """
    if not name:
        return "unnamed"
    return _RE_INVALID_FILENAME.sub("_", name).strip() or "unnamed"
