"""Automated checks for the R-2A through R-5 deterministic context system."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


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
        live_rule_ids = {rule["rule_id"] for rule in context_system.parse_rule_packs(ROOT)}
        mapped_conditional_ids = {item["rule_id"] for item in mapping if item["destination"] != "PROJECT_RULES.md"}
        self.assertLessEqual(mapped_conditional_ids, live_rule_ids)
        self.assertIn("rule.validation.python-runtime-resolution", live_rule_ids)

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

    def test_context_artifacts_use_one_whole_file_unit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = {"nested": [{"index": index, "value": {"deep": True}} for index in range(100)]}
            for relative in (
                "context/requests/request.json",
                "context/work/work.json",
                "context/payloads/payload.json",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value), encoding="utf-8")
                record = context_system.classify_file(relative, root)
                units = context_system.extract_units_for_file(root, record)
                self.assertEqual("whole_file", record["unit_strategy"])
                self.assertEqual(1, len(units))

    def test_historical_backup_links_are_not_active_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "docs/report.md"
            document.parent.mkdir(parents=True)
            document.write_text(
                "[history](../backup/missing.md)\n[active](missing.md)\n",
                encoding="utf-8",
            )

            errors, count = context_system.validate_markdown_links(root, ["docs/report.md"])

            self.assertEqual(2, count)
            self.assertEqual(["broken local link: docs/report.md -> missing.md"], errors)

    def test_project_scan_excludes_context_system_transients(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog"
            catalog.mkdir()
            (catalog / "tmpghost").write_text("ghost", encoding="utf-8")
            (catalog / f"{context_system.ATOMIC_TEMP_PREFIX}ghost{context_system.ATOMIC_TEMP_SUFFIX}").write_text(
                "ghost", encoding="utf-8"
            )
            (catalog / context_system.REPOSITORY_LOCK_NAME).write_bytes(b"\0")
            (catalog / "kept.json").write_text("{}", encoding="utf-8")

            paths = context_system.iter_project_files(root)

            self.assertEqual(["catalog/kept.json"], paths)

    def test_repository_lock_blocks_a_second_process_and_recovers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ready = root / "ready"
            child_script = """
import importlib.util
import pathlib
import sys
import time

spec = importlib.util.spec_from_file_location("context_system_child", sys.argv[1])
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
with module.repository_lock(pathlib.Path(sys.argv[2]), timeout_seconds=5.0):
    pathlib.Path(sys.argv[3]).write_text("ready", encoding="utf-8")
    time.sleep(1.0)
"""
            process = subprocess.Popen(
                [sys.executable, "-c", child_script, str(MODULE_PATH), str(root), str(ready)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.monotonic() + 5.0
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(ready.exists(), "child process did not acquire repository lock")
                with self.assertRaisesRegex(context_system.ContextSystemError, "repository lock timeout"):
                    with context_system.repository_lock(root, timeout_seconds=0.1):
                        pass
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(0, process.returncode, stdout + stderr)
                with context_system.repository_lock(root, timeout_seconds=0.5):
                    pass
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)

    def test_repository_lock_releases_process_guard_when_setup_or_close_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def assert_another_thread_can_acquire() -> None:
                entered = threading.Event()
                failures = []

                def acquire_after_failure() -> None:
                    try:
                        with context_system.repository_lock(root, timeout_seconds=0.5):
                            entered.set()
                    except Exception as exc:  # pragma: no cover - asserted through failures
                        failures.append(exc)

                thread = threading.Thread(target=acquire_after_failure)
                thread.start()
                thread.join(timeout=2)
                self.assertTrue(entered.is_set(), failures)
                self.assertEqual([], failures)

            with mock.patch.object(Path, "open", side_effect=OSError("simulated lock-file open failure")):
                with self.assertRaisesRegex(OSError, "simulated lock-file open failure"):
                    with context_system.repository_lock(root, timeout_seconds=0.1):
                        pass
            assert_another_thread_can_acquire()

            real_open = Path.open

            class CloseFailureHandle:
                def __init__(self, wrapped):
                    self.wrapped = wrapped

                def __getattr__(self, name):
                    return getattr(self.wrapped, name)

                def close(self):
                    self.wrapped.close()
                    raise OSError("simulated lock-file close failure")

            def open_with_close_failure(path, *args, **kwargs):
                return CloseFailureHandle(real_open(path, *args, **kwargs))

            with mock.patch.object(Path, "open", autospec=True, side_effect=open_with_close_failure):
                with self.assertRaisesRegex(OSError, "simulated lock-file close failure"):
                    with context_system.repository_lock(root, timeout_seconds=0.1):
                        pass
            assert_another_thread_can_acquire()

    def test_atomic_write_retries_transient_permission_error_and_cleans_temp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "projection.jsonl"
            real_replace = context_system.os.replace
            calls = {"count": 0}

            def transient_replace(source, destination):
                calls["count"] += 1
                if calls["count"] < 3:
                    raise PermissionError(5, "simulated transient replace denial")
                return real_replace(source, destination)

            with mock.patch.object(context_system.os, "replace", side_effect=transient_replace):
                context_system.write_text_atomic(target, "ok\n")

            self.assertEqual(3, calls["count"])
            self.assertEqual("ok\n", target.read_text(encoding="utf-8"))
            self.assertEqual([], list(root.glob(f"{context_system.ATOMIC_TEMP_PREFIX}*")))

    def test_atomic_write_terminal_failure_cleans_temp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "projection.jsonl"
            with mock.patch.object(
                context_system.os,
                "replace",
                side_effect=PermissionError(5, "simulated persistent replace denial"),
            ):
                with self.assertRaises(PermissionError):
                    context_system.write_text_atomic(target, "blocked\n")

            self.assertFalse(target.exists())
            self.assertEqual([], list(root.glob(f"{context_system.ATOMIC_TEMP_PREFIX}*")))

    def test_atomic_write_reports_secondary_cleanup_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            temporary = root / "temporary.jsonl"
            temporary.write_text("blocked\n", encoding="utf-8")
            target = root / "projection.jsonl"
            with (
                mock.patch.object(
                    context_system.os,
                    "replace",
                    side_effect=PermissionError(5, "simulated persistent replace denial"),
                ),
                mock.patch.object(
                    Path,
                    "unlink",
                    side_effect=OSError(5, "simulated cleanup denial"),
                ),
            ):
                with self.assertRaises(context_system.ContextSystemError) as raised:
                    context_system._replace_atomic(temporary, target, attempts=1)

            self.assertIn("temporary cleanup failed", str(raised.exception))
            self.assertIsInstance(raised.exception.__cause__, PermissionError)

    def test_planned_file_id_distinguishes_same_stem_extensions(self) -> None:
        existing_path = "tools/runtime/run_python.ps1"
        catalog_record = context_system.classify_file("catalog/files.jsonl", ROOT)
        existing_record = context_system.classify_file(existing_path, ROOT)
        records = [catalog_record, existing_record]
        captured = {}

        def capture_records(_path, value):
            captured["records"] = value

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                mock.patch.object(context_system, "sync_catalog"),
                mock.patch.object(context_system, "load_file_catalog", return_value=records),
                mock.patch.object(context_system, "write_jsonl_atomic", side_effect=capture_records),
                mock.patch.object(context_system, "append_event", return_value={"event_id": "event.catalog-sync.test"}),
            ):
                result = context_system.plan_file(root, "tools/runtime/run_python.cmd")

        planned = next(record for record in captured["records"] if record["path"] == "tools/runtime/run_python.cmd")
        self.assertEqual("file.tools.runtime.run-python.cmd", result["file_id"])
        self.assertEqual(result["file_id"], planned["file_id"])

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

    def test_r2b_decisions_are_independent_and_approved(self) -> None:
        records = context_system.load_jsonl(ROOT / "catalog/records.jsonl")
        decisions = [record for record in records if record.get("record_kind") == "decision"]
        self.assertEqual(17, len(decisions))
        self.assertEqual({f"D-{number:02d}" for number in range(1, 18)}, {record["legacy_id"] for record in decisions})
        self.assertTrue(all(record["status"] == "accepted" for record in decisions))
        self.assertTrue(all(record["approval"]["approved_by"] == "user" for record in decisions))
        self.assertTrue(all(record["approval"]["evidence_source_id"] for record in decisions))

    def test_r2b_decision_evidence_fixture_traces_to_sources(self) -> None:
        context = context_system.load_json(ROOT / "context/work/r2b_decision_evidence.json")
        manifest = context["record_manifest"]
        selected = {item["record_id"]: item["record"] for item in manifest["records"]}
        self.assertIn("decision.r1.1.d14", selected)
        self.assertIn("knowledge.context.shared-work-context", selected)
        self.assertIn("source.repo.r1.1", selected)
        self.assertEqual("accepted", selected["decision.r1.1.d14"]["status"])
        self.assertEqual("verified", selected["knowledge.context.shared-work-context"]["status"])
        self.assertTrue(selected["source.repo.r1.1"]["locator"])
        self.assertFalse(any("reports/history" in rule_id for rule_id in context["authority"]["selected_conditional_rule_ids"]))

    def test_r2b_case_fixture_separates_symptom_and_resolution(self) -> None:
        context = context_system.load_json(ROOT / "context/work/r2b_case_resolution.json")
        selected = {item["record_id"]: item["record"] for item in context["record_manifest"]["records"]}
        case = selected["case.project.document-authority-duplication"]
        self.assertEqual("resolved", case["status"])
        self.assertEqual("confirmed", case["symptom"]["state"])
        self.assertEqual("resolved", case["resolution"]["state"])
        self.assertTrue(case["symptom"]["evidence"])
        self.assertTrue(case["resolution"]["evidence"])
        historical = selected["source.history.overview"]
        self.assertEqual("historical_candidate", historical["status"])
        self.assertFalse(historical["retrieval_eligible"])

    def test_relation_candidates_cannot_be_active_before_review(self) -> None:
        relations = context_system.load_jsonl(ROOT / "knowledge/relations.jsonl")
        candidates = [record for record in relations if record["status"] == "candidate"]
        self.assertTrue(candidates)
        self.assertTrue(all(record["review_status"] == "pending" for record in candidates))
        self.assertTrue(all(not record["retrieval_eligible"] for record in candidates))

    def test_r3_code_config_test_and_binary_sidecar_unit_adapters(self) -> None:
        base = {
            "file_id": "file.fixture",
            "path": "fixture.py",
            "purpose": "Fixture",
            "owner": "test",
            "read_when": [],
            "write_when": [],
            "validators": [],
            "content_sha256": "0" * 64,
            "runtime_hash": None,
            "task_tags": [],
        }
        code = context_system.code_symbol_units("class Alpha:\n    def run(self):\n        return 1\n", base)
        tests = context_system.code_symbol_units("def helper():\n    pass\n\ndef test_value():\n    assert True\n", base, tests_only=True)
        config = context_system.config_key_units("[service]\nport = 8080\n", base, ".toml")
        self.assertIn("symbol:Alpha.run", {unit["locator"] for unit in code})
        self.assertEqual({"symbol:test_value"}, {unit["locator"] for unit in tests})
        self.assertIn("key:service.port", {unit["locator"] for unit in config})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "asset.png"
            binary.write_bytes(b"PNG fixture")
            sidecar = root / "asset.png.sidecar.json"
            sidecar.write_text(json.dumps({"title": "fixture"}), encoding="utf-8")
            record = {**base, "path": "asset.png", "content_sha256": context_system.sha256_file(binary)}
            unit = context_system.binary_sidecar_unit(root, binary, record)
            self.assertEqual("binary_sidecar", unit["locator_type"])
            self.assertEqual("active", unit["status"])
            self.assertNotEqual(context_system.sha256_file(binary), unit["unit_hash"])

    def test_r3_lifecycle_move_and_delete_are_contract_gated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "context/work").mkdir(parents=True)
            (root / "context/payloads").mkdir(parents=True)
            source = root / "source.txt"
            source.write_text("value\n", encoding="utf-8")
            source_hash = context_system.sha256_file(source)
            context = {
                "request": {"task_id": "task.move", "write_payload_path": "context/payloads/move.json"},
                "request_hash": "1" * 64,
                "write_contract": {
                    "contract_id": "contract.task.move",
                    "request_hash": "1" * 64,
                    "allowed_actions": ["move"],
                    "targets": [
                        {"path": "source.txt", "status": "active", "before_file_hash": source_hash},
                        {"path": "moved.txt", "status": "planned", "before_file_hash": None},
                    ],
                },
            }
            payload = {"operations": [{"target_path": "source.txt", "destination_path": "moved.txt", "operation": "move_file"}]}
            (root / "context/work/move.json").write_text(json.dumps(context), encoding="utf-8")
            (root / "context/payloads/move.json").write_text(json.dumps(payload), encoding="utf-8")
            result = context_system.write_fixture(root, "context/work/move.json", "context/payloads/move.json")
            self.assertFalse(source.exists())
            self.assertEqual("value\n", (root / "moved.txt").read_text(encoding="utf-8"))
            self.assertTrue(result["event_id"].startswith("event.lifecycle-applied"))

            moved_hash = context_system.sha256_file(root / "moved.txt")
            context["request"] = {"task_id": "task.delete", "write_payload_path": "context/payloads/delete.json"}
            context["request_hash"] = "2" * 64
            context["write_contract"] = {
                "contract_id": "contract.task.delete",
                "request_hash": "2" * 64,
                "allowed_actions": ["delete"],
                "targets": [{"path": "moved.txt", "status": "active", "before_file_hash": moved_hash}],
            }
            (root / "context/work/delete.json").write_text(json.dumps(context), encoding="utf-8")
            (root / "context/payloads/delete.json").write_text(json.dumps({"operations": [{"target_path": "moved.txt", "operation": "delete_file"}]}), encoding="utf-8")
            context_system.write_fixture(root, "context/work/delete.json", "context/payloads/delete.json")
            self.assertFalse((root / "moved.txt").exists())

    def test_r3_partial_write_rolls_back_and_retry_is_linked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "context/work").mkdir(parents=True)
            (root / "context/payloads").mkdir(parents=True)
            for name in ("a.txt", "b.txt"):
                (root / name).write_text(f"{name}-before\n", encoding="utf-8")
            context = {
                "request": {"task_id": "task.retry", "write_payload_path": "context/payloads/retry.json"},
                "request_hash": "3" * 64,
                "write_contract": {
                    "contract_id": "contract.task.retry",
                    "request_hash": "3" * 64,
                    "allowed_actions": ["write"],
                    "targets": [
                        {"path": name, "status": "active", "before_file_hash": context_system.sha256_file(root / name)}
                        for name in ("a.txt", "b.txt")
                    ],
                },
            }
            payload = {"operations": [{"target_path": name, "operation": "replace_file", "content": f"{name}-after\n"} for name in ("a.txt", "b.txt")]}
            (root / "context/work/retry.json").write_text(json.dumps(context), encoding="utf-8")
            (root / "context/payloads/retry.json").write_text(json.dumps(payload), encoding="utf-8")
            original_commit = context_system._commit_operation
            calls = {"count": 0}

            def fail_second(*args):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("simulated commit failure")
                return original_commit(*args)

            with mock.patch.object(context_system, "_commit_operation", side_effect=fail_second):
                with self.assertRaises(context_system.ContextSystemError):
                    context_system.write_fixture(root, "context/work/retry.json", "context/payloads/retry.json")
            self.assertEqual("a.txt-before\n", (root / "a.txt").read_text(encoding="utf-8"))
            self.assertEqual("b.txt-before\n", (root / "b.txt").read_text(encoding="utf-8"))
            failed = context_system.load_jsonl(root / "records/work/events.jsonl")[-1]
            self.assertEqual("write_failed", failed["event_type"])
            self.assertEqual("success", failed["details"]["rollback"])
            payload["retry_of_event_id"] = failed["event_id"]
            (root / "context/payloads/retry.json").write_text(json.dumps(payload), encoding="utf-8")
            result = context_system.write_fixture(root, "context/work/retry.json", "context/payloads/retry.json")
            self.assertTrue(result["event_id"].startswith("event.write-retried"))
            self.assertEqual("a.txt-after\n", (root / "a.txt").read_text(encoding="utf-8"))

    def test_r3_knowledge_candidate_review_and_supersession(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ("knowledge", "schemas", "operations"):
                (root / path).mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "schemas/knowledge.schema.json", root / "schemas/knowledge.schema.json")
            source = {"source_id": "source.fixture", "record_kind": "source"}
            context_system.write_jsonl_atomic(root / "knowledge/sources.jsonl", [source])
            for path in ("items.jsonl", "relations.jsonl", "reviews.jsonl", "revisions.jsonl"):
                (root / "knowledge" / path).write_text("", encoding="utf-8")
            timestamp = "2026-07-21T01:00:00+09:00"

            def candidate(knowledge_id: str, statement: str) -> dict:
                return {
                    "schema_version": "1.0.0", "record_kind": "knowledge", "knowledge_id": knowledge_id,
                    "title": knowledge_id, "language": "en", "classification": "fact", "statement": statement,
                    "created_at": timestamp, "updated_at": timestamp, "author": "test", "status": "candidate",
                    "confidence": "medium", "confidence_basis": "fixture", "validated_by": "", "validated_at": "",
                    "source_refs": [{"source_id": "source.fixture", "locator": "fixture"}], "relation_ids": [],
                    "validity_scope": "test", "last_checked_at": timestamp, "review_policy": "event_driven",
                    "review_due_at": None, "review_triggers": ["source_change"], "revision": 1,
                    "retrieval_eligible": False, "task_tags": ["fixture"],
                }

            create = {"operation_id": "op.create", "task_id": "task.knowledge", "action": "create_candidate", "actor": "test", "timestamp": timestamp, "reason": "fixture", "record": candidate("knowledge.fixture.one", "one")}
            (root / "operations/create.json").write_text(json.dumps(create), encoding="utf-8")
            context_system.maintain_knowledge(root, "operations/create.json")
            current = context_system.load_jsonl(root / "knowledge/items.jsonl")[0]
            verify = {"operation_id": "op.verify", "task_id": "task.knowledge", "action": "review", "outcome": "verified", "knowledge_id": current["knowledge_id"], "expected_record_hash": context_system.sha256_text(context_system.canonical_json(current)), "expected_revision": 1, "actor": "test", "timestamp": timestamp, "reason": "verified fixture"}
            (root / "operations/verify.json").write_text(json.dumps(verify), encoding="utf-8")
            context_system.maintain_knowledge(root, "operations/verify.json")
            current = context_system.load_jsonl(root / "knowledge/items.jsonl")[0]
            self.assertEqual("verified", current["status"])
            self.assertTrue(current["retrieval_eligible"])
            supersede = {"operation_id": "op.supersede", "task_id": "task.knowledge", "action": "supersede", "knowledge_id": current["knowledge_id"], "expected_record_hash": context_system.sha256_text(context_system.canonical_json(current)), "expected_revision": 2, "actor": "test", "timestamp": timestamp, "reason": "replacement fixture", "replacement_record": candidate("knowledge.fixture.two", "two")}
            (root / "operations/supersede.json").write_text(json.dumps(supersede), encoding="utf-8")
            context_system.maintain_knowledge(root, "operations/supersede.json")
            items = {item["knowledge_id"]: item for item in context_system.load_jsonl(root / "knowledge/items.jsonl")}
            self.assertEqual("superseded", items["knowledge.fixture.one"]["status"])
            self.assertEqual("candidate", items["knowledge.fixture.two"]["status"])
            relation = context_system.load_jsonl(root / "knowledge/relations.jsonl")[0]
            self.assertEqual("supersedes", relation["relation_type"])
            self.assertEqual("pending", relation["review_status"])

    def test_r3_source_change_marks_dependents_needs_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "knowledge").mkdir()
            source_path = root / "source.md"
            source_path.write_text("before\n", encoding="utf-8")
            old_hash = context_system.sha256_file(source_path)
            source = {"source_id": "source.local", "source_type": "project_document", "locator": "source.md", "status": "active", "retrieval_eligible": True, "content_sha256": old_hash}
            item = {"knowledge_id": "knowledge.local", "status": "verified", "retrieval_eligible": True, "revision": 1, "updated_at": "old", "source_refs": [{"source_id": "source.local", "locator": "source.md"}]}
            context_system.write_jsonl_atomic(root / "knowledge/sources.jsonl", [source])
            context_system.write_jsonl_atomic(root / "knowledge/items.jsonl", [item])
            for name in ("reviews.jsonl", "revisions.jsonl"):
                (root / "knowledge" / name).write_text("", encoding="utf-8")
            source_path.write_text("after\n", encoding="utf-8")
            result = context_system.check_source_hashes(root)
            self.assertEqual(["source.local"], result["changed_source_ids"])
            self.assertEqual(["knowledge.local"], result["changed_knowledge_ids"])
            self.assertEqual("needs_review", context_system.load_jsonl(root / "knowledge/sources.jsonl")[0]["status"])
            changed_item = context_system.load_jsonl(root / "knowledge/items.jsonl")[0]
            self.assertEqual("needs_review", changed_item["status"])
            self.assertFalse(changed_item["retrieval_eligible"])
            changed_source = context_system.load_jsonl(root / "knowledge/sources.jsonl")[0]
            operation = {
                "operation_id": "op.source.accept", "task_id": "task.source.review",
                "source_id": "source.local",
                "expected_record_hash": context_system.sha256_text(context_system.canonical_json(changed_source)),
                "actor": "test", "timestamp": "2026-07-21T02:00:00+09:00",
                "reason": "Reviewed fixture change.", "outcome": "accept_current_hash",
            }
            (root / "source_review.json").write_text(json.dumps(operation), encoding="utf-8")
            context_system.maintain_source(root, "source_review.json")
            reviewed_source = context_system.load_jsonl(root / "knowledge/sources.jsonl")[0]
            self.assertEqual("active", reviewed_source["status"])
            self.assertEqual(context_system.sha256_file(source_path), reviewed_source["content_sha256"])

    def test_r3_session_generation_and_selection_reproduction(self) -> None:
        session = context_system.render_session_summary({
            "session_id": "session.fixture", "title": "Fixture Session", "date": "2026-07-21",
            "goal": "Verify rendering.", "scope": ["R-3"], "completed": ["Implemented"],
            "validation": ["passed"], "failures": [], "risks": [], "next_action": "Stop.",
            "path": "records/sessions/session.fixture.md",
        })
        handoff = context_system.render_handoff({
            "checkpoint": "R-3 complete.", "approval_state": "R-4 approved.", "completed": ["R-3"],
            "validation": ["passed"], "failure_ledger": [], "risks": [], "artifacts": ["artifact"],
            "next_actions": ["R-4"], "start_prompt": "Resume R-4.",
        })
        self.assertIn("## Failure ledger", session)
        self.assertIn("## Next-session start prompt", handoff)
        revisions = {"catalog": "a" * 64, "rules": "b" * 64}
        selections = {"files": ["file.a"], "rules": ["rule.a"], "units": [], "records": [], "relations": []}
        first = context_system.selection_fingerprint_for("c" * 64, revisions, selections)
        second = context_system.selection_fingerprint_for("c" * 64, revisions, selections)
        self.assertEqual(first, second)
        self.assertTrue(context_system._file_matches_metadata({"path": "tools/context/a.py", "kind": "code", "status": "active", "task_tags": ["context"]}, {"kinds": ["code"], "task_tags": ["context"]}, ["tools/context"]))

    def test_r4_fixed_evaluation_meets_strict_metrics_without_fts(self) -> None:
        result = context_system.load_json(ROOT / "evaluation/retrieval/r4_baseline_result.json")
        self.assertTrue(result["ok"])
        self.assertEqual("not_needed_baseline_passed", result["fts_decision"])
        self.assertIsNone(result["search_projection"])
        self.assertEqual(8, result["summary"]["queries"])
        self.assertEqual(8, result["summary"]["passed"])
        self.assertEqual(0, result["summary"]["failed"])
        self.assertEqual(1.0, result["summary"]["minimum_recall_at_k"])
        self.assertEqual(1.0, result["summary"]["minimum_precision_at_k"])
        self.assertEqual(1.0, result["summary"]["minimum_source_trace_rate"])
        self.assertEqual(0, result["summary"]["protected_leakage"])
        self.assertEqual(0, result["summary"]["budget_failures"])
        self.assertEqual(result["logical_result_hash"], context_system.sha256_text(context_system.canonical_json(result["queries"])))
        self.assertFalse(any(Path(path).suffix in {".db", ".sqlite", ".sqlite3"} for path in context_system.iter_project_files(ROOT)))

    def test_r4_logical_retrieval_is_deterministic_and_source_traced(self) -> None:
        evaluation = context_system.load_json(ROOT / "evaluation/retrieval/r4_queries.json")
        query = next(item for item in evaluation["queries"] if item["query_id"] == "r4.decision.d14-evidence")
        first = context_system.retrieve_evaluation_query(ROOT, query)
        second = context_system.retrieve_evaluation_query(ROOT, query)
        self.assertEqual(first, second)
        self.assertEqual(
            {"decision.r1.1.d14", "knowledge.context.shared-work-context"},
            {result["item_id"] for result in first["results"]},
        )
        self.assertTrue(all(result["source_trace"] for result in first["results"]))

    def test_r5_operational_acceptance_result_passes_all_nine_scenarios(self) -> None:
        result = context_system.load_json(ROOT / "evaluation/operations/r5_acceptance_result.json")
        self.assertTrue(result["ok"])
        self.assertEqual(9, result["summary"]["scenarios"])
        self.assertEqual(9, result["summary"]["passed"])
        self.assertEqual(0, result["summary"]["failed"])
        self.assertEqual(0, result["summary"]["rule_file_leakage"])
        self.assertTrue(all(scenario["passed"] for scenario in result["scenarios"]))
        self.assertEqual(
            result["logical_result_hash"],
            context_system.sha256_text(context_system.canonical_json(result["scenarios"])),
        )

    def test_r5_protected_scope_is_exact_and_never_globally_walked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authorized = root / "inputs/task-one/source.mp4"
            unauthorized = root / "inputs/task-two/secret.mp4"
            authorized.parent.mkdir(parents=True)
            unauthorized.parent.mkdir(parents=True)
            authorized.write_bytes(b"authorized")
            unauthorized.write_bytes(b"unauthorized")
            self.assertEqual(
                "inputs/task-one/source.mp4",
                context_system.assert_task_scoped_path(
                    "inputs/task-one/source.mp4", root, ["inputs/task-one"]
                ),
            )
            with self.assertRaises(context_system.ContextSystemError):
                context_system.assert_task_scoped_path(
                    "inputs/task-two/secret.mp4", root, ["inputs/task-one"]
                )
            self.assertEqual([], context_system.iter_project_files(root))

    def test_r5_catalog_logical_revision_ignores_observation_self_hash(self) -> None:
        first = [{"path": "catalog/files.jsonl", "runtime_hash": "a" * 64, "observed_at": "one", "status": "active"}]
        second = [{"path": "catalog/files.jsonl", "runtime_hash": "b" * 64, "observed_at": "two", "status": "active"}]
        self.assertEqual(
            context_system._revision_hash(first, {"observed_at"}),
            context_system._revision_hash(second, {"observed_at"}),
        )

    def test_r5_conflict_relation_type_matches_maintenance_contract(self) -> None:
        schema = context_system.load_json(ROOT / "schemas/relation.schema.json")
        allowed = schema["properties"]["relation_type"]["enum"]
        self.assertIn("contradicted_by", allowed)
        result = context_system.load_json(ROOT / "evaluation/operations/r5_acceptance_result.json")
        scenario = next(item for item in result["scenarios"] if item["scenario_kind"] == "conflict_supersession_coexistence")
        self.assertEqual(["contradicted_by", "supersedes"], scenario["evidence"]["relation_types"])


if __name__ == "__main__":
    unittest.main()
