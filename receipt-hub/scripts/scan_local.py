#!/usr/bin/env python3
"""
ローカルファイルスキャナー

mdfind（Spotlight）と find を組み合わせて対象期間のファイルを収集する。
- ~/Downloads, ~/Desktop → mdfind（ダウンロード日基準）
- その他フォルダ         → find -newermt（更新日基準）

使い方:
  python3 scripts/scan_local.py --start 2026-03-01 --end 2026-03-31
  python3 scripts/scan_local.py --start 2026-03-01 --end 2026-03-31 --dirs ~/Downloads ~/Documents/領収書/未処理
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".heic"}

# mdfind でホーム全体を検索（Spotlight インデックス使用）
MDFIND_ROOT = Path.home()

# find でも補完するフォルダ（mdfind が拾えないケース向け）
FIND_FALLBACK_DIRS = [
    Path.home() / "Documents" / "領収書" / "未処理",
]


def _is_target(path: str) -> bool:
    return Path(path).suffix.lower() in EXTENSIONS


def scan_mdfind(folder: Path, start: date, end: date) -> list[dict]:
    """Spotlight でダウンロード日基準の検索。"""
    start_iso = f"{start}T00:00:00"
    end_iso = f"{end}T23:59:59"
    query = (
        f'kMDItemDownloadedDate >= $time.iso("{start_iso}") '
        f'&& kMDItemDownloadedDate <= $time.iso("{end_iso}")'
    )
    try:
        result = subprocess.run(
            ["mdfind", "-onlyin", str(folder), query],
            capture_output=True, text=True, timeout=15
        )
        paths = [p for p in result.stdout.splitlines() if _is_target(p)]
        items = []
        for p in paths:
            mtime = datetime.fromtimestamp(Path(p).stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            items.append({"path": p, "method": "mdfind(ダウンロード日)", "mtime": mtime})
        return items
    except Exception:
        return []


def scan_find(folder: Path, start: date, end: date) -> list[dict]:
    """find で更新日基準の検索。"""
    # end の翌日を「以前」として指定
    end_str = end.strftime("%Y-%m-%d 23:59:59")
    start_str = (start.replace(day=start.day - 1) if start.day > 1
                 else start).strftime("%Y-%m-%d 23:59:59")

    ext_args = []
    for i, ext in enumerate(EXTENSIONS):
        if i > 0:
            ext_args.append("-o")
        ext_args += ["-iname", f"*{ext}"]

    try:
        result = subprocess.run(
            ["find", str(folder), "-type", "f",
             "(", *ext_args, ")",
             "-newermt", f"{start.isoformat()} 00:00:00",
             "!", "-newermt", f"{end.isoformat()} 23:59:59"],
            capture_output=True, text=True, timeout=30
        )
        items = []
        for p in result.stdout.splitlines():
            if not p:
                continue
            mtime = datetime.fromtimestamp(Path(p).stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            items.append({"path": p, "method": "find(更新日)", "mtime": mtime})
        return items
    except Exception:
        return []


def scan(start: date, end: date, extra_dirs: list[Path]) -> dict:
    seen = set()
    all_items = []
    report = []

    # mdfind でホーム全体をダウンロード日で検索
    items = scan_mdfind(MDFIND_ROOT, start, end)
    new = [i for i in items if i["path"] not in seen]
    seen.update(i["path"] for i in new)
    all_items.extend(new)
    report.append(f"  ~/ 全体 ({len(new)}件) ← mdfind/ダウンロード日")

    # find で補完（mdfind が拾えないファイル向け）
    find_dirs = extra_dirs if extra_dirs else FIND_FALLBACK_DIRS
    for folder in find_dirs:
        if not folder.exists():
            report.append(f"  {folder} — フォルダが見つかりません")
            continue
        items = scan_find(folder, start, end)
        new = [i for i in items if i["path"] not in seen]
        seen.update(i["path"] for i in new)
        all_items.extend(new)
        report.append(f"  {folder} ({len(new)}件) ← find/更新日（補完）")

    return {
        "items": all_items,
        "stats": {
            "total": len(all_items),
            "period": f"{start} 〜 {end}",
        },
        "report": report,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="開始日 YYYY-MM-DD")
    parser.add_argument("--end",   required=True, help="終了日 YYYY-MM-DD")
    parser.add_argument("--dirs",  nargs="*", default=[], help="追加スキャンフォルダ")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end   = date.fromisoformat(args.end)

    default_extra = [Path.home() / "Documents" / "領収書" / "未処理"]
    extra_dirs = [Path(d).expanduser() for d in args.dirs] if args.dirs else default_extra

    result = scan(start, end, extra_dirs)

    # 人間向けサマリーを stderr に出力
    print(f"\nローカルスキャン結果（{result['stats']['period']}）:", file=sys.stderr)
    for line in result["report"]:
        print(line, file=sys.stderr)
    print(f"  合計: {result['stats']['total']} 件\n", file=sys.stderr)

    # 機械処理用 JSON を stdout に出力
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
