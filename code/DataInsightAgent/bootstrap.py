from __future__ import annotations

import sys
from pathlib import Path


AGENT_DIR = Path(__file__).resolve().parent
VENDOR_DIR = AGENT_DIR / "vendor"


def add_vendor_path() -> None:
    """Python 3.10 可复用旧 vendor；其他版本使用 pip 安装的依赖。"""
    if sys.version_info[:2] != (3, 10):
        return
    vendor = str(VENDOR_DIR)
    if VENDOR_DIR.exists() and vendor not in sys.path:
        sys.path.insert(0, vendor)
