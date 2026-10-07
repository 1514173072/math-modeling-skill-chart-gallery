# -*- coding: utf-8 -*-
"""Portable entry point for the open-source 60-chart browser."""
from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "MathModelingChartGallery"


def package_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def configure() -> Path:
    root = package_root()
    library = root / "library"
    if not library.is_dir():
        raise FileNotFoundError(f"图表资源目录不存在：{library}")

    state_root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / APP_NAME
    state_root.mkdir(parents=True, exist_ok=True)
    os.environ["CHART_GALLERY_APP_DIR"] = str(state_root)
    os.environ["CHART_GALLERY_LIB_DIR"] = str(library)
    os.environ.setdefault("CHART_GALLERY_PYTHON", "python" if getattr(sys, "frozen", False) else sys.executable)
    os.environ["CHART_GALLERY_DISABLE_AI"] = "1"
    os.environ["CHART_GALLERY_TITLE"] = "数学建模高级图表库"
    os.environ["CHART_GALLERY_SUBTITLE"] = "开源分享版 · 60个可复现模板"
    return library


def smoke_test() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from chart_gallery.ui_browse import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    ok = len(window.entries) == 60 and "数学建模高级图表库" in window.windowTitle()
    window.close()
    app.processEvents()
    print(f"SMOKE entries={len(window.entries)} ok={ok}")
    return 0 if ok else 2


def main() -> int:
    root = package_root()
    if not getattr(sys, "frozen", False):
        sys.path.insert(0, str(root / "src"))
    configure()
    if "--smoke-test" in sys.argv:
        return smoke_test()

    from chart_gallery.main import main as start_app
    start_app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
