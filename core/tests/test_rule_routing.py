from collections import Counter
from pathlib import Path
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / "core" / "rules"


def _state_routes(project_rules: str) -> dict[str, str]:
    ainotebook_match = re.search(
        r'`root_name == "ainotebook"`.*?`(extension/work/'
        r'AINOTEBOOK_WORKTREE_STATE\.md)`',
        project_rules,
    )
    default_match = re.search(
        r'`root_name != "ainotebook"`.*?`(SESSION_HANDOFF\.md)`',
        project_rules,
    )
    if ainotebook_match is None or default_match is None:
        raise ValueError("state routes are incomplete")
    return {
        "ainotebook": ainotebook_match.group(1),
        "default": default_match.group(1),
    }


def _select_state_document(
    root: Path,
    project_rules: str,
    *,
    require_exists: bool = True,
) -> str:
    routes = _state_routes(project_rules)
    normalized = str(root).replace("\\", "/").rstrip("/").casefold()
    root_name = normalized.rsplit("/", 1)[-1]
    selected = routes["ainotebook"] if root_name == "ainotebook" else routes["default"]
    if require_exists and not (root / selected).is_file():
        raise FileNotFoundError(selected)
    return selected


def _state_owner_scope(text: str) -> str:
    if "ainotebook 이외 worktree" in text:
        return "default"
    if "ainotebook 워크트리의" in text:
        return "ainotebook"
    raise ValueError("state owner scope is not explicit")


def _validate_unique_owner_scopes(*documents: str) -> None:
    scopes = [_state_owner_scope(text) for text in documents]
    if len(scopes) != len(set(scopes)):
        raise ValueError("multiple state documents claim the same owner scope")


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

    def test_rule_governance_places_rules_by_reusable_trigger(self):
        governance = (
            ROOT / "core" / "rules" / "rule-governance.md"
        ).read_text(encoding="utf-8")
        self.assertIn("not from the path, report, domain task", governance)
        self.assertIn("applies unchanged across domains", governance)
        self.assertIn("split it before routing", governance)
        self.assertIn(
            "not a reason to place a foundation rule in extension",
            governance,
        )
        self.assertIn(
            "Core and extension rule files must not route each other",
            governance,
        )

    def test_project_rules_routes_extension_entry_point(self):
        project_rules = (ROOT / "PROJECT_RULES.md").read_text(encoding="utf-8")
        self.assertRegex(
            project_rules,
            r"\[[^\]]+\]\(extension/README\.md\)",
        )

    def test_design_documents_are_bounded_and_role_separated(self):
        document_work = (
            ROOT / "core" / "rules" / "document-work.md"
        ).read_text(encoding="utf-8")

        for role in ("`overall-design`", "`phase-design`", "`reference-evidence`"):
            self.assertIn(role, document_work)
        self.assertIn("120 lines and 8,000 Unicode characters", document_work)
        self.assertIn("160 lines and 12,000 Unicode characters", document_work)
        self.assertIn("must not be a startup-required read", document_work)
        self.assertIn("Treat a read-budget excess", document_work)

    def test_staged_work_has_one_active_phase_and_four_gates(self):
        staged = (
            ROOT / "core" / "rules" / "staged-work-design.md"
        ).read_text(encoding="utf-8")

        self.assertIn("at most one active `phase-design`", staged)
        self.assertIn("Do not create detailed documents for all future phases", staged)
        for gate in ("`entry gate`", "`slice gate`", "`exit gate`", "`transition gate`"):
            self.assertIn(gate, staged)
        self.assertIn(
            "[Staged work design](core/rules/staged-work-design.md)",
            (ROOT / "PROJECT_RULES.md").read_text(encoding="utf-8"),
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
        self.assertIn("git rev-parse --show-toplevel", project_rules)
        self.assertIn("case-insensitively", project_rules)
        self.assertIn("Do not use the branch name", project_rules)

        self.assertEqual(
            "extension/work/AINOTEBOOK_WORKTREE_STATE.md",
            _select_state_document(
                Path("C:\\Workspace\\AINOTEBOOK\\"),
                project_rules,
                require_exists=False,
            ),
        )
        self.assertEqual(
            "SESSION_HANDOFF.md",
            _select_state_document(
                Path(r"C:\Workspace\김실버유튜브"),
                project_rules,
                require_exists=False,
            ),
        )

    def test_obsidian_contract_requires_connected_rule_nodes(self):
        contract = (
            ROOT / "core" / "docs" / "obsidian" / "OBSIDIAN_REVIEW_CONTRACT.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`PROJECT_RULES.md`의 조건부 route", contract)
        self.assertIn("활성 `core/rules/*.md` 각각을 정확히 한 번", contract)
        self.assertIn("`AGENTS.md`는 core rule에 직접 연결하지 않고", contract)
        self.assertIn("고아 node로 남기지 않는다", contract)


class G4RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_rules = (ROOT / "PROJECT_RULES.md").read_text(encoding="utf-8")
        cls.agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        cls.claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        cls.master = (
            ROOT
            / "extension"
            / "reports"
            / "codex_2026-07-28_문서기반_지시준수와_워크트리상태관리_개선안.md"
        ).read_text(encoding="utf-8")

    def test_g4_s01_main_root_selects_only_session_handoff(self):
        self.assertEqual(
            "SESSION_HANDOFF.md",
            _select_state_document(ROOT, self.project_rules),
        )

    def test_g4_s02_ainotebook_root_selects_only_dedicated_state(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            root = Path(temp_directory) / "AINOTEBOOK"
            state = root / "extension" / "work" / "AINOTEBOOK_WORKTREE_STATE.md"
            state.parent.mkdir(parents=True)
            state.write_text(
                "- 역할: ainotebook 워크트리의 현재 상태 단일 owner\n",
                encoding="utf-8",
            )
            self.assertEqual(
                "extension/work/AINOTEBOOK_WORKTREE_STATE.md",
                _select_state_document(root, self.project_rules),
            )

    def test_g4_s03_state_selection_never_returns_both_documents(self):
        routes = _state_routes(self.project_rules)
        self.assertEqual(2, len(set(routes.values())))
        for root in (Path("main"), Path("ainotebook")):
            selected = _select_state_document(
                root,
                self.project_rules,
                require_exists=False,
            )
            self.assertIn(selected, routes.values())
            self.assertIsInstance(selected, str)

    def test_g4_s04_entrypoints_own_no_classification_or_routing(self):
        forbidden = (
            "root_name",
            "quick",
            "standard",
            "controlled",
            "core/rules/",
            "extension/README.md",
            "SESSION_HANDOFF.md",
            "AINOTEBOOK_WORKTREE_STATE.md",
        )
        for text in (self.agents, self.claude):
            for token in forbidden:
                self.assertNotIn(token, text)

    def test_g4_s05_entrypoints_link_only_project_rules(self):
        agents_links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", self.agents)
        claude_includes = re.findall(r"(?m)^@([^\s]+\.md)$", self.claude)
        self.assertEqual(["PROJECT_RULES.md"], agents_links)
        self.assertEqual(["PROJECT_RULES.md"], claude_includes)

    def test_g4_s06_project_rules_routes_all_active_rules_once(self):
        routed = re.findall(
            r"\[[^\]]+\]\((core/rules/[^)]+\.md)\)",
            self.project_rules,
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
        self.assertNotRegex(self.agents, r"\]\(core/rules/")

    def test_g4_s07_missing_selected_state_is_an_explicit_failure(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            root = Path(temp_directory) / "ainotebook"
            root.mkdir()
            with self.assertRaises(FileNotFoundError):
                _select_state_document(root, self.project_rules)

    def test_g4_s08_duplicate_single_owner_scope_is_rejected(self):
        session = (ROOT / "SESSION_HANDOFF.md").read_text(encoding="utf-8")
        dedicated = "- 역할: ainotebook 워크트리의 현재 상태 단일 owner\n"
        _validate_unique_owner_scopes(session, dedicated)
        duplicate = "- 역할: ainotebook 이외 worktree의 현재 상태 단일 owner\n"
        with self.assertRaises(ValueError):
            _validate_unique_owner_scopes(session, duplicate)

    def test_g4_s09_controlled_plan_invalidates_on_user_correction(self):
        self.assertIn("사용자가 의도 오해를 지적하면 즉시 중단한다.", self.master)
        self.assertIn(
            "기존 계획을 무효화하고 master를 갱신하기 전에는 다음 mutation을 실행하지 않는다.",
            self.master,
        )

    def test_g4_s10_destructive_git_requires_target_recovery_and_approval(self):
        version_control = (
            ROOT / "core" / "rules" / "version-control.md"
        ).read_text(encoding="utf-8")
        self.assertRegex(
            version_control,
            r"Before restore, clean, or overwrite.*exact target.*diff.*"
            r"recovery copy.*user approval",
        )

    def test_g4_s11_agent_proposal_is_not_user_authority(self):
        governance = (
            ROOT / "core" / "rules" / "rule-governance.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "An agent proposal does not become a user instruction or project policy",
            governance,
        )

    def test_g4_s12_incomplete_stage_has_selected_state_checkpoint(self):
        in_progress_rows = [
            line
            for line in self.master.splitlines()
            if line.startswith("|") and "| 진행 중 |" in line
        ]
        if in_progress_rows:
            self.assertEqual(1, len(in_progress_rows))
        else:
            completed_rows = [
                line
                for line in self.master.splitlines()
                if re.match(r"^\| [0-5] \| G[0-5](?:\s|\|)", line)
                and "| 완료 |" in line
            ]
            self.assertEqual(6, len(completed_rows))
        selected = _select_state_document(ROOT, self.project_rules)
        state = (ROOT / selected).read_text(encoding="utf-8")
        self.assertRegex(state, r"(?m)^- 상태: .+")
        next_action = state.split("## 첫 다음 행동", 1)
        self.assertEqual(2, len(next_action))
        self.assertRegex(next_action[1], r"(?m)^1\. .+")


if __name__ == "__main__":
    unittest.main()
