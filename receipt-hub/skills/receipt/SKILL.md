---
name: receipt
description: |
  領収書・請求書の収集から CSV 出力まで一括実行するメインスキル。「領収書処理して」「経費まとめて」「今月の領収書」「レシート全部処理して」と言われたときに使う。Gmail・Chatwork・ローカルフォルダを巡回し、AI解析でCSVファイルに出力する。
tools:
  - Read
  - Bash
  - mcp__d8d4c261-d776-4785-b50d-82ee22bc31bf__search_threads
  - mcp__d8d4c261-d776-4785-b50d-82ee22bc31bf__get_thread
  - mcp__chatwork__list_rooms
  - mcp__chatwork__list_room_messages
  - mcp__chatwork__get_room_message
---

# 領収書パイプライン 一括実行

## 基本方針

**途中で止まらない。** 収集→解析→重複除去→CSV出力を全自動で完走する。
ユーザーへの確認は対象期間の指定のみ。それ以外は止めずに処理する。
判断はCSV出力後にユーザーが行う。

## Step 1: 対象期間の確認

期間が指定されていない場合のみ確認する。指定済みならスキップ。

## Step 2: 収集フェーズ

`receipt-collect` スキルの手順に従い、3チャネルを並行して収集する：

1. Gmail — 対象期間のスレッドを検索
2. Chatwork — 全ルームのファイルを `created_at` で絞り込み
3. ローカル — `scan_local.py` でホーム全体をスキャン

収集件数を報告してそのまま次へ進む。スキップしない。

## Step 3: 解析フェーズ

`receipt-analyze` スキルの手順に従い、全件を Gemini Vision で解析する。
途中でユーザーに確認しない。確信度が low のものも処理を止めずそのまま解析する。

## Step 4: 重複除去

```bash
python3 scripts/dedup.py items.json
```

重複を自動除去してそのまま次へ進む。除去した件数は最後にまとめて報告する。

## Step 5: CSV 出力

`receipt-csv` スキルの手順に従い CSV を生成する。確認なしで即出力。

## Step 6: 完了報告

処理が終わったら以下をまとめて報告する：

```
✓ 完了
  収集: N 件（Gmail N / Chatwork N / ローカル N）
  重複除外: N 件
  CSV出力: ~/Documents/領収書/exports/YYYYMMDD_経費.csv
  　領収書 N 件 / 請求書 N 件 / 合計 ¥XXX,XXX

⚠ 要確認（confidence=low）: N 件
  CSVの「確信度」列が「low」の行を確認してください。
```

エラーが発生したアイテムは処理をスキップして最後に件数だけ報告する。
