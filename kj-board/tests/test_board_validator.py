"""Small standard-library test suite for the bundled authoring validator."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "skills/kj-board-authoring/scripts/validate_board.py"
SAMPLE = ROOT / "skills/kj-board-authoring/references/reference-board.json"
spec = importlib.util.spec_from_file_location("kj_board_validator", VALIDATOR)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class TestBoardValidator(unittest.TestCase):
    def setUp(self):
        self.board = json.loads(SAMPLE.read_text(encoding="utf-8"))

    def test_reference_board_is_valid(self):
        errors, warnings = validator.validate_board(self.board, strict=True)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_imported_sequence_diagram_reference(self):
        """Imported original skill example retains 4 steps x 3 media cards."""
        self.assertEqual(len(self.board["notes"]), 12)
        self.assertEqual(set(self.board), {"title", "notes"})
        for i, note in enumerate(self.board["notes"]):
            self.assertEqual(note["type"], ("markdown", "code", "mermaid")[i % 3])
            self.assertEqual(note["x"], 80 + (i % 3) * 270)
            self.assertEqual(note["y"], 180 + (i // 3) * 240)
            if note["type"] == "markdown":
                self.assertEqual(note["markdownSource"], note["inline"])
            elif note["type"] == "mermaid":
                self.assertTrue(note["inline"].startswith("sequenceDiagram"))

    def test_unsupported_type_is_rejected(self):
        self.board["notes"][0]["type"] = "text"
        errors, _ = validator.validate_board(self.board, strict=True)
        self.assertTrue(any("type" in message for message in errors))

    def test_duplicate_identifier_is_rejected(self):
        self.board["notes"][1]["id"] = self.board["notes"][0]["id"]
        errors, _ = validator.validate_board(self.board, strict=True)
        self.assertTrue(any("duplicate" in message for message in errors))

    def test_legacy_groups_are_rejected_in_strict_mode(self):
        self.board["groups"] = []
        errors, _ = validator.validate_board(self.board, strict=True)
        self.assertTrue(any("groups" in message for message in errors))

    def test_unhashable_type_is_rejected_gracefully(self):
        self.board["notes"][0]["type"] = []
        errors, _ = validator.validate_board(self.board, strict=True)
        self.assertTrue(any("type" in message for message in errors))


if __name__ == "__main__":
    unittest.main()
