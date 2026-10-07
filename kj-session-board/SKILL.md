---
name: kj-session-board-json-authoring
description: >
  KJ Session Board に読み込ませる JSON データを設計・生成・改善するためのスキル。
  付箋の title / text / popup content の3段階情報設計を行い、ポップアップを説明の核心、
  title と text をポップアップへ誘導するフックとして設計する。さらに、ボード面積、
  グループ境界、付箋間距離、意味的な類縁性を考慮して、読みやすく整然とした配置を生成する。
---

# KJ Session Board JSON Authoring Skill

## 1. Purpose

このスキルは、KJ Session Board で閲覧・説明・プレゼンテーションに使える高品質な JSON ボードを生成する。

最重要原則は次の3点である。

1. **説明の核心はポップアップに置く**
2. **タイトルとボード上の見出しは、ポップアップを開きたくなるフックにする**
3. **情報の類縁性を、グループだけでなく座標と距離でも表現する**

ボード上だけですべてを説明しようとしてはならない。
ボードは「全体像を瞬時に把握する面」、ポップアップは「理解を深める面」として役割を分離する。

---

## 2. When to use

次の依頼でこのスキルを使う。

- KJ Session Board 用 JSON を新規作成する
- 既存 JSON の内容、付箋構成、グルーピング、配置を改善する
- 技術教材、概念解説、比較表現、アーキテクチャ説明、チュートリアルを KJ Session Board 化する
- markdown / code / mermaid / image 付箋を組み合わせた説明ボードを作る
- 「付箋が多すぎる」「散らかっている」「説明が付箋内に詰まりすぎている」ボードを再設計する

---

## 3. Current board model

基本 JSON は次の形とする。

```json
{
  "title": "Board title",
  "notes": [],
  "groups": [],
  "edges": []
}
```

### 3.1 Note schema

```json
{
  "id": "note_unique_id",
  "title": "付箋タイトル",
  "text": "ボード上に表示する短い見出し",
  "type": "markdown",
  "inline": "ポップアップでレンダリングするソース",
  "language": "text",
  "imageUrl": "",
  "color": "#DCEEFF",
  "x": 120,
  "y": 180,
  "w": 210,
  "h": 150
}
```

使用可能な `type`:

- `markdown`
- `code`
- `mermaid`
- `image`

**デフォルト `type` は `markdown` とする。**

短いメモ、一言コメント、補助説明であっても `type: "text"` は使用しない。
メモ用途も `markdown` とし、`inline` に本文または補足情報を持たせる。

`code` / `markdown` / `mermaid` のポップアップ本体は `inline` に格納する。
`image` のポップアップ本体は `imageUrl` である。

`text` は **note の type ではなく、ボード上に表示する短い見出しフィールド** としてのみ使用する。

### 3.2 Group schema

```json
{
  "id": "group_unique_id",
  "name": "グループ名",
  "noteIds": ["note_1", "note_2"],
  "childGroupIds": []
}
```

グループの表示矩形は、所属付箋と子グループの座標から自動計算される。
したがって、**グループの見栄えは note の x/y 設計で決まる。**

### 3.3 Edge schema

```json
{
  "id": "edge_unique_id",
  "source": "group_a",
  "target": "group_b",
  "label": "理解してから進む",
  "direction": "right"
}
```

`direction` は次のいずれか。

- `none`
- `right`
- `left`

edge はグループ間の意味関係が明確な場合だけ使用する。
単なる近接関係を edge で重複表現しない。

---

## 4. Three-layer information architecture

すべての rich note は、次の3階層で設計する。

| Layer | JSON field | Role | Principle |
|---|---|---|---|
| 1 | `title` | 識別 | 一瞬でテーマを認識 |
| 2 | `text` | 誘導 | 疑問・効果・差分を示しクリックを誘う |
| 3 | `inline` / `imageUrl` | 核心 | 説明、コード、図解、根拠を提示 |

### 4.1 Layer 1: title

タイトルは「何の付箋か」を一瞬で識別するラベルである。

推奨:

- 日本語ならおおむね 6〜18 文字
- 名詞句、短い問い、技術用語を中心にする
- 同じグループ内でタイトルの粒度をそろえる
- 詳しい結論を書かない

良い例:

- `ルートはどう決まる？`
- `ミドルウェアの順序`
- `失敗時の流れ`
- `最小の Express`

避ける例:

- `Express.js におけるルーティング処理の詳細について`
- `重要`
- `ポイント`
- `説明`

### 4.2 Layer 2: text

`text` はボード上で読める短い見出しであり、
**Layer 3 を開く理由を作るコピー**である。

推奨:

- 原則 1〜2 行
- 1文または2つの短いフレーズ
- 「なぜ？」「どうなる？」「何が変わる？」を感じさせる
- Layer 3 の要約を全部書かない
- 具体語を1つ以上入れる

良い例:

- `上から順に実行される。では next() は何を渡す？`
- `3行のコードから、リクエスト処理の全体像を見る`
- `404 は最後に置く。順序を図で確認する`

避ける例:

- `詳しくはポップアップを見てください`
- `Express.js の説明です`
- 長い箇条書き
- コード全文
- Markdown の長文

### 4.3 Layer 3: popup content

ポップアップを説明の中心にする。

#### markdown

概念説明の第一選択とする。

構成例:

```markdown
## ここで理解すること

結論を2〜3文で説明する。

### なぜそうなるか

原因、仕組み、判断基準を説明する。

### 実務で見るポイント

- 運用上の注意
- よくある誤解
- 次に確認する項目
```

必要に応じて以下を含める。

- 小さな表
- 箇条書き
- Before / After
- 注意点
- 具体例
- 関連付箋への接続を意識した最後の一文

#### code

ポップアップで読ませたい実コードを `inline` に置く。

- 動作単位が分かる最小コードを優先
- 説明に不要な boilerplate は削る
- コメントは「なぜ」を補うために使う
- `language` を必ず適切に設定する
- コードそのものが核心でない場合は markdown note を使う

#### mermaid

関係・流れ・状態遷移・構造を視覚化するときに使う。

- 1 diagram = 1 message
- ノード数を増やしすぎない
- ボード上の `text` では図の結論を先に言い切らない
- Mermaid ソースをそのまま `inline` に格納する

#### image

画像そのものが説明価値を持つときだけ使う。

- `imageUrl` に表示可能な URL を設定する
- `title` と `text` は画像を見る観点を示す
- 画像に依存する重要事実は、必要なら別 markdown note でも補完する

---

## 5. Popup-first authoring workflow

**必ず Layer 3 から書き始める。**

作業順序:

1. その付箋で本当に理解してほしい「核心」を1文で定義する
2. 核心を `inline` または `imageUrl` として完成させる
3. 核心を開きたくなる `text` を作る
4. 最後に `title` を短く付ける

禁止する順序:

- title を大量に先に作ってから中身を埋める
- text を長文化して popup を補足扱いにする

### Content test

各付箋について次を確認する。

- title だけで付箋のテーマを識別できるか
- text を読むと「開いて確かめたい」と思えるか
- popup 単体で核心まで理解できるか
- title / text / popup が同じ文章の言い換えになっていないか

---

## 6. Board-space design

KJ Session Board の標準付箋サイズは `210 x 150 px`。
初期キャンバスは少なくとも `1500 x 900 px` を確保する。

デフォルト値:

```text
NOTE_W = 210
NOTE_H = 150
BOARD_BASE_W = 1500
BOARD_BASE_H = 900
```

### 6.1 Safe area

セッションタイトルとの競合を避けるため、主要付箋の配置開始は概ね次を推奨する。

```text
x >= 70
y >= 150
```

画面端へ詰めすぎない。

### 6.2 Recommended spacing

同一グループ内:

```text
horizontal gap: 30〜50 px
vertical gap:   30〜55 px
```

別グループ間:

```text
90〜160 px
```

強く関連する隣接グループ:

```text
80〜120 px
```

意味的に遠いグループ:

```text
140 px 以上
```

### 6.3 Group padding awareness

グループ矩形には、付箋群の外側へおおむね次の余白が自動付与される。

```text
left:   30 px
right:  30 px
top:    52 px
bottom: 30 px
```

したがって、

- グループどうしの note 距離を狭くしすぎない
- グループ上端のラベル領域を考慮する
- note が整列していないと group box も崩れる

### 6.4 Compactness target

原則として、最初の表示で全体構造が把握できる密度を目指す。

推奨規模:

- 1グループ: 2〜5付箋
- 1ボード: 2〜5グループ
- 主要付箋: 6〜16枚程度

付箋が増えすぎる場合は、説明を popup に統合する。
「情報量が多いから付箋を増やす」のではなく、
「比較・判断・概念単位が異なるから付箋を分ける」。

---

## 7. Semantic proximity

座標は装飾ではなく情報である。

付箋間の距離を、意味的距離に対応させる。

### 7.1 Affinity score

配置前に、付箋ペアの類縁度を内部的に3段階で評価する。

```text
3 = 直接つながる。同じ理解単位。
2 = 同じグループだが別観点。
1 = 関連はあるが別グループ。
0 = 直接関係しない。
```

配置指針:

| Affinity | Placement |
|---|---|
| 3 | 隣接。30〜45 px 程度 |
| 2 | 同一クラスタ。45〜70 px 程度 |
| 1 | グループを分けつつ近接 |
| 0 | 明確に空間を空ける |

### 7.2 Reading order

学習・説明ボードでは、視線の流れを設計する。

優先順位:

1. 左 → 右
2. 上 → 下
3. 基礎 → 詳細
4. 入力 → 処理 → 出力
5. 問い → 仕組み → 実践
6. 正常系 → 例外系

円環・相互依存を表したい場合を除き、ランダムな散布配置を避ける。

### 7.3 Cluster shape

1グループ内では、次を優先する。

- 2枚: 横並び
- 3枚: 横3枚、または中心1 + 下2
- 4枚: 2 x 2
- 5〜6枚: 3 x 2

意味的順序がある場合は、きれいな対称性より読順を優先する。

---

## 8. Layout algorithm

JSON を出力する前に、内部で以下を実行する。

### Step 1: derive concepts

依頼テーマを 2〜5 個の主要クラスタへ分解する。

クラスタ例:

```text
入口
仕組み
実装
例外
運用
```

### Step 2: define note roles

各付箋に役割を割り当てる。

```text
Concept
Question
Example
Code
Flow
Comparison
Pitfall
Practice
```

同じ内容を markdown / code / mermaid で重複させない。
異なるメディアは異なる理解価値を持たせる。

### Step 3: write popup core

各 rich note の Layer 3 を完成させる。

### Step 4: derive hooks

popup から `text`、その後 `title` を逆算する。

### Step 5: build affinity matrix

近接させるべき note を決める。

### Step 6: place groups

最も重要なグループを左上または中央左へ配置する。
関連グループを読順に配置する。

### Step 7: place notes inside groups

210 x 150 を基本単位としてグリッド配置する。

推奨開始値:

```text
first group origin: x=90, y=170
note horizontal pitch: 250
note vertical pitch: 195
```

例:

```text
note A: x=100, y=180
note B: x=350, y=180
note C: x=100, y=375
note D: x=350, y=375
```

### Step 8: separate groups

次のグループは、前グループの自動 group box を想定して 100 px 前後の空白を取る。

### Step 9: add edges last

edge は「空間だけでは表せない方向性」がある場合に追加する。

例:

- prerequisite
- leads to
- input to
- failure path
- feedback

### Step 10: run layout validation

重なりと過剰な空白を検査する。

---

## 9. Layout validation rules

### 9.1 Note collision

任意の2付箋 `A`, `B` について矩形重なりを禁止する。

```text
A.right  <= B.left
OR
B.right  <= A.left
OR
A.bottom <= B.top
OR
B.bottom <= A.top
```

いずれも成立しない場合は collision である。

### 9.2 Minimum visual gap

同一グループ内でも、付箋同士を最低 24 px 以上離す。

### 9.3 Group crowding

別グループに属する付箋の外周が近すぎて、
自動 group box が接触・重複しそうな配置を避ける。

### 9.4 Empty-space balance

次を避ける。

- 左上だけに密集し右側が大きく空く
- 1枚だけ遠くへ孤立
- 同じグループ内で不規則な段差が多い
- 付箋の列が数 px 単位でずれる

座標は 5 または 10 px 単位へ丸めることを推奨する。

---

## 10. Color strategy

使用可能な代表色:

```text
Yellow  #FFF2A8
Green   #DDF4D2
Blue    #DCEEFF
Pink    #F7DDF1
Orange  #FFE0C2
Purple  #E9E0FF
```

色は意味を持たせる。

推奨例:

- Yellow: 基礎・問い
- Blue: 仕組み・構造
- Green: 実装・成功パターン
- Orange: 注意・境界
- Pink: 例外・失敗・アンチパターン
- Purple: 発展・設計判断

ただし、**色より空間構造を優先する。**
同じ意味を「色・距離・group・edge」のすべてで過剰表現しない。

---

## 11. Content-type selection

| Goal | Preferred type |
|---|---|
| 概念を説明する | `markdown` |
| 実装そのものを見せる | `code` |
| 流れ・関係・状態を理解させる | `mermaid` |
| 実物・画面・図版を見る | `image` |
| 一言メモ、ラベル、補助情報 | `markdown` |

### Default-type rule

特別な理由がない限り `markdown` を使う。

- 短いメモ → `markdown`
- 用語説明 → `markdown`
- 注意書き → `markdown`
- 比較・補足 → `markdown`
- 次の付箋への導入 → `markdown`

`code` は「コードそのものを読む価値」がある場合、
`mermaid` は「図として見る価値」がある場合、
`image` は「画像そのものを見る価値」がある場合に選ぶ。

`type: "text"` は生成しない。

### Mixed-media rule

複数タイプを使う場合、同じ核心をコピーしない。

例:

- markdown: 「middleware がなぜ順番依存なのか」
- code: 「最小の middleware chain」
- mermaid: 「request が handler を通過する順序」

これは重複ではなく、**説明・実装・構造**の異なる観点である。

---

## 12. Research and factual accuracy

依頼テーマが技術、製品、規格、バージョン依存情報の場合:

1. ユーザーが提供した資料を優先する
2. 最新情報が必要なら信頼できる一次情報を確認する
3. バージョン依存事項は popup 内で対象バージョンを明示する
4. 不確かな内容を断定しない
5. ボード上の短い hook に正確性を犠牲にした誇張を入れない

---

## 13. JSON authoring rules

### Required

- UTF-8 JSON
- JSON として parse 可能
- `notes`, `groups`, `edges` は配列
- すべての `id` は一意
- `group.noteIds` は存在する note ID のみ
- `childGroupIds` は存在する group ID のみ
- 自己参照 group を作らない
- group 階層に cycle を作らない
- edge の source / target は存在する group
- source != target
- `direction` は `none | right | left`
- note の `w`, `h` は特別な理由がなければ `210`, `150`
- rich note の生ソースを `inline` にそのまま保持する
- Markdown を HTML に事前変換しない
- Mermaid を SVG に事前変換しない
- code を HTML highlight 済みにしない

### ID naming

人間が追跡しやすい安定 ID を使う。

例:

```text
n01_request
n02_route
n03_middleware
g01_basics
e01_basics_to_flow
```

ランダム UUID は必要な場合だけ使う。

---

## 14. Quality gates

最終 JSON を出力する前に、次をすべて確認する。

### Content gate

- [ ] 各 rich note の説明の核心が popup にある
- [ ] title は短く識別しやすい
- [ ] text は popup へのフックになっている
- [ ] title / text / popup が重複していない
- [ ] popup を開くと疑問が解消する
- [ ] 1 note = 1 central idea

### Structure gate

- [ ] 類似内容が同じ group にまとまっている
- [ ] 異なる group の境界が明確
- [ ] edge は本当に必要なものだけ
- [ ] group 名だけでボードの論理構造を把握できる

### Layout gate

- [ ] note collision がない
- [ ] 同一 group の note は整列している
- [ ] 類縁度が高い note ほど近い
- [ ] group 間に十分な空白がある
- [ ] 左→右 / 上→下の自然な読順がある
- [ ] 初期 1500 x 900 付近で主要構造が把握できる
- [ ] 無駄に巨大なキャンバスにしていない

### Technical gate

- [ ] JSON parse 可能
- [ ] ID 参照がすべて有効
- [ ] すべての note.type が `markdown | code | mermaid | image` のいずれか
- [ ] メモ用途にも `markdown` が使われている
- [ ] code language が適切
- [ ] Mermaid syntax が妥当
- [ ] image URL が必要な場合に設定されている

---

## 15. Output behavior

ユーザーが「JSON ファイルを作成」と依頼した場合:

1. 内部で構成案とレイアウトを設計する
2. quality gates を検証する
3. **最終成果物として JSON ファイルを生成する**
4. 依頼がない限り、JSON 外に長い解説を混ぜない

ユーザーが「JSON を表示」と依頼した場合は、純粋な JSON をコードブロックで返す。

ユーザーが「改善案」を求めた場合は、まず問題点を説明してから改善 JSON を生成してよい。

---

## 16. Preferred planning sheet

JSON 化の前に内部で次の表を作ると品質が安定する。

| ID | Group | Role | Title | Hook (`text`) | Popup core | Type | Affinity |
|---|---|---|---|---|---|---|---|
| n01 | Basics | Concept | 最小の Express | 3行から全体像を見る | app → route → listen | code | n02=3 |
| n02 | Basics | Question | ルートはどう決まる？ | URLだけでは決まらない | method + path | markdown | n01=3 |
| n03 | Flow | Flow | 処理の通り道 | next() が次へ渡す | middleware chain | mermaid | n04=3 |

この表は通常ユーザーへ出力しない。
配置設計用の内部成果物として使う。

---

## 17. Reference layout pattern

4グループ、各2〜4付箋の例:

```text
┌────────────────┐      ┌────────────────┐
│ 01. 基礎        │ ---> │ 02. 処理の流れ   │
│ [A] [B]        │      │ [D] [E]        │
│ [C]            │      │ [F]            │
└────────────────┘      └────────────────┘

        ↓                         ↓

┌────────────────┐      ┌────────────────┐
│ 03. 実装        │ ---> │ 04. 失敗と運用   │
│ [G] [H]        │      │ [J] [K]        │
│ [I]            │      │ [L]            │
└────────────────┘      └────────────────┘
```

この形を機械的に使うのではなく、
テーマの意味構造に合わせて変形する。

---

## 18. Bundled reference board

`examples/reference-board.json` は、
Mermaid Sequence Diagram の書き方を説明するリファレンスボードである。

このサンプルから特に次を学ぶこと。

- `markdown` を通常メモのデフォルトとして使う
- `code` で Mermaid ソースそのものを読ませる
- `mermaid` で同じ構文の描画結果を確認させる
- グループを左から右へ並べ、学習順序を空間で表現する
- 各グループ内では「解説 → ソース → 描画」の順に縦配置する
- グループ間 edge は学習ステップの方向だけを示す

サンプルの題材は Mermaid 公式 Sequence Diagram ドキュメントの主要構文に基づく。

---

## 19. Final principle

良い KJ Session Board は「付箋を読ませるボード」ではない。

**ボードを眺めると構造が分かり、  
気になる付箋を開くと核心が分かる。**

この二段階の体験を、
`title → text → popup` の三層コピーと、
`group → distance → edge` の空間設計によって実現する。
