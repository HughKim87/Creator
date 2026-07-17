"""Property-style tests: seeded random command sequences against invariants.

No external property-testing dependency is used; sequences are generated
with a seeded ``random.Random`` so every run is reproducible. The random
source lives in the test only — the domain itself never sees it.
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from tests.support.domain_factories import agent_actor, fingerprint, human_actor
from video_workflow.domain import (
    TERMINAL_STATUSES,
    AdvancePhase,
    ApprovalDecision,
    ApprovalTarget,
    ApprovalType,
    ArtifactId,
    ArtifactRole,
    Cancel,
    CloseGeneration,
    Command,
    CommandId,
    Complete,
    CreateGeneration,
    EventId,
    GenerationId,
    GenerationStatus,
    LifecycleStatus,
    Phase,
    ProjectId,
    ProjectState,
    RecordApproval,
    RecordArtifact,
    RecordFailure,
    RegisterSource,
    Resume,
    SerializationError,
    SourceId,
    Suspend,
    TransitionAccepted,
    TransitionRejected,
    canonical_json_bytes,
    initial_state,
    serialize,
    transition,
)

SEEDS = (1, 7, 42, 2026, 20260717)
SEQUENCE_LENGTH = 250


class SequenceGenerator:
    """Generates a reproducible stream of commands (valid and hostile)."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.counter = seed * 1_000_000
        self.base_time = datetime(2026, 7, 17, 0, 0, 0, tzinfo=UTC)
        self.source_id = self._source()
        self.fingerprint = fingerprint()
        self.drifted = fingerprint(digest="d" * 64)
        self.known_generations: list[GenerationId] = []
        self.known_artifacts: list[ArtifactId] = []
        self.reused_command: Command | None = None

    def _uuid(self) -> uuid.UUID:
        self.counter += 1
        return uuid.UUID(int=self.counter, version=4)

    def _source(self) -> SourceId:
        return SourceId.from_uuid(self._uuid())

    def _digest(self) -> str:
        return format(self.rng.getrandbits(256), "064x")

    def _base_kwargs(self) -> dict[str, object]:
        occurred = self.base_time + timedelta(seconds=self.counter % 100_000)
        return {
            "command_id": CommandId.from_uuid(self._uuid()),
            "event_id": EventId.from_uuid(self._uuid()),
            "occurred_at": occurred,
            "actor": human_actor(occurred) if self.rng.random() < 0.5 else agent_actor(),
        }

    def next_command(self, state: ProjectState) -> Command:
        choice = self.rng.randrange(14)
        kwargs = self._base_kwargs()
        if choice == 0:
            return RegisterSource(source_id=self.source_id, fingerprint=self.fingerprint, **kwargs)  # type: ignore[arg-type]
        if choice == 1:
            observed = self.fingerprint if self.rng.random() < 0.8 else self.drifted
            return AdvancePhase(observed_fingerprint=observed, **kwargs)  # type: ignore[arg-type]
        if choice == 2:
            target = "waiting_user" if self.rng.random() < 0.5 else "blocked_external"
            return Suspend(target=target, reason="probe", **kwargs)  # type: ignore[arg-type]
        if choice == 3:
            return Resume(**kwargs)  # type: ignore[arg-type]
        if choice == 4:
            return RecordFailure(
                objective="probe-objective",
                failure_fingerprint=self._digest(),
                evidence_refs=("evidence/probe.txt",),
                **kwargs,  # type: ignore[arg-type]
            )
        if choice == 5:
            generation = GenerationId.from_uuid(self._uuid())
            self.known_generations.append(generation)
            return CreateGeneration(generation_id=generation, **kwargs)  # type: ignore[arg-type]
        if choice == 6 and self.known_generations:
            outcome = self.rng.choice(["completed", "aborted"])
            return CloseGeneration(
                generation_id=self.rng.choice(self.known_generations),
                outcome=outcome,
                baseline_hash=self._digest() if outcome == "completed" else None,
                failure_id=None,
                **kwargs,  # type: ignore[arg-type]
            )
        if choice == 7 and self.known_generations:
            artifact = ArtifactId.from_uuid(self._uuid())
            parents: tuple[ArtifactId, ...] = ()
            if self.known_artifacts and self.rng.random() < 0.5:
                parents = (self.rng.choice(self.known_artifacts),)
            self.known_artifacts.append(artifact)
            role = self.rng.choice([ArtifactRole.DRAFT, ArtifactRole.CURRENT_DELIVERABLE])
            return RecordArtifact(
                artifact_id=artifact,
                generation_id=self.rng.choice(self.known_generations),
                role=role,
                content_hash=self._digest(),
                parent_ids=parents,
                **kwargs,  # type: ignore[arg-type]
            )
        if choice == 8:
            approval_type = self.rng.choice(list(ApprovalType))
            generation = (
                self.rng.choice(self.known_generations)
                if self.known_generations and self.rng.random() < 0.7
                else None
            )
            content = self.fingerprint.digest if self.rng.random() < 0.5 else self._digest()
            target_obj = ApprovalTarget(generation_id=generation, content_hash=content)
            return RecordApproval(
                approval_type=approval_type,
                decision=(
                    ApprovalDecision.APPROVED
                    if self.rng.random() < 0.8
                    else ApprovalDecision.REJECTED
                ),
                target=target_obj,
                **kwargs,  # type: ignore[arg-type]
            )
        if choice == 9:
            return Complete(**kwargs)  # type: ignore[arg-type]
        if choice == 10:
            return Cancel(reason="probe-cancel", **kwargs)  # type: ignore[arg-type]
        if choice == 11 and self.reused_command is not None:
            return self.reused_command
        if choice == 12 and self.reused_command is not None:
            # Same command id, different payload.
            return Suspend(
                command_id=self.reused_command.command_id,
                event_id=EventId.from_uuid(self._uuid()),
                occurred_at=self.base_time,
                actor=agent_actor(),
                target="waiting_user",
                reason="id-reuse-probe",
            )
        return AdvancePhase(observed_fingerprint=self.fingerprint, **kwargs)  # type: ignore[arg-type]


def _run_sequence(seed: int) -> tuple[ProjectState, list[bytes]]:
    generator = SequenceGenerator(seed)
    state = initial_state(ProjectId.from_uuid(uuid.UUID(int=seed + 1, version=4)))
    event_bytes: list[bytes] = []
    for _ in range(SEQUENCE_LENGTH):
        command = generator.next_command(state)
        if generator.reused_command is None:
            generator.reused_command = command
        before = state
        result = transition(state, command)
        if isinstance(result, TransitionAccepted):
            state = result.state
            _assert_step_invariants(before, state, command, result)
            for event in result.events:
                event_bytes.append(canonical_json_bytes(event))
        else:
            assert isinstance(result, TransitionRejected)
            assert result.code and result.message
            assert result.command_id == command.command_id
            state = before  # rejected commands must not change anything
    return state, event_bytes


def _assert_step_invariants(
    before: ProjectState,
    after: ProjectState,
    command: Command,
    result: TransitionAccepted,
) -> None:
    # Terminal states accept nothing (checked before dispatch), so a terminal
    # 'before' can never appear here.
    assert before.lifecycle not in TERMINAL_STATUSES
    # Phase only changes via AdvancePhase.
    if not isinstance(command, AdvancePhase):
        assert after.phase is before.phase, "phase must be preserved"
    # Suspension and failure preserve phase (re-checked explicitly).
    if isinstance(command, Suspend | RecordFailure | Resume):
        assert after.phase is before.phase
    # Generations never disappear and closed generations never change.
    assert len(after.generations) >= len(before.generations)
    closed_before = {
        generation.generation_id: generation
        for generation in before.generations
        if generation.status is not GenerationStatus.OPEN
    }
    for generation in after.generations:
        if generation.generation_id in closed_before:
            assert generation == closed_before[generation.generation_id]
    # No generation without enough consumed human approvals.
    approvals = sum(
        1
        for record in after.approvals
        if record.approval_type is ApprovalType.GENERATION
        and record.decision is ApprovalDecision.APPROVED
    )
    assert len(after.generations) <= approvals or not after.generations
    # Every emitted event uses the externally supplied identity and time.
    for event in result.events:
        assert event.event_id == command.event_id
        assert event.occurred_at == command.occurred_at
    # Failure evidence only grows.
    assert len(after.failures) >= len(before.failures)
    # current_deliverable artifacts only for completed generations.
    for artifact in after.artifacts:
        if artifact.role is ArtifactRole.CURRENT_DELIVERABLE:
            generation = after.generation(artifact.generation_id)
            assert generation is not None
            assert generation.status is GenerationStatus.COMPLETED


@pytest.mark.parametrize("seed", SEEDS)
def test_random_sequences_respect_invariants(seed: int) -> None:
    state, _ = _run_sequence(seed)
    assert state.lifecycle in LifecycleStatus
    assert state.phase in Phase


@pytest.mark.parametrize("seed", SEEDS)
def test_sequences_are_deterministic(seed: int) -> None:
    state_a, events_a = _run_sequence(seed)
    state_b, events_b = _run_sequence(seed)
    assert canonical_json_bytes(state_a) == canonical_json_bytes(state_b)
    assert events_a == events_b


def test_no_disallowed_lifecycle_pairs_ever_succeed() -> None:
    """Exhaustive guard: completed/cancelled accept no command at all."""
    generator = SequenceGenerator(99)
    state, _ = _run_sequence(99)
    if state.lifecycle not in TERMINAL_STATUSES:
        pytest.skip("sequence did not end terminal; covered by other seeds")
    command = generator.next_command(state)
    result = transition(state, command)
    assert isinstance(result, TransitionRejected)


def test_event_serialization_stable_shape() -> None:
    _, events = _run_sequence(42)
    assert events, "expected at least one accepted transition"
    for raw in events[:10]:
        assert raw.startswith(b'{"data":')
        assert b'"schema_version":2' in raw


def test_serialize_rejects_foreign_types() -> None:
    with pytest.raises(SerializationError):
        serialize(object())  # type: ignore[arg-type]
