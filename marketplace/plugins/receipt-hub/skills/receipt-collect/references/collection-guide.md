# 収集ガイド

## Gmail 詳細手順

### 検索クエリの組み立て
期間指定あり:
```
(領収書 OR 請求書 OR receipt OR invoice) after:2026/03/01 before:2026/04/01
```

添付ファイルのみ:
```
(領収書 OR 請求書 OR receipt OR invoice) has:attachment after:2026/03/01 before:2026/04/01
```

### メール本文から金額を検出するパターン
- `¥[0-9,]+` または `[0-9,]+円`
- `合計[　 ]*¥?[0-9,]+`
- `金額[　 ]*¥?[0-9,]+`
- `total.*\$?[0-9,]+`

### Gmail 添付ファイルの取得手順

Gmail添付は **Drive には保存されていない** のが大半なので、Drive 検索ではなく `get_thread` のレスポンスに含まれる base64 データを直接デコードして保存する。

**Step 1: スレッドを取得**
```
mcp__d8d4c261-d776-4785-b50d-82ee22bc31bf__get_thread
  thread_id: <候補メールの thread_id>
```

**Step 2: 添付パートを抽出してデコード**

`messages[].payload.parts[]` を再帰的に走査し、`filename` が空でないパートの `body.data`（base64url）を取り出してデコードし、`~/Desktop/領収書/<ファイル名>` に保存する。

```bash
python3 - <<'PY'
import base64, pathlib
data = "<body.data>"
out = pathlib.Path("~/Desktop/領収書/<filename>").expanduser()
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)))
PY
```

**保存後の扱い**
- 収集フェーズでは `thread_id` を `id` に詰めて渡し、ファイル取得は解析フェーズの Step 1.5 で行う
- 解析フェーズで保存した絶対パスを `file_path` に記録する
- 添付パートが見つからない／デコードに失敗したときだけ、メール本文を Gemini に渡してフォールバック解析する

### 重複回避
処理済みのメールには Gmail ラベル「receipt-hub/処理済」を付与する。
次回の収集時はこのラベルがついているものをスキップ。

---

## Chatwork 詳細手順

### 日付フィルタリングの仕組み

Chatwork API の `list_room_files` レスポンスには各ファイルに `created_at`（Unixタイムスタンプ）が含まれる。
これを使って期間フィルタリングを行う。**ファイル名は判定に使わない**（名前がなんであれ対象期間のファイルは候補に含める）。

```
created_at >= 対象期間の開始日 0:00:00
created_at <= 対象期間の終了日 23:59:59
```

### ルームの優先度
1. 「経理」「会計」「finance」を含むルーム名
2. その他全ルーム

### 対象拡張子
`.pdf`, `.jpg`, `.jpeg`, `.png`, `.heic`

### 報告時の注意
「ファイルなし」のときも **何件確認したか・期間はどこか** を必ず報告する。例：
```
Chatwork: 0件（全5ルーム、2026/03/01〜03/31 の created_at で絞り込み済み）
```

---

## ローカルフォルダ 詳細手順

### スキャン方法

`scripts/scan_local.py` が mdfind でホーム全体を一括検索する：

| 対象 | 方法 | 基準日時 |
|------|------|---------|
| `~/`（ホーム全体） | mdfind（Spotlight） | ダウンロード日（正確） |
| `--dirs` 指定フォルダ | find | 更新日（mtime、オプション） |

### 実行コマンド

```bash
# デフォルト（ホーム全体を mdfind でスキャン）
python3 scripts/scan_local.py --start 2026-03-01 --end 2026-03-31

# 特定フォルダを追加で find スキャンしたい場合
python3 scripts/scan_local.py --start 2026-03-01 --end 2026-03-31 \
  --dirs ~/外付けHDD/領収書
```

### 出力

stderr: 人間向けサマリー（そのままユーザーに報告）
stdout: JSON（後続処理で使用）

```
ローカルスキャン結果（2026-03-01 〜 2026-03-31）:
  ~/ 全体 (5件) ← mdfind/ダウンロード日
  合計: 5 件
```
