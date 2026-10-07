# KJ Session Board JSON Reference

## Canonical shape

```json
{
  "title": "string",
  "notes": [
    {
      "id": "string",
      "title": "string",
      "text": "string",
      "type": "markdown | code | mermaid | image",
      "inline": "string",
      "language": "string",
      "imageUrl": "string",
      "color": "#RRGGBB",
      "x": 0,
      "y": 0,
      "w": 210,
      "h": 150
    }
  ],
  "groups": [
    {
      "id": "string",
      "name": "string",
      "noteIds": ["note-id"],
      "childGroupIds": ["group-id"]
    }
  ],
  "edges": [
    {
      "id": "string",
      "source": "group-id",
      "target": "group-id",
      "label": "string",
      "direction": "none | right | left"
    }
  ]
}
```

## Type policy

Authoring で使用可能な `type` は次の4種類だけとする。

```text
markdown
code
mermaid
image
```

デフォルトは `markdown`。

短いメモ、補助説明、一言コメントでも `type: "text"` は使用しない。
`text` は note type ではなく、**ボード上に表示する短い見出しフィールド**である。

## Rendering semantics

- `title`: sticky note header.
- `text`: short hook/heading shown directly on the board.
- `markdown`: `inline` is rendered as Markdown in the popup.
- `code`: `inline` is syntax-highlighted using `language`.
- `mermaid`: `inline` is rendered as Mermaid in the popup.
- `image`: `imageUrl` is rendered as the popup image.

## Default authoring rule

特別な理由がなければ `markdown` を選ぶ。

```text
memo / explanation / caution / comparison / glossary
        ↓
     markdown
```

`code`, `mermaid`, `image` は、それぞれコード・図・画像自体が
説明の核心になる場合に使う。

## Geometry

Default note:

```text
210 x 150 px
```

Base canvas:

```text
1500 x 900 px
```

Automatic group padding around member content:

```text
left   30
right  30
top    52
bottom 30
```

The application expands the canvas automatically when notes or groups extend beyond the base area.
