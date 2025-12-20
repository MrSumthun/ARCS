# arcs_utils.py
# Handler utilities for ARCS application data
from __future__ import annotations

import json
import os
import tempfile
import sys
import datetime
import re
from typing import Any, Dict, List, Optional


def get_resource_path(rel_path: str) -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.dirname(__file__), rel_path)


def user_data_dir() -> str:
    home = os.path.expanduser("~")
    _userDirectory = os.path.join(home, ".arcsoftware")
    os.makedirs(_userDirectory, exist_ok=True)
    return _userDirectory


def atomic_write_json(path: str, data: Any) -> None:
    dirpath = os.path.dirname(path)
    os.makedirs(dirpath, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmpf:
            json.dump(data, tmpf, indent=4, default=str)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def load_json_file(path: str) -> List[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_json_file(path: str, data: Any) -> None:
    atomic_write_json(path, data)


def create_quote(name: Optional[str] = None) -> Dict[str, Any]:
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "id": int(now.timestamp()),
        "name": name or f"ARCS {now.strftime('%Y-%m-%d')}",
        "created_at": now.isoformat(),
        "items": [],
        "notes": "",
    }


def normalize_quote_name(q: Dict[str, Any]) -> str:
    created_at = q.get("created_at")
    if created_at:
        try:
            dt = datetime.datetime.fromisoformat(created_at)
            date_str = dt.date().isoformat()
        except Exception:
            date_str = str(created_at)[:10]
    else:
        date_str = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

    name = f"ARCS {date_str}"
    po = q.get("po_number")
    if po:
        name = f"{name} [PO:{po}]"
    return name


def safe_filename(name: str, max_len: int = 120) -> str:
    fname = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return fname[:max_len]
