---
name: receipt-csv
description: |
  解析済みの領収書・請求書データをCSVファイルに出力するスキル。「CSVに出力して」「エクスポートして」「ファイルに保存して」と言われたときに使う。exports/ディレクトリにUTF-8 BOM付きCSVを生成する。GoogleスプレッドシートやExcelにそのまま貼り付け可能。
tools:
  - Bash
---

# CSVエクスポート

## Step 1: 重複除去

解析済みアイテムを `/tmp/receipt_items.json` に書き出してから重複除去を実行する。

```bash
# items は解析結果のJSON配列。/tmp に書き出す
python3 scripts/dedup.py /tmp/receipt_items.json > /tmp/receipt_deduped.json
```

重複を自動除去してそのまま次へ進む。除去した件数は最後の完了報告にまとめる。

## Step 2: CSV 出力

重複除去後のファイルをスクリプトに渡して出力する：

```bash
python3 - /tmp/receipt_deduped.json <<'PYEOF'
import csv, json, sys
from datetime import datetime
from pathlib import Path

# dedup.py の出力は {"items": [...], ...} 形式
raw = json.loads(open(sys.argv[1], encoding="utf-8").read())
items = raw.get("items", raw) if isinstance(raw, dict) else raw

config = json.loads((Path.home() / ".receipt-hub" / "config.json").read_text())
exports_dir = Path(config.get("exports_dir", str(Path.home() / "Desktop" / "領収書" / "exports")))
exports_dir.mkdir(parents=True, exist_ok=True)

filename = exports_dir / f"{datetime.now().strftime('%Y%m')}_経費.csv"
headers = ["日付", "店名・先方", "金額(税込)", "税抜金額", "消費税率",
           "勘定科目", "種別", "メモ", "ソース", "確信度", "元ファイル"]

file_exists = filename.exists()
with open(filename, "a", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    if not file_exists:
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
            item.get("file_path", ""),
        ])
print(filename)
PYEOF
```

## 出力仕様

| 項目 | 内容 |
|------|------|
| 保存先 | `~/Desktop/領収書/exports/` |
| ファイル名 | `YYYYMM_経費.csv`（月次・追記）|
| 文字コード | UTF-8 BOM付き（Excel・Sheets で文字化けなし）|
| ヘッダー | `日付,店名・先方,金額(税込),税抜金額,消費税率,勘定科目,種別,メモ,ソース,確信度,元ファイル` |
| 追記モード | 同月ファイルが既存なら追記、なければ新規作成 |

## 完了後の報告

```
→ exports/20260427_経費.csv を生成しました
  領収書 N 件 / 請求書 N 件 / 合計 ¥XXX,XXX
  ※ 重複 N 件を除外しました（除外リストは上記）
```
