#!/usr/bin/env python3
"""Validate full, portable-PDF, or notes-only corpus indexes."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INDEX = Path(__file__).resolve().parents[1] / "references" / "corpus-index.json"
EXPECTED_BY_YEAR = {2020: 40, 2021: 44, 2022: 42, 2023: 58, 2024: 24, 2025: 21}
VALID_PROBLEMS = set("ABCDEF")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验优秀论文语料索引的完整性。")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX, help="索引JSON路径")
    return parser.parse_args()


def load_payload(index: Path) -> dict[str, Any]:
    try:
        payload = json.loads(index.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"索引不存在：{index}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"索引读取失败：{index}（{exc}）") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("papers"), list):
        raise ValueError("索引顶层必须是对象，且包含 papers 数组")
    return payload


def resolve_source_path(index: Path, payload: dict[str, Any], value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if payload.get("portable_package"):
        return index.resolve().parents[1] / path
    return path


def validate(payload: dict[str, Any], index: Path) -> list[str]:
    errors: list[str] = []
    papers = payload["papers"]
    portable = bool(payload.get("portable_package"))
    notes_only = bool(payload.get("notes_only_package"))
    expected_total = (
        payload.get("paper_count")
        if portable or notes_only
        else sum(EXPECTED_BY_YEAR.values())
    )
    if len(papers) != expected_total:
        errors.append(f"总数应为{expected_total}，实际为{len(papers)}")
    if payload.get("paper_count") != len(papers):
        errors.append(
            f"paper_count={payload.get('paper_count')!r}，与papers长度{len(papers)}不一致"
        )

    year_counts: Counter[int] = Counter()
    problems_by_year: dict[int, set[str]] = defaultdict(set)
    seen_paths: set[str] = set()
    seen_ids: set[str] = set()
    required = {
        "paper_id", "year", "problem_code", "file_name", "source_path",
        "relative_path", "size_bytes", "page_count", "reading_status", "note_path",
    }

    for position, record in enumerate(papers, start=1):
        label = f"第{position}条"
        if not isinstance(record, dict):
            errors.append(f"{label}不是对象")
            continue
        missing = required - set(record)
        if missing:
            errors.append(f"{label}缺少字段：{', '.join(sorted(missing))}")
        year = record.get("year")
        problem = record.get("problem_code")
        if year not in EXPECTED_BY_YEAR:
            errors.append(f"{label}年份无效：{year!r}")
        else:
            year_counts[year] += 1
            if isinstance(problem, str):
                problems_by_year[year].add(problem)
        if problem not in VALID_PROBLEMS:
            errors.append(f"{label}题号应为A-F，实际为{problem!r}")

        path_value = record.get("source_path")
        if not isinstance(path_value, str) or not path_value:
            errors.append(f"{label}路径为空或不是字符串")
        else:
            path = resolve_source_path(index, payload, path_value)
            path_key = str(path.resolve()).casefold()
            if path_key in seen_paths:
                errors.append(f"重复路径：{path}")
            seen_paths.add(path_key)
            if notes_only and record.get("availability") == "not_included":
                pass
            elif not path.is_file():
                errors.append(f"路径不存在：{path}")
            elif path.suffix.lower() != ".pdf":
                errors.append(f"不是PDF：{path}")
            if "赛题正文" in str(path):
                errors.append(f"索引错误收录赛题：{path}")

        record_id = record.get("paper_id")
        if not isinstance(record_id, str) or not record_id:
            errors.append(f"{label} ID为空或不是字符串")
        elif record_id in seen_ids:
            errors.append(f"重复ID：{record_id}")
        else:
            seen_ids.add(record_id)
        pages = record.get("page_count")
        if pages is not None and (not isinstance(pages, int) or isinstance(pages, bool) or pages <= 0):
            errors.append(f"{label} page_count必须为正整数或null，实际为{pages!r}")
        size_bytes = record.get("size_bytes")
        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes <= 0:
            errors.append(f"{label} size_bytes必须为正整数，实际为{size_bytes!r}")
        status = record.get("reading_status")
        if not isinstance(status, str) or not status.strip():
            errors.append(f"{label} status为空或不是字符串")
        note_value = record.get("note_path")
        if notes_only and (not isinstance(note_value, str) or not (index.resolve().parents[1] / note_value).is_file()):
            errors.append(f"{label}精读笔记不存在：{note_value!r}")

    if not portable and not notes_only:
        for year, expected in EXPECTED_BY_YEAR.items():
            actual = year_counts[year]
            if actual != expected:
                errors.append(f"{year}年应为{expected}篇，实际为{actual}篇")
            missing_problems = VALID_PROBLEMS - problems_by_year[year]
            extra_problems = problems_by_year[year] - VALID_PROBLEMS
            if missing_problems:
                errors.append(f"{year}年缺少题号：{', '.join(sorted(missing_problems))}")
            if extra_problems:
                errors.append(f"{year}年出现非法题号：{', '.join(sorted(extra_problems))}")
    return errors


def main() -> int:
    args = parse_args()
    try:
        payload = load_payload(args.index)
    except ValueError as exc:
        print(f"校验失败：{exc}", file=sys.stderr)
        return 1
    errors = validate(payload, args.index)
    if errors:
        print(f"校验失败，共{len(errors)}项：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    counts = Counter(record["year"] for record in payload["papers"])
    detail = "，".join(f"{year}:{counts[year]}" for year in sorted(counts))
    if payload.get("notes_only_package"):
        suffix = "开源版精读笔记齐全，论文原文未附带"
    elif payload.get("portable_package"):
        suffix = "便携精读子集，路径均存在"
    else:
        suffix = "每年A-F齐全，路径均存在"
    print(f"校验通过：共{len(payload['papers'])}篇（{detail}），{suffix}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
