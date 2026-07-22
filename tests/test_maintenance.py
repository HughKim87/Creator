from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4

from file_data.context import ContextService
from file_data.knowledge import KnowledgeService
from file_data.lifecycle import LifecycleService
from file_data.maintenance import GENERATED_INVENTORY_REF, MaintenanceService


class MaintenanceServiceTests(unittest.TestCase):
    def _root(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(prefix="stage08-maintenance-")

    def _fixture(self, raw_root: str) -> tuple[MaintenanceService, dict, dict]:
        root = Path(raw_root)
        (root / "docs" / "obsidian").mkdir(parents=True)
        (root / "src" / "file_data").mkdir(parents=True)
        (root / "schemas").mkdir()
        (root / "README.md").write_text("# 테스트\n\n[현재](SESSION_HANDOFF.md)\n", encoding="utf-8")
        (root / "SESSION_HANDOFF.md").write_text("# 현재 상태\n", encoding="utf-8")
        (root / "docs" / "source.md").write_text("# 출처\n\nversion one\n", encoding="utf-8")
        (root / "docs" / "obsidian" / "DOCUMENT_MAP.md").write_text(
            "# 지도\n\n[현재](../../SESSION_HANDOFF.md)\n"
            "[자동 inventory](GENERATED_DOCUMENT_INVENTORY.md)\n",
            encoding="utf-8",
        )
        (root / "src" / "file_data" / "neutral.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "schemas" / "neutral.json").write_text("{}\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
        knowledge = KnowledgeService(root)
        knowledge.initialize()
        source = knowledge.create_source(
            source_kind="local_document", locator="docs/source.md", evidence_role="primary",
            record_id=str(uuid4())
        )
        claim = knowledge.create_knowledge(
            statement="유지보수 scan은 정본을 자동 변경하지 않는다", classification="constraint",
            scope="test", source_ids=[source["id"]], verification_status="verified",
            verified_by="agent:test", record_id=str(uuid4())
        )
        LifecycleService(root).register_existing(actor="agent:test", approval_kind="standing_policy")
        maintenance = MaintenanceService(root)
        maintenance.write_inventory()
        return maintenance, source, claim

    def test_inventory_is_deterministic_and_regenerates_after_deletion(self) -> None:
        with self._root() as raw_root:
            maintenance, _, _ = self._fixture(raw_root)
            first = maintenance.render_inventory()
            second = maintenance.render_inventory()
            self.assertEqual(first, second)
            target = Path(raw_root) / GENERATED_INVENTORY_REF
            target.unlink()
            self.assertFalse(maintenance.inventory_status()["matches"])
            status = maintenance.write_inventory()
            self.assertTrue(status["matches"])
            self.assertEqual(target.read_text(encoding="utf-8"), first)

    def test_scan_detects_drift_without_changing_lifecycle(self) -> None:
        with self._root() as raw_root:
            maintenance, source, claim = self._fixture(raw_root)
            lifecycle = LifecycleService(raw_root)
            before_events = len(lifecycle._events()[0])
            before_source = lifecycle.get_state(source["id"])
            (Path(raw_root) / "docs" / "source.md").write_text(
                "# 출처\n\nversion two\n", encoding="utf-8"
            )
            report = maintenance.scan()
            self.assertFalse(report["ok"])
            self.assertEqual(
                {item["target_id"] for item in report["drift"]}, {source["id"], claim["id"]}
            )
            self.assertEqual(len(lifecycle._events()[0]), before_events)
            self.assertEqual(lifecycle.get_state(source["id"]), before_source)

    def test_scan_detects_exact_current_knowledge_duplicate(self) -> None:
        with self._root() as raw_root:
            maintenance, source, claim = self._fixture(raw_root)
            knowledge = KnowledgeService(raw_root)
            duplicate = knowledge.create_knowledge(
                statement=claim["payload"]["statement"], classification="constraint", scope="test",
                source_ids=[source["id"]], verification_status="verified",
                verified_by="agent:test", record_id=str(uuid4())
            )
            LifecycleService(raw_root).register(
                duplicate["id"], initial_state="current", actor="agent:test",
                approval_kind="standing_policy", reason="중복 탐지 fixture"
            )
            duplicates = maintenance.detect_duplicates()
            self.assertEqual(len(duplicates), 1)
            self.assertEqual(set(duplicates[0]["record_ids"]), {claim["id"], duplicate["id"]})

    def test_verify_passes_and_broken_link_fails_explicitly(self) -> None:
        with self._root() as raw_root:
            maintenance, _, _ = self._fixture(raw_root)
            passed = maintenance.verify()
            self.assertTrue(passed["ok"], passed["errors"])
            map_path = Path(raw_root) / "docs" / "obsidian" / "DOCUMENT_MAP.md"
            map_path.write_text(
                map_path.read_text(encoding="utf-8") + "[끊김](missing.md)\n", encoding="utf-8"
            )
            maintenance.write_inventory()
            failed = maintenance.verify()
            self.assertFalse(failed["ok"])
            self.assertTrue(any(error.startswith("missing_link:") for error in failed["errors"]))

    def test_context_evaluation_reruns_with_current_baseline(self) -> None:
        with self._root() as raw_root:
            maintenance, _, claim = self._fixture(raw_root)
            result = maintenance.evaluate_context(
                {
                    "evaluations": [
                        {
                            "name": "current claim",
                            "request": {
                                "purpose": "유지보수 평가",
                                "records": [{"id": claim["id"], "reason": "필수 current 지식"}],
                                "char_limit": 12000,
                            },
                            "expected_record_ids": [claim["id"]],
                            "forbidden_record_ids": [],
                            "max_characters": 12000,
                            "min_reduction_percent": 0,
                            "max_irrelevant_records": 0,
                        }
                    ]
                }
            )
            self.assertTrue(result["ok"])
            self.assertTrue(result["results"][0]["checks"]["repeatable"])

    def test_context_evaluation_reports_forbidden_record_without_mutation(self) -> None:
        with self._root() as raw_root:
            maintenance, _, claim = self._fixture(raw_root)
            before = len(LifecycleService(raw_root)._events()[0])
            result = maintenance.evaluate_context(
                {
                    "evaluations": [
                        {
                            "name": "forbidden fixture",
                            "request": {
                                "purpose": "금지 결과 검사",
                                "records": [{"id": claim["id"], "reason": "명시 선택"}],
                            },
                            "expected_record_ids": [],
                            "forbidden_record_ids": [claim["id"]],
                            "max_characters": 12000,
                            "min_reduction_percent": 0,
                            "max_irrelevant_records": 1,
                        }
                    ]
                }
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["results"][0]["forbidden_record_ids"], [claim["id"]])
            self.assertEqual(len(LifecycleService(raw_root)._events()[0]), before)

    def test_cost_report_exposes_documents_records_events_and_runtime(self) -> None:
        with self._root() as raw_root:
            maintenance, _, _ = self._fixture(raw_root)
            report = maintenance.scan()["costs"]
            self.assertGreaterEqual(report["documents"]["documents"], 5)
            self.assertEqual(report["records_by_type"]["knowledge"], 1)
            self.assertGreaterEqual(report["events"]["lifecycle"], 2)
            self.assertIsInstance(report["elapsed_ms"], float)

    def test_cli_inventory_and_scan(self) -> None:
        with self._root() as raw_root:
            self._fixture(raw_root)
            env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src"), "PYTHONUTF8": "1"}
            checked = subprocess.run(
                [sys.executable, "-m", "file_data", "--root", raw_root, "maintenance-inventory"],
                capture_output=True, text=True, encoding="utf-8", env=env, check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertTrue(json.loads(checked.stdout)["result"]["matches"])
            scanned = subprocess.run(
                [sys.executable, "-m", "file_data", "--root", raw_root, "maintenance-scan"],
                capture_output=True, text=True, encoding="utf-8", env=env, check=False,
            )
            self.assertEqual(scanned.returncode, 0, scanned.stderr)
            self.assertTrue(json.loads(scanned.stdout)["result"]["ok"])


if __name__ == "__main__":
    unittest.main()
