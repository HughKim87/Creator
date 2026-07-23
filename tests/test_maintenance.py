from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4

from file_data.context import ContextError, ContextService
from file_data.knowledge import KnowledgeService
from file_data.lifecycle import LifecycleService
from file_data.maintenance import GENERATED_INVENTORY_REF, MaintenanceService
from test_support import TEST_WRITE_CAPABILITY


FAILURE_TEXT = """# 유지보수 실패

- 상태: 해결·회귀 검증 완료
- 적용 범위: 테스트

## 증상

예상 결과와 달랐다.

## 확인된 원인

검증 경로가 없었다.

## 해결과 검증

- 직접 검증 경로를 추가했다.
- 전체 회귀가 통과했다.

## 재사용 규칙

- canonical 문서를 직접 검증한다.
"""


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
        knowledge = KnowledgeService(
            root,
            _write_capability=TEST_WRITE_CAPABILITY,
        )
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
        LifecycleService(
            root,
            _write_capability=TEST_WRITE_CAPABILITY,
        ).register_existing(actor="agent:test", approval_kind="standing_policy")
        maintenance = MaintenanceService(
            root,
            _write_capability=TEST_WRITE_CAPABILITY,
        )
        maintenance.write_inventory()
        return maintenance, source, claim

    @staticmethod
    def _write_knowledge_replacement(
        root: Path,
        claim: dict,
        *,
        statement: str | None = None,
        replacement_id: str | None = None,
        target: str = "docs/canonical.md",
        key: str = "canonical-maintenance-claim",
    ) -> None:
        payload = claim["payload"]
        rendered_statement = statement or payload["statement"]
        (root / target).write_text(
            f"""# Canonical

<!-- project-data:v1 kind=knowledge key={key} -->
```json
{{
  "key": "{key}",
  "kind": "knowledge",
  "payload": {{
    "statement": {json.dumps(rendered_statement, ensure_ascii=False)},
    "classification": {json.dumps(payload["classification"], ensure_ascii=False)},
    "scope": {json.dumps(payload["scope"], ensure_ascii=False)},
    "verification_status": {json.dumps(payload["verification_status"], ensure_ascii=False)},
    "verified_by": {json.dumps(payload["verified_by"], ensure_ascii=False)},
    "replaces_legacy_ids": ["{replacement_id or claim["id"]}"]
  }},
  "source_refs": ["docs/source.md"],
  "status": "current"
}}
```
<!-- /project-data -->
""",
            encoding="utf-8",
        )

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

    def test_inventory_includes_markdown_inside_untracked_nested_directory(self) -> None:
        with self._root() as raw_root:
            maintenance, _, _ = self._fixture(raw_root)
            nested = Path(raw_root) / "docs" / "domain" / "youtube" / "contract.md"
            nested.parent.mkdir(parents=True)
            nested.write_text("# 새 도메인 계약\n", encoding="utf-8")
            self.assertIn("docs/domain/youtube/contract.md", maintenance.document_refs())
            self.assertFalse(maintenance.inventory_status()["matches"])
            self.assertTrue(maintenance.write_inventory()["matches"])
            self.assertIn("docs/domain/youtube/contract.md", maintenance.render_inventory())

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

    def test_exact_document_replacement_suppresses_only_exclusively_migrated_legacy(
        self,
    ) -> None:
        with self._root() as raw_root:
            maintenance, source, claim = self._fixture(raw_root)
            root = Path(raw_root)
            self._write_knowledge_replacement(root, claim)
            (root / "docs" / "source.md").write_text(
                "# 출처\n\nversion two\n",
                encoding="utf-8",
            )
            self.assertEqual(maintenance.detect_drift(), [])
            self.assertEqual(maintenance.detect_duplicates(), [])

            (root / "docs" / "source.md").write_text(
                "# 출처\n\nversion one\n",
                encoding="utf-8",
            )
            second = KnowledgeService(
                root,
                _write_capability=TEST_WRITE_CAPABILITY,
            ).create_knowledge(
                statement="공유 출처를 사용하는 별도 현재 지식",
                classification="fact",
                scope="test",
                source_ids=[source["id"]],
                verification_status="verified",
                verified_by="agent:test",
                record_id=str(uuid4()),
            )
            LifecycleService(
                root,
                _write_capability=TEST_WRITE_CAPABILITY,
            ).register(
                second["id"],
                initial_state="current",
                actor="agent:test",
                approval_kind="standing_policy",
                reason="공유 출처 drift fixture",
            )
            (root / "docs" / "source.md").write_text(
                "# 출처\n\nversion two\n",
                encoding="utf-8",
            )
            findings = maintenance.detect_drift()
            self.assertEqual(
                {finding["target_id"] for finding in findings},
                {source["id"], second["id"]},
            )

    def test_inexact_document_replacement_fails_closed_as_document_data(self) -> None:
        with self._root() as raw_root:
            maintenance, _, claim = self._fixture(raw_root)
            self._write_knowledge_replacement(
                Path(raw_root),
                claim,
                statement="legacy와 일치하지 않는 문장",
            )
            findings = maintenance.detect_drift()
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["target_id"], "project-data:v1")
            self.assertIn("does not exactly match", findings[0]["reason"])

    def test_unknown_terminal_wrong_type_and_duplicate_replacements_fail_closed(
        self,
    ) -> None:
        with self._root() as raw_root:
            maintenance, source, claim = self._fixture(raw_root)
            root = Path(raw_root)

            self._write_knowledge_replacement(
                root,
                claim,
                replacement_id=str(uuid4()),
            )
            self.assertIn(
                "has no lifecycle state",
                maintenance.detect_drift()[0]["reason"],
            )

            self._write_knowledge_replacement(
                root,
                claim,
                replacement_id=source["id"],
            )
            self.assertIn(
                "not exactly match legacy record",
                maintenance.detect_drift()[0]["reason"],
            )

            self._write_knowledge_replacement(root, claim)
            lifecycle = LifecycleService(
                root,
                _write_capability=TEST_WRITE_CAPABILITY,
            )
            state = lifecycle.get_state(claim["id"])
            lifecycle.transition(
                claim["id"],
                expected_state_hash=state["content_hash"],
                action="retire",
                actor="agent:test",
                approval_kind="standing_policy",
                reason="terminal replacement fixture",
            )
            self.assertIn(
                "target is terminal",
                maintenance.detect_drift()[0]["reason"],
            )

        with self._root() as raw_root:
            maintenance, _, claim = self._fixture(raw_root)
            root = Path(raw_root)
            self._write_knowledge_replacement(root, claim)
            self._write_knowledge_replacement(
                root,
                claim,
                target="docs/canonical-second.md",
                key="canonical-maintenance-claim-second",
            )
            self.assertIn(
                "claimed by multiple document blocks",
                maintenance.detect_drift()[0]["reason"],
            )

    def test_scan_validates_canonical_failures_without_projection_records(self) -> None:
        with self._root() as raw_root:
            maintenance, _, _ = self._fixture(raw_root)
            failures = Path(raw_root) / "failures"
            failures.mkdir()
            target = failures / "case.md"
            target.write_text(FAILURE_TEXT, encoding="utf-8")
            maintenance.write_inventory()
            before_records = {
                path.name for path in (Path(raw_root) / "data" / "records").glob("*.json")
            }
            passed = maintenance.scan()
            self.assertTrue(passed["ok"], passed["drift"])
            self.assertEqual(passed["costs"]["canonical_failure_documents"], 1)
            self.assertEqual(
                {path.name for path in (Path(raw_root) / "data" / "records").glob("*.json")},
                before_records,
            )
            target.write_text(
                FAILURE_TEXT.replace("- 상태: 해결·회귀 검증 완료", "- 상태: 원인 조사 중"),
                encoding="utf-8",
            )
            failed = maintenance.scan()
            self.assertFalse(failed["ok"])
            self.assertEqual(failed["drift"][0]["target_id"], "failures/case.md")

    def test_legacy_failure_coexists_without_default_search_or_drift_duplication(self) -> None:
        with self._root() as raw_root:
            maintenance, _, _ = self._fixture(raw_root)
            root = Path(raw_root)
            failures = root / "failures"
            failures.mkdir()
            target = failures / "case.md"
            target.write_text(FAILURE_TEXT, encoding="utf-8")
            knowledge = KnowledgeService(
                root,
                _write_capability=TEST_WRITE_CAPABILITY,
            )
            legacy = knowledge._import_legacy_failure_knowledge(
                "failures/case.md",
                projected_by="agent:test",
                record_id=str(uuid4()),
                source_id=str(uuid4()),
            )
            lifecycle = LifecycleService(
                root,
                _write_capability=TEST_WRITE_CAPABILITY,
            )
            lifecycle.register_existing(
                actor="agent:test",
                approval_kind="standing_policy",
            )
            maintenance.write_inventory()
            before_records = {
                path.name for path in (root / "data" / "records").glob("*.json")
            }
            before_events = {
                path.name: path.read_bytes()
                for path in (root / "data" / "events").glob("*.jsonl")
            }

            imported = knowledge.import_failure_knowledge(
                "failures/case.md",
                projected_by="agent:test",
            )
            self.assertFalse(imported["stored"])
            target.write_text(
                FAILURE_TEXT.replace(
                    "canonical 문서를 직접 검증한다",
                    "canonical 개정 문서를 직접 검증한다",
                ),
                encoding="utf-8",
            )
            refreshed = lifecycle.refresh_failure_projection(
                legacy["failure_knowledge"]["id"],
                actor="agent:test",
                approval_kind="standing_policy",
                reason="정본 개정 직접 검증",
            )
            self.assertFalse(refreshed["stored"])

            context = ContextService(root)
            filtered = context.filter_records({"record_type": "failure_knowledge"})
            self.assertEqual(
                [item["ref"] for item in filtered],
                ["failures/case.md"],
            )
            searched = context.search(
                "canonical 개정 문서를 직접 검증",
                {"record_type": "failure_knowledge"},
            )
            self.assertEqual(
                [item["ref"] for item in searched],
                ["failures/case.md"],
            )
            report = maintenance.scan()
            self.assertTrue(report["ok"], report["drift"])
            self.assertEqual(report["drift"], [])
            self.assertEqual(report["costs"]["canonical_failure_documents"], 1)
            self.assertEqual(
                {path.name for path in (root / "data" / "records").glob("*.json")},
                before_records,
            )
            self.assertEqual(
                {
                    path.name: path.read_bytes()
                    for path in (root / "data" / "events").glob("*.jsonl")
                },
                before_events,
            )

    def test_scan_detects_exact_current_knowledge_duplicate(self) -> None:
        with self._root() as raw_root:
            maintenance, source, claim = self._fixture(raw_root)
            knowledge = KnowledgeService(
                raw_root,
                _write_capability=TEST_WRITE_CAPABILITY,
            )
            duplicate = knowledge.create_knowledge(
                statement=claim["payload"]["statement"], classification="constraint", scope="test",
                source_ids=[source["id"]], verification_status="verified",
                verified_by="agent:test", record_id=str(uuid4())
            )
            LifecycleService(
                raw_root,
                _write_capability=TEST_WRITE_CAPABILITY,
            ).register(
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

    def test_verify_checks_python_in_separate_domain_package(self) -> None:
        with self._root() as raw_root:
            maintenance, _, _ = self._fixture(raw_root)
            broken = Path(raw_root) / "src" / "youtube_domain" / "broken.py"
            broken.parent.mkdir(parents=True)
            broken.write_text("def broken(:\n", encoding="utf-8")
            failed = maintenance.verify()
            self.assertFalse(failed["ok"])
            self.assertTrue(
                any(error.startswith("python:src/youtube_domain/broken.py:") for error in failed["errors"])
            )

    def test_context_evaluation_reruns_with_current_baseline(self) -> None:
        with self._root() as raw_root:
            maintenance, _, claim = self._fixture(raw_root)
            payload = {
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
            with self.assertRaisesRegex(ContextError, "legacy_mode_required"):
                maintenance.evaluate_context(payload)
            result = maintenance.evaluate_context(payload, legacy=True)
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
                },
                legacy=True,
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
