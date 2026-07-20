"""Regression checks for minimum routes after Obsidian-native optimization."""

from __future__ import annotations

import unittest
from pathlib import Path


AGENTS_PATH = Path(__file__).resolve().parents[1] / "AGENTS.md"


def route_cells(route_id: str) -> list[str]:
    prefix = f"| `{route_id}` |"
    lines = AGENTS_PATH.read_text(encoding="utf-8").splitlines()
    start = lines.index("## Task routing")
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith(prefix):
            return [cell.strip() for cell in line.strip("|").split("|")]
    raise AssertionError(f"missing task route {route_id!r}")


class DocumentRoutingTests(unittest.TestCase):
    def test_resume_route_has_no_document_delta(self) -> None:
        cells = route_cells("resume_current_work")
        self.assertEqual(cells[2], "None")
        self.assertIn("Plans", cells[4])
        self.assertIn("reports", cells[4])

    def test_document_move_and_classification_are_separate(self) -> None:
        move = route_cells("change_document_route")
        classification = route_cells("change_document_classification")
        self.assertIn("`docs/agent/navigation/DOCUMENT_PLACEMENT.md`", move[2])
        self.assertIn("Exact affected note properties and destination", move[3])
        self.assertIn("`docs/agent/navigation/DOCUMENT_REGISTRY.md`", classification[2])
        self.assertIn("Exact affected note properties or Base view", classification[3])

    def test_normal_state_operation_excludes_schema_internals(self) -> None:
        state = route_cells("handle_video_task_state")
        self.assertIn("`docs/agent/state/STATE_OPERATIONS.md`", state[2])
        self.assertIn("Exact designated task `state.json` and operation", state[3])
        self.assertIn("schema internals", state[4])
        schema = route_cells("change_video_state_contract")
        self.assertIn("`docs/agent/state/VIDEO_TASK_STATE.md`", schema[2])
        self.assertIn("video_task_state.schema.json", schema[2])

    def test_unknown_route_uses_one_obsidian_domain_and_reports_failure(self) -> None:
        agents = AGENTS_PATH.read_text(encoding="utf-8")
        self.assertIn("Use the table directly", agents)
        self.assertIn("official Obsidian CLI", agents)
        self.assertIn("narrowest Base domain view or domain folder", agents)
        self.assertIn("purpose` and `authority", agents)
        self.assertIn("do not guess, silently use direct routing", agents)
        self.assertIn("stop the unresolved part and report it", agents)
        self.assertIn("Do not expand from one selected document", agents)


if __name__ == "__main__":
    unittest.main()
