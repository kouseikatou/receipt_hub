---
name: sync-to-sheet
description: |
  解析済みの領収書・請求書データをGoogleスプレッドシートに記録するスキル。「スプレッドシートに書き込んで」「シートに記録して」「Googleスプレッドシートを更新して」と言われたときに使う。gspread + OAuth（ブラウザ認証）で動作する。
tools:
  - Bash
  - Read
---

# Googleスプレッドシートへの記録

詳細なシート設定手順は `references/sheet-setup.md` を参照。

## 列構成（標準）

| 列 | 内容 | 例 |
|----|------|-----|
| A | 日付 | 2024-01-15 |
| B | 店名・先方 | スターバックス渋谷店 |
| C | 金額（税込）| 1650 |
| D | 税抜金額 | 1500 |
| E | 消費税率 | 10% |
| F | 勘定科目 | 会議費 |
| G | 種別 | 領収書 |
| H | メモ | 打ち合わせ・スタバ渋谷 |
| I | ソース | Gmail |
| J | ステータス | 処理済 |
| K | 記録日時 | 2024-01-20 10:30 |

## 書き込み手順

### 1. 環境確認
```bash
python3 -c "import gspread; print('gspread OK')"
```
エラーの場合は `references/sheet-setup.md` のセットアップ手順を案内する。

### 2. スプレッドシートに追記
```python
import gspread
from datetime import datetime

# OAuth認証（初回のみブラウザが開く、2回目以降はトークンを自動使用）
gc = gspread.oauth()

# config.json からスプレッドシートURLを読み込む
import json, os
config_path = os.path.expanduser("~/.receipt-hub/config.json")
with open(config_path) as f:
    config = json.load(f)

sheet = gc.open_by_url(config["spreadsheet_url"]).sheet1

# 追記する行データ
row = [
    item["date"],
    item["vendor"],
    item["amount"],
    item.get("amount_excl_tax", ""),
    f"{item.get('tax_rate', 10)}%",
    item["category"],
    item["doc_type"],
    item.get("memo", ""),
    item.get("source", ""),
    "処理済",
    datetime.now().strftime("%Y-%m-%d %H:%M"),
]
sheet.append_row(row, value_input_option="USER_ENTERED")
```

### 3. 重複確認
書き込み前に既存データの日付・金額・店名を照合し、重複がある場合はスキップしてユーザーに報告する。

## config.json の管理
スプレッドシートURLとローカルフォルダパスは `~/.receipt-hub/config.json` に保存されている。
`python3 setup.py` で自動生成されるため、通常は手動編集不要。

```json
{
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/xxx",
  "local_folder": "~/Documents/領収書/未処理"
}
```

config.json が存在しない場合は `python3 setup.py` を実行するようユーザーに案内する。
