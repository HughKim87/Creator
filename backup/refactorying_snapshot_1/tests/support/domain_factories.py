"""Deterministic factories shared by domain unit, contract, and property tests.

All identity and time values are generated deterministically so tests never
depend on a real clock or entropy source.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime

from video_workflow.domain import (
    Actor,
    ActorKind,
    ActorProvenance,
    AdvancePhase,
    ApprovalDecision,
    ApprovalTarget,
    ApprovalType,
    ArtifactId,
    ArtifactRole,
    CloseGeneration,
    Command,
    CommandId,
    CreateGeneration,
    EventId,
    GenerationId,
    Phase,
    ProjectId,
    ProjectState,
    RecordApproval,
    RecordArtifact,
    RegisterSource,
    SourceFingerprint,
    SourceId,
    TransitionAccepted,
    initial_state,
    transition,
)

FIXED_NOW = datetime(2026, 7, 17, 5, 0, 0, tzinfo=UTC)

SOURCE_DIGEST = "a" * 64
BASELINE_DIGEST = "b" * 64
DELIVERABLE_DIGEST = "c" * 64


class IdFactory:
    """Sequential, deterministic UUID4-based ids."""

    def __init__(self, start: int = 1) -> None:
        self._counter = start

    def _next_uuid(self) -> uuid.UUID:
        value = uuid.UUID(int=self._counter, version=4)
        self._counter += 1
        return value

    def project(self) -> ProjectId:
        return ProjectId.from_uuid(self._next_uuid())

    def source(self) -> SourceId:
        return SourceId.from_uuid(self._next_uuid())

    def generation(self) -> GenerationId:
        return GenerationId.from_uuid(self._next_uuid())

    def artifact(self) -> ArtifactId:
        return ArtifactId.from_uuid(self._next_uuid())

    def event(self) -> EventId:
        return EventId.from_uuid(self._next_uuid())

    def command(self) -> CommandId:
        return CommandId.from_uuid(self._next_uuid())


def human_actor(now: datetime = FIXED_NOW) -> Actor:
    return Actor(
        kind=ActorKind.HUMAN,
        actor_id="user-hugh",
        provenance=ActorProvenance(channel="chat", session_id="session-1", decided_at=now),
    )


def agent_actor() -> Actor:
    return Actor(kind=ActorKind.AGENT, actor_id="agent-implementer")


def fingerprint(digest: str = SOURCE_DIGEST, size_bytes: int = 1024) -> SourceFingerprint:
    return SourceFingerprint(algorithm="sha256", digest=digest, size_bytes=size_bytes)


class Driver:
    """Builds a project state up to well-known milestones via real transitions."""

    def __init__(self, start: int = 1) -> None:
        self.ids = IdFactory(start)
        self.project_id = self.ids.project()
        self.source_id = self.ids.source()
        self.fingerprint = fingerprint()
        self.state: ProjectState = initial_state(self.project_id)
        self.generation_id: GenerationId | None = None
        self.artifact_id: ArtifactId | None = None

    def _apply(self, command: Command) -> None:
        result = transition(self.state, command)
        assert isinstance(result, TransitionAccepted), f"driver step rejected: {result!r}"
        self.state = result.state

    def build(self, command_type: type[Command], **kwargs: object) -> Command:
        actor = kwargs.pop("actor", agent_actor())
        return command_type(
            command_id=self.ids.command(),
            event_id=self.ids.event(),
            occurred_at=FIXED_NOW,
            actor=actor,  # type: ignore[arg-type]
            **kwargs,  # type: ignore[arg-type]
        )

    def register_source(self) -> None:
        self._apply(
            self.build(RegisterSource, source_id=self.source_id, fingerprint=self.fingerprint)
        )

    def advance(self) -> None:
        self._apply(self.build(AdvancePhase, observed_fingerprint=self.fingerprint))

    def to_editing(self) -> None:
        self.register_source()
        self.advance()  # intake -> planning
        self.advance()  # planning -> editing
        assert self.state.phase is Phase.EDITING

    def approve_generation(self) -> None:
        self._apply(
            self.build(
                RecordApproval,
                actor=human_actor(),
                approval_type=ApprovalType.GENERATION,
                decision=ApprovalDecision.APPROVED,
                target=ApprovalTarget(generation_id=None, content_hash=self.fingerprint.digest),
            )
        )

    def open_generation(self) -> GenerationId:
        self.approve_generation()
        generation_id = self.ids.generation()
        self._apply(self.build(CreateGeneration, generation_id=generation_id))
        self.generation_id = generation_id
        return generation_id

    def record_draft_artifact(self) -> ArtifactId:
        assert self.generation_id is not None
        artifact_id = self.ids.artifact()
        self._apply(
            self.build(
                RecordArtifact,
                artifact_id=artifact_id,
                generation_id=self.generation_id,
                role=ArtifactRole.DRAFT,
                content_hash=BASELINE_DIGEST,
                parent_ids=(),
            )
        )
        self.artifact_id = artifact_id
        return artifact_id

    def complete_generation(self) -> None:
        assert self.generation_id is not None
        self._apply(
            self.build(
                CloseGeneration,
                generation_id=self.generation_id,
                outcome="completed",
                baseline_hash=BASELINE_DIGEST,
                failure_id=None,
            )
        )

    def approve_technical(self) -> None:
        assert self.generation_id is not None
        self._apply(
            self.build(
                RecordApproval,
                approval_type=ApprovalType.TECHNICAL_VALIDATION,
                decision=ApprovalDecision.APPROVED,
                target=ApprovalTarget(
                    generation_id=self.generation_id, content_hash=BASELINE_DIGEST
                ),
            )
        )

    def approve_human_av(self) -> None:
        assert self.generation_id is not None
        self._apply(
            self.build(
                RecordApproval,
                actor=human_actor(),
                approval_type=ApprovalType.HUMAN_AV,
                decision=ApprovalDecision.APPROVED,
                target=ApprovalTarget(
                    generation_id=self.generation_id, content_hash=BASELINE_DIGEST
                ),
            )
        )

    def to_delivery(self) -> None:
        """intake -> ... -> delivery with one completed, fully approved generation."""
        self.to_editing()
        self.open_generation()
        self.record_draft_artifact()
        self.complete_generation()
        self.advance()  # editing -> technical_validation
        self.approve_technical()
        self.advance()  # technical_validation -> human_approval
        self.approve_human_av()
        self.advance()  # human_approval -> delivery
        assert self.state.phase is Phase.DELIVERY

    def with_state(self, **changes: object) -> None:
        self.state = replace(self.state, **changes)  # type: ignore[arg-type]
