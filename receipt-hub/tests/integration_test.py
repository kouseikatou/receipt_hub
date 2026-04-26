#!/usr/bin/env python3
"""
Receipt Hub 総合テスト

使い方:
    python3 tests/integration_test.py

全工程（環境チェック → 解析 → CSV出力 → 後片付け）を通しで確認します。
テスト用に生成したCSVファイルは自動的に削除されます。
"""

import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}"); return False
def warn(msg): print(f"  {YELLOW}⚠{RESET} {msg}")
def section(n, title): print(f"\n{BOLD}[{n}] {title}{RESET}")


# ─────────────────────────────────────────────
# Step 1: 環境チェック
# ─────────────────────────────────────────────

def check_environment():
    section("1/4", "環境チェック")
    passed = True

    # exports/ ディレクトリ確認
    exports_dir = Path("exports")
    if not exports_dir.exists():
        exports_dir.mkdir(exist_ok=True)
        ok("exports/ ディレクトリを作成しました")
    else:
        ok("exports/ ディレクトリ確認済み")

    # ローカルフォルダ確認
    local_dir = Path.home() / "Documents" / "領収書" / "未処理"
    if local_dir.exists():
        ok(f"ローカルフォルダ確認済み: ~/Documents/領収書/未処理/")
    else:
        warn("ローカルフォルダが見つかりません。`python3 setup.py` を実行してください。")

    # Python バージョン確認
    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 8:
        ok(f"Python {major}.{minor} ✓")
    else:
        fail(f"Python 3.8以上が必要です (現在: {major}.{minor})")
        passed = False

    return passed


# ─────────────────────────────────────────────
# Step 2: サンプル領収書の解析テスト
# ─────────────────────────────────────────────

CATEGORY_RULES = {
    "会議費":     ["スターバックス", "カフェ", "打ち合わせ", "コーヒー", "ドトール", "タリーズ"],
    "旅費交通費": ["タクシー", "電車", "バス", "新幹線", "飛行機", "suica", "pasmo", "go タクシー"],
    "通信費":     ["aws", "amazon web services", "google cloud", "さくらインターネット",
                   "cloudflare", "netlify", "vercel", "heroku", "github"],
    "新聞図書費": ["amazon.co.jp", "kindle", "書籍", "udemy", "book"],
    "消耗品費":   ["ヨドバシ", "ビックカメラ", "文具", "事務用品"],
    "広告宣伝費": ["google ads", "facebook広告", "名刺"],
    "外注費":     ["業務委託", "外注", "制作費", "フリーランス"],
    "地代家賃":   ["家賃", "コワーキング", "レンタルオフィス", "ウィーワーク"],
    "研修費":     ["セミナー", "勉強会", "connpass", "研修"],
}

AMOUNT_PATTERN = re.compile(r"[¥\\]\s*([\d,]+)|(\d[\d,]*)\s*円")
DATE_PATTERNS  = [
    (re.compile(r"(\d{4})[/\-年](\d{1,2})[/\-月](\d{1,2})"), "%Y-%m-%d"),
    (re.compile(r"R(\d+)[./年](\d{1,2})[./月](\d{1,2})"),     "reiwa"),
]

def parse_amount(text):
    matches = AMOUNT_PATTERN.findall(text)
    amounts = []
    for yen_prefix, yen_suffix in matches:
        raw = (yen_prefix or yen_suffix).replace(",", "")
        if raw.isdigit():
            amounts.append(int(raw))
    amounts = [a for a in amounts if not (1900 <= a <= 2100)]
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
# Step 3: CSV出力テスト
# ─────────────────────────────────────────────

TEST_CSV_NAME = None

def check_csv_export():
    section("3/4", "CSV出力テスト")
    global TEST_CSV_NAME

    test_items = [
        {
            "date": "2024-01-15", "vendor": "スターバックス渋谷店",
            "amount": 1650, "amount_excl_tax": 1500, "tax_rate": 10,
            "category": "会議費", "doc_type": "領収書",
            "memo": "打ち合わせ代", "source": "Gmail",
        },
        {
            "date": "2024-01-20", "vendor": "GO タクシー, 東京",
            "amount": 2340, "amount_excl_tax": 2127, "tax_rate": 10,
            "category": "旅費交通費", "doc_type": "領収書",
            "memo": "客先訪問", "source": "ローカル",
        },
    ]

    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = exports_dir / f"{date_str}_テスト.csv"
    TEST_CSV_NAME = filename

    headers = ["日付", "店名・先方", "金額(税込)", "税抜金額", "消費税率",
               "勘定科目", "種別", "メモ", "ソース"]

    try:
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)
            for item in test_items:
                writer.writerow([
                    item["date"], item["vendor"],
                    item["amount"], item["amount_excl_tax"],
                    f"{item['tax_rate']}%",
                    item["category"], item["doc_type"],
                    item["memo"], item["source"],
                ])
        ok(f"CSVファイルを生成しました: {filename}")
    except Exception as e:
        fail(f"CSV生成に失敗: {e}")
        return False

    # 検証: 読み取って内容確認
    try:
        with open(filename, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert rows[0] == headers, "ヘッダーが正しくありません"
        assert len(rows) == 3, f"行数が不正: {len(rows)}"
        assert rows[1][1] == "スターバックス渋谷店", "店名が正しくありません"
        # カンマ含む店名が正しくエスケープされているか
        assert rows[2][1] == "GO タクシー, 東京", "カンマ含む値のエスケープが正しくありません"
        ok(f"ヘッダー・データ行・カンマエスケープの検証 OK ({len(rows)-1}件)")
    except Exception as e:
        fail(f"CSV検証に失敗: {e}")
        return False

    # BOM確認
    with open(filename, "rb") as f:
        bom = f.read(3)
    if bom == b"\xef\xbb\xbf":
        ok("UTF-8 BOM付き確認済み（Excelで文字化けなし）")
    else:
        fail("BOMが付いていません")
        return False

    return True


# ─────────────────────────────────────────────
# Step 4: 後片付け
# ─────────────────────────────────────────────

def cleanup():
    section("4/4", "後片付け（テストCSV削除）")
    if TEST_CSV_NAME and Path(TEST_CSV_NAME).exists():
        Path(TEST_CSV_NAME).unlink()
        ok(f"テストCSVを削除しました: {TEST_CSV_NAME}")
    else:
        warn("削除対象のファイルが見つかりませんでした。")
    return True


# ─────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────

def main():
    print(f"\n{BOLD}{'═' * 50}")
    print("  Receipt Hub 総合テスト")
    print(f"{'═' * 50}{RESET}")

    results = []

    env_ok = check_environment()
    results.append(("環境チェック", env_ok))
    if not env_ok:
        print(f"\n{RED}環境が整っていません。上記のエラーを解消してから再実行してください。{RESET}")
        sys.exit(1)

    parse_ok = check_parsing()
    results.append(("解析テスト", parse_ok))

    csv_ok = check_csv_export()
    results.append(("CSV出力", csv_ok))

    cleanup_ok = cleanup()
    results.append(("後片付け", cleanup_ok))

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
