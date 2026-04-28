#!/usr/bin/env python3
"""
重複検出ヘルパー

使い方:
  python3 scripts/dedup.py items.json
  cat items.json | python3 scripts/dedup.py

入力: 解析済みアイテムの JSON 配列（ファイルまたは stdin）
出力: stdout に JSON
  {
    "items":      [...],   # 重複除去後のアイテム
    "duplicates": [...],   # 除外されたアイテムと除外理由
    "stats": { "before": N, "after": N, "removed": N }
  }
"""

import json
import sys
from datetime import date, timedelta
from difflib import SequenceMatcher


def _parse_date(s: str):
    """YYYY-MM-DD を date オブジェクトに変換。失敗したら None。"""
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _vendor_similar(a: str, b: str) -> bool:
    """ベンダー名の類似度判定。一方が他方を含むか、類似度 0.7 以上。"""
    a_lower, b_lower = a.lower(), b.lower()
    if a_lower in b_lower or b_lower in a_lower:
        return True
    ratio = SequenceMatcher(None, a_lower, b_lower).ratio()
    return ratio >= 0.7


def _match_count(a: dict, b: dict) -> tuple[int, list[str]]:
    """2 アイテム間の一致条件数と一致した条件名のリストを返す。"""
    matched = []

    # 金額一致
    if a.get("amount") and b.get("amount") and a["amount"] == b["amount"]:
        matched.append("金額")

    # 日付±1日以内
    da, db = _parse_date(a.get("date", "")), _parse_date(b.get("date", ""))
    if da and db and abs((da - db).days) <= 1:
        matched.append("日付(±1日)")

    # ベンダー類似
    va, vb = a.get("vendor", ""), b.get("vendor", "")
    if va and vb and _vendor_similar(va, vb):
        matched.append("ベンダー名")

    return len(matched), matched


def detect(items: list[dict]) -> dict:
    """重複を検出して除去済みリストと除外リストを返す。"""
    keep = []
    duplicates = []
    removed_indices = set()

    for i, item_i in enumerate(items):
        if i in removed_indices:
            continue
        for j in range(i + 1, len(items)):
            if j in removed_indices:
                continue
            item_j = items[j]
            count, reasons = _match_count(item_i, item_j)
            if count >= 2:
                removed_indices.add(j)
                duplicates.append({
                    "removed": item_j,
                    "kept": {k: item_i.get(k) for k in ("vendor", "date", "amount", "source")},
                    "matched_criteria": reasons,
                    "reason": f"{' / '.join(reasons)} が一致",
                })
        keep.append(item_i)

    return {
        "items": keep,
        "duplicates": duplicates,
        "stats": {
            "before": len(items),
            "after": len(keep),
            "removed": len(duplicates),
        },
    }


def main():
    if len(sys.argv) >= 2:
        raw = open(sys.argv[1], encoding="utf-8").read()
    else:
        raw = sys.stdin.read()

    items = json.loads(raw)
    result = detect(items)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 重複があった場合は stderr に要約を出す
    stats = result["stats"]
    if stats["removed"] > 0:
        print(f"\n⚠ 重複 {stats['removed']} 件を除外しました "
              f"({stats['before']} → {stats['after']} 件)", file=sys.stderr)
        for dup in result["duplicates"]:
            print(f"  - {dup['removed'].get('vendor')} "
                  f"{dup['removed'].get('date')} "
                  f"¥{dup['removed'].get('amount')} "
                  f"[{dup['removed'].get('source')}] "
                  f"← {dup['reason']}", file=sys.stderr)


if __name__ == "__main__":
    main()
