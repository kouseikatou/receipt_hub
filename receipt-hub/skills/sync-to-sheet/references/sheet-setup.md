# Googleスプレッドシート セットアップ手順（OAuth方式）

## 概要
サービスアカウント不要。自分のGoogleアカウントでブラウザ認証するだけ。
初回のみブラウザが開くので「許可」を押すだけ。2回目以降は完全自動。

---

## 初回セットアップ（30分以内で完了）

### Step 1: Python ライブラリのインストール
```bash
pip3 install gspread
```

### Step 2: Google Cloud でOAuth認証情報を作成
1. https://console.cloud.google.com/ を開く
2. 新規プロジェクト作成（例: `receipt-hub`）または既存プロジェクトを選択
3. 「APIとサービス」→「ライブラリ」で以下を有効化：
   - **Google Sheets API**
   - **Google Drive API**
4. 「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuthクライアントID」
5. アプリの種類: **「デスクトップアプリ」** を選択
6. 名前: `receipt-hub`（なんでもOK）
7. 「作成」→「JSONをダウンロード」

### Step 3: 認証情報ファイルを配置
ダウンロードしたJSONファイルを以下の場所に保存：
```bash
mkdir -p ~/.config/gspread
mv ~/Downloads/client_secret_*.json ~/.config/gspread/credentials.json
```

### Step 4: 初回ブラウザ認証
以下のPythonを1回だけ実行する：
```bash
python3 -c "
import gspread
gc = gspread.oauth()
print('認証成功！')
"
```
ブラウザが自動で開くので：
1. Googleアカウントを選択
2. 「receipt-hubがGoogleドライブとスプレッドシートにアクセスすることを許可しますか？」→「許可」
3. ターミナルに「認証成功！」と表示されたら完了

> 認証トークンは `~/.config/gspread/authorized_user.json` に保存される。
> 以降はこのファイルが自動的に使われ、ブラウザは開かない。

### Step 5: config.json を作成
```bash
mkdir -p ~/.receipt-hub
cat > ~/.receipt-hub/config.json << 'EOF'
{
  "spreadsheet_url": "YOUR_SPREADSHEET_URL_HERE",
  "local_folder": "~/Documents/領収書/未処理"
}
EOF
```
`YOUR_SPREADSHEET_URL_HERE` を実際のスプレッドシートのURLに書き換える。

### Step 6: スプレッドシートのヘッダー行を設定
A1〜K1 に以下を入力：
```
日付	店名・先方	金額(税込)	税抜金額	消費税率	勘定科目	種別	メモ	ソース	ステータス	記録日時
```

---

## 動作確認
```bash
python3 - << 'EOF'
import gspread, json, os

gc = gspread.oauth()
with open(os.path.expanduser("~/.receipt-hub/config.json")) as f:
    config = json.load(f)

sheet = gc.open_by_url(config["spreadsheet_url"]).sheet1
print(f"接続成功: {sheet.title}")
print(f"現在の行数: {len(sheet.get_all_values())}")
EOF
```

---

## サービスアカウント方式との違い
| 項目 | OAuth方式（今回） | サービスアカウント方式 |
|------|----------------|------------------|
| 設定の簡単さ | ◎ ブラウザで1回許可するだけ | △ サービスアカウント作成・共有設定が必要 |
| スプレッドシートの共有設定 | 不要（自分のアカウントでアクセス） | 必要（サービスアカウントメールを共有に追加） |
| トークンの有効期限 | 自動更新（再認証不要） | 無期限 |
| 向いているケース | 個人利用 | チーム・サーバー運用 |

---

## freee 取り込み用フォーマット（参考）
freeeの仕訳インポートCSVに変換する場合の列マッピング：

| receipt-hub列 | freee列 |
|--------------|---------|
| 日付 | 発生日 |
| 勘定科目 | 借方勘定科目 |
| 金額(税込) | 借方金額 |
| 消費税率 | 借方税区分 |
| 店名・先方 | 取引先 |
| メモ | 備考 |
