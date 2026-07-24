from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "src"))

from file_data import (  # noqa: E402
    EMPTY_STREAM_HASH,
    ConcurrentWriteError,
    ConflictError,
    ExpectationMismatchError,
    LegacyReadOnlyError,
    RecordNotFoundError,
    RecordStore,
    RecordValidationError,
    StoreNotInitializedError,
    build_record,
)
from file_data.store import _atomic_write_record  # noqa: E402
from test_support import TEST_WRITE_CAPABILITY  # noqa: E402


FIRST_ID = "123e4567-e89b-42d3-a456-426614174000"
SECOND_ID = "123e4567-e89b-42d3-a456-426614174001"
MISSING_ID = "123e4567-e89b-42d3-a456-426614174099"


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


class RecordStoreTests(unittest.TestCase):
    def make_store(self, root: Path) -> RecordStore:
        store = RecordStore._for_test(root)
        store.initialize()
        return store

    def test_initialization_is_required_and_scoped(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-init-") as raw_root:
            root = Path(raw_root)
            with self.assertRaises(LegacyReadOnlyError):
                RecordStore(root).initialize()
            store = RecordStore._for_test(root)
            with self.assertRaises(StoreNotInitializedError):
                store.list_records("example")
            result = store.initialize()
            self.assertEqual(result, {"records": "extension/data/records", "events": "extension/data/events"})
            self.assertEqual(
                sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir()),
                [
                    "extension",
                    "extension/data",
                    "extension/data/events",
                    "extension/data/records",
                ],
            )

    def test_test_write_capability_rejects_active_project_root(self) -> None:
        with self.assertRaises(LegacyReadOnlyError):
            RecordStore._for_test(ROOT)

        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "core" / "tests" / "test_cli_entry.py"),
                "--root",
                str(ROOT),
                "init",
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(json.loads(completed.stderr)["error"]["kind"], "legacy_read_only")

        with (
            tempfile.TemporaryDirectory(prefix="stage03-bound-first-") as first_root,
            tempfile.TemporaryDirectory(prefix="stage03-bound-second-") as second_root,
        ):
            first_store = RecordStore._for_test(Path(first_root))
            with self.assertRaisesRegex(LegacyReadOnlyError, "bound to another root"):
                RecordStore(
                    Path(second_root),
                    _write_capability=first_store._write_capability,
                )

    def test_create_get_list_and_expected_update(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-record-") as raw_root:
            root = Path(raw_root)
            store = self.make_store(root)
            created = store.create_record(
                "example",
                {"revision": 1},
                record_id=FIRST_ID,
                timestamp=datetime(2026, 7, 23, 1, 0, tzinfo=UTC),
            )
            self.assertEqual(store.get_record(FIRST_ID), created)
            self.assertEqual(store.list_records("example"), [created])
            before_path = root / "extension" / "data" / "records" / f"{FIRST_ID}.json"
            before = before_path.read_bytes()
            with self.assertRaises(ExpectationMismatchError):
                store.update_record(
                    FIRST_ID,
                    {"revision": 2},
                    expected_content_hash="sha256:" + "0" * 64,
                )
            self.assertEqual(before_path.read_bytes(), before)
            updated = store.update_record(
                FIRST_ID,
                {"revision": 2},
                expected_content_hash=created["content_hash"],
                timestamp=datetime(2026, 7, 23, 1, 1, tzinfo=UTC),
            )
            self.assertEqual(updated["created_at"], created["created_at"])
            self.assertEqual(updated["updated_at"], "2026-07-23T01:01:00Z")
            self.assertNotEqual(updated["content_hash"], created["content_hash"])
            self.assertEqual(store.get_record(FIRST_ID), updated)

    def test_duplicate_missing_and_unapproved_type_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-errors-") as raw_root:
            store = self.make_store(Path(raw_root))
            store.create_record("example", {}, record_id=FIRST_ID)
            with self.assertRaises(ConflictError):
                store.create_record("example", {}, record_id=FIRST_ID)
            with self.assertRaises(RecordNotFoundError):
                store.get_record(MISSING_ID)
            with self.assertRaisesRegex(Exception, "not approved"):
                store.create_record("future_type", {})

    def test_existing_record_lock_reports_concurrent_write(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-lock-") as raw_root:
            root = Path(raw_root)
            store = self.make_store(root)
            lock = root / "extension" / "data" / "records" / f".{FIRST_ID}.json.lock"
            lock.write_text("pid=external\n", encoding="ascii")
            with self.assertRaises(ConcurrentWriteError):
                store.create_record("example", {}, record_id=FIRST_ID)
            self.assertEqual(lock.read_text(encoding="ascii"), "pid=external\n")

    def test_append_list_hash_and_expectation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-events-") as raw_root:
            root = Path(raw_root)
            store = self.make_store(root)
            events, initial_hash = store.list_events("example_events")
            self.assertEqual(events, [])
            self.assertEqual(initial_hash, EMPTY_STREAM_HASH)
            first = store.append_event(
                "example_events",
                {"sequence": 1},
                expected_stream_hash=initial_hash,
                event_id=FIRST_ID,
                timestamp=datetime(2026, 7, 23, 2, 0, tzinfo=UTC),
            )
            stream_path = root / "extension" / "data" / "events" / "example_events.jsonl"
            before = stream_path.read_bytes()
            with self.assertRaises(ExpectationMismatchError):
                store.append_event(
                    "example_events",
                    {"sequence": 2},
                    expected_stream_hash=EMPTY_STREAM_HASH,
                    event_id=SECOND_ID,
                )
            self.assertEqual(stream_path.read_bytes(), before)
            second = store.append_event(
                "example_events",
                {"sequence": 2},
                expected_stream_hash=first["stream_hash"],
                event_id=SECOND_ID,
                timestamp=datetime(2026, 7, 23, 2, 1, tzinfo=UTC),
            )
            events, final_hash = store.list_events("example_events")
            self.assertEqual([event["payload"]["sequence"] for event in events], [1, 2])
            self.assertEqual(second["count"], 2)
            self.assertEqual(second["stream_hash"], final_hash)
            self.assertTrue(stream_path.read_bytes().endswith(b"\n"))

    def test_stream_corruption_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-corrupt-") as raw_root:
            root = Path(raw_root)
            store = self.make_store(root)
            stream = root / "extension" / "data" / "events" / "example_events.jsonl"
            stream.write_bytes(b'{"partial":true}')
            with self.assertRaises(RecordValidationError) as caught:
                store.list_events("example_events")
            self.assertEqual(caught.exception.code, "partial_jsonl")

    def test_stream_replace_failure_preserves_source_and_cleans_owned_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-replace-") as raw_root:
            root = Path(raw_root)
            store = self.make_store(root)
            first = store.append_event("example_events", {"sequence": 1}, event_id=FIRST_ID)
            stream = root / "extension" / "data" / "events" / "example_events.jsonl"
            before = stream.read_bytes()
            with patch("file_data.store.os.replace", side_effect=OSError("simulated stream replace failure")):
                with self.assertRaisesRegex(OSError, "simulated stream replace failure"):
                    store.append_event(
                        "example_events",
                        {"sequence": 2},
                        expected_stream_hash=first["stream_hash"],
                        event_id=SECOND_ID,
                    )
            self.assertEqual(stream.read_bytes(), before)
            self.assertEqual(list(stream.parent.glob("*.tmp")), [])
            self.assertEqual(list(stream.parent.glob("*.lock")), [])

    def test_corrupt_record_causes_list_failure_instead_of_skip(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-list-") as raw_root:
            root = Path(raw_root)
            store = self.make_store(root)
            store.create_record("example", {}, record_id=FIRST_ID)
            corrupt = root / "extension" / "data" / "records" / f"{SECOND_ID}.json"
            corrupt.write_bytes(b"{}\n")
            with self.assertRaises(RecordValidationError):
                store.list_records("example")

    def test_directly_injected_unapproved_record_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-unapproved-") as raw_root:
            root = Path(raw_root)
            store = self.make_store(root)
            record = build_record("future_type", {}, record_id=FIRST_ID)
            path = Path("extension") / "data" / "records" / f"{FIRST_ID}.json"
            atomic_write_record(root, path, record)
            with self.assertRaises(RecordValidationError) as caught:
                store.get_record(FIRST_ID)
            self.assertEqual(caught.exception.code, "unapproved_record_type")
            with self.assertRaises(RecordValidationError):
                store.list_records("example")

    def test_no_delete_or_move_entry_points_exist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-surface-") as raw_root:
            store = self.make_store(Path(raw_root))
            self.assertFalse(hasattr(store, "delete_record"))
            self.assertFalse(hasattr(store, "move_record"))


class RecordCliTests(unittest.TestCase):
    def run_cli(
        self, root: Path, *arguments: str, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "core" / "src")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        prepared = list(arguments)
        if prepared and prepared[0] in {
            "get",
            "list",
            "list-events",
        }:
            prepared.insert(0, "--legacy-read")
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "core" / "tests" / "test_cli_entry.py"),
                "--root",
                str(root),
                *prepared,
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            encoding="utf-8",
            input=input_text,
            capture_output=True,
            check=False,
        )

    def test_cli_success_flow_matches_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-cli-") as raw_root:
            root = Path(raw_root)
            initialized = self.run_cli(root, "init")
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            created = self.run_cli(
                root,
                "create",
                "--type",
                "example",
                "--id",
                FIRST_ID,
                "--payload-json",
                json.dumps({"message": "CLI 생성"}, ensure_ascii=False),
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            created_payload = json.loads(created.stdout)
            self.assertTrue(created_payload["ok"])
            self.assertTrue((root / created_payload["result"]["path"]).is_file())
            fetched = self.run_cli(root, "get", "--id", FIRST_ID)
            self.assertEqual(fetched.returncode, 0, fetched.stderr)
            self.assertEqual(
                json.loads(fetched.stdout)["result"]["record"],
                created_payload["result"]["record"],
            )
            listed = self.run_cli(root, "list", "--type", "example")
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(json.loads(listed.stdout)["result"]["count"], 1)
            updated = self.run_cli(
                root,
                "update",
                "--id",
                FIRST_ID,
                "--expected-hash",
                created_payload["result"]["record"]["content_hash"],
                "--payload-json",
                '{"message":"CLI revised"}',
            )
            self.assertEqual(updated.returncode, 0, updated.stderr)
            self.assertEqual(json.loads(updated.stdout)["result"]["record"]["payload"]["message"], "CLI revised")
            appended = self.run_cli(
                root,
                "append",
                "--stream",
                "example_events",
                "--id",
                SECOND_ID,
                "--payload-json",
                '{"sequence":1}',
            )
            self.assertEqual(appended.returncode, 0, appended.stderr)
            self.assertEqual(json.loads(appended.stdout)["result"]["count"], 1)

    def test_cli_errors_use_distinct_status_and_structured_stderr(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-cli-error-") as raw_root:
            root = Path(raw_root)
            not_initialized = self.run_cli(root, "get", "--id", MISSING_ID)
            self.assertEqual(not_initialized.returncode, 2)
            self.assertEqual(json.loads(not_initialized.stderr)["error"]["kind"], "not_initialized")
            self.assertEqual(self.run_cli(root, "init").returncode, 0)
            missing = self.run_cli(root, "get", "--id", MISSING_ID)
            self.assertEqual(missing.returncode, 3)
            self.assertEqual(json.loads(missing.stderr)["error"]["kind"], "not_found")
            bad_payload = self.run_cli(root, "create", "--type", "example", "--payload-json", "[]")
            self.assertEqual(bad_payload.returncode, 2)
            self.assertEqual(json.loads(bad_payload.stderr)["error"]["kind"], "input_error")
            unapproved = self.run_cli(root, "list", "--type", "future_type")
            self.assertEqual(unapproved.returncode, 2)
            self.assertEqual(json.loads(unapproved.stderr)["error"]["kind"], "input_error")

    def test_cli_accepts_utf8_json_from_stdin(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage03-cli-stdin-") as raw_root:
            root = Path(raw_root)
            self.assertEqual(self.run_cli(root, "init").returncode, 0)
            created = self.run_cli(
                root,
                "create",
                "--type",
                "example",
                "--id",
                FIRST_ID,
                "--payload-stdin",
                input_text=json.dumps({"message": "PowerShell 안전 입력"}, ensure_ascii=False),
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            payload = json.loads(created.stdout)["result"]["record"]["payload"]
            self.assertEqual(payload, {"message": "PowerShell 안전 입력"})


if __name__ == "__main__":
    unittest.main()
