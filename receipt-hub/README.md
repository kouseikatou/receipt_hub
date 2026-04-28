# Receipt Hub

Gmail・Chatwork・ローカルフォルダから領収書・請求書を自動収集し、AI解析でCSVファイルに出力する経理自動化プラグインです。

「領収書を処理して」と一言言うだけで、収集→解析→CSV出力まで全自動で完結します。出力したCSVはGoogleスプレッドシートやExcelにそのまま取り込めます。

---

## 目次

1. [できること](#できること)
2. [動作の仕組み](#動作の仕組み)
3. [必要な環境](#必要な環境)
4. [環境構築](#環境構築)
   - [Step 1: プラグインのインストール](#step-1-プラグインのインストール)
   - [Step 2: MCPサーバーの接続確認](#step-2-mcpサーバーの接続確認)
   - [Step 3: セットアップスクリプトを実行](#step-3-セットアップスクリプトを実行)
5. [動作確認テスト](#動作確認テスト)
6. [使い方](#使い方)
7. [CSVの列構成](#csvの列構成)
8. [スキル一覧](#スキル一覧)
9. [プラグインの更新（開発者向け）](#プラグインの更新開発者向け)
10. [トラブルシューティング](#トラブルシューティング)

---

## できること

| 機能 | 詳細 |
|------|------|
| **マルチチャネル収集** | Gmail・Chatwork・ローカルフォルダを横断して未処理の領収書・請求書を自動収集 |
| **AI解析** | PDF・画像（JPG/PNG/HEIC）・メール本文すべてに対応。金額・日付・店名を自動抽出 |
| **勘定科目の自動判定** | 「スタバ代 → 会議費」「タクシー → 旅費交通費」など、文脈から適切な科目を判定 |
| **CSV出力** | UTF-8 BOM付きCSVで出力。GoogleスプレッドシートもExcelも文字化けなしで取り込み可能 |
| **一発実行** | 「領収書を処理して」の一言で収集→解析→CSV出力まで全工程を完結 |

---

## 動作の仕組み

```
┌─────────────────────────────────────────────────────────┐
│                      Receipt Hub                        │
│                                                         │
│  [収集] ──────────────────────────────────────────      │
│   Gmail ──┐                                             │
│  Chatwork─┼──→ [AI解析] ──→ [勘定科目判定] ──→ [CSV]   │
│  ローカル ─┘   金額/日付/店名   会議費/交通費etc  出力   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

1. **収集フェーズ**: Gmail・Chatwork・ローカルフォルダを巡回し、領収書・請求書を検出
2. **解析フェーズ**: Gemini Vision で書類を解析し、構造化データに変換（OCR や regex は使用しない）
3. **判定フェーズ**: 日本の勘定科目ルールと過去履歴（`vendor_history.json`）に基づいて科目を自動判定。確信度が低くても処理は止めず `confidence` 列に記録
4. **出力フェーズ**: `~/Desktop/領収書/exports/YYYYMM_経費.csv` を生成（**月次ファイルに追記**、UTF-8 BOM 付き）。CSV ファイルへの書き込みは Claude Code の Write ツールで行い、Python は JSON → CSV テキストの変換のみを担当する（`com.apple.quarantine` 付与によるエラー53を構造的に回避するため）

---

## 必要な環境

| 要件 | バージョン | 用途 |
|------|-----------|------|
| Claude Code | 最新版 | プラグインの実行環境 |
| Python | 3.8以上 | CSVエクスポートスクリプト（標準ライブラリのみ） |

**必要な接続（Claude Codeに設定済みであること）:**

| 種別 | 名前 | 用途 |
|------|------|------|
| コネクタ | Gmail | メールの検索・添付ファイルの取得 |
| MCPサーバー | chatwork | ルーム・ファイル・メッセージの取得 |
| MCPサーバー | gemini | 画像・PDFの Vision 解析 |

外部APIやサードパーティライブラリは不要です。Pythonの標準ライブラリのみで動作します。

---

## 環境構築

### Step 1: プラグインのインストール

```bash
# GitHubマーケットプレイスを追加
claude plugin marketplace add "kouseikatou/receipt_hub"

# プラグインをインストール
claude plugin install receipt-hub@receipt-hub
```

確認：

```bash
claude plugin list
# receipt-hub@receipt-hub が表示されればOK
```

---

### Step 2: MCPサーバーの接続確認

```bash
claude mcp list
```

以下が `Connected` になっていることを確認：

```
chatwork   ✓ Connected
gemini     ✓ Connected
```

> **Gmail について**: Gmail は MCP サーバーではなく Claude Code の**コネクタ**として接続します。`claude mcp list` には表示されませんが、Claude Code の設定画面からコネクタとして追加してください。接続済みであれば `/receipt` スキル実行時に自動的に使用されます。

---

### Step 3: セットアップスクリプトを実行

```bash
python3 setup.py
```

以下が自動で完了します：
- `~/Desktop/領収書/exports/` の作成（CSV 出力先）
- `~/.receipt-hub/config.json` の保存（出力先パスを記録）
- `~/.receipt-hub/vendor_history.json` の初期化（勘定科目の学習用履歴）

「✓ セットアップ完了！」と表示されれば環境構築完了です。

---

## 動作確認テスト

環境構築後に以下を実行して、全工程を通しで確認します。

```bash
# プラグインディレクトリで実行する必要があります
cd "$(claude plugin path receipt-hub@receipt-hub)"  # または手元のクローン先
python3 tests/integration_test.py
```

**テストの流れ:**

```
[1/4] 環境チェック    カレント exports/・~/Desktop/領収書/exports/・Python バージョンを確認
[2/4] 解析テスト      4 種類のサンプル（tests/fixtures/sample_receipts.json）で金額・日付・勘定科目の抽出を確認
[3/4] CSV出力テスト   実際にCSVを生成してBOM・内容・エスケープを検証
[4/4] 後片付け        テスト用CSVを自動削除
```

全項目「合格」で本番利用の準備完了です。

---

## 使い方

### 基本（一発実行）

```
領収書を処理して
```

```
今月の経費をまとめて
```

```
先月分の領収書を全部CSVに出力して
```

実行フロー：
1. 対象期間を確認（指定済みならスキップ）
2. Gmail・Chatwork・ローカル全体から収集（確認なし）
3. 全ファイルを Gemini Vision で解析（確認なし）
4. 重複を自動除去
5. `~/Desktop/領収書/exports/YYYYMM_経費.csv` に追記出力
6. 完了報告（件数・合計金額・ファイルパス・確信度 low の件数）

### 個別実行

```
Gmailから今月の領収書を集めて
```

```
この画像の領収書を解析して（画像を添付）
```

```
解析結果をCSVに出力して
```

### CSVの取り込み方

**Googleスプレッドシート:** ファイル → インポート → アップロード → CSVファイルを選択

**Excel:** ファイルを開く → CSVを選択（文字コードはUTF-8で自動認識）

### 実行例

```
ユーザー: 今月の領収書を処理して

Claude: 対象期間: 2026年4月（2026/04/01〜04/30）で進めます。

[収集中...]
- Gmail: 8件を検出
- Chatwork: 2件を検出（created_at で期間絞り込み済み）
- ローカル ~/全体: 3件を検出（mdfind/ダウンロード日）
合計 13件

[解析中... Gemini Vision]
[重複除去... 1件除外]

✓ 完了
  収集 13件 → 重複除外 1件 → 出力 12件
  ~/Desktop/領収書/exports/202604_経費.csv（追記）
  領収書 9件 / 請求書 3件 / 合計 ¥89,240
  ⚠ 確信度 low: 1件（CSVの J列を確認してください）
```

---

## CSVの列構成

| 列 | 内容 | 例 |
|----|------|----|
| A | 日付 | 2024-01-15 |
| B | 店名・先方 | スターバックス渋谷店 |
| C | 金額（税込）| 1650 |
| D | 税抜金額 | 1500 |
| E | 消費税率 | 10% |
| F | 勘定科目 | 会議費 |
| G | 種別 | 領収書 |
| H | メモ | 打ち合わせ代 |
| I | ソース | Gmail |
| J | 確信度 | high / medium / low |
| K | 元ファイル | /Users/.../Downloads/invoice.pdf |

`確信度` が `low` の行は AI が判断できなかった項目があることを示します。該当行を確認・修正してから会計ソフトに取り込んでください。
`元ファイル` のパスをクリックすると原本 PDF・画像を開けます。

**freee への取り込み対応:**

| CSV列 | freee列 |
|-------|---------|
| 日付（A）| 発生日 |
| 勘定科目（F）| 借方勘定科目 |
| 金額・税込（C）| 借方金額 |
| 消費税率（E）| 借方税区分 |
| 店名・先方（B）| 取引先 |
| メモ（H）| 備考 |

---

## スキル一覧

| スキル | スラッシュコマンド | トリガーワード | 説明 |
|--------|-----------------|-------------|------|
| receipt | `/receipt` | 「領収書を処理して」「経費をまとめて」 | 収集→解析→CSV出力を一括実行 |
| receipt-collect | `/receipt-collect` | 「領収書を集めて」「メールを探して」 | 3チャネルから収集のみ |
| receipt-analyze | `/receipt-analyze` | 「解析して」「勘定科目を判定して」 | 1件の書類を解析のみ |
| receipt-csv | `/receipt-csv` | 「CSVに出力して」「エクスポートして」 | CSV出力のみ |
| receipt-accounts | `/receipt-accounts` | 「勘定科目は？」「会議費と交際費の違いは？」 | 日本の経費ルールを参照（自動）|

---

## プラグインの更新（開発者向け）

```bash
# スキルファイルを編集後
git add .
git commit -m "スキル名: 修正内容"
git push origin main

# Claude Codeでアップデート
claude plugin update receipt-hub
```

**アジャイル開発サイクル:**

```
スキルを試す → 改善点を発見 → SKILL.md を修正
     ↑                                  ↓
 再テスト    ←  claude plugin update  ←  git push
```

---

## トラブルシューティング

### Gmailの領収書が見つからない

- Gmail は MCP ではなく **コネクタ** として接続するため `claude mcp list` には表示されません。Claude Code の設定画面 → コネクタから接続状態を確認してください
- 「過去30日分の領収書を探して」など期間を明示すると精度が上がります

### 勘定科目の判定がズレる

- 「この経費の勘定科目を教えて」と聞くと詳しく解説します
- `skills/receipt-accounts/references/japanese-categories.md` にルールを追記してカスタマイズできます

### CSVが文字化けする

- ファイルの文字コードがUTF-8 BOM付きになっているか確認（テストで検証済みのはずですが）
- Excelで開く場合は「データ → テキストファイルから」→ UTF-8を選択

### Excel for Mac で「ファイルが見つかりません (エラー 53)」が出る

サンドボックス経由で Python が `open()` した CSV に macOS が `com.apple.quarantine` を付与すると、Excel for Mac はそのファイルを開けなくなります（中身は正常）。

**対処法:**

1. 既存ファイルから quarantine 属性を剥がす：
   ```bash
   xattr -d com.apple.quarantine ~/Desktop/領収書/exports/YYYYMM_経費.csv
   ```
2. 再発防止: 本プラグインは v0.2 以降、CSV の書き込みを **Claude Code の Write ツール** に切り替え、Python の `open(..., "w")` を全廃しています。最新版にアップデートしてください（`claude plugin update receipt-hub`）。

### プラグインが見つからない

```bash
claude plugin marketplace add "kouseikatou/receipt_hub"
claude plugin install receipt-hub@receipt-hub
```
