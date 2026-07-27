from collections import Counter
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / "core" / "rules"


class RuleRoutingTests(unittest.TestCase):
    def test_agents_routes_every_core_rule_exactly_once(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        routed = re.findall(r"\[[^\]]+\]\((core/rules/[^)]+\.md)\)", agents)
        expected = {
            path.relative_to(ROOT).as_posix()
            for path in RULES_DIR.glob("*.md")
        }

        self.assertEqual(expected, set(routed))
        self.assertEqual(
            {path: 1 for path in expected},
            dict(Counter(routed)),
        )

        for relative_path in routed:
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

    def test_every_core_rule_declares_routing_metadata(self):
        for path in RULES_DIR.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertRegex(text, r"(?m)^- Purpose:")
                self.assertRegex(text, r"(?m)^- Read when:")
                self.assertRegex(text, r"(?m)^- Authority:")

    def test_agents_routes_extension_entry_point(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertRegex(
            agents,
            r"\[[^\]]+\]\(extension/README\.md\)",
        )

    def test_obsidian_contract_requires_connected_rule_nodes(self):
        contract = (
            ROOT / "core" / "docs" / "obsidian" / "OBSIDIAN_REVIEW_CONTRACT.md"
        ).read_text(encoding="utf-8")
        self.assertIn("활성 `core/rules/*.md` 각각을 정확히 한 번", contract)
        self.assertIn("고아 node로 남기지 않는다", contract)


if __name__ == "__main__":
    unittest.main()
