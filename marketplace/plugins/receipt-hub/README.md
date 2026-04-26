# Receipt Hub

Gmail・Chatwork・ローカルフォルダから領収書・請求書を自動収集し、AI解析でGoogleスプレッドシートに記録する経理自動化プラグインです。

「領収書を処理して」と一言言うだけで、収集→解析→記録まで全自動で完結します。

---

## 目次

1. [できること](#できること)
2. [動作の仕組み](#動作の仕組み)
3. [必要な環境](#必要な環境)
4. [環境構築](#環境構築)
   - [Step 1: プラグインのインストール](#step-1-プラグインのインストール)
   - [Step 2: MCPサーバーの接続確認](#step-2-mcpサーバーの接続確認)
   - [Step 3: Google Sheets OAuth認証](#step-3-google-sheets-oauth認証)
   - [Step 4: Googleスプレッドシートの準備](#step-4-googleスプレッドシートの準備)
   - [Step 5: ローカルフォルダの準備](#step-5-ローカルフォルダの準備)
   - [Step 6: config.json の作成](#step-6-configjson-の作成)
5. [使い方](#使い方)
6. [スプレッドシートの列構成](#スプレッドシートの列構成)
7. [スキル一覧](#スキル一覧)
8. [プラグインの更新（開発者向け）](#プラグインの更新開発者向け)
9. [トラブルシューティング](#トラブルシューティング)

---

## できること

| 機能 | 詳細 |
|------|------|
| **マルチチャネル収集** | Gmail・Chatwork・ローカルフォルダを横断して未処理の領収書・請求書を自動収集 |
| **AI解析** | PDF・画像（JPG/PNG/HEIC）・メール本文すべてに対応。金額・日付・店名を自動抽出 |
| **勘定科目の自動判定** | 「スタバ代 → 会議費」「タクシー → 旅費交通費」など、文脈から適切な科目を判定 |
| **スプレッドシートへの自動記録** | 11列の標準フォーマットで記録。freee・マネーフォワードへの取り込みにも対応 |
| **一発実行** | 「領収書を処理して」の一言で収集→解析→記録まで全工程を完結 |

---

## 動作の仕組み

```
┌─────────────────────────────────────────────────────────┐
│                      Receipt Hub                        │
│                                                         │
│  [収集] ──────────────────────────────────────────      │
│   Gmail ──┐                                             │
│  Chatwork─┼──→ [AI解析] ──→ [勘定科目判定] ──→ [記録]  │
│  ローカル ─┘   金額/日付/店名   会議費/交通費etc  Sheets │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

1. **収集フェーズ**: Gmail・Chatwork・ローカルフォルダを巡回し、領収書・請求書を検出
2. **解析フェーズ**: Gemini Vision + OCRで書類を解析し、構造化データ（JSON）に変換
3. **判定フェーズ**: 日本の勘定科目ルールに基づいて科目を自動判定（不明な場合はユーザーに確認）
4. **記録フェーズ**: gspread（OAuth認証）でGoogleスプレッドシートに追記

---

## 必要な環境

| 要件 | バージョン | 用途 |
|------|-----------|------|
| Claude Code | 最新版 | プラグインの実行環境 |
| Python | 3.8以上 | gspreadによるSheets書き込み |
| pip | 最新版 | Pythonライブラリの管理 |
| Googleアカウント | - | スプレッドシートへのアクセス |

**必要なMCPサーバー（Claude Codeに接続済みであること）:**

| MCP | 用途 |
|-----|------|
| Gmail | メールの検索・添付ファイルの取得 |
| Chatwork | ルーム・ファイル・メッセージの取得 |
| Google Drive | ドライブ内ファイルの検索 |
| Gemini | 画像・PDFのOCR解析 |

---

## 環境構築

### Step 1: プラグインのインストール

Claude Code のターミナルで以下を実行します。

```bash
# GitHubマーケットプレイスを追加
claude plugin marketplace add "kouseikatou/receipt_hub"

# プラグインをインストール
claude plugin install receipt-hub@receipt-hub
```

インストールを確認：

```bash
claude plugin list
# receipt-hub@receipt-hub が表示されればOK
```

---

### Step 2: MCPサーバーの接続確認

以下のコマンドで必要なMCPが接続されているか確認します。

```bash
claude mcp list
```

**確認するサーバー:**

```
gmail      ✓ Connected   ← メール収集に必要
chatwork   ✓ Connected   ← Chatwork収集に必要
gdrive     ✓ Connected   ← ドライブ検索に必要
gemini     ✓ Connected   ← 画像・PDF解析に必要
```

接続されていない場合は Claude Code の設定（Settings → MCP Servers）から追加してください。

---

### Step 3: Google Sheets OAuth認証

サービスアカウント不要。自分のGoogleアカウントでブラウザ認証するだけです。**初回のみブラウザが開きます。2回目以降は完全自動です。**

#### 3-1. gspread をインストール

```bash
pip3 install gspread
```

#### 3-2. Google Cloud で OAuth 認証情報を作成

1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. 新規プロジェクトを作成（例: `receipt-hub`）
3. 左メニュー「APIとサービス」→「ライブラリ」で以下を有効化：
   - `Google Sheets API`
   - `Google Drive API`
4. 「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuthクライアントID」
5. アプリの種類: **「デスクトップアプリ」** を選択
6. 名前は任意（例: `receipt-hub`）→「作成」
7. 「JSONをダウンロード」をクリック

#### 3-3. 認証情報ファイルを配置

```bash
mkdir -p ~/.config/gspread
mv ~/Downloads/client_secret_*.json ~/.config/gspread/credentials.json
```

#### 3-4. 初回ブラウザ認証（1回だけ）

```bash
python3 -c "
import gspread
gc = gspread.oauth()
print('✓ 認証成功！')
"
```

ブラウザが自動で開くので：
1. Googleアカウントを選択
2. 「このアプリがGoogleドライブとスプレッドシートにアクセスすることを許可しますか？」→「許可」
3. ターミナルに「✓ 認証成功！」と表示されたら完了

> 認証トークンは `~/.config/gspread/authorized_user.json` に保存されます。
> 以降この操作は不要です。

---

### Step 4: Googleスプレッドシートの準備

1. [Google スプレッドシート](https://sheets.google.com) を開き、新しいシートを作成
2. シート名を任意で設定（例: `経費管理2024`）
3. **1行目にヘッダーを入力**（A1〜K1）：

```
日付	店名・先方	金額(税込)	税抜金額	消費税率	勘定科目	種別	メモ	ソース	ステータス	記録日時
```

4. スプレッドシートのURLをコピーしておく（次のステップで使用）

---

### Step 5: ローカルフォルダの準備（任意）

スマホで撮影したレシート画像やダウンロードしたPDFをローカルで管理する場合に設定します。

```bash
mkdir -p ~/Documents/領収書/未処理
mkdir -p ~/Documents/領収書/処理済
```

**使い方:**
- `未処理/` フォルダに領収書・請求書ファイル（PDF/JPG/PNG）を入れる
- 処理が完了すると自動的に `処理済/` に移動される

---

### Step 6: config.json の作成

スプレッドシートURLとフォルダパスを保存します。

```bash
mkdir -p ~/.receipt-hub
```

以下の内容で `~/.receipt-hub/config.json` を作成し、**YOUR_SPREADSHEET_URL** を実際のURLに書き換えてください：

```bash
cat > ~/.receipt-hub/config.json << 'EOF'
{
  "spreadsheet_url": "YOUR_SPREADSHEET_URL",
  "local_folder": "~/Documents/領収書/未処理"
}
EOF
```

**設定例:**
```json
{
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1ABC...xyz/edit",
  "local_folder": "~/Documents/領収書/未処理"
}
```

#### 動作確認

すべての設定が正しいか確認します：

```bash
python3 - << 'EOF'
import gspread, json, os

gc = gspread.oauth()
with open(os.path.expanduser("~/.receipt-hub/config.json")) as f:
    config = json.load(f)

sheet = gc.open_by_url(config["spreadsheet_url"]).sheet1
print(f"✓ 接続成功: {sheet.title}")
print(f"✓ 現在の行数: {len(sheet.get_all_values())}")
EOF
```

「✓ 接続成功」と表示されれば環境構築完了です。

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
先月分の領収書を全部スプレッドシートに記録して
```

実行すると以下のフローが自動で走ります：
1. 対象期間の確認（初回のみ）
2. Gmail・Chatwork・ローカルフォルダから収集
3. 各書類を解析（金額・日付・勘定科目を抽出）
4. 解析結果をテーブルで提示し確認
5. スプレッドシートに書き込み
6. 完了報告（処理件数・合計金額）

### 個別実行

特定の操作だけ実行したい場合：

```
Gmailから今月の領収書を集めて
```

```
この画像の領収書を解析して（画像を添付）
```

```
解析結果をスプレッドシートに記録して
```

```
この経費の勘定科目を教えて
```

### 実行例

```
ユーザー: 今月の領収書を処理して

Claude: 対象期間: 2024年1月（2024/01/01〜01/31）で進めます。

[収集中...]
- Gmail: 8件の領収書・請求書を検出
- Chatwork: 2件のファイルを検出
- ローカル: 3件のファイルを検出
合計 13件 を収集しました。

[解析中...]

| 日付 | 店名・先方 | 金額 | 勘定科目 | 種別 |
|------|-----------|------|---------|------|
| 01/05 | スターバックス渋谷 | ¥1,650 | 会議費 | 領収書 |
| 01/08 | タクシー 東京 | ¥2,340 | 旅費交通費 | 領収書 |
| 01/12 | AWS | $89.50 | 通信費 | 請求書 |
...

この内容でスプレッドシートに記録しますか？
```

---

## スプレッドシートの列構成

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
| J | ステータス | 処理済 |
| K | 記録日時 | 2024-01-20 10:30 |

**freee への取り込み対応:**

| receipt-hub 列 | freee 列 |
|--------------|---------|
| 日付（A）| 発生日 |
| 勘定科目（F）| 借方勘定科目 |
| 金額・税込（C）| 借方金額 |
| 消費税率（E）| 借方税区分 |
| 店名・先方（B）| 取引先 |
| メモ（H）| 備考 |

---

## スキル一覧

| スキル | トリガーワード | 説明 |
|--------|-------------|------|
| `run-receipt-pipeline` | 「領収書を処理して」「経費をまとめて」 | 収集→解析→記録を一括実行 |
| `collect-receipts` | 「領収書を集めて」「メールを探して」 | 3チャネルから収集のみ |
| `process-document` | 「解析して」「勘定科目を判定して」 | 1件の書類を解析のみ |
| `sync-to-sheet` | 「スプレッドシートに記録して」 | 記録のみ |
| `accounting-knowledge` | 「勘定科目は？」「会議費と交際費の違いは？」 | 日本の経費ルールを参照（自動） |

---

## 動作確認テスト

環境構築が完了したら、以下のコマンドで全工程を通しで確認できます。

```bash
python3 tests/integration_test.py
```

**テストの流れ:**

```
[1/4] 環境チェック         gspread認証・config.json・スプレッドシートURLを確認
[2/4] サンプル領収書の解析  4種類のサンプルで金額・日付・勘定科目の抽出を確認
[3/4] Sheets書き込みテスト  テスト行をスプレッドシートに書き込んで読み取りを確認
[4/4] 後片付け             書き込んだテストデータを自動削除
```

全項目「合格」になれば本番利用の準備完了です。テスト用データは自動削除されるため、スプレッドシートが汚れる心配はありません。

---

## プラグインの更新（開発者向け）

スキルファイルを編集してGitHubにプッシュすれば、即座に反映されます。

```bash
# 1. スキルファイルを編集
#    marketplace/plugins/receipt-hub/skills/ 以下のSKILL.mdを修正

# 2. GitHubにプッシュ
git add .
git commit -m "スキル名: 修正内容"
git push origin main

# 3. Claude Codeでアップデート
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

### gspread が認証エラーになる

```bash
# トークンを削除して再認証
rm ~/.config/gspread/authorized_user.json
python3 -c "import gspread; gspread.oauth()"
```

### スプレッドシートに書き込めない

- `config.json` の `spreadsheet_url` が正しいか確認
- スプレッドシートのURLは `/edit` まで含めて貼り付けてください
- Google Sheets API と Google Drive API が有効になっているか Google Cloud Console で確認

### Gmailの領収書が見つからない

- Gmail MCP が `claude mcp list` で `Connected` になっているか確認
- 「過去30日分の領収書を探して」など期間を明示すると精度が上がります

### 勘定科目の判定がズレる

- 「この経費の勘定科目を教えて」と聞くと詳しく解説します
- スキルファイル `skills/accounting-knowledge/references/japanese-categories.md` にルールを追記してカスタマイズできます

### プラグインが見つからない

```bash
# マーケットプレイスの再追加
claude plugin marketplace add "kouseikatou/receipt_hub"
claude plugin install receipt-hub@receipt-hub
```
