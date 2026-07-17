"""Domain records: events, artifacts, approvals, failures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from video_workflow.domain.enums import (
    HUMAN_ONLY_APPROVALS,
    ActorKind,
    ApprovalDecision,
    ApprovalType,
    ArtifactRole,
    EventKind,
)
from video_workflow.domain.errors import DomainValidationError
from video_workflow.domain.ids import ArtifactId, EventId, GenerationId, ProjectId, SourceId
from video_workflow.domain.values import (
    Actor,
    require_non_empty_str,
    require_sha256_hex,
    require_utc,
)

Payload = tuple[tuple[str, str], ...]


def make_payload(mapping: dict[str, str]) -> Payload:
    """Build a deterministic, immutable event payload (sorted string pairs)."""
    items: list[tuple[str, str]] = []
    for key in sorted(mapping):
        value = mapping[key]
        require_non_empty_str(key, "payload key")
        if not isinstance(value, str):
            raise DomainValidationError("payload values must be str")
        items.append((key, value))
    return tuple(items)


@dataclass(frozen=True, slots=True)
class WorkflowEvent:
    """Append-only domain event. Identity, time, and actor are supplied
    externally so emitting them stays deterministic."""

    event_id: EventId
    project_id: ProjectId
    kind: EventKind
    occurred_at: datetime
    actor: Actor
    payload: Payload

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, EventId):
            raise DomainValidationError("WorkflowEvent.event_id must be EventId")
        if not isinstance(self.project_id, ProjectId):
            raise DomainValidationError("WorkflowEvent.project_id must be ProjectId")
        if not isinstance(self.kind, EventKind):
            raise DomainValidationError("WorkflowEvent.kind must be EventKind")
        require_utc(self.occurred_at, "WorkflowEvent.occurred_at")
        if not isinstance(self.actor, Actor):
            raise DomainValidationError("WorkflowEvent.actor must be Actor")
        if not isinstance(self.payload, tuple):
            raise DomainValidationError("WorkflowEvent.payload must be a payload tuple")


@dataclass(frozen=True, slots=True)
class ApprovalTarget:
    """What an approval covers: a generation baseline and/or a content hash.

    At least one anchor is required so a later target change can invalidate
    the approval instead of silently reusing it.
    """

    generation_id: GenerationId | None
    content_hash: str | None

    def __post_init__(self) -> None:
        if self.generation_id is None and self.content_hash is None:
            raise DomainValidationError("ApprovalTarget requires generation_id or content_hash")
        if self.generation_id is not None and not isinstance(self.generation_id, GenerationId):
            raise DomainValidationError("ApprovalTarget.generation_id must be GenerationId")
        if self.content_hash is not None:
            require_sha256_hex(self.content_hash, "ApprovalTarget.content_hash")


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    """A technical-validation or human decision bound to a specific target."""

    approval_id: EventId
    approval_type: ApprovalType
    decision: ApprovalDecision
    actor: Actor
    target: ApprovalTarget
    decided_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.approval_id, EventId):
            raise DomainValidationError("ApprovalRecord.approval_id must be EventId")
        if not isinstance(self.approval_type, ApprovalType):
            raise DomainValidationError("ApprovalRecord.approval_type must be ApprovalType")
        if not isinstance(self.decision, ApprovalDecision):
            raise DomainValidationError("ApprovalRecord.decision must be ApprovalDecision")
        if not isinstance(self.actor, Actor):
            raise DomainValidationError("ApprovalRecord.actor must be Actor")
        if not isinstance(self.target, ApprovalTarget):
            raise DomainValidationError("ApprovalRecord.target must be ApprovalTarget")
        require_utc(self.decided_at, "ApprovalRecord.decided_at")
        if self.approval_type in HUMAN_ONLY_APPROVALS and self.actor.kind is not ActorKind.HUMAN:
            raise DomainValidationError(
                f"{self.approval_type.value} approval requires a human actor"
            )
        if self.actor.kind is ActorKind.HUMAN and self.actor.provenance is None:
            raise DomainValidationError("human approval requires provenance")


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    """A produced artifact with full lineage.

    File existence alone never registers an artifact; only transitions do.
    """

    artifact_id: ArtifactId
    project_id: ProjectId
    generation_id: GenerationId
    source_id: SourceId
    role: ArtifactRole
    content_hash: str
    parent_ids: tuple[ArtifactId, ...]
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_id, ArtifactId):
            raise DomainValidationError("ArtifactRecord.artifact_id must be ArtifactId")
        if not isinstance(self.project_id, ProjectId):
            raise DomainValidationError("ArtifactRecord.project_id must be ProjectId")
        if not isinstance(self.generation_id, GenerationId):
            raise DomainValidationError("ArtifactRecord.generation_id must be GenerationId")
        if not isinstance(self.source_id, SourceId):
            raise DomainValidationError("ArtifactRecord.source_id must be SourceId")
        if not isinstance(self.role, ArtifactRole):
            raise DomainValidationError("ArtifactRecord.role must be ArtifactRole")
        require_sha256_hex(self.content_hash, "ArtifactRecord.content_hash")
        if not isinstance(self.parent_ids, tuple):
            raise DomainValidationError("ArtifactRecord.parent_ids must be a tuple")
        for parent in self.parent_ids:
            if not isinstance(parent, ArtifactId):
                raise DomainValidationError("ArtifactRecord.parent_ids must hold ArtifactId")
            if parent == self.artifact_id:
                raise DomainValidationError("artifact cannot be its own parent")
        if len(set(self.parent_ids)) != len(self.parent_ids):
            raise DomainValidationError("duplicate parent ids")
        require_utc(self.recorded_at, "ArtifactRecord.recorded_at")


@dataclass(frozen=True, slots=True)
class FailureRecord:
    """Preserved failure evidence. Failures are never deleted or rewritten."""

    failure_id: EventId
    objective: str
    failure_fingerprint: str
    evidence_refs: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.failure_id, EventId):
            raise DomainValidationError("FailureRecord.failure_id must be EventId")
        require_non_empty_str(self.objective, "FailureRecord.objective")
        require_sha256_hex(self.failure_fingerprint, "FailureRecord.failure_fingerprint")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise DomainValidationError("FailureRecord.evidence_refs must be non-empty")
        for ref in self.evidence_refs:
            require_non_empty_str(ref, "FailureRecord.evidence_refs entry")
        require_utc(self.occurred_at, "FailureRecord.occurred_at")
