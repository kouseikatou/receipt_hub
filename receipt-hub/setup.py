#!/usr/bin/env python3
"""
Receipt Hub セットアップスクリプト

使い方:
    python3 setup.py

以下を自動で行います：
1. gspread の認証確認
2. スプレッドシートURLを入力 → config.json に保存
3. ローカルフォルダを作成
"""

import json
import sys
from pathlib import Path

GREEN = "\033[92m"
RED   = "\033[91m"
BOLD  = "\033[1m"
RESET = "\033[0m"

def ok(msg):  print(f"  {GREEN}✓{RESET} {msg}")
def err(msg): print(f"  {RED}✗{RESET} {msg}")
def section(title): print(f"\n{BOLD}{title}{RESET}")


def main():
    print(f"\n{BOLD}{'═' * 50}")
    print("  Receipt Hub セットアップ")
    print(f"{'═' * 50}{RESET}")

    # ── Step 1: gspread 認証確認 ─────────────────
    section("Step 1: gspread 認証確認")
    try:
        import gspread
    except ImportError:
        err("gspread が見つかりません。`pip3 install gspread` を実行してください。")
        sys.exit(1)

    try:
        gc = gspread.oauth()
        ok("OAuth 認証済み")
    except Exception as e:
        err(f"認証に失敗しました: {e}")
        err("README の Step 3 を参照してください。")
        sys.exit(1)

    # ── Step 2: スプレッドシートURLの入力 ────────
    section("Step 2: スプレッドシートURLの設定")

    config_path = Path.home() / ".receipt-hub" / "config.json"

    # 既存設定の確認
    existing_url = ""
    if config_path.exists():
        try:
            with open(config_path) as f:
                existing_url = json.load(f).get("spreadsheet_url", "")
        except Exception:
            pass

    if existing_url:
        ok(f"設定済み: {existing_url}")
        try:
            answer = input("  URLを変更しますか？ [y/N]: ").strip().lower()
        except EOFError:
            answer = "n"
        if answer != "y":
            print()
        else:
            existing_url = ""

    if not existing_url:
        print("  Googleスプレッドシートを手動で作成し、URLを貼り付けてください。")
        print("  （シートの作成方法は README の Step 4 を参照）\n")
        try:
            url = input("  スプレッドシートURL: ").strip()
        except EOFError:
            err("URLが入力されませんでした。")
            sys.exit(1)

        if "docs.google.com/spreadsheets" not in url:
            err("正しいGoogleスプレッドシートのURLを入力してください。")
            sys.exit(1)

        # 接続テスト
        try:
            sheet = gc.open_by_url(url).sheet1
            ok(f"接続確認済み: {sheet.title}")
        except Exception as e:
            err(f"スプレッドシートに接続できません: {e}")
            err("URLが正しいか、シートが存在するか確認してください。")
            sys.exit(1)

        existing_url = url

    # ── Step 3: config.json を保存 ───────────────
    section("Step 3: config.json を保存")

    local_folder = str(Path.home() / "Documents" / "領収書" / "未処理")
    config = {
        "spreadsheet_url": existing_url,
        "local_folder": local_folder,
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    ok(f"保存しました: {config_path}")

    # ── Step 4: ローカルフォルダを作成 ───────────
    section("Step 4: ローカルフォルダを作成")
    for folder in ["未処理", "処理済", "要確認"]:
        path = Path.home() / "Documents" / "領収書" / folder
        path.mkdir(parents=True, exist_ok=True)
        ok(f"~/Documents/領収書/{folder}/")

    # ── 完了 ────────────────────────────────────
    print(f"\n{BOLD}{'═' * 50}{RESET}")
    print(f"{GREEN}{BOLD}✓ セットアップ完了！{RESET}")
    print("\n  動作確認テストを実行してください：")
    print("  python3 tests/integration_test.py\n")


if __name__ == "__main__":
    main()
