"""Design and execution contracts for staged work.

The work-state contract keeps the execution pointer small.  The phase design
document remains the owner of detailed scope and gates; this module only
validates the pointer, its tier, and its content fingerprint.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .record import UnsafePathError, resolve_project_path
from .store import InputContractError


EXECUTION_TIERS = frozenset({"quick", "standard", "controlled"})
EXECUTION_FIELDS = frozenset({"tier", "phase_id", "design_ref", "design_fingerprint"})
OPTIONAL_REQUEST_FIELDS = frozenset({"execution"})
DESIGN_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_DESIGN_POINTER_FIELDS = frozenset({"phase_id", "design_ref", "design_fingerprint"})


class DesignContractError(InputContractError):
    """Base error for an invalid or incomplete execution design pointer."""

    kind = "design_contract_error"


class DesignRequiredError(DesignContractError):
    """Raised when a controlled mutation has no complete design pointer."""

    kind = "design_required"


class DesignInvalidatedError(DesignContractError):
    """Raised when the design document no longer matches its approved hash."""

    kind = "design_invalidated"


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DesignContractError(f"{field} must be a non-empty string")
    return value


def _nullable_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _non_empty_string(value, field)


def normalize_execution(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize one optional execution pointer."""

    if not isinstance(value, Mapping):
        raise DesignContractError("execution must be an object")
    fields = set(value)
    if "tier" not in fields or fields - EXECUTION_FIELDS:
        raise DesignContractError(
            f"execution must contain tier and only these fields: {sorted(EXECUTION_FIELDS)}"
        )
    tier = _non_empty_string(value["tier"], "execution.tier")
    if tier not in EXECUTION_TIERS:
        raise DesignContractError(f"unsupported execution tier: {tier}")
    normalized = {
        "tier": tier,
        "phase_id": _nullable_string(value.get("phase_id"), "execution.phase_id"),
        "design_ref": _nullable_string(value.get("design_ref"), "execution.design_ref"),
        "design_fingerprint": _nullable_string(
            value.get("design_fingerprint"), "execution.design_fingerprint"
        ),
    }
    fingerprint = normalized["design_fingerprint"]
    if fingerprint is not None and DESIGN_HASH_PATTERN.fullmatch(fingerprint) is None:
        raise DesignContractError("execution.design_fingerprint must be sha256:<64 lowercase hex>")
    pointer_values = [normalized[field] for field in _DESIGN_POINTER_FIELDS]
    if tier in {"quick", "standard"} and any(pointer_values):
        raise DesignContractError(
            f"{tier} execution cannot persist a phase design pointer"
        )
    if tier == "controlled" and any(value is None for value in pointer_values):
        raise DesignRequiredError(
            "controlled execution requires phase_id, design_ref, and design_fingerprint"
        )
    return normalized


def request_execution(request: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the explicit execution pointer, or None for legacy requests."""

    value = request.get("execution")
    if value is None:
        return None
    return normalize_execution(value)


def compute_design_fingerprint(
    project_root: Path | str | None,
    source: Mapping[str, Any] | bytes | str | Path,
) -> str:
    """Compute a stable design hash from JSON-like content or a project file."""

    if isinstance(source, Mapping):
        rendered = json.dumps(
            dict(source),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    elif isinstance(source, bytes):
        rendered = source
    else:
        if project_root is None:
            raise DesignContractError("project_root is required when hashing a design path")
        try:
            target = resolve_project_path(project_root, source)
        except UnsafePathError as exc:
            raise DesignContractError(str(exc)) from exc
        if not target.is_file():
            raise DesignRequiredError(f"design document does not exist: {source}")
        try:
            rendered = target.read_bytes()
        except OSError as exc:
            raise DesignRequiredError(f"design document cannot be read: {source}") from exc
    return f"sha256:{hashlib.sha256(rendered).hexdigest()}"


def validate_execution_contract(
    project_root: Path | str,
    execution: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Validate the pointer and, for controlled work, the current design file."""

    if execution is None:
        return None
    normalized = normalize_execution(execution)
    if normalized["tier"] != "controlled":
        return normalized
    actual = compute_design_fingerprint(project_root, normalized["design_ref"])
    if actual != normalized["design_fingerprint"]:
        raise DesignInvalidatedError(
            "controlled phase design fingerprint changed; reapproval is required"
        )
    return normalized


def compare_request_contract(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> dict[str, Any]:
    """Detect request or design changes that invalidate queued execution."""

    comparable_fields = (
        "desired_outcome",
        "authorized_actions",
        "excluded_scope",
        "input_refs",
        "protection_boundaries",
        "required_decisions",
        "verification_levels",
    )
    changed = [field for field in comparable_fields if previous.get(field) != current.get(field)]
    previous_execution = request_execution(previous)
    current_execution = request_execution(current)
    if previous_execution != current_execution:
        changed.append("execution")
    return {
        "invalidated": bool(changed),
        "reapproval_required": bool(changed),
        "changed_fields": changed,
        "previous_execution": previous_execution,
        "current_execution": current_execution,
    }
