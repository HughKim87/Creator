"""Regression checks for the three L3 minimum document profiles."""

from __future__ import annotations

import unittest
from pathlib import Path


AGENTS_PATH = Path(__file__).resolve().parents[1] / "AGENTS.md"


def profile_cells(profile: str) -> list[str]:
    prefix = f"| `{profile}` |"
    for line in AGENTS_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return [cell.strip() for cell in line.strip("|").split("|")]
    raise AssertionError(f"missing routing profile {profile!r}")


class DocumentRoutingTests(unittest.TestCase):
    def test_resume_profile_reads_only_global_rules_and_current_state(self) -> None:
        cells = profile_cells("resume_current_work")
        read_set = cells[1]
        exclusions = cells[3]
        self.assertIn("`AGENTS.md`", read_set)
        self.assertIn("`PROJECT_RULES.md`", read_set)
        self.assertIn("`SESSION_HANDOFF.md`", read_set)
        self.assertNotIn("REBUILD_PLAN", read_set)
        self.assertIn("Plans", exclusions)
        self.assertIn("reports", exclusions)

    def test_document_route_profile_is_affected_file_only(self) -> None:
        cells = profile_cells("change_document_route")
        read_set = cells[1]
        write_set = cells[2]
        exclusions = cells[3]
        self.assertIn("`docs/agent/DOCUMENT_REGISTRY.md`", read_set)
        self.assertIn("affected active documents", read_set)
        self.assertIn("affected authorities only", write_set)
        self.assertIn("Unrelated documents", exclusions)
        self.assertIn("user data", exclusions)

    def test_video_state_profile_is_exact_task_only(self) -> None:
        cells = profile_cells("handle_video_task_state")
        read_set = cells[1]
        write_set = cells[2]
        exclusions = cells[3]
        self.assertIn("`docs/agent/FILE_DATA_CONTRACT.md`", read_set)
        self.assertIn("exact designated `state.json`", read_set)
        self.assertIn("Designated state", write_set)
        self.assertIn("Other tasks", exclusions)
        self.assertIn("rebuild documents", exclusions)


if __name__ == "__main__":
    unittest.main()
