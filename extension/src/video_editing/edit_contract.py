from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any


CONTRACT_VERSION = 1
CONTRACT_FIELDS = frozenset(
    {
        "contract_version",
        "task_id",
        "phase",
        "time_references",
        "deliverable",
        "calibration",
        "events",
        "feedback",
        "state",
        "validation",
    }
)
TIME_REFERENCE_FIELDS = frozenset(
    {"id", "raw", "coordinate_system", "unit", "scope", "confirmed_by"}
)
DELIVERABLE_FIELDS = frozenset({"artifacts", "sequence_mode", "allowed_sidecars"})
ARTIFACT_FIELDS = frozenset({"kind", "count"})
CALIBRATION_FIELDS = frozenset(
    {"required", "status", "approved_by", "approval_evidence"}
)
EVENT_FIELDS = frozenset(
    {
        "id",
        "role",
        "source_in",
        "source_out",
        "depends_on",
        "microbeat_status",
        "continuity_reason",
    }
)
FEEDBACK_FIELDS = frozenset({"positive_locks", "defects", "untouched"})
PRESERVATION_FIELDS = frozenset({"id", "preserved"})
DEFECT_FIELDS = frozenset({"id", "source_anchor", "status", "evidence", "approved_by"})
STATE_FIELDS = frozenset(
    {
        "owner_conflict",
        "current_artifact_id",
        "source_manifest_hash",
        "source_revision_status",
    }
)
VALIDATION_FIELDS = frozenset(
    {
        "causal_space",
        "tempo_repetition",
        "av_boundary",
        "semantic_gate",
        "reviewed_by",
        "editorial_score",
    }
)

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
EVENT_ROLES_REQUIRING_CAUSE = frozenset(
    {"reaction", "escape", "result", "transition", "state_change"}
)
VALID_EVENT_ROLES = frozenset(
    {
        "setup",
        "cause",
        "discovery",
        "action",
        "attempt",
        "reaction",
        "escape",
        "result",
        "transition",
        "state_change",
        "atmosphere",
    }
)
CAUSAL_ANCHOR_ROLES = frozenset(
    {
        "setup",
        "cause",
        "discovery",
        "action",
        "attempt",
        "reaction",
        "escape",
        "result",
        "state_change",
    }
)


class EditContractError(ValueError):
    def __init__(self, issues: list[dict[str, str]]) -> None:
        self.code = issues[0]["code"] if issues else "invalid_edit_contract"
        self.issues = issues
        super().__init__(issues[0]["message"] if issues else "invalid edit contract")


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint_source_manifest(value: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class _Collector:
    def __init__(self) -> None:
        self.issues: list[dict[str, str]] = []

    def add(self, code: str, message: str, path: str) -> None:
        self.issues.append({"code": code, "message": message, "path": path})

    def object(
        self,
        value: Any,
        fields: frozenset[str],
        path: str,
    ) -> Mapping[str, Any] | None:
        if not isinstance(value, Mapping):
            self.add("invalid_contract_fields", f"{path} must be an object", path)
            return None
        if set(value) != fields:
            self.add(
                "invalid_contract_fields",
                f"{path} must contain exactly: {sorted(fields)}",
                path,
            )
        return value

    def text(self, value: Any, path: str, *, allow_empty: bool = False) -> str | None:
        if not isinstance(value, str) or (not allow_empty and not value.strip()):
            self.add("invalid_contract_fields", f"{path} must be a non-empty string", path)
            return None
        return value.strip()


def _value(value: Mapping[str, Any] | None, key: str) -> Any:
    return value.get(key) if value is not None else None


def _enum(
    collector: _Collector,
    value: Any,
    allowed: frozenset[str],
    path: str,
) -> str | None:
    rendered = collector.text(value, path)
    if rendered is not None and rendered not in allowed:
        collector.add(
            "invalid_contract_fields",
            f"{path} must be one of: {sorted(allowed)}",
            path,
        )
        return None
    return rendered


def _boolean(collector: _Collector, value: Any, path: str) -> bool | None:
    if not isinstance(value, bool):
        collector.add("invalid_contract_fields", f"{path} must be boolean", path)
        return None
    return value


def _integer(collector: _Collector, value: Any, path: str, minimum: int = 0) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        collector.add(
            "invalid_contract_fields",
            f"{path} must be an integer >= {minimum}",
            path,
        )
        return None
    return value


def _list(collector: _Collector, value: Any, path: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (nonempty and not value):
        qualifier = "a non-empty list" if nonempty else "a list"
        collector.add("invalid_contract_fields", f"{path} must be {qualifier}", path)
        return []
    return value


def _validate_time_references(value: Any, collector: _Collector) -> None:
    seen: set[str] = set()
    for index, raw in enumerate(_list(collector, value, "time_references")):
        path = f"time_references[{index}]"
        item = collector.object(raw, TIME_REFERENCE_FIELDS, path)
        identifier = collector.text(_value(item, "id"), f"{path}.id")
        collector.text(_value(item, "raw"), f"{path}.raw")
        _enum(
            collector,
            _value(item, "coordinate_system"),
            frozenset({"source", "timeline"}),
            f"{path}.coordinate_system",
        )
        _enum(
            collector,
            _value(item, "unit"),
            frozenset({"timecode", "seconds", "frames"}),
            f"{path}.unit",
        )
        collector.text(_value(item, "scope"), f"{path}.scope")
        confirmation = _enum(
            collector,
            _value(item, "confirmed_by"),
            frozenset({"user", "conversation_correction"}),
            f"{path}.confirmed_by",
        )
        if confirmation is None:
            collector.add(
                "ambiguous_time_reference",
                "time references must be normalized and confirmed before editing",
                path,
            )
        if identifier is not None:
            if identifier in seen:
                collector.add("duplicate_reference_id", f"duplicate time reference: {identifier}", path)
            seen.add(identifier)


def _validate_deliverable(
    value: Any,
    collector: _Collector,
    *,
    purpose: str | None,
) -> None:
    deliverable = collector.object(value, DELIVERABLE_FIELDS, "deliverable")
    artifacts = _list(
        collector,
        _value(deliverable, "artifacts"),
        "deliverable.artifacts",
        nonempty=True,
    )
    artifact_counts: dict[str, int] = {}
    for index, raw in enumerate(artifacts):
        path = f"deliverable.artifacts[{index}]"
        artifact = collector.object(raw, ARTIFACT_FIELDS, path)
        kind = collector.text(_value(artifact, "kind"), f"{path}.kind")
        count = _integer(collector, _value(artifact, "count"), f"{path}.count", 1)
        if kind is not None and count is not None:
            if kind in artifact_counts:
                collector.add("duplicate_artifact_kind", f"duplicate artifact kind: {kind}", path)
            artifact_counts[kind] = count
    sequence_mode = _enum(
        collector,
        _value(deliverable, "sequence_mode"),
        frozenset({"single_continuous", "multiple_explicit"}),
        "deliverable.sequence_mode",
    )
    sidecars = _list(collector, _value(deliverable, "allowed_sidecars"), "deliverable.allowed_sidecars")
    seen_sidecars: set[str] = set()
    for index, raw in enumerate(sidecars):
        item = collector.text(raw, f"deliverable.allowed_sidecars[{index}]")
        if item is not None and item in seen_sidecars:
            collector.add(
                "duplicate_sidecar",
                f"duplicate allowed sidecar: {item}",
                f"deliverable.allowed_sidecars[{index}]",
            )
        if item is not None:
            seen_sidecars.add(item)
    if purpose == "premiere_xml":
        if artifact_counts != {"premiere_xml": 1}:
            collector.add(
                "deliverable_contract_mismatch",
                "Premiere XML generation requires exactly one promised premiere_xml artifact",
                "deliverable.artifacts",
            )
        if sequence_mode != "single_continuous":
            collector.add(
                "deliverable_contract_mismatch",
                "Premiere XML generation requires one continuous sequence",
                "deliverable.sequence_mode",
            )


def _validate_calibration(value: Any, collector: _Collector, phase: str | None) -> None:
    calibration = collector.object(value, CALIBRATION_FIELDS, "calibration")
    required = _boolean(collector, _value(calibration, "required"), "calibration.required")
    status = _enum(
        collector,
        _value(calibration, "status"),
        frozenset({"pending", "approved", "rejected", "not_required"}),
        "calibration.status",
    )
    approved_by_value = _value(calibration, "approved_by")
    approved_by = None
    if approved_by_value is not None:
        approved_by = collector.text(approved_by_value, "calibration.approved_by")
    approval_evidence_value = _value(calibration, "approval_evidence")
    approval_evidence = None
    if approval_evidence_value is not None:
        approval_evidence = collector.text(
            approval_evidence_value,
            "calibration.approval_evidence",
        )
    if status == "approved" and (
        approved_by != "user" or approval_evidence is None
    ):
        collector.add(
            "calibration_approval_missing",
            "approved calibration requires explicit user ownership and approval evidence",
            "calibration",
        )
    if status != "approved" and (
        approved_by is not None or approval_evidence is not None
    ):
        collector.add(
            "stale_calibration_approval",
            "non-approved calibration must not retain approval ownership or evidence",
            "calibration",
        )
    if required is True and phase == "full" and status != "approved":
        collector.add(
            "calibration_not_approved",
            "full expansion is blocked until the editing grammar is user-approved",
            "calibration.status",
        )
    if required is True and status == "rejected":
        collector.add(
            "calibration_rejected",
            "a rejected editing grammar cannot be expanded or exported again",
            "calibration.status",
        )
    if required is True and status == "not_required":
        collector.add(
            "invalid_contract_fields",
            "calibration.status cannot be not_required when calibration.required is true",
            "calibration.status",
        )
    if required is False and status != "not_required":
        collector.add(
            "invalid_contract_fields",
            "calibration.status must be not_required when calibration.required is false",
            "calibration.status",
        )


def _validate_events(value: Any, collector: _Collector) -> None:
    events = _list(collector, value, "events", nonempty=True)
    seen: set[str] = set()
    seen_roles: dict[str, str] = {}
    for index, raw in enumerate(events):
        path = f"events[{index}]"
        event = collector.object(raw, EVENT_FIELDS, path)
        identifier = collector.text(_value(event, "id"), f"{path}.id")
        role = _enum(
            collector,
            _value(event, "role"),
            VALID_EVENT_ROLES,
            f"{path}.role",
        )
        source_in = _integer(collector, _value(event, "source_in"), f"{path}.source_in")
        source_out = _integer(collector, _value(event, "source_out"), f"{path}.source_out", 1)
        if source_in is not None and source_out is not None and source_in >= source_out:
            collector.add("invalid_event_range", "event source range must increase", path)
        dependencies = _list(collector, _value(event, "depends_on"), f"{path}.depends_on")
        causal_dependencies: list[str] = []
        for dependency_index, dependency in enumerate(dependencies):
            dependency_path = f"{path}.depends_on[{dependency_index}]"
            dependency_id = collector.text(dependency, dependency_path)
            if dependency_id is not None:
                if dependency_id not in seen:
                    collector.add(
                        "invalid_event_dependency",
                        f"event dependency must refer to an earlier event: {dependency_id}",
                        dependency_path,
                    )
                elif seen_roles.get(dependency_id) in CAUSAL_ANCHOR_ROLES:
                    causal_dependencies.append(dependency_id)
        if role in EVENT_ROLES_REQUIRING_CAUSE and not causal_dependencies:
            collector.add(
                "missing_cause_anchor",
                f"{role} must retain an earlier cause, discovery, or state anchor",
                f"{path}.depends_on",
            )
        microbeat_status = _enum(
            collector,
            _value(event, "microbeat_status"),
            frozenset({"reviewed", "uncuttable_reviewed", "pending"}),
            f"{path}.microbeat_status",
        )
        reason_value = _value(event, "continuity_reason")
        continuity_reason = None
        if reason_value is not None:
            continuity_reason = collector.text(reason_value, f"{path}.continuity_reason")
        if microbeat_status == "pending":
            collector.add(
                "microbeat_review_incomplete",
                "rough blocks cannot pass as completed detailed editing",
                f"{path}.microbeat_status",
            )
        if microbeat_status == "uncuttable_reviewed" and continuity_reason is None:
            collector.add(
                "missing_continuity_reason",
                "an uncuttable event requires a source-based continuity reason",
                f"{path}.continuity_reason",
            )
        if identifier is not None:
            if identifier in seen:
                collector.add("duplicate_event_id", f"duplicate event id: {identifier}", path)
            seen.add(identifier)
            if role is not None:
                seen_roles[identifier] = role


def _validate_feedback(value: Any, collector: _Collector) -> None:
    feedback = collector.object(value, FEEDBACK_FIELDS, "feedback")
    for collection_name, issue_code in (
        ("positive_locks", "positive_lock_regression"),
        ("untouched", "untouched_scope_regression"),
    ):
        entries = _list(collector, _value(feedback, collection_name), f"feedback.{collection_name}")
        for index, raw in enumerate(entries):
            path = f"feedback.{collection_name}[{index}]"
            entry = collector.object(raw, PRESERVATION_FIELDS, path)
            collector.text(_value(entry, "id"), f"{path}.id")
            preserved = _boolean(collector, _value(entry, "preserved"), f"{path}.preserved")
            if preserved is False:
                collector.add(issue_code, f"{collection_name} must be preserved in the next revision", path)
    defects = _list(collector, _value(feedback, "defects"), "feedback.defects")
    for index, raw in enumerate(defects):
        path = f"feedback.defects[{index}]"
        defect = collector.object(raw, DEFECT_FIELDS, path)
        collector.text(_value(defect, "id"), f"{path}.id")
        collector.text(_value(defect, "source_anchor"), f"{path}.source_anchor")
        status = _enum(
            collector,
            _value(defect, "status"),
            frozenset({"resolved", "approved_defer", "unreproduced"}),
            f"{path}.status",
        )
        evidence = collector.text(_value(defect, "evidence"), f"{path}.evidence")
        approved_by_value = _value(defect, "approved_by")
        approved_by = None
        if approved_by_value is not None:
            approved_by = collector.text(approved_by_value, f"{path}.approved_by")
        if status in {"approved_defer", "unreproduced"} and approved_by != "user":
            collector.add(
                "unresolved_defect",
                "deferred or unreproduced defects require explicit user approval",
                path,
            )
        if status is not None and evidence is None:
            collector.add("unresolved_defect", "every defect disposition requires evidence", path)


def _validate_state(
    value: Any,
    collector: _Collector,
    *,
    timeline_id: str | None,
    expected_source_manifest_hash: str | None,
) -> None:
    state = collector.object(value, STATE_FIELDS, "state")
    conflict = _boolean(collector, _value(state, "owner_conflict"), "state.owner_conflict")
    artifact_id = collector.text(_value(state, "current_artifact_id"), "state.current_artifact_id")
    source_hash = collector.text(_value(state, "source_manifest_hash"), "state.source_manifest_hash")
    revision_status = _enum(
        collector,
        _value(state, "source_revision_status"),
        frozenset({"current", "use_prohibited", "historical"}),
        "state.source_revision_status",
    )
    if conflict is True:
        collector.add("state_owner_conflict", "state owner conflict blocks editing and XML generation", "state")
    if revision_status != "current":
        collector.add(
            "invalid_source_revision",
            "only the current, non-rejected revision may be used as the XML source",
            "state.source_revision_status",
        )
    if source_hash is not None and SHA256_PATTERN.fullmatch(source_hash) is None:
        collector.add(
            "invalid_contract_fields",
            "state.source_manifest_hash must be sha256:<64 lowercase hex>",
            "state.source_manifest_hash",
        )
    if (
        source_hash is not None
        and expected_source_manifest_hash is not None
        and source_hash != expected_source_manifest_hash
    ):
        collector.add(
            "source_manifest_mismatch",
            "contract source_manifest_hash must match the timeline source manifest",
            "state.source_manifest_hash",
        )
    if timeline_id is not None and artifact_id is not None and artifact_id != timeline_id:
        collector.add(
            "current_artifact_mismatch",
            "contract current_artifact_id must match the timeline being exported",
            "state.current_artifact_id",
        )


def _validate_validation(value: Any, collector: _Collector, *, purpose: str | None) -> None:
    validation = collector.object(value, VALIDATION_FIELDS, "validation")
    statuses: dict[str, str | None] = {}
    for name in ("causal_space", "tempo_repetition", "av_boundary"):
        statuses[name] = _enum(
            collector,
            _value(validation, name),
            frozenset({"not_run", "passed", "failed", "not_applicable"}),
            f"validation.{name}",
        )
    semantic_gate = _enum(
        collector,
        _value(validation, "semantic_gate"),
        frozenset({"not_run", "passed", "failed"}),
        "validation.semantic_gate",
    )
    reviewed_by_value = _value(validation, "reviewed_by")
    reviewed_by = None
    if reviewed_by_value is not None:
        reviewed_by = collector.text(reviewed_by_value, "validation.reviewed_by")
    required_passes = all(statuses[name] == "passed" for name in statuses)
    if semantic_gate == "passed" and not required_passes:
        collector.add(
            "semantic_gate_without_normal_speed_review",
            "semantic_gate cannot pass until all three normal-speed reviews pass",
            "validation.semantic_gate",
        )
    if semantic_gate == "passed" and reviewed_by is None:
        collector.add(
            "semantic_gate_without_reviewer",
            "a passed semantic gate requires the reviewer identity",
            "validation.reviewed_by",
        )
    score = _value(validation, "editorial_score")
    score_is_number = isinstance(score, (int, float)) and not isinstance(score, bool)
    if score != "not_scored" and not score_is_number:
        collector.add(
            "invalid_contract_fields",
            "validation.editorial_score must be not_scored or a number from 0 to 100",
            "validation.editorial_score",
        )
    if score_is_number and not 0 <= score <= 100:
        collector.add(
            "invalid_contract_fields",
            "validation.editorial_score must be from 0 to 100",
            "validation.editorial_score",
        )
    if score_is_number and (semantic_gate != "passed" or not required_passes):
        collector.add(
            "editorial_score_without_semantic_gate",
            "editorial quality cannot be scored before normal-speed semantic review passes",
            "validation.editorial_score",
        )
    if purpose == "premiere_xml" and semantic_gate != "passed":
        collector.add(
            "semantic_gate_incomplete",
            "Premiere XML generation is blocked until semantic_gate passes",
            "validation.semantic_gate",
        )


def validate_edit_contract(
    value: Mapping[str, Any],
    *,
    purpose: str | None = None,
    timeline_id: str | None = None,
    expected_source_manifest_hash: str | None = None,
) -> dict[str, Any]:
    collector = _Collector()
    contract = collector.object(value, CONTRACT_FIELDS, "contract")
    if _value(contract, "contract_version") != CONTRACT_VERSION:
        collector.add(
            "invalid_contract_fields",
            f"contract_version must be {CONTRACT_VERSION}",
            "contract.contract_version",
        )
    task_id = collector.text(_value(contract, "task_id"), "contract.task_id")
    if task_id is not None and SLUG_PATTERN.fullmatch(task_id) is None:
        collector.add("invalid_contract_fields", "task_id must be a lowercase ASCII slug", "contract.task_id")
    phase = _enum(
        collector,
        _value(contract, "phase"),
        frozenset({"calibration", "full"}),
        "contract.phase",
    )
    _validate_time_references(_value(contract, "time_references"), collector)
    _validate_deliverable(_value(contract, "deliverable"), collector, purpose=purpose)
    _validate_calibration(_value(contract, "calibration"), collector, phase)
    _validate_events(_value(contract, "events"), collector)
    _validate_feedback(_value(contract, "feedback"), collector)
    _validate_state(
        _value(contract, "state"),
        collector,
        timeline_id=timeline_id,
        expected_source_manifest_hash=expected_source_manifest_hash,
    )
    _validate_validation(_value(contract, "validation"), collector, purpose=purpose)
    if collector.issues:
        raise EditContractError(collector.issues)
    return dict(value)


def inspect_edit_contract(
    value: Mapping[str, Any],
    *,
    purpose: str | None = None,
    timeline_id: str | None = None,
    expected_source_manifest_hash: str | None = None,
) -> dict[str, Any]:
    try:
        contract = validate_edit_contract(
            value,
            purpose=purpose,
            timeline_id=timeline_id,
            expected_source_manifest_hash=expected_source_manifest_hash,
        )
    except EditContractError as exc:
        report: dict[str, Any] = {"ok": False, "errors": exc.issues}
    else:
        report = {
            "ok": True,
            "task_id": contract["task_id"],
            "phase": contract["phase"],
            "event_count": len(contract["events"]),
            "checks": [
                "time_reference_confirmation",
                "deliverable_contract",
                "calibration_approval",
                "event_dependencies",
                "microbeat_completion",
                "feedback_regression",
                "state_owner",
                "normal_speed_semantic_review",
            ],
        }
    report["fingerprint"] = "sha256:" + hashlib.sha256(
        _canonical(value).encode("utf-8")
    ).hexdigest()
    return report
