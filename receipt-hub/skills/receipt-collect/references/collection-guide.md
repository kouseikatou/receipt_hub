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

`scripts/scan_local.py` が mdfind と find を自動で使い分ける：

| フォルダ | 方法 | 基準日時 |
|----------|------|---------|
| `~/Downloads` | mdfind（Spotlight） | ダウンロード日（正確） |
| `~/Desktop` | mdfind（Spotlight） | ダウンロード日（正確） |
| `~/Documents/領収書/未処理` | find | 更新日（mtime） |
| ユーザー指定フォルダ | find | 更新日（mtime） |

### 実行コマンド

```bash
# デフォルト（Downloads + Desktop + Documents/領収書/未処理）
python3 scripts/scan_local.py --start 2026-03-01 --end 2026-03-31

# フォルダを追加指定
python3 scripts/scan_local.py --start 2026-03-01 --end 2026-03-31 \
  --dirs ~/Downloads ~/Desktop ~/Documents/領収書/未処理 ~/Documents/経費
```

### 出力

stderr: 人間向けサマリー（そのままユーザーに報告）
stdout: JSON（後続処理で使用）

```
ローカルスキャン結果（2026-03-01 〜 2026-03-31）:
  /Users/xxx/Downloads (2件) ← mdfind/ダウンロード日
  /Users/xxx/Desktop (1件) ← mdfind/ダウンロード日
  /Users/xxx/Documents/領収書/未処理 (0件) ← find/更新日
  合計: 3 件
```
