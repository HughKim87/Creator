"""Governance checks for Obsidian properties, domain folders, and context limits."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/agent/navigation/DOCUMENT_REGISTRY.md"
BASE = ROOT / "docs/agent/navigation/AGENT_DOCUMENTS.base"
ROOT_CONTROLS = (
    ROOT / "AGENTS.md",
    ROOT / "PROJECT_RULES.md",
    ROOT / "SESSION_HANDOFF.md",
)
ROOT_METADATA = (
    "- Purpose:",
    "- Scope:",
    "- Audience and language:",
    "- Read when:",
    "- Write when:",
    "- Authority:",
)
PROPERTY_KEYS = {
    "doc_id",
    "kind",
    "domain",
    "lifecycle",
    "authority",
    "audience",
    "language",
    "validation",
    "purpose",
    "scope",
    "read_when",
    "write_when",
}
DOMAIN_FOLDERS = {
    "navigation": "docs/agent/navigation/",
    "rebuild": "docs/agent/rebuild/",
    "workflow": "docs/agent/workflow/",
    "tooling": "docs/agent/tooling/",
    "state": "docs/agent/state/",
    "user_status": "docs/user/",
    "history": "docs/reports/",
}


def managed_markdown() -> list[Path]:
    return sorted((ROOT / "docs").rglob("*.md"))


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"missing YAML frontmatter: {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError(f"unclosed YAML frontmatter: {path}") from exc
    result: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator or not key or not value.strip():
            raise AssertionError(f"invalid property line in {path}: {line!r}")
        result[key.strip()] = value.strip().strip('"')
    return result


def prose_without_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`]*`", "", text)


class DocumentGovernanceTests(unittest.TestCase):
    def test_every_managed_note_has_unique_complete_properties(self) -> None:
        seen: dict[str, Path] = {}
        for path in managed_markdown():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                properties = frontmatter(path)
                self.assertTrue(PROPERTY_KEYS.issubset(properties), PROPERTY_KEYS - properties.keys())
                doc_id = properties["doc_id"]
                self.assertRegex(doc_id, r"^doc\.[a-z0-9_]+$")
                self.assertNotIn(doc_id, seen, f"duplicate {doc_id}: {seen.get(doc_id)}")
                seen[doc_id] = path

    def test_properties_match_domain_folders(self) -> None:
        for path in managed_markdown():
            relative = path.relative_to(ROOT).as_posix()
            properties = frontmatter(path)
            with self.subTest(path=relative):
                self.assertIn(properties["domain"], DOMAIN_FOLDERS)
                self.assertTrue(relative.startswith(DOMAIN_FOLDERS[properties["domain"]]))
                if properties["lifecycle"] == "active" and relative.startswith("docs/agent/"):
                    self.assertEqual(properties["language"], "en")

    def test_root_controls_keep_compact_metadata(self) -> None:
        for path in ROOT_CONTROLS:
            with self.subTest(path=path.name):
                header = "\n".join(path.read_text(encoding="utf-8").splitlines()[:10])
                for field in ROOT_METADATA:
                    self.assertIn(field, header)

    def test_registered_assets_exist_and_all_managed_files_are_clean_utf8(self) -> None:
        assets = [BASE, ROOT / "docs/agent/state/schemas/video_task_state.schema.json"]
        for path in [*ROOT_CONTROLS, *managed_markdown(), *assets]:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertTrue(path.is_file())
                raw = path.read_bytes()
                self.assertNotIn(b"\x00", raw)
                self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
                raw.decode("utf-8")

    def test_local_markdown_links_resolve(self) -> None:
        link_pattern = re.compile(r"\[[^]]+\]\((?!https?://|#)([^)#]+)(?:#[^)]+)?\)")
        for path in [*ROOT_CONTROLS, *managed_markdown()]:
            for target in link_pattern.findall(path.read_text(encoding="utf-8")):
                with self.subTest(path=path.name, target=target):
                    self.assertTrue((path.parent / target).resolve().is_file())

    def test_agent_and_user_language_boundaries(self) -> None:
        for path in (ROOT / "docs/agent").rglob("*.md"):
            with self.subTest(path=path.name):
                self.assertIsNone(re.search(r"[가-힣]", prose_without_code(path.read_text(encoding="utf-8"))))
        for path in [*(ROOT / "docs/user").glob("*.md"), *(ROOT / "docs/reports").glob("*.md")]:
            with self.subTest(path=path.name):
                properties = frontmatter(path)
                self.assertEqual(properties["language"], "ko")
                self.assertIsNotNone(re.search(r"[가-힣]", path.read_text(encoding="utf-8")))

    def test_reports_are_evidence_not_execution_authorities(self) -> None:
        for path in (ROOT / "docs/reports").glob("*.md"):
            with self.subTest(path=path.name):
                properties = frontmatter(path)
                self.assertEqual(properties["kind"], "report")
                self.assertIn(properties["lifecycle"], {"historical", "superseded"})
                self.assertIn("evidence", properties["authority"])

    def test_obsidian_base_is_derived_and_bounded(self) -> None:
        registry = REGISTRY.read_text(encoding="utf-8")
        base = BASE.read_text(encoding="utf-8")
        self.assertNotIn("## Registered documents", registry)
        self.assertIn("generated view, not another source of truth", registry)
        for view in ("Navigation", "Rebuild", "Workflow", "Tooling", "State", "Historical evidence"):
            self.assertIn(f"name: {view}", base)
        for forbidden in ("inputs/", "outputs/", "backup/", ".git/"):
            self.assertNotIn(forbidden, base)

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
        reconstruction = (ROOT / "docs/agent/rebuild/RECONSTRUCTION_MAP.md").read_text(encoding="utf-8")
        row = next(line for line in reconstruction.splitlines() if line.startswith("| Graphify document discovery"))
        self.assertIn("| excluded |", row)

    def test_official_obsidian_discovery_is_direct_property_and_base_bounded(self) -> None:
        for relative_path in (
            "tools/obsidian_document_search.py",
            "tests/test_obsidian_document_search.py",
        ):
            self.assertFalse((ROOT / relative_path).exists(), relative_path)
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        requirements = (ROOT / "docs/agent/tooling/TOOL_REQUIREMENTS.md").read_text(encoding="utf-8")
        self.assertIn("call the official Obsidian CLI directly", agents)
        self.assertIn("base:query path='docs/agent/navigation/AGENT_DOCUMENTS.base'", requirements)
        self.assertIn("limit=3 format=json", requirements)
        self.assertIn("property:read", requirements)
        self.assertIn("Do not silently fall back", requirements)

    def test_handoff_contains_no_dynamic_git_snapshot(self) -> None:
        handoff = (ROOT / "SESSION_HANDOFF.md").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"(?i)\b(ahead|behind|dirty|uncommitted)\b|미커밋", handoff))
        self.assertIsNone(re.search(r"\b[0-9a-f]{7,40}\b", handoff))

    def test_rebuild_plan_requires_archive_independence(self) -> None:
        plan = (ROOT / "docs/agent/rebuild/REBUILD_PLAN.md").read_text(encoding="utf-8")
        self.assertIn("## Backup independence rule", plan)
        self.assertIn("temporary migration input", plan)
        self.assertIn("A layer is incomplete", plan)
        self.assertIn("## Archive-retirement gate", plan)
        self.assertIn("separate explicit user request", plan)

    def test_active_execution_sources_do_not_route_to_migration_archive(self) -> None:
        forbidden_path = "back" + "up/"
        active_documents = [ROOT / "AGENTS.md", *(ROOT / "docs/agent").rglob("*.md")]
        for path in active_documents:
            if path == ROOT / "docs/agent/rebuild/REBUILD_PLAN.md":
                continue
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(forbidden_path, text)
                self.assertNotIn("INHERITANCE" + "_MAP.md", text)
        for path in [*(ROOT / "tools").glob("*.py"), *(ROOT / "tests").glob("*.py")]:
            if path.name == Path(__file__).name:
                continue
            with self.subTest(path=path.name):
                self.assertNotIn(forbidden_path, path.read_text(encoding="utf-8"))

    def test_control_documents_stay_within_context_budgets(self) -> None:
        for name, maximum in {"AGENTS.md": 100, "PROJECT_RULES.md": 120, "SESSION_HANDOFF.md": 70}.items():
            with self.subTest(name=name):
                self.assertLessEqual(len((ROOT / name).read_text(encoding="utf-8").splitlines()), maximum)

    def test_old_flat_agent_locations_are_absent(self) -> None:
        old_paths = (
            "docs/agent/DOCUMENT_REGISTRY.md",
            "docs/agent/REBUILD_PRINCIPLES.md",
            "docs/agent/REBUILD_PLAN.md",
            "docs/agent/RECONSTRUCTION_MAP.md",
            "docs/agent/FILE_DATA_CONTRACT.md",
            "docs/agent/WORKFLOW_FOUNDATION.md",
            "docs/agent/EDITING_QUALITY_RULES.md",
            "docs/agent/TOOL_REQUIREMENTS.md",
            "docs/agent/SKILL_REQUIREMENTS.md",
            "docs/agent/schemas/video_task_state.schema.json",
        )
        for relative_path in old_paths:
            self.assertFalse((ROOT / relative_path).exists(), relative_path)


if __name__ == "__main__":
    unittest.main()
