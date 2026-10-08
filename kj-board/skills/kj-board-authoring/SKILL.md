---
name: kj-board-authoring
description: >
  KJ Board (Streamlit) 用の JSON ボードを設計・生成・改善するためのスキル。
  付箋の title / text / popup の3層情報設計を重視し、ポップアップの核心から
  タイトルと興味を引く短い見出しを逆算する。意味的な近さを付箋の位置と距離で表現し、
  Markdown・Code・Mermaid・Image の付箋を現行スキーマで作成・検証する。
---

# KJ Board Authoring

## 目的と最重要原則

**ボードを眺めると構造が分かり、気になる付箋を開くと核心が分かる。**

このスキルは `kj_board_app.py` に読み込ませる **UTF-8 JSON ボード**を制作する。
添付元の `kj-session-board-json-authoring` の情報設計を継承し、次の原則を守る。

1. **説明の核心はポップアップに置く**。ボード上だけで説明を完結させない。
2. **`title` と `text` は興味を喚起するフック**。ポップアップ本文の焼き直しにしない。
3. **座標と距離は意味を表す**。類縁度の高い付箋ほど近く、段階の違いは空白で示す。
4. **先にポップアップを書き、最後にタイトルを付ける**（Popup-first）。
5. **現行版は付箋のみ**。旧版の `groups` / `edges` / `type: "text"` を生成しない。

## 使用する場面

- 技術教材・概念解説・操作ガイド・比較表・アーキテクチャ説明を JSON ボード化する
- 既存ボードの付箋文面・情報密度・並び順・余白を改善する
- Markdown / Code / Mermaid / Image の複合ボードを制作する
- ポップアップの説明が薄い、付箋が多すぎる、配置に学習順序がない、といった問題を修正する

## 必ず参照するファイル

- [`references/board-format.md`](references/board-format.md) — **現行 JSON スキーマの正本**。旧形式からの差分を確認する。
- [`references/authoring-guidelines.md`](references/authoring-guidelines.md) — 付箋文面、意味的類縁度、配置、色、品質検査の詳細指針。
- [`references/reference-board.json`](references/reference-board.json) — 添付元スキルの「Mermaid Sequence Diagram」参照ボード（12付箋）を現行形式へ移植したもの。
- [`scripts/validate_board.py`](scripts/validate_board.py) — JSONの構造・色・座標・タイプごとのソースを検証。

参照題材の構文確認先: [Mermaid Sequence Diagram 公式仕様](https://mermaid.ai/open-source/syntax/sequenceDiagram.html)。

## ボードと付箋の情報設計

ルートは原則 `{"title": "…", "notes": [...]}`。個々の note は次の3階層を持つ。

| 階層 | JSON フィールド | 機能 | 書き方 |
| --- | --- | --- | --- |
| 1 | `title` | 瞬時の識別 | 原則 6〜18 日本語文字程度。名詞句、具体的な問い、差分を短く |
| 2 | `text` | 興味を引くフック | 原則 1〜2 行。具体語を含む問い・意外性・効果。説明を言い切らない |
| 3 | `markdownSource` / `inline` / `imageUrl` | 説明の核心 | 原理、根拠、コード、図、画像を詳しく提示する |

**良い組合せの例**

```text
title:   「ミドルウェアの順序」
text:    「404は最後。途中に置くと何が起きる？」
popup:   middleware chain、next()、404の挙動を図と例で解説
```

`text` は付箋タイプではなく **ボード面に表示される内容・メモのフィールド**。
単なる一言メモも `type: "markdown"` を使うこと。`type: "text"` は禁止。

### 付箋タイプの選択

| 種類 | 核心を格納するフィールド | 用途 |
| --- | --- | --- |
| `markdown`（デフォルト） | `markdownSource`、互換用 `inline` | 概念・注記・比較・用語・手順。生Markdownを保持し、GFM表も可 |
| `code` | `inline`、`language` | 実コード・コマンド。最小実例と「なぜ」のコメントを優先 |
| `mermaid` | `inline` | 処理順・関係・シーケンス。**Mermaidソースそのもの**を保持 |
| `image` | `imageUrl` | 実画面・実画像。アクセス可能な URL に限る。説明は `title` / `text` に |

`markdownSource` と Markdown の `inline` は同じ内容にする。HTML / SVG / シンタックスハイライトに事前変換しない。
**Image は特定の信頼できる画像URLがある場合のみ**使用し、架空のURLを生成しない。

## Popup-first オーサリング手順

1. **目的と対象読者を定義**する。学習後に何を理解・判断・実践できるか決める。
2. テーマを **2〜5 の意味的クラスタ**に分解する（例: 導入 → 仕組み → 実装 → 例外 → 運用）。これは概念上の区分であり、旧 `groups` オブジェクトではない。
3. 各付箋に Concept / Question / Example / Code / Flow / Comparison / Pitfall / Practice などの役割を割り当て、**一付箋一主題**にする。
4. **最初に Layer 3 を完成**する。`markdownSource`、`inline` または `imageUrl` に、詳しい核心を格納する。
5. 核心を開きたくなる **Layer 2 `text`** を逆算する。結論やソース全文をボード上に置かない。
6. 最後に簡潔で識別しやすい **Layer 1 `title`** を付ける。抽象的な「説明」「ポイント」は避ける。
7. 意味的類縁度（3=直結、2=同じクラスタ、1=関連、0=独立）に従い、座標を決める。近い概念は隣接させ、違うクラスタは余白で区切る。
8. 学習用・PDF用に **上→下、同じ段は左→右** の順序を設計する。`z` は前後の重なり順であり、読順ではない。
9. パレットから色を選び、意味を補助する。色だけに重要な区別を依存させない。
10. JSON を生成し、バリデータと可能ならアプリ画面で品質を確認する。

## 配置の基本

- 通常の付箋幅: 約 **220 px**。高さは内容・メモに応じて増えるため、配置時は余裕を持つ。
- 開始位置の目安: `x >= 70`、`y >= 160`（セッションタイトルを避ける）。
- 隣接付箋の水平方向の空白: **30〜50 px 程度**。縦方向は本文の長さを見て **45 px 以上**を目安にする。
- 異なるクラスタの境界は、例えば **90〜160 px**のまとまった空白で示す。
- 複数行のタイトルや長い `text` による衝突を避ける。
- 視覚上の区分を表すための **JSON `groups` / `edges` は使用しない**。
- PDFの目次が座標で並ぶため、曖昧な段差を付けず、同じ行の `y` をそろえる。

添付元の参照例の4テーマ「基本の骨格」「メッセージ」「制御構造」「読みやすくする」は、現行版では **4つの学習段階（縦方向）× 説明・ソース・図（横方向）** に再配置している。

## 品質ゲート

- [ ] `title` だけでテーマが識別でき、`text` は開きたくなる具体的なフックになっている
- [ ] ポップアップ単体で核心が理解でき、`title` / `text` の繰返しになっていない
- [ ] 説明・実装・図解が異なる価値を提供し、同じ内容の無意味な複製でない
- [ ] ユーザーの資料・一次情報を優先し、バージョン情報や出典を必要に応じて明示する
- [ ] JSON は UTF-8、ID一意、`type` は4種類だけ、`groups` / `edges` 不在
- [ ] Markdown は `markdownSource` と `inline` が同一。Code は妥当な `language`、Mermaid は妥当なソース
- [ ] 付箋に重なりや極端な空白がなく、PDFの目次の順序も自然
- [ ] Mermaid が極端に巨大にならず、画像URLが実際に参照可能（可能な範囲で確認）

```bash
python skills/kj-board-authoring/scripts/validate_board.py \
  skills/kj-board-authoring/references/reference-board.json --strict
python skills/kj-board-authoring/scripts/validate_board.py \
  path/to/new-board.json --strict
```

**この検証は構造チェック**であり、Mermaid の構文実行や外部画像URLの疎通までは保証しない。可能なら KJ Board の編集・表示モード、PDF出力で確認する。

## 成果物

「JSONファイルを作って」と頼まれたら、品質検査を通した **JSON ファイル**を納品する。「JSON を表示」なら JSON そのものを出す。改善依頼なら、問題と改善方針を簡潔に説明してから修正版を作る。JSONファイルの内容へ余計な Markdown や説明文を混入させない。

**結論：全体像はボード面で、核心はポップアップで。**
