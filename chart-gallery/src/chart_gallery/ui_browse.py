# -*- coding: utf-8 -*-
"""主窗口 v2：双列大卡（窗口≥1240px 内容区升三列）、左栏重排（应用头+维度分段+类别+选图车底条）、定高顶栏。"""
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QRect, QTimer, QFileSystemWatcher
from PySide6.QtGui import QImageReader, QPixmap, QKeySequence, QShortcut
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                               QLineEdit, QPushButton, QListWidget, QButtonGroup,
                               QScrollArea, QFrame, QGridLayout)
from shiboken6 import isValid

from . import config, library, cart, usage
from .ui_cart import CartDialog
from .ui_detail import DetailDialog
from .ui_stats import StatsDialog

PAD, GRID, IMG_H = 16, 16, 200
SIDEBAR_W = 224
DESC_MAX = 56                       # 卡片说明截断字数（约两行）
COL3_MIN = 1240                     # 内容区达到该宽度升三列


def _scaled_pixmap(path: str, box_w: int, box_h: int) -> QPixmap:
    """按比例缩到盒子内（不解码全尺寸）。"""
    r = QImageReader(path)
    s = r.size()
    if not s.isValid() or s.height() <= 0 or s.width() <= 0:
        return QPixmap()
    k = min(box_w / s.width(), box_h / s.height())
    r.setScaledSize(QSize(max(1, int(s.width() * k)), max(1, int(s.height() * k))))
    return QPixmap.fromImageReader(r)


def _truncate(text: str, limit: int = DESC_MAX) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


class Card(QFrame):
    def __init__(self, entry, width: int):
        super().__init__()
        self.entry = entry
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(width, IMG_H + 118)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(7)

        img = QLabel()
        img.setObjectName("cardImg")
        img.setFixedHeight(IMG_H)
        img.setAlignment(Qt.AlignCenter)
        self.img = img
        self._needs_thumb = False
        thumb = entry.path.with_name(f"{entry.stem}_thumb.png")
        fresh = thumb.exists() and (not entry.has_png or
                                    thumb.stat().st_mtime >= entry.png.stat().st_mtime)
        if fresh:
            img.setPixmap(_scaled_pixmap(str(thumb), width - 28, IMG_H))
        elif entry.has_png:
            self._needs_thumb = True               # 无缩略图：后台队列补，避免启动卡顿
        else:
            img.setText("无预览")
        lay.addWidget(img)

        row = QHBoxLayout()
        row.setSpacing(8)
        name = QLabel(_truncate(entry.name, 18))
        name.setObjectName("cardName")
        row.addWidget(name, 1)
        if entry.verified == "已验证":
            badge = QLabel("已验证")
            badge.setObjectName("cardBadge")
        elif entry.verified == "思路参考":
            badge = QLabel("思路")
            badge.setObjectName("cardBadge")
        else:
            badge = QLabel("未验证")
            badge.setObjectName("cardBadgeBad")
        row.addWidget(badge, 0, Qt.AlignVCenter)
        lay.addLayout(row)

        desc = QLabel(_truncate(entry.desc))
        desc.setObjectName("cardDesc")
        desc.setWordWrap(True)
        desc.setFixedHeight(36)
        desc.setAlignment(Qt.AlignTop)
        lay.addWidget(desc)

    def mousePressEvent(self, e):
        self.window().open_detail(self.entry)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(os.environ.get("CHART_GALLERY_TITLE", "图表库"))
        self.resize(1280, 820)
        self.cfg = config.load()
        geo = self.cfg.get("geometry")
        if geo:
            self.setGeometry(QRect(*geo))
        self._geom = None                     # (cols, card_w) 缓存，避免 resize 抖动

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), 1)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.search.setFocus)

        # 缩略图后台队列须先于首次 reload 建立；新库尚无 thumb 时会立即入队。
        self._thumb_queue = []
        self._thumb_timer = QTimer(self)
        self._thumb_timer.setInterval(60)
        self._thumb_timer.timeout.connect(self._process_thumb)

        self.reload(restore=True)

        # 库目录监听：新增/修改条目自动刷新，不用手点刷新
        self._watcher = QFileSystemWatcher([str(Path(self.cfg["lib_dir"]))])
        self._watcher.directoryChanged.connect(self._on_lib_changed)
        self._reload_timer = QTimer(self)
        self._reload_timer.setSingleShot(True)
        self._reload_timer.setInterval(700)
        self._reload_timer.timeout.connect(lambda: self.reload(restore=True))

    # ---------------- 左栏 ----------------
    def _build_sidebar(self) -> QFrame:
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(SIDEBAR_W)
        v = QVBoxLayout(side)
        v.setContentsMargins(14, 16, 14, 14)
        v.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(10)
        logo = QLabel()
        if getattr(sys, "frozen", False):
            icon = Path(sys._MEIPASS) / "icon.png"
        else:
            icon = Path(config.__file__).resolve().parents[2] / "assets" / "icon.png"
        if not icon.exists():
            icon = Path(config.__file__).resolve().parent / "icon.png"
        if icon.exists():
            logo.setPixmap(QPixmap(str(icon)).scaled(34, 34, Qt.KeepAspectRatio,
                                                     Qt.SmoothTransformation))
        head.addWidget(logo)
        col = QVBoxLayout()
        col.setSpacing(0)
        t = QLabel(os.environ.get("CHART_GALLERY_TITLE", "图表库"))
        t.setObjectName("appTitle")
        s = QLabel(os.environ.get("CHART_GALLERY_SUBTITLE", "因果图表模板库"))
        s.setObjectName("appSub")
        col.addWidget(t)
        col.addWidget(s)
        head.addLayout(col)
        head.addStretch()
        v.addLayout(head)

        self.btn_data = QPushButton("数据类型")
        self.btn_method = QPushButton("方法类型")
        self.btn_star = QPushButton("★ 常用")
        for b in (self.btn_data, self.btn_method, self.btn_star):
            b.setObjectName("seg")
            b.setCheckable(True)
        self.btn_data.setChecked(True)
        group = QButtonGroup(self)
        group.setExclusive(True)
        for b in (self.btn_data, self.btn_method, self.btn_star):
            group.addButton(b)
        group.buttonClicked.connect(lambda _: self._on_dim_change())
        v.addWidget(self.btn_data)
        v.addWidget(self.btn_method)
        v.addWidget(self.btn_star)

        self.cats = QListWidget()
        self.cats.setObjectName("cats")
        self.cats.currentRowChanged.connect(lambda _: self._rebuild())
        v.addWidget(self.cats, 1)

        hline = QFrame()
        hline.setObjectName("hline")
        hline.setFixedHeight(1)
        v.addWidget(hline)

        cartbar = QFrame()
        cartbar.setObjectName("cartbar")
        cartbar.setCursor(Qt.PointingHandCursor)
        ch = QHBoxLayout(cartbar)
        ch.setContentsMargins(12, 10, 12, 10)
        self.cart_label = QLabel("★ 选图车（0）")
        self.cart_label.setObjectName("cartText")
        ch.addWidget(self.cart_label)
        ch.addStretch()
        cartbar.mousePressEvent = lambda e: self._show_cart()
        v.addWidget(cartbar)

        stats = QPushButton("📊 库体检（覆盖度统计）")
        stats.setObjectName("secondary")
        stats.clicked.connect(self._show_stats)
        v.addWidget(stats)
        return side

    # ---------------- 内容区 ----------------
    def _build_content(self) -> QWidget:
        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(56)
        top = QHBoxLayout(topbar)
        top.setContentsMargins(PAD, 0, PAD, 0)
        top.setSpacing(12)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 搜索名称或说明…")
        self.search.setFixedWidth(340)
        self.search.textChanged.connect(lambda _: self._rebuild())
        self.count_label = QLabel("共 0 张")
        self.count_label.setObjectName("count")
        refresh = QPushButton("⟳ 刷新")
        refresh.setObjectName("secondary")
        refresh.clicked.connect(lambda: self.reload())
        top.addWidget(self.search)
        top.addWidget(self.count_label)
        top.addStretch()
        top.addWidget(refresh)
        v.addWidget(topbar)

        inner = QWidget()
        vi = QVBoxLayout(inner)
        vi.setContentsMargins(PAD, PAD, PAD, PAD)
        vi.setSpacing(0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setSpacing(GRID)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.grid_widget)
        vi.addWidget(self.scroll, 1)
        v.addWidget(inner, 1)
        return content

    # ---------------- 数据 ----------------
    def reload(self, restore=False):
        self.entries = library.load_library(self.cfg["lib_dir"])
        self.vocab = library.load_vocab(self.cfg["lib_dir"])
        lt = self.cfg.get("last_tab", 0)
        if restore and lt == "常用":
            self.btn_star.setChecked(True)
            self._on_dim_change()
        else:
            if restore and lt in (0, 1):
                (self.btn_data if lt == 0 else self.btn_method).setChecked(True)
            self._fill_cats(restore)
            self._rebuild()
        self._update_cart()

    def _fill_cats(self, restore):
        dim = self._dim()
        self.cats.blockSignals(True)
        self.cats.clear()
        if dim == "常用":
            self.cats.setEnabled(False)
            self.cats.addItem("（按使用频次自动排列）")
            self.cats.item(0).setFlags(Qt.NoItemFlags)
            self.cats.blockSignals(False)
            return
        self.cats.setEnabled(True)
        self.cats.addItem("全部")
        for term in self.vocab.get(dim, []):
            self.cats.addItem(term)
        self.cats.blockSignals(False)
        if restore and self.cfg.get("last_category"):
            hits = self.cats.findItems(self.cfg["last_category"], Qt.MatchExactly)
            if hits:
                self.cats.setCurrentItem(hits[0])
                return
        self.cats.setCurrentRow(0)

    def _dim(self) -> str:
        if self.btn_star.isChecked():
            return "常用"
        return "数据类型" if self.btn_data.isChecked() else "方法类型"

    def _on_dim_change(self):
        self._fill_cats(False)
        self._rebuild()

    def _card_geometry(self):
        avail = self.scroll.viewport().width() - 2 * PAD
        cols = 3 if avail >= COL3_MIN else 2
        card_w = max(360, (avail - (cols - 1) * GRID) // cols)
        return cols, card_w

    def _rebuild(self):
        dim = self._dim()
        q = self.search.text().strip().lower()
        if dim == "常用":
            stems = usage.top(6)
            by_stem = {e.stem: e for e in self.entries}
            rows = [by_stem[s] for s in stems if s in by_stem]
            rows = [e for e in rows if not q or q in (e.name + e.desc + e.stem).lower()]
        else:
            attr = "data_type" if dim == "数据类型" else "method_type"
            term = self.cats.currentItem().text() if self.cats.currentItem() else "全部"
            rows = [e for e in self.entries
                    if (term == "全部" or getattr(e, attr) == term)
                    and (not q or q in (e.name + e.desc + e.stem).lower())]
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                it.widget().hide()          # 先隐藏，防止延迟删除期间与新卡叠画
                it.widget().deleteLater()
        cols, card_w = self._card_geometry()
        self._geom = (cols, card_w)
        for i, e in enumerate(rows):
            card = Card(e, card_w)
            self.grid.addWidget(card, i // cols, i % cols)
            if card._needs_thumb:
                self._queue_thumb(card)
        self.count_label.setText(f"共 {len(rows)} 张")
        self.cfg["last_tab"] = "常用" if dim == "常用" else (0 if dim == "数据类型" else 1)
        if dim != "常用":
            self.cfg["last_category"] = term
        config.save(self.cfg)

    def _update_cart(self):
        self.cart_label.setText(f"★ 选图车（{cart.count(self.cfg['lib_dir'])}）")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if not hasattr(self, "grid") or self._geom is None:
            return
        cols, card_w = self._card_geometry()
        if (cols, card_w) != self._geom and abs(card_w - self._geom[1]) > 10:
            if not getattr(self, "_resize_pending", False):
                self._resize_pending = True
                QTimer.singleShot(120, self._flush_resize)

    def _flush_resize(self):
        self._resize_pending = False
        if hasattr(self, "grid"):
            cols, card_w = self._card_geometry()
            if (cols, card_w) != self._geom and abs(card_w - self._geom[1]) > 10:
                self._rebuild()

    # ---------------- 动作 ----------------
    def open_detail(self, entry):
        usage.record(entry.stem, "view")
        DetailDialog(entry, self.cfg, on_changed=self._update_cart, parent=self).exec()
        self.reload(restore=True)

    def _show_stats(self):
        StatsDialog(self.entries, self.vocab, parent=self).exec()

    def _show_cart(self):
        CartDialog(self.cfg, on_changed=self._update_cart, parent=self).exec()

    def _queue_thumb(self, card):
        self._thumb_queue.append(card)
        if not self._thumb_timer.isActive():
            self._thumb_timer.start()

    def _process_thumb(self):
        if not self._thumb_queue:
            self._thumb_timer.stop()
            return
        card = self._thumb_queue.pop(0)
        try:
            if not isValid(card):
                return
            e = card.entry
            png, thumb = e.png, e.path.with_name(f"{e.stem}_thumb.png")
            if png.exists() and (not thumb.exists() or
                                 thumb.stat().st_mtime < png.stat().st_mtime):
                pm = QPixmap(str(png))
                if not pm.isNull():
                    pm.scaled(480, 4800, Qt.KeepAspectRatio,
                              Qt.SmoothTransformation).save(str(thumb))
            if isValid(card) and card.isVisible() and thumb.exists():
                card.img.setPixmap(_scaled_pixmap(str(thumb), card.width() - 28, IMG_H))
        except RuntimeError:
            return                                   # 卡片已被 deleteLater

    def _on_lib_changed(self, path):
        # 目录被移动/重命名时监听会失效，重挂后防抖重载
        want = str(Path(self.cfg["lib_dir"]))
        if self._watcher.directories() != [want]:
            for d in self._watcher.directories():
                self._watcher.removePath(d)
            self._watcher.addPath(want)
        self._reload_timer.start()

    def closeEvent(self, e):
        g = self.geometry()
        self.cfg["geometry"] = [g.x(), g.y(), g.width(), g.height()]
        config.save(self.cfg)
        super().closeEvent(e)
