---
name: csv
description: |
  解析済みの領収書・請求書データをCSVファイルに出力するスキル。「CSVに出力して」「エクスポートして」「ファイルに保存して」と言われたときに使う。exports/ディレクトリにUTF-8 BOM付きCSVを生成する。GoogleスプレッドシートやExcelにそのまま貼り付け可能。
tools:
  - Bash
---

# CSVエクスポート

## 出力仕様

| 項目 | 内容 |
|------|------|
| 保存先 | プロジェクト直下の `exports/` ディレクトリ |
| ファイル名 | `YYYYMMDD_項目名.csv`（例: `20240115_経費.csv`）|
| 文字コード | UTF-8 BOM付き（Excel・Sheetsで文字化けなし）|
| 1行目 | ヘッダー行（固定）|
| カンマを含むデータ | ダブルクォーテーションで自動エスケープ |

## ヘッダー構成

```
日付,店名・先方,金額(税込),税抜金額,消費税率,勘定科目,種別,メモ,ソース
```

## 出力スクリプト

以下のPythonを Bash ツールで実行する：

```python
import csv, os
from datetime import datetime

def export_to_csv(items, label="経費"):
    os.makedirs("exports", exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"exports/{date_str}_{label}.csv"

    headers = ["日付", "店名・先方", "金額(税込)", "税抜金額", "消費税率",
               "勘定科目", "種別", "メモ", "ソース"]

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
            ])
    return filename
```

## 完了後の報告

エクスポート完了後、以下を報告する：
- 出力ファイルパス
- 件数（領収書N件・請求書N件）
- 合計金額
- 「このファイルをGoogleスプレッドシートに取り込む場合は、ファイル→インポートから選択してください」
