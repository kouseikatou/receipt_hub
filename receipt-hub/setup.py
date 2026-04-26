#!/usr/bin/env python3
"""
Receipt Hub セットアップスクリプト

使い方:
    python3 setup.py

以下を自動で行います：
1. exports/ ディレクトリの作成
2. ローカルフォルダの作成
3. config.json の保存
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

    # ── Step 1: exports/ ディレクトリ ────────────
    section("Step 1: exports/ ディレクトリを作成")
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    ok(f"{exports_dir.resolve()}/")

    # ── Step 2: ローカルフォルダ ─────────────────
    section("Step 2: ローカルフォルダを作成")
    for folder in ["未処理", "処理済", "要確認"]:
        path = Path.home() / "Documents" / "領収書" / folder
        path.mkdir(parents=True, exist_ok=True)
        ok(f"~/Documents/領収書/{folder}/")

    # ── Step 3: config.json ──────────────────────
    section("Step 3: config.json を保存")
    config_path = Path.home() / ".receipt-hub" / "config.json"

    local_folder = str(Path.home() / "Documents" / "領収書" / "未処理")
    config = {
        "local_folder": local_folder,
        "exports_dir": str(Path("exports").resolve()),
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    ok(f"保存しました: {config_path}")

    # ── 完了 ────────────────────────────────────
    print(f"\n{BOLD}{'═' * 50}{RESET}")
    print(f"{GREEN}{BOLD}✓ セットアップ完了！{RESET}")
    print("\n  動作確認テストを実行してください：")
    print("  python3 tests/integration_test.py\n")


if __name__ == "__main__":
    main()
