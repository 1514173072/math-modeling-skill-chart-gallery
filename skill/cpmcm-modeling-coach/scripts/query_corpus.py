#!/usr/bin/env python3
"""Query the excellent-paper corpus index by metadata or keyword."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_INDEX = Path(__file__).resolve().parents[1] / "references" / "corpus-index.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="查询优秀论文语料索引。")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX, help="索引JSON路径")
    parser.add_argument("--year", type=int, choices=range(2020, 2026), help="年份")
    parser.add_argument("--problem", type=str.upper, choices=list("ABCDEF"), help="题号A-F")
    parser.add_argument(
        "--status",
        help="阅读/复现状态，如 indexed、screened、full_read、model_reconstructable",
    )
    parser.add_argument(
        "--keyword",
        help="不区分大小写，搜索ID、文件名、路径、状态和笔记路径；多个词按完整子串匹配。",
    )
    parser.add_argument("--json", action="store_true", help="以JSON输出匹配记录")
    parser.add_argument("--count", action="store_true", help="只输出匹配数量")
    return parser.parse_args()


def load_papers(index: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(index.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"索引不存在：{index}；请先运行 build_corpus_index.py") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"索引读取失败：{index}（{exc}）") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("papers"), list):
        raise ValueError(f"索引格式错误，缺少 papers 数组：{index}")
    return [record for record in payload["papers"] if isinstance(record, dict)]


def searchable_text(record: dict[str, Any]) -> str:
    fields = (
        "paper_id", "file_name", "source_path", "relative_path",
        "reading_status", "note_path",
    )
    return "\n".join(str(record.get(field, "")) for field in fields).casefold()


def main() -> int:
    args = parse_args()
    try:
        papers = load_papers(args.index)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    keyword = args.keyword.casefold() if args.keyword else None
    status = args.status.casefold() if args.status else None
    matches = [
        record
        for record in papers
        if (args.year is None or record.get("year") == args.year)
        and (args.problem is None or record.get("problem_code") == args.problem)
        and (status is None or str(record.get("reading_status", "")).casefold() == status)
        and (keyword is None or keyword in searchable_text(record))
    ]

    if args.count:
        print(len(matches))
    elif args.json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        for record in matches:
            pages = record.get("page_count")
            page_text = "?" if pages is None else str(pages)
            print(
                f"{record.get('year')} {record.get('problem_code')} | "
                f"{record.get('reading_status')} | {page_text}页 | {record.get('source_path')}"
            )
        print(f"共 {len(matches)} 篇", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
