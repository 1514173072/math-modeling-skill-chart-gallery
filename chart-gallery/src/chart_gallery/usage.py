# -*- coding: utf-8 -*-
"""使用记录：记录查看/复制/渲染频次，支撑侧栏"★ 常用"智能分组。存 exe 旁 json，不入 vault。"""
import json
from datetime import datetime
from pathlib import Path

from . import config

WEIGHT = {"view": 1, "star": 1, "copy": 2, "render": 3}
FIELDS = {"view": "views", "copy": "copies", "render": "renders", "star": "stars"}


def _path() -> Path:
    return config.app_dir() / "图表库使用记录.json"


def load() -> dict:
    p = _path()
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    return {}


def save(d: dict) -> None:
    try:
        _path().write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def record(stem: str, kind: str) -> None:
    if kind not in WEIGHT:
        return
    d = load()
    e = d.setdefault(stem, {"score": 0, "views": 0, "copies": 0,
                            "renders": 0, "stars": 0, "last": ""})
    e["score"] = e.get("score", 0) + WEIGHT[kind]
    e[FIELDS[kind]] = e.get(FIELDS[kind], 0) + 1
    e["last"] = datetime.now().isoformat(timespec="seconds")
    save(d)


def top(n: int = 6) -> list[str]:
    """按加权分取最常用的条目 stem，降序；无记录返回空。"""
    d = load()
    scored = [(v.get("score", 0), k) for k, v in d.items() if v.get("score", 0) > 0]
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [k for _, k in scored[:n]]
