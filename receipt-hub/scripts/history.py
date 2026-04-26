#!/usr/bin/env python3
"""
vendor_history ヘルパー

使い方:
  python3 scripts/history.py lookup "スターバックス渋谷店"
  python3 scripts/history.py add    "スターバックス渋谷店" "会議費" "2026-04-27"
  python3 scripts/history.py list
  python3 scripts/history.py stats
"""

import json
import sys
from datetime import date
from pathlib import Path

HISTORY_PATH = Path.home() / ".receipt-hub" / "vendor_history.json"
HIGH_CONFIDENCE_THRESHOLD = 3


def _load() -> dict:
    if not HISTORY_PATH.exists():
        return {}
    return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))


def _save(history: dict) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_lookup(vendor: str) -> None:
    history = _load()
    entry = history.get(vendor)
    if not entry:
        print(json.dumps({"found": False}))
        return
    count = entry["count"]
    confidence = "high" if count >= HIGH_CONFIDENCE_THRESHOLD else "medium"
    print(json.dumps({
        "found": True,
        "category": entry["category"],
        "count": count,
        "last_confirmed": entry["last_confirmed"],
        "confidence": confidence,
    }, ensure_ascii=False))


def cmd_add(vendor: str, category: str, confirmed_date: str = None) -> None:
    history = _load()
    entry = history.get(vendor, {"category": category, "count": 0, "last_confirmed": ""})
    entry["count"] += 1
    entry["category"] = category
    entry["last_confirmed"] = confirmed_date or date.today().isoformat()
    history[vendor] = entry
    _save(history)
    print(f"履歴更新: {vendor} → {category} (累計 {entry['count']} 件)")


def cmd_list() -> None:
    history = _load()
    if not history:
        print("（履歴なし）")
        return
    rows = sorted(history.items(), key=lambda x: x[1]["count"], reverse=True)
    print(f"{'ベンダー':<30} {'勘定科目':<16} {'件数':>4}  最終確認")
    print("-" * 70)
    for vendor, entry in rows:
        mark = "★" if entry["count"] >= HIGH_CONFIDENCE_THRESHOLD else " "
        print(f"{mark}{vendor:<29} {entry['category']:<16} {entry['count']:>4}  {entry['last_confirmed']}")


def cmd_stats() -> None:
    history = _load()
    if not history:
        print("（履歴なし）")
        return
    total = len(history)
    high = sum(1 for e in history.values() if e["count"] >= HIGH_CONFIDENCE_THRESHOLD)
    by_category: dict[str, int] = {}
    for entry in history.values():
        by_category[entry["category"]] = by_category.get(entry["category"], 0) + 1
    print(f"登録ベンダー数: {total}  うち高確信度(★): {high}")
    print("\n勘定科目別ベンダー数:")
    for cat, cnt in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat:<16} {cnt} 件")


COMMANDS = {"lookup": cmd_lookup, "add": cmd_add, "list": cmd_list, "stats": cmd_stats}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    cmd = args[0]
    COMMANDS[cmd](*args[1:])
