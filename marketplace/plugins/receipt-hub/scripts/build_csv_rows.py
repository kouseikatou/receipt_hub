#!/usr/bin/env python3
"""dedup 後の JSON を CSV テキストに変換して stdout に出力する。

ファイル書き込みはしない（quarantine 回避のため、書き込みは Claude Code の Write ツールに任せる）。

使い方:
  python3 build_csv_rows.py /tmp/receipt_deduped.json                # データ行のみ
  python3 build_csv_rows.py /tmp/receipt_deduped.json --with-header  # BOM + ヘッダー + データ行（新規ファイル用）
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HEADERS = [
    "日付", "店名・先方", "金額(税込)", "税抜金額", "消費税率",
    "勘定科目", "種別", "メモ", "ソース", "確信度", "元ファイル",
]


def load_items(path: str) -> list[dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return raw.get("items", raw) if isinstance(raw, dict) else raw


def to_csv_text(items: list[dict], with_header: bool) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    if with_header:
        writer.writerow(HEADERS)
    for item in items:
        writer.writerow([
            item.get("date", ""),
            item.get("vendor", ""),
            item.get("amount", ""),
            item.get("amount_excl_tax", ""),
            f"{item.get('tax_rate', 10)}%",
            item.get("category", ""),
            item.get("doc_type", ""),
            item.get("memo", ""),
            item.get("source", ""),
            item.get("confidence", ""),
            item.get("file_path", ""),
        ])
    text = buf.getvalue()
    return ("﻿" + text) if with_header else text


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: build_csv_rows.py <deduped.json> [--with-header]", file=sys.stderr)
        return 2
    items = load_items(sys.argv[1])
    with_header = "--with-header" in sys.argv[2:]
    sys.stdout.write(to_csv_text(items, with_header))
    return 0


if __name__ == "__main__":
    sys.exit(main())
