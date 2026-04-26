---
name: collect
description: |
  Gmail・Chatwork・ローカルフォルダから領収書・請求書を収集するスキル。「領収書を集めて」「メールの領収書を探して」「Chatworkの請求書を取得して」「フォルダをスキャンして」と言われたときに使う。
tools:
  - Read
  - Bash
  - mcp__d8d4c261-d776-4785-b50d-82ee22bc31bf__search_threads
  - mcp__d8d4c261-d776-4785-b50d-82ee22bc31bf__get_thread
  - mcp__d8d4c261-d776-4785-b50d-82ee22bc31bf__list_labels
  - mcp__chatwork__list_rooms
  - mcp__chatwork__list_room_messages
  - mcp__chatwork__list_room_files
  - mcp__chatwork__get_room_file
  - mcp__gdrive__search
---

# 領収書・請求書の収集

詳細な収集手順は `references/collection-guide.md` を参照。

## 収集チャネル概要

### Gmail
- 検索クエリ例: `領収書 OR 請求書 OR receipt OR invoice has:attachment`
- 対象ファイル: PDF添付、画像添付（JPG/PNG）、本文に金額記載のメール
- ラベル「処理済」がついているものはスキップ

### Chatwork
- 全ルームのファイル一覧を確認
- 「領収書」「請求書」「invoice」を含むファイル名を優先
- 本文に金額・日付が含まれるメッセージも対象

### ローカルフォルダ
- デフォルトパス: ユーザーが指定したフォルダ
- 対象拡張子: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.heic`
- サブフォルダも再帰的に検索

## 収集後の出力形式

収集したアイテムをリスト化して返す：
```
[
  { source: "Gmail", id: "xxx", subject: "...", date: "...", type: "pdf", raw: <data> },
  { source: "Chatwork", room_id: "...", file_id: "...", filename: "...", raw: <data> },
  { source: "local", path: "/path/to/file.pdf", filename: "..." }
]
```
