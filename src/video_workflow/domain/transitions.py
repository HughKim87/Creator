"""Pure transition function.

``transition(state, command)`` returns either ``TransitionAccepted`` (new
state plus the domain events to append) or ``TransitionRejected`` (a
structured refusal). It never touches files, databases, subprocesses,
clocks, or random sources; identical inputs always produce identical
results. Everything outside the allowlist below is rejected (default deny).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace

from video_workflow.domain.commands import (
    AdvancePhase,
    Cancel,
    CloseGeneration,
    Command,
    Complete,
    CreateGeneration,
    RecordApproval,
    RecordArtifact,
    RecordFailure,
    RegisterSource,
    Resume,
    Suspend,
)
from video_workflow.domain.enums import (
    HUMAN_ONLY_APPROVALS,
    TERMINAL_STATUSES,
    ActorKind,
    ApprovalDecision,
    ApprovalType,
    ArtifactRole,
    EventKind,
    GenerationStatus,
    LifecycleStatus,
    Phase,
    next_phase,
)
from video_workflow.domain.ids import CommandId
from video_workflow.domain.records import (
    ApprovalRecord,
    ArtifactRecord,
    FailureRecord,
    WorkflowEvent,
    make_payload,
)
from video_workflow.domain.state import (
    GenerationState,
    ProcessedCommand,
    ProjectState,
)


@dataclass(frozen=True, slots=True)
class TransitionAccepted:
    state: ProjectState
    events: tuple[WorkflowEvent, ...]


@dataclass(frozen=True, slots=True)
class TransitionRejected:
    command_id: CommandId
    code: str
    message: str


TransitionResult = TransitionAccepted | TransitionRejected


def command_digest(command: Command) -> str:
    """Deterministic digest of a command's action and content (not its id)."""
    material = repr(command.content_fields()).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _event(
    state: ProjectState, command: Command, kind: EventKind, payload: dict[str, str]
) -> WorkflowEvent:
    return WorkflowEvent(
        event_id=command.event_id,
        project_id=state.project_id,
        kind=kind,
        occurred_at=command.occurred_at,
        actor=command.actor,
        payload=make_payload(payload),
    )


def _accept(
    state: ProjectState, command: Command, events: tuple[WorkflowEvent, ...]
) -> TransitionAccepted:
    ledger = state.processed_commands + (
        ProcessedCommand(command.command_id, command_digest(command)),
    )
    return TransitionAccepted(replace(state, processed_commands=ledger), events)


def _reject(command: Command, code: str, message: str) -> TransitionRejected:
    return TransitionRejected(command.command_id, code, message)


def _latest_completed_generation(state: ProjectState) -> GenerationState | None:
    for generation in reversed(state.generations):
        if generation.status is GenerationStatus.COMPLETED:
            return generation
    return None


def _open_generation(state: ProjectState) -> GenerationState | None:
    for generation in state.generations:
        if generation.status is GenerationStatus.OPEN:
            return generation
    return None


def _approved(state: ProjectState, approval_type: ApprovalType) -> tuple[ApprovalRecord, ...]:
    return tuple(
        record
        for record in state.approvals
        if record.approval_type is approval_type and record.decision is ApprovalDecision.APPROVED
    )


def _fresh_approval_for_generation(
    state: ProjectState, approval_type: ApprovalType, generation: GenerationState
) -> ApprovalRecord | None:
    """An approval is fresh only while its recorded target still matches."""
    for record in _approved(state, approval_type):
        if record.target.generation_id != generation.generation_id:
            continue
        if (
            record.target.content_hash is not None
            and record.target.content_hash != generation.baseline_hash
        ):
            continue
        return record
    return None


def transition(state: ProjectState, command: Command) -> TransitionResult:
    """Apply one command to one project state (pure, deterministic)."""
    digest = command_digest(command)
    for processed in state.processed_commands:
        if processed.command_id == command.command_id:
            if processed.request_digest == digest:
                return _reject(
                    command,
                    "duplicate_command_id",
                    "command was already applied; replay is idempotently refused",
                )
            return _reject(
                command,
                "command_id_conflict",
                "command id reused with a different action or payload",
            )

    if state.lifecycle in TERMINAL_STATUSES:
        return _reject(
            command,
            "terminal_state",
            f"no transitions allowed from {state.lifecycle.value}",
        )

    if isinstance(command, RegisterSource):
        return _register_source(state, command)
    if isinstance(command, AdvancePhase):
        return _advance_phase(state, command)
    if isinstance(command, Suspend):
        return _suspend(state, command)
    if isinstance(command, Resume):
        return _resume(state, command)
    if isinstance(command, RecordFailure):
        return _record_failure(state, command)
    if isinstance(command, Cancel):
        return _cancel(state, command)
    if isinstance(command, CreateGeneration):
        return _create_generation(state, command)
    if isinstance(command, CloseGeneration):
        return _close_generation(state, command)
    if isinstance(command, RecordArtifact):
        return _record_artifact(state, command)
    if isinstance(command, RecordApproval):
        return _record_approval(state, command)
    if isinstance(command, Complete):
        return _complete(state, command)
    return _reject(command, "unknown_command", f"unsupported command {command.action()}")


def _require_active(state: ProjectState, command: Command) -> TransitionRejected | None:
    if state.lifecycle is not LifecycleStatus.ACTIVE:
        return _reject(
            command,
            "not_active",
            f"lifecycle is {state.lifecycle.value}; command requires active",
        )
    return None


def _register_source(state: ProjectState, command: RegisterSource) -> TransitionResult:
    blocked = _require_active(state, command)
    if blocked is not None:
        return blocked
    if state.phase is not Phase.INTAKE:
        return _reject(command, "wrong_phase", "source registration is intake-only")
    if state.source_id is not None:
        return _reject(
            command,
            "source_already_registered",
            "project already has a source; a source id never accepts a second "
            "fingerprint and a fingerprint never accepts a second source id",
        )
    new_state = replace(state, source_id=command.source_id, source_fingerprint=command.fingerprint)
    event = _event(
        state,
        command,
        EventKind.SOURCE_REGISTERED,
        {
            "source_id": command.source_id.value,
            "fingerprint_digest": command.fingerprint.digest,
        },
    )
    return _accept(new_state, command, (event,))


def _advance_phase(state: ProjectState, command: AdvancePhase) -> TransitionResult:
    blocked = _require_active(state, command)
    if blocked is not None:
        return blocked
    if state.source_fingerprint is None:
        return _reject(command, "source_not_registered", "register a source first")
    if command.observed_fingerprint != state.source_fingerprint:
        return _reject(
            command,
            "fingerprint_drift",
            "observed source fingerprint differs from the registered one; "
            "progress is blocked until the drift is resolved",
        )
    target = next_phase(state.phase)
    if target is None:
        return _reject(command, "wrong_phase", "delivery is the last phase; use Complete")
    if target is Phase.TECHNICAL_VALIDATION:
        if _latest_completed_generation(state) is None:
            return _reject(
                command,
                "generation_required",
                "technical validation requires a completed generation",
            )
    if target is Phase.HUMAN_APPROVAL:
        generation = _latest_completed_generation(state)
        if generation is None:
            return _reject(
                command,
                "generation_required",
                "human approval requires a completed generation",
            )
        if (
            _fresh_approval_for_generation(state, ApprovalType.TECHNICAL_VALIDATION, generation)
            is None
        ):
            return _reject(
                command,
                "approval_missing",
                "entering human_approval requires a fresh technical validation "
                "approval for the latest completed generation",
            )
    if target is Phase.DELIVERY:
        generation = _latest_completed_generation(state)
        if generation is None:
            return _reject(
                command,
                "generation_required",
                "delivery requires a completed generation",
            )
        if _fresh_approval_for_generation(state, ApprovalType.HUMAN_AV, generation) is None:
            return _reject(
                command,
                "approval_missing",
                "entering delivery requires a fresh human A/V approval for the "
                "latest completed generation",
            )
    event = _event(
        state,
        command,
        EventKind.PHASE_ADVANCED,
        {"phase_before": state.phase.value, "phase_after": target.value},
    )
    return _accept(replace(state, phase=target), command, (event,))


def _suspend(state: ProjectState, command: Suspend) -> TransitionResult:
    blocked = _require_active(state, command)
    if blocked is not None:
        return blocked
    target = (
        LifecycleStatus.WAITING_USER
        if command.target == "waiting_user"
        else LifecycleStatus.BLOCKED_EXTERNAL
    )
    event = _event(
        state,
        command,
        EventKind.LIFECYCLE_CHANGED,
        {
            "lifecycle_before": state.lifecycle.value,
            "lifecycle_after": target.value,
            "phase": state.phase.value,
            "reason": command.reason,
        },
    )
    return _accept(replace(state, lifecycle=target), command, (event,))


def _resume(state: ProjectState, command: Resume) -> TransitionResult:
    if state.lifecycle is LifecycleStatus.ACTIVE:
        return _reject(command, "resume_not_allowed", "project is already active")
    event = _event(
        state,
        command,
        EventKind.LIFECYCLE_CHANGED,
        {
            "lifecycle_before": state.lifecycle.value,
            "lifecycle_after": LifecycleStatus.ACTIVE.value,
            "phase": state.phase.value,
        },
    )
    return _accept(replace(state, lifecycle=LifecycleStatus.ACTIVE), command, (event,))


def _record_failure(state: ProjectState, command: RecordFailure) -> TransitionResult:
    blocked = _require_active(state, command)
    if blocked is not None:
        return blocked
    record = FailureRecord(
        failure_id=command.event_id,
        objective=command.objective,
        failure_fingerprint=command.failure_fingerprint,
        evidence_refs=command.evidence_refs,
        occurred_at=command.occurred_at,
    )
    event = _event(
        state,
        command,
        EventKind.FAILURE_RECORDED,
        {
            "lifecycle_before": state.lifecycle.value,
            "lifecycle_after": LifecycleStatus.FAILED.value,
            "phase": state.phase.value,
            "objective": command.objective,
            "failure_fingerprint": command.failure_fingerprint,
        },
    )
    new_state = replace(
        state,
        lifecycle=LifecycleStatus.FAILED,
        failures=state.failures + (record,),
    )
    return _accept(new_state, command, (event,))


def _cancel(state: ProjectState, command: Cancel) -> TransitionResult:
    event = _event(
        state,
        command,
        EventKind.PROJECT_CANCELLED,
        {
            "lifecycle_before": state.lifecycle.value,
            "phase": state.phase.value,
            "reason": command.reason,
        },
    )
    return _accept(replace(state, lifecycle=LifecycleStatus.CANCELLED), command, (event,))


def _create_generation(state: ProjectState, command: CreateGeneration) -> TransitionResult:
    blocked = _require_active(state, command)
    if blocked is not None:
        return blocked
    if state.phase is not Phase.EDITING:
        return _reject(command, "wrong_phase", "generations are created in editing")
    if state.source_fingerprint is None:
        return _reject(command, "source_not_registered", "register a source first")
    if state.generation(command.generation_id) is not None:
        return _reject(command, "generation_exists", "generation id already used")
    if _open_generation(state) is not None:
        return _reject(command, "generation_open", "close the open generation first")
    source_digest = state.source_fingerprint.digest
    matching = tuple(
        record
        for record in _approved(state, ApprovalType.GENERATION)
        if record.target.content_hash == source_digest
    )
    if len(matching) <= len(state.generations):
        return _reject(
            command,
            "approval_missing",
            "each generation requires its own prior human generation approval "
            "bound to the current source fingerprint",
        )
    generation = GenerationState(generation_id=command.generation_id, status=GenerationStatus.OPEN)
    event = _event(
        state,
        command,
        EventKind.GENERATION_CREATED,
        {"generation_id": command.generation_id.value},
    )
    return _accept(
        replace(state, generations=state.generations + (generation,)),
        command,
        (event,),
    )


def _close_generation(state: ProjectState, command: CloseGeneration) -> TransitionResult:
    blocked = _require_active(state, command)
    if blocked is not None:
        return blocked
    generation = state.generation(command.generation_id)
    if generation is None:
        return _reject(command, "generation_not_found", "unknown generation id")
    if generation.status is not GenerationStatus.OPEN:
        return _reject(
            command,
            "generation_already_closed",
            "closed generations are never overwritten",
        )
    if command.outcome == "failed":
        known = {record.failure_id for record in state.failures}
        if command.failure_id not in known:
            return _reject(
                command,
                "failure_evidence_missing",
                "failed generations require an existing failure record",
            )
    outcome = {
        "completed": GenerationStatus.COMPLETED,
        "failed": GenerationStatus.FAILED,
        "aborted": GenerationStatus.ABORTED,
    }[command.outcome]
    updated = GenerationState(
        generation_id=generation.generation_id,
        status=outcome,
        baseline_hash=command.baseline_hash,
    )
    event = _event(
        state,
        command,
        EventKind.GENERATION_CLOSED,
        {
            "generation_id": generation.generation_id.value,
            "outcome": command.outcome,
        },
    )
    return _accept(state.with_generation_replaced(updated), command, (event,))


def _record_artifact(state: ProjectState, command: RecordArtifact) -> TransitionResult:
    blocked = _require_active(state, command)
    if blocked is not None:
        return blocked
    if state.source_id is None or state.source_fingerprint is None:
        return _reject(command, "source_not_registered", "register a source first")
    generation = state.generation(command.generation_id)
    if generation is None:
        return _reject(command, "generation_not_found", "unknown generation id")
    if any(record.artifact_id == command.artifact_id for record in state.artifacts):
        return _reject(command, "artifact_exists", "artifact id already used")
    known_ids = {record.artifact_id for record in state.artifacts}
    for parent in command.parent_ids:
        if parent not in known_ids:
            return _reject(
                command,
                "parent_not_found",
                "artifact lineage must reference existing artifacts only",
            )
    if command.content_hash == state.source_fingerprint.digest:
        return _reject(
            command,
            "artifact_is_input",
            "an input source cannot also be registered as an artifact",
        )
    if command.role is ArtifactRole.CURRENT_DELIVERABLE:
        if state.phase is not Phase.DELIVERY:
            return _reject(
                command,
                "promotion_forbidden",
                "current_deliverable promotion requires the delivery phase",
            )
        if generation.status is not GenerationStatus.COMPLETED:
            return _reject(
                command,
                "promotion_forbidden",
                "artifacts of failed, aborted, or open generations are never "
                "promoted to current deliverable",
            )
        if _fresh_approval_for_generation(state, ApprovalType.HUMAN_AV, generation) is None:
            return _reject(
                command,
                "promotion_forbidden",
                "current_deliverable promotion requires a fresh human A/V "
                "approval for its generation",
            )
    elif generation.status is not GenerationStatus.OPEN:
        return _reject(
            command,
            "generation_not_open",
            "artifacts are recorded while their generation is open",
        )
    record = ArtifactRecord(
        artifact_id=command.artifact_id,
        project_id=state.project_id,
        generation_id=command.generation_id,
        source_id=state.source_id,
        role=command.role,
        content_hash=command.content_hash,
        parent_ids=command.parent_ids,
        recorded_at=command.occurred_at,
    )
    event = _event(
        state,
        command,
        EventKind.ARTIFACT_RECORDED,
        {
            "artifact_id": command.artifact_id.value,
            "generation_id": command.generation_id.value,
            "role": command.role.value,
            "content_hash": command.content_hash,
        },
    )
    return _accept(replace(state, artifacts=state.artifacts + (record,)), command, (event,))


def _record_approval(state: ProjectState, command: RecordApproval) -> TransitionResult:
    if state.lifecycle not in (
        LifecycleStatus.ACTIVE,
        LifecycleStatus.WAITING_USER,
    ):
        return _reject(
            command,
            "not_active",
            f"approvals are recorded while active or waiting_user, not {state.lifecycle.value}",
        )
    if command.approval_type in HUMAN_ONLY_APPROVALS and command.actor.kind is not ActorKind.HUMAN:
        return _reject(
            command,
            "human_actor_required",
            f"{command.approval_type.value} approval requires a human actor "
            "with provenance; agents cannot impersonate one",
        )
    if command.target.generation_id is not None:
        if state.generation(command.target.generation_id) is None:
            return _reject(command, "generation_not_found", "unknown approval target")
    if any(record.approval_id == command.event_id for record in state.approvals):
        return _reject(command, "approval_exists", "approval id already used")
    record = ApprovalRecord(
        approval_id=command.event_id,
        approval_type=command.approval_type,
        decision=command.decision,
        actor=command.actor,
        target=command.target,
        decided_at=command.occurred_at,
    )
    event = _event(
        state,
        command,
        EventKind.APPROVAL_RECORDED,
        {
            "approval_type": command.approval_type.value,
            "decision": command.decision.value,
            "target_generation_id": (
                command.target.generation_id.value
                if command.target.generation_id is not None
                else ""
            ),
            "target_content_hash": command.target.content_hash or "",
        },
    )
    return _accept(replace(state, approvals=state.approvals + (record,)), command, (event,))


def _complete(state: ProjectState, command: Complete) -> TransitionResult:
    blocked = _require_active(state, command)
    if blocked is not None:
        return blocked
    if state.phase is not Phase.DELIVERY:
        return _reject(
            command,
            "completion_requires_delivery",
            "completion requires the delivery phase",
        )
    generation = _latest_completed_generation(state)
    if generation is None:
        return _reject(command, "generation_required", "completion requires a completed generation")
    if _fresh_approval_for_generation(state, ApprovalType.HUMAN_AV, generation) is None:
        return _reject(
            command,
            "approval_missing",
            "completion requires a fresh human A/V approval for the latest completed generation",
        )
    has_deliverable = any(
        record.role is ArtifactRole.CURRENT_DELIVERABLE
        and record.generation_id == generation.generation_id
        for record in state.artifacts
    )
    if not has_deliverable:
        return _reject(
            command,
            "deliverable_missing",
            "completion requires a registered current deliverable",
        )
    event = _event(
        state,
        command,
        EventKind.PROJECT_COMPLETED,
        {"phase": state.phase.value, "generation_id": generation.generation_id.value},
    )
    return _accept(replace(state, lifecycle=LifecycleStatus.COMPLETED), command, (event,))
