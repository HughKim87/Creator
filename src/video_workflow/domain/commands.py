"""Transition commands.

Every command carries externally supplied identity and time: ``command_id``
for idempotency, ``event_id`` for the event the transition would emit, and a
UTC ``occurred_at``. The pure transition function never invents UUIDs or
reads a clock, so identical commands always produce identical results.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime

from video_workflow.domain.enums import ApprovalDecision, ApprovalType, ArtifactRole
from video_workflow.domain.errors import DomainValidationError
from video_workflow.domain.ids import (
    ArtifactId,
    CommandId,
    EventId,
    GenerationId,
    SourceId,
)
from video_workflow.domain.records import ApprovalTarget
from video_workflow.domain.values import (
    Actor,
    SourceFingerprint,
    require_non_empty_str,
    require_sha256_hex,
    require_utc,
)


@dataclass(frozen=True, slots=True)
class Command:
    """Base command. Do not instantiate directly."""

    command_id: CommandId
    event_id: EventId
    occurred_at: datetime
    actor: Actor

    def __post_init__(self) -> None:
        if type(self) is Command:
            raise DomainValidationError("Command is abstract; use a concrete command")
        if not isinstance(self.command_id, CommandId):
            raise DomainValidationError("Command.command_id must be CommandId")
        if not isinstance(self.event_id, EventId):
            raise DomainValidationError("Command.event_id must be EventId")
        require_utc(self.occurred_at, "Command.occurred_at")
        if not isinstance(self.actor, Actor):
            raise DomainValidationError("Command.actor must be Actor")

    def action(self) -> str:
        return type(self).__name__

    def content_fields(self) -> tuple[tuple[str, str], ...]:
        """Deterministic (name, repr) pairs of all fields except command_id.

        Used to detect the same command id being reused with a different
        action or payload.
        """
        pairs: list[tuple[str, str]] = [("action", self.action())]
        for spec in fields(self):
            if spec.name == "command_id":
                continue
            pairs.append((spec.name, repr(getattr(self, spec.name))))
        return tuple(sorted(pairs))


@dataclass(frozen=True, slots=True)
class RegisterSource(Command):
    """Bind one source fingerprint to one source id (intake only)."""

    source_id: SourceId
    fingerprint: SourceFingerprint

    def __post_init__(self) -> None:
        Command.__post_init__(self)
        if not isinstance(self.source_id, SourceId):
            raise DomainValidationError("RegisterSource.source_id must be SourceId")
        if not isinstance(self.fingerprint, SourceFingerprint):
            raise DomainValidationError("RegisterSource.fingerprint must be SourceFingerprint")


@dataclass(frozen=True, slots=True)
class AdvancePhase(Command):
    """Move to the immediate next phase.

    ``observed_fingerprint`` is the fingerprint of the source as observed at
    command time; any drift from the registered fingerprint blocks progress.
    """

    observed_fingerprint: SourceFingerprint

    def __post_init__(self) -> None:
        Command.__post_init__(self)
        if not isinstance(self.observed_fingerprint, SourceFingerprint):
            raise DomainValidationError(
                "AdvancePhase.observed_fingerprint must be SourceFingerprint"
            )


@dataclass(frozen=True, slots=True)
class Suspend(Command):
    """Move lifecycle to waiting_user or blocked_external, preserving phase."""

    target: str  # "waiting_user" | "blocked_external"
    reason: str

    def __post_init__(self) -> None:
        Command.__post_init__(self)
        if self.target not in ("waiting_user", "blocked_external"):
            raise DomainValidationError(
                "Suspend.target must be 'waiting_user' or 'blocked_external'"
            )
        require_non_empty_str(self.reason, "Suspend.reason")


@dataclass(frozen=True, slots=True)
class Resume(Command):
    """Return a suspended or failed project to active at its preserved phase."""


@dataclass(frozen=True, slots=True)
class RecordFailure(Command):
    """Enter failed lifecycle with mandatory evidence, preserving phase."""

    objective: str
    failure_fingerprint: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        Command.__post_init__(self)
        require_non_empty_str(self.objective, "RecordFailure.objective")
        require_sha256_hex(self.failure_fingerprint, "RecordFailure.failure_fingerprint")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise DomainValidationError("RecordFailure.evidence_refs must be non-empty")
        for ref in self.evidence_refs:
            require_non_empty_str(ref, "RecordFailure.evidence_refs entry")


@dataclass(frozen=True, slots=True)
class Cancel(Command):
    """Terminal cancellation."""

    reason: str

    def __post_init__(self) -> None:
        Command.__post_init__(self)
        require_non_empty_str(self.reason, "Cancel.reason")


@dataclass(frozen=True, slots=True)
class CreateGeneration(Command):
    """Open a new generation (editing phase, prior generation approval required)."""

    generation_id: GenerationId

    def __post_init__(self) -> None:
        Command.__post_init__(self)
        if not isinstance(self.generation_id, GenerationId):
            raise DomainValidationError("CreateGeneration.generation_id must be GenerationId")


@dataclass(frozen=True, slots=True)
class CloseGeneration(Command):
    """Close a generation as completed, failed, or aborted."""

    generation_id: GenerationId
    outcome: str  # "completed" | "failed" | "aborted"
    baseline_hash: str | None
    failure_id: EventId | None

    def __post_init__(self) -> None:
        Command.__post_init__(self)
        if not isinstance(self.generation_id, GenerationId):
            raise DomainValidationError("CloseGeneration.generation_id must be GenerationId")
        if self.outcome not in ("completed", "failed", "aborted"):
            raise DomainValidationError(
                "CloseGeneration.outcome must be completed, failed, or aborted"
            )
        if self.outcome == "completed":
            if self.baseline_hash is None:
                raise DomainValidationError("completed generation requires baseline_hash")
            require_sha256_hex(self.baseline_hash, "CloseGeneration.baseline_hash")
        if self.outcome == "failed" and self.failure_id is None:
            raise DomainValidationError("failed generation requires failure_id evidence")
        if self.failure_id is not None and not isinstance(self.failure_id, EventId):
            raise DomainValidationError("CloseGeneration.failure_id must be EventId")


@dataclass(frozen=True, slots=True)
class RecordArtifact(Command):
    """Register a produced artifact with lineage."""

    artifact_id: ArtifactId
    generation_id: GenerationId
    role: ArtifactRole
    content_hash: str
    parent_ids: tuple[ArtifactId, ...]

    def __post_init__(self) -> None:
        Command.__post_init__(self)
        if not isinstance(self.artifact_id, ArtifactId):
            raise DomainValidationError("RecordArtifact.artifact_id must be ArtifactId")
        if not isinstance(self.generation_id, GenerationId):
            raise DomainValidationError("RecordArtifact.generation_id must be GenerationId")
        if not isinstance(self.role, ArtifactRole):
            raise DomainValidationError("RecordArtifact.role must be ArtifactRole")
        require_sha256_hex(self.content_hash, "RecordArtifact.content_hash")
        if not isinstance(self.parent_ids, tuple):
            raise DomainValidationError("RecordArtifact.parent_ids must be a tuple")
        for parent in self.parent_ids:
            if not isinstance(parent, ArtifactId):
                raise DomainValidationError("RecordArtifact.parent_ids must hold ArtifactId")


@dataclass(frozen=True, slots=True)
class RecordApproval(Command):
    """Record a decision (technical validation or human approval)."""

    approval_type: ApprovalType
    decision: ApprovalDecision
    target: ApprovalTarget

    def __post_init__(self) -> None:
        Command.__post_init__(self)
        if not isinstance(self.approval_type, ApprovalType):
            raise DomainValidationError("RecordApproval.approval_type must be ApprovalType")
        if not isinstance(self.decision, ApprovalDecision):
            raise DomainValidationError("RecordApproval.decision must be ApprovalDecision")
        if not isinstance(self.target, ApprovalTarget):
            raise DomainValidationError("RecordApproval.target must be ApprovalTarget")


@dataclass(frozen=True, slots=True)
class Complete(Command):
    """Terminal completion; requires delivery phase and required approvals."""
