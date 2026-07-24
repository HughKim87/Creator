from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from file_data import (  # noqa: E402
    ARTIFACT_OWNERS,
    ArtifactService,
    DocumentDataError,
    DocumentDataService,
    DocumentWorkService,
    DuplicateRecordError,
    ExpectationMismatchError,
    LegacyReadOnlyError,
    RecordStore,
    RecordValidationError,
    UnsafePathError,
    build_record,
    decode_record,
    read_record,
    resolve_project_path,
    validate_record,
)
from file_data.record import (  # noqa: E402
    REQUIRED_FIELDS,
    SCHEMA_VERSION,
)
from file_data.store import _atomic_write_record  # noqa: E402
from test_support import TEST_WRITE_CAPABILITY  # noqa: E402


FIXTURES = ROOT / "tests" / "fixtures" / "file_data"


def atomic_write_record(
    project_root: Path,
    relative_path: Path,
    record: dict,
    *,
    overwrite: bool = False,
) -> Path:
    return _atomic_write_record(
        project_root,
        relative_path,
        record,
        write_capability=TEST_WRITE_CAPABILITY,
        overwrite=overwrite,
    )


class FileDataFoundationTests(unittest.TestCase):
    @staticmethod
    def _knowledge_block(key: str = "test-knowledge") -> str:
        return f"""<!-- project-data:v1 kind=knowledge key={key} -->
```json
{{
  "key": "{key}",
  "kind": "knowledge",
  "payload": {{
    "statement": "문서 정본 테스트",
    "classification": "fact",
    "scope": "test",
    "verification_status": "verified",
    "verified_by": "agent:test",
    "replaces_legacy_ids": ["123e4567-e89b-42d3-a456-426614174000"]
  }},
  "source_refs": ["docs/owner.md"],
  "status": "current"
}}
```
<!-- /project-data -->
"""

    @staticmethod
    def _work_block(key: str = "active-work") -> str:
        return f"""# Handoff

<!-- project-data:v1 kind=work key={key} -->
```json
{{
  "key": "{key}",
  "kind": "work",
  "payload": {{
    "desired_outcome": "문서 정본 작업 상태를 원자적으로 갱신한다.",
    "authorized_actions": ["테스트"],
    "excluded_scope": [],
    "input_refs": ["docs/evidence.md"],
    "protection_boundaries": [],
    "required_decisions": [],
    "verification_levels": ["재읽기"],
    "completed_items": [],
    "blockers": [],
    "next_action": "첫 체크포인트를 기록한다.",
    "evidence_refs": ["docs/evidence.md"],
    "checkpoints": []
  }},
  "source_refs": ["docs/evidence.md"],
  "status": "in_progress"
}}
```
<!-- /project-data -->
"""

    def test_json_schema_and_runtime_contract_agree(self) -> None:
        schema = json.loads((ROOT / "schemas" / "common-record-v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), REQUIRED_FIELDS)
        self.assertEqual(set(schema["properties"]), REQUIRED_FIELDS)
        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)

    def test_valid_fixture_round_trips(self) -> None:
        data = (FIXTURES / "valid" / "neutral-record.json").read_bytes()
        record = decode_record(data)
        self.assertEqual(record["record_type"], "example")
        self.assertEqual(record["payload"]["message"], "중립 예제")

    def test_invalid_fixtures_report_expected_failure_classes(self) -> None:
        cases = {
            "missing-field.json": "missing_field",
            "wrong-id.json": "invalid_id",
            "wrong-version.json": "unsupported_version",
            "tampered-content.json": "hash_mismatch",
        }
        for name, expected_code in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(RecordValidationError) as caught:
                    decode_record((FIXTURES / "invalid" / name).read_bytes())
                self.assertEqual(caught.exception.code, expected_code)

    def test_invalid_utf8_nul_and_duplicate_keys_are_rejected(self) -> None:
        for data, expected_code in (
            (b"\xff", "invalid_utf8"),
            (b'{"value":"\x00"}', "nul_byte"),
            (b'{"id":1,"id":2}', "duplicate_key"),
        ):
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(RecordValidationError) as caught:
                    decode_record(data)
                self.assertEqual(caught.exception.code, expected_code)

    def test_non_string_envelope_key_is_rejected_cleanly(self) -> None:
        record = build_record("example", {"value": 1})
        record[1] = "invalid"
        with self.assertRaises(RecordValidationError) as caught:
            validate_record(record)
        self.assertEqual(caught.exception.code, "not_json")

    def test_build_record_normalizes_utc_and_detects_time_order(self) -> None:
        timestamp = datetime(2026, 7, 23, 9, 30, 1, 900, tzinfo=UTC)
        record = build_record("example", {"value": 1}, timestamp=timestamp)
        self.assertEqual(record["created_at"], "2026-07-23T09:30:01Z")
        record["updated_at"] = "2026-07-23T09:30:00Z"
        record["content_hash"] = "sha256:" + "0" * 64
        with self.assertRaises(RecordValidationError) as caught:
            decode_record(json.dumps(record).encode("utf-8"))
        self.assertEqual(caught.exception.code, "timestamp_order")

    def test_path_boundary_rejects_escape_absolute_and_protected_segments(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage02-root-") as raw_root:
            root = Path(raw_root)
            allowed = resolve_project_path(root, Path("data") / "record.json")
            self.assertEqual(allowed, root / "data" / "record.json")
            for path in (
                Path("..") / "escape.json",
                root / "absolute.json",
                Path("nested") / "inputs" / "secret.json",
                Path("backup") / "history.json",
                Path(".obsidian") / "state.json",
                "data/./record.json",
                "data//record.json",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(UnsafePathError):
                        resolve_project_path(root, path)

    def test_atomic_write_and_read_work_in_unicode_space_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="단계 02 경로 ") as raw_root:
            root = Path(raw_root)
            (root / "data" / "records").mkdir(parents=True)
            record = build_record("example", {"message": "안전 저장"})
            path = Path("data") / "records" / f"{record['id']}.json"
            target = atomic_write_record(root, path, record)
            self.assertEqual(target, root / path)
            self.assertEqual(read_record(root, path), record)
            self.assertEqual(list(target.parent.glob(f".{target.name}.*.tmp")), [])

    def test_existing_file_is_preserved_when_overwrite_is_not_approved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage02-existing-") as raw_root:
            root = Path(raw_root)
            (root / "data" / "records").mkdir(parents=True)
            first = build_record("example", {"revision": 1})
            path = Path("data") / "records" / f"{first['id']}.json"
            atomic_write_record(root, path, first)
            before = (root / path).read_bytes()
            with self.assertRaises(FileExistsError):
                atomic_write_record(root, path, first)
            self.assertEqual((root / path).read_bytes(), before)

    def test_different_id_cannot_replace_existing_record(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage02-id-") as raw_root:
            root = Path(raw_root)
            (root / "data" / "records").mkdir(parents=True)
            first = build_record("example", {"revision": 1})
            path = Path("data") / "records" / f"{first['id']}.json"
            atomic_write_record(root, path, first)
            with self.assertRaises(DuplicateRecordError):
                atomic_write_record(root, path, build_record("example", {"revision": 2}), overwrite=True)

    def test_record_address_is_single_and_id_derived(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage02-address-") as raw_root:
            root = Path(raw_root)
            (root / "data" / "records").mkdir(parents=True)
            record = build_record("example", {"value": 1})
            with self.assertRaises(UnsafePathError):
                atomic_write_record(root, Path("other") / f"{record['id']}.json", record)
            with self.assertRaises(DuplicateRecordError):
                atomic_write_record(root, Path("data") / "records" / "wrong.json", record)

    def test_replace_failure_keeps_existing_file_and_cleans_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage02-failure-") as raw_root:
            root = Path(raw_root)
            (root / "data" / "records").mkdir(parents=True)
            original = build_record("example", {"revision": 1})
            path = Path("data") / "records" / f"{original['id']}.json"
            atomic_write_record(root, path, original)
            replacement = build_record(
                "example",
                {"revision": 2},
                record_id=original["id"],
                timestamp=datetime(2026, 7, 23, 1, 0, tzinfo=UTC),
            )
            before = (root / path).read_bytes()
            with patch("file_data.store.os.replace", side_effect=OSError("simulated replace failure")):
                with self.assertRaisesRegex(OSError, "simulated replace failure"):
                    atomic_write_record(root, path, replacement, overwrite=True)
            self.assertEqual((root / path).read_bytes(), before)
            self.assertEqual(list((root / "data" / "records").glob(".*.tmp")), [])

    def test_deleting_derived_copy_does_not_remove_source_fixture(self) -> None:
        source = FIXTURES / "valid" / "neutral-record.json"
        with tempfile.TemporaryDirectory(prefix="stage02-derived-") as raw_root:
            derived = Path(raw_root) / "derived.json"
            derived.write_bytes(source.read_bytes())
            derived.unlink()
            self.assertTrue(source.is_file())

    def test_document_data_parser_validates_actual_project_blocks(self) -> None:
        service = DocumentDataService(ROOT)
        result = service.validate()
        self.assertEqual(result["blocks"], 3)
        self.assertEqual(
            result["counts_by_kind"],
            {"knowledge": 3},
        )
        block = service.get_block("context-package-deterministic-derived-view")
        self.assertEqual(block["owner"], "docs/CONTEXT_PACKAGE_CONTRACT.md")
        self.assertEqual(block["status"], "current")

    def test_document_markers_inside_commonmark_code_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage10-document-parser-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            fake = "<!-- project-data:v1 kind=knowledge key=ignored -->"
            (root / "docs" / "owner.md").write_text(
                "# Owner\n\n"
                + self._knowledge_block()
                + "\n````markdown\n"
                + fake
                + "\n```json\nnot-json\n```\n<!-- /project-data -->\n````\n"
                + "\n~~~text\n"
                + fake
                + "\n~~~\n"
                + "\n    "
                + fake
                + "\n",
                encoding="utf-8",
            )
            blocks = DocumentDataService(root).list_blocks()
            self.assertEqual([block["key"] for block in blocks], ["test-knowledge"])

    def test_document_data_duplicate_key_and_wrong_owner_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage10-document-invalid-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            duplicate = self._knowledge_block().replace(
                '"status": "current"',
                '"status": "current", "status": "candidate"',
            )
            (root / "docs" / "owner.md").write_text(duplicate, encoding="utf-8")
            with self.assertRaisesRegex(DocumentDataError, "duplicate JSON key"):
                DocumentDataService(root).validate()

            (root / "docs" / "owner.md").write_text(
                self._knowledge_block().replace("kind=knowledge", "kind=work").replace(
                    '"kind": "knowledge"', '"kind": "work"'
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DocumentDataError, "not allowed in owner"):
                DocumentDataService(root).validate()

    def test_document_data_rejects_whitespace_keys_nonfinite_json_and_malformed_markers(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="stage10-document-strict-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            owner = root / "docs" / "owner.md"
            owner.write_text(
                self._knowledge_block().replace(
                    '"key": "test-knowledge"',
                    '"key": " test-knowledge "',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DocumentDataError, "leading or trailing whitespace"):
                DocumentDataService(root).validate()

            owner.write_text(
                self._knowledge_block().replace(
                    '"statement": "문서 정본 테스트"',
                    '"statement": NaN',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DocumentDataError, "non-finite number"):
                DocumentDataService(root).validate()

            owner.write_text(
                "<!-- project-data:v1 kind=knowledge bad_key=test -->\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DocumentDataError, "malformed project marker"):
                DocumentDataService(root).validate()

            owner.write_text(
                "<!-- project-artifact:v1 bad_path=x verify=json-semantic -->\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DocumentDataError, "malformed project marker"):
                DocumentDataService(root).validate()

            for malformed in (
                "<!-- project-data:v1kind=knowledge key=x -->\n",
                "<!-- project-artifact:v1path=x verify=json-semantic -->\n",
            ):
                owner.write_text(malformed, encoding="utf-8")
                with self.assertRaisesRegex(DocumentDataError, "malformed project marker"):
                    DocumentDataService(root).validate()

    def test_native_document_knowledge_allows_empty_legacy_replacements(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage10-document-native-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            (root / "docs" / "owner.md").write_text(
                self._knowledge_block().replace(
                    '"replaces_legacy_ids": ["123e4567-e89b-42d3-a456-426614174000"]',
                    '"replaces_legacy_ids": []',
                ),
                encoding="utf-8",
            )
            self.assertEqual(DocumentDataService(root).validate()["blocks"], 1)

    def test_invalid_backtick_info_string_does_not_hide_following_valid_block(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage10-document-fence-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            (root / "docs" / "owner.md").write_text(
                "```bad`\nnot a CommonMark fence\n\n" + self._knowledge_block(),
                encoding="utf-8",
            )
            blocks = DocumentDataService(root).list_blocks()
            self.assertEqual([block["key"] for block in blocks], ["test-knowledge"])

    def test_protected_directories_are_rejected_before_recursive_scan(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage10-document-prefilter-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            (root / "docs" / "owner.md").write_text(
                self._knowledge_block(),
                encoding="utf-8",
            )
            (root / "inputs").mkdir()
            (root / "inputs" / "hidden.md").write_text("secret", encoding="utf-8")
            original_scandir = os.scandir
            visited: list[Path] = []

            def observing_scandir(path: str | os.PathLike[str]):
                resolved = Path(path).resolve()
                visited.append(resolved)
                if resolved == (root / "inputs").resolve():
                    raise AssertionError("protected inputs directory was scanned")
                return original_scandir(path)

            with patch("file_data.document_data.os.scandir", side_effect=observing_scandir):
                self.assertEqual(DocumentDataService(root).validate()["blocks"], 1)
            self.assertNotIn((root / "inputs").resolve(), visited)

    def test_document_work_checkpoint_is_hash_guarded_atomic_and_reread(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage10-document-work-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            (root / "docs" / "evidence.md").write_text("# Evidence\n", encoding="utf-8")
            handoff = root / "SESSION_HANDOFF.md"
            handoff.write_text(self._work_block(), encoding="utf-8")
            service = DocumentWorkService(root)
            before = service.get_work()
            after = service.checkpoint(
                expected_hash=before["block_hash"],
                actor="codex:test",
                summary="원자 갱신 검증을 완료했다.",
                evidence_refs=["docs/evidence.md"],
                completed_items=["원자 갱신 테스트"],
                next_action="독립 재검증을 수행한다.",
                timestamp=datetime(2026, 7, 23, 6, 0, tzinfo=UTC),
            )
            self.assertNotEqual(after["block_hash"], before["block_hash"])
            self.assertEqual(after["payload"]["next_action"], "독립 재검증을 수행한다.")
            self.assertEqual(after["payload"]["completed_items"], ["원자 갱신 테스트"])
            self.assertEqual(after["payload"]["checkpoints"][0]["at"], "2026-07-23T06:00:00Z")
            self.assertEqual(service.get_work(), after)
            self.assertFalse((root / ".SESSION_HANDOFF.md.lock").exists())

    def test_document_work_stale_hash_and_replace_failure_preserve_original(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage10-document-work-failure-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            (root / "docs" / "evidence.md").write_text("# Evidence\n", encoding="utf-8")
            handoff = root / "SESSION_HANDOFF.md"
            handoff.write_text(self._work_block(), encoding="utf-8")
            service = DocumentWorkService(root)
            current = service.get_work()
            before = handoff.read_bytes()
            arguments = {
                "actor": "codex:test",
                "summary": "실패 경로를 검증한다.",
                "evidence_refs": ["docs/evidence.md"],
                "completed_items": [],
                "next_action": "원본 보존을 확인한다.",
            }

            with self.assertRaises(ExpectationMismatchError):
                service.checkpoint(expected_hash="sha256:" + "0" * 64, **arguments)
            self.assertEqual(handoff.read_bytes(), before)

            with patch(
                "file_data.document_data.os.replace",
                side_effect=OSError("replace failed"),
            ):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    service.checkpoint(
                        expected_hash=current["block_hash"],
                        **arguments,
                    )
            self.assertEqual(handoff.read_bytes(), before)
            self.assertEqual(list(root.glob(".SESSION_HANDOFF.md.*.tmp")), [])
            self.assertFalse((root / ".SESSION_HANDOFF.md.lock").exists())

    def test_all_json_artifacts_rebuild_from_document_blocks_in_isolated_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage10-artifacts-") as raw_root:
            root = Path(raw_root)
            owners = sorted(set(ARTIFACT_OWNERS.values()))
            for relative in owners:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            for relative in ARTIFACT_OWNERS:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            service = ArtifactService(root)
            self.assertEqual(service.check(), {"artifacts": 20, "drift": []})
            for target_ref in sorted(ARTIFACT_OWNERS):
                target = root / target_ref
                target.unlink()
                result = service.rebuild(target_ref)
                self.assertEqual(result["target"], target_ref)
                self.assertTrue(target.is_file())
                self.assertEqual(service.check(), {"artifacts": 20, "drift": []})

    def test_production_record_writes_fail_before_touching_runtime_data(self) -> None:
        before = {
            path.name: path.read_bytes()
            for path in (ROOT / "data" / "events").glob("*.jsonl")
        }
        store = RecordStore(ROOT)
        with self.assertRaises(LegacyReadOnlyError):
            store.create_record("example", {"forbidden": True})
        with self.assertRaises(LegacyReadOnlyError):
            store.append_event("example_events", {"forbidden": True})
        with self.assertRaisesRegex(LegacyReadOnlyError, "isolated test capability"):
            _atomic_write_record(
                ROOT,
                Path("data") / "records" / "00000000-0000-4000-8000-000000000000.json",
                build_record(
                    "example",
                    {"forbidden": True},
                    record_id="00000000-0000-4000-8000-000000000000",
                ),
                write_capability=None,
            )
        import file_data
        import file_data.record

        self.assertFalse(hasattr(file_data, "atomic_write_record"))
        self.assertFalse(hasattr(file_data.record, "atomic_write_record"))
        self.assertEqual(
            {
                path.name: path.read_bytes()
                for path in (ROOT / "data" / "events").glob("*.jsonl")
            },
            before,
        )

if __name__ == "__main__":
    unittest.main()
