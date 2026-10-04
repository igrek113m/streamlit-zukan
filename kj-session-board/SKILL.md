# SKILL.md — KJ Session Board Implementation Skill

## Skill name

`kj-session-board-development`

## Purpose

Streamlit Custom Components v2 を利用した KJ Session Board に対して、既存仕様を壊さずに機能追加・不具合修正・JSON schema 拡張を行う。

この skill を使う前に:

- `AGENT.md`
- `DESIGN.md`
- `reference_board.json`

を読むこと。

---

## 1. Trigger

次の依頼で使用する。

- 付箋機能を追加・変更
- グループ化を変更
- nested group を変更
- 接続線を変更
- edit/view mode を変更
- rich popup を変更
- JSON schema / import / export を変更
- fullscreen を変更
- KJ Session Board の不具合修正
- UI / interaction / layout の改善

---

## 2. First-pass analysis

要求を次の5分類へ分ける。

| 分類 | 問い |
|---|---|
| Data | JSON schema は変わるか |
| Interaction | click / dblclick / pointer / keyboard は変わるか |
| Geometry | note/group/edge の座標計算は変わるか |
| Presentation | edit / view / fullscreen の見た目は変わるか |
| Compatibility | 既存JSONを読み続けられるか |

変更箇所を決める前に、この5点を明示的に考える。

---

## 3. Read the current implementation

最低限検索する。

```bash
grep -nE 'normalizeBoard|addNote|deleteNote|createGroup|groupBoundsById|boundaryPoint|renderEdges|renderGroups|renderNotes|openNoteModal|setViewMode|exportJson|importJsonFile|fullscreen' app.py
```

特に対象機能の既存 event listener と state update の順序を確認する。

---

## 4. Data-model change recipe

新 field を追加するとき:

1. canonical JSON を決める
2. `normalizeBoard()` へ default を追加
3. 新規作成処理へ field を追加
4. Editor UI で変更するなら save handler へ追加
5. Renderer へ反映
6. JSON Export / Import round trip を確認
7. 必要に応じ `reference_board.json` も更新

reference fixture の制約:

```text
groups = 2
notes  = 4
```

は維持する。

---

## 5. Note change recipe

### text

表面本文を直接編集可能。

```text
blur
  ↓
snapshot()
  ↓
note.text = ...
  ↓
sync()
```

### rich note

対象:

```text
code
markdown
mermaid
image
```

表面:

```text
title + summary text + type badge
```

詳細:

```text
double click → modal
```

Edit mode:

```text
editable form
```

View mode:

```text
render-only preview
```

rich note type を増やす場合は:

1. normalize
2. add-note default
3. modal editor
4. display preview
5. badge / styles
6. JSON round trip

をセットで変更する。

---

## 6. Pointer-event safety recipe

ドラッグ可能 UI 内へ button を置く場合:

```javascript
button.addEventListener("pointerdown", evt => {
  evt.stopPropagation();
});

button.addEventListener("click", evt => {
  evt.preventDefault();
  evt.stopPropagation();
  evt.stopImmediatePropagation();
  action();
});
```

parent drag handler:

```javascript
if (evt.target.closest(".button-selector")) return;
```

Regression test:

```text
1. ボタン単クリック
2. ボタン長押し
3. ボタン周辺からdrag
4. 通常handleからdrag
```

---

## 7. Group geometry change recipe

`groupBoundsById()` は pure geometry function として扱う。

禁止:

- group DOM の `getBoundingClientRect()` を canonical geometry に使う
- group x/y/w/h を JSON に保存して真実とする
- child bounds を無視する

変更したら次をテスト。

```text
single note group
2-note group
nested group
deep nested group
child group moved
note deleted from child
child group deleted
```

親矩形から子タイトル・子点線・余白がはみ出さないこと。

---

## 8. Edge change recipe

現在の意味:

```text
source / target = logical relation
direction       = marker direction
geometry        = center-to-center direction
line endpoint   = group border
```

変更時は source/target と visual arrow direction を混同しない。

Boundary test:

```text
target right
target left
target above
target below
diagonal NE
diagonal NW
diagonal SE
diagonal SW
```

すべてで線端が矩形中心ではなく境界上にあること。

---

## 9. View-mode change recipe

UI を隠すだけではなく interaction を無効化する。

両方必要。

```text
CSS:
.view-mode .edit-control { display:none }

JS:
if (viewMode !== "edit") return
```

rich note popup は例外で view mode でも有効。

---

## 10. Fullscreen change recipe

fullscreen 対象:

```javascript
root.requestFullscreen()
```

`viewport.requestFullscreen()` へ戻さない。

modal は root subtree 内に置く。

fullscreen 中に modal を扱う場合:

```css
.kj-app:fullscreen .modal-shell.open {
  z-index: 2147483646;
}
```

Test:

```text
view mode
→ fullscreen
→ code note double click
→ popup visible
→ Esc
→ popup close
```

---

## 11. JSON change recipe

### Export test

1. `reference_board.json` を load
2. タイトルを変更
3. note を移動
4. edge direction を変更
5. JSON保存

### Import test

保存した JSON を読み込み直す。

比較対象:

```text
title
notes.length
groups.length
edges.length
note positions
note type
inline
language
imageUrl
color
group noteIds
group childGroupIds
edge label
edge direction
```

Invalid data でもクラッシュしないこと:

```text
missing title
missing note optional fields
invalid childGroupIds
edge points to missing group
invalid edge direction
```

---

## 12. Static verification

### Python

```bash
python -m py_compile app.py
```

### Embedded JavaScript

`app.py` 内の `JS = r""" ... """` を一時 `.mjs` へ抽出して確認する。

```python
from pathlib import Path
import re

src = Path("app.py").read_text(encoding="utf-8")
m = re.search(
    r'JS = r"""(.*?)"""\n\nKJ_BOARD_COMPONENT',
    src,
    flags=re.S,
)
assert m
Path("/tmp/kj_component.mjs").write_text(
    m.group(1),
    encoding="utf-8",
)
```

```bash
node --check /tmp/kj_component.mjs
```

---

## 13. Reference fixture verification

対象:

```text
reference_board.json
```

Python static check:

```python
import json

with open("reference_board.json", encoding="utf-8") as f:
    board = json.load(f)

assert len(board["groups"]) == 2
assert len(board["notes"]) == 4
assert len(board["edges"]) == 1

group_ids = {g["id"] for g in board["groups"]}
note_ids = {n["id"] for n in board["notes"]}

for g in board["groups"]:
    assert set(g["noteIds"]) <= note_ids
    assert set(g["childGroupIds"]) <= group_ids

for e in board["edges"]:
    assert e["source"] in group_ids
    assert e["target"] in group_ids
```

ブラウザでは JSON読込後:

```text
付箋 4 / グループ 2 / 接続 1
```

となること。

---

## 14. Browser acceptance sequence

変更後は可能なら次の順序で1回通す。

```text
1. app startup
2. reference_board.json import
3. edit title
4. add text note
5. delete note with ×
6. drag note
7. group notes
8. nest group
9. connect groups
10. edit edge
11. code popup edit
12. markdown popup edit
13. mermaid popup edit
14. image note create + URL
15. switch to view mode
16. open every rich note
17. fullscreen
18. rich note popup in fullscreen
19. JSON export
20. JSON re-import
21. undo
```

---

## 15. Change discipline

### Do

- 小さな関数を既存 `app` object へ追加
- state mutation 前に snapshot
- render と sync の責務を分ける
- normalizeBoard で compatibility を吸収
- `reference_board.json` を fixture として使う
- user-visible terminology を既存UIに合わせる

### Do not

- DOMだけを書き換えて state を更新しない
- JSON schema を説明なしに破壊する
- view mode の編集ガードを削る
- group bounds を固定保存する
- edge を中心点まで描く
- delete button の propagation guard を外す
- fullscreen 対象を modal の外側へ狭める
- Mermaid `securityLevel` を安易に緩める

---

## 16. Completion report template

AI エージェントは作業完了時、最低限次を報告する。

```text
変更:
- ...

互換性:
- reference_board.json: OK
- JSON round trip: OK

検証:
- Python syntax: OK
- JavaScript syntax: OK
- Browser test: OK / 未実施

既知の制約:
- ...
```

検証していない項目を「OK」と書かない。
