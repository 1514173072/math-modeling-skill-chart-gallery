# -*- coding: utf-8 -*-
"""入口：加载 QSS、启动主窗口。"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


def resource_path(name: str) -> Path:
    """兼容 PyInstaller 打包（_MEIPASS）与源码运行。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def main():
    app = QApplication(sys.argv)
    qss = resource_path("style.qss")
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))
    icon = resource_path("icon.png")
    if icon.exists():
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(icon)))
    from .ui_browse import MainWindow
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
