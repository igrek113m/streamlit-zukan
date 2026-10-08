#!/usr/bin/env python3
"""Validate JSON intended for the current KJ Board application.

Uses only the Python standard library. Run with --strict before importing into
KJ Board; this tool validates structure, not browser rendering or URL reachability.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

TYPES = {"markdown", "code", "mermaid", "image"}
COLORS = {
    "#FFF2A8": "Yellow",
    "#DDF4D2": "Green",
    "#DCEEFF": "Blue",
    "#F7DDF1": "Pink",
    "#FFE0C2": "Orange",
    "#E9E0FF": "Purple",
}
CORE_FIELDS = ("id", "title", "text", "type", "color", "x", "y", "w", "z")
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


def is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_board(board: object, strict: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(board, dict):
        return ["Top-level JSON must be an object"], warnings
    if not isinstance(board.get("title"), str):
        errors.append("title: must be a string")
    notes = board.get("notes")
    if not isinstance(notes, list):
        return errors + ["notes: must be an array"], warnings
    if not notes:
        warnings.append("notes: board has no cards")
    for forbidden in ("groups", "edges"):
        if forbidden in board:
            msg = f"{forbidden}: obsolete; current KJ Board ignores this field"
            (errors if strict else warnings).append(msg)
    for extra in sorted(set(board) - {"title", "notes", "groups", "edges"}):
        warnings.append(f"root: additional field '{extra}' may not be preserved")

    seen: set[str] = set()
    zs: list[int] = []
    for index, note in enumerate(notes):
        path = f"notes[{index}]"
        if not isinstance(note, dict):
            errors.append(f"{path}: must be an object")
            continue
        for key in CORE_FIELDS:
            if key not in note:
                errors.append(f"{path}.{key}: required for new boards")
        note_type = note.get("type")
        if not isinstance(note_type, str) or note_type not in TYPES:
            errors.append(f"{path}.type: must be one of {', '.join(sorted(TYPES))}")
        nid = note.get("id")
        if not isinstance(nid, str) or not ID_PATTERN.fullmatch(nid):
            errors.append(f"{path}.id: nonblank stable ID expected (ASCII letters, digits, _ or -)")
        elif nid in seen:
            errors.append(f"{path}.id: duplicate '{nid}'")
        else:
            seen.add(nid)
        for field in ("title", "text"):
            if field not in note or not isinstance(note[field], str):
                errors.append(f"{path}.{field}: must be a string")
        if not note.get("title") and not note.get("text"):
            warnings.append(f"{path}: both title and summary are empty")
        if isinstance(note.get("title"), str) and len(note["title"].splitlines()[0]) > 42:
            warnings.append(f"{path}.title: long first line may be hard to read on the canvas")
        if isinstance(note.get("text"), str) and len(note["text"]) > 160:
            warnings.append(f"{path}.text: summary is long; put details in the popup source")
        color = note.get("color")
        if not isinstance(color, str) or color not in COLORS:
            errors.append(f"{path}.color: use one of {', '.join(COLORS)}")
        for field in ("x", "y", "w", "z"):
            value = note.get(field)
            if not is_finite_number(value):
                errors.append(f"{path}.{field}: expected finite number")
        if is_finite_number(note.get("w")) and note["w"] <= 0:
            errors.append(f"{path}.w: must be > 0")
        if is_finite_number(note.get("z")):
            z = note["z"]
            if not isinstance(z, int) or isinstance(z, bool) or z < 0:
                errors.append(f"{path}.z: expected non-negative integer")
            else:
                zs.append(z)
        if note_type == "markdown":
            source = note.get("markdownSource")
            if not isinstance(source, str) or not source.strip():
                errors.append(f"{path}.markdownSource: must contain Markdown")
            inline = note.get("inline", "")
            if inline and inline != source:
                warnings.append(f"{path}.inline differs from markdownSource; keep them in sync")
        elif note_type in ("code", "mermaid"):
            source = note.get("inline")
            if not isinstance(source, str) or not source.strip():
                errors.append(f"{path}.inline: must contain source text")
            if note_type == "code" and not isinstance(note.get("language"), str):
                errors.append(f"{path}.language: code language string required")
            if note_type == "mermaid" and isinstance(source, str) and not source.lstrip().startswith((
                "sequenceDiagram", "flowchart", "graph", "classDiagram", "stateDiagram",
                "erDiagram", "gantt", "journey", "pie", "mindmap", "timeline", "quadrantChart",
                "gitGraph", "C4", "requirementDiagram", "sankey", "xychart", "block",
                "architecture", "packet", "kanban", "zenuml", "treemap", "radar", "title",
                "---",
            )):
                warnings.append(f"{path}.inline: Mermaid diagram header not recognized; check syntax")
        elif note_type == "image":
            url = note.get("imageUrl")
            if not isinstance(url, str) or not url.strip():
                errors.append(f"{path}.imageUrl: nonblank image URL is required")
            elif not (url.startswith("data:image/") or (
                urlparse(url).scheme in ("http", "https") and urlparse(url).netloc
            )):
                errors.append(f"{path}.imageUrl: expected HTTPS/HTTP or data:image URI")
            elif url.startswith("http://"):
                warnings.append(f"{path}.imageUrl: HTTPS is recommended")

    if len(zs) == len(notes) and sorted(zs) != list(range(len(notes))):
        warnings.append("z: recommend contiguous stacking order 0..N-1")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path, help="KJ Board JSON file to validate")
    parser.add_argument("--strict", action="store_true", help="Reject obsolete top-level groups/edges")
    args = parser.parse_args()
    try:
        board = json.loads(args.board.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors, warnings = validate_board(board, strict=args.strict)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Validated {args.board}: {len(board.get('notes', [])) if isinstance(board, dict) and isinstance(board.get('notes'), list) else 0} notes, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
