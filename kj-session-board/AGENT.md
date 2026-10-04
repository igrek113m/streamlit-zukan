# AGENT.md — KJ Session Board 開発エージェント指示

## 1. 目的

このリポジトリでは、Streamlit 上で動作する **KJ Session Board** を開発・保守する。

AI エージェントは、ユーザーから追加・変更要求を受けたとき、既存の操作性・JSON互換性・プレゼン表示を壊さず、必要な変更を `app.py` へ実装すること。

実装前に必ず次を読む。

1. `AGENT.md` — 作業上の契約と受け入れ条件
2. `DESIGN.md` — 現行アーキテクチャ、データモデル、UI/幾何アルゴリズム
3. `SKILL.md` — 実際の変更作業手順と検証方法
4. `reference_board.json` — canonical JSON の最小参照データ

`reference_board.json` は **2グループ・4付箋・1接続線**で構成される。JSON入出力や描画変更を行った場合は、必ずこのファイルを読み込んでスモークテストする。

---

## 2. 成果物

基本構成は次とする。

```text
.
├── app.py
├── requirements.txt
├── AGENT.md
├── DESIGN.md
├── SKILL.md
└── reference_board.json
```

標準依存関係:

```text
streamlit>=1.64,<2
```

KJボード本体は **Streamlit Custom Components v2** を使用し、原則として `app.py` 内へ HTML / CSS / JavaScript を埋め込む単一ファイル構成を維持する。

別フロントエンドプロジェクト、Node build、React/Vite 等へ分離するのは、ユーザーが明示的に要求した場合だけとする。

---

## 3. 現行機能 — 削除してはならないもの

ユーザーが明示的に削除を要求しない限り、以下を保持する。

### ボード

- ボード左上のセッションタイトル
- JSON エクスポート
- JSON インポート
- Undo / Redo
- 全消去
- 自動的なキャンバス拡張

### モード

- 編集モード
- 表示モード
- 表示モードでの全画面表示
- 全画面表示中の rich 付箋ダブルクリック・ポップアップ

### 付箋

- ドラッグ移動
- ×ボタンで削除
- 6色プリセット
- `text`
- `code`
- `markdown`
- `mermaid`
- `image`

### rich 付箋

- `code`: 言語選択、編集モードでコード編集、表示モードで syntax highlight
- `markdown`: 編集モードでソース編集、表示モードでレンダリング結果のみ
- `mermaid`: 編集モードでソース編集、表示モードで図のみ
- `image`: 編集モードで URL 設定、表示モードで画像表示

### グループ

- 矩形選択によるグループ化
- グループ名
- グループ内グループ
- 子グループを含めて親矩形を自動拡張
- タイトルを点線矩形の左上内側へ配置
- グループ削除時に内容を可能な限り親へ昇格

### 接続線

- 2グループ間の接続
- `none` / `right` / `left`
- 関係ラベル
- グループ中心を結ぶ方向を基準とし、線端は矩形境界へ接続
- 編集モードで接続線をダブルクリックして編集・削除

---

## 4. 非機能要件

### 4.1 状態の唯一の正

ボード状態の canonical model は次だけ。

```text
board
├── title
├── notes[]
├── groups[]
└── edges[]
```

DOM を真実の状態にしてはならない。操作後は必ず `board` を変更し、`render()` と `sync()` を行う。

### 4.2 Streamlit との同期

JavaScript → Streamlit の同期は Custom Components v2 の:

```javascript
setStateValue("board", payload)
```

を使う。

Python 側では component state を読み、`st.session_state.board_seed` へ保持する。

### 4.3 JSON互換性

canonical schema は `DESIGN.md` を参照する。

変更時のルール:

- 既存フィールドを不用意に削除しない
- 新フィールドには default を与える
- `normalizeBoard()` で欠損値を補完する
- 不正な edge / childGroupIds は可能な範囲で除去する
- `reference_board.json` は変更後も読み込めること
- Export → Import で情報が欠落しないこと

### 4.4 編集モード / 表示モードの分離

表示モードでは、ユーザーがボードを誤編集できないこと。

表示モードで許可する操作:

- ボード閲覧
- スクロール
- 全画面
- rich 付箋のダブルクリック表示
- modal を閉じる

表示モードで禁止する操作:

- 付箋作成・削除・移動
- text 本文編集
- グループ作成・削除・名称変更
- 接続線作成・編集
- Undo / Redo

### 4.5 外部ライブラリ

現行ブラウザ側依存:

- Marked 16
- Mermaid 11
- highlight.js 11.11.1

CDN は `https://cdn.jsdelivr.net/npm/.../+esm` を使用する。

Mermaid:

```javascript
mermaid.initialize({
  startOnLoad: false,
  securityLevel: "strict",
  theme: "default",
});
```

閉域対応を要求された場合のみローカル配布へ変更する。

---

## 5. 変更時の最重要ルール

### 付箋削除

×ボタンはドラッグハンドル内部にある。

そのため削除ボタンには最低限:

```javascript
pointerdown -> stopPropagation()
click       -> preventDefault()
               stopPropagation()
               stopImmediatePropagation()
```

を維持し、ハンドル側でも:

```javascript
if (evt.target.closest(".note-delete")) return;
```

でドラッグ開始を抑止する。

この対策を削除すると「×を押しても削除されない」回帰が起きやすい。

### グループ矩形

固定座標を保存しない。

グループ矩形は毎回:

- direct note bounds
- child group bounds

から再帰計算する。

### 接続線

中心から中心へ直接描画してはならない。

中心間ベクトルを基準に `boundaryPoint()` で source / target の矩形境界との交点を算出する。

### rich 付箋

付箋表面には要約 `text` を表示する。

詳細コンテンツは:

- `code`, `markdown`, `mermaid` → `inline`
- `image` → `imageUrl`

に保存する。

---

## 6. 作業フロー

1. 現在の `app.py`, `DESIGN.md`, `SKILL.md`, `reference_board.json` を読む。
2. ユーザー要求を「データモデル / UI / interaction / rendering / compatibility」に分解する。
3. 既存 JSON schema への影響を判定する。
4. `app.py` を修正する。
5. Python syntax check。
6. 埋め込み JavaScript syntax check。
7. `reference_board.json` を読み込む。
8. 受け入れテストを実施する。
9. 変更内容と既知の制約を簡潔に報告する。

---

## 7. 必須受け入れテスト

最低限、以下を確認する。

### 起動

```bash
python -m py_compile app.py
streamlit run app.py
```

### Reference JSON

`reference_board.json` を JSON読込する。

期待値:

```text
title  = KJ Session Board Reference
notes  = 4
groups = 2
edges  = 1
```

### 編集

- 新規 text 付箋を作れる
- 付箋を移動できる
- ×で付箋を削除できる
- 付箋を囲みグループ化できる
- 既存グループ内でさらにグループ化できる
- 親グループ矩形が子グループ全体を包含する
- グループ接続を作れる
- `none/right/left` が反映される
- 接続線をダブルクリックして編集できる

### rich 付箋

- code を編集できる
- markdown を編集できる
- mermaid を編集できる
- image URL を編集できる

### 表示

- 編集UIが隠れる
- text が編集できない
- rich 付箋がダブルクリックで開く
- code は syntax highlighted
- markdown はソースではなくレンダリング結果
- mermaid はソースではなく図
- image は画像
- 全画面中も上記 modal が開く

### JSON

- セッションタイトルを保存できる
- Export → Import で同じボードへ戻る
- `reference_board.json` の読み込み後も Undo できる

---

## 8. 完了条件

変更を「実装済み」と呼べるのは、少なくとも次を満たした場合のみ。

- Python syntax error がない
- JavaScript syntax error がない
- canonical board schema を壊していない
- `reference_board.json` がロード可能
- 編集モードと表示モードが混線していない
- 付箋削除が機能する
- nested group bounds が破綻しない
- edge が矩形境界へ接続される
- JSON round trip で必要情報が失われない

実ブラウザ検証ができなかった場合は、完了報告でその事実を明記する。
