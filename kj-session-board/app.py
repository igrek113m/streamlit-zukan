from __future__ import annotations

import copy
from typing import Any

import streamlit as st


st.set_page_config(
    page_title="KJ Session Board",
    page_icon="🗂️",
    layout="wide",
)

EMPTY_BOARD: dict[str, Any] = {
    "title": "",
    "notes": [],
    "groups": [],
    "edges": [],
}

HTML = r"""
<div class="kj-app edit-mode">
  <div class="board-header">
    <div class="board-brand">
      <span class="board-brand-mark">KJ</span>
      <div>
        <strong>KJ Session Board</strong>
        <span class="board-subtitle">発散・グループ化・関係付け</span>
      </div>
    </div>
    <div class="presentation-controls">
      <div class="view-switch" role="group" aria-label="表示モード切替">
        <button data-view="edit" class="view-btn active">✎ 編集モード</button>
        <button data-view="view" class="view-btn">▶ 表示モード</button>
      </div>
      <div class="file-controls" role="group" aria-label="ファイル入出力">
        <button data-action="export-json" title="ボードを JSON ファイルとしてダウンロード">JSON保存</button>
        <button data-action="import-json" title="JSON ファイルからボードを読み込む">JSON読込</button>
        <input class="json-file-input" type="file" accept="application/json,.json" hidden />
      </div>
      <button data-action="fullscreen" class="fullscreen-btn" title="ボードを全画面表示">⛶</button>
    </div>
  </div>

  <div class="edit-toolbar">
    <div class="toolbar-section note-creator">
      <input class="new-note-title" type="text" placeholder="付箋タイトル（任意）" />
      <textarea class="new-note-text" rows="2" placeholder="付箋に表示する内容…"></textarea>
      <label class="field-label compact-field">
        種類
        <select class="new-note-type">
          <option value="text">text</option>
          <option value="code">code</option>
          <option value="markdown">markdown</option>
          <option value="mermaid">mermaid</option>
          <option value="image">image</option>
        </select>
      </label>
      <label class="field-label compact-field">
        色
        <select class="new-note-color">
          <option value="#FFF2A8">イエロー</option>
          <option value="#DDF4D2">グリーン</option>
          <option value="#DCEEFF">ブルー</option>
          <option value="#F7DDF1">ピンク</option>
          <option value="#FFE0C2">オレンジ</option>
          <option value="#E9E0FF">パープル</option>
        </select>
      </label>
      <button class="primary-btn" data-action="add-note">＋ 付箋</button>
    </div>

    <div class="toolbar-row-secondary">
      <div class="toolbar-section mode-switch">
        <button data-mode="move" class="mode-btn active">✥ 移動</button>
        <button data-mode="group" class="mode-btn">▭ グループ化</button>
        <button data-mode="connect" class="mode-btn">↔ グループ接続</button>
      </div>

      <div class="toolbar-section connection-settings">
        <label class="field-label">
          接続線
          <select class="edge-direction">
            <option value="none">矢印なし</option>
            <option value="right" selected>右向き矢印</option>
            <option value="left">左向き矢印</option>
          </select>
        </label>
      </div>

      <div class="toolbar-section utilities">
        <button data-action="undo" title="Undo">↶</button>
        <button data-action="redo" title="Redo">↷</button>
        <button data-action="reset" class="danger-ghost">全消去</button>
      </div>
    </div>
  </div>

  <div class="hint-row">
    <span class="mode-hint"></span>
    <span class="stats"></span>
  </div>

  <div class="board-viewport">
    <div class="board-canvas">
      <div class="session-title-panel">
        <input class="session-title-input" type="text" maxlength="120"
               placeholder="セッションタイトルを入力…" aria-label="セッションタイトル" />
        <div class="session-title-display"></div>
      </div>
      <svg class="edge-layer" aria-label="関係線レイヤー"></svg>
      <div class="group-layer"></div>
      <div class="note-layer"></div>
      <div class="selection-rect"></div>
    </div>
  </div>

  <div class="note-modal modal-shell" aria-hidden="true">
    <div class="modal-backdrop" data-action="close-note-modal"></div>
    <section class="modal-panel" role="dialog" aria-modal="true" aria-label="付箋詳細">
      <header class="modal-header">
        <div>
          <div class="modal-kicker">STICKY NOTE</div>
          <h2 class="note-modal-title">付箋</h2>
        </div>
        <button class="modal-close" data-action="close-note-modal" title="閉じる">×</button>
      </header>
      <div class="note-modal-content"></div>
      <footer class="note-modal-footer"></footer>
    </section>
  </div>

  <div class="edge-modal modal-shell" aria-hidden="true">
    <div class="modal-backdrop" data-action="close-edge-modal"></div>
    <section class="modal-panel edge-modal-panel" role="dialog" aria-modal="true" aria-label="接続線編集">
      <header class="modal-header">
        <div>
          <div class="modal-kicker">RELATION</div>
          <h2>接続線</h2>
        </div>
        <button class="modal-close" data-action="close-edge-modal" title="閉じる">×</button>
      </header>
      <div class="edge-editor-form">
        <label class="editor-field">
          <span>関係名</span>
          <input class="edge-editor-label" type="text" />
        </label>
        <label class="editor-field">
          <span>矢印</span>
          <select class="edge-editor-direction">
            <option value="none">矢印なし</option>
            <option value="right">右向き矢印</option>
            <option value="left">左向き矢印</option>
          </select>
        </label>
      </div>
      <footer class="modal-actions">
        <button data-action="delete-edge" class="danger-ghost">削除</button>
        <span class="action-spacer"></span>
        <button data-action="close-edge-modal">キャンセル</button>
        <button data-action="save-edge" class="primary-btn">保存</button>
      </footer>
    </section>
  </div>
</div>
"""

CSS = r"""
:host {
  --canvas-w: 1900px;
  --canvas-h: 1200px;
  --toolbar-bg: color-mix(in srgb, var(--st-secondary-background-color) 88%, white);
  --border: color-mix(in srgb, var(--st-text-color) 18%, transparent);
  --muted: color-mix(in srgb, var(--st-text-color) 60%, transparent);
  --accent: var(--st-primary-color);
  display: block;
}

* { box-sizing: border-box; }

.kj-app {
  width: 100%;
  color: var(--st-text-color);
  font-family: var(--st-font);
}

button, input, textarea, select { font: inherit; }

button {
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: .48rem .7rem;
  background: var(--st-background-color);
  color: var(--st-text-color);
  cursor: pointer;
  white-space: nowrap;
}

button:hover { border-color: color-mix(in srgb, var(--accent) 65%, var(--border)); }
.primary-btn { background: var(--accent); border-color: var(--accent); color: white; font-weight: 700; }
.danger-ghost:hover { border-color: #bf3c3c; color: #bf3c3c; }

.board-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: .72rem .85rem;
  border: 1px solid var(--border);
  border-radius: 14px 14px 0 0;
  background: var(--st-background-color);
}

.board-brand { display: flex; align-items: center; gap: .65rem; }
.board-brand > div { display: flex; flex-direction: column; gap: .05rem; }
.board-brand-mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--accent);
  color: white;
  font-weight: 900;
  letter-spacing: -.04em;
}
.board-subtitle { color: var(--muted); font-size: 11px; }
.presentation-controls { display: flex; align-items: center; gap: .45rem; flex-wrap: wrap; justify-content: flex-end; }
.file-controls { display: flex; align-items: center; gap: .3rem; }
.file-controls button { padding: .42rem .58rem; font-size: 12px; }
.view-switch { display: flex; padding: 3px; gap: 2px; border-radius: 11px; background: var(--st-secondary-background-color); }
.view-btn { border: none; background: transparent; padding: .42rem .68rem; }
.view-btn.active { background: var(--st-background-color); box-shadow: 0 1px 5px rgba(0,0,0,.12); font-weight: 750; }
.fullscreen-btn { width: 38px; height: 38px; padding: 0; font-size: 20px; }

.edit-toolbar {
  display: flex;
  flex-direction: column;
  gap: .6rem;
  padding: .7rem;
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
  background: var(--toolbar-bg);
}
.toolbar-section { display: flex; align-items: center; gap: .45rem; }
.note-creator { width: 100%; flex-wrap: wrap; }
.toolbar-row-secondary { display: flex; align-items: center; justify-content: space-between; gap: .7rem; flex-wrap: wrap; }
.mode-switch { flex: 0 1 auto; }
.connection-settings { flex: 0 1 auto; }
.utilities { margin-left: auto; }

.new-note-title,
.new-note-text,
select,
.editor-field input,
.editor-field textarea {
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: .5rem .65rem;
  background: var(--st-background-color);
  color: var(--st-text-color);
}
.new-note-title { min-width: 180px; flex: 0 1 230px; }
.new-note-text { min-width: 300px; flex: 1 1 420px; resize: vertical; min-height: 42px; max-height: 90px; }
.field-label { display: inline-flex; align-items: center; gap: .35rem; color: var(--muted); font-size: .84rem; }
.field-label select { color: var(--st-text-color); }
.compact-field select { min-width: 105px; }
.mode-btn.active { outline: 2px solid color-mix(in srgb, var(--accent) 45%, transparent); border-color: var(--accent); }

.hint-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: .34rem .8rem;
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
  background: color-mix(in srgb, var(--st-secondary-background-color) 55%, transparent);
  font-size: .82rem;
  color: var(--muted);
}

.board-viewport {
  height: 72vh;
  min-height: 570px;
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: 0 0 14px 14px;
  background:
    linear-gradient(to right, color-mix(in srgb, var(--st-text-color) 5%, transparent) 1px, transparent 1px),
    linear-gradient(to bottom, color-mix(in srgb, var(--st-text-color) 5%, transparent) 1px, transparent 1px),
    var(--st-background-color);
  background-size: 24px 24px;
}

.board-canvas {
  width: var(--canvas-w);
  height: var(--canvas-h);
  position: relative;
  overflow: hidden;
  user-select: none;
}

.session-title-panel {
  position: absolute;
  top: 22px;
  left: 28px;
  z-index: 6;
  max-width: min(900px, calc(100% - 56px));
  pointer-events: none;
}
.session-title-input {
  width: min(720px, 62vw);
  max-width: calc(100vw - 120px);
  padding: .5rem .7rem;
  border: 1px dashed color-mix(in srgb, var(--accent) 48%, var(--border));
  border-radius: 9px;
  background: color-mix(in srgb, var(--st-background-color) 88%, transparent);
  color: var(--st-text-color);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -.015em;
  pointer-events: auto;
  outline: none;
}
.session-title-input:focus {
  border-style: solid;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 13%, transparent);
}
.session-title-display {
  max-width: 900px;
  color: var(--st-text-color);
  font-size: clamp(26px, 3vw, 42px);
  font-weight: 900;
  line-height: 1.15;
  letter-spacing: -.025em;
  text-shadow: 0 2px 10px color-mix(in srgb, var(--st-background-color) 65%, transparent);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.kj-app.edit-mode .session-title-display { display: none; }
.kj-app.view-mode .session-title-input { display: none; }
.kj-app.view-mode .session-title-panel { top: 28px; left: 34px; }

.kj-app:fullscreen {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--st-background-color);
}
.kj-app:fullscreen .board-header { border-radius: 0; flex: 0 0 auto; }
.kj-app:fullscreen .edit-toolbar,
.kj-app:fullscreen .hint-row { flex: 0 0 auto; }
.kj-app:fullscreen .board-viewport {
  flex: 1 1 auto;
  height: auto !important;
  min-height: 0 !important;
  border-radius: 0;
}
.kj-app:fullscreen .modal-shell.open {
  display: block;
  z-index: 2147483646;
}
.note-layer, .group-layer, .edge-layer { position: absolute; inset: 0; }
.edge-layer { width: 100%; height: 100%; overflow: visible; pointer-events: none; z-index: 1; }
.group-layer { z-index: 2; pointer-events: none; }
.note-layer { z-index: 3; pointer-events: none; }

.sticky-note {
  position: absolute;
  width: 210px;
  height: 150px;
  border: 1px solid rgba(0,0,0,.14);
  border-radius: 5px;
  box-shadow: 0 7px 18px rgba(0,0,0,.14);
  pointer-events: auto;
  color: #202020;
  transform: rotate(-.18deg);
  overflow: hidden;
  transition: box-shadow .16s ease, transform .16s ease;
}
.sticky-note:hover { box-shadow: 0 11px 25px rgba(0,0,0,.18); transform: rotate(0deg) translateY(-1px); }
.note-handle {
  height: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 .35rem 0 .5rem;
  cursor: grab;
  border-bottom: 1px dashed rgba(0,0,0,.14);
  font-size: 11px;
  color: rgba(0,0,0,.5);
}
.note-handle:active { cursor: grabbing; }
.note-delete { width: 24px; height: 22px; padding: 0; border: none; color: rgba(0,0,0,.55); background: transparent; font-weight: 900; }
.note-delete:hover { color: #b22; }
.note-title {
  display: flex;
  align-items: center;
  gap: .35rem;
  min-height: 29px;
  padding: .28rem .65rem;
  border-bottom: 1px solid rgba(0,0,0,.08);
  background: rgba(255,255,255,.28);
  font-size: 12px;
  font-weight: 850;
  overflow: hidden;
}
.note-title-text { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.note-type-badge {
  margin-left: auto;
  flex: 0 0 auto;
  padding: .08rem .32rem;
  border: 1px solid rgba(0,0,0,.16);
  border-radius: 999px;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: .04em;
}
.note-body {
  height: 95px;
  padding: .62rem .74rem .72rem;
  outline: none;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  overflow: auto;
  user-select: text;
  cursor: text;
  line-height: 1.42;
  font-size: 14px;
}
.sticky-note.no-title .note-body { height: 124px; }
.sticky-note.rich-note { cursor: zoom-in; }

.group-box {
  position: absolute;
  border: 2px dashed color-mix(in srgb, var(--accent) 68%, #5b78ff);
  border-radius: 14px;
  background: color-mix(in srgb, var(--accent) 5%, transparent);
  pointer-events: none;
}
.group-label {
  position: absolute;
  top: 7px;
  left: 10px;
  max-width: calc(100% - 54px);
  padding: .24rem .48rem;
  border-radius: 6px;
  background: color-mix(in srgb, var(--st-background-color) 92%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 40%, var(--border));
  color: var(--st-text-color);
  font-size: 12px;
  font-weight: 800;
  pointer-events: auto;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.group-label.connection-source { outline: 3px solid color-mix(in srgb, var(--accent) 52%, transparent); outline-offset: 2px; }
.group-delete {
  position: absolute;
  top: 7px;
  right: 8px;
  width: 26px;
  height: 25px;
  padding: 0;
  pointer-events: auto;
  border-radius: 7px;
  background: var(--st-background-color);
  color: var(--muted);
}

.edge-line {
  stroke: color-mix(in srgb, var(--st-text-color) 62%, transparent);
  stroke-width: 2.35;
  pointer-events: stroke;
  cursor: pointer;
}
.edge-label-bg { fill: var(--st-background-color); stroke: var(--border); stroke-width: 1; rx: 7; ry: 7; pointer-events: all; cursor: pointer; }
.edge-label-text { fill: var(--st-text-color); font-size: 12px; text-anchor: middle; dominant-baseline: middle; pointer-events: all; cursor: pointer; }

.selection-rect {
  position: absolute;
  display: none;
  border: 2px solid var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  pointer-events: none;
  z-index: 5;
}

.modal-shell { display: none; position: fixed; inset: 0; z-index: 10000; }
.modal-shell.open { display: block; }
.modal-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,.58); backdrop-filter: blur(3px); }
.modal-panel {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: min(1080px, 92vw);
  max-height: 90vh;
  overflow: auto;
  padding: 1.2rem 1.3rem 1.35rem;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--st-background-color);
  color: var(--st-text-color);
  box-shadow: 0 30px 85px rgba(0,0,0,.38);
}
.edge-modal-panel { width: min(620px, 92vw); }
.modal-header { display: flex; justify-content: space-between; gap: 1rem; align-items: start; padding-bottom: .75rem; border-bottom: 1px solid var(--border); }
.modal-header h2 { margin: .15rem 0 0; font-size: 1.3rem; }
.modal-kicker { color: var(--muted); font-size: 10px; font-weight: 850; letter-spacing: .14em; }
.modal-close { width: 38px; height: 38px; padding: 0; font-size: 23px; }
.note-modal-content { padding-top: 1rem; }
.note-modal-footer { padding-top: 1rem; display: flex; justify-content: flex-end; gap: .5rem; }
.editor-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .85rem; }
.editor-field { display: flex; flex-direction: column; gap: .32rem; color: var(--muted); font-size: 12px; font-weight: 700; }
.editor-field.full { grid-column: 1 / -1; }
.editor-field input, .editor-field textarea, .editor-field select { width: 100%; color: var(--st-text-color); }
.editor-field textarea { min-height: 280px; resize: vertical; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; line-height: 1.45; }
.editor-field textarea.summary-editor { min-height: 110px; font-family: var(--st-font); }
.preview-surface {
  min-height: 180px;
  padding: 1.1rem 1.2rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: color-mix(in srgb, var(--st-secondary-background-color) 50%, var(--st-background-color));
  overflow: auto;
}
.preview-surface img { display: block; max-width: 100%; max-height: 68vh; margin: 0 auto; object-fit: contain; border-radius: 8px; }
.preview-surface .mermaid-host svg { display: block; max-width: 100%; height: auto; margin: 0 auto; }
.preview-surface pre { margin: 0; padding: 1rem; overflow: auto; border-radius: 10px; background: #111827; color: #e5e7eb; line-height: 1.5; }
.preview-surface code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; }
.hljs-keyword, .hljs-selector-tag, .hljs-literal, .hljs-section, .hljs-link { color: #c084fc; }
.hljs-string, .hljs-title, .hljs-name, .hljs-type, .hljs-attribute, .hljs-symbol, .hljs-bullet, .hljs-addition { color: #86efac; }
.hljs-number, .hljs-meta, .hljs-built_in, .hljs-builtin-name, .hljs-params { color: #fbbf24; }
.hljs-comment, .hljs-quote, .hljs-deletion { color: #94a3b8; font-style: italic; }
.hljs-variable, .hljs-template-variable, .hljs-selector-id, .hljs-selector-class { color: #7dd3fc; }
.hljs-regexp, .hljs-template-tag { color: #fda4af; }
.hljs-emphasis { font-style: italic; }
.hljs-strong { font-weight: 800; }
.markdown-preview { line-height: 1.65; }
.markdown-preview h1, .markdown-preview h2, .markdown-preview h3 { margin-top: 1.1em; }
.markdown-preview table { border-collapse: collapse; width: 100%; }
.markdown-preview th, .markdown-preview td { border: 1px solid var(--border); padding: .4rem .55rem; }
.markdown-preview blockquote { margin-left: 0; padding-left: .8rem; border-left: 4px solid var(--accent); color: var(--muted); }
.markdown-preview img { max-width: 100%; }
.preview-error { padding: .8rem; border: 1px solid #d66; color: #b22; border-radius: 8px; white-space: pre-wrap; }
.loading-preview { color: var(--muted); text-align: center; padding: 2rem; }
.modal-actions { display: flex; gap: .5rem; align-items: center; padding-top: 1rem; }
.action-spacer { flex: 1; }
.edge-editor-form { display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; padding-top: 1rem; }

.kj-app.view-mode .edit-toolbar,
.kj-app.view-mode .hint-row,
.kj-app.view-mode .note-handle,
.kj-app.view-mode .note-delete,
.kj-app.view-mode .group-delete { display: none !important; }
.kj-app.view-mode .board-header { border-radius: 14px 14px 0 0; background: color-mix(in srgb, var(--st-background-color) 94%, var(--accent)); }
.kj-app.view-mode .board-brand-mark { background: color-mix(in srgb, var(--accent) 80%, #101828); }
.kj-app.view-mode .board-viewport {
  height: 82vh;
  min-height: 650px;
  border-radius: 0 0 14px 14px;
  background: radial-gradient(circle at 50% -20%, color-mix(in srgb, var(--accent) 8%, transparent), transparent 45%), var(--st-background-color);
  background-size: auto;
}
.kj-app.view-mode .sticky-note { box-shadow: 0 12px 30px rgba(0,0,0,.18); transform: none; }
.kj-app.view-mode .sticky-note:hover { transform: translateY(-2px) scale(1.01); }
.kj-app.view-mode .note-body { cursor: default; font-size: 15px; }
.kj-app.view-mode .group-box { background: color-mix(in srgb, var(--accent) 3%, transparent); }
.kj-app.view-mode .group-label { cursor: default; }
.kj-app.view-mode .edge-line,
.kj-app.view-mode .edge-label-bg,
.kj-app.view-mode .edge-label-text { cursor: default; }
.board-canvas.mode-group { cursor: crosshair; }


@media (max-width: 980px) {
  .board-header { align-items: flex-start; flex-direction: column; }
  .presentation-controls { width: 100%; justify-content: space-between; }
  .toolbar-row-secondary { align-items: flex-start; }
  .utilities { margin-left: 0; }
  .editor-grid, .edge-editor-form { grid-template-columns: 1fr; }
  .editor-field.full { grid-column: auto; }
}
"""

JS = r"""
const NOTE_W = 210;
const NOTE_H = 150;
const GROUP_PAD = {left: 30, right: 30, top: 52, bottom: 30};
const GROUP_MIN_W = 190;
const GROUP_MIN_H = 120;

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function uid(prefix) {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeBoard(board) {
  const src = board && typeof board === "object" ? board : {};
  const notes = Array.isArray(src.notes) ? src.notes.map((note) => {
    let type = note.type || "text";
    let inline = note.inline || "";
    let language = note.language || "python";
    let imageUrl = note.imageUrl || "";

    // Compatibility with the previous details model.
    if (!note.type && Array.isArray(note.details) && note.details.length) {
      const d = note.details[0] || {};
      type = d.kind === "mermaid" ? "mermaid" : "code";
      inline = d.code || "";
      language = d.lang || (type === "mermaid" ? "mermaid" : "text");
    }

    return {
      id: note.id || uid("note"),
      title: note.title || "",
      text: note.text || "",
      type,
      inline,
      language,
      imageUrl,
      color: note.color || "#FFF2A8",
      x: Number(note.x ?? 80),
      y: Number(note.y ?? 80),
      w: Number(note.w || NOTE_W),
      h: Number(note.h || NOTE_H),
    };
  }) : [];

  const groups = Array.isArray(src.groups) ? src.groups.map((group) => ({
    id: group.id || uid("group"),
    name: group.name || "無題グループ",
    noteIds: Array.isArray(group.noteIds) ? [...new Set(group.noteIds)] : [],
    childGroupIds: Array.isArray(group.childGroupIds) ? [...new Set(group.childGroupIds)] : [],
  })) : [];

  const groupIds = new Set(groups.map(g => g.id));
  for (const group of groups) {
    group.childGroupIds = group.childGroupIds.filter(id => id !== group.id && groupIds.has(id));
  }

  const edges = Array.isArray(src.edges) ? src.edges.map((edge) => ({
    id: edge.id || uid("edge"),
    source: edge.source,
    target: edge.target,
    label: edge.label || "関連",
    direction: ["none", "right", "left"].includes(edge.direction) ? edge.direction : "right",
  })).filter(e => groupIds.has(e.source) && groupIds.has(e.target) && e.source !== e.target) : [];

  return {title: String(src.title || ""), notes, groups, edges};
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

export default function(component) {
  const { parentElement, data, setStateValue } = component;

  if (parentElement.__kjApp) {
    const app = parentElement.__kjApp;
    const incoming = normalizeBoard(data?.board);
    const incomingSerialized = JSON.stringify(incoming);
    if (incomingSerialized !== app.lastSyncedSerialized && incomingSerialized !== JSON.stringify(app.board)) {
      app.board = clone(incoming);
      app.history = [];
      app.future = [];
      app.render();
    }
    return;
  }

  const root = parentElement.querySelector(".kj-app");
  const canvas = root.querySelector(".board-canvas");
  const viewport = root.querySelector(".board-viewport");
  const sessionTitleInput = root.querySelector(".session-title-input");
  const sessionTitleDisplay = root.querySelector(".session-title-display");
  const noteLayer = root.querySelector(".note-layer");
  const groupLayer = root.querySelector(".group-layer");
  const edgeLayer = root.querySelector(".edge-layer");
  const selectionRect = root.querySelector(".selection-rect");
  const noteTitleInput = root.querySelector(".new-note-title");
  const noteTextInput = root.querySelector(".new-note-text");
  const noteTypeSelect = root.querySelector(".new-note-type");
  const noteColorSelect = root.querySelector(".new-note-color");
  const edgeDirectionSelect = root.querySelector(".edge-direction");
  const modeHint = root.querySelector(".mode-hint");
  const statsEl = root.querySelector(".stats");
  const noteModal = root.querySelector(".note-modal");
  const noteModalTitle = root.querySelector(".note-modal-title");
  const noteModalContent = root.querySelector(".note-modal-content");
  const noteModalFooter = root.querySelector(".note-modal-footer");
  const edgeModal = root.querySelector(".edge-modal");
  const edgeEditorLabel = root.querySelector(".edge-editor-label");
  const edgeEditorDirection = root.querySelector(".edge-editor-direction");
  const jsonFileInput = root.querySelector(".json-file-input");

  const app = {
    board: clone(normalizeBoard(data?.board)),
    mode: "move",
    viewMode: "edit",
    connectionSource: null,
    history: [],
    future: [],
    lastSyncedSerialized: "",
    activeNoteId: null,
    activeEdgeId: null,

    noteById(id) { return this.board.notes.find(n => n.id === id); },
    groupById(id) { return this.board.groups.find(g => g.id === id); },
    edgeById(id) { return this.board.edges.find(e => e.id === id); },

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

    downloadBlob(blob, filename) {
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
    },

    timestampForFilename() {
      const d = new Date();
      const pad = (n) => String(n).padStart(2, "0");
      return `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
    },

    exportJson() {
      const text = JSON.stringify(this.board, null, 2);
      const blob = new Blob([text], {type: "application/json;charset=utf-8"});
      this.downloadBlob(blob, `kj-board-${this.timestampForFilename()}.json`);
    },

    requestJsonImport() {
      jsonFileInput.value = "";
      jsonFileInput.click();
    },

    async importJsonFile(file) {
      if (!file) return;
      try {
        const text = await file.text();
        const parsed = JSON.parse(text);
        const valid = parsed && typeof parsed === "object" &&
          Array.isArray(parsed.notes) && Array.isArray(parsed.groups) && Array.isArray(parsed.edges);
        if (!valid) throw new Error("notes / groups / edges 配列を持つ KJ ボード JSON ではありません。");
        if (!window.confirm("現在のボード内容を、選択した JSON ファイルの内容で置き換えますか？")) return;

        this.snapshot();
        this.closeNoteModal();
        this.closeEdgeModal();
        this.connectionSource = null;
        this.board = normalizeBoard(parsed);
        this.render();
        this.sync();
      } catch (err) {
        window.alert(`JSON の読み込みに失敗しました。\n${err?.message || String(err)}`);
      } finally {
        jsonFileInput.value = "";
      }
    },

    setViewMode(mode) {
      this.viewMode = mode === "view" ? "view" : "edit";
      root.classList.toggle("view-mode", this.viewMode === "view");
      root.classList.toggle("edit-mode", this.viewMode === "edit");
      root.querySelectorAll(".view-btn").forEach(btn => btn.classList.toggle("active", btn.dataset.view === this.viewMode));
      this.connectionSource = null;
      this.closeNoteModal();
      this.closeEdgeModal();
      this.render();
    },

    setMode(mode) {
      if (this.viewMode !== "edit") return;
      this.mode = mode;
      this.connectionSource = null;
      canvas.classList.toggle("mode-group", mode === "group");
      root.querySelectorAll(".mode-btn").forEach(btn => btn.classList.toggle("active", btn.dataset.mode === mode));
      const hints = {
        move: "編集: 付箋上部をドラッグして移動。text は本文を直接編集できます。",
        group: "グループ化: 空白から矩形をドラッグし、付箋や既存グループを囲みます。",
        connect: "グループ接続: 2つのグループタイトルを順に選択します。矢印種別は右のドロップダウンを使用します。",
      };
      modeHint.textContent = hints[mode] || "";
      this.render();
    },

    parentMap() {
      const map = new Map();
      for (const group of this.board.groups) {
        for (const child of group.childGroupIds || []) {
          if (!map.has(child)) map.set(child, group.id);
        }
      }
      return map;
    },

    groupDepth(id) {
      const parents = this.parentMap();
      let depth = 0;
      let current = id;
      const seen = new Set();
      while (parents.has(current) && !seen.has(current)) {
        seen.add(current);
        current = parents.get(current);
        depth += 1;
      }
      return depth;
    },

    noteRect(note) {
      return {
        x: Number(note.x || 0),
        y: Number(note.y || 0),
        w: Number(note.w || NOTE_W),
        h: Number(note.h || NOTE_H),
      };
    },

    groupBoundsById(groupId, stack = new Set()) {
      if (stack.has(groupId)) return null;
      const group = this.groupById(groupId);
      if (!group) return null;
      const nextStack = new Set(stack);
      nextStack.add(groupId);

      const rects = [];
      for (const noteId of group.noteIds || []) {
        const note = this.noteById(noteId);
        if (note) rects.push(this.noteRect(note));
      }
      for (const childId of group.childGroupIds || []) {
        const child = this.groupBoundsById(childId, nextStack);
        if (child) rects.push(child);
      }
      if (!rects.length) return null;

      const minX = Math.min(...rects.map(r => r.x));
      const minY = Math.min(...rects.map(r => r.y));
      const maxX = Math.max(...rects.map(r => r.x + r.w));
      const maxY = Math.max(...rects.map(r => r.y + r.h));
      const naturalW = (maxX - minX) + GROUP_PAD.left + GROUP_PAD.right;
      const naturalH = (maxY - minY) + GROUP_PAD.top + GROUP_PAD.bottom;
      const w = Math.max(GROUP_MIN_W, naturalW);
      const h = Math.max(GROUP_MIN_H, naturalH);
      const x = minX - GROUP_PAD.left;
      const y = minY - GROUP_PAD.top;
      return {x, y, w, h, cx: x + w / 2, cy: y + h / 2};
    },

    notesInsideGroup(groupId, stack = new Set()) {
      if (stack.has(groupId)) return new Set();
      const group = this.groupById(groupId);
      if (!group) return new Set();
      const nextStack = new Set(stack);
      nextStack.add(groupId);
      const result = new Set(group.noteIds || []);
      for (const childId of group.childGroupIds || []) {
        for (const noteId of this.notesInsideGroup(childId, nextStack)) result.add(noteId);
      }
      return result;
    },

    boundaryPoint(rect, targetX, targetY) {
      const dx = targetX - rect.cx;
      const dy = targetY - rect.cy;
      if (Math.abs(dx) < 0.0001 && Math.abs(dy) < 0.0001) return {x: rect.cx, y: rect.cy};
      const halfW = rect.w / 2;
      const halfH = rect.h / 2;
      const scaleX = Math.abs(dx) > 0.0001 ? halfW / Math.abs(dx) : Infinity;
      const scaleY = Math.abs(dy) > 0.0001 ? halfH / Math.abs(dy) : Infinity;
      const scale = Math.min(scaleX, scaleY);
      return {x: rect.cx + dx * scale, y: rect.cy + dy * scale};
    },

    resizeCanvas() {
      let maxX = 1500;
      let maxY = 900;
      for (const note of this.board.notes) {
        const r = this.noteRect(note);
        maxX = Math.max(maxX, r.x + r.w + 220);
        maxY = Math.max(maxY, r.y + r.h + 220);
      }
      for (const group of this.board.groups) {
        const r = this.groupBoundsById(group.id);
        if (!r) continue;
        maxX = Math.max(maxX, r.x + r.w + 220);
        maxY = Math.max(maxY, r.y + r.h + 220);
      }
      canvas.style.width = `${Math.ceil(maxX)}px`;
      canvas.style.height = `${Math.ceil(maxY)}px`;
    },

    addNote() {
      if (this.viewMode !== "edit") return;
      const text = noteTextInput.value.trim();
      const title = noteTitleInput.value.trim();
      if (!text && !title) {
        noteTextInput.focus();
        return;
      }
      this.snapshot();
      const type = noteTypeSelect.value;
      const x = Math.min(canvas.clientWidth - NOTE_W - 10, Math.max(35, viewport.scrollLeft + 75 + Math.random() * 70));
      const y = Math.min(canvas.clientHeight - NOTE_H - 10, Math.max(115, viewport.scrollTop + 115 + Math.random() * 70));
      const note = {
        id: uid("note"),
        title,
        text,
        type,
        inline: "",
        language: "python",
        imageUrl: "",
        color: noteColorSelect.value,
        x: Math.round(x),
        y: Math.round(y),
        w: NOTE_W,
        h: NOTE_H,
      };
      this.board.notes.push(note);
      noteTitleInput.value = "";
      noteTextInput.value = "";
      this.render();
      this.sync();
      if (type !== "text") this.openNoteModal(note.id);
      else noteTextInput.focus();
    },

    deleteNote(id) {
      if (this.viewMode !== "edit") return;
      this.snapshot();
      this.board.notes = this.board.notes.filter(n => n.id !== id);
      for (const group of this.board.groups) group.noteIds = (group.noteIds || []).filter(nid => nid !== id);
      this.cleanupEmptyGroups();
      this.render();
      this.sync();
    },

    cleanupEmptyGroups() {
      let changed = true;
      while (changed) {
        changed = false;
        const validIds = new Set(this.board.groups.map(g => g.id));
        for (const group of this.board.groups) group.childGroupIds = (group.childGroupIds || []).filter(id => validIds.has(id));
        const emptyIds = new Set(this.board.groups.filter(g => !(g.noteIds || []).length && !(g.childGroupIds || []).length).map(g => g.id));
        if (emptyIds.size) {
          changed = true;
          this.board.groups = this.board.groups.filter(g => !emptyIds.has(g.id));
          for (const group of this.board.groups) group.childGroupIds = (group.childGroupIds || []).filter(id => !emptyIds.has(id));
          this.board.edges = this.board.edges.filter(e => !emptyIds.has(e.source) && !emptyIds.has(e.target));
        }
      }
    },

    deleteGroup(id) {
      if (this.viewMode !== "edit") return;
      const group = this.groupById(id);
      if (!group) return;
      this.snapshot();
      const parents = this.board.groups.filter(g => (g.childGroupIds || []).includes(id));
      for (const parent of parents) {
        parent.childGroupIds = (parent.childGroupIds || []).filter(gid => gid !== id);
        parent.childGroupIds.push(...(group.childGroupIds || []).filter(gid => gid !== parent.id));
        parent.childGroupIds = [...new Set(parent.childGroupIds)];
        parent.noteIds = [...new Set([...(parent.noteIds || []), ...(group.noteIds || [])])];
      }
      this.board.groups = this.board.groups.filter(g => g.id !== id);
      this.board.edges = this.board.edges.filter(e => e.source !== id && e.target !== id);
      if (this.connectionSource === id) this.connectionSource = null;
      this.render();
      this.sync();
    },

    createGroup(noteIds, childGroupIds, parentGroupId = null) {
      if (this.viewMode !== "edit") return;
      if (!noteIds.length && !childGroupIds.length) return;
      const name = window.prompt("グループ名を入力してください", "新しいグループ");
      if (name === null) return;
      this.snapshot();

      const newGroupId = uid("group");
      const selectedChildren = new Set(childGroupIds);

      // Re-parent selected groups so a group has one visual parent.
      for (const group of this.board.groups) {
        group.childGroupIds = (group.childGroupIds || []).filter(id => !selectedChildren.has(id));
      }

      // When a new group is created inside an existing group, move directly-owned
      // selected notes into the child group and attach that child to the parent.
      if (parentGroupId) {
        const parent = this.groupById(parentGroupId);
        if (parent) {
          const selectedNotes = new Set(noteIds);
          parent.noteIds = (parent.noteIds || []).filter(id => !selectedNotes.has(id));
          parent.childGroupIds = [...new Set([...(parent.childGroupIds || []), newGroupId])];
        }
      }

      this.board.groups.push({
        id: newGroupId,
        name: name.trim() || "無題グループ",
        noteIds: [...new Set(noteIds)],
        childGroupIds: [...selectedChildren],
      });
      this.render();
      this.sync();
    },

    handleGroupClick(id) {
      if (this.viewMode !== "edit" || this.mode !== "connect") return;
      if (!this.connectionSource) {
        this.connectionSource = id;
        this.render();
        return;
      }
      if (this.connectionSource === id) {
        this.connectionSource = null;
        this.render();
        return;
      }
      const src = this.groupById(this.connectionSource);
      const dst = this.groupById(id);
      const label = window.prompt(`「${src?.name || ""}」と「${dst?.name || ""}」の関係名`, "関連");
      if (label !== null) {
        this.snapshot();
        this.board.edges.push({
          id: uid("edge"),
          source: this.connectionSource,
          target: id,
          label: label.trim() || "関連",
          direction: edgeDirectionSelect.value,
        });
        this.sync();
      }
      this.connectionSource = null;
      this.render();
    },

    openEdgeModal(edgeId) {
      if (this.viewMode !== "edit") return;
      const edge = this.edgeById(edgeId);
      if (!edge) return;
      this.activeEdgeId = edgeId;
      edgeEditorLabel.value = edge.label || "関連";
      edgeEditorDirection.value = edge.direction || "right";
      edgeModal.classList.add("open");
      edgeModal.setAttribute("aria-hidden", "false");
    },

    closeEdgeModal() {
      this.activeEdgeId = null;
      edgeModal.classList.remove("open");
      edgeModal.setAttribute("aria-hidden", "true");
    },

    saveEdgeModal() {
      if (this.viewMode !== "edit" || !this.activeEdgeId) return;
      const edge = this.edgeById(this.activeEdgeId);
      if (!edge) return;
      this.snapshot();
      edge.label = edgeEditorLabel.value.trim() || "関連";
      edge.direction = edgeEditorDirection.value;
      this.closeEdgeModal();
      this.render();
      this.sync();
    },

    deleteActiveEdge() {
      if (this.viewMode !== "edit" || !this.activeEdgeId) return;
      const id = this.activeEdgeId;
      this.snapshot();
      this.board.edges = this.board.edges.filter(e => e.id !== id);
      this.closeEdgeModal();
      this.render();
      this.sync();
    },

    closeNoteModal() {
      this.activeNoteId = null;
      noteModal.classList.remove("open");
      noteModal.setAttribute("aria-hidden", "true");
      noteModalContent.innerHTML = "";
      noteModalFooter.innerHTML = "";
    },

    async renderDisplayPreview(note, host) {
      host.innerHTML = `<div class="loading-preview">プレビューを生成しています…</div>`;
      try {
        if (note.type === "image") {
          if (!note.imageUrl) {
            host.innerHTML = `<div class="preview-error">画像 URL が設定されていません。</div>`;
            return;
          }
          host.innerHTML = `<img src="${escapeHtml(note.imageUrl)}" alt="${escapeHtml(note.title || "付箋画像")}" />`;
          return;
        }

        if (note.type === "text") {
          host.innerHTML = `<div style="white-space:pre-wrap;font-size:1.08rem;line-height:1.7">${escapeHtml(note.text)}</div>`;
          return;
        }

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
          host.innerHTML = `<div class="markdown-preview">${modules.marked.parse(note.inline || "")}</div>`;
          return;
        }

        if (note.type === "mermaid") {
          const id = `mermaid_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
          const rendered = await modules.mermaid.render(id, note.inline || "graph TD\n  A[未設定] --> B[Mermaid]");
          host.innerHTML = `<div class="mermaid-host">${rendered.svg}</div>`;
          return;
        }
      } catch (err) {
        host.innerHTML = `<div class="preview-error">プレビュー生成に失敗しました。\n${escapeHtml(err?.message || String(err))}</div>`;
      }
    },

    openNoteModal(noteId) {
      const note = this.noteById(noteId);
      if (!note) return;
      this.activeNoteId = noteId;
      noteModalTitle.textContent = note.title || `${note.type} 付箋`;
      noteModalContent.innerHTML = "";
      noteModalFooter.innerHTML = "";

      if (this.viewMode === "view") {
        const preview = document.createElement("div");
        preview.className = "preview-surface";
        noteModalContent.appendChild(preview);
        this.renderDisplayPreview(note, preview);
        noteModal.classList.add("open");
        noteModal.setAttribute("aria-hidden", "false");
        return;
      }

      const grid = document.createElement("div");
      grid.className = "editor-grid";

      const titleField = document.createElement("label");
      titleField.className = "editor-field";
      titleField.innerHTML = `<span>タイトル</span><input class="edit-note-title" type="text" value="${escapeHtml(note.title)}" />`;
      grid.appendChild(titleField);

      const colorField = document.createElement("label");
      colorField.className = "editor-field";
      colorField.innerHTML = `
        <span>付箋色</span>
        <select class="edit-note-color">
          <option value="#FFF2A8">イエロー</option>
          <option value="#DDF4D2">グリーン</option>
          <option value="#DCEEFF">ブルー</option>
          <option value="#F7DDF1">ピンク</option>
          <option value="#FFE0C2">オレンジ</option>
          <option value="#E9E0FF">パープル</option>
        </select>`;
      grid.appendChild(colorField);

      const summaryField = document.createElement("label");
      summaryField.className = "editor-field full";
      summaryField.innerHTML = `<span>付箋に表示する内容</span><textarea class="summary-editor edit-note-text">${escapeHtml(note.text)}</textarea>`;
      grid.appendChild(summaryField);

      if (note.type === "code") {
        const langField = document.createElement("label");
        langField.className = "editor-field";
        langField.innerHTML = `
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
          </select>`;
        grid.appendChild(langField);
      }

      if (["code", "markdown", "mermaid"].includes(note.type)) {
        const inlineField = document.createElement("label");
        inlineField.className = "editor-field full";
        const label = note.type === "code" ? "コード" : note.type === "markdown" ? "Markdown" : "Mermaid";
        inlineField.innerHTML = `<span>${label}</span><textarea class="edit-note-inline" spellcheck="false">${escapeHtml(note.inline || "")}</textarea>`;
        grid.appendChild(inlineField);
      } else if (note.type === "image") {
        const urlField = document.createElement("label");
        urlField.className = "editor-field full";
        urlField.innerHTML = `<span>画像 URL</span><input class="edit-note-image" type="url" placeholder="https://example.com/image.png" value="${escapeHtml(note.imageUrl || "")}" />`;
        grid.appendChild(urlField);
        const preview = document.createElement("div");
        preview.className = "preview-surface full image-edit-preview";
        if (note.imageUrl) preview.innerHTML = `<img src="${escapeHtml(note.imageUrl)}" alt="preview" />`;
        grid.appendChild(preview);
      }

      noteModalContent.appendChild(grid);
      const colorSelect = grid.querySelector(".edit-note-color");
      if (colorSelect) colorSelect.value = note.color;
      const langSelect = grid.querySelector(".edit-note-language");
      if (langSelect) langSelect.value = note.language || "python";
      const imageInput = grid.querySelector(".edit-note-image");
      if (imageInput) {
        imageInput.addEventListener("input", () => {
          const preview = grid.querySelector(".image-edit-preview");
          preview.innerHTML = imageInput.value.trim() ? `<img src="${escapeHtml(imageInput.value.trim())}" alt="preview" />` : "";
        });
      }

      const cancel = document.createElement("button");
      cancel.textContent = "キャンセル";
      cancel.addEventListener("click", () => this.closeNoteModal());
      const save = document.createElement("button");
      save.className = "primary-btn";
      save.textContent = "保存";
      save.addEventListener("click", () => {
        const current = this.noteById(noteId);
        if (!current) return;
        this.snapshot();
        current.title = grid.querySelector(".edit-note-title")?.value.trim() || "";
        current.text = grid.querySelector(".edit-note-text")?.value || "";
        current.color = grid.querySelector(".edit-note-color")?.value || current.color;
        if (current.type === "code") current.language = grid.querySelector(".edit-note-language")?.value || "plaintext";
        if (["code", "markdown", "mermaid"].includes(current.type)) current.inline = grid.querySelector(".edit-note-inline")?.value || "";
        if (current.type === "image") current.imageUrl = grid.querySelector(".edit-note-image")?.value.trim() || "";
        this.closeNoteModal();
        this.render();
        this.sync();
      });
      noteModalFooter.append(cancel, save);
      noteModal.classList.add("open");
      noteModal.setAttribute("aria-hidden", "false");
    },

    renderEdges() {
      edgeLayer.innerHTML = `
        <defs>
          <marker id="arrow-right" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto" markerUnits="strokeWidth">
            <polygon points="0 0, 10 3.5, 0 7" fill="color-mix(in srgb, var(--st-text-color) 62%, transparent)"></polygon>
          </marker>
          <marker id="arrow-left" markerWidth="10" markerHeight="7" refX="1" refY="3.5" orient="auto" markerUnits="strokeWidth">
            <polygon points="10 0, 0 3.5, 10 7" fill="color-mix(in srgb, var(--st-text-color) 62%, transparent)"></polygon>
          </marker>
        </defs>`;

      for (const edge of this.board.edges) {
        const a = this.groupBoundsById(edge.source);
        const b = this.groupBoundsById(edge.target);
        if (!a || !b) continue;
        const start = this.boundaryPoint(a, b.cx, b.cy);
        const end = this.boundaryPoint(b, a.cx, a.cy);
        const mx = (start.x + end.x) / 2;
        const my = (start.y + end.y) / 2;

        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", start.x);
        line.setAttribute("y1", start.y);
        line.setAttribute("x2", end.x);
        line.setAttribute("y2", end.y);
        line.setAttribute("class", "edge-line");
        if (edge.direction === "right") line.setAttribute("marker-end", "url(#arrow-right)");
        if (edge.direction === "left") line.setAttribute("marker-start", "url(#arrow-left)");

        const labelWidth = Math.max(64, Math.min(250, 22 + String(edge.label || "").length * 12));
        const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        bg.setAttribute("x", mx - labelWidth / 2);
        bg.setAttribute("y", my - 15);
        bg.setAttribute("width", labelWidth);
        bg.setAttribute("height", 30);
        bg.setAttribute("class", "edge-label-bg");
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", mx);
        text.setAttribute("y", my + 1);
        text.setAttribute("class", "edge-label-text");
        text.textContent = edge.label;

        if (this.viewMode === "edit") {
          const edit = (evt) => { evt.stopPropagation(); this.openEdgeModal(edge.id); };
          line.addEventListener("dblclick", edit);
          bg.addEventListener("dblclick", edit);
          text.addEventListener("dblclick", edit);
        }
        g.append(line, bg, text);
        edgeLayer.appendChild(g);
      }
    },

    renderGroups() {
      groupLayer.innerHTML = "";
      const groups = [...this.board.groups].sort((a, b) => this.groupDepth(a.id) - this.groupDepth(b.id));
      for (const group of groups) {
        const b = this.groupBoundsById(group.id);
        if (!b) continue;
        const el = document.createElement("div");
        el.className = "group-box";
        el.style.left = `${b.x}px`;
        el.style.top = `${b.y}px`;
        el.style.width = `${b.w}px`;
        el.style.height = `${b.h}px`;
        el.dataset.groupId = group.id;

        const label = document.createElement("div");
        label.className = "group-label";
        if (group.id === this.connectionSource) label.classList.add("connection-source");
        label.textContent = group.name;
        label.title = this.viewMode === "edit" ? "接続モード: クリック / 名前変更: ダブルクリック" : group.name;
        if (this.viewMode === "edit") {
          label.addEventListener("click", (evt) => { evt.stopPropagation(); this.handleGroupClick(group.id); });
          label.addEventListener("dblclick", (evt) => {
            evt.preventDefault();
            evt.stopPropagation();
            const next = window.prompt("グループ名を編集", group.name);
            if (next === null) return;
            this.snapshot();
            group.name = next.trim() || "無題グループ";
            this.render();
            this.sync();
          });
        }

        const del = document.createElement("button");
        del.className = "group-delete";
        del.textContent = "×";
        del.title = "グループのみ解除";
        del.addEventListener("click", (evt) => { evt.stopPropagation(); this.deleteGroup(group.id); });

        el.append(label, del);
        groupLayer.appendChild(el);
      }
    },

    renderNotes() {
      noteLayer.innerHTML = "";
      for (const note of this.board.notes) {
        const el = document.createElement("div");
        el.className = "sticky-note";
        if (!note.title && note.type === "text") el.classList.add("no-title");
        if (note.type !== "text") el.classList.add("rich-note");
        el.style.left = `${note.x}px`;
        el.style.top = `${note.y}px`;
        el.style.width = `${note.w || NOTE_W}px`;
        el.style.height = `${note.h || NOTE_H}px`;
        el.style.background = note.color;
        el.dataset.noteId = note.id;

        const handle = document.createElement("div");
        handle.className = "note-handle";
        handle.innerHTML = `<span>⋮⋮ drag</span>`;
        const del = document.createElement("button");
        del.className = "note-delete";
        del.textContent = "×";
        del.title = "付箋を削除";
        del.addEventListener("pointerdown", (evt) => {
          evt.stopPropagation();
        });
        del.addEventListener("dblclick", (evt) => {
          evt.preventDefault();
          evt.stopPropagation();
        });
        del.addEventListener("click", (evt) => {
          evt.preventDefault();
          evt.stopPropagation();
          evt.stopImmediatePropagation();
          this.deleteNote(note.id);
        });
        handle.appendChild(del);
        el.appendChild(handle);

        const titleBar = document.createElement("div");
        titleBar.className = "note-title";
        const titleText = document.createElement("span");
        titleText.className = "note-title-text";
        titleText.textContent = note.title || (note.type === "text" ? "" : note.type);
        titleText.title = note.title || note.type;
        const badge = document.createElement("span");
        badge.className = "note-type-badge";
        badge.textContent = note.type;
        titleBar.append(titleText, badge);
        if (note.title || note.type !== "text") el.appendChild(titleBar);

        const body = document.createElement("div");
        body.className = "note-body";
        body.spellcheck = false;
        body.textContent = note.text;
        body.contentEditable = this.viewMode === "edit" && note.type === "text" ? "true" : "false";

        if (this.viewMode === "edit" && note.type === "text") {
          body.addEventListener("blur", () => {
            const next = body.textContent ?? "";
            if (next !== note.text) {
              this.snapshot();
              note.text = next;
              this.sync();
            }
          });
          body.addEventListener("keydown", (evt) => {
            if ((evt.ctrlKey || evt.metaKey) && evt.key === "Enter") body.blur();
          });
        }

        el.addEventListener("dblclick", (evt) => {
          if (evt.target.closest(".note-delete")) return;
          if (note.type === "text" && this.viewMode === "edit") return;
          evt.preventDefault();
          evt.stopPropagation();
          this.openNoteModal(note.id);
        });

        handle.addEventListener("pointerdown", (evt) => {
          if (evt.target.closest(".note-delete")) return;
          if (this.viewMode !== "edit" || this.mode !== "move") return;
          evt.preventDefault();
          evt.stopPropagation();
          this.snapshot();
          const startX = evt.clientX;
          const startY = evt.clientY;
          const originalX = note.x;
          const originalY = note.y;
          handle.setPointerCapture(evt.pointerId);

          const move = (moveEvt) => {
            const dx = moveEvt.clientX - startX;
            const dy = moveEvt.clientY - startY;
            note.x = Math.max(4, Math.min(canvas.clientWidth - (note.w || NOTE_W) - 4, originalX + dx));
            note.y = Math.max(4, Math.min(canvas.clientHeight - (note.h || NOTE_H) - 4, originalY + dy));
            el.style.left = `${note.x}px`;
            el.style.top = `${note.y}px`;
            this.renderGroups();
            this.renderEdges();
          };
          const up = (upEvt) => {
            try { handle.releasePointerCapture(upEvt.pointerId); } catch (_) {}
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

        el.appendChild(body);
        noteLayer.appendChild(el);
      }
    },

    renderTitle() {
      const title = this.board.title || "";
      if (document.activeElement !== sessionTitleInput) sessionTitleInput.value = title;
      sessionTitleDisplay.textContent = title || "KJ Session";
    },

    renderStats() {
      const typeCounts = {};
      for (const note of this.board.notes) typeCounts[note.type] = (typeCounts[note.type] || 0) + 1;
      const rich = ["code", "markdown", "mermaid", "image"].reduce((sum, key) => sum + (typeCounts[key] || 0), 0);
      statsEl.textContent = `付箋 ${this.board.notes.length} / グループ ${this.board.groups.length} / 接続 ${this.board.edges.length} / リッチ付箋 ${rich}`;
    },

    render() {
      this.resizeCanvas();
      this.renderTitle();
      this.renderNotes();
      this.renderGroups();
      this.renderEdges();
      this.renderStats();
    },

    undo() {
      if (this.viewMode !== "edit" || !this.history.length) return;
      this.future.push(clone(this.board));
      this.board = this.history.pop();
      this.connectionSource = null;
      this.render();
      this.sync();
    },

    redo() {
      if (this.viewMode !== "edit" || !this.future.length) return;
      this.history.push(clone(this.board));
      this.board = this.future.pop();
      this.connectionSource = null;
      this.render();
      this.sync();
    },

    reset() {
      if (this.viewMode !== "edit") return;
      if (!window.confirm("ボード上の付箋・グループ・接続線をすべて削除しますか？")) return;
      this.snapshot();
      this.board = {title: this.board.title || "", notes: [], groups: [], edges: []};
      this.connectionSource = null;
      this.render();
      this.sync();
    },
  };

  parentElement.__kjApp = app;

  root.querySelector('[data-action="add-note"]').addEventListener("click", () => app.addNote());
  const commitSessionTitle = () => {
    const next = sessionTitleInput.value.trim();
    if (next === (app.board.title || "")) return;
    app.snapshot();
    app.board.title = next;
    app.renderTitle();
    app.sync();
  };
  sessionTitleInput.addEventListener("blur", commitSessionTitle);
  sessionTitleInput.addEventListener("keydown", (evt) => {
    if (evt.key === "Enter") {
      evt.preventDefault();
      sessionTitleInput.blur();
    }
  });

  noteTextInput.addEventListener("keydown", (evt) => {
    if ((evt.ctrlKey || evt.metaKey) && evt.key === "Enter") {
      evt.preventDefault();
      app.addNote();
    }
  });
  root.querySelectorAll(".mode-btn").forEach(btn => btn.addEventListener("click", () => app.setMode(btn.dataset.mode)));
  root.querySelectorAll(".view-btn").forEach(btn => btn.addEventListener("click", () => app.setViewMode(btn.dataset.view)));
  root.querySelector('[data-action="undo"]').addEventListener("click", () => app.undo());
  root.querySelector('[data-action="redo"]').addEventListener("click", () => app.redo());
  root.querySelector('[data-action="reset"]').addEventListener("click", () => app.reset());
  root.querySelector('[data-action="export-json"]').addEventListener("click", () => app.exportJson());
  root.querySelector('[data-action="import-json"]').addEventListener("click", () => app.requestJsonImport());
  jsonFileInput.addEventListener("change", () => app.importJsonFile(jsonFileInput.files?.[0]));
  root.querySelector('[data-action="fullscreen"]').addEventListener("click", async () => {
    try {
      if (!document.fullscreenElement) await root.requestFullscreen();
      else await document.exitFullscreen();
    } catch (err) {
      window.alert(`全画面表示を開始できませんでした。\n${err?.message || String(err)}`);
    }
  });

  root.querySelectorAll('[data-action="close-note-modal"]').forEach(el => el.addEventListener("click", () => app.closeNoteModal()));
  root.querySelectorAll('[data-action="close-edge-modal"]').forEach(el => el.addEventListener("click", () => app.closeEdgeModal()));
  root.querySelector('[data-action="save-edge"]').addEventListener("click", () => app.saveEdgeModal());
  root.querySelector('[data-action="delete-edge"]').addEventListener("click", () => app.deleteActiveEdge());

  root.addEventListener("keydown", (evt) => {
    if (evt.key === "Escape") {
      if (noteModal.classList.contains("open")) app.closeNoteModal();
      if (edgeModal.classList.contains("open")) app.closeEdgeModal();
    }
  });

  canvas.addEventListener("pointerdown", (evt) => {
    if (app.viewMode !== "edit" || app.mode !== "group") return;
    if (evt.target !== canvas && evt.target !== noteLayer && evt.target !== groupLayer && evt.target !== edgeLayer) return;

    evt.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const startX = evt.clientX - rect.left;
    const startY = evt.clientY - rect.top;
    selectionRect.style.display = "block";
    selectionRect.style.left = `${startX}px`;
    selectionRect.style.top = `${startY}px`;
    selectionRect.style.width = "0px";
    selectionRect.style.height = "0px";
    canvas.setPointerCapture(evt.pointerId);

    const move = (moveEvt) => {
      const x = moveEvt.clientX - rect.left;
      const y = moveEvt.clientY - rect.top;
      const left = Math.min(startX, x);
      const top = Math.min(startY, y);
      selectionRect.style.left = `${left}px`;
      selectionRect.style.top = `${top}px`;
      selectionRect.style.width = `${Math.abs(x - startX)}px`;
      selectionRect.style.height = `${Math.abs(y - startY)}px`;
    };

    const up = (upEvt) => {
      try { canvas.releasePointerCapture(upEvt.pointerId); } catch (_) {}
      canvas.removeEventListener("pointermove", move);
      canvas.removeEventListener("pointerup", up);
      canvas.removeEventListener("pointercancel", up);

      const left = parseFloat(selectionRect.style.left);
      const top = parseFloat(selectionRect.style.top);
      const width = parseFloat(selectionRect.style.width);
      const height = parseFloat(selectionRect.style.height);
      selectionRect.style.display = "none";
      if (width < 14 || height < 14) return;
      const right = left + width;
      const bottom = top + height;

      const allSelectedGroups = app.board.groups.filter(group => {
        const b = app.groupBoundsById(group.id);
        return b && b.x >= left && b.y >= top && b.x + b.w <= right && b.y + b.h <= bottom;
      }).map(g => g.id);
      const selectedSet = new Set(allSelectedGroups);
      const parents = app.parentMap();
      const topSelectedGroups = allSelectedGroups.filter(id => {
        let p = parents.get(id);
        while (p) {
          if (selectedSet.has(p)) return false;
          p = parents.get(p);
        }
        return true;
      });

      const notesCoveredBySelectedGroups = new Set();
      for (const gid of topSelectedGroups) {
        for (const nid of app.notesInsideGroup(gid)) notesCoveredBySelectedGroups.add(nid);
      }

      // If the selection is completely inside an existing group, make the new
      // group its child. Choosing the deepest container keeps nesting intuitive.
      const containerCandidates = app.board.groups.filter(group => {
        if (selectedSet.has(group.id)) return false;
        const b = app.groupBoundsById(group.id);
        return b && left >= b.x && top >= b.y && right <= b.x + b.w && bottom <= b.y + b.h;
      }).sort((a, b) => app.groupDepth(b.id) - app.groupDepth(a.id));
      const parentGroupId = containerCandidates.length ? containerCandidates[0].id : null;

      // Notes already enclosed by a selected child group belong to that child.
      // For an inner group, only take notes directly owned by the container (or
      // currently ungrouped notes) to avoid pulling notes out of a partially
      // selected sibling group.
      const directOwners = new Map();
      for (const group of app.board.groups) {
        for (const nid of group.noteIds || []) {
          if (!directOwners.has(nid)) directOwners.set(nid, group.id);
        }
      }
      const selectedNotes = app.board.notes.filter(note => {
        if (notesCoveredBySelectedGroups.has(note.id)) return false;
        const owner = directOwners.get(note.id) || null;
        if (parentGroupId && owner && owner !== parentGroupId) return false;
        if (!parentGroupId && owner) return false;
        const r = app.noteRect(note);
        const cx = r.x + r.w / 2;
        const cy = r.y + r.h / 2;
        return cx >= left && cx <= right && cy >= top && cy <= bottom;
      }).map(n => n.id);

      app.createGroup(selectedNotes, topSelectedGroups, parentGroupId);
    };

    canvas.addEventListener("pointermove", move);
    canvas.addEventListener("pointerup", up);
    canvas.addEventListener("pointercancel", up);
  });

  app.setViewMode("edit");
  app.setMode("move");
  app.render();
  if (!data?.board || !Array.isArray(data.board.notes)) app.sync();

  return () => { delete parentElement.__kjApp; };
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
    "オンライン KJ 法セッション向けボード。編集モードで付箋・グループ・関係を構築し、"
    "表示モードでプレゼンテーション向けに閲覧できます。"
)

with st.expander("操作ガイド", expanded=False):
    st.markdown(
        """
- **編集モード**: 付箋の作成・移動、グループ化、接続線の作成・編集を行います。
- **表示モード**: 編集 UI を隠し、ボードをプレゼン向けに表示します。全画面表示中も `code` / `markdown` / `mermaid` / `image` 付箋をダブルクリックして内容を開けます。
- **グループ化**: 空白から矩形選択します。既存グループを含めて囲むと親グループになり、子グループの矩形・タイトル・余白まで含むよう親矩形が自動拡張されます。
- **接続線**: 接続モードで2つのグループ名を順に選びます。矢印なし・右向き・左向きを選択できます。
- **リッチ付箋**: `code` / `markdown` / `mermaid` は編集モードのポップアップでソースを編集します。`image` は画像 URL を設定します。
- **セッションタイトル**: ボード左上で編集できます。JSON 保存時にもタイトルが保持されます。
- **JSON保存 / JSON読込**: 現在のボードを JSON に保存し、保存済み JSON でボード全体を置き換えられます。
        """
    )

component_key = "kj_board_component"
current_board = get_component_board(component_key)
result = KJ_BOARD_COMPONENT(
    data={"board": current_board},
    default={"board": current_board},
    key=component_key,
    on_board_change=lambda: None,
)

board = getattr(result, "board", current_board) or current_board
st.session_state.board_seed = copy.deepcopy(board)

c1, c2, c3 = st.columns(3)
c1.metric("付箋", len(board.get("notes", [])))
c2.metric("グループ", len(board.get("groups", [])))
c3.metric("接続線", len(board.get("edges", [])))

st.caption(
    "Markdown / Mermaid / シンタックスハイライトの表示はブラウザ側レンダリングです。"
    "閉域環境へ展開する場合は、各 JavaScript ライブラリをローカル配布へ切り替えてください。"
)
