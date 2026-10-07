# -*- coding: utf-8 -*-
"""详情对话框 v2：分区卡片化（预览/说明契约/代码），大预览，等宽按钮，代码高亮+行号。"""
import os
import re

from PySide6.QtCore import Qt, QSize, QTimer, QRect, QThread, Signal
from PySide6.QtGui import (QImageReader, QPixmap, QColor, QFont, QPainter,
                           QSyntaxHighlighter, QTextCharFormat, QGuiApplication)
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QPlainTextEdit, QMessageBox, QApplication, QWidget,
                               QScrollArea, QFrame, QLineEdit, QTextBrowser)

from . import cart, render, usage

KEYWORDS = ("and as assert async await break class continue def del elif else except "
            "False finally for from global if import in is lambda None nonlocal not "
            "or pass raise return True try while with yield").split()

FMT_COMMENT = QTextCharFormat()
FMT_COMMENT.setForeground(QColor("#7A8B99"))
FMT_STRING = QTextCharFormat()
FMT_STRING.setForeground(QColor("#1F7A4D"))
FMT_KEYWORD = QTextCharFormat()
FMT_KEYWORD.setForeground(QColor("#005A8E"))
FMT_KEYWORD.setFontWeight(QFont.Bold)
FMT_NUMBER = QTextCharFormat()
FMT_NUMBER.setForeground(QColor("#B35900"))


class PythonHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text: str):
        if text.lstrip().startswith("#"):
            self.setFormat(0, len(text), FMT_COMMENT)
            return
        for pattern, fmt in [
            (r"(?:'''[^']*?'''|\"\"\".*?\"\"\")", FMT_STRING),
            (r"(?:'[^'\n]*'|\"[^\"\n]*\")", FMT_STRING),
            (r"#[^\n]*", FMT_COMMENT),
            (r"\b\d+\.?\d*\b", FMT_NUMBER),
        ]:
            for m in re.finditer(pattern, text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)
        for kw in KEYWORDS:
            for m in re.finditer(rf"\b{kw}\b", text):
                self.setFormat(m.start(), len(kw), FMT_KEYWORD)


class _LineArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def paintEvent(self, event):
        self.editor.line_area_paint(event)


class CodeEditor(QPlainTextEdit):
    """带行号区的只读代码框。"""

    def __init__(self, text: str):
        super().__init__(text)
        self.setObjectName("code")
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        f = QFont("Consolas", 10)
        f.setStyleHint(QFont.Monospace)
        self.setFont(f)
        self._area = _LineArea(self)
        self.blockCountChanged.connect(self._update_width)
        self.updateRequest.connect(self._update_area)
        self._update_width(0)
        PythonHighlighter(self.document())

    def line_area_width(self) -> int:
        digits = max(2, len(str(max(1, self.blockCount()))))
        fm = self.fontMetrics()
        return 16 + fm.horizontalAdvance("9") * digits

    def _update_width(self, _):
        self.setViewportMargins(self.line_area_width(), 0, 0, 0)

    def _update_area(self, rect, dy):
        if dy:
            self._area.scroll(0, dy)
        else:
            self._area.update(0, rect.y(), self._area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_width(0)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        cr = self.contentsRect()
        self._area.setGeometry(QRect(cr.left(), cr.top(), self.line_area_width(),
                                     cr.height()))

    def line_area_paint(self, event):
        painter = QPainter(self._area)
        painter.fillRect(event.rect(), QColor("#F2F5F9"))
        block = self.firstVisibleBlock()
        n = self.blockCount()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        painter.setFont(self.font())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor("#9AA6B2"))
                painter.drawText(0, top, self._area.width() - 8,
                                 self.fontMetrics().height(), Qt.AlignRight,
                                 str(block.blockNumber() + 1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            if not n:
                break


class _AskWorker(QThread):
    """内置 AI 问答线程：完成后自动自清理，对话框关闭也不会拖住程序。"""
    done = Signal(str)
    fail = Signal(str)

    def __init__(self, question, image_path, context):
        super().__init__()
        self.question, self.image_path, self.context = question, image_path, context

    def run(self):
        try:
            from importlib import import_module
            ai_module = import_module(f"{__package__}.ai")
            self.done.emit(ai_module.ask(self.question, self.image_path, self.context))
        except Exception as e:
            self.fail.emit(str(e))
        finally:
            self.deleteLater()


class FullscreenImage(QDialog):
    """双击预览进入的全屏查看：黑底等比缩放，点击或 Esc 退出。"""

    def __init__(self, png_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("预览（点击任意处退出）")
        self.setModal(True)
        self.setStyleSheet("background:black;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        scr = QGuiApplication.primaryScreen().availableGeometry()
        r = QImageReader(png_path)
        s = r.size()
        if s.isValid() and s.width() > 0 and s.height() > 0:
            k = min(scr.width() / s.width(), scr.height() / s.height())
            r.setScaledSize(QSize(max(1, int(s.width() * k)), max(1, int(s.height() * k))))
            lbl.setPixmap(QPixmap.fromImageReader(r))
        lay.addWidget(lbl)

    def mousePressEvent(self, e):
        self.accept()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(e)


class DetailDialog(QDialog):
    def __init__(self, entry, cfg, on_changed=None, parent=None):
        super().__init__(parent)
        self.entry, self.cfg, self.on_changed = entry, cfg, on_changed
        self.setWindowTitle(entry.name or entry.stem)
        scr = QGuiApplication.primaryScreen().availableGeometry()
        self.resize(min(1020, scr.width() - 60), min(940, scr.height() - 60))
        base = self.parent().geometry() if self.parent() else scr
        self.move(max(scr.left(), base.x() + (base.width() - self.width()) // 2),
                  max(scr.top(), base.y() + (base.height() - self.height()) // 2))
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(18, 18, 18, 14)
        lay.setSpacing(12)
        outer.addWidget(scroll, 1)
        scroll.setWidget(body)

        # ---- 分区 1：预览 ----
        sec_img = QFrame()
        sec_img.setObjectName("section")
        v1 = QVBoxLayout(sec_img)
        v1.setContentsMargins(14, 14, 14, 14)
        v1.setSpacing(6)
        t0 = QLabel("预览（双击进入全屏查看）")
        t0.setObjectName("secTitle")
        v1.addWidget(t0)
        self.img = QLabel()
        self.img.setAlignment(Qt.AlignCenter)
        self.img.setCursor(Qt.PointingHandCursor)
        self.img.mouseDoubleClickEvent = lambda e: self._fullscreen()
        v1.addWidget(self.img)
        lay.addWidget(sec_img)

        # ---- 分区 2：说明 + 契约 + 来源 ----
        sec_meta = QFrame()
        sec_meta.setObjectName("section")
        v2 = QVBoxLayout(sec_meta)
        v2.setContentsMargins(14, 12, 14, 12)
        v2.setSpacing(8)
        self.badge = QLabel()
        self._set_badge()
        v2.addWidget(self.badge)
        t1 = QLabel("说 明")
        t1.setObjectName("secTitle")
        v2.addWidget(t1)
        desc = QLabel(entry.desc or "（无说明）")
        desc.setTextFormat(Qt.RichText)
        desc.setText(f"<p style='line-height:165%; margin:0;'>{(entry.desc or '（无说明）').strip()}</p>")
        desc.setWordWrap(True)
        v2.addWidget(desc)
        t2 = QLabel("数据契约")
        t2.setObjectName("secTitle")
        v2.addWidget(t2)
        contract = QLabel(entry.contract or "（未填写）")
        contract.setObjectName("contract")
        contract.setWordWrap(True)
        v2.addWidget(contract)
        src = QLabel(f"来源：{entry.source}　·　原始脚本：{entry.script}")
        src.setObjectName("source")
        src.setWordWrap(True)
        v2.addWidget(src)
        lay.addWidget(sec_meta)

        # ---- 按钮行 ----
        btns = QHBoxLayout()
        btns.setSpacing(10)
        b_copy = QPushButton("复制代码")
        b_copy.setMinimumWidth(150)
        b_copy.clicked.connect(self._copy_code)
        b_ai = QPushButton("复制 AI 请求")
        b_ai.setObjectName("secondary")
        b_ai.setMinimumWidth(140)
        b_ai.clicked.connect(self._copy_ai)
        b_render = QPushButton("⟳ 重渲染")
        b_render.setObjectName("secondary")
        b_render.setMinimumWidth(120)
        b_render.clicked.connect(self._render)
        b_star = QPushButton()
        b_star.setObjectName("secondary")
        b_star.setMinimumWidth(130)
        b_star.clicked.connect(self._star)
        self._star_btn = b_star
        for b in (b_copy, b_ai, b_render, b_star):
            btns.addWidget(b)
        btns.addStretch()
        lay.addLayout(btns)
        self._has_code = bool(entry.code)
        if not self._has_code:
            b_copy.hide()
            b_render.hide()

        # ---- 分区 3：代码（模板） / 构造思路（思路参考） ----
        if self._has_code:
            sec_code = QFrame()
            sec_code.setObjectName("section")
            v3 = QVBoxLayout(sec_code)
            v3.setContentsMargins(10, 10, 10, 10)
            self.code_view = CodeEditor(entry.code)
            self.code_view.setMinimumHeight(280)
            v3.addWidget(self.code_view)
            lay.addWidget(sec_code, 1)
        else:
            sec_idea = QFrame()
            sec_idea.setObjectName("section")
            v3 = QVBoxLayout(sec_idea)
            v3.setContentsMargins(14, 12, 14, 12)
            v3.setSpacing(6)
            t3 = QLabel("构造思路（不复现，供借鉴）")
            t3.setObjectName("secTitle")
            v3.addWidget(t3)
            idea = QLabel(self._body_html())
            idea.setTextFormat(Qt.RichText)
            idea.setWordWrap(True)
            v3.addWidget(idea)
            lay.addWidget(sec_idea, 1)

        # ---- 分区 4：问一问（完整版可选；公开精选版不打包私人接口） ----
        if os.environ.get("CHART_GALLERY_DISABLE_AI") != "1":
            sec_ask = QFrame()
            sec_ask.setObjectName("section")
            v4 = QVBoxLayout(sec_ask)
            v4.setContentsMargins(14, 12, 14, 12)
            v4.setSpacing(8)
            t3 = QLabel("问一问（内置 AI · 解答这张图的细节）")
            t3.setObjectName("secTitle")
            v4.addWidget(t3)
            quick = QHBoxLayout()
            quick.setSpacing(8)
            for text in ("这张图怎么读？", "什么场景该用它？", "换成我的数据要注意什么？"):
                qb = QPushButton(text)
                qb.setObjectName("secondary")
                qb.clicked.connect(lambda _, t=text: self._ask(t))
                quick.addWidget(qb)
            quick.addStretch()
            v4.addLayout(quick)
            askrow = QHBoxLayout()
            askrow.setSpacing(8)
            self.ask_input = QLineEdit()
            self.ask_input.setPlaceholderText("输入关于这张图的问题，回车或点“提问”…")
            self.ask_input.returnPressed.connect(self._ask_from_input)
            self.ask_btn = QPushButton("提问")
            self.ask_btn.clicked.connect(self._ask_from_input)
            askrow.addWidget(self.ask_input, 1)
            askrow.addWidget(self.ask_btn)
            v4.addLayout(askrow)
            self.answer = QTextBrowser()
            self.answer.setObjectName("answer")
            self.answer.setMinimumHeight(96)
            self.answer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.answer.setPlaceholderText("（尚未提问——回答会出现在这里，只基于图片与元数据，不编造）")
            v4.addWidget(self.answer)
            lay.addWidget(sec_ask)
        self._worker = None
        lay.addStretch(0)

        self.toast = QLabel(self)
        self.toast.setObjectName("toast")
        self.toast.hide()
        self._load_image()
        self._update_star()
        usage.record(entry.stem, "view")

    def _body_html(self) -> str:
        """思路参考条目：把 md 正文转成可读 HTML（去标题/围栏/双链，粗体与行距）。"""
        text = (self.entry.body or "").strip()
        text = re.sub(r"^## .*$", "", text, flags=re.M)
        text = text.replace("```text", "").replace("```", "")
        text = re.sub(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]", r"\1", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        return "".join(f"<p style='line-height:170%; margin:0 0 9px 0;'>"
                       f"{p.replace(chr(10), '<br>')}</p>" for p in paras)

    def _fullscreen(self):
        if self.entry.has_png:
            FullscreenImage(str(self.entry.png), self).showFullScreen()

    # ---- 内部 ----
    def _load_image(self):
        if not self.entry.has_png:
            self.img.setText("（无预览图，请先重渲染）")
            return
        r = QImageReader(str(self.entry.png))
        s = r.size()
        box_w = self.width() - 100
        if s.isValid() and s.height() > 0 and s.width() > 0:
            k = min(box_w / s.width(), 620 / s.height())
            r.setScaledSize(QSize(max(1, int(s.width() * k)), max(1, int(s.height() * k))))
            self.img.setPixmap(QPixmap.fromImageReader(r))

    def _set_badge(self):
        if self.entry.verified == "已验证":
            self.badge.setText("● 已验证（代码在本机跑通并产出预览图）")
            self.badge.setObjectName("badge")
        elif self.entry.verified == "思路参考":
            self.badge.setText("● 思路参考条目——不复现，仅供构造借鉴")
            self.badge.setObjectName("source")
        else:
            self.badge.setText(f"● {self.entry.verified or '未验证'}")
            self.badge.setObjectName("badgeBad")

    def _show_toast(self, msg: str):
        self.toast.setText(msg)
        self.toast.adjustSize()
        self.toast.move((self.width() - self.toast.width()) // 2,
                        self.height() - self.toast.height() - 24)
        self.toast.show()
        self.toast.raise_()
        QTimer.singleShot(2000, self.toast.hide)

    # ---- 动作 ----
    def _copy_code(self):
        QApplication.clipboard().setText(self.entry.code)
        usage.record(self.entry.stem, "copy")
        self._show_toast("已复制模板代码")

    def _copy_ai(self):
        e = self.entry
        text = (f"请用下面的图表模板画我的数据。\n\n"
                f"【图表】{e.name}\n【数据契约】{e.contract}\n【模板代码】\n"
                f"```python\n{e.code}\n```\n\n"
                f"我的数据如下，请先核对是否满足数据契约，再改写模板：")
        QApplication.clipboard().setText(text)
        usage.record(e.stem, "copy")
        self._show_toast("已复制 AI 请求，粘贴到会话即可")

    def _render(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            ok, msg = render.render_entry(self.entry, self.cfg["lib_dir"], self.cfg["python"])
        finally:
            QApplication.restoreOverrideCursor()
        if ok:
            self._load_image()
            self.entry.verified = "已验证"
            self._set_badge()
            self._show_toast(msg)
            usage.record(self.entry.stem, "render")
            if self.on_changed:
                self.on_changed()
        else:
            QMessageBox.critical(self, "渲染失败", msg)

    def _update_star(self):
        in_cart = (self.entry.name or self.entry.stem) in cart.entries(self.cfg["lib_dir"])
        self._star_btn.setText("★ 取消收藏" if in_cart else "★ 收藏")

    # ---- 内置 AI ----
    def _ask_from_input(self):
        q = self.ask_input.text().strip()
        if q:
            self._ask(q)

    def _ask(self, question: str):
        if self._worker is not None and self._worker.isRunning():
            return
        if not self.entry.has_png:
            QMessageBox.information(self, "无预览图", "先重渲染生成预览图，再向 AI 提问。")
            return
        self.ask_input.setText(question)
        e = self.entry
        context = (f"名称：{e.name}；说明：{e.desc}；数据契约：{e.contract}；"
                   f"验证状态：{e.verified}")
        self.answer.setPlainText("思考中…（内置 AI 正在看图）")
        self.ask_btn.setEnabled(False)
        self.ask_input.setEnabled(False)
        self._worker = _AskWorker(question, str(self.entry.png), context)
        self._worker.done.connect(self._on_answer)
        self._worker.fail.connect(self._on_answer_fail)
        self._worker.start()

    def _on_answer(self, text: str):
        from html import escape
        body = escape(text).replace("\n", "<br>")
        self.answer.setHtml(body)
        self._ask_done()

    def _on_answer_fail(self, err: str):
        self.answer.setPlainText(f"提问失败：{err}")
        self._ask_done()

    def _ask_done(self):
        self.ask_btn.setEnabled(True)
        self.ask_input.setEnabled(True)
        self._worker = None

    def _star(self):
        name = self.entry.name or self.entry.stem
        if name in cart.entries(self.cfg["lib_dir"]):
            cart.remove(self.cfg["lib_dir"], name)
            self._show_toast("已移出选图车")
        else:
            cart.add(self.cfg["lib_dir"], name)
            self._show_toast("已加入选图车")
        self._update_star()
        if self.on_changed:
            self.on_changed()
