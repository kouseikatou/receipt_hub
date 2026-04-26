---
name: receipt-collect
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

## 事前確認：収集設定

収集を開始する前に以下をユーザーに確認する（すでに指定されている場合はスキップ）：

1. **対象期間** — 例: 「2026年3月」「先月」「2026/03/01〜03/31」
2. **ローカルスキャンフォルダ** — 複数指定可。未指定ならデフォルト一覧を提示：
   - `~/Downloads`
   - `~/Desktop`
   - `~/Documents/領収書/未処理`

## 収集チャネル

### Gmail
- 検索クエリで期間・キーワードを絞り込む（詳細は references 参照）
- ラベル「receipt-hub/処理済」がついているものはスキップ

### Chatwork
Chatworkの日付フィルタリングは **ファイルの投稿日時（APIの `created_at` フィールド）** を使う。
ファイル名に「領収書」が含まれていなくても、投稿日が対象期間内であれば候補に含める。

手順：
1. `list_rooms` で全ルームを取得
2. 各ルームの `list_room_files` でファイル一覧を取得（`account_id` 等でフィルタ不要、全ファイル対象）
3. 各ファイルの `created_at`（Unix秒）を対象期間と照合してフィルタリング
4. 対象期間内のファイルのうち拡張子が `.pdf/.jpg/.jpeg/.png/.heic` のものを候補とする
5. ファイル名にキーワードがなくても候補に含め、解析フェーズで判断する

**報告形式**（「なし」の場合も根拠を明示）：
```
Chatwork: ○件（created_at が 2026/03/01〜03/31 のファイルを確認）
  - ルームA: 0件
  - ルームB: 2件（invoice_march.pdf, 20260315_請求.pdf）
```

### ローカルフォルダ
対象期間内に **更新されたファイル** を日付で絞り込む。

スキャン対象フォルダ（ユーザー指定 + デフォルト）を Bash で検索：
```bash
# 例: 2026年3月1日〜31日に更新されたPDF・画像
find ~/Downloads ~/Desktop -type f \
  \( -iname "*.pdf" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.heic" \) \
  -newermt "2026-02-28" ! -newermt "2026-04-01" \
  -not -path "*/.receipt_hub_processed/*"
```

`-newermt` で期間を指定し、ファイル名・フォルダ名に「領収書」が含まれなくてもヒットさせる。

**報告形式**：
```
ローカル: ○件（~/Downloads, ~/Desktop を 2026/03/01〜03/31 の更新日で検索）
  - ~/Downloads/invoice_202603.pdf（更新: 2026-03-15）
  - ~/Desktop/receipt.jpg（更新: 2026-03-22）
```
ファイルが0件のときも「どのフォルダをどの期間で検索したか」を報告する。

## 収集後の出力形式

```
[
  { source: "Gmail", id: "xxx", subject: "...", date: "...", type: "pdf" },
  { source: "Chatwork", room_id: "...", file_id: "...", filename: "...", created_at: "2026-03-15" },
  { source: "local", path: "/Users/.../Downloads/invoice.pdf", mtime: "2026-03-22" }
]
```
