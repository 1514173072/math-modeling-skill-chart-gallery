# -*- coding: utf-8 -*-
"""库体检：两个维度各类目的条目覆盖统计，QPainter 直绘条形（空缺类目橙色警示）。"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap, QPen
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget,
                               QVBoxLayout as QVL)

OI = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#999999"]
BAR_H, ROW_H, LABEL_W, PAD_L, PAD_R = 20, 30, 130, 12, 60


def _panel(rows: list[tuple[str, int]], width: int, title: str, vmax: int) -> QPixmap:
    """rows: (类目, 条数)；零条目用橙色空心条警示。vmax 全局统一，跨组长度可比。"""
    h = ROW_H * len(rows) + 48
    pm = QPixmap(width, h)
    pm.fill(QColor("#FFFFFF"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor("#8A94A3"))
    f = QFont("Microsoft YaHei", 9)
    f.setBold(True)
    p.setFont(f)
    p.drawText(PAD_L, 26, title)
    f2 = QFont("Microsoft YaHei", 9)
    p.setFont(f2)
    y = 44
    for i, (name, cnt) in enumerate(rows):
        p.setPen(QColor("#1F2937"))
        p.drawText(0, y, LABEL_W, BAR_H, Qt.AlignRight | Qt.AlignVCenter, name)
        bar_w = 0 if cnt == 0 else max(6, int((width - LABEL_W - PAD_L - PAD_R - 30) * cnt / vmax))
        x = LABEL_W + PAD_L
        if cnt == 0:
            p.setPen(QPen(QColor("#D55E00"), 1.2))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(x, y + 3, 60, BAR_H - 6, 4, 4)
            p.setPen(QColor("#D55E00"))
            p.drawText(x + 66, y, 160, BAR_H, Qt.AlignVCenter, "空缺——待补")
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(OI[i % len(OI)]))
            p.drawRoundedRect(x, y + 3, bar_w, BAR_H - 6, 4, 4)
            p.setPen(QColor("#374151"))
            p.drawText(x + bar_w + 8, y, 50, BAR_H, Qt.AlignVCenter, str(cnt))
        y += ROW_H
    p.end()
    return pm


class StatsDialog(QDialog):
    def __init__(self, entries, vocab, parent=None):
        super().__init__(parent)
        self.setWindowTitle("库体检")
        scr = self.screen().availableGeometry() if self.screen() else None
        self.resize(820, min(800, scr.height() - 80) if scr else 800)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 14)
        v.setSpacing(10)

        verified = sum(1 for e in entries if e.verified == "已验证")
        gaps = {dim: [t for t in vocab.get(dim, [])
                      if not any(getattr(e, "data_type" if dim == "数据类型" else "method_type") == t
                                 for e in entries)]
                for dim in ("数据类型", "方法类型")}
        total_gaps = sum(len(g) for g in gaps.values())
        summary = QLabel(f"共 {len(entries)} 条 · 已验证 {verified} 条 · "
                         f"类目空缺 {total_gaps} 个"
                         + ("" if total_gaps else " · 覆盖完整 ✓"))
        summary.setObjectName("contract")
        summary.setWordWrap(True)
        v.addWidget(summary)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        vi = QVL(inner)
        vi.setContentsMargins(0, 0, 0, 0)
        vi.setSpacing(12)
        dim_rows = {}
        for dim in ("数据类型", "方法类型"):
            counts = {t: 0 for t in vocab.get(dim, [])}
            attr = "data_type" if dim == "数据类型" else "method_type"
            for e in entries:
                val = getattr(e, attr)
                if val in counts:
                    counts[val] += 1
                elif val:
                    counts[val] = counts.get(val, 0) + 1
            dim_rows[dim] = sorted(counts.items(), key=lambda kv: -kv[1])
        global_max = max([v for rows in dim_rows.values() for _, v in rows], default=1) or 1
        for dim, rows in dim_rows.items():
            img = QLabel()
            img.setAlignment(Qt.AlignCenter)
            img.setPixmap(_panel(rows, 760, f"{dim}覆盖（条目数）", global_max))
            vi.addWidget(img)
        inner.setStyleSheet("background:white;border:1px solid #E7EBF0;border-radius:12px;")
        scroll.setWidget(inner)
        v.addWidget(scroll, 1)

        hint = QLabel("空缺类目可作为后续补充模板的优先方向；本图随库自动更新。")
        hint.setObjectName("source")
        v.addWidget(hint)
