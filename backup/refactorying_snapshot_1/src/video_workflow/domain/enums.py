"""Domain enums for the two-axis phase/lifecycle model.

Draft semantics from ``docs/rebuild/stage-02/AGENT_STAGE_02_DOMAIN_CONTRACTS.md``
section 6. Names marked USER in ``CONTRACT_MAPPING.md`` remain subject to the
user semantic-approval gate before stage 03.

``Phase`` is where the work is; ``LifecycleStatus`` is whether it can proceed.
Entering ``waiting_user``/``blocked_external``/``failed`` never erases the
current phase.
"""

from __future__ import annotations

import enum
from typing import Self

from video_workflow.domain.errors import DomainValidationError


class _StrictEnum(enum.Enum):
    """Enum with strict external parsing and no implicit string coercion."""

    @classmethod
    def parse(cls, value: object) -> Self:
        if not isinstance(value, str):
            raise DomainValidationError(
                f"{cls.__name__}.parse requires str, got {type(value).__name__}"
            )
        for member in cls:
            if member.value == value:
                return member
        raise DomainValidationError(f"unknown {cls.__name__}: {value!r}")


class Phase(_StrictEnum):
    INTAKE = "intake"
    PLANNING = "planning"
    EDITING = "editing"
    TECHNICAL_VALIDATION = "technical_validation"
    HUMAN_APPROVAL = "human_approval"
    DELIVERY = "delivery"


PHASE_ORDER: tuple[Phase, ...] = (
    Phase.INTAKE,
    Phase.PLANNING,
    Phase.EDITING,
    Phase.TECHNICAL_VALIDATION,
    Phase.HUMAN_APPROVAL,
    Phase.DELIVERY,
)


def next_phase(current: Phase) -> Phase | None:
    """Return the immediate successor phase, or None at the end of the order."""
    index = PHASE_ORDER.index(current)
    if index + 1 >= len(PHASE_ORDER):
        return None
    return PHASE_ORDER[index + 1]


class LifecycleStatus(_StrictEnum):
    ACTIVE = "active"
    WAITING_USER = "waiting_user"
    BLOCKED_EXTERNAL = "blocked_external"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


TERMINAL_STATUSES: frozenset[LifecycleStatus] = frozenset(
    {LifecycleStatus.COMPLETED, LifecycleStatus.CANCELLED}
)

SUSPENDED_STATUSES: frozenset[LifecycleStatus] = frozenset(
    {
        LifecycleStatus.WAITING_USER,
        LifecycleStatus.BLOCKED_EXTERNAL,
        LifecycleStatus.FAILED,
    }
)


class ActorKind(_StrictEnum):
    HUMAN = "human"
    AGENT = "agent"
    AUTOMATION = "automation"


class ApprovalType(_StrictEnum):
    GENERATION = "generation"
    TECHNICAL_VALIDATION = "technical_validation"
    HUMAN_AV = "human_av"
    WAIVER = "waiver"


HUMAN_ONLY_APPROVALS: frozenset[ApprovalType] = frozenset(
    {ApprovalType.GENERATION, ApprovalType.HUMAN_AV, ApprovalType.WAIVER}
)


class ApprovalDecision(_StrictEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ArtifactRole(_StrictEnum):
    DRAFT = "draft"
    CALIBRATION_CANDIDATE = "calibration_candidate"
    APPROVED_BASELINE = "approved_baseline"
    CURRENT_DELIVERABLE = "current_deliverable"
    SUPERSEDED = "superseded"
    FAILURE_EVIDENCE = "failure_evidence"


class GenerationStatus(_StrictEnum):
    OPEN = "open"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class EventKind(_StrictEnum):
    SOURCE_REGISTERED = "source_registered"
    PHASE_ADVANCED = "phase_advanced"
    LIFECYCLE_CHANGED = "lifecycle_changed"
    GENERATION_CREATED = "generation_created"
    GENERATION_CLOSED = "generation_closed"
    ARTIFACT_RECORDED = "artifact_recorded"
    APPROVAL_RECORDED = "approval_recorded"
    FAILURE_RECORDED = "failure_recorded"
    PROJECT_COMPLETED = "project_completed"
    PROJECT_CANCELLED = "project_cancelled"
