"""Strict persistence and lifecycle validation for video-task state."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 2
STATE_FILENAME = "state.json"
PORTABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
VALIDATION_LEVELS = frozenset(
    {
        "generated",
        "parsed",
        "structure_validated",
        "tool_validated",
        "app_validated",
        "user_validated",
    }
)
VALIDATION_LEVEL_ORDER = (
    "generated",
    "parsed",
    "structure_validated",
    "tool_validated",
    "app_validated",
    "user_validated",
)
OUTPUT_STATUSES = frozenset({"current", "superseded", "failed"})
APPROVAL_STATES = frozenset(
    {"not_required", "pending", "approved", "revision_requested"}
)
NEXT_USE_STATES = frozenset({"eligible", "ineligible"})

_STATE_KEYS = frozenset(
    {
        "schema_version",
        "project_id",
        "current_stage",
        "reference_input",
        "outputs",
        "next_action",
        "blocker",
        "user_decision",
        "validation_level",
    }
)
_REFERENCE_KEYS = frozenset({"source_id", "path", "fingerprint"})
_FINGERPRINT_KEYS = frozenset({"algorithm", "digest", "size_bytes"})
_OUTPUT_KEYS = frozenset(
    {
        "role",
        "version",
        "path",
        "source_id",
        "status",
        "supersedes",
        "integrity",
        "validation_level",
        "approval_state",
        "next_use",
    }
)


class StateValidationError(ValueError):
    """The state payload or requested project location violates the contract."""


class StateIOError(RuntimeError):
    """A valid state payload could not be safely read or written."""


def _expect_object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StateValidationError(f"{field} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise StateValidationError(f"{field} keys must be strings")
    return value


def _expect_exact_keys(data: dict[str, Any], expected: frozenset[str], field: str) -> None:
    actual = set(data)
    unknown = actual - expected
    missing = expected - actual
    if unknown:
        raise StateValidationError(f"{field} has unknown fields: {sorted(unknown)}")
    if missing:
        raise StateValidationError(f"{field} is missing fields: {sorted(missing)}")


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StateValidationError(f"{field} must be a non-empty string")
    return value


def _require_portable_id(value: object, field: str) -> str:
    identifier = _require_string(value, field)
    if not PORTABLE_ID_PATTERN.fullmatch(identifier):
        raise StateValidationError(f"{field} must be a portable lowercase ASCII identifier")
    return identifier


def _require_optional_string(value: object, field: str) -> None:
    if value is not None:
        _require_string(value, field)


def _require_validation_level(value: object, field: str) -> str:
    level = _require_string(value, field)
    if level not in VALIDATION_LEVELS:
        raise StateValidationError(f"{field} has unknown validation level {level!r}")
    return level


def _require_choice(value: object, field: str, choices: frozenset[str]) -> str:
    choice = _require_string(value, field)
    if choice not in choices:
        raise StateValidationError(f"{field} has unknown value {choice!r}")
    return choice


def _require_relative_path(value: object, field: str, prefix: tuple[str, ...]) -> str:
    raw_path = _require_string(value, field)
    if "\\" in raw_path:
        raise StateValidationError(f"{field} must use forward slashes")
    raw_parts = raw_path.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise StateValidationError(f"{field} must not contain empty, dot, or parent segments")
    path = PurePosixPath(raw_path)
    if path.is_absolute():
        raise StateValidationError(f"{field} must be a safe repository-relative path")
    if path.parts[: len(prefix)] != prefix or len(path.parts) <= len(prefix):
        expected = "/".join(prefix) + "/"
        raise StateValidationError(f"{field} must be below {expected}")
    return path.as_posix()


def _require_integrity(value: object, field: str) -> tuple[str, int]:
    integrity = _expect_object(value, field)
    _expect_exact_keys(integrity, _FINGERPRINT_KEYS, field)
    if integrity["algorithm"] != "sha256":
        raise StateValidationError(f"{field}.algorithm must be 'sha256'")
    digest = integrity["digest"]
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        raise StateValidationError(
            f"{field}.digest must be 64 lowercase hex characters"
        )
    size_bytes = integrity["size_bytes"]
    if type(size_bytes) is not int or size_bytes < 0:
        raise StateValidationError(f"{field}.size_bytes must be a non-negative integer")
    return digest, size_bytes


def validate_state(payload: object, expected_project_id: str | None = None) -> None:
    """Validate one complete schema-v2 state payload without mutating it."""

    data = _expect_object(payload, "state")
    _expect_exact_keys(data, _STATE_KEYS, "state")

    version = data["schema_version"]
    if type(version) is not int or version != SCHEMA_VERSION:
        raise StateValidationError(
            f"state.schema_version must be integer {SCHEMA_VERSION}"
        )

    project_id = _require_portable_id(data["project_id"], "state.project_id")
    if expected_project_id is not None:
        requested_id = _require_portable_id(expected_project_id, "expected_project_id")
        if project_id != requested_id:
            raise StateValidationError(
                f"state.project_id {project_id!r} does not match {requested_id!r}"
            )

    _require_portable_id(data["current_stage"], "state.current_stage")
    _require_portable_id(data["next_action"], "state.next_action")
    _require_optional_string(data["blocker"], "state.blocker")
    _require_optional_string(data["user_decision"], "state.user_decision")
    _require_validation_level(data["validation_level"], "state.validation_level")

    reference = _expect_object(data["reference_input"], "state.reference_input")
    _expect_exact_keys(reference, _REFERENCE_KEYS, "state.reference_input")
    source_id = _require_portable_id(
        reference["source_id"], "state.reference_input.source_id"
    )
    _require_relative_path(reference["path"], "state.reference_input.path", ("inputs",))

    _require_integrity(
        reference["fingerprint"], "state.reference_input.fingerprint"
    )

    outputs = data["outputs"]
    if not isinstance(outputs, list):
        raise StateValidationError("state.outputs must be a list")
    seen_paths: set[str] = set()
    seen_role_versions: set[tuple[str, int]] = set()
    current_roles: set[str] = set()
    output_records: list[dict[str, Any]] = []
    for index, value in enumerate(outputs):
        field = f"state.outputs[{index}]"
        output = _expect_object(value, field)
        _expect_exact_keys(output, _OUTPUT_KEYS, field)
        role = _require_portable_id(output["role"], f"{field}.role")
        version_number = output["version"]
        if type(version_number) is not int or version_number < 1:
            raise StateValidationError(f"{field}.version must be a positive integer")
        role_version = (role, version_number)
        if role_version in seen_role_versions:
            raise StateValidationError(
                f"{field} duplicates role/version {role!r}/{version_number}"
            )
        seen_role_versions.add(role_version)
        output_path = _require_relative_path(
            output["path"], f"{field}.path", ("outputs", project_id)
        )
        if output_path in seen_paths:
            raise StateValidationError(f"{field}.path duplicates {output_path!r}")
        seen_paths.add(output_path)
        output_source_id = _require_portable_id(output["source_id"], f"{field}.source_id")
        if output_source_id != source_id:
            raise StateValidationError(
                f"{field}.source_id must match state.reference_input.source_id"
            )
        status = _require_choice(output["status"], f"{field}.status", OUTPUT_STATUSES)
        if status == "current":
            if role in current_roles:
                raise StateValidationError(f"state.outputs has multiple current {role!r} outputs")
            current_roles.add(role)
        supersedes_raw = output["supersedes"]
        supersedes = None
        if supersedes_raw is not None:
            supersedes = _require_relative_path(
                supersedes_raw, f"{field}.supersedes", ("outputs", project_id)
            )
            if supersedes == output_path:
                raise StateValidationError(f"{field} cannot supersede itself")
        if status == "failed" and supersedes is not None:
            raise StateValidationError(f"{field}.supersedes must be null for failed output")
        _require_integrity(output["integrity"], f"{field}.integrity")
        validation_level = _require_validation_level(
            output["validation_level"], f"{field}.validation_level"
        )
        approval_state = _require_choice(
            output["approval_state"], f"{field}.approval_state", APPROVAL_STATES
        )
        next_use = _require_choice(
            output["next_use"], f"{field}.next_use", NEXT_USE_STATES
        )
        if next_use == "eligible":
            if status != "current":
                raise StateValidationError(f"{field} must be current to be eligible")
            if approval_state not in {"not_required", "approved"}:
                raise StateValidationError(
                    f"{field} requires resolved approval to be eligible"
                )
            if VALIDATION_LEVEL_ORDER.index(validation_level) < VALIDATION_LEVEL_ORDER.index(
                "structure_validated"
            ):
                raise StateValidationError(
                    f"{field} requires structure validation to be eligible"
                )
        output_records.append(
            {
                "field": field,
                "role": role,
                "version": version_number,
                "path": output_path,
                "source_id": output_source_id,
                "status": status,
                "supersedes": supersedes,
            }
        )

    records_by_path = {record["path"]: record for record in output_records}
    superseded_targets: set[str] = set()
    for record in output_records:
        supersedes = record["supersedes"]
        if supersedes is None:
            continue
        target = records_by_path.get(supersedes)
        if target is None:
            raise StateValidationError(
                f"{record['field']}.supersedes references an unrecorded output"
            )
        if supersedes in superseded_targets:
            raise StateValidationError(f"output {supersedes!r} is superseded more than once")
        superseded_targets.add(supersedes)
        if target["status"] != "superseded":
            raise StateValidationError(
                f"{record['field']}.supersedes target must have superseded status"
            )
        if target["role"] != record["role"] or target["source_id"] != record["source_id"]:
            raise StateValidationError(
                f"{record['field']}.supersedes target must share role and source_id"
            )
        if target["version"] >= record["version"]:
            raise StateValidationError(
                f"{record['field']}.supersedes target must have a lower version"
            )

    for record in output_records:
        if record["status"] == "superseded" and record["path"] not in superseded_targets:
            raise StateValidationError(
                f"{record['field']} is superseded but no newer output references it"
            )


def validate_output_files(
    workspace_root: str | os.PathLike[str], payload: object
) -> None:
    """Verify every recorded output exists inside the workspace and matches integrity."""

    validate_state(payload)
    try:
        root = Path(workspace_root).resolve(strict=True)
    except OSError as exc:
        raise StateIOError("workspace root does not exist") from exc
    data = _expect_object(payload, "state")
    outputs = data["outputs"]
    for index, value in enumerate(outputs):
        field = f"state.outputs[{index}]"
        output = _expect_object(value, field)
        relative_path = PurePosixPath(output["path"])
        candidate = root.joinpath(*relative_path.parts)
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError) as exc:
            raise StateIOError(f"{field}.path is missing or outside the workspace") from exc
        if not resolved.is_file():
            raise StateIOError(f"{field}.path is not a file")
        digest = hashlib.sha256()
        size_bytes = 0
        try:
            with resolved.open("rb") as output_file:
                for chunk in iter(lambda: output_file.read(1024 * 1024), b""):
                    digest.update(chunk)
                    size_bytes += len(chunk)
        except OSError as exc:
            raise StateIOError(f"cannot read {field}.path for integrity validation") from exc
        expected_digest, expected_size = _require_integrity(
            output["integrity"], f"{field}.integrity"
        )
        if digest.hexdigest() != expected_digest or size_bytes != expected_size:
            raise StateIOError(f"{field}.integrity does not match the recorded file")


def _project_directory(outputs_root: str | os.PathLike[str], project_id: str) -> Path:
    _require_portable_id(project_id, "project_id")
    root = Path(outputs_root).resolve(strict=False)
    project_directory = root / project_id
    try:
        project_directory.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise StateValidationError("project directory escapes the outputs root") from exc
    return project_directory


def state_path(outputs_root: str | os.PathLike[str], project_id: str) -> Path:
    """Return the validated state path without reading or writing it."""

    return _project_directory(outputs_root, project_id) / STATE_FILENAME


def save_state(
    outputs_root: str | os.PathLike[str], project_id: str, payload: object
) -> Path:
    """Validate and atomically replace one project's state file."""

    validate_state(payload, expected_project_id=project_id)
    project_directory = _project_directory(outputs_root, project_id)
    try:
        project_directory.mkdir(parents=True, exist_ok=True)
        root = Path(outputs_root).resolve(strict=True)
        resolved_project_directory = project_directory.resolve(strict=True)
        resolved_project_directory.relative_to(root)
    except (OSError, ValueError) as exc:
        raise StateIOError("cannot create a safe project state directory") from exc

    target = resolved_project_directory / STATE_FILENAME
    if target.exists() or target.is_symlink():
        try:
            target.resolve(strict=False).relative_to(root)
        except (OSError, ValueError) as exc:
            raise StateIOError("state file resolves outside the outputs root") from exc

    encoded = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".state.", suffix=".tmp", dir=resolved_project_directory
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as temporary_file:
            temporary_file.write(encoded)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, target)
    except OSError as exc:
        raise StateIOError("atomic state write failed; prior state was preserved") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
    return target


def load_state(outputs_root: str | os.PathLike[str], project_id: str) -> dict[str, Any]:
    """Read and strictly validate one project's state file."""

    target = state_path(outputs_root, project_id)
    root = Path(outputs_root).resolve(strict=False)
    if not target.exists():
        raise StateIOError(f"state file does not exist for project {project_id!r}")
    try:
        target.resolve(strict=True).relative_to(root)
        raw = target.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise StateIOError(f"cannot safely read state for project {project_id!r}") from exc
    validate_state(payload, expected_project_id=project_id)
    return _expect_object(payload, "state")
