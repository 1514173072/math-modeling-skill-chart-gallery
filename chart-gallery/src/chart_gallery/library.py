# -*- coding: utf-8 -*-
"""扫库：解析 60_图表库 的条目 md 与 _维度字典.md。库本体在 vault，本模块只读。"""
import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Entry:
    path: Path
    stem: str
    name: str = ""
    desc: str = ""
    data_type: str = ""
    method_type: str = ""
    contract: str = ""
    source: str = ""
    script: str = ""
    verified: str = ""
    code: str = ""
    body: str = ""

    @property
    def png(self) -> Path:
        return self.path.with_suffix(".png")

    @property
    def has_png(self) -> bool:
        return self.png.exists()

    @property
    def kind(self) -> str:
        return "模板" if self.code else "思路"


def _split_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (m.group(1), text[m.end():]) if m else ("", text)


def _extract_code(body: str) -> str:
    m = re.search(r"```python\n(.*?)```", body, re.S)
    return m.group(1) if m else ""


def _fm_parse(fm_text: str) -> dict:
    try:
        d = yaml.safe_load(fm_text)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    out = {}
    for ln in fm_text.split("\n"):            # 兜底：简单 key: value 解析
        m = re.match(r"^([\w\u4e00-\u9fff]+):\s*(.*)$", ln)
        if m:
            out[m.group(1)] = m.group(2).strip().strip("'\"")
    return out


def load_entry(md: Path) -> Entry | None:
    try:
        text = md.read_text(encoding="utf-8")
    except Exception:
        return None
    fm_text, body = _split_frontmatter(text)
    fm = _fm_parse(fm_text)
    return Entry(
        path=md, stem=md.stem,
        name=str(fm.get("名称", md.stem)),
        desc=str(fm.get("说明", "")),
        data_type=str(fm.get("数据类型", "")),
        method_type=str(fm.get("方法类型", "")),
        contract=str(fm.get("数据契约", "")),
        source=str(fm.get("来源项目", "")),
        script=str(fm.get("原始脚本", "")),
        verified=str(fm.get("验证状态", "")),
        code=_extract_code(body),
        body=body.strip(),
    )


def load_library(lib_dir) -> list[Entry]:
    lib_dir = Path(lib_dir)
    if not lib_dir.exists():
        return []
    out = []
    for md in sorted(lib_dir.glob("*.md")):
        if md.name.startswith("_"):
            continue
        e = load_entry(md)
        if not e:
            continue
        if e.code or e.verified == "思路参考":     # 模板条目须有代码；思路扩展无代码
            out.append(e)
    return out


def load_vocab(lib_dir) -> dict[str, list[str]]:
    """从 _维度字典.md 的两个表格解析词表：取每行第一格。"""
    path = Path(lib_dir) / "_维度字典.md"
    vocab = {"数据类型": [], "方法类型": []}
    if not path.exists():
        entries = load_library(lib_dir)
        vocab["数据类型"] = sorted({e.data_type for e in entries if e.data_type})
        vocab["方法类型"] = sorted({e.method_type for e in entries if e.method_type})
        return vocab
    section = None
    for ln in path.read_text(encoding="utf-8").split("\n"):
        if ln.startswith("## "):
            section = "数据类型" if "数据类型" in ln else (
                "方法类型" if "方法类型" in ln else None)
            continue
        if section and ln.startswith("|") and "---" not in ln:
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if cells and cells[0] and cells[0] not in ("词", "维度"):
                vocab[section].append(cells[0])
    return vocab
