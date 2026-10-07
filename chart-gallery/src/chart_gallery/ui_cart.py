# -*- coding: utf-8 -*-
"""选图车对话框：应用内管理选中的图——移出所选/清空/一键复制全部 AI 请求/打开文件。"""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
                               QPushButton, QMessageBox, QApplication)

from . import cart, library


class CartDialog(QDialog):
    def __init__(self, cfg, on_changed=None, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.on_changed = on_changed
        self.setWindowTitle("选图车")
        self.resize(640, 560)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 14)
        lay.setSpacing(10)

        tip = QLabel("选中的图会写入库里的 _选图车.md；AI 会话从这里接单。双击条目移出。")
        tip.setObjectName("source")
        tip.setWordWrap(True)
        lay.addWidget(tip)

        self.listw = QListWidget()
        lay.addWidget(self.listw, 1)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        b_copy = QPushButton("复制全部 AI 请求")
        b_copy.clicked.connect(self._copy_all)
        b_del = QPushButton("移出所选")
        b_del.setObjectName("secondary")
        b_del.clicked.connect(self._remove_selected)
        b_clear = QPushButton("清空")
        b_clear.setObjectName("secondary")
        b_clear.clicked.connect(self._clear)
        b_file = QPushButton("打开文件")
        b_file.setObjectName("secondary")
        b_file.clicked.connect(self._open_file)
        for b in (b_copy, b_del, b_clear, b_file):
            btns.addWidget(b)
        btns.addStretch()
        b_close = QPushButton("关闭")
        b_close.setObjectName("secondary")
        b_close.clicked.connect(self.accept)
        btns.addWidget(b_close)
        lay.addLayout(btns)

        self._refresh()

    def _refresh(self):
        self.listw.clear()
        for name in cart.entries(self.cfg["lib_dir"]):
            self.listw.addItem(name)
        if not self.listw.count():
            self.listw.addItem("（暂无——在图表详情页点 ★ 收藏加入）")
            self.listw.item(0).setFlags(Qt.NoItemFlags)

    def _selected_name(self):
        it = self.listw.currentItem()
        return it.text() if it and not (it.flags() & Qt.ItemFlag.ItemIsSelectable) == 0 else None

    def _remove_selected(self):
        it = self.listw.currentItem()
        if not it or it.text().startswith("（暂无"):
            return
        if cart.remove(self.cfg["lib_dir"], it.text()):
            self._refresh()
            if self.on_changed:
                self.on_changed()

    def _clear(self):
        if cart.count(self.cfg["lib_dir"]) and QMessageBox.question(
                self, "清空选图车", "确定清空全部选图？") == QMessageBox.Yes:
            cart.clear(self.cfg["lib_dir"])
            self._refresh()
            if self.on_changed:
                self.on_changed()

    def _copy_all(self):
        names = cart.entries(self.cfg["lib_dir"])
        if not names:
            self._show_nothing()
            return
        by_name = {e.name or e.stem: e for e in library.load_library(self.cfg["lib_dir"])}
        parts = ["请按选图车里的图表逐一处理我的数据："]
        missing = []
        for i, name in enumerate(names, 1):
            e = by_name.get(name)
            if not e:
                missing.append(name)
                continue
            parts.append(f"\n—— {i}. {e.name} ——\n【数据契约】{e.contract}\n"
                         f"【模板代码】\n```python\n{e.code}\n```")
        parts.append("\n我的数据如下；请先逐条核对数据契约，不满足的告诉我缺什么，"
                     "满足的改写模板出成品（全中文、图内无标题、代码可复现）。")
        if missing:
            parts.append(f"\n（注：以下条目在库中未找到，请忽略或告知：{'、'.join(missing)}）")
        QApplication.clipboard().setText("\n".join(parts))
        QMessageBox.information(self, "已复制",
                                f"已复制 {len(names) - len(missing)} 张图的 AI 请求，粘贴到会话即可。")

    def _show_nothing(self):
        QMessageBox.information(self, "选图车为空", "先在图表详情页点 ★ 收藏。")

    def _open_file(self):
        import os
        try:
            os.startfile(str(Path(self.cfg["lib_dir"]) / "_选图车.md"))
        except OSError:
            pass
