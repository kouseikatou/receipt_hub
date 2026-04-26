---
name: receipt-analyze
description: |
  領収書・請求書1件を解析して構造化データを抽出するスキル。「この領収書を解析して」「添付ファイルから金額を読み取って」「勘定科目を判定して」と言われたときに使う。PDF・画像・メール本文すべてに対応。
tools:
  - Read
  - Bash
  - mcp__gemini__analyze_media
---

# 領収書・請求書の解析

## 解析の原則

**全ファイルを Gemini Vision で解析する。** テキスト抽出や regex は使わない。
PDF・画像・HEIC いずれも `mcp__gemini__analyze_media` に直接投げる。
メール本文のみの場合（添付なし）は本文テキストを Gemini に渡して解析させる。

## Step 1: 履歴参照（高速パス）

解析前に `~/.receipt-hub/vendor_history.json` を読み込む。
ベンダー名が履歴に存在し `count >= 3` の場合、勘定科目はそのまま採用（確信度: high）。
履歴にないベンダーは Step 2 へ進む。

## Step 2: Gemini Vision で解析

`mcp__gemini__analyze_media` に以下のプロンプトで投げる：

```
この書類から以下を抽出してJSON形式で返してください。

{
  "doc_type": "領収書 または 請求書（判断できない場合は null）",
  "date": "YYYY-MM-DD（不明な場合は null）",
  "vendor": "店名・発行元・先方",
  "amount": 税込合計金額（整数、不明な場合は null）,
  "amount_excl_tax": 税抜金額（整数、不明な場合は null）,
  "tax_rate": 消費税率（8 または 10、不明な場合は null）,
  "memo": "品目・用途を簡潔に（例: 打ち合わせ代、クラウドサービス月額）",
  "confidence": "high / medium / low",
  "confidence_reason": "確信度が medium/low の場合、その理由"
}

判断基準：
- confidence=high: 全項目が明確に読み取れる
- confidence=medium: 金額か日付のどちらかが不明瞭
- confidence=low: 領収書・請求書かどうか自体が不確か、または主要項目が複数不明
```

## Step 3: 勘定科目の判定

1. `~/.receipt-hub/vendor_history.json` に vendor が存在 → 履歴の category を使用
2. 存在しない場合 → `receipt-accounts` スキルのルールで判定
3. 候補が2つ以上に絞れない場合 → confidence を medium に下げてユーザーに提示

## Step 4: 確信度による振り分け

| confidence | 処理 |
|------------|------|
| high | 自動採用。ユーザーへの確認不要 |
| medium | 解析結果を提示し「この内容で正しいですか？」と1件ずつ確認 |
| low | 「要確認リスト」に追加。解析できた項目と判断できなかった理由を明示 |

## Step 5: 履歴への書き戻し

ユーザーが確認・承認したアイテム（high/medium どちらも）を履歴に記録する：

```bash
python3 - <<'EOF'
import json
from pathlib import Path

history_path = Path.home() / ".receipt-hub" / "vendor_history.json"
history_path.parent.mkdir(exist_ok=True)
history = json.loads(history_path.read_text()) if history_path.exists() else {}

vendor = "スターバックス渋谷店"   # 実際のベンダー名に置き換え
category = "会議費"               # 確定した勘定科目に置き換え

entry = history.get(vendor, {"category": category, "count": 0, "last_confirmed": ""})
entry["count"] += 1
entry["category"] = category
entry["last_confirmed"] = "2026-04-27"   # 処理日に置き換え
history[vendor] = entry

history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2))
print(f"履歴更新: {vendor} → {category} (累計 {entry['count']} 件)")
EOF
```

## 出力形式

```json
{
  "date": "2026-03-15",
  "vendor": "スターバックス渋谷店",
  "amount": 1650,
  "amount_excl_tax": 1500,
  "tax_rate": 10,
  "doc_type": "領収書",
  "category": "会議費",
  "memo": "打ち合わせ代",
  "confidence": "high",
  "source": "Gmail",
  "raw_source_id": "thread_xxx"
}
```

## 要確認リストの形式

```
【要確認】
- ファイル: invoice_unknown.pdf（Gmail, thread_yyy）
- 読み取れた内容: 金額 ¥12,000、日付不明、発行元不明
- 判断できなかった理由: 日付・発行元の記載が見当たらない
- → ユーザーに日付と発行元を直接入力してもらう
```
