# -*- coding: utf-8 -*-
"""选图车 v2：_选图车.md 的读写与单条移除，exe 与 AI 会话的交接文件。"""
import re
from datetime import date
from pathlib import Path

MARKER = "## 选图记录"
_LINE = re.compile(r"^- (.*)（\d{4}-\d{2}-\d{2}）$")


def _cart_path(lib_dir) -> Path:
    return Path(lib_dir) / "_选图车.md"


def _read(lib_dir) -> str:
    p = _cart_path(lib_dir)
    return p.read_text(encoding="utf-8") if p.exists() else f"# 选图车\n\n{MARKER}\n"


def entries(lib_dir) -> list[str]:
    """选图车中的图表名列表（按加入顺序，剥日期后缀）。"""
    _, _, tail = _read(lib_dir).partition(MARKER)
    out = []
    for ln in tail.split("\n"):
        ln = ln.strip()
        if ln.startswith("- "):
            m = _LINE.match(ln)
            out.append((m.group(1) if m else ln[2:]).strip())
    return out


def add(lib_dir, name: str) -> bool:
    """追加一条；已存在则跳过。返回是否真的写入。"""
    text = _read(lib_dir)
    if MARKER not in text:
        text += f"\n{MARKER}\n"
    head, _, tail = text.partition(MARKER)
    line = f"- {name}（{date.today().isoformat()}）"
    if any(ln.strip() == line or (ln.strip().startswith("- ") and
                                  (ln.strip()[2:].split("（")[0].strip() == name))
           for ln in tail.split("\n")):
        return False
    tail = "\n".join(ln for ln in tail.split("\n")
                     if ln.strip() and ln.strip() != "（暂无）").rstrip()
    text = head + MARKER + "\n" + (tail + "\n" if tail else "") + line + "\n"
    _cart_path(lib_dir).write_text(text, encoding="utf-8")
    return True


def remove(lib_dir, name: str) -> bool:
    """移除指定图表；返回是否真的移除。"""
    text = _read(lib_dir)
    if MARKER not in text:
        return False
    head, _, tail = text.partition(MARKER)
    kept = []
    removed = False
    for ln in tail.split("\n"):
        s = ln.strip()
        if s.startswith("- ") and (s[2:].split("（")[0].strip() == name):
            removed = True
            continue
        kept.append(ln)
    if not removed:
        return False
    body = "\n".join(k for k in kept).strip("\n").rstrip()
    text = head + MARKER + "\n" + (body + "\n" if body else "\n（暂无）\n")
    _cart_path(lib_dir).write_text(text, encoding="utf-8")
    return True


def clear(lib_dir) -> None:
    text = _read(lib_dir)
    head, _, _ = text.partition(MARKER)
    _cart_path(lib_dir).write_text(head.rstrip() + f"\n\n{MARKER}\n\n（暂无）\n", encoding="utf-8")


def count(lib_dir) -> int:
    return len(entries(lib_dir))
