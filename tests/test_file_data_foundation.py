from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from file_data import (  # noqa: E402
    DuplicateRecordError,
    RecordValidationError,
    UnsafePathError,
    atomic_write_record,
    build_record,
    decode_record,
    read_record,
    resolve_project_path,
    validate_record,
)
from file_data.record import REQUIRED_FIELDS, SCHEMA_VERSION  # noqa: E402


FIXTURES = ROOT / "tests" / "fixtures" / "file_data"


class FileDataFoundationTests(unittest.TestCase):
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
            with patch("file_data.record.os.replace", side_effect=OSError("simulated replace failure")):
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


if __name__ == "__main__":
    unittest.main()
