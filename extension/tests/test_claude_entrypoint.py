from __future__ import annotations

from pathlib import Path
import unittest


class ClaudeEntrypointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]
        cls.text = (cls.root / "CLAUDE.md").read_text(encoding="utf-8")

    def test_required_entrypoints_are_referenced_exactly_once(self) -> None:
        lines = self.text.splitlines()
        self.assertEqual(lines.count("@core/PROJECT_RULES.md"), 1)
        self.assertEqual(lines.count("@PROJECT_RULES.md"), 1)
        self.assertEqual(lines.count("@SESSION_HANDOFF.md"), 1)
        self.assertNotIn("@AGENTS.md", self.text)

    def test_entrypoint_contains_only_the_three_contract_pointers(self) -> None:
        nonempty_lines = [line for line in self.text.splitlines() if line.strip()]
        self.assertEqual(
            [
                "# Claude Entry",
                "Read these files completely in order before any action:",
                "@core/PROJECT_RULES.md",
                "@PROJECT_RULES.md",
                "@SESSION_HANDOFF.md",
            ],
            nonempty_lines,
        )

    def test_entrypoint_owns_no_project_routing(self) -> None:
        self.assertNotIn("AINOTEBOOK_WORKTREE_STATE.md", self.text)
        self.assertNotIn("core/rules/", self.text)
        self.assertNotIn("extension/README.md", self.text)
        self.assertNotIn("## Claude tool mapping", self.text)


if __name__ == "__main__":
    unittest.main()
