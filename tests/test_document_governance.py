"""Governance checks for active document placement, metadata, and context size."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/agent/DOCUMENT_REGISTRY.md"
AGENT_ROOT_DOCUMENTS = (
    ROOT / "AGENTS.md",
    ROOT / "PROJECT_RULES.md",
    ROOT / "SESSION_HANDOFF.md",
)
AGENT_METADATA = (
    "- Purpose:",
    "- Scope:",
    "- Audience and language:",
    "- Read when:",
    "- Write when:",
    "- Authority:",
)
USER_METADATA = (
    "- 사용 목적:",
    "- 사용 범위:",
    "- 독자·언어:",
    "- 읽는 시점:",
    "- 수정하는 시점:",
    "- 정본 여부:",
)


def registered_paths() -> set[str]:
    paths: set[str] = set()
    pattern = re.compile(r"^\| `doc\.[^`]+` \| `([^`]+)` \|")
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            paths.add(match.group(1))
    return paths


def prose_without_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`]*`", "", text)


class DocumentGovernanceTests(unittest.TestCase):
    def test_every_active_document_is_registered_and_exists(self) -> None:
        registered = registered_paths()
        actual_markdown = {
            path.relative_to(ROOT).as_posix() for path in ROOT.glob("*.md")
        }
        actual_markdown.update(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "docs").rglob("*.md")
        )
        self.assertEqual(actual_markdown, {p for p in registered if p.endswith(".md")})
        for relative_path in registered:
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

    def test_registered_documents_are_clean_utf8(self) -> None:
        for relative_path in registered_paths():
            with self.subTest(path=relative_path):
                raw = (ROOT / relative_path).read_bytes()
                self.assertNotIn(b"\x00", raw)
                self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
                raw.decode("utf-8")

    def test_local_markdown_links_resolve(self) -> None:
        link_pattern = re.compile(r"\[[^]]+\]\((?!https?://|#)([^)#]+)(?:#[^)]+)?\)")
        markdown_paths = [ROOT / path for path in registered_paths() if path.endswith(".md")]
        for path in markdown_paths:
            for target in link_pattern.findall(path.read_text(encoding="utf-8")):
                with self.subTest(path=path.name, target=target):
                    self.assertTrue((path.parent / target).resolve().is_file())

    def test_agent_documents_have_english_governance_metadata(self) -> None:
        agent_documents = list(AGENT_ROOT_DOCUMENTS)
        agent_documents.extend((ROOT / "docs/agent").glob("*.md"))
        for path in agent_documents:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                header = "\n".join(text.splitlines()[:10])
                for field in AGENT_METADATA:
                    self.assertIn(field, header)
                self.assertIsNone(re.search(r"[가-힣]", prose_without_code(text)))

    def test_user_documents_have_korean_governance_metadata(self) -> None:
        user_documents = list((ROOT / "docs/user").glob("*.md"))
        user_documents.extend((ROOT / "docs/reports").glob("*.md"))
        for path in user_documents:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                header = "\n".join(text.splitlines()[:12])
                for field in USER_METADATA:
                    self.assertIn(field, header)
                self.assertIsNotNone(re.search(r"[가-힣]", header))

    def test_reports_are_not_registered_as_execution_authorities(self) -> None:
        registry = REGISTRY.read_text(encoding="utf-8")
        for report in (
            "doc.structure_report",
            "doc.rebuild_report",
            "doc.graphify_adoption_failure_report",
        ):
            row = next(
                line for line in registry.splitlines() if line.startswith(f"| `{report}` |")
            )
            self.assertIn("| report |", row)
            self.assertIn("| evidence |", row)

    def test_graphify_is_excluded_from_active_routing(self) -> None:
        for relative_path in (
            ".graphifyignore",
            "tools/knowledge_navigation.py",
            "tools/route_task.ps1",
            "tests/test_knowledge_navigation.py",
        ):
            self.assertFalse((ROOT / relative_path).exists(), relative_path)

        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("Graphify", agents)
        self.assertNotIn("route_task.ps1", agents)

        reconstruction = (ROOT / "docs/agent/RECONSTRUCTION_MAP.md").read_text(
            encoding="utf-8"
        )
        graphify_row = next(
            line
            for line in reconstruction.splitlines()
            if line.startswith("| Graphify document discovery")
        )
        self.assertIn("| excluded |", graphify_row)

    def test_handoff_contains_no_dynamic_git_snapshot(self) -> None:
        handoff = (ROOT / "SESSION_HANDOFF.md").read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"(?i)\b(ahead|behind|dirty|uncommitted)\b|미커밋", handoff)
        )
        self.assertIsNone(re.search(r"\b[0-9a-f]{7,40}\b", handoff))

    def test_rebuild_plan_requires_archive_independence(self) -> None:
        plan = (ROOT / "docs/agent/REBUILD_PLAN.md").read_text(encoding="utf-8")
        self.assertIn("## Backup independence rule", plan)
        self.assertIn("temporary migration input", plan)
        self.assertIn("A layer is incomplete", plan)
        self.assertIn("## Archive-retirement gate", plan)
        self.assertIn("separate explicit user request", plan)

    def test_active_execution_sources_do_not_route_to_migration_archive(self) -> None:
        forbidden_path = "back" + "up/"
        active_execution_documents = (
            ROOT / "AGENTS.md",
            ROOT / "docs/agent/DOCUMENT_REGISTRY.md",
            ROOT / "docs/agent/REBUILD_PRINCIPLES.md",
            ROOT / "docs/agent/RECONSTRUCTION_MAP.md",
            ROOT / "docs/agent/FILE_DATA_CONTRACT.md",
            ROOT / "docs/agent/WORKFLOW_FOUNDATION.md",
            ROOT / "docs/agent/EDITING_QUALITY_RULES.md",
            ROOT / "docs/agent/TOOL_REQUIREMENTS.md",
            ROOT / "docs/agent/SKILL_REQUIREMENTS.md",
        )
        for path in active_execution_documents:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(forbidden_path, text)
                self.assertNotIn("INHERITANCE" + "_MAP.md", text)

        implementation_files = list((ROOT / "tools").glob("*.py"))
        implementation_files.extend(
            path
            for path in (ROOT / "tests").glob("*.py")
            if path.name != Path(__file__).name
        )
        for path in implementation_files:
            with self.subTest(path=path.name):
                self.assertNotIn(forbidden_path, path.read_text(encoding="utf-8"))

    def test_control_documents_stay_within_context_budgets(self) -> None:
        budgets = {
            "AGENTS.md": 100,
            "PROJECT_RULES.md": 120,
            "SESSION_HANDOFF.md": 70,
        }
        for name, maximum in budgets.items():
            with self.subTest(name=name):
                line_count = len((ROOT / name).read_text(encoding="utf-8").splitlines())
                self.assertLessEqual(line_count, maximum)

    def test_superseded_document_locations_are_absent(self) -> None:
        old_paths = (
            "PROJECT_STATUS.md",
            "PROJECT_STRUCTURE_ANALYSIS.md",
            "docs/FILE_DATA_CONTRACT.md",
            "docs/INHERITANCE_MAP.md",
            "docs/agent/INHERITANCE_MAP.md",
            "docs/REBUILD_EXECUTION_REPORT.md",
            "docs/REBUILD_PLAN.md",
            "docs/REBUILD_PRINCIPLES.md",
        )
        for relative_path in old_paths:
            self.assertFalse((ROOT / relative_path).exists(), relative_path)


if __name__ == "__main__":
    unittest.main()
