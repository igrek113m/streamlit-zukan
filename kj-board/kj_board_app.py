from __future__ import annotations

import base64
import copy
import mimetypes
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import streamlit as st


st.set_page_config(
    page_title="KJ Session Board",
    page_icon="🗂️",
    layout="wide",
)

EMPTY_BOARD: dict[str, Any] = {
    "title": "",
    "notes": [],
}


PDF_IMAGE_MAX_BYTES = 12 * 1024 * 1024
PDF_IMAGE_TIMEOUT_SECONDS = 6


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_pdf_image_data_url(url: str) -> str:
    """Fetch an external image on the Streamlit server for PDF embedding.

    Browser display of an external <img> can succeed even when html2canvas cannot
    read that image because the remote server does not allow cross-origin canvas
    access. Converting the image to a data URL on the Streamlit server avoids that
    browser CORS limitation during PDF export.
    """
    value = str(url or "").strip()
    if not value:
        return ""
    if value.startswith("data:image/"):
        return value

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""

    try:
        request = Request(
            value,
            headers={
                "User-Agent": "Mozilla/5.0 KJ-Session-Board-PDF/1.0",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=PDF_IMAGE_TIMEOUT_SECONDS) as response:
            content_type = (response.headers.get_content_type() or "").lower()
            if not content_type.startswith("image/"):
                guessed, _ = mimetypes.guess_type(parsed.path)
                content_type = guessed or ""
            if not content_type.startswith("image/"):
                return ""
            payload = response.read(PDF_IMAGE_MAX_BYTES + 1)
        if not payload or len(payload) > PDF_IMAGE_MAX_BYTES:
            return ""
        encoded = base64.b64encode(payload).decode("ascii")
        return f"data:{content_type};base64,{encoded}"
    except Exception:
        # Keep the board usable even if a remote image is temporarily unreachable.
        # The browser-side exporter will show an explicit placeholder instead of
        # silently producing an empty PDF image page.
        return ""


def build_pdf_image_data(board: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    notes = board.get("notes", []) if isinstance(board, dict) else []
    for note in notes:
        if not isinstance(note, dict) or note.get("type") != "image":
            continue
        url = str(note.get("imageUrl", "") or "").strip()
        if not url or url in result:
            continue
        data_url = fetch_pdf_image_data_url(url)
        if data_url:
            result[url] = data_url
    return result

HTML = r"""
<div class="kj-app edit-mode">
  <div class="workspace-shell">
    <section class="control-panel">
      <header class="board-header">
        <div class="board-brand">
          <span class="board-brand-mark">KJ</span>
          <strong>KJ Board</strong>
        </div>
      </header>

      <section class="panel-section creator-section">
        <div class="creator-top-row">
          <div class="panel-heading">付箋を追加</div>
          <div class="creator-grid">
            <select class="new-note-type" aria-label="付箋タイプ" title="付箋タイプ">
              <option value="markdown">Markdown</option>
              <option value="code">Code</option>
              <option value="mermaid">Mermaid</option>
              <option value="image">Image</option>
            </select>
            <input class="new-note-title" type="text" placeholder="タイトル" aria-label="タイトル" />
            <input class="new-note-text" type="text" placeholder="内容・メモ（任意）" aria-label="内容・メモ" />
            <select class="new-note-color" aria-label="付箋色" title="付箋色">
              <option value="#FFF2A8">Yellow</option>
              <option value="#DDF4D2">Green</option>
              <option value="#DCEEFF">Blue</option>
              <option value="#F7DDF1">Pink</option>
              <option value="#FFE0C2">Orange</option>
              <option value="#E9E0FF">Purple</option>
            </select>
            <button class="primary-btn add-note-btn" data-action="add-note">＋追加</button>
          </div>
        </div>
        <div class="visual-language-row" aria-label="付箋タイプの視覚言語">
          <strong>視覚言語</strong>
          <span><b class="type-chip">MD</b> Markdown</span>
          <span><b class="type-chip">CODE</b> Code</span>
          <span><b class="type-chip">MMD</b> Mermaid</span>
          <span><b class="type-chip">IMG</b> Image</span>
        </div>
      </section>

      <section class="panel-section z-order-panel">
        <div class="panel-heading-row">
          <div class="panel-heading">Z順</div>
          <div class="selected-note-summary">付箋を選択してください</div>
        </div>
        <div class="z-order-actions">
          <button data-action="step-front" disabled title="前面へ">↑前</button>
          <button data-action="step-back" disabled title="背面へ">↓後</button>
          <button data-action="bring-front" disabled title="最前面へ">⇈最前</button>
          <button data-action="send-back" disabled title="最背面へ">⇊最背</button>
        </div>
      </section>

      <section class="panel-section utilities">
        <div class="panel-heading-row">
          <div class="panel-heading">ボード</div>
          <span class="stats"></span>
        </div>
        <div class="utility-actions">
          <button data-action="undo" title="Undo" aria-label="Undo">↶</button>
          <button data-action="redo" title="Redo" aria-label="Redo">↷</button>
          <button data-action="export-json">保存</button>
          <button data-action="import-json">読込</button>
          <input class="json-file-input" type="file" accept="application/json,.json" hidden />
          <button data-action="reset" class="danger-ghost">消去</button>
        </div>
      </section>
    </section>

    <main class="board-main">
      <div class="presentation-toolbar" role="group" aria-label="表示モードと全画面">
        <button data-view="edit" class="view-btn active">✎ 編集</button>
        <button data-view="view" class="view-btn">▶ 表示</button>
        <button data-action="fullscreen" class="fullscreen-btn" title="全画面表示" aria-label="全画面表示">⛶ 全画面</button>
        <button data-action="export-pdf" class="pdf-btn" title="付箋をPDFに保存" aria-label="付箋をPDFに保存">PDF</button>
        <label class="horizontal-scroll-control" title="ボードを横スクロール">
          <span aria-hidden="true">↔</span>
          <input class="horizontal-scroll-slider" type="range" min="0" max="0" value="0" step="1" aria-label="ボードの横スクロール" />
        </label>
      </div>

      <div class="board-viewport">
        <div class="board-canvas">
          <div class="session-title-panel">
            <input class="session-title-input" type="text" maxlength="120"
                   placeholder="セッションタイトル" aria-label="セッションタイトル" />
            <div class="session-title-display"></div>
          </div>
          <div class="note-layer"></div>
        </div>
      </div>
    </main>
  </div>

  <div class="note-editor-modal modal-shell" aria-hidden="true">
    <div class="modal-backdrop" data-action="close-editor-modal"></div>
    <section class="modal-panel editor-modal-panel" role="dialog" aria-modal="true" aria-label="付箋編集">
      <header class="modal-header">
        <div>
          <div class="modal-kicker">STICKY NOTE</div>
          <h2 class="note-modal-heading">付箋</h2>
        </div>
        <button class="modal-close" data-action="close-editor-modal" title="閉じる">×</button>
      </header>

      <div class="editor-grid">
        <label class="editor-field">
          <span>タイトル</span>
          <input class="edit-note-title" type="text" placeholder="タイトル" />
        </label>
        <label class="editor-field">
          <span>付箋色</span>
          <select class="edit-note-color">
            <option value="#FFF2A8">Yellow</option>
            <option value="#DDF4D2">Green</option>
            <option value="#DCEEFF">Blue</option>
            <option value="#F7DDF1">Pink</option>
            <option value="#FFE0C2">Orange</option>
            <option value="#E9E0FF">Purple</option>
          </select>
        </label>
        <label class="editor-field full">
          <span>付箋に表示する内容</span>
          <textarea class="edit-note-text" rows="5" placeholder="内容・メモ（改行可）"></textarea>
        </label>
        <label class="editor-field edit-code-language-field" hidden>
          <span>プログラム言語</span>
          <select class="edit-note-language">
            <option value="python">Python</option>
            <option value="bash">Bash / Shell</option>
            <option value="powershell">PowerShell</option>
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
            <option value="json">JSON</option>
            <option value="yaml">YAML</option>
            <option value="sql">SQL</option>
            <option value="java">Java</option>
            <option value="csharp">C#</option>
            <option value="go">Go</option>
            <option value="rust">Rust</option>
            <option value="hcl">HCL / Terraform</option>
            <option value="dockerfile">Dockerfile</option>
            <option value="plaintext">Plain text</option>
          </select>
        </label>
        <label class="editor-field full edit-markdown-field">
          <span class="edit-rich-label">Markdown</span>
          <textarea class="edit-note-markdown" rows="12" spellcheck="false" placeholder="# Markdown"></textarea>
        </label>
        <label class="editor-field full edit-image-field" hidden>
          <span>画像 URL</span>
          <input class="edit-note-image" type="url" placeholder="https://example.com/image.png" />
        </label>
        <div class="image-preview full" hidden>
          <img class="image-preview-img" alt="画像プレビュー" />
          <div class="image-preview-empty" aria-hidden="true"></div>
        </div>
      </div>

      <footer class="modal-actions">
        <span class="action-spacer"></span>
        <button data-action="close-editor-modal">キャンセル</button>
        <button data-action="save-note" class="primary-btn">保存</button>
      </footer>
    </section>
  </div>

  <div class="note-viewer-modal modal-shell" aria-hidden="true">
    <div class="modal-backdrop viewer-backdrop" data-action="close-viewer-modal"></div>
    <section class="viewer-panel" role="dialog" aria-modal="true" aria-label="付箋表示">
      <header class="modal-header viewer-header">
        <div>
          <div class="modal-kicker">STICKY NOTE</div>
          <h2 class="viewer-modal-heading">付箋</h2>
        </div>
        <button class="modal-close viewer-close" data-action="close-viewer-modal" title="閉じる" aria-label="閉じる">×</button>
      </header>
      <div class="viewer-content">
        <div class="rendered-markdown markdown-view-card"></div>
        <div class="image-only-view" hidden>
          <img class="image-only-img" alt="付箋画像" />
        </div>
      </div>
    </section>
  </div>
</div>
"""

CSS = r"""
:host {
  --border: color-mix(in srgb, var(--st-text-color) 18%, transparent);
  --muted: color-mix(in srgb, var(--st-text-color) 61%, transparent);
  --accent: var(--st-primary-color);
  display: block;
}

* { box-sizing: border-box; }
[hidden] { display: none !important; }
button, input, textarea, select { font: inherit; }
button {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: .44rem .58rem;
  background: var(--st-background-color);
  color: var(--st-text-color);
  cursor: pointer;
}
button:hover:not(:disabled) { border-color: var(--accent); }
button:disabled { opacity: .4; cursor: default; }
.primary-btn { background: var(--accent); border-color: var(--accent); color: white; font-weight: 800; }
.danger-ghost:hover { border-color: #b42318; color: #b42318; }

.kj-app { width: 100%; color: var(--st-text-color); font-family: var(--st-font); }
.workspace-shell {
  display: flex;
  flex-direction: column;
  min-height: 76vh;
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  background: var(--st-background-color);
}
.control-panel {
  --control-font-size: 14px;
  flex: 0 0 auto;
  display: grid;
  grid-template-columns: 110px minmax(650px, 1fr) minmax(300px, .48fr) minmax(330px, .52fr);
  align-items: stretch;
  min-height: 64px;
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--st-secondary-background-color) 70%, var(--st-background-color));
  font-size: var(--control-font-size);
}
.control-panel button,
.control-panel input,
.control-panel select,
.control-panel .panel-heading,
.control-panel .selected-note-summary,
.control-panel .visual-language-row,
.control-panel .stats { font-size: var(--control-font-size); }
.board-header {
  padding: .28rem .4rem;
  background: var(--st-background-color);
  display: flex;
  align-items: center;
  border-right: 1px solid var(--border);
}
.board-brand { display: flex; gap: .36rem; align-items: center; white-space: nowrap; }
.board-brand strong { font-size: var(--control-font-size); line-height: 1; }
.board-brand-mark {
  width: 25px; height: 25px; border-radius: 6px; display: grid; place-items: center;
  background: var(--accent); color: white; font-size: 9px; font-weight: 900;
}
.panel-section { min-width: 0; border-right: 1px solid var(--border); }
.panel-heading { margin: 0; line-height: 1; font-weight: 800; color: var(--muted); white-space: nowrap; }
.panel-heading-row { display: flex; align-items: center; justify-content: space-between; gap: .35rem; min-width: 0; }
.creator-section { display: grid; grid-template-rows: 38px 25px; padding: 0; }
.creator-top-row { display: flex; align-items: center; gap: .42rem; padding: .22rem .42rem .16rem; min-width: 0; }
.creator-top-row > .panel-heading { flex: 0 0 auto; }
.creator-grid { flex: 1 1 auto; display: grid; grid-template-columns: 112px minmax(110px, .55fr) minmax(150px, 1fr) 86px 62px; gap: .2rem; align-items: center; min-width: 0; }
.new-note-type, .new-note-title, .new-note-text, .new-note-color {
  width: 100%; height: 30px; min-height: 30px; border: 1px solid var(--border); border-radius: 6px; padding: .25rem .4rem;
  background: var(--st-background-color); color: var(--st-text-color); line-height: 1.1;
}
.add-note-btn { height: 30px; padding: .22rem .42rem; white-space: nowrap; line-height: 1; }
.visual-language-row {
  display: flex; align-items: center; gap: .55rem; min-width: 0; padding: .08rem .42rem .16rem;
  border-top: 1px solid color-mix(in srgb, var(--border) 65%, transparent); color: var(--muted); line-height: 1; white-space: nowrap;
}
.visual-language-row strong { color: var(--muted); }
.visual-language-row > span { display: inline-flex; gap: .2rem; align-items: center; }
.type-chip { display: inline-grid; place-items: center; min-width: 25px; padding: .04rem .18rem; border: 1px solid var(--border); border-radius: 3px; background: var(--st-background-color); font-size: .78em; line-height: 1.05; font-weight: 900; }
.z-order-panel, .utilities { display: grid; grid-template-rows: 25px 38px; padding: 0 .42rem; align-content: center; }
.z-order-panel .panel-heading-row, .utilities .panel-heading-row { padding-top: .15rem; }
.selected-note-summary {
  min-width: 0; max-width: 190px; padding: 0; border: 0; background: transparent; color: var(--muted);
  line-height: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.selected-note-summary.has-selection { color: var(--st-text-color); }
.z-order-actions { display: grid; grid-template-columns: repeat(4, minmax(58px, 1fr)); gap: .2rem; align-items: center; }
.z-order-actions button { height: 30px; padding: .18rem .26rem; white-space: nowrap; }
.utility-actions { display: grid; grid-template-columns: 42px 42px repeat(3, minmax(70px, 1fr)); gap: .2rem; align-items: center; }
.utility-actions button { height: 30px; padding: .18rem .32rem; white-space: nowrap; }
.utility-actions [data-action="undo"], .utility-actions [data-action="redo"] { padding: 0; font-size: 18px; }
.stats { min-width: 0; color: var(--muted); line-height: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.board-main { min-width: 0; position: relative; flex: 1 1 auto; background: var(--st-background-color); }
.presentation-toolbar {
  position: absolute; top: 12px; right: 14px; z-index: 30; display: flex; align-items: center; gap: .35rem; padding: .35rem;
  border: 1px solid var(--border); border-radius: 10px; background: color-mix(in srgb, var(--st-background-color) 92%, transparent);
  box-shadow: 0 4px 16px rgba(0,0,0,.10); backdrop-filter: blur(4px);
}
.presentation-toolbar button { min-height: 34px; font-size: 14px; }
.view-btn.active { border-color: var(--accent); box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 15%, transparent); font-weight: 800; }
.fullscreen-btn { min-width: 88px; width: auto; padding-inline: .55rem; font-size: 14px; line-height: 1; white-space: nowrap; }
.pdf-btn { min-width: 48px; width: auto; padding-inline: .5rem; font-weight: 800; white-space: nowrap; }
.pdf-btn:disabled { opacity: .55; cursor: wait; }
.horizontal-scroll-control { display: flex; align-items: center; gap: .28rem; min-width: 118px; padding: 0 .2rem; color: var(--muted); }
.horizontal-scroll-control > span { flex: 0 0 auto; font-size: 15px; line-height: 1; }
.horizontal-scroll-slider { width: clamp(88px, 10vw, 150px); margin: 0; accent-color: var(--accent); cursor: ew-resize; }
.horizontal-scroll-slider:disabled { opacity: .35; cursor: default; }
.board-viewport {
  height: 82vh; min-height: 650px; overflow: auto;
  background: linear-gradient(to right, rgba(70,70,70,.055) 1px, transparent 1px), linear-gradient(to bottom, rgba(70,70,70,.055) 1px, transparent 1px), var(--st-background-color);
  background-size: 24px 24px;
}
.board-canvas { width: 2300px; height: 1500px; position: relative; user-select: none; }
.session-title-panel { position: absolute; top: 22px; left: 30px; z-index: 9000; }
.session-title-input { width: min(990px, 82.5vw); padding: .45rem .6rem; border: 1px dashed var(--border); border-radius: 8px; background: color-mix(in srgb, var(--st-background-color) 90%, transparent); font-size: 21px; font-weight: 850; color: var(--st-text-color); }
.session-title-display { max-width: 1350px; font-size: 21px; font-weight: 900; line-height: 1.2; white-space: pre-wrap; overflow-wrap: anywhere; }
.kj-app.edit-mode .session-title-display { display: none; }
.kj-app.view-mode .session-title-input { display: none; }
.note-layer { position: absolute; inset: 0; z-index: 3; pointer-events: none; }

.sticky-note {
  position: absolute; width: 220px; min-height: 165px; height: auto; border: 1px solid rgba(0,0,0,.17); border-radius: 4px;
  box-shadow: 0 7px 18px rgba(0,0,0,.14); pointer-events: auto; color: #202020; overflow: hidden; transform: rotate(-.14deg);
  transition: box-shadow .14s ease, transform .14s ease, outline .1s ease;
}
.sticky-note:hover { box-shadow: 0 11px 25px rgba(0,0,0,.18); transform: translateY(-1px); }
.sticky-note.selected-note { outline: 3px solid var(--accent); outline-offset: 3px; box-shadow: 0 12px 28px rgba(0,0,0,.23); }
.note-handle { height: 25px; display: flex; justify-content: space-between; align-items: center; padding: 0 .32rem 0 .5rem; border-bottom: 1px dashed rgba(0,0,0,.17); cursor: grab; color: rgba(0,0,0,.55); font-size: 10px; }
.note-handle:active { cursor: grabbing; }
.note-delete { width: 24px; height: 22px; padding: 0; border: none; background: transparent; color: rgba(0,0,0,.52); font-weight: 900; }
.note-delete:hover { color: #a00; }
.note-title { min-height: 31px; padding: .36rem .62rem; display: flex; gap: .4rem; align-items: flex-start; background: rgba(255,255,255,.28); border-bottom: 1px solid rgba(0,0,0,.10); }
.note-title-text { flex: 1; min-width: 0; white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word; font-weight: 850; font-size: 14px; line-height: 1.32; }
.note-type-badge { flex: 0 0 auto; font-size: 9px; border: 1px solid rgba(0,0,0,.22); border-radius: 999px; padding: .06rem .3rem; white-space: nowrap; }
.note-body { min-height: 84px; max-height: 190px; padding: .62rem .72rem; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; user-select: text; font-size: 14px; line-height: 1.42; color: #171717; }
.note-thumbnail-wrap { padding: 0 .62rem .68rem; }
.note-thumbnail { display: block; width: 100%; height: 112px; object-fit: cover; border: 1px solid rgba(0,0,0,.16); border-radius: 5px; background: rgba(255,255,255,.45); }
.note-thumbnail-empty { display: grid; place-items: center; min-height: 72px; padding: .5rem; border: 1px dashed rgba(0,0,0,.25); border-radius: 5px; color: rgba(0,0,0,.55); font-size: 11px; text-align: center; }

.modal-shell { display: none; position: fixed; inset: 0; z-index: 10000; align-items: center; justify-content: center; padding: min(4vh, 32px) min(4vw, 32px); }
.modal-shell.open { display: flex; }
.modal-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,.58); backdrop-filter: blur(3px); }
.modal-panel { position: relative; z-index: 1; width: min(900px, 92vw); max-height: 90vh; overflow: auto; margin: 0; padding: 1rem; border: 1px solid var(--border); border-radius: 14px; background: var(--st-background-color); box-shadow: 0 24px 70px rgba(0,0,0,.32); }
.modal-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; border-bottom: 1px solid var(--border); padding-bottom: .7rem; }
.modal-header h2 { margin: .15rem 0 0; font-size: 1.15rem; }
.modal-kicker { color: var(--muted); font-size: 10px; font-weight: 900; letter-spacing: .08em; }
.modal-close { width: 34px; height: 34px; padding: 0; font-size: 22px; }
.editor-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; padding-top: .8rem; }
.editor-field.full, .image-preview.full { grid-column: 1 / -1; }
.editor-field input, .editor-field textarea, .editor-field select { width: 100%; border: 1px solid var(--border); border-radius: 8px; padding: .55rem .65rem; background: var(--st-background-color); color: var(--st-text-color); }
.editor-field textarea { white-space: pre-wrap; resize: vertical; }
.edit-note-markdown { min-height: 250px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; line-height: 1.5; }
.edit-code-language-field { align-self: end; }
.image-preview { width: min(510px, 100%); height: 180px; padding: .65rem; border: 1px solid var(--border); border-radius: 10px; background: var(--st-secondary-background-color); }
.image-preview-img { display: none; width: 100%; height: 100%; object-fit: contain; border-radius: 7px; }
.image-preview.has-image .image-preview-img { display: block; }
.image-preview-empty { display: none; }
.modal-actions { display: flex; gap: .5rem; align-items: center; padding-top: .9rem; }
.action-spacer { flex: 1; }

.viewer-panel { position: relative; z-index: 1; width: min(1080px, 94vw); max-height: 92vh; overflow: auto; margin: 0; padding: 1.1rem 1.35rem 1.35rem; border: 1px solid var(--border); border-radius: 14px; background: var(--st-background-color); box-shadow: 0 24px 70px rgba(0,0,0,.38); }
.viewer-header { margin-bottom: 1rem; }
.viewer-content { min-width: 0; }
.viewer-close { flex: 0 0 auto; }
.markdown-view-card { min-height: 400px; padding: 2rem 1.25rem; border: 1px solid var(--border); border-radius: 10px; background: color-mix(in srgb, var(--st-secondary-background-color) 52%, var(--st-background-color)); }
.rendered-markdown { color: var(--st-text-color); line-height: 1.7; overflow-wrap: anywhere; }
.rendered-markdown h1, .rendered-markdown h2, .rendered-markdown h3, .rendered-markdown h4, .rendered-markdown h5, .rendered-markdown h6 { line-height: 1.25; margin: 1.15em 0 .55em; }
.rendered-markdown h1 { font-size: 2rem; }.rendered-markdown h2 { font-size: 1.55rem; }.rendered-markdown h3 { font-size: 1.25rem; }.rendered-markdown h4 { font-size: 1.05rem; }.rendered-markdown h5 { font-size: .88rem; }.rendered-markdown h6 { font-size: .76rem; }
.rendered-markdown h1:first-child, .rendered-markdown h2:first-child, .rendered-markdown h3:first-child, .rendered-markdown h4:first-child, .rendered-markdown h5:first-child, .rendered-markdown h6:first-child { margin-top: .2rem; }
.rendered-markdown p { margin: .65rem 0; }
.rendered-markdown ul, .rendered-markdown ol { padding-left: 1.5rem; }
.rendered-markdown blockquote { margin: .8rem 0; padding: .35rem .8rem; border-left: 4px solid var(--accent); background: var(--st-secondary-background-color); color: var(--muted); }
.rendered-markdown pre { overflow: auto; padding: .85rem; border-radius: 8px; background: color-mix(in srgb, var(--st-secondary-background-color) 78%, #111 8%); }
.rendered-markdown code { padding: .08rem .25rem; border-radius: 4px; background: var(--st-secondary-background-color); font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.rendered-markdown pre code { padding: 0; background: transparent; }
/* Code sticky-note viewer: keep the same dark palette in both Streamlit themes. */
.rendered-markdown.code-note-preview {
  background: #23242b;
  color: #e5e7eb;
  border-color: #30323b;
}
.rendered-markdown.code-note-preview pre {
  margin: 0;
  padding: 1rem;
  border-radius: 8px;
  background: #23242b !important;
  color: #e5e7eb !important;
}
.rendered-markdown.code-note-preview pre code.hljs {
  display: block;
  padding: 0;
  background: transparent !important;
  color: #e5e7eb !important;
}
.rendered-markdown .mermaid-host svg { display: block; max-width: 100%; height: auto; margin: 0 auto; }
.loading-preview { color: var(--muted); text-align: center; padding: 2rem; }
.preview-error { padding: .8rem; border: 1px solid #d66; color: #b22; border-radius: 8px; white-space: pre-wrap; }
.hljs-keyword, .hljs-selector-tag, .hljs-literal, .hljs-section, .hljs-link { color: #c084fc; }
.hljs-string, .hljs-title, .hljs-name, .hljs-type, .hljs-attribute, .hljs-symbol, .hljs-bullet, .hljs-addition { color: #86efac; }
.hljs-number, .hljs-meta, .hljs-built_in, .hljs-builtin-name, .hljs-params { color: #fbbf24; }
.hljs-comment, .hljs-quote, .hljs-deletion { color: #94a3b8; font-style: italic; }
.hljs-variable, .hljs-template-variable, .hljs-selector-id, .hljs-selector-class { color: #7dd3fc; }
.hljs-regexp, .hljs-template-tag { color: #fda4af; }
.hljs-emphasis { font-style: italic; }
.hljs-strong { font-weight: 800; }
.rendered-markdown a { color: var(--accent); }
.rendered-markdown hr { border: 0; border-top: 1px solid var(--border); margin: 1.2rem 0; }
.markdown-table-scroll { width: 100%; overflow-x: auto; }
.rendered-markdown table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
.rendered-markdown th, .rendered-markdown td { padding: .5rem .65rem; border: 1px solid var(--border); text-align: left; vertical-align: top; }
.rendered-markdown th { font-weight: 800; background: var(--st-secondary-background-color); }
.rendered-markdown tbody tr:nth-child(even) { background: color-mix(in srgb, var(--st-secondary-background-color) 45%, transparent); }
.image-only-view { display: grid; place-items: center; min-height: 400px; padding: 1rem; border: 1px solid var(--border); border-radius: 10px; background: color-mix(in srgb, var(--st-secondary-background-color) 52%, var(--st-background-color)); }
.image-only-img { display: block; max-width: 100%; max-height: 72vh; object-fit: contain; border-radius: 7px; }

.kj-app.view-mode .control-panel { display: none; }
.kj-app.view-mode .note-handle, .kj-app.view-mode .note-delete { display: none; }
.kj-app.view-mode .board-viewport { height: 88vh; }
.kj-app.view-mode .sticky-note { transform: none; box-shadow: 0 12px 28px rgba(0,0,0,.18); }
.kj-app.view-mode .sticky-note:hover { transform: translateY(-2px) scale(1.01); }
.kj-app.view-mode .sticky-note.selected-note { outline: none; }
.kj-app.view-mode .session-title-panel { top: 28px; left: 34px; }

.kj-app:fullscreen { width: 100vw; height: 100vh; background: var(--st-background-color); }
.kj-app:fullscreen .workspace-shell { height: 100vh; min-height: 0; border-radius: 0; border: none; }
.kj-app:fullscreen .board-main { min-height: 0; }
.kj-app:fullscreen .board-viewport { height: 100%; min-height: 0; }
.kj-app:fullscreen .presentation-toolbar { position: absolute; top: 10px; right: 14px; }
.kj-app:fullscreen .modal-shell.open { z-index: 2147483646; }

@media (max-width: 1380px) {
  .control-panel { grid-template-columns: 96px minmax(570px, 1fr) minmax(260px, .46fr) minmax(280px, .48fr); }
  .creator-grid { grid-template-columns: 110px minmax(135px, .6fr) minmax(170px, 1fr) 88px 64px; }
  .selected-note-summary { max-width: 120px; }
  .z-order-actions { grid-template-columns: repeat(4, minmax(50px, 1fr)); }
  .utility-actions { grid-template-columns: 38px 38px repeat(3, minmax(58px, 1fr)); }
}
@media (max-width: 1050px) {
  .control-panel { display: grid; grid-template-columns: 92px minmax(0, 1fr); min-height: 0; }
  .board-header { grid-row: 1 / span 3; }
  .creator-section, .z-order-panel, .utilities { grid-column: 2; border-right: none; border-bottom: 1px solid var(--border); }
  .creator-grid { grid-template-columns: 110px minmax(130px, .65fr) minmax(180px, 1fr) minmax(90px, .45fr) 68px; }
  .presentation-toolbar { left: 10px; right: 10px; flex-wrap: wrap; }
  .horizontal-scroll-control { flex: 1 1 120px; }
}
@media (max-width: 760px) {
  .control-panel { display: block; }
  .board-header { display: none; }
  .creator-section { grid-template-rows: auto auto; }
  .creator-top-row { display: block; padding-top: .35rem; }
  .creator-top-row > .panel-heading { margin-bottom: .3rem; }
  .creator-grid { grid-template-columns: 1fr 1fr; }
  .creator-grid .new-note-type, .creator-grid .new-note-title, .creator-grid .new-note-text { grid-column: 1 / -1; }
  .visual-language-row { flex-wrap: wrap; }
  .z-order-panel, .utilities { padding-bottom: .35rem; }
  .z-order-actions { grid-template-columns: repeat(4, 1fr); }
  .utility-actions { grid-template-columns: 42px 42px repeat(3, 1fr); }
  .editor-grid { grid-template-columns: 1fr; }
  .editor-field.full, .image-preview.full { grid-column: auto; }
}

"""

JS = r"""
const NOTE_W = 220;
const NOTE_ESTIMATED_H = 190;
const IMAGE_ESTIMATED_H = 330;

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function uid(prefix) {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function normalizeText(value) {
  return value == null ? "" : String(value).replace(/\r\n?/g, "\n");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

let moduleCache = null;

async function loadRenderModules() {
  if (moduleCache) return moduleCache;
  moduleCache = Promise.all([
    import("https://cdn.jsdelivr.net/npm/marked@16/+esm"),
    import("https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"),
    import("https://cdn.jsdelivr.net/npm/highlight.js@11.11.1/+esm"),
  ]).then(([markedModule, mermaidModule, highlightModule]) => {
    const mermaid = mermaidModule.default;
    mermaid.initialize({startOnLoad: false, securityLevel: "strict", theme: "default"});
    return {
      marked: markedModule.marked,
      mermaid,
      hljs: highlightModule.default || highlightModule,
    };
  });
  return moduleCache;
}

let pdfModuleLoader = null;

function loadScriptOnce(src, ready, errorMessage) {
  if (ready()) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = [...document.scripts].find(script => script.src === src);
    if (existing) {
      const wait = () => ready() ? resolve() : reject(new Error(errorMessage));
      if (existing.dataset.kjLoaded === "true") { wait(); return; }
      existing.addEventListener("load", wait, {once: true});
      existing.addEventListener("error", () => reject(new Error(errorMessage)), {once: true});
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onload = () => {
      script.dataset.kjLoaded = "true";
      ready() ? resolve() : reject(new Error(errorMessage));
    };
    script.onerror = () => reject(new Error(errorMessage));
    document.head.appendChild(script);
  });
}

function loadPdfModules() {
  if (window.html2canvas && window.jspdf?.jsPDF) {
    return Promise.resolve({html2canvas: window.html2canvas, jsPDF: window.jspdf.jsPDF});
  }
  if (pdfModuleLoader) return pdfModuleLoader;
  pdfModuleLoader = Promise.all([
    loadScriptOnce(
      "https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js",
      () => Boolean(window.html2canvas),
      "html2canvas の読み込みに失敗しました。"
    ),
    loadScriptOnce(
      "https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js",
      () => Boolean(window.jspdf?.jsPDF),
      "jsPDF の読み込みに失敗しました。"
    ),
  ]).then(() => ({html2canvas: window.html2canvas, jsPDF: window.jspdf.jsPDF}));
  return pdfModuleLoader;
}

function waitForImage(img, timeoutMs = 8000) {
  if (!img || !img.src || img.complete) return Promise.resolve();
  return new Promise(resolve => {
    const done = () => {
      clearTimeout(timer);
      img.removeEventListener("load", done);
      img.removeEventListener("error", done);
      resolve();
    };
    const timer = setTimeout(done, timeoutMs);
    img.addEventListener("load", done, {once: true});
    img.addEventListener("error", done, {once: true});
  });
}

function noteTypeLabel(type) {
  return ({markdown: "Markdown", code: "Code", mermaid: "Mermaid", image: "Image"})[type] || "Markdown";
}

function noteTypeBadge(type) {
  return ({markdown: "MD", code: "CODE", mermaid: "MMD", image: "IMG"})[type] || "MD";
}

function sanitizeHref(value) {
  const href = String(value || "").trim();
  if (/^(https?:|mailto:|#)/i.test(href)) return href;
  return "#";
}

function renderInlineMarkdown(text) {
  let html = escapeHtml(text);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/__([^_]+)__/g, "<strong>$1</strong>");
  html = html.replace(/~~([^~]+)~~/g, "<del>$1</del>");
  html = html.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => `<a href="${escapeHtml(sanitizeHref(href))}" target="_blank" rel="noopener noreferrer">${label}</a>`);
  return html;
}

function renderMarkdown(source) {
  const input = source == null ? "" : String(source);
  if (!input.trim()) return '<p class="empty-markdown">Markdown ソースは未入力です。</p>';

  const codeBlocks = [];
  const tokenized = input.replace(/```([^\n]*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const token = `@@KJCODE${codeBlocks.length}@@`;
    codeBlocks.push(`<pre><code data-language="${escapeHtml(lang.trim())}">${escapeHtml(code.replace(/\n$/, ""))}</code></pre>`);
    return `\n${token}\n`;
  });

  const splitTableRow = line => {
    let value = String(line ?? "").trim();
    if (value.startsWith("|")) value = value.slice(1);
    if (value.endsWith("|")) value = value.slice(0, -1);
    const cells = [];
    let cell = "";
    let escaped = false;
    for (const ch of value) {
      if (escaped) {
        cell += ch;
        escaped = false;
      } else if (ch === "\\") {
        escaped = true;
        cell += ch;
      } else if (ch === "|") {
        cells.push(cell.trim());
        cell = "";
      } else {
        cell += ch;
      }
    }
    cells.push(cell.trim());
    return cells;
  };
  const tableDelimiter = cell => /^:?-{3,}:?$/.test(String(cell || "").replace(/\s+/g, ""));
  const tableBlocks = [];
  const sourceLines = tokenized.split(/\r?\n/);
  const tableTokenizedLines = [];
  for (let i = 0; i < sourceLines.length; i += 1) {
    const headerLine = sourceLines[i];
    const delimiterLine = sourceLines[i + 1];
    const headerCells = splitTableRow(headerLine);
    const delimiterCells = delimiterLine == null ? [] : splitTableRow(delimiterLine);
    const looksLikeTable = headerLine.includes("|") && delimiterCells.length === headerCells.length && delimiterCells.length > 0 && delimiterCells.every(tableDelimiter);
    if (!looksLikeTable) {
      tableTokenizedLines.push(headerLine);
      continue;
    }

    const aligns = delimiterCells.map(cell => {
      const value = cell.replace(/\s+/g, "");
      if (value.startsWith(":") && value.endsWith(":")) return "center";
      if (value.endsWith(":")) return "right";
      return "left";
    });
    const bodyRows = [];
    i += 1;
    while (i + 1 < sourceLines.length) {
      const candidate = sourceLines[i + 1];
      if (!candidate.trim() || !candidate.includes("|")) break;
      const cells = splitTableRow(candidate);
      if (cells.length !== headerCells.length) break;
      bodyRows.push(cells);
      i += 1;
    }
    const headerHtml = headerCells.map((cell, index) => `<th style="text-align:${aligns[index]}">${renderInlineMarkdown(cell)}</th>`).join("");
    const bodyHtml = bodyRows.map(row => `<tr>${row.map((cell, index) => `<td style="text-align:${aligns[index]}">${renderInlineMarkdown(cell)}</td>`).join("")}</tr>`).join("");
    const token = `@@KJTABLE${tableBlocks.length}@@`;
    tableBlocks.push(`<div class="markdown-table-scroll"><table><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table></div>`);
    tableTokenizedLines.push(token);
  }

  const lines = tableTokenizedLines;
  const out = [];
  let listType = null;
  let paragraph = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    out.push(`<p>${paragraph.map(renderInlineMarkdown).join("<br>")}</p>`);
    paragraph = [];
  };
  const closeList = () => {
    if (!listType) return;
    out.push(`</${listType}>`);
    listType = null;
  };
  const openList = type => {
    if (listType === type) return;
    closeList();
    flushParagraph();
    listType = type;
    out.push(`<${type}>`);
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      closeList();
      continue;
    }
    if (/^@@KJ(?:CODE|TABLE)\d+@@$/.test(trimmed)) {
      flushParagraph(); closeList(); out.push(trimmed); continue;
    }
    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushParagraph(); closeList(); const level = heading[1].length; out.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`); continue;
    }
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      flushParagraph(); closeList(); out.push("<hr>"); continue;
    }
    const quote = trimmed.match(/^>\s?(.*)$/);
    if (quote) {
      flushParagraph(); closeList(); out.push(`<blockquote>${renderInlineMarkdown(quote[1])}</blockquote>`); continue;
    }
    const unordered = trimmed.match(/^[-*+]\s+(.+)$/);
    if (unordered) {
      openList("ul"); out.push(`<li>${renderInlineMarkdown(unordered[1])}</li>`); continue;
    }
    const ordered = trimmed.match(/^\d+[.)]\s+(.+)$/);
    if (ordered) {
      openList("ol"); out.push(`<li>${renderInlineMarkdown(ordered[1])}</li>`); continue;
    }
    closeList();
    paragraph.push(line);
  }
  flushParagraph();
  closeList();

  let html = out.join("\n");
  html = html.replace(/@@KJCODE(\d+)@@/g, (_, index) => codeBlocks[Number(index)] || "");
  html = html.replace(/@@KJTABLE(\d+)@@/g, (_, index) => tableBlocks[Number(index)] || "");
  return html;
}

function migrateLegacyNote(note, index) {
  let sourceType = String(note?.type || "").toLowerCase();
  if (!sourceType && Array.isArray(note?.details) && note.details.length) {
    sourceType = note.details[0]?.kind === "mermaid" ? "mermaid" : "code";
  }
  if (!sourceType) sourceType = "markdown";
  const allowedTypes = ["markdown", "code", "mermaid", "image"];
  const type = allowedTypes.includes(sourceType) ? sourceType : "markdown";
  const text = normalizeText(note?.text || "");
  let markdownSource = normalizeText(note?.markdownSource || note?.markdown || "");
  let inline = normalizeText(note?.inline || "");
  let language = String(note?.language || "python");

  if (type === "markdown" && !markdownSource && inline) markdownSource = inline;
  if ((type === "code" || type === "mermaid") && !inline && markdownSource) inline = markdownSource;

  // Compatibility with the older details model used by rich notes.
  if (Array.isArray(note?.details) && note.details.length) {
    const detail = note.details[0] || {};
    const detailText = normalizeText(detail.code || "");
    if (detailText) {
      if (detail.kind === "mermaid") {
        inline = inline || detailText;
        language = "mermaid";
      } else if (type === "code") {
        inline = inline || detailText;
        language = String(detail.lang || language || "plaintext");
      } else if (type === "markdown") {
        markdownSource = markdownSource || detailText;
      }
    }
  }

  return {
    id: note?.id || uid("note"),
    title: normalizeText(note?.title || ""),
    text,
    markdownSource: type === "markdown" ? markdownSource : "",
    inline: type === "markdown" ? markdownSource : (type === "image" ? "" : inline),
    language: type === "code" ? language : (type === "mermaid" ? "mermaid" : ""),
    type,
    imageUrl: normalizeText(note?.imageUrl || "").trim(),
    color: note?.color || "#FFF2A8",
    x: Number(note?.x ?? 90),
    y: Number(note?.y ?? 130),
    w: Number(note?.w || NOTE_W),
    z: Number.isFinite(Number(note?.z)) ? Number(note.z) : index,
  };
}

function normalizeBoard(board) {
  const src = board && typeof board === "object" ? board : {};
  const rawNotes = Array.isArray(src.notes) ? src.notes : [];
  const notes = rawNotes.map((note, index) => migrateLegacyNote(note, index));
  const ordered = [...notes].sort((a, b) => a.z - b.z);
  ordered.forEach((note, index) => { note.z = index; });
  return { title: normalizeText(src.title || ""), notes };
}

/** Get the union of the Mermaid SVG viewBox and the actual graphics bbox. */
function mermaidPdfBounds(svg) {
  const boxes = [];
  const vb = svg.viewBox?.baseVal;
  if (vb && [vb.x, vb.y, vb.width, vb.height].every(Number.isFinite) && vb.width > 0 && vb.height > 0) {
    boxes.push({x: vb.x, y: vb.y, width: vb.width, height: vb.height});
  }
  try {
    const box = svg.getBBox();
    if ([box.x, box.y, box.width, box.height].every(Number.isFinite) && box.width > 0 && box.height > 0) {
      boxes.push(box);
    }
  } catch (_) { /* getBBox may fail on some browser engines. */ }
  if (!boxes.length) throw new Error("SVG の描画範囲を取得できません");
  const left = Math.min(...boxes.map(b => b.x));
  const top = Math.min(...boxes.map(b => b.y));
  const right = Math.max(...boxes.map(b => b.x + b.width));
  const bottom = Math.max(...boxes.map(b => b.y + b.height));
  const margin = Math.max(12, Math.min(36, Math.max(right - left, bottom - top) * .02));
  return {x: left - margin, y: top - margin, width: right - left + margin * 2, height: bottom - top + margin * 2};
}

function loadSvgAsImage(source, timeoutMs = 12000) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    let settled = false;
    const timer = setTimeout(() => done(new Error("SVG の読み込みがタイムアウトしました")), timeoutMs);
    const done = (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      img.onload = null;
      img.onerror = null;
      if (err) reject(err);
      else resolve(img);
    };
    img.onload = () => done();
    img.onerror = () => done(new Error("Mermaid SVG を画像に変換できません"));
    img.src = source;
  });
}

async function rasterizeMermaidForPdf(svg, host) {
  const bounds = mermaidPdfBounds(svg);
  // Set absolute source dimensions, independent of the A4 frame and any
  // Mermaid-generated CSS max-width. A percentage-sized SVG inside an <img>
  // is a major source of clipping/blank diagrams in Chromium.
  const clone = svg.cloneNode(true);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
  clone.setAttribute("viewBox", `${bounds.x} ${bounds.y} ${bounds.width} ${bounds.height}`);
  clone.setAttribute("width", String(bounds.width));
  clone.setAttribute("height", String(bounds.height));
  clone.setAttribute("preserveAspectRatio", "xMidYMid meet");
  clone.style.removeProperty("max-width");
  clone.style.removeProperty("max-height");
  clone.style.setProperty("width", `${bounds.width}px`, "important");
  clone.style.setProperty("height", `${bounds.height}px`, "important");
  clone.style.setProperty("overflow", "visible", "important");

  const xml = new XMLSerializer().serializeToString(clone);
  const sourceImage = await loadSvgAsImage(`data:image/svg+xml;charset=utf-8,${encodeURIComponent(xml)}`);
  const availableWidth = host.clientWidth;
  const availableHeight = host.clientHeight;
  if (availableWidth <= 0 || availableHeight <= 0) throw new Error("PDF の Mermaid 描画枠が未確定です");

  // Exact numeric width/height (rather than 100% + object-fit) guarantee the
  // diagram stays within *both* A4 axes, even for very tall/wide flowcharts.
  const fit = Math.min(availableWidth / bounds.width, availableHeight / bounds.height);
  const renderWidth = Math.max(1, Math.min(availableWidth, bounds.width * fit));
  const renderHeight = Math.max(1, Math.min(availableHeight, bounds.height * fit));
  const pixelScale = Math.min(2, 3000 / renderWidth, 3000 / renderHeight);
  const bitmap = document.createElement("canvas");
  bitmap.className = "kj-pdf-mermaid-canvas";
  bitmap.width = Math.max(1, Math.round(renderWidth * pixelScale));
  bitmap.height = Math.max(1, Math.round(renderHeight * pixelScale));
  bitmap.style.width = `${renderWidth}px`;
  bitmap.style.height = `${renderHeight}px`;
  const context = bitmap.getContext("2d");
  if (!context) throw new Error("Mermaid 用 Canvas を作成できません");
  context.drawImage(sourceImage, 0, 0, bitmap.width, bitmap.height);
  // Check that the browser can read the bitmap before html2canvas is invoked.
  // If it was tainted by an external resource, don't silently save a blank PDF.
  bitmap.toDataURL("image/png");
  host.replaceChildren(bitmap);
}

export default function(component) {
  const { parentElement, data, setStateValue } = component;

  if (parentElement.__kjApp) {
    const app = parentElement.__kjApp;
    app.pdfImageData = data?.pdfImageData && typeof data.pdfImageData === "object" ? data.pdfImageData : {};
    const incoming = normalizeBoard(data?.board);
    const incomingSerialized = JSON.stringify(incoming);
    if (incomingSerialized !== app.lastSyncedSerialized && incomingSerialized !== JSON.stringify(app.board)) {
      app.board = clone(incoming);
      app.history = [];
      app.future = [];
      if (app.selectedNoteId && !app.noteById(app.selectedNoteId)) app.selectedNoteId = null;
      app.render();
    }
    return;
  }

  const root = parentElement.querySelector(".kj-app");
  const canvas = root.querySelector(".board-canvas");
  const viewport = root.querySelector(".board-viewport");
  const noteLayer = root.querySelector(".note-layer");
  const sessionTitleInput = root.querySelector(".session-title-input");
  const sessionTitleDisplay = root.querySelector(".session-title-display");
  const typeInput = root.querySelector(".new-note-type");
  const titleInput = root.querySelector(".new-note-title");
  const textInput = root.querySelector(".new-note-text");
  const colorInput = root.querySelector(".new-note-color");
  const stats = root.querySelector(".stats");
  const fileInput = root.querySelector(".json-file-input");
  const horizontalScrollSlider = root.querySelector(".horizontal-scroll-slider");
  const pdfButton = root.querySelector('[data-action="export-pdf"]');
  const selectedSummary = root.querySelector(".selected-note-summary");

  const editorModal = root.querySelector(".note-editor-modal");
  const modalHeading = root.querySelector(".note-modal-heading");
  const editTitle = root.querySelector(".edit-note-title");
  const editColor = root.querySelector(".edit-note-color");
  const editText = root.querySelector(".edit-note-text");
  const editMarkdownField = root.querySelector(".edit-markdown-field");
  const editRichLabel = root.querySelector(".edit-rich-label");
  const editMarkdown = root.querySelector(".edit-note-markdown");
  const editCodeLanguageField = root.querySelector(".edit-code-language-field");
  const editLanguage = root.querySelector(".edit-note-language");
  const editImageField = root.querySelector(".edit-image-field");
  const editImage = root.querySelector(".edit-note-image");
  const imagePreview = root.querySelector(".image-preview");
  const imagePreviewImg = root.querySelector(".image-preview-img");
  const saveNoteButton = root.querySelector('[data-action="save-note"]');

  const viewerModal = root.querySelector(".note-viewer-modal");
  const viewerHeading = root.querySelector(".viewer-modal-heading");
  const renderedMarkdown = root.querySelector(".rendered-markdown");
  const imageOnlyView = root.querySelector(".image-only-view");
  const imageOnlyImg = root.querySelector(".image-only-img");

  const zButtons = {
    stepFront: root.querySelector('[data-action="step-front"]'),
    stepBack: root.querySelector('[data-action="step-back"]'),
    front: root.querySelector('[data-action="bring-front"]'),
    back: root.querySelector('[data-action="send-back"]'),
  };

  const app = {
    board: clone(normalizeBoard(data?.board)),
    viewMode: "edit",
    history: [],
    future: [],
    lastSyncedSerialized: "",
    activeNoteId: null,
    selectedNoteId: null,
    editorMode: "edit",
    editorNoteType: "markdown",
    pdfImageData: data?.pdfImageData && typeof data.pdfImageData === "object" ? data.pdfImageData : {},

    noteById(id) {
      return this.board.notes.find(note => note.id === id);
    },

    snapshot() {
      this.history.push(clone(this.board));
      if (this.history.length > 70) this.history.shift();
      this.future = [];
    },

    sync() {
      const payload = clone(this.board);
      this.lastSyncedSerialized = JSON.stringify(payload);
      setStateValue("board", payload);
    },

    normalizeZ() {
      const ordered = [...this.board.notes].sort((a, b) => (Number(a.z) - Number(b.z)) || a.id.localeCompare(b.id));
      ordered.forEach((note, index) => { note.z = index; });
    },

    orderedNotes() {
      return [...this.board.notes].sort((a, b) => (Number(a.z) - Number(b.z)) || a.id.localeCompare(b.id));
    },

    spatiallyOrderedNotes() {
      const source = [...this.board.notes].sort((a, b) =>
        (Number(a.y || 0) - Number(b.y || 0)) ||
        (Number(a.x || 0) - Number(b.x || 0)) ||
        String(a.id).localeCompare(String(b.id))
      );
      const rows = [];
      const rowTolerance = 90;
      for (const note of source) {
        const y = Number(note.y || 0);
        let row = rows.find(item => Math.abs(y - item.anchorY) <= rowTolerance);
        if (!row) {
          row = {anchorY: y, notes: []};
          rows.push(row);
        }
        row.notes.push(note);
        row.anchorY = row.notes.reduce((sum, item) => sum + Number(item.y || 0), 0) / row.notes.length;
      }
      rows.sort((a, b) => a.anchorY - b.anchorY);
      for (const row of rows) {
        row.notes.sort((a, b) =>
          (Number(a.x || 0) - Number(b.x || 0)) ||
          (Number(a.y || 0) - Number(b.y || 0)) ||
          String(a.id).localeCompare(String(b.id))
        );
      }
      return rows.flatMap(row => row.notes);
    },

    selectNote(noteId) {
      if (this.viewMode !== "edit") return;
      this.selectedNoteId = noteId && this.noteById(noteId) ? noteId : null;
      noteLayer.querySelectorAll(".sticky-note").forEach(element => {
        element.classList.toggle("selected-note", element.dataset.noteId === this.selectedNoteId);
      });
      this.refreshZControls();
    },

    refreshZControls() {
      const note = this.selectedNoteId ? this.noteById(this.selectedNoteId) : null;
      const disabled = !note || this.viewMode !== "edit";
      Object.values(zButtons).forEach(button => { button.disabled = disabled; });
      if (!note) {
        selectedSummary.textContent = "付箋を選択してください";
        selectedSummary.classList.remove("has-selection");
        return;
      }
      const firstLine = (note.title || "無題").split("\n")[0];
      selectedSummary.textContent = `${noteTypeBadge(note.type)} / ${firstLine} / Z:${note.z}`;
      selectedSummary.classList.add("has-selection");
    },

    moveZ(delta) {
      if (this.viewMode !== "edit" || !this.selectedNoteId) return;
      const ordered = this.orderedNotes();
      const index = ordered.findIndex(note => note.id === this.selectedNoteId);
      if (index < 0) return;
      const nextIndex = Math.max(0, Math.min(ordered.length - 1, index + delta));
      if (nextIndex === index) return;
      this.snapshot();
      const other = ordered[nextIndex];
      const selected = ordered[index];
      const oldZ = selected.z;
      selected.z = other.z;
      other.z = oldZ;
      this.normalizeZ();
      this.render();
      this.sync();
    },

    moveZExtreme(front) {
      if (this.viewMode !== "edit" || !this.selectedNoteId) return;
      const selected = this.noteById(this.selectedNoteId);
      if (!selected) return;
      const ordered = this.orderedNotes().filter(note => note.id !== selected.id);
      const currentIndex = this.orderedNotes().findIndex(note => note.id === selected.id);
      const targetIndex = front ? this.board.notes.length - 1 : 0;
      if (currentIndex === targetIndex) return;
      this.snapshot();
      if (front) ordered.push(selected); else ordered.unshift(selected);
      ordered.forEach((note, index) => { note.z = index; });
      this.render();
      this.sync();
    },

    noteEstimatedHeight(note) {
      const titleLines = Math.max(1, normalizeText(note.title).split("\n").length);
      const textLines = Math.max(1, normalizeText(note.text).split("\n").length);
      const base = 78 + Math.min(5, titleLines) * 18 + Math.min(8, textLines) * 19;
      return Math.max(note.type === "image" ? IMAGE_ESTIMATED_H : NOTE_ESTIMATED_H, base + (note.type === "image" ? 120 : 0));
    },

    resizeCanvas() {
      let maxX = 2200;
      let maxY = 1450;
      for (const note of this.board.notes) {
        maxX = Math.max(maxX, Number(note.x || 0) + Number(note.w || NOTE_W) + 260);
        maxY = Math.max(maxY, Number(note.y || 0) + this.noteEstimatedHeight(note) + 260);
      }
      canvas.style.width = `${Math.ceil(maxX)}px`;
      canvas.style.height = `${Math.ceil(maxY)}px`;
      requestAnimationFrame(updateHorizontalScrollSlider);
    },

    renderTitle() {
      const title = this.board.title || "";
      if (document.activeElement !== sessionTitleInput) sessionTitleInput.value = title;
      sessionTitleDisplay.textContent = title || "KJ Session";
    },

    renderStats() {
      const counts = {markdown: 0, code: 0, mermaid: 0, image: 0};
      for (const note of this.board.notes) counts[note.type] = (counts[note.type] || 0) + 1;
      stats.textContent = `付箋 ${this.board.notes.length} / MD ${counts.markdown || 0} / Code ${counts.code || 0} / Mermaid ${counts.mermaid || 0} / Image ${counts.image || 0}`;
    },

    renderNotes() {
      noteLayer.innerHTML = "";

      for (const note of this.orderedNotes()) {
        const el = document.createElement("article");
        el.className = "sticky-note";
        if (this.viewMode === "edit" && note.id === this.selectedNoteId) el.classList.add("selected-note");
        el.dataset.noteId = note.id;
        el.dataset.noteType = note.type;
        el.style.left = `${Number(note.x || 0)}px`;
        el.style.top = `${Number(note.y || 0)}px`;
        el.style.width = `${Number(note.w || NOTE_W)}px`;
        el.style.background = note.color;
        el.style.zIndex = String(10 + Number(note.z || 0));

        const handle = document.createElement("div");
        handle.className = "note-handle";
        const dragLabel = document.createElement("span");
        dragLabel.textContent = "⋮⋮ drag";
        const del = document.createElement("button");
        del.className = "note-delete";
        del.type = "button";
        del.textContent = "×";
        del.title = "付箋を削除";
        del.addEventListener("pointerdown", event => event.stopPropagation());
        del.addEventListener("dblclick", event => { event.preventDefault(); event.stopPropagation(); });
        del.addEventListener("click", event => { event.preventDefault(); event.stopPropagation(); this.deleteNote(note.id); });
        handle.append(dragLabel, del);
        el.appendChild(handle);

        const titleBar = document.createElement("div");
        titleBar.className = "note-title";
        const titleText = document.createElement("div");
        titleText.className = "note-title-text";
        titleText.textContent = note.title || "無題";
        const badge = document.createElement("span");
        badge.className = "note-type-badge";
        badge.textContent = noteTypeBadge(note.type);
        titleBar.append(titleText, badge);
        el.appendChild(titleBar);

        const body = document.createElement("div");
        body.className = "note-body";
        body.textContent = note.text || "";
        el.appendChild(body);

        if (note.type === "image") {
          const thumbWrap = document.createElement("div");
          thumbWrap.className = "note-thumbnail-wrap";
          if (note.imageUrl) {
            const img = document.createElement("img");
            img.className = "note-thumbnail";
            img.src = note.imageUrl;
            img.alt = note.title || "付箋画像";
            img.loading = "lazy";
            img.addEventListener("error", () => {
              img.remove();
              const empty = document.createElement("div");
              empty.className = "note-thumbnail-empty";
              empty.textContent = "画像を読み込めませんでした";
              thumbWrap.appendChild(empty);
            }, {once: true});
            thumbWrap.appendChild(img);
          } else {
            const empty = document.createElement("div");
            empty.className = "note-thumbnail-empty";
            empty.textContent = "画像 URL 未設定";
            thumbWrap.appendChild(empty);
          }
          el.appendChild(thumbWrap);
        }

        el.addEventListener("click", event => {
          if (event.target.closest(".note-delete")) return;
          if (this.viewMode === "edit") {
            event.stopPropagation();
            this.selectNote(note.id);
          }
        });

        el.addEventListener("dblclick", event => {
          if (event.target.closest(".note-delete")) return;
          event.preventDefault();
          event.stopPropagation();
          if (this.viewMode === "edit") this.openEditorModal(note.id);
          else this.openViewerModal(note.id);
        });

        handle.addEventListener("pointerdown", event => {
          if (event.target.closest(".note-delete") || this.viewMode !== "edit") return;
          event.preventDefault();
          event.stopPropagation();
          this.selectNote(note.id);
          this.snapshot();

          const startX = event.clientX;
          const startY = event.clientY;
          const originalX = Number(note.x || 0);
          const originalY = Number(note.y || 0);
          handle.setPointerCapture(event.pointerId);

          const move = moveEvent => {
            const dx = moveEvent.clientX - startX;
            const dy = moveEvent.clientY - startY;
            note.x = Math.max(4, originalX + dx);
            note.y = Math.max(96, originalY + dy);
            el.style.left = `${note.x}px`;
            el.style.top = `${note.y}px`;
          };

          const up = upEvent => {
            try { handle.releasePointerCapture(upEvent.pointerId); } catch (_) {}
            handle.removeEventListener("pointermove", move);
            handle.removeEventListener("pointerup", up);
            handle.removeEventListener("pointercancel", up);
            note.x = Math.round(note.x);
            note.y = Math.round(note.y);
            this.resizeCanvas();
            this.sync();
          };

          handle.addEventListener("pointermove", move);
          handle.addEventListener("pointerup", up);
          handle.addEventListener("pointercancel", up);
        });

        noteLayer.appendChild(el);
      }
    },

    render() {
      this.normalizeZ();
      this.resizeCanvas();
      this.renderTitle();
      this.renderNotes();
      this.renderStats();
      this.refreshZControls();
    },

    openCreateModal() {
      if (this.viewMode !== "edit") return;
      const requestedType = String(typeInput.value || "markdown");
      const type = ["markdown", "code", "mermaid", "image"].includes(requestedType) ? requestedType : "markdown";
      this.activeNoteId = null;
      this.editorMode = "create";
      this.editorNoteType = type;
      modalHeading.textContent = `${noteTypeLabel(type)}付箋`;
      editTitle.value = normalizeText(titleInput.value).trim();
      editColor.value = colorInput.value || "#FFF2A8";
      editText.value = normalizeText(textInput.value).trim();
      editMarkdown.value = "";
      editLanguage.value = "python";
      editImage.value = "";
      this.updateEditorTypeState();
      editorModal.classList.add("open");
      editorModal.setAttribute("aria-hidden", "false");
      requestAnimationFrame(() => editTitle.focus());
    },

    deleteNote(noteId) {
      if (this.viewMode !== "edit") return;
      const note = this.noteById(noteId);
      if (!note) return;
      this.snapshot();
      this.board.notes = this.board.notes.filter(item => item.id !== noteId);
      if (this.activeNoteId === noteId) this.closeEditorModal();
      if (this.selectedNoteId === noteId) this.selectedNoteId = null;
      this.normalizeZ();
      this.render();
      this.sync();
    },

    updateEditorTypeState() {
      const isImage = this.editorNoteType === "image";
      const isCode = this.editorNoteType === "code";
      const isMermaid = this.editorNoteType === "mermaid";
      editMarkdownField.hidden = isImage;
      editCodeLanguageField.hidden = !isCode;
      editImageField.hidden = !isImage;
      imagePreview.hidden = !isImage;

      if (!isImage) {
        editRichLabel.textContent = isCode ? "コード" : (isMermaid ? "Mermaid" : "Markdown");
        editMarkdown.placeholder = isCode ? "コードを入力" : (isMermaid ? "graph TD\n  A --> B" : "# Markdown");
      }

      if (isImage) this.updateImagePreview();
      else {
        imagePreview.classList.remove("has-image");
        imagePreviewImg.removeAttribute("src");
      }
    },

    updateImagePreview() {
      const url = editImage.value.trim();
      imagePreview.classList.remove("has-image");
      imagePreviewImg.removeAttribute("src");
      if (url) imagePreviewImg.src = url;
    },

    openEditorModal(noteId) {
      const note = this.noteById(noteId);
      if (!note || this.viewMode !== "edit") return;
      this.activeNoteId = noteId;
      this.editorMode = "edit";
      this.editorNoteType = ["markdown", "code", "mermaid", "image"].includes(note.type) ? note.type : "markdown";
      this.selectedNoteId = noteId;
      modalHeading.textContent = note.title.split("\n")[0] || `${noteTypeLabel(this.editorNoteType)}付箋`;
      editTitle.value = note.title || "";
      editColor.value = note.color || "#FFF2A8";
      editText.value = note.text || "";
      editMarkdown.value = this.editorNoteType === "markdown" ? (note.markdownSource || note.inline || "") : (note.inline || "");
      editLanguage.value = note.language || "python";
      editImage.value = note.imageUrl || "";
      this.updateEditorTypeState();
      editorModal.classList.add("open");
      editorModal.setAttribute("aria-hidden", "false");
      this.refreshZControls();
    },

    closeEditorModal() {
      this.activeNoteId = null;
      this.editorMode = "edit";
      editorModal.classList.remove("open");
      editorModal.setAttribute("aria-hidden", "true");
      imagePreview.classList.remove("has-image");
      imagePreviewImg.removeAttribute("src");
    },

    async renderDisplayPreview(note, host) {
      host.classList.toggle("code-note-preview", note.type === "code");
      host.innerHTML = `<div class="loading-preview">プレビューを生成しています…</div>`;
      try {
        const modules = await loadRenderModules();

        if (note.type === "code") {
          const code = note.inline || "";
          let highlighted;
          try {
            highlighted = modules.hljs.highlight(code, {language: note.language || "plaintext", ignoreIllegals: true}).value;
          } catch (_) {
            highlighted = escapeHtml(code);
          }
          host.innerHTML = `<pre><code class="hljs language-${escapeHtml(note.language || "plaintext")}">${highlighted}</code></pre>`;
          return;
        }

        if (note.type === "markdown") {
          host.innerHTML = `<div class="markdown-preview">${modules.marked.parse(note.markdownSource || note.inline || "")}</div>`;
          return;
        }

        if (note.type === "mermaid") {
          const id = `mermaid_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
          const rendered = await modules.mermaid.render(id, note.inline || "graph TD\n  A[未設定] --> B[Mermaid]");
          host.innerHTML = `<div class="mermaid-host">${rendered.svg}</div>`;
          return;
        }

        host.innerHTML = `<div class="preview-error">表示できない付箋タイプです。</div>`;
      } catch (err) {
        host.innerHTML = `<div class="preview-error">プレビュー生成に失敗しました。\n${escapeHtml(err?.message || String(err))}</div>`;
      }
    },

    async openViewerModal(noteId) {
      const note = this.noteById(noteId);
      if (!note || this.viewMode !== "view") return;
      const isImage = note.type === "image";
      viewerModal.classList.toggle("image-mode", isImage);
      viewerHeading.textContent = note.title || `${noteTypeLabel(note.type)}付箋`;
      renderedMarkdown.hidden = isImage;
      imageOnlyView.hidden = !isImage;

      if (isImage) {
        renderedMarkdown.innerHTML = "";
        if (note.imageUrl) {
          imageOnlyImg.src = note.imageUrl;
          imageOnlyImg.alt = note.title || "付箋画像";
        } else {
          imageOnlyImg.removeAttribute("src");
          imageOnlyImg.alt = "画像 URL 未設定";
        }
        viewerModal.classList.add("open");
        viewerModal.setAttribute("aria-hidden", "false");
        return;
      }

      imageOnlyImg.removeAttribute("src");
      viewerModal.classList.add("open");
      viewerModal.setAttribute("aria-hidden", "false");
      await this.renderDisplayPreview(note, renderedMarkdown);
    },

    closeViewerModal() {
      viewerModal.classList.remove("open", "image-mode");
      viewerModal.setAttribute("aria-hidden", "true");
      renderedMarkdown.innerHTML = "";
      renderedMarkdown.classList.remove("code-note-preview");
      imageOnlyImg.removeAttribute("src");
    },

    saveActiveNote() {
      if (this.viewMode !== "edit") return;
      const requestedType = String(this.editorNoteType || "markdown");
      const type = ["markdown", "code", "mermaid", "image"].includes(requestedType) ? requestedType : "markdown";
      const title = normalizeText(editTitle.value).trim();
      const text = normalizeText(editText.value).trim();
      const richSource = type === "image" ? "" : normalizeText(editMarkdown.value);
      const markdownSource = type === "markdown" ? richSource : "";
      const inline = type === "markdown" ? richSource : (["code", "mermaid"].includes(type) ? richSource : "");
      const language = type === "code" ? (editLanguage.value || "plaintext") : (type === "mermaid" ? "mermaid" : "");
      const imageUrl = type === "image" ? editImage.value.trim() : "";
      const color = editColor.value || "#FFF2A8";

      if (this.editorMode === "create") {
        if (!title && !text && !richSource && !imageUrl) {
          editTitle.focus();
          return;
        }
        this.snapshot();
        const x = Math.max(35, viewport.scrollLeft + 75 + Math.random() * 80);
        const y = Math.max(120, viewport.scrollTop + 120 + Math.random() * 80);
        const note = {
          id: uid("note"), title, text, markdownSource, inline, language, type, imageUrl, color,
          x: Math.round(x), y: Math.round(y), w: NOTE_W, z: this.board.notes.length,
        };
        this.board.notes.push(note);
        this.selectedNoteId = note.id;
        titleInput.value = "";
        textInput.value = "";
        this.closeEditorModal();
        this.render();
        this.sync();
        return;
      }

      if (!this.activeNoteId) return;
      const note = this.noteById(this.activeNoteId);
      if (!note) return;
      this.snapshot();
      note.title = title;
      note.color = color;
      note.text = text;
      note.type = type;
      note.markdownSource = markdownSource;
      note.inline = inline;
      note.language = language;
      note.imageUrl = imageUrl;
      this.closeEditorModal();
      this.render();
      this.sync();
    },

    setViewMode(mode) {
      this.viewMode = mode === "view" ? "view" : "edit";
      root.classList.toggle("view-mode", this.viewMode === "view");
      root.classList.toggle("edit-mode", this.viewMode === "edit");
      root.querySelectorAll(".view-btn").forEach(button => button.classList.toggle("active", button.dataset.view === this.viewMode));
      this.closeEditorModal();
      this.closeViewerModal();
      if (this.viewMode === "view") this.selectedNoteId = null;
      this.render();
    },

    undo() {
      if (this.viewMode !== "edit" || !this.history.length) return;
      this.future.push(clone(this.board));
      this.board = this.history.pop();
      this.closeEditorModal();
      if (this.selectedNoteId && !this.noteById(this.selectedNoteId)) this.selectedNoteId = null;
      this.render();
      this.sync();
    },

    redo() {
      if (this.viewMode !== "edit" || !this.future.length) return;
      this.history.push(clone(this.board));
      this.board = this.future.pop();
      this.closeEditorModal();
      if (this.selectedNoteId && !this.noteById(this.selectedNoteId)) this.selectedNoteId = null;
      this.render();
      this.sync();
    },

    reset() {
      if (this.viewMode !== "edit") return;
      if (!window.confirm("ボード上の付箋をすべて削除しますか？")) return;
      this.snapshot();
      this.board = {title: this.board.title || "", notes: []};
      this.selectedNoteId = null;
      this.closeEditorModal();
      this.render();
      this.sync();
    },

    buildPdfExportStyle() {
      return `
        .kj-pdf-export-root { position: fixed; left: -12000px; top: 0; width: 210mm; z-index: 2147483000; pointer-events: none; background: #fff; color: #202124; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", sans-serif; }
        .kj-pdf-export-root * { box-sizing: border-box; }
        .kj-pdf-page { width: 210mm; min-height: 297mm; padding: 15mm 16mm 14mm; background: #fff; color: #202124; page-break-after: always; break-after: page; }
        .kj-pdf-page:last-child { page-break-after: auto; break-after: auto; }
        .kj-pdf-index-page { page-break-after: always; break-after: page; }
        .kj-pdf-kicker { color: #6b7280; font-size: 10px; font-weight: 900; letter-spacing: .15em; }
        .kj-pdf-board-title { margin: 5px 0 4px; font-size: 26px; line-height: 1.25; font-weight: 900; overflow-wrap: anywhere; }
        .kj-pdf-subtitle { margin: 0 0 18px; color: #6b7280; font-size: 13px; }
        .kj-pdf-index-list { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }
        .kj-pdf-index-item { display: grid; grid-template-columns: 34px 54px minmax(0, 1fr); gap: 9px; align-items: start; padding: 9px 10px; border: 1px solid #d8dde5; border-radius: 8px; break-inside: avoid; page-break-inside: avoid; background: #fff; }
        .kj-pdf-index-number { display: grid; place-items: center; width: 30px; height: 30px; border-radius: 50%; background: #f0f2f5; font-size: 11px; font-weight: 900; }
        .kj-pdf-type { display: inline-grid; place-items: center; min-width: 46px; min-height: 24px; padding: 3px 6px; border: 1px solid #cbd1da; border-radius: 999px; color: #4b5563; font-size: 9px; font-weight: 900; letter-spacing: .04em; }
        .kj-pdf-index-copy { min-width: 0; }
        .kj-pdf-index-title { margin: 0 0 3px; font-size: 14px; line-height: 1.35; font-weight: 850; white-space: pre-wrap; overflow-wrap: anywhere; }
        .kj-pdf-index-text { margin: 0; color: #4b5563; font-size: 11px; line-height: 1.5; white-space: pre-wrap; overflow-wrap: anywhere; }
        .kj-pdf-note-header { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; padding-bottom: 10px; margin-bottom: 14px; border-bottom: 1px solid #d8dde5; }
        .kj-pdf-note-heading { margin: 4px 0 0; font-size: 22px; line-height: 1.3; font-weight: 900; white-space: pre-wrap; overflow-wrap: anywhere; }
        .kj-pdf-note-order { color: #6b7280; font-size: 11px; font-weight: 800; white-space: nowrap; }
        .kj-pdf-note-content { min-height: 232mm; padding: 14px 16px; border: 1px solid #d8dde5; border-radius: 10px; background: #f8f9fb; color: #202124; font-size: 13px; line-height: 1.65; overflow-wrap: anywhere; }
        .kj-pdf-note-content h1, .kj-pdf-note-content h2, .kj-pdf-note-content h3, .kj-pdf-note-content h4, .kj-pdf-note-content h5, .kj-pdf-note-content h6 { line-height: 1.25; margin: 1em 0 .5em; }
        .kj-pdf-note-content h1 { font-size: 28px; } .kj-pdf-note-content h2 { font-size: 22px; } .kj-pdf-note-content h3 { font-size: 18px; }
        .kj-pdf-note-content table { width: 100%; border-collapse: collapse; margin: 12px 0; }
        .kj-pdf-note-content th, .kj-pdf-note-content td { border: 1px solid #cbd1da; padding: 6px 8px; text-align: left; vertical-align: top; }
        .kj-pdf-note-content th { background: #eef1f5; font-weight: 800; }
        .kj-pdf-note-content blockquote { margin: 10px 0; padding: 6px 10px; border-left: 4px solid #7a8190; background: #eef1f5; color: #4b5563; }
        .kj-pdf-note-content pre { overflow: visible; white-space: pre-wrap; overflow-wrap: anywhere; padding: 12px; border-radius: 8px; }
        .kj-pdf-note-content code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
        .kj-pdf-note-content.code-note-preview { min-height: 232mm; background: #23242b; color: #e5e7eb; border-color: #30323b; }
        .kj-pdf-note-content.code-note-preview pre { margin: 0; background: #23242b !important; color: #e5e7eb !important; }
        .kj-pdf-note-content.code-note-preview pre code.hljs { display: block; background: transparent !important; color: #e5e7eb !important; }
        .kj-pdf-note-content .hljs-keyword, .kj-pdf-note-content .hljs-selector-tag, .kj-pdf-note-content .hljs-literal, .kj-pdf-note-content .hljs-section, .kj-pdf-note-content .hljs-link { color: #c084fc; }
        .kj-pdf-note-content .hljs-string, .kj-pdf-note-content .hljs-title, .kj-pdf-note-content .hljs-name, .kj-pdf-note-content .hljs-type, .kj-pdf-note-content .hljs-attribute, .kj-pdf-note-content .hljs-symbol, .kj-pdf-note-content .hljs-bullet, .kj-pdf-note-content .hljs-addition { color: #86efac; }
        .kj-pdf-note-content .hljs-number, .kj-pdf-note-content .hljs-meta, .kj-pdf-note-content .hljs-built_in, .kj-pdf-note-content .hljs-builtin-name, .kj-pdf-note-content .hljs-params { color: #fbbf24; }
        .kj-pdf-note-content .hljs-comment, .kj-pdf-note-content .hljs-quote, .kj-pdf-note-content .hljs-deletion { color: #94a3b8; font-style: italic; }
        .kj-pdf-note-content .hljs-variable, .kj-pdf-note-content .hljs-template-variable, .kj-pdf-note-content .hljs-selector-id, .kj-pdf-note-content .hljs-selector-class { color: #7dd3fc; }
        .kj-pdf-note-content .hljs-regexp, .kj-pdf-note-content .hljs-template-tag { color: #fda4af; }
        /* Media pages use the remaining A4 height as a fixed frame. */
        .kj-pdf-media-page { height: 297mm; min-height: 297mm; max-height: 297mm; display: flex; flex-direction: column; overflow: hidden; }
        .kj-pdf-media-page .kj-pdf-note-header { flex: 0 0 auto; }
        .kj-pdf-media-page .kj-pdf-note-content,
        .kj-pdf-media-page .kj-pdf-image-content { flex: 1 1 auto; min-height: 0; height: auto; max-height: none; overflow: hidden; }
        .kj-pdf-note-content.mermaid-pdf-content { display: flex; align-items: center; justify-content: center; padding: 8mm; }
        .kj-pdf-note-content.mermaid-pdf-content .mermaid-host { width: 100%; height: 100%; min-width: 0; min-height: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        .kj-pdf-note-content.mermaid-pdf-content .mermaid-host svg { display: block !important; max-width: none !important; max-height: none !important; overflow: visible !important; }
        /* html2canvas captures this already-rasterized canvas, not a live SVG with an unstable viewport. */
        .kj-pdf-mermaid-canvas { display: block; flex: none; max-width: 100%; max-height: 100%; margin: auto; }
        .kj-pdf-image-content { display: flex; align-items: center; justify-content: center; padding: 8mm; border: 1px solid #d8dde5; border-radius: 10px; background: #f8f9fb; overflow: hidden; }
        /* Intrinsic size by default; only shrink when either dimension exceeds the printable frame. */
        .kj-pdf-image-content img { display: block; flex: none; width: auto; height: auto; max-width: 100%; max-height: 100%; margin: auto; object-fit: contain; object-position: center center; border-radius: 7px; }
        .kj-pdf-image-missing { margin: auto; color: #6b7280; font-size: 13px; text-align: center; }
      `;
    },

    async buildPdfExportDocument(notes) {
      const exportRoot = document.createElement("div");
      exportRoot.className = "kj-pdf-export-root";
      const style = document.createElement("style");
      style.textContent = this.buildPdfExportStyle();
      exportRoot.appendChild(style);

      const indexPage = document.createElement("section");
      indexPage.className = "kj-pdf-page kj-pdf-index-page";
      const kicker = document.createElement("div");
      kicker.className = "kj-pdf-kicker";
      kicker.textContent = "KJ SESSION BOARD";
      const boardTitle = document.createElement("h1");
      boardTitle.className = "kj-pdf-board-title";
      boardTitle.textContent = this.board.title || "KJ Session";
      const subtitle = document.createElement("p");
      subtitle.className = "kj-pdf-subtitle";
      subtitle.textContent = `付箋目次 - ${notes.length}件 - 上→下 / 同じ段は左→右`;
      const list = document.createElement("ol");
      list.className = "kj-pdf-index-list";
      notes.forEach((note, index) => {
        const item = document.createElement("li");
        item.className = "kj-pdf-index-item";
        const number = document.createElement("span");
        number.className = "kj-pdf-index-number";
        number.textContent = String(index + 1).padStart(2, "0");
        const badge = document.createElement("span");
        badge.className = "kj-pdf-type";
        badge.textContent = noteTypeBadge(note.type);
        const copy = document.createElement("div");
        copy.className = "kj-pdf-index-copy";
        const title = document.createElement("div");
        title.className = "kj-pdf-index-title";
        title.textContent = note.title || "無題";
        const text = document.createElement("p");
        text.className = "kj-pdf-index-text";
        text.textContent = note.text || "";
        copy.append(title, text);
        item.append(number, badge, copy);
        list.appendChild(item);
      });
      indexPage.append(kicker, boardTitle, subtitle, list);
      exportRoot.appendChild(indexPage);

      for (let index = 0; index < notes.length; index += 1) {
        const note = notes[index];
        const page = document.createElement("section");
        page.className = "kj-pdf-page kj-pdf-note-page";
        if (["mermaid", "image"].includes(note.type)) page.classList.add("kj-pdf-media-page");
        const header = document.createElement("header");
        header.className = "kj-pdf-note-header";
        const headingWrap = document.createElement("div");
        const noteKicker = document.createElement("div");
        noteKicker.className = "kj-pdf-kicker";
        noteKicker.textContent = `STICKY NOTE / ${noteTypeLabel(note.type).toUpperCase()}`;
        const heading = document.createElement("h2");
        heading.className = "kj-pdf-note-heading";
        heading.textContent = note.title || `${noteTypeLabel(note.type)}付箋`;
        headingWrap.append(noteKicker, heading);
        const order = document.createElement("div");
        order.className = "kj-pdf-note-order";
        order.textContent = `${String(index + 1).padStart(2, "0")} / ${String(notes.length).padStart(2, "0")}`;
        header.append(headingWrap, order);
        page.appendChild(header);

        if (note.type === "image") {
          const imageHost = document.createElement("div");
          imageHost.className = "kj-pdf-image-content";
          if (note.imageUrl) {
            const embeddedSource = this.pdfImageData?.[note.imageUrl] || "";
            const img = document.createElement("img");
            img.alt = note.title || "付箋画像";
            // Prefer a server-resolved data URL. This is essential for html2canvas:
            // a normal browser <img> may display a cross-origin URL while canvas
            // export still has to omit it because CORS read access was denied.
            if (embeddedSource) {
              img.src = embeddedSource;
            } else {
              img.crossOrigin = "anonymous";
              img.src = note.imageUrl;
            }
            img.addEventListener("error", () => {
              imageHost.replaceChildren();
              const missing = document.createElement("div");
              missing.className = "kj-pdf-image-missing";
              missing.textContent = "画像を PDF 用に取得できませんでした。";
              imageHost.appendChild(missing);
            }, {once: true});
            imageHost.appendChild(img);
          } else {
            const missing = document.createElement("div");
            missing.className = "kj-pdf-image-missing";
            missing.textContent = "画像 URL 未設定";
            imageHost.appendChild(missing);
          }
          page.appendChild(imageHost);
        } else {
          const content = document.createElement("div");
          content.className = "kj-pdf-note-content rendered-markdown";
          if (note.type === "mermaid") content.classList.add("mermaid-pdf-content");
          page.appendChild(content);
          await this.renderDisplayPreview(note, content);
          // SVG is kept at its original measured dimensions until the export
          // document is attached. preparePdfMedia() then rasterizes it to a
          // fitted canvas using the full SVG geometry, not CSS percentages.
        }
        exportRoot.appendChild(page);
      }
      return exportRoot;
    },

    async preparePdfMedia(exportRoot) {
      // The export DOM must be attached before measuring A4 media frames.
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));

      // 1. Preserve each image's intrinsic CSS-pixel size if it already fits.
      //    Otherwise shrink uniformly; do not enlarge smaller images.
      for (const frame of exportRoot.querySelectorAll(".kj-pdf-image-content")) {
        const img = frame.querySelector("img");
        if (!img) continue;
        await waitForImage(img);
        if (!img.naturalWidth || !img.naturalHeight) continue;
        const style = getComputedStyle(frame);
        const width = Math.max(1, frame.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight));
        const height = Math.max(1, frame.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom));
        const scale = Math.min(1, width / img.naturalWidth, height / img.naturalHeight);
        img.style.width = `${img.naturalWidth * scale}px`;
        img.style.height = `${img.naturalHeight * scale}px`;
        img.style.maxWidth = "100%";
        img.style.maxHeight = "100%";
      }

      // 2. Flatten each Mermaid diagram into a native Canvas at its *actual*
      //    geometry before html2canvas clones the A4 page. This avoids SVG
      //    clipping caused by inherited SVG width/height, foreignObject layout,
      //    and the browser's SVG-as-<img> viewport behavior.
      for (const host of exportRoot.querySelectorAll(".mermaid-pdf-content .mermaid-host")) {
        const svg = host.querySelector("svg");
        if (!svg) continue;
        try {
          await rasterizeMermaidForPdf(svg, host);
        } catch (error) {
          console.error("KJ PDF Mermaid rasterization failed", error);
          const placeholder = document.createElement("div");
          placeholder.className = "kj-pdf-image-missing";
          placeholder.textContent = `Mermaid の PDF 描画に失敗しました: ${error?.message || String(error)}`;
          host.replaceChildren(placeholder);
        }
      }
    },

    async exportPdf() {
      if (!this.board.notes.length) {
        window.alert("PDF に出力する付箋がありません。");
        return;
      }
      const originalLabel = pdfButton.textContent;
      pdfButton.disabled = true;
      pdfButton.textContent = "PDF…";
      let exportRoot = null;
      try {
        const {html2canvas, jsPDF} = await loadPdfModules();
        const notes = this.spatiallyOrderedNotes();
        exportRoot = await this.buildPdfExportDocument(notes);

        // Attach outside the component root. Streamlit Components v2 may render the
        // board in a shadow-root-like context; attaching the export DOM to body keeps
        // html2canvas cloning predictable. It remains off-screen for the user.
        document.body.appendChild(exportRoot);
        await this.preparePdfMedia(exportRoot);
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));

        const pdf = new jsPDF({unit: "mm", format: "a4", orientation: "portrait", compress: true});
        const pageWidthMm = 210;
        const pageHeightMm = 297;
        let hasPdfPage = false;
        const sourcePages = [...exportRoot.querySelectorAll(".kj-pdf-page")];

        for (let pageIndex = 0; pageIndex < sourcePages.length; pageIndex += 1) {
          const pageElement = sourcePages[pageIndex];
          const pageId = `kj_pdf_${Date.now()}_${pageIndex}_${Math.random().toString(36).slice(2, 7)}`;
          pageElement.dataset.pdfCaptureId = pageId;

          // Render one logical PDF page at a time. This avoids the browser's maximum
          // canvas-height limit, which caused multi-note exports to become blank.
          const canvas = await html2canvas(pageElement, {
            scale: 1.5,
            useCORS: true,
            allowTaint: false,
            backgroundColor: "#ffffff",
            logging: false,
            scrollX: 0,
            scrollY: 0,
            windowWidth: Math.max(document.documentElement.clientWidth, 1200),
            windowHeight: Math.max(document.documentElement.clientHeight, 1200),
            onclone: clonedDocument => {
              const clonedPage = clonedDocument.querySelector(`[data-pdf-capture-id="${pageId}"]`);
              if (!clonedPage) return;
              const clonedRoot = clonedPage.closest(".kj-pdf-export-root");
              if (clonedRoot) {
                clonedRoot.style.position = "absolute";
                clonedRoot.style.left = "0";
                clonedRoot.style.top = "0";
                clonedRoot.style.zIndex = "0";
                clonedRoot.style.pointerEvents = "none";
              }
            },
          });

          if (!canvas.width || !canvas.height) {
            throw new Error(`PDF ページ ${pageIndex + 1} の描画結果が空です。`);
          }

          // A long Markdown/code page can exceed A4. Split only that page's canvas
          // into A4-height slices, rather than creating one giant canvas for the whole PDF.
          const sliceHeightPx = Math.max(1, Math.floor(canvas.width * pageHeightMm / pageWidthMm));
          for (let offsetY = 0; offsetY < canvas.height; offsetY += sliceHeightPx) {
            const currentHeight = Math.min(sliceHeightPx, canvas.height - offsetY);
            const slice = document.createElement("canvas");
            slice.width = canvas.width;
            slice.height = currentHeight;
            const context = slice.getContext("2d", {alpha: false});
            if (!context) throw new Error("PDF ページ用 Canvas を作成できませんでした。");
            context.fillStyle = "#ffffff";
            context.fillRect(0, 0, slice.width, slice.height);
            context.drawImage(
              canvas,
              0, offsetY, canvas.width, currentHeight,
              0, 0, canvas.width, currentHeight
            );

            if (hasPdfPage) pdf.addPage("a4", "portrait");
            hasPdfPage = true;
            const imageHeightMm = currentHeight / canvas.width * pageWidthMm;
            const dataUrl = slice.toDataURL("image/jpeg", 0.94);
            pdf.addImage(dataUrl, "JPEG", 0, 0, pageWidthMm, imageHeightMm, undefined, "FAST");
          }
          delete pageElement.dataset.pdfCaptureId;
        }

        if (!hasPdfPage) throw new Error("PDF に追加できるページがありませんでした。");

        const safeTitle = (this.board.title || "kj-session-board")
          .replace(/[\\/:*?"<>|]+/g, "-")
          .replace(/\s+/g, " ")
          .trim() || "kj-session-board";
        pdf.save(`${safeTitle}-${this.timestampForFilename()}.pdf`);
      } catch (error) {
        window.alert(`PDF の生成に失敗しました。\n${error?.message || String(error)}`);
      } finally {
        exportRoot?.remove();
        pdfButton.disabled = false;
        pdfButton.textContent = originalLabel;
      }
    },

    timestampForFilename() {
      const d = new Date();
      const pad = n => String(n).padStart(2, "0");
      return `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
    },

    downloadJson() {
      const blob = new Blob([JSON.stringify(this.board, null, 2)], {type: "application/json;charset=utf-8"});
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `kj-session-board-${this.timestampForFilename()}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1200);
    },

    async importJson(file) {
      if (!file) return;
      try {
        const parsed = JSON.parse(await file.text());
        if (!parsed || typeof parsed !== "object" || !Array.isArray(parsed.notes)) {
          throw new Error("notes 配列を持つ KJ Session Board JSON ではありません。");
        }
        if (!window.confirm("現在のボードを読み込んだ内容で置き換えますか？")) return;
        this.snapshot();
        this.board = normalizeBoard(parsed);
        this.selectedNoteId = null;
        this.closeEditorModal();
        this.closeViewerModal();
        this.render();
        this.sync();
      } catch (error) {
        window.alert(`JSON の読み込みに失敗しました。\n${error?.message || String(error)}`);
      } finally {
        fileInput.value = "";
      }
    },
  };

  parentElement.__kjApp = app;

  function updateHorizontalScrollSlider() {
    const max = Math.max(0, viewport.scrollWidth - viewport.clientWidth);
    horizontalScrollSlider.max = String(Math.ceil(max));
    horizontalScrollSlider.value = String(Math.min(max, viewport.scrollLeft));
    horizontalScrollSlider.disabled = max <= 1;
  }

  root.querySelector('[data-action="add-note"]').addEventListener("click", () => app.openCreateModal());
  for (const input of [titleInput, textInput]) {
    input.addEventListener("keydown", event => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        app.openCreateModal();
      }
    });
  }

  const commitSessionTitle = () => {
    const next = normalizeText(sessionTitleInput.value).trim();
    if (next === (app.board.title || "")) return;
    app.snapshot();
    app.board.title = next;
    app.renderTitle();
    app.sync();
  };
  sessionTitleInput.addEventListener("blur", commitSessionTitle);
  sessionTitleInput.addEventListener("keydown", event => {
    if (event.key === "Enter") { event.preventDefault(); sessionTitleInput.blur(); }
  });

  root.querySelectorAll(".view-btn").forEach(button => button.addEventListener("click", () => app.setViewMode(button.dataset.view)));
  zButtons.stepFront.addEventListener("click", () => app.moveZ(1));
  zButtons.stepBack.addEventListener("click", () => app.moveZ(-1));
  zButtons.front.addEventListener("click", () => app.moveZExtreme(true));
  zButtons.back.addEventListener("click", () => app.moveZExtreme(false));
  root.querySelector('[data-action="undo"]').addEventListener("click", () => app.undo());
  root.querySelector('[data-action="redo"]').addEventListener("click", () => app.redo());
  root.querySelector('[data-action="reset"]').addEventListener("click", () => app.reset());
  root.querySelector('[data-action="export-json"]').addEventListener("click", () => app.downloadJson());
  root.querySelector('[data-action="import-json"]').addEventListener("click", () => { fileInput.value = ""; fileInput.click(); });
  fileInput.addEventListener("change", () => app.importJson(fileInput.files?.[0]));
  pdfButton.addEventListener("click", () => app.exportPdf());

  root.querySelector('[data-action="fullscreen"]').addEventListener("click", async () => {
    try {
      if (!document.fullscreenElement) await root.requestFullscreen();
      else await document.exitFullscreen();
    } catch (error) {
      window.alert(`全画面表示を開始できませんでした。\n${error?.message || String(error)}`);
    }
  });

  root.querySelectorAll('[data-action="close-editor-modal"]').forEach(element => element.addEventListener("click", () => app.closeEditorModal()));
  root.querySelectorAll('[data-action="close-viewer-modal"]').forEach(element => element.addEventListener("click", () => app.closeViewerModal()));
  saveNoteButton.addEventListener("click", () => app.saveActiveNote());
  editImage.addEventListener("input", () => app.updateImagePreview());
  imagePreviewImg.addEventListener("load", () => imagePreview.classList.add("has-image"));
  imagePreviewImg.addEventListener("error", () => imagePreview.classList.remove("has-image"));

  root.addEventListener("keydown", event => {
    if (event.key !== "Escape") return;
    if (editorModal.classList.contains("open")) app.closeEditorModal();
    if (viewerModal.classList.contains("open")) app.closeViewerModal();
  });

  canvas.addEventListener("click", event => {
    if (app.viewMode !== "edit") return;
    if (event.target === canvas || event.target === noteLayer) app.selectNote(null);
  });

  horizontalScrollSlider.addEventListener("input", () => { viewport.scrollLeft = Number(horizontalScrollSlider.value) || 0; });
  viewport.addEventListener("scroll", updateHorizontalScrollSlider, {passive: true});
  document.addEventListener("fullscreenchange", () => requestAnimationFrame(updateHorizontalScrollSlider));
  const resizeObserver = new ResizeObserver(() => updateHorizontalScrollSlider());
  resizeObserver.observe(viewport);

  app.setViewMode("edit");
  app.render();
  if (!data?.board || !Array.isArray(data.board.notes)) app.sync();

  return () => {
    resizeObserver.disconnect();
    delete parentElement.__kjApp;
  };
}
"""

KJ_BOARD_COMPONENT = st.components.v2.component(
    "kj_session_board",
    html=HTML,
    css=CSS,
    js=JS,
)


def get_component_board(key: str) -> dict[str, Any]:
    component_state = st.session_state.get(key, {})
    if isinstance(component_state, dict) and isinstance(component_state.get("board"), dict):
        return copy.deepcopy(component_state["board"])
    return copy.deepcopy(st.session_state.get("board_seed", EMPTY_BOARD))


if "board_seed" not in st.session_state:
    st.session_state.board_seed = copy.deepcopy(EMPTY_BOARD)

st.title("KJ Session Board")
st.caption(
    "上部操作パネルから Markdown / Code / Mermaid / Image 付箋を追加し、Z順を含めて整理できる "
    "KJ セッションボードです。"
)

with st.expander("操作ガイド", expanded=False):
    st.markdown(
        """
- **付箋の追加**: 上部パネルで `Markdown` / `Code` / `Mermaid` / `Image`、タイトル、内容・メモ、色を指定して **＋追加** を押すと専用ポップアップが開きます。ポップアップの **保存** で付箋を作成します。
- **Z順**: 編集モードで付箋をクリックして選択し、`前面へ / 背面へ / 最前面へ / 最背面へ` を操作できます。Z順は JSON と Undo / Redo に保持されます。
- **Markdown / Code / Mermaid 編集**: 編集モードで対象付箋をダブルクリックすると、旧版と同じソース編集ポップアップを開きます。Code は言語を選択できます。
- **Markdown / Code / Mermaid 表示**: 表示モードでダブルクリックすると、Markdown は marked、Code は highlight.js、Mermaid は Mermaid.js でレンダリングします。
- **Image 付箋**: 現行版の編集・サムネイル・表示モードの仕様を維持します。
- **JSON互換性**: 旧形式の `groups` / `edges` は読み込み時に破棄し、旧 `code` / `markdown` / `mermaid` の `inline` / `language` をそのまま引き継ぎます。
- **JSON保存 / JSON読込**: 現在のセッションタイトル、付箋、Markdown ソース、Z順を JSON として保存・復元できます。
- **PDF**: ボード上の付箋を上→下、同じ段では左→右の順に並べたタイトル＋内容・メモの目次を先頭に作成し、その後へ各付箋の表示モード相当ページを連結して保存します。
        """
    )

component_key = "kj_board_component"
current_board = get_component_board(component_key)
pdf_image_data = build_pdf_image_data(current_board)
result = KJ_BOARD_COMPONENT(
    data={"board": current_board, "pdfImageData": pdf_image_data},
    default={"board": current_board},
    key=component_key,
    on_board_change=lambda: None,
)

board = getattr(result, "board", current_board) or current_board
st.session_state.board_seed = copy.deepcopy(board)

notes = board.get("notes", []) if isinstance(board, dict) else []
markdown_count = sum(1 for note in notes if isinstance(note, dict) and note.get("type") == "markdown")
code_count = sum(1 for note in notes if isinstance(note, dict) and note.get("type") == "code")
mermaid_count = sum(1 for note in notes if isinstance(note, dict) and note.get("type") == "mermaid")
image_count = sum(1 for note in notes if isinstance(note, dict) and note.get("type") == "image")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("付箋", len(notes))
c2.metric("Markdown", markdown_count)
c3.metric("Code", code_count)
c4.metric("Mermaid", mermaid_count)
c5.metric("Image", image_count)


st.caption(
    "Markdown / Mermaid / シンタックスハイライトの表示はブラウザ側レンダリングです。"
    "閉域環境へ展開する場合は、各 JavaScript ライブラリをローカル配布へ切り替えてください。"
)
