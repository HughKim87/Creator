"""Approved high-level record and append-only event I/O entry point."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterator
from uuid import UUID

from .record import (
    RECORD_TYPE_PATTERN,
    DuplicateRecordError,
    RecordValidationError,
    UnsafePathError,
    build_record,
    compute_content_hash,
    decode_record,
    encode_record,
    read_record,
    resolve_project_path,
    validate_record,
)


APPROVED_RECORD_TYPES = frozenset({"example"})
APPROVED_STREAMS = frozenset({"example_events"})
EMPTY_STREAM_HASH = "sha256:" + hashlib.sha256(b"").hexdigest()
_ISOLATED_TEST_WRITE_CAPABILITY = object()
_BOUND_TEST_WRITE_CAPABILITY_NONCE = object()


class RecordIOError(Exception):
    """Base class for deterministic high-level I/O failures."""

    kind = "record_io_error"
    exit_status = 7
    recoverable = False


class InputContractError(RecordIOError):
    kind = "input_error"
    exit_status = 2


class StoreNotInitializedError(InputContractError):
    kind = "not_initialized"


class LegacyReadOnlyError(InputContractError):
    kind = "legacy_read_only"


class RecordNotFoundError(RecordIOError):
    kind = "not_found"
    exit_status = 3


class ConflictError(RecordIOError):
    kind = "conflict"
    exit_status = 4
    recoverable = True


class ExpectationMismatchError(ConflictError):
    kind = "expectation_mismatch"


class ConcurrentWriteError(ConflictError):
    kind = "concurrent_write"


class _BoundIsolatedTestWriteCapability:
    """Test-only write authority bound to one verified temporary root."""

    __slots__ = ("root", "_nonce")

    def __init__(self, root: Path, nonce: object) -> None:
        if nonce is not _BOUND_TEST_WRITE_CAPABILITY_NONCE:
            raise InputContractError("invalid write capability")
        self.root = root
        self._nonce = nonce


def _bind_isolated_test_write_capability(
    project_root: Path,
    write_capability: object | None,
) -> _BoundIsolatedTestWriteCapability:
    """Fail closed unless the capability is bound to a detached temporary fixture."""

    if isinstance(write_capability, _BoundIsolatedTestWriteCapability):
        if (
            write_capability._nonce is _BOUND_TEST_WRITE_CAPABILITY_NONCE
            and write_capability.root == project_root
        ):
            return write_capability
        raise LegacyReadOnlyError(
            "legacy data is read-only; test write capability is bound to another root"
        )

    if write_capability is not _ISOLATED_TEST_WRITE_CAPABILITY:
        raise LegacyReadOnlyError(
            "legacy data is read-only; low-level writes require the isolated test capability"
        )

    temporary_root = Path(tempfile.gettempdir()).resolve(strict=True)
    try:
        relative_fixture = project_root.relative_to(temporary_root)
    except ValueError as exc:
        raise LegacyReadOnlyError(
            "legacy data is read-only; test writes require a temporary isolated root"
        ) from exc
    if relative_fixture == Path("."):
        raise LegacyReadOnlyError(
            "legacy data is read-only; the shared temporary root is not an isolated fixture"
        )

    source_project_root = Path(__file__).resolve().parents[2]
    try:
        project_root.relative_to(source_project_root)
    except ValueError:
        pass
    else:
        raise LegacyReadOnlyError(
            "legacy data is read-only; test writes cannot target the source project tree"
        )

    return _BoundIsolatedTestWriteCapability(
        project_root,
        _BOUND_TEST_WRITE_CAPABILITY_NONCE,
    )


def stream_content_hash(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _require_approved(value: str, approved: frozenset[str], label: str) -> None:
    if not isinstance(value, str) or RECORD_TYPE_PATTERN.fullmatch(value) is None:
        raise InputContractError(f"{label} must be lower snake case.")
    if value not in approved:
        raise InputContractError(f"{label} is not approved: {value}")


def _render_time(value: datetime | None) -> str:
    current = value or datetime.now(UTC)
    if current.tzinfo is None or current.utcoffset() is None:
        raise InputContractError("timestamp must be timezone-aware")
    return current.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _compact_record_bytes(record: Mapping[str, Any]) -> bytes:
    validate_record(record)
    rendered = json.dumps(
        dict(record),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if "\n" in rendered or "\r" in rendered:
        raise RecordValidationError("jsonl_line", "JSONL record must render as exactly one line.")
    return rendered.encode("utf-8") + b"\n"


def decode_stream(data: bytes, stream_name: str) -> list[dict[str, Any]]:
    """Validate a complete JSONL stream and reject partial or duplicate entries."""

    if not data:
        return []
    if not data.endswith(b"\n"):
        raise RecordValidationError("partial_jsonl", "JSONL stream must end with a newline.")
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(data.splitlines(), start=1):
        if not line:
            raise RecordValidationError("blank_jsonl_line", f"Blank JSONL line at {line_number}.")
        record = decode_record(line)
        if record["record_type"] != stream_name:
            raise RecordValidationError(
                "stream_type_mismatch",
                f"Line {line_number} type does not match stream {stream_name}.",
            )
        if record["id"] in seen_ids:
            raise RecordValidationError("duplicate_id", f"Duplicate event id at line {line_number}.")
        seen_ids.add(record["id"])
        records.append(record)
    return records


@contextmanager
def _exclusive_lock(target: Path) -> Iterator[None]:
    lock_path = target.parent / f".{target.name}.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ConcurrentWriteError(f"Write lock already exists: {lock_path.name}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="\n") as stream:
            stream.write(f"pid={os.getpid()}\n")
            stream.flush()
            os.fsync(stream.fileno())
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def _atomic_replace_stream(target: Path, data: bytes, stream_name: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        decode_stream(temporary_path.read_bytes(), stream_name)
        os.replace(temporary_path, target)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _atomic_write_record(
    project_root: Path | str,
    relative_path: Path | str,
    record: Mapping[str, Any],
    *,
    write_capability: object | None,
    overwrite: bool = False,
) -> Path:
    """Private record writer that requires the explicit isolated-test capability."""

    try:
        root = Path(project_root).resolve(strict=True)
    except FileNotFoundError as exc:
        raise InputContractError("Project root does not exist.") from exc
    _bind_isolated_test_write_capability(root, write_capability)
    encoded = encode_record(record)
    target = resolve_project_path(root, relative_path)
    if target.parent != root / "data" / "records":
        raise UnsafePathError("Common records must use data/records/<uuid>.json.")
    if target.suffix != ".json" or target.stem != record["id"]:
        raise DuplicateRecordError("Record filename must equal its record id.")
    if not target.parent.is_dir():
        raise InputContractError("Target parent directory must already exist.")

    if target.exists():
        existing = decode_record(target.read_bytes())
        if not overwrite:
            raise FileExistsError(f"Record already exists: {relative_path}")
        if existing["id"] != record["id"]:
            raise DuplicateRecordError("Overwrite cannot replace a different record id.")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        verified = decode_record(temporary_path.read_bytes())
        if verified != dict(record):
            raise RecordValidationError(
                "write_verification",
                "Temporary record differs after write.",
            )
        os.replace(temporary_path, target)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return target


class RecordStore:
    """Single approved library entry point for neutral records and event streams."""

    def __init__(
        self,
        project_root: Path | str,
        *,
        approved_record_types: frozenset[str] = APPROVED_RECORD_TYPES,
        approved_streams: frozenset[str] = APPROVED_STREAMS,
        _write_capability: object | None = None,
    ) -> None:
        root = Path(project_root)
        try:
            self.root = root.resolve(strict=True)
        except FileNotFoundError as exc:
            raise InputContractError("Project root does not exist.") from exc
        if not self.root.is_dir():
            raise InputContractError("Project root must be a directory.")
        self.approved_record_types = approved_record_types
        self.approved_streams = approved_streams
        self._write_capability = (
            None
            if _write_capability is None
            else _bind_isolated_test_write_capability(self.root, _write_capability)
        )

    @classmethod
    def _for_test(
        cls,
        project_root: Path | str,
        *,
        approved_record_types: frozenset[str] = APPROVED_RECORD_TYPES,
        approved_streams: frozenset[str] = APPROVED_STREAMS,
    ) -> RecordStore:
        """Create an explicitly writable isolated test fixture store."""

        return cls(
            project_root,
            approved_record_types=approved_record_types,
            approved_streams=approved_streams,
            _write_capability=_ISOLATED_TEST_WRITE_CAPABILITY,
        )

    def _require_writable_test_root(self) -> None:
        self._write_capability = _bind_isolated_test_write_capability(
            self.root,
            self._write_capability,
        )

    @property
    def records_directory(self) -> Path:
        return resolve_project_path(self.root, Path("data") / "records")

    @property
    def events_directory(self) -> Path:
        return resolve_project_path(self.root, Path("data") / "events")

    def initialize(self) -> dict[str, str]:
        self._require_writable_test_root()
        try:
            self.records_directory.mkdir(parents=True, exist_ok=True)
            self.events_directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RecordIOError(f"Could not initialize data directories: {exc}") from exc
        return {
            "records": "data/records",
            "events": "data/events",
        }

    def _require_initialized(self) -> None:
        if not self.records_directory.is_dir() or not self.events_directory.is_dir():
            raise StoreNotInitializedError("Run the init entry point before record operations.")

    def _record_relative_path(self, record_id: str) -> Path:
        try:
            parsed = UUID(record_id)
        except (ValueError, AttributeError) as exc:
            raise InputContractError("record id must be a lowercase canonical UUIDv4") from exc
        if parsed.version != 4 or str(parsed) != record_id:
            raise InputContractError("record id must be a lowercase canonical UUIDv4")
        return Path("data") / "records" / f"{record_id}.json"

    def _stream_relative_path(self, stream_name: str) -> Path:
        _require_approved(stream_name, self.approved_streams, "stream")
        return Path("data") / "events" / f"{stream_name}.jsonl"

    def _require_approved_record(self, record: Mapping[str, Any]) -> None:
        if record["record_type"] not in self.approved_record_types:
            raise RecordValidationError(
                "unapproved_record_type",
                f"Stored record type is not approved: {record['record_type']}",
            )

    def create_record(
        self,
        record_type: str,
        payload: Mapping[str, Any],
        *,
        record_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        self._require_writable_test_root()
        self._require_initialized()
        _require_approved(record_type, self.approved_record_types, "record_type")
        if not isinstance(payload, Mapping):
            raise InputContractError("payload must be a JSON object")
        try:
            record = build_record(record_type, payload, record_id=record_id, timestamp=timestamp)
            relative = Path("data") / "records" / f"{record['id']}.json"
            target = resolve_project_path(self.root, relative)
            with _exclusive_lock(target):
                _atomic_write_record(
                    self.root,
                    relative,
                    record,
                    write_capability=self._write_capability,
                )
                if read_record(self.root, relative) != record:
                    raise RecordIOError("Post-write record verification failed.")
            return record
        except (DuplicateRecordError, FileExistsError) as exc:
            raise ConflictError(str(exc)) from exc
        except UnsafePathError as exc:
            raise InputContractError(str(exc)) from exc

    def get_record(self, record_id: str) -> dict[str, Any]:
        self._require_initialized()
        relative = self._record_relative_path(record_id)
        try:
            record = read_record(self.root, relative)
        except FileNotFoundError as exc:
            raise RecordNotFoundError(f"Record not found: {record_id}") from exc
        self._require_approved_record(record)
        return record

    def list_records(self, record_type: str) -> list[dict[str, Any]]:
        self._require_initialized()
        _require_approved(record_type, self.approved_record_types, "record_type")
        records: list[dict[str, Any]] = []
        for path in sorted(self.records_directory.glob("*.json"), key=lambda item: item.name):
            relative = path.relative_to(self.root)
            record = read_record(self.root, relative)
            self._require_approved_record(record)
            if record["record_type"] == record_type:
                records.append(record)
        return records

    def update_record(
        self,
        record_id: str,
        payload: Mapping[str, Any],
        *,
        expected_content_hash: str,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        self._require_writable_test_root()
        self._require_initialized()
        if not isinstance(payload, Mapping):
            raise InputContractError("payload must be a JSON object")
        relative = self._record_relative_path(record_id)
        target = resolve_project_path(self.root, relative)
        with _exclusive_lock(target):
            try:
                current = read_record(self.root, relative)
            except FileNotFoundError as exc:
                raise RecordNotFoundError(f"Record not found: {record_id}") from exc
            self._require_approved_record(current)
            if current["content_hash"] != expected_content_hash:
                raise ExpectationMismatchError("Current content_hash differs from the expected value.")
            updated = dict(current)
            updated["payload"] = dict(payload)
            updated["updated_at"] = _render_time(timestamp)
            updated["content_hash"] = compute_content_hash(updated)
            validate_record(updated)
            _atomic_write_record(
                self.root,
                relative,
                updated,
                write_capability=self._write_capability,
                overwrite=True,
            )
            if read_record(self.root, relative) != updated:
                raise RecordIOError("Post-update record verification failed.")
        return updated

    def append_event(
        self,
        stream_name: str,
        payload: Mapping[str, Any],
        *,
        expected_stream_hash: str | None = None,
        event_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        self._require_writable_test_root()
        self._require_initialized()
        _require_approved(stream_name, self.approved_streams, "stream")
        if not isinstance(payload, Mapping):
            raise InputContractError("payload must be a JSON object")
        relative = self._stream_relative_path(stream_name)
        target = resolve_project_path(self.root, relative)
        event = build_record(stream_name, payload, record_id=event_id, timestamp=timestamp)
        with _exclusive_lock(target):
            before = target.read_bytes() if target.exists() else b""
            existing = decode_stream(before, stream_name)
            before_hash = stream_content_hash(before)
            if expected_stream_hash is not None and expected_stream_hash != before_hash:
                raise ExpectationMismatchError("Current stream hash differs from the expected value.")
            if any(item["id"] == event["id"] for item in existing):
                raise ConflictError(f"Duplicate event id: {event['id']}")
            after = before + _compact_record_bytes(event)
            _atomic_replace_stream(target, after, stream_name)
            verified_bytes = target.read_bytes()
            verified = decode_stream(verified_bytes, stream_name)
            if not verified or verified[-1] != event:
                raise RecordIOError("Post-append stream verification failed.")
            after_hash = stream_content_hash(verified_bytes)
        return {
            "event": event,
            "stream_hash": after_hash,
            "count": len(verified),
        }

    def list_events(self, stream_name: str) -> tuple[list[dict[str, Any]], str]:
        self._require_initialized()
        relative = self._stream_relative_path(stream_name)
        target = resolve_project_path(self.root, relative)
        data = target.read_bytes() if target.exists() else b""
        return decode_stream(data, stream_name), stream_content_hash(data)
