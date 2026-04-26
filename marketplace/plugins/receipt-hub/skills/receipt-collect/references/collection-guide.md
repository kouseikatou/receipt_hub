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

### スキャン対象フォルダ

ユーザーが指定したフォルダを優先。未指定の場合はデフォルト一覧を提示して選ばせる：

| フォルダ | 用途 |
|----------|------|
| `~/Downloads` | ブラウザ・アプリからダウンロードしたファイル |
| `~/Desktop` | デスクトップに置いたファイル |
| `~/Documents/領収書/未処理` | 手動で整理済みのファイル |

複数フォルダを同時スキャン可能（スペース区切りで `find` に渡す）。

### 日付フィルタリング

`find` の `-newermt` オプションでファイルの更新日時（mtime）を使って絞り込む：

```bash
# 2026年3月のファイルを ~/Downloads と ~/Desktop から検索
find ~/Downloads ~/Desktop -type f \
  \( -iname "*.pdf" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.heic" \) \
  -newermt "2026-02-28 23:59:59" ! -newermt "2026-03-31 23:59:59"
```

ファイル名に「領収書」が含まれていなくても、日付が範囲内であれば全て候補とする。
解析フェーズ（receipt-analyze）で領収書・請求書かどうかを判断する。

### 処理済みファイルの管理

スキャン済みファイルのパスを `~/.receipt-hub/processed_files.txt` に記録し、次回スキャン時にスキップ：

```bash
# 処理済みリストに追加
echo "/path/to/file.pdf" >> ~/.receipt-hub/processed_files.txt

# 処理済みを除外して検索
find ... | grep -vxFf ~/.receipt-hub/processed_files.txt
```

### 報告形式

ファイルが見つかった場合：
```
ローカル: 3件（~/Downloads, ~/Desktop を 2026/03/01〜03/31 の更新日で検索）
  - ~/Downloads/invoice_202603.pdf（更新: 2026-03-15 14:32）
  - ~/Downloads/receipt_starbucks.jpg（更新: 2026-03-22 09:15）
  - ~/Desktop/bill.pdf（更新: 2026-03-28 18:00）
```

ファイルが見つからなかった場合（根拠を明示）：
```
ローカル: 0件（~/Downloads, ~/Desktop を 2026/03/01〜03/31 の更新日で検索。対象拡張子: pdf/jpg/jpeg/png/heic）
```
