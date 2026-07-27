from collections import Counter
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / "core" / "rules"


class RuleRoutingTests(unittest.TestCase):
    def test_project_rules_routes_every_core_rule_exactly_once(self):
        project_rules = (ROOT / "PROJECT_RULES.md").read_text(encoding="utf-8")
        routed = re.findall(
            r"\[[^\]]+\]\((core/rules/[^)]+\.md)\)",
            project_rules,
        )
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

    def test_project_rules_routes_extension_entry_point(self):
        project_rules = (ROOT / "PROJECT_RULES.md").read_text(encoding="utf-8")
        self.assertRegex(
            project_rules,
            r"\[[^\]]+\]\(extension/README\.md\)",
        )

    def test_agents_is_only_a_project_rules_pointer(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", agents)

        self.assertEqual(["PROJECT_RULES.md"], links)
        self.assertNotIn("core/rules/", agents)
        self.assertNotIn("extension/README.md", agents)
        self.assertNotIn("SESSION_HANDOFF.md", agents)
        self.assertNotIn("AINOTEBOOK_WORKTREE_STATE.md", agents)
        self.assertNotIn("## Startup", agents)
        self.assertNotIn("## Classify", agents)

    def test_project_rules_selects_one_state_document_from_root_name(self):
        project_rules = (ROOT / "PROJECT_RULES.md").read_text(encoding="utf-8")
        ainotebook_match = re.search(
            r'`root_name == "ainotebook"`.*?`(extension/work/'
            r'AINOTEBOOK_WORKTREE_STATE\.md)`',
            project_rules,
        )
        default_match = re.search(
            r'`root_name != "ainotebook"`.*?`(SESSION_HANDOFF\.md)`',
            project_rules,
        )

        self.assertIsNotNone(ainotebook_match)
        self.assertIsNotNone(default_match)
        self.assertIn("git rev-parse --show-toplevel", project_rules)
        self.assertIn("case-insensitively", project_rules)
        self.assertIn("Do not use the branch name", project_rules)

        routes = {
            "ainotebook": ainotebook_match.group(1),
            "default": default_match.group(1),
        }

        def select_state_document(root: str) -> str:
            normalized = root.replace("\\", "/").rstrip("/").casefold()
            root_name = normalized.rsplit("/", 1)[-1]
            return routes["ainotebook"] if root_name == "ainotebook" else routes["default"]

        self.assertEqual(
            "extension/work/AINOTEBOOK_WORKTREE_STATE.md",
            select_state_document("C:\\Workspace\\AINOTEBOOK\\"),
        )
        self.assertEqual(
            "SESSION_HANDOFF.md",
            select_state_document(r"C:\Workspace\김실버유튜브"),
        )

    def test_obsidian_contract_requires_connected_rule_nodes(self):
        contract = (
            ROOT / "core" / "docs" / "obsidian" / "OBSIDIAN_REVIEW_CONTRACT.md"
        ).read_text(encoding="utf-8")
        self.assertIn("활성 `core/rules/*.md` 각각을 정확히 한 번", contract)
        self.assertIn("고아 node로 남기지 않는다", contract)


if __name__ == "__main__":
    unittest.main()
