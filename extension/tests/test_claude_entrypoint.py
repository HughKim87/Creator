from __future__ import annotations

from pathlib import Path
import unittest


class ClaudeEntrypointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]
        cls.text = (cls.root / "CLAUDE.md").read_text(encoding="utf-8")

    def test_project_rules_entrypoint_is_referenced_exactly_once(self) -> None:
        self.assertEqual(self.text.count("@PROJECT_RULES.md"), 1)
        self.assertNotIn("@AGENTS.md", self.text)

    def test_entrypoint_contains_only_the_project_rules_pointer(self) -> None:
        nonempty_lines = [line for line in self.text.splitlines() if line.strip()]
        self.assertEqual(
            ["# Claude Entry Point", "@PROJECT_RULES.md"],
            nonempty_lines,
        )

    def test_entrypoint_owns_no_project_routing(self) -> None:
        self.assertNotIn("SESSION_HANDOFF.md", self.text)
        self.assertNotIn("AINOTEBOOK_WORKTREE_STATE.md", self.text)
        self.assertNotIn("core/rules/", self.text)
        self.assertNotIn("extension/README.md", self.text)
        self.assertNotIn("## Claude tool mapping", self.text)


if __name__ == "__main__":
    unittest.main()
