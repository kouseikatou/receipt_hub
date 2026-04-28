---
name: receipt-csv
description: |
  解析済みの領収書・請求書データをCSVファイルに出力するスキル。「CSVに出力して」「エクスポートして」「ファイルに保存して」と言われたときに使う。exports/ディレクトリにUTF-8 BOM付きCSVを生成する。GoogleスプレッドシートやExcelにそのまま貼り付け可能。
tools:
  - Bash
  - Read
  - Write
---

# CSVエクスポート

## 設計原則

**ユーザーが開く CSV ファイルへの書き込みは Claude Code の Write ツールで行う。**
Python の `open()` で書くとサンドボックス経由で `com.apple.quarantine` が付与され、Excel for Mac が「ファイルが見つかりません (エラー 53)」で開けなくなる。Python は **JSON → CSV テキストへの変換** までしか行わない（純粋関数）。

## Step 1: 重複除去

解析済みアイテムを `/tmp/receipt_items.json` に書き出してから重複除去を実行する。

```bash
# items は解析結果のJSON配列。/tmp に書き出す
python3 scripts/dedup.py /tmp/receipt_items.json > /tmp/receipt_deduped.json
```

重複を自動除去してそのまま次へ進む。除去した件数は最後の完了報告にまとめる。

## Step 2: CSV テキスト生成

`build_csv_rows.py` で deduped JSON → CSV テキストに変換する（**stdout に出力するだけでファイルは書かない**）。

```bash
# データ行のみ（既存ファイルへの追記用）
python3 scripts/build_csv_rows.py /tmp/receipt_deduped.json > /tmp/receipt_new_rows.csv

# 新規ファイル用（BOM + ヘッダー + データ行）
python3 scripts/build_csv_rows.py /tmp/receipt_deduped.json --with-header > /tmp/receipt_new_full.csv
```

## Step 3: 月次CSVへ書き出し（Write ツール）

ファイル名は **必ず `YYYYMM_経費.csv`（月次）** とし、タイムスタンプや「2026年4月」などの suffix は絶対に付けない。

保存先パスを取得：

```bash
python3 - <<'PY'
import json
from datetime import datetime
from pathlib import Path
config = json.loads((Path.home() / ".receipt-hub" / "config.json").read_text())
exports_dir = Path(config.get("exports_dir", str(Path.home() / "Desktop" / "領収書" / "exports")))
exports_dir.mkdir(parents=True, exist_ok=True)
print(exports_dir / f"{datetime.now().strftime('%Y%m')}_経費.csv")
PY
```

返ってきた **絶対パス** をターゲットにして、

### 既存ファイルがある場合（追記）

1. **Read** ツールで既存CSVを読む
2. 既存内容の末尾に `/tmp/receipt_new_rows.csv` の中身（データ行のみ）を連結
3. **Write** ツールで結合後の全体を上書き保存

### ファイルがない場合（新規）

1. `/tmp/receipt_new_full.csv`（BOM + ヘッダー + データ行）の中身をそのまま **Write** ツールで保存

> 既存有無は `ls` か `test -f` で判定する。Read を試みて失敗したら新規扱い、でも可。

## 出力仕様

| 項目 | 内容 |
|------|------|
| 保存先 | `~/Desktop/領収書/exports/`（`~/.receipt-hub/config.json` の `exports_dir` で上書き可） |
| ファイル名 | `YYYYMM_経費.csv`（月次・追記） |
| 文字コード | UTF-8 BOM 付き（新規時は `--with-header` の出力に BOM が含まれる） |
| 改行 | LF（`\n`） |
| ヘッダー | `日付,店名・先方,金額(税込),税抜金額,消費税率,勘定科目,種別,メモ,ソース,確信度,元ファイル` |
| 書き込み手段 | **Claude Code の Write ツール**（Python は CSV テキスト生成のみ） |

## 完了後の報告

絶対パスをそのまま報告する（`exports/...` のような相対形は使わない。エラー53の遠因になる）。

```
→ /Users/xxx/Desktop/領収書/exports/202604_経費.csv に書き出しました
  領収書 N 件 / 請求書 N 件 / 合計 ¥XXX,XXX
  ※ 重複 N 件を除外しました（除外リストは上記）
```
