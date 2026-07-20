"""Contract serialization (schema version 2).

Policy (fixed for this version, fail-closed):
- Every envelope carries ``schema_version``. Unknown or missing versions are
  rejected, never guessed.
- Unknown fields are rejected in version 2; nothing is silently dropped.
- Times serialize as UTC ISO-8601 with explicit offset; naive times are
  rejected on both directions.
- Ids, enums, and hashes go through the strict domain validators.
- Serialized output is canonical: sorted keys, fixed separators, UTF-8, so
  identical inputs are byte-identical.
- Logs and payloads never carry secrets or full source content, only hashes
  and identifiers.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import cast

from video_workflow.domain.enums import (
    ActorKind,
    ApprovalDecision,
    ApprovalType,
    ArtifactRole,
    EventKind,
    GenerationStatus,
    LifecycleStatus,
    Phase,
)
from video_workflow.domain.errors import DomainValidationError, SerializationError
from video_workflow.domain.ids import (
    ArtifactId,
    CommandId,
    EventId,
    GenerationId,
    ProjectId,
    SourceId,
)
from video_workflow.domain.records import (
    ApprovalRecord,
    ApprovalTarget,
    ArtifactRecord,
    FailureRecord,
    WorkflowEvent,
)
from video_workflow.domain.state import GenerationState, ProcessedCommand, ProjectState
from video_workflow.domain.values import Actor, ActorProvenance, SourceFingerprint

SCHEMA_VERSION = 2

_KINDS = ("WorkflowEvent", "ApprovalRecord", "ArtifactRecord", "FailureRecord", "ProjectState")

Serializable = WorkflowEvent | ApprovalRecord | ArtifactRecord | FailureRecord | ProjectState


def _dt(value: datetime) -> str:
    return value.isoformat()


def _parse_dt(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise SerializationError(f"{field} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise SerializationError(f"{field} is not ISO-8601: {value!r}") from exc
    offset = parsed.utcoffset()
    if parsed.tzinfo is None or offset is None or offset.total_seconds() != 0:
        raise SerializationError(f"{field} must be UTC with explicit offset")
    return parsed


def _expect_mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SerializationError(f"{field} must be an object")
    for key in value:
        if not isinstance(key, str):
            raise SerializationError(f"{field} keys must be strings")
    return cast(dict[str, object], value)


def _expect_keys(data: dict[str, object], required: frozenset[str], field: str) -> None:
    actual = set(data)
    unknown = actual - required
    missing = required - actual
    if unknown:
        raise SerializationError(
            f"{field} has unknown fields (rejected by v{SCHEMA_VERSION} policy): {sorted(unknown)}"
        )
    if missing:
        raise SerializationError(f"{field} is missing fields: {sorted(missing)}")


def _fingerprint_dict(value: SourceFingerprint) -> dict[str, object]:
    return {
        "algorithm": value.algorithm,
        "digest": value.digest,
        "size_bytes": value.size_bytes,
    }


_FINGERPRINT_KEYS = frozenset({"algorithm", "digest", "size_bytes"})


def _parse_fingerprint(value: object, field: str) -> SourceFingerprint:
    data = _expect_mapping(value, field)
    _expect_keys(data, _FINGERPRINT_KEYS, field)
    algorithm = data["algorithm"]
    digest = data["digest"]
    size = data["size_bytes"]
    if not isinstance(algorithm, str) or not isinstance(digest, str):
        raise SerializationError(f"{field} algorithm/digest must be strings")
    if isinstance(size, bool) or not isinstance(size, int):
        raise SerializationError(f"{field}.size_bytes must be an integer")
    return SourceFingerprint(algorithm=algorithm, digest=digest, size_bytes=size)


def _actor_dict(value: Actor) -> dict[str, object]:
    provenance: dict[str, object] | None = None
    if value.provenance is not None:
        provenance = {
            "channel": value.provenance.channel,
            "session_id": value.provenance.session_id,
            "decided_at": _dt(value.provenance.decided_at),
        }
    return {"kind": value.kind.value, "actor_id": value.actor_id, "provenance": provenance}


_ACTOR_KEYS = frozenset({"kind", "actor_id", "provenance"})
_PROVENANCE_KEYS = frozenset({"channel", "session_id", "decided_at"})


def _parse_actor(value: object, field: str) -> Actor:
    data = _expect_mapping(value, field)
    _expect_keys(data, _ACTOR_KEYS, field)
    provenance_raw = data["provenance"]
    provenance: ActorProvenance | None = None
    if provenance_raw is not None:
        pdata = _expect_mapping(provenance_raw, f"{field}.provenance")
        _expect_keys(pdata, _PROVENANCE_KEYS, f"{field}.provenance")
        channel = pdata["channel"]
        session_id = pdata["session_id"]
        if not isinstance(channel, str) or not isinstance(session_id, str):
            raise SerializationError(f"{field}.provenance strings required")
        provenance = ActorProvenance(
            channel=channel,
            session_id=session_id,
            decided_at=_parse_dt(pdata["decided_at"], f"{field}.provenance.decided_at"),
        )
    actor_id = data["actor_id"]
    if not isinstance(actor_id, str):
        raise SerializationError(f"{field}.actor_id must be a string")
    return Actor(kind=ActorKind.parse(data["kind"]), actor_id=actor_id, provenance=provenance)


def _target_dict(value: ApprovalTarget) -> dict[str, object]:
    return {
        "generation_id": value.generation_id.value if value.generation_id else None,
        "content_hash": value.content_hash,
    }


_TARGET_KEYS = frozenset({"generation_id", "content_hash"})


def _parse_target(value: object, field: str) -> ApprovalTarget:
    data = _expect_mapping(value, field)
    _expect_keys(data, _TARGET_KEYS, field)
    generation_raw = data["generation_id"]
    content_raw = data["content_hash"]
    generation = GenerationId.parse(generation_raw) if generation_raw is not None else None
    if content_raw is not None and not isinstance(content_raw, str):
        raise SerializationError(f"{field}.content_hash must be a string or null")
    return ApprovalTarget(generation_id=generation, content_hash=content_raw)


def serialize(value: Serializable) -> dict[str, object]:
    """Serialize a domain object into a versioned envelope."""
    data: dict[str, object]
    if isinstance(value, WorkflowEvent):
        data = {
            "event_id": value.event_id.value,
            "project_id": value.project_id.value,
            "kind": value.kind.value,
            "occurred_at": _dt(value.occurred_at),
            "actor": _actor_dict(value.actor),
            "payload": [[key, item] for key, item in value.payload],
        }
    elif isinstance(value, ApprovalRecord):
        data = {
            "approval_id": value.approval_id.value,
            "approval_type": value.approval_type.value,
            "decision": value.decision.value,
            "actor": _actor_dict(value.actor),
            "target": _target_dict(value.target),
            "decided_at": _dt(value.decided_at),
        }
    elif isinstance(value, ArtifactRecord):
        data = {
            "artifact_id": value.artifact_id.value,
            "project_id": value.project_id.value,
            "generation_id": value.generation_id.value,
            "source_id": value.source_id.value,
            "role": value.role.value,
            "content_hash": value.content_hash,
            "parent_ids": [parent.value for parent in value.parent_ids],
            "recorded_at": _dt(value.recorded_at),
        }
    elif isinstance(value, FailureRecord):
        data = {
            "failure_id": value.failure_id.value,
            "objective": value.objective,
            "failure_fingerprint": value.failure_fingerprint,
            "evidence_refs": list(value.evidence_refs),
            "occurred_at": _dt(value.occurred_at),
        }
    elif isinstance(value, ProjectState):
        data = {
            "project_id": value.project_id.value,
            "phase": value.phase.value,
            "lifecycle": value.lifecycle.value,
            "source_id": value.source_id.value if value.source_id else None,
            "source_fingerprint": (
                _fingerprint_dict(value.source_fingerprint) if value.source_fingerprint else None
            ),
            "generations": [
                {
                    "generation_id": generation.generation_id.value,
                    "status": generation.status.value,
                    "baseline_hash": generation.baseline_hash,
                }
                for generation in value.generations
            ],
            "artifacts": [serialize(record) for record in value.artifacts],
            "approvals": [serialize(record) for record in value.approvals],
            "failures": [serialize(record) for record in value.failures],
            "processed_commands": [
                {
                    "command_id": processed.command_id.value,
                    "request_digest": processed.request_digest,
                }
                for processed in value.processed_commands
            ],
        }
    else:
        raise SerializationError(f"unsupported type {type(value).__name__}")
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": type(value).__name__,
        "data": data,
    }


def canonical_json_bytes(value: Serializable) -> bytes:
    """Byte-identical canonical serialization for identical inputs."""
    return json.dumps(
        serialize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


_EVENT_KEYS = frozenset({"event_id", "project_id", "kind", "occurred_at", "actor", "payload"})
_APPROVAL_KEYS = frozenset(
    {"approval_id", "approval_type", "decision", "actor", "target", "decided_at"}
)
_ARTIFACT_KEYS = frozenset(
    {
        "artifact_id",
        "project_id",
        "generation_id",
        "source_id",
        "role",
        "content_hash",
        "parent_ids",
        "recorded_at",
    }
)
_FAILURE_KEYS = frozenset(
    {"failure_id", "objective", "failure_fingerprint", "evidence_refs", "occurred_at"}
)
_STATE_KEYS = frozenset(
    {
        "project_id",
        "phase",
        "lifecycle",
        "source_id",
        "source_fingerprint",
        "generations",
        "artifacts",
        "approvals",
        "failures",
        "processed_commands",
    }
)
_GENERATION_KEYS = frozenset({"generation_id", "status", "baseline_hash"})
_PROCESSED_KEYS = frozenset({"command_id", "request_digest"})


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise SerializationError(f"{field} must be a string")
    return value


def _require_list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise SerializationError(f"{field} must be a list")
    return cast(list[object], value)


def deserialize(payload: object) -> Serializable:
    """Strictly deserialize a versioned envelope. Fail-closed on unknowns."""
    envelope = _expect_mapping(payload, "envelope")
    _expect_keys(envelope, frozenset({"schema_version", "kind", "data"}), "envelope")
    version = envelope["schema_version"]
    if version != SCHEMA_VERSION:
        raise SerializationError(
            f"unknown schema_version {version!r}; only {SCHEMA_VERSION} is accepted"
        )
    kind = envelope["kind"]
    if kind not in _KINDS:
        raise SerializationError(f"unknown kind {kind!r}")
    data = _expect_mapping(envelope["data"], "data")
    try:
        if kind == "WorkflowEvent":
            return _deserialize_event(data)
        if kind == "ApprovalRecord":
            return _deserialize_approval(data)
        if kind == "ArtifactRecord":
            return _deserialize_artifact(data)
        if kind == "FailureRecord":
            return _deserialize_failure(data)
        return _deserialize_state(data)
    except DomainValidationError as exc:
        raise SerializationError(str(exc)) from exc


def _deserialize_event(data: dict[str, object]) -> WorkflowEvent:
    _expect_keys(data, _EVENT_KEYS, "WorkflowEvent")
    payload_items: list[tuple[str, str]] = []
    for entry in _require_list(data["payload"], "WorkflowEvent.payload"):
        if (
            not isinstance(entry, list)
            or len(entry) != 2
            or not isinstance(entry[0], str)
            or not isinstance(entry[1], str)
        ):
            raise SerializationError("WorkflowEvent.payload entries must be [str, str]")
        payload_items.append((entry[0], entry[1]))
    return WorkflowEvent(
        event_id=EventId.parse(data["event_id"]),
        project_id=ProjectId.parse(data["project_id"]),
        kind=EventKind.parse(data["kind"]),
        occurred_at=_parse_dt(data["occurred_at"], "WorkflowEvent.occurred_at"),
        actor=_parse_actor(data["actor"], "WorkflowEvent.actor"),
        payload=tuple(payload_items),
    )


def _deserialize_approval(data: dict[str, object]) -> ApprovalRecord:
    _expect_keys(data, _APPROVAL_KEYS, "ApprovalRecord")
    return ApprovalRecord(
        approval_id=EventId.parse(data["approval_id"]),
        approval_type=ApprovalType.parse(data["approval_type"]),
        decision=ApprovalDecision.parse(data["decision"]),
        actor=_parse_actor(data["actor"], "ApprovalRecord.actor"),
        target=_parse_target(data["target"], "ApprovalRecord.target"),
        decided_at=_parse_dt(data["decided_at"], "ApprovalRecord.decided_at"),
    )


def _deserialize_artifact(data: dict[str, object]) -> ArtifactRecord:
    _expect_keys(data, _ARTIFACT_KEYS, "ArtifactRecord")
    parents = tuple(
        ArtifactId.parse(entry)
        for entry in _require_list(data["parent_ids"], "ArtifactRecord.parent_ids")
    )
    return ArtifactRecord(
        artifact_id=ArtifactId.parse(data["artifact_id"]),
        project_id=ProjectId.parse(data["project_id"]),
        generation_id=GenerationId.parse(data["generation_id"]),
        source_id=SourceId.parse(data["source_id"]),
        role=ArtifactRole.parse(data["role"]),
        content_hash=_require_str(data["content_hash"], "ArtifactRecord.content_hash"),
        parent_ids=parents,
        recorded_at=_parse_dt(data["recorded_at"], "ArtifactRecord.recorded_at"),
    )


def _deserialize_failure(data: dict[str, object]) -> FailureRecord:
    _expect_keys(data, _FAILURE_KEYS, "FailureRecord")
    refs = tuple(
        _require_str(entry, "FailureRecord.evidence_refs entry")
        for entry in _require_list(data["evidence_refs"], "FailureRecord.evidence_refs")
    )
    return FailureRecord(
        failure_id=EventId.parse(data["failure_id"]),
        objective=_require_str(data["objective"], "FailureRecord.objective"),
        failure_fingerprint=_require_str(
            data["failure_fingerprint"], "FailureRecord.failure_fingerprint"
        ),
        evidence_refs=refs,
        occurred_at=_parse_dt(data["occurred_at"], "FailureRecord.occurred_at"),
    )


def _deserialize_state(data: dict[str, object]) -> ProjectState:
    _expect_keys(data, _STATE_KEYS, "ProjectState")
    source_raw = data["source_id"]
    fingerprint_raw = data["source_fingerprint"]
    generations: list[GenerationState] = []
    for entry in _require_list(data["generations"], "ProjectState.generations"):
        gdata = _expect_mapping(entry, "ProjectState.generations entry")
        _expect_keys(gdata, _GENERATION_KEYS, "ProjectState.generations entry")
        baseline = gdata["baseline_hash"]
        if baseline is not None and not isinstance(baseline, str):
            raise SerializationError("generation baseline_hash must be string or null")
        generations.append(
            GenerationState(
                generation_id=GenerationId.parse(gdata["generation_id"]),
                status=GenerationStatus.parse(gdata["status"]),
                baseline_hash=baseline,
            )
        )
    artifacts: list[ArtifactRecord] = []
    for entry in _require_list(data["artifacts"], "ProjectState.artifacts"):
        record = deserialize(entry)
        if not isinstance(record, ArtifactRecord):
            raise SerializationError("ProjectState.artifacts must hold ArtifactRecord")
        artifacts.append(record)
    approvals: list[ApprovalRecord] = []
    for entry in _require_list(data["approvals"], "ProjectState.approvals"):
        record_a = deserialize(entry)
        if not isinstance(record_a, ApprovalRecord):
            raise SerializationError("ProjectState.approvals must hold ApprovalRecord")
        approvals.append(record_a)
    failures: list[FailureRecord] = []
    for entry in _require_list(data["failures"], "ProjectState.failures"):
        record_f = deserialize(entry)
        if not isinstance(record_f, FailureRecord):
            raise SerializationError("ProjectState.failures must hold FailureRecord")
        failures.append(record_f)
    processed: list[ProcessedCommand] = []
    for entry in _require_list(data["processed_commands"], "ProjectState.processed_commands"):
        pdata = _expect_mapping(entry, "ProjectState.processed_commands entry")
        _expect_keys(pdata, _PROCESSED_KEYS, "ProjectState.processed_commands entry")
        processed.append(
            ProcessedCommand(
                command_id=CommandId.parse(pdata["command_id"]),
                request_digest=_require_str(
                    pdata["request_digest"], "ProcessedCommand.request_digest"
                ),
            )
        )
    return ProjectState(
        project_id=ProjectId.parse(data["project_id"]),
        phase=Phase.parse(data["phase"]),
        lifecycle=LifecycleStatus.parse(data["lifecycle"]),
        source_id=SourceId.parse(source_raw) if source_raw is not None else None,
        source_fingerprint=(
            _parse_fingerprint(fingerprint_raw, "ProjectState.source_fingerprint")
            if fingerprint_raw is not None
            else None
        ),
        generations=tuple(generations),
        artifacts=tuple(artifacts),
        approvals=tuple(approvals),
        failures=tuple(failures),
        processed_commands=tuple(processed),
    )
