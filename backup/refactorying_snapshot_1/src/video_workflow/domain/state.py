"""Immutable project state for the pure transition function.

There is no global "current task" singleton: every project (and every
generation inside it) owns its own state. Persistence is a stage 03 concern;
this module knows nothing about files or databases.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from video_workflow.domain.enums import (
    GenerationStatus,
    LifecycleStatus,
    Phase,
)
from video_workflow.domain.errors import DomainValidationError
from video_workflow.domain.ids import CommandId, GenerationId, ProjectId, SourceId
from video_workflow.domain.records import ApprovalRecord, ArtifactRecord, FailureRecord
from video_workflow.domain.values import SourceFingerprint, require_sha256_hex


@dataclass(frozen=True, slots=True)
class GenerationState:
    """One generation of produced work inside a project."""

    generation_id: GenerationId
    status: GenerationStatus
    baseline_hash: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.generation_id, GenerationId):
            raise DomainValidationError("GenerationState.generation_id must be GenerationId")
        if not isinstance(self.status, GenerationStatus):
            raise DomainValidationError("GenerationState.status must be GenerationStatus")
        if self.baseline_hash is not None:
            require_sha256_hex(self.baseline_hash, "GenerationState.baseline_hash")
        if self.status is GenerationStatus.COMPLETED and self.baseline_hash is None:
            raise DomainValidationError("completed generation requires a baseline hash")


@dataclass(frozen=True, slots=True)
class ProcessedCommand:
    """Idempotency ledger entry: command id plus a digest of its content."""

    command_id: CommandId
    request_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.command_id, CommandId):
            raise DomainValidationError("ProcessedCommand.command_id must be CommandId")
        require_sha256_hex(self.request_digest, "ProcessedCommand.request_digest")


@dataclass(frozen=True, slots=True)
class ProjectState:
    """Full domain state of one project. Immutable; transitions return copies."""

    project_id: ProjectId
    phase: Phase = Phase.INTAKE
    lifecycle: LifecycleStatus = LifecycleStatus.ACTIVE
    source_id: SourceId | None = None
    source_fingerprint: SourceFingerprint | None = None
    generations: tuple[GenerationState, ...] = field(default_factory=tuple)
    artifacts: tuple[ArtifactRecord, ...] = field(default_factory=tuple)
    approvals: tuple[ApprovalRecord, ...] = field(default_factory=tuple)
    failures: tuple[FailureRecord, ...] = field(default_factory=tuple)
    processed_commands: tuple[ProcessedCommand, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, ProjectId):
            raise DomainValidationError("ProjectState.project_id must be ProjectId")
        if not isinstance(self.phase, Phase):
            raise DomainValidationError("ProjectState.phase must be Phase")
        if not isinstance(self.lifecycle, LifecycleStatus):
            raise DomainValidationError("ProjectState.lifecycle must be LifecycleStatus")
        if (self.source_id is None) != (self.source_fingerprint is None):
            raise DomainValidationError("source_id and source_fingerprint must be set together")
        seen_generations = {gen.generation_id for gen in self.generations}
        if len(seen_generations) != len(self.generations):
            raise DomainValidationError("duplicate generation ids in state")
        seen_artifacts = {art.artifact_id for art in self.artifacts}
        if len(seen_artifacts) != len(self.artifacts):
            raise DomainValidationError("duplicate artifact ids in state")

    def generation(self, generation_id: GenerationId) -> GenerationState | None:
        for gen in self.generations:
            if gen.generation_id == generation_id:
                return gen
        return None

    def with_generation_replaced(self, updated: GenerationState) -> ProjectState:
        replaced = tuple(
            updated if gen.generation_id == updated.generation_id else gen
            for gen in self.generations
        )
        return replace(self, generations=replaced)


def initial_state(project_id: ProjectId) -> ProjectState:
    """A new project starts in intake/active with nothing recorded."""
    return ProjectState(project_id=project_id)
