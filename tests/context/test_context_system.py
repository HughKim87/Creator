"""Automated checks for the R-2A deterministic context system."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/context/context_system.py"
SPEC = importlib.util.spec_from_file_location("context_system", MODULE_PATH)
assert SPEC and SPEC.loader
context_system = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(context_system)


class ContextSystemTests(unittest.TestCase):
    def test_bootstrap_mapping_is_exact_8_plus_21(self) -> None:
        manifest = context_system.load_json(ROOT / "catalog/bootstrap.json")
        mapping = manifest["rule_mapping"]
        self.assertEqual(29, len(mapping))
        self.assertEqual(29, len({item["source"] for item in mapping}))
        self.assertEqual(29, len({item["rule_id"] for item in mapping}))
        self.assertEqual(8, sum(item["destination"] == "PROJECT_RULES.md" for item in mapping))
        self.assertEqual(21, sum(item["destination"] != "PROJECT_RULES.md" for item in mapping))

    def test_minimum_markdown_json_and_jsonl_unit_parsers(self) -> None:
        file_record = {
            "file_id": "file.fixture",
            "path": "fixture.md",
            "purpose": "Fixture",
            "owner": "test",
            "read_when": [],
            "write_when": [],
            "validators": [],
            "content_sha256": "0" * 64,
            "runtime_hash": None,
            "task_tags": [],
        }
        markdown = context_system.markdown_units("# Root\n\n## Child\nBody\n", file_record)
        json_units = context_system.json_pointer_units({"alpha": {"beta": 1}}, file_record)
        jsonl = context_system.jsonl_units([{"event_id": "event.fixture.0001", "value": 1}], file_record)
        self.assertEqual(2, len(markdown))
        self.assertEqual({"/", "/alpha", "/alpha/beta"}, {unit["locator"] for unit in json_units})
        self.assertEqual("record:event.fixture.0001", jsonl[0]["locator"])

    def test_protected_paths_are_rejected_before_traversal(self) -> None:
        for path in ("backup/item", "inputs/item", "outputs/item", ".git/config"):
            with self.assertRaises(context_system.ContextSystemError):
                context_system.assert_allowed_path(path, ROOT)

    def test_live_read_context_is_bounded_to_exact_heading(self) -> None:
        context = context_system.load_json(ROOT / "context/work/r2a_read.json")
        self.assertIsNone(context["write_contract"])
        self.assertIn("rule.retrieval.direct-routing-first", context["authority"]["selected_conditional_rule_ids"])
        workflow = next(item for item in context["read_manifest"] if item["path"] == "docs/agent/WORKFLOW.md")
        self.assertEqual(1, len(workflow["units"]))
        self.assertEqual(
            "unit.file.docs.agent.workflow.heading.common-work-workflow.5.-validate",
            workflow["units"][0]["unit_id"],
        )
        selected_paths = {item["path"] for item in context["read_manifest"]}
        self.assertNotIn("docs/reports/2026-07-20_R-1.1_지식_시스템_설계_보정.md", selected_paths)

    def test_write_without_contract_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "context/work").mkdir(parents=True)
            (root / "context/payloads").mkdir(parents=True)
            target = root / "target.md"
            target.write_text("original\n", encoding="utf-8")
            context = {
                "schema_version": "1.0.0",
                "context_id": "context.task.fixture",
                "request": {"task_id": "task.fixture", "write_payload_path": "context/payloads/payload.json"},
                "request_hash": "0" * 64,
                "write_contract": None,
            }
            payload = {
                "operations": [
                    {"target_path": "target.md", "operation": "replace_file", "content": "changed\n"}
                ]
            }
            (root / "context/work/context.json").write_text(json.dumps(context), encoding="utf-8")
            (root / "context/payloads/payload.json").write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(context_system.ContextSystemError):
                context_system.write_fixture(root, "context/work/context.json", "context/payloads/payload.json")
            self.assertEqual("original\n", target.read_text(encoding="utf-8"))

    def test_integrated_structural_validation_passes(self) -> None:
        result = context_system.validate_project(ROOT)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(0, result["counts"]["orphan_files"])


if __name__ == "__main__":
    unittest.main()
