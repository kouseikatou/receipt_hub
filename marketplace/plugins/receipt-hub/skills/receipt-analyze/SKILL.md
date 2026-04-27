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

```bash
python3 scripts/history.py lookup "ベンダー名"
```

返り値の `confidence=high`（count >= 3）なら勘定科目をそのまま採用し Step 2〜3 をスキップ。
`found=false` または `confidence=medium` なら Step 2 へ進む。

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

## Step 4: 確信度の記録

確信度にかかわらず全件そのまま処理を続ける。途中でユーザーに確認しない。
`confidence` フィールドをデータに含めて CSV に出力し、ユーザーが後から判断できるようにする。

| confidence | 意味 | CSV での扱い |
|------------|------|------------|
| high | 全項目が明確 | そのまま出力 |
| medium | 金額か日付が不明瞭 | そのまま出力（確信度列に記録） |
| low | 主要項目が複数不明 | そのまま出力（確信度列に「low」と記録）|

## Step 5: 履歴への書き戻し

ユーザーが確認・承認したアイテム（high/medium どちらも）を記録する：

```bash
python3 scripts/history.py add "ベンダー名" "勘定科目" "YYYY-MM-DD"
```

全件処理後に履歴の状態を確認：

```bash
python3 scripts/history.py list
python3 scripts/history.py stats
```

## ファイルの保存

- **ローカルファイル**: 元のパスをそのまま `file_path` に記録する
- **Gmail 添付 / Chatwork ファイル**: `~/Documents/領収書/処理済/` にダウンロード保存し、そのパスを `file_path` に記録する
- **会話に貼り付けられた PDF**: 一時パスをそのまま `file_path` に記録する

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
  "file_path": "/Users/xxx/Documents/領収書/処理済/invoice_20260315.pdf",
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
