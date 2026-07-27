from __future__ import annotations

from pathlib import Path
import unittest


class ClaudeEntrypointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]
        cls.text = (cls.root / "CLAUDE.md").read_text(encoding="utf-8")

    def test_shared_entrypoint_is_referenced_exactly_once(self) -> None:
        self.assertEqual(self.text.count("@AGENTS.md"), 1)

    def test_current_owners_are_explicit_without_stale_handoff_claim(self) -> None:
        self.assertIn("`AGENTS.md` owns shared startup, classification, and routing", self.text)
        self.assertIn("`PROJECT_RULES.md` owns policy", self.text)
        self.assertIn("`SESSION_HANDOFF.md` owns current work state", self.text)
        self.assertNotIn("SESSION_HANDOFF.md` is large", self.text)

    def test_adapter_keeps_only_claude_specific_routing_constraints(self) -> None:
        self.assertIn("inputs", self.text)
        self.assertIn("outputs", self.text)
        self.assertIn("exact item and purpose", self.text)
        self.assertIn("`.agents/skills/`", self.text)
        self.assertIn("`extension/README.md`", self.text)
        self.assertEqual(self.text.count("## Claude tool mapping"), 1)


if __name__ == "__main__":
    unittest.main()
