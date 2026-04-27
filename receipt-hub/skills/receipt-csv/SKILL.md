---
name: receipt-csv
description: |
  解析済みの領収書・請求書データをCSVファイルに出力するスキル。「CSVに出力して」「エクスポートして」「ファイルに保存して」と言われたときに使う。exports/ディレクトリにUTF-8 BOM付きCSVを生成する。GoogleスプレッドシートやExcelにそのまま貼り付け可能。
tools:
  - Bash
---

# CSVエクスポート

## Step 1: 重複除去

CSV 出力の前に必ず重複チェックを実行する。

```bash
# 解析済みアイテムを items.json として保存してから実行
python3 scripts/dedup.py items.json
```

重複を自動除去してそのまま次へ進む。除去した件数は最後の完了報告にまとめる。

## Step 2: CSV 出力

重複除去後の `items` を使って出力する：

```bash
python3 - <<'PYEOF'
import csv, json, sys
from datetime import datetime
from pathlib import Path

items = json.loads(sys.stdin.read())
config = json.loads((Path.home() / ".receipt-hub" / "config.json").read_text())
exports_dir = Path(config.get("exports_dir", str(Path.home() / "Documents" / "領収書" / "exports")))
exports_dir.mkdir(parents=True, exist_ok=True)
filename = exports_dir / f"{datetime.now().strftime('%Y%m%d')}_経費.csv"
headers = ["日付", "店名・先方", "金額(税込)", "税抜金額", "消費税率",
           "勘定科目", "種別", "メモ", "ソース", "確信度"]

with open(filename, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
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
        ])
print(filename)
PYEOF
```

## 出力仕様

| 項目 | 内容 |
|------|------|
| 保存先 | `exports/` |
| ファイル名 | `YYYYMMDD_経費.csv` |
| 文字コード | UTF-8 BOM付き（Excel・Sheets で文字化けなし）|
| ヘッダー | `日付,店名・先方,金額(税込),税抜金額,消費税率,勘定科目,種別,メモ,ソース` |

## 完了後の報告

```
→ exports/20260427_経費.csv を生成しました
  領収書 N 件 / 請求書 N 件 / 合計 ¥XXX,XXX
  ※ 重複 N 件を除外しました（除外リストは上記）
```
