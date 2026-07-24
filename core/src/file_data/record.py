"""Strict, domain-neutral JSON record validation and atomic storage."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
from typing import Any
from uuid import UUID, uuid4


SCHEMA_VERSION = 1
REQUIRED_FIELDS = frozenset(
    {
        "id",
        "record_type",
        "schema_version",
        "created_at",
        "updated_at",
        "payload",
        "content_hash",
    }
)
PROTECTED_SEGMENTS = frozenset({".git", ".obsidian", "backup", "inputs", "outputs"})
RECORD_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
UTC_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class RecordValidationError(ValueError):
    """Raised when record bytes or fields violate the v1 contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class UnsafePathError(ValueError):
    """Raised when a target path crosses the project storage boundary."""


class DuplicateRecordError(ValueError):
    """Raised when an overwrite would replace a different record identity."""


def _canonical_body_bytes(record: Mapping[str, Any]) -> bytes:
    body = dict(record)
    body.pop("content_hash", None)
    try:
        rendered = json.dumps(
            body,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise RecordValidationError("not_json", "Record contains a non-JSON value.") from exc
    return rendered.encode("utf-8")


def compute_content_hash(record: Mapping[str, Any]) -> str:
    """Return the v1 SHA-256 hash over canonical JSON without content_hash."""

    digest = hashlib.sha256(_canonical_body_bytes(record)).hexdigest()
    return f"sha256:{digest}"


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise RecordValidationError(
            "invalid_timestamp",
            f"{field} must be an RFC 3339 UTC timestamp with second precision.",
        )
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise RecordValidationError("invalid_timestamp", f"{field} is not a real timestamp.") from exc


def _validate_json_value(value: Any, location: str = "record") -> None:
    if isinstance(value, str):
        if "\x00" in value:
            raise RecordValidationError("nul_character", f"NUL character found at {location}.")
        return
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RecordValidationError("not_json", f"Non-finite number found at {location}.")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise RecordValidationError("not_json", f"Non-string key found at {location}.")
            _validate_json_value(key, f"{location}.<key>")
            _validate_json_value(item, f"{location}.{key}")
        return
    raise RecordValidationError("not_json", f"Unsupported value found at {location}.")


def validate_record(record: Mapping[str, Any]) -> None:
    """Validate an in-memory record against the strict common-record v1 contract."""

    if not isinstance(record, Mapping):
        raise RecordValidationError("root_type", "Record root must be a JSON object.")
    if any(not isinstance(key, str) for key in record):
        raise RecordValidationError("not_json", "Record field names must be strings.")
    fields = set(record)
    missing = REQUIRED_FIELDS - fields
    extra = fields - REQUIRED_FIELDS
    if missing:
        raise RecordValidationError("missing_field", f"Missing required fields: {sorted(missing)}")
    if extra:
        raise RecordValidationError("extra_field", f"Unexpected fields: {sorted(extra)}")

    record_id = record["id"]
    if not isinstance(record_id, str):
        raise RecordValidationError("invalid_id", "id must be a lowercase canonical UUIDv4 string.")
    try:
        parsed_id = UUID(record_id)
    except (ValueError, AttributeError) as exc:
        raise RecordValidationError("invalid_id", "id must be a lowercase canonical UUIDv4 string.") from exc
    if parsed_id.version != 4 or str(parsed_id) != record_id:
        raise RecordValidationError("invalid_id", "id must be a lowercase canonical UUIDv4 string.")

    record_type = record["record_type"]
    if not isinstance(record_type, str) or RECORD_TYPE_PATTERN.fullmatch(record_type) is None:
        raise RecordValidationError("invalid_record_type", "record_type must be lower snake case.")

    version = record["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version != SCHEMA_VERSION:
        raise RecordValidationError("unsupported_version", f"schema_version must be {SCHEMA_VERSION}.")

    created = _parse_timestamp(record["created_at"], "created_at")
    updated = _parse_timestamp(record["updated_at"], "updated_at")
    if updated < created:
        raise RecordValidationError("timestamp_order", "updated_at cannot precede created_at.")

    if not isinstance(record["payload"], dict):
        raise RecordValidationError("payload_type", "payload must be a JSON object.")
    _validate_json_value(dict(record))

    content_hash = record["content_hash"]
    if not isinstance(content_hash, str) or HASH_PATTERN.fullmatch(content_hash) is None:
        raise RecordValidationError("invalid_hash", "content_hash must be sha256 followed by 64 lowercase hex digits.")
    expected_hash = compute_content_hash(record)
    if not hmac.compare_digest(content_hash, expected_hash):
        raise RecordValidationError("hash_mismatch", "content_hash does not match the canonical record body.")


def build_record(
    record_type: str,
    payload: Mapping[str, Any],
    *,
    record_id: str | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Build and validate a new neutral v1 record."""

    now = timestamp or datetime.now(UTC)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    rendered_time = now.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    record: dict[str, Any] = {
        "id": record_id or str(uuid4()),
        "record_type": record_type,
        "schema_version": SCHEMA_VERSION,
        "created_at": rendered_time,
        "updated_at": rendered_time,
        "payload": dict(payload),
    }
    record["content_hash"] = compute_content_hash(record)
    validate_record(record)
    return record


def encode_record(record: Mapping[str, Any]) -> bytes:
    """Validate and encode a record as deterministic UTF-8 JSON with one final newline."""

    validate_record(record)
    rendered = json.dumps(
        dict(record),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    )
    return f"{rendered}\n".encode("utf-8")


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RecordValidationError("duplicate_key", f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def decode_record(data: bytes) -> dict[str, Any]:
    """Decode strict UTF-8 JSON, reject duplicate keys, and validate the record."""

    if b"\x00" in data:
        raise RecordValidationError("nul_byte", "NUL byte found in record bytes.")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RecordValidationError("invalid_utf8", "Record is not strict UTF-8.") from exc
    try:
        value = json.loads(text, object_pairs_hook=_object_without_duplicates)
    except RecordValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise RecordValidationError("invalid_json", "Record is not valid JSON.") from exc
    if not isinstance(value, dict):
        raise RecordValidationError("root_type", "Record root must be a JSON object.")
    validate_record(value)
    return value


def resolve_project_path(project_root: Path | str, relative_path: Path | str) -> Path:
    """Resolve a safe project-relative path without entering protected segments."""

    root = Path(project_root).resolve(strict=True)
    raw_path = os.fspath(relative_path)
    raw_parts = re.split(r"[\\/]", raw_path)
    candidate = Path(raw_path)
    if candidate.is_absolute():
        raise UnsafePathError("Absolute paths are not allowed.")
    if not candidate.parts or any(part in {"", ".", ".."} for part in raw_parts):
        raise UnsafePathError("Path must be a normalized non-empty project-relative path.")
    if any(part.casefold() in PROTECTED_SEGMENTS for part in candidate.parts):
        raise UnsafePathError("Path enters a protected project segment.")
    target = (root / candidate).resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise UnsafePathError("Path escapes the project root.") from exc
    return target


def _validate_record_address(relative_path: Path | str, record_id: str | None = None) -> None:
    candidate = Path(relative_path)
    parts = candidate.parts
    if len(parts) != 4 or parts[:3] != ("extension", "data", "records"):
        raise UnsafePathError(
            "Common records must use extension/data/records/<uuid>.json."
        )
    if candidate.suffix != ".json":
        raise UnsafePathError("Common records must use the .json suffix.")
    if record_id is not None and candidate.stem != record_id:
        raise DuplicateRecordError("Record filename must equal its record id.")


def read_record(project_root: Path | str, relative_path: Path | str) -> dict[str, Any]:
    """Read and validate one common JSON record from a safe relative path."""

    _validate_record_address(relative_path)
    target = resolve_project_path(project_root, relative_path)
    record = decode_record(target.read_bytes())
    _validate_record_address(relative_path, record["id"])
    return record
