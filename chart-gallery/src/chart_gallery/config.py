# -*- coding: utf-8 -*-
"""配置：库路径与解释器路径，存 exe 旁的 json，开箱即用可改。"""
import json
import os
import sys
from pathlib import Path

DEFAULTS = {
    "lib_dir": os.environ.get(
        "CHART_GALLERY_LIB_DIR",
        str(Path(__file__).resolve().parents[2] / "library"),
    ),
    "python": os.environ.get("CHART_GALLERY_PYTHON", sys.executable),
    "last_tab": 0,
    "last_category": "",
    "geometry": None,
}


def app_dir() -> Path:
    override = os.environ.get("CHART_GALLERY_APP_DIR")
    if override:
        return Path(override)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[2]


def config_path() -> Path:
    return app_dir() / "图表库配置.json"


def load() -> dict:
    cfg = dict(DEFAULTS)
    p = config_path()
    if p.exists():
        try:
            cfg.update(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def save(cfg: dict) -> None:
    try:
        config_path().write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
    except Exception:
        pass
