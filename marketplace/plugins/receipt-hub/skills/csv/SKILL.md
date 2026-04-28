---
name: csv
description: |
  （非推奨・互換維持用）CSV出力。新フローでは `receipt-csv` を使うこと。Python の open() で CSV を書くと com.apple.quarantine が付与されて Excel for Mac が「ファイルが見つかりません (エラー 53)」で開けなくなるため、書き込みは Claude Code の Write ツールで行う。
tools:
  - Bash
  - Read
  - Write
---

# CSVエクスポート（互換ラッパー）

このスキルは旧名互換のために残してある。**新規実装は `receipt-csv` スキルを使うこと**。

実体は `receipt-csv` と同じ。手順は次の3ステップ：

1. `python3 scripts/dedup.py /tmp/receipt_items.json > /tmp/receipt_deduped.json`
2. `python3 scripts/build_csv_rows.py /tmp/receipt_deduped.json [--with-header]` で CSV テキストを stdout に取得
3. **Write ツール** で `~/Desktop/領収書/exports/YYYYMM_経費.csv` に保存（既存があれば Read → 末尾連結 → Write）

**Python は絶対にユーザーが開くファイルに `open(..., "w")` してはいけない**（quarantine が付くため）。
