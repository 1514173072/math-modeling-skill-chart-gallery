#!/usr/bin/env python3
"""Search evidence-backed full-read notes instead of guessing from filenames."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = SKILL_ROOT / "references" / "corpus-index.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检索已有全文精读笔记。")
    parser.add_argument("keywords", nargs="+", help="关键词；默认要求全部命中同一篇笔记")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--year", type=int, choices=range(2020, 2026))
    parser.add_argument("--problem", type=str.upper, choices=list("ABCDEF"))
    parser.add_argument("--any", action="store_true", help="任一关键词命中即可")
    parser.add_argument("--context", type=int, default=0, help="每个命中行前后显示的行数")
    parser.add_argument("--json", action="store_true", help="输出JSON")
    return parser.parse_args()


def load_records(index: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"索引读取失败：{index}（{exc}）") from exc
    papers = payload.get("papers") if isinstance(payload, dict) else None
    if not isinstance(papers, list):
        raise ValueError("索引缺少papers数组")
    return [item for item in papers if isinstance(item, dict)]


def matching_snippets(lines: list[str], keys: list[str], radius: int) -> list[dict[str, Any]]:
    hit_lines = [i for i, line in enumerate(lines) if any(key in line.casefold() for key in keys)]
    snippets: list[dict[str, Any]] = []
    used_ranges: set[tuple[int, int]] = set()
    for i in hit_lines:
        start = max(0, i - radius)
        end = min(len(lines), i + radius + 1)
        span = (start, end)
        if span in used_ranges:
            continue
        used_ranges.add(span)
        snippets.append({"line": i + 1, "text": "\n".join(lines[start:end])})
    return snippets


def main() -> int:
    args = parse_args()
    if args.context < 0:
        print("错误：--context不能为负数", file=sys.stderr)
        return 2
    try:
        records = load_records(args.index)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    keys = [word.casefold() for word in args.keywords]
    results: list[dict[str, Any]] = []
    for record in records:
        if record.get("reading_status") != "full_read":
            continue
        if args.year is not None and record.get("year") != args.year:
            continue
        if args.problem is not None and record.get("problem_code") != args.problem:
            continue
        note_value = record.get("note_path")
        if not isinstance(note_value, str) or not note_value:
            continue
        note = (SKILL_ROOT / note_value).resolve()
        try:
            text = note.read_text(encoding="utf-8")
        except OSError:
            continue
        folded = text.casefold()
        accepted = any(key in folded for key in keys) if args.any else all(key in folded for key in keys)
        if not accepted:
            continue
        lines = text.splitlines()
        results.append(
            {
                "paper_id": record.get("paper_id"),
                "year": record.get("year"),
                "problem_code": record.get("problem_code"),
                "note_path": note_value,
                "source_path": record.get("source_path"),
                "snippets": matching_snippets(lines, keys, args.context),
            }
        )
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for result in results:
            print(
                f"{result['paper_id']} | {result['note_path']} | "
                f"{len(result['snippets'])}个命中行"
            )
            for snippet in result["snippets"]:
                rendered = snippet["text"].replace("\n", " / ")
                print(f"  L{snippet['line']}: {rendered}")
        print(f"共 {len(results)} 篇", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
