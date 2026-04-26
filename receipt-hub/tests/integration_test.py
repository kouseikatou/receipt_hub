#!/usr/bin/env python3
"""
Receipt Hub 総合テスト

使い方:
    python3 tests/integration_test.py

全工程（環境チェック → 解析 → Sheets書き込み → 後片付け）を通しで確認します。
テスト用に書き込んだデータは自動的に削除されます。
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# 表示ユーティリティ
# ─────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):    print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):  print(f"  {RED}✗{RESET} {msg}"); return False
def warn(msg):  print(f"  {YELLOW}⚠{RESET} {msg}")
def section(n, title): print(f"\n{BOLD}[{n}] {title}{RESET}")


# ─────────────────────────────────────────────
# Step 1: 環境チェック
# ─────────────────────────────────────────────

def check_environment():
    section("1/4", "環境チェック")
    passed = True

    # gspread インポート確認
    try:
        import gspread
        ok(f"gspread インストール済み (v{gspread.__version__})")
    except ImportError:
        fail("gspread が見つかりません。`pip3 install gspread` を実行してください。")
        passed = False

    # OAuth トークン確認
    token_path = Path.home() / ".config" / "gspread" / "authorized_user.json"
    cred_path  = Path.home() / ".config" / "gspread" / "credentials.json"
    if token_path.exists():
        ok("OAuth トークン確認済み")
    elif cred_path.exists():
        warn("credentials.json はありますが初回認証が未完了です。")
        warn("`python3 -c \"import gspread; gspread.oauth()\"` を実行してブラウザで許可してください。")
        passed = False
    else:
        fail("OAuth 認証情報が見つかりません。README の Step 3 を参照してください。")
        passed = False

    # config.json 確認
    config_path = Path.home() / ".receipt-hub" / "config.json"
    if not config_path.exists():
        fail(f"config.json が見つかりません: {config_path}")
        fail("README の Step 6 を参照して作成してください。")
        passed = False
    else:
        try:
            with open(config_path) as f:
                config = json.load(f)
            url = config.get("spreadsheet_url", "")
            if "docs.google.com/spreadsheets" not in url:
                fail("config.json の spreadsheet_url が正しくありません。")
                passed = False
            else:
                ok("config.json 確認済み")
        except json.JSONDecodeError:
            fail("config.json のJSON形式が不正です。")
            passed = False

    return passed, config if passed else None


# ─────────────────────────────────────────────
# Step 2: サンプル領収書の解析テスト
# ─────────────────────────────────────────────

CATEGORY_RULES = {
    "会議費":     ["スターバックス", "カフェ", "打ち合わせ", "コーヒー", "ドトール", "タリーズ"],
    "旅費交通費": ["タクシー", "電車", "バス", "新幹線", "飛行機", "suica", "ic", "go"],
    "通信費":     ["aws", "amazon web services", "google cloud", "さくら", "さくらインターネット",
                   "cloudflare", "netlify", "vercel", "heroku", "github"],
    "新聞図書費": ["amazon.co.jp", "kindle", "書籍", "本", "udemy", "book"],
    "消耗品費":   ["ヨドバシ", "ビックカメラ", "amazon", "文具", "事務用品"],
    "広告宣伝費": ["meta", "google ads", "facebook", "twitter", "名刺"],
    "外注費":     ["業務委託", "外注", "制作費", "フリーランス"],
    "地代家賃":   ["家賃", "コワーキング", "レンタルオフィス", "ウィーワーク"],
    "研修費":     ["セミナー", "勉強会", "udemy", "connpass", "研修"],
}

AMOUNT_PATTERN  = re.compile(r"[¥\\]?\s*([\d,]+)\s*円?")
DATE_PATTERNS   = [
    (re.compile(r"(\d{4})[/\-年](\d{1,2})[/\-月](\d{1,2})"), "%Y-%m-%d"),
    (re.compile(r"R(\d+)[./年](\d{1,2})[./月](\d{1,2})"),     "reiwa"),
]

def parse_amount(text):
    matches = AMOUNT_PATTERN.findall(text.replace(",", ""))
    amounts = [int(m.replace(",", "")) for m in matches if m]
    return max(amounts) if amounts else None

def parse_date(text):
    for pattern, fmt in DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            if fmt == "reiwa":
                year = 2018 + int(m.group(1))
                return f"{year}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None

def parse_category(text):
    lower = text.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(kw.lower() in lower for kw in keywords):
            return category
    return "雑費"

def check_parsing():
    section("2/4", "サンプル領収書の解析テスト")

    fixtures_path = Path(__file__).parent / "fixtures" / "sample_receipts.json"
    with open(fixtures_path) as f:
        samples = json.load(f)

    passed = True
    for sample in samples:
        desc     = sample["description"]
        raw      = sample["raw_text"]
        expected = sample["expected"]

        amount   = parse_amount(raw)
        date     = parse_date(raw)
        category = parse_category(raw)

        errors = []
        if amount != expected["amount"]:
            errors.append(f"金額: 期待={expected['amount']} 実際={amount}")
        if date != expected["date"]:
            errors.append(f"日付: 期待={expected['date']} 実際={date}")
        if category != expected["category"]:
            errors.append(f"勘定科目: 期待={expected['category']} 実際={category}")

        if errors:
            fail(f"{desc}")
            for e in errors:
                print(f"      → {e}")
            passed = False
        else:
            ok(f"{desc} (金額:{amount}円 / 日付:{date} / 科目:{category})")

    return passed


# ─────────────────────────────────────────────
# Step 3: Googleスプレッドシート 書き込みテスト
# ─────────────────────────────────────────────

TEST_MARKER = "[RECEIPT_HUB_TEST]"

def check_sheets(config):
    section("3/4", "Googleスプレッドシート 書き込みテスト")

    try:
        import gspread
    except ImportError:
        fail("gspread が使えません。")
        return False, None

    try:
        gc    = gspread.oauth()
        sheet = gc.open_by_url(config["spreadsheet_url"]).sheet1
        ok(f"スプレッドシートに接続: {sheet.title}")
    except Exception as e:
        fail(f"スプレッドシートへの接続に失敗: {e}")
        return False, None

    # テスト行を書き込む
    test_row = [
        "2024-01-01",
        TEST_MARKER,
        "9999",
        "9090",
        "10%",
        "雑費",
        "領収書",
        "統合テスト用データ（自動削除）",
        "test",
        "テスト中",
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    ]
    try:
        sheet.append_row(test_row, value_input_option="USER_ENTERED")
        ok("テスト行の書き込み成功")
    except Exception as e:
        fail(f"書き込みに失敗: {e}")
        return False, sheet

    # 書き込んだ行を確認
    try:
        all_values = sheet.get_all_values()
        written = any(TEST_MARKER in row for row in all_values)
        if written:
            ok("書き込んだデータの読み取り確認済み")
        else:
            fail("書き込んだデータが見つかりません。")
            return False, sheet
    except Exception as e:
        fail(f"読み取りに失敗: {e}")
        return False, sheet

    return True, sheet


# ─────────────────────────────────────────────
# Step 4: 後片付け（テストデータ削除）
# ─────────────────────────────────────────────

def cleanup(sheet):
    section("4/4", "後片付け（テストデータ削除）")

    if sheet is None:
        warn("シートに接続されていないためスキップします。")
        return True

    try:
        all_values = sheet.get_all_values()
        rows_to_delete = [
            i + 1
            for i, row in enumerate(all_values)
            if TEST_MARKER in row
        ]
        for row_num in reversed(rows_to_delete):
            sheet.delete_rows(row_num)
        ok(f"テスト行を削除しました（{len(rows_to_delete)}行）")
        return True
    except Exception as e:
        warn(f"テスト行の削除に失敗しました（手動で削除してください）: {e}")
        warn(f"  条件: B列が '{TEST_MARKER}' の行")
        return False


# ─────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────

def main():
    print(f"\n{BOLD}{'═' * 50}")
    print("  Receipt Hub 総合テスト")
    print(f"{'═' * 50}{RESET}")

    results = []
    sheet   = None

    # Step 1
    env_ok, config = check_environment()
    results.append(("環境チェック", env_ok))
    if not env_ok:
        print(f"\n{RED}環境が整っていません。上記のエラーを解消してから再実行してください。{RESET}")
        sys.exit(1)

    # Step 2
    parse_ok = check_parsing()
    results.append(("解析テスト", parse_ok))

    # Step 3
    sheets_ok, sheet = check_sheets(config)
    results.append(("Sheets書き込み", sheets_ok))

    # Step 4
    cleanup_ok = cleanup(sheet)
    results.append(("後片付け", cleanup_ok))

    # サマリー
    print(f"\n{BOLD}{'─' * 50}")
    print("  テスト結果")
    print(f"{'─' * 50}{RESET}")
    all_passed = True
    for name, result in results:
        status = f"{GREEN}合格{RESET}" if result else f"{RED}失敗{RESET}"
        print(f"  {name:<20} {status}")
        if not result:
            all_passed = False

    print(f"{BOLD}{'═' * 50}{RESET}\n")

    if all_passed:
        print(f"{GREEN}{BOLD}✓ 全テスト合格！本番利用の準備ができています。{RESET}\n")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}✗ 一部のテストに失敗しました。上記のエラーを確認してください。{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
