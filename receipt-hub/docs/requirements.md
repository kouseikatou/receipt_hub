# Receipt Hub 要件定義

## 基本方針

- 収集→解析→重複除去→CSV出力を**途中確認なしで全自動**で完走する
- 判断はCSV出力後にユーザーが行う
- 使えば使うほど精度が上がる（vendor履歴の蓄積）

---

## 収集

### チャネル
| チャネル | 接続方式 | 日付フィルタ |
|---------|---------|------------|
| Gmail | Claude Desktop コネクタ | メール受信日（Gmail検索クエリ） |
| Chatwork | MCP（`chatwork`） | ファイルの `created_at`（投稿日時） |
| ローカル | `scripts/scan_local.py` | ダウンロード日 or 更新日（mtime） |

### ローカルスキャン
- `~/`（ホーム全体）→ mdfind でダウンロード日基準
- `~/Documents/領収書/未処理` → find で更新日（mtime）基準（補完）
- フォルダ指定は不要。全自動。

### 対象拡張子
`.pdf` `.jpg` `.jpeg` `.png` `.heic`

---

## 解析

- **全ファイルを Gemini Vision（`mcp__gemini__analyze_media`）で解析**
- regex・pdftotext は使わない
- メール本文のみの場合はテキストを Gemini に渡す

### 高速パス（vendor履歴）
`scripts/history.py lookup` で count >= 3 のベンダーは Gemini をスキップして履歴の勘定科目を採用

### 確信度
| 値 | 意味 |
|----|------|
| high | 全項目明確 |
| medium | 金額か日付が不明瞭 |
| low | 主要項目が複数不明、または種別不明 |

確信度にかかわらず処理を止めない。CSV の J列に記録してユーザーが後から確認。

### 勘定科目の判定順
1. vendor履歴（count >= 3）→ 履歴の category を採用
2. `receipt-accounts` スキルのルール → 自動判定
3. 絞れない場合 → confidence を medium に下げてそのまま出力

---

## 重複除去

`scripts/dedup.py` を CSV 出力前に自動実行。確認なしで除去。

同一アイテムの条件（2つ以上一致）:
1. 金額が同じ
2. 日付 ±1日以内
3. ベンダー名の類似度 0.7 以上、または一方が他方を含む

---

## CSV出力

| 項目 | 仕様 |
|------|------|
| 保存先 | `~/Documents/領収書/exports/` |
| ファイル名 | `YYYYMM_経費.csv`（月次） |
| 書き込みモード | 同月ファイルが存在すれば**追記**、なければ新規作成 |
| 文字コード | UTF-8 BOM付き |

### 列構成（A〜K）

| 列 | 項目 | 例 |
|----|------|----|
| A | 日付 | 2026-03-15 |
| B | 店名・先方 | スターバックス渋谷店 |
| C | 金額（税込） | 1650 |
| D | 税抜金額 | 1500 |
| E | 消費税率 | 10% |
| F | 勘定科目 | 会議費 |
| G | 種別 | 領収書 / 請求書 |
| H | メモ | 打ち合わせ代 |
| I | ソース | Gmail / Chatwork / ローカル |
| J | 確信度 | high / medium / low |
| K | 元ファイル | /Users/.../invoice.pdf |

---

## vendor履歴（学習）

| ファイル | `~/.receipt-hub/vendor_history.json` |
|---------|--------------------------------------|
| スクリプト | `scripts/history.py` |

- `lookup` → ベンダー名で検索（count >= 3 で confidence=high）
- `add` → 解析後に全件自動書き戻し（確認不要）
- `list` / `stats` → 蓄積状況の確認

---

## スキル一覧

| コマンド | 役割 |
|---------|------|
| `/receipt` | 全自動パイプライン（期間を聞くだけで完走） |
| `/receipt-collect` | 収集のみ |
| `/receipt-analyze` | 1件解析（PDF貼り付けにも対応） |
| `/receipt-csv` | CSV追記出力のみ |
| `/receipt-accounts` | 勘定科目ルールの参照 |

---

## スクリプト一覧

| ファイル | 役割 |
|---------|------|
| `scripts/history.py` | vendor履歴の参照・書き込み |
| `scripts/dedup.py` | 重複検出・除去 |
| `scripts/scan_local.py` | ローカルファイルスキャン（mdfind + find） |
| `setup.py` | 初回セットアップ（フォルダ作成・config・履歴初期化） |
| `tests/integration_test.py` | 総合テスト |

---

## 設定ファイル

| ファイル | 内容 |
|---------|------|
| `~/.receipt-hub/config.json` | exports_dir・local_folder |
| `~/.receipt-hub/vendor_history.json` | ベンダー→勘定科目の学習データ |

---

## 必要な接続

| 種別 | 名前 | 用途 |
|------|------|------|
| コネクタ | Gmail | メール検索・添付取得 |
| MCPサーバー | chatwork | ルーム・ファイル取得 |
| MCPサーバー | gemini | Gemini Vision 解析 |
