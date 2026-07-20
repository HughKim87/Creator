"""State service: builds commands, runs the pure domain transition, and
commits atomically through the storage port.

This is the only layer that generates UUIDs and reads the clock; the domain
stays pure. A rejected transition changes nothing in the database and is
reported as a structured refusal.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

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
    Cancel,
    CloseGeneration,
    Command,
    CommandId,
    Complete,
    CreateGeneration,
    EventId,
    GenerationId,
    Phase,
    RecordApproval,
    RecordArtifact,
    RecordFailure,
    RegisterSource,
    Resume,
    SourceFingerprint,
    SourceId,
    Suspend,
    TransitionAccepted,
    TransitionRejected,
    next_phase,
    transition,
)
from video_workflow.storage.errors import ApprovalTrustError
from video_workflow.storage.port import (
    ApprovalProvenanceExtras,
    CommitExtras,
    CommitReceipt,
    StateStore,
)

AGENT_ACTOR_ID = "workflow-cli"


class _BaseFields(TypedDict):
    command_id: CommandId
    event_id: EventId
    occurred_at: datetime
    actor: Actor


@dataclass(frozen=True, slots=True)
class ApplyOutcome:
    """Either a committed receipt or a structured rejection."""

    receipt: CommitReceipt | None
    rejection: TransitionRejected | None

    @property
    def ok(self) -> bool:
        return self.receipt is not None


def _now() -> datetime:
    return datetime.now(UTC)


def new_command_id() -> CommandId:
    return CommandId.from_uuid(uuid.uuid4())


def new_event_id() -> EventId:
    return EventId.from_uuid(uuid.uuid4())


def agent_actor() -> Actor:
    return Actor(kind=ActorKind.AGENT, actor_id=AGENT_ACTOR_ID)


def human_actor(session_id: str, channel: str) -> Actor:
    return Actor(
        kind=ActorKind.HUMAN,
        actor_id="user",
        provenance=ActorProvenance(channel=channel, session_id=session_id, decided_at=_now()),
    )


def fingerprint_file(path: Path) -> SourceFingerprint:
    """Hash a file read-only to build its fingerprint."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return SourceFingerprint(algorithm="sha256", digest=digest.hexdigest(), size_bytes=size)


class StateService:
    """Applies commands to one project through the storage port."""

    def __init__(self, store: StateStore) -> None:
        self._store = store

    def _apply(
        self,
        command: Command,
        extras: CommitExtras | None = None,
    ) -> ApplyOutcome:
        stored = self._store.load()
        result = transition(stored.state, command)
        if isinstance(result, TransitionRejected):
            return ApplyOutcome(receipt=None, rejection=result)
        assert isinstance(result, TransitionAccepted)
        receipt = self._store.commit_transition(stored.state_version, command, result, extras)
        return ApplyOutcome(receipt=receipt, rejection=None)

    def _base(self, actor: Actor) -> _BaseFields:
        return {
            "command_id": new_command_id(),
            "event_id": new_event_id(),
            "occurred_at": _now(),
            "actor": actor,
        }

    # -- lifecycle commands -------------------------------------------------

    def register_source(
        self,
        fingerprint: SourceFingerprint,
        locator: str,
        reason: str | None = None,
    ) -> ApplyOutcome:
        command = RegisterSource(
            source_id=SourceId.from_uuid(uuid.uuid4()),
            fingerprint=fingerprint,
            **self._base(agent_actor()),
        )
        return self._apply(command, CommitExtras(reason=reason, source_locator=locator))

    def advance(
        self,
        target: str,
        reason: str | None = None,
        observed: SourceFingerprint | None = None,
    ) -> ApplyOutcome:
        stored = self._store.load()
        if stored.state.source_fingerprint is None:
            # Let the domain produce its structured rejection.
            observed_fingerprint = observed or SourceFingerprint("sha256", "0" * 64, 0)
        else:
            observed_fingerprint = observed or stored.state.source_fingerprint
        expected = next_phase(stored.state.phase)
        if expected is None or Phase.parse(target) is not expected:
            rejection = TransitionRejected(
                command_id=new_command_id(),
                code="wrong_phase",
                message=(
                    f"--to must name the immediate next phase "
                    f"({expected.value if expected else 'none: delivery is last'})"
                ),
            )
            return ApplyOutcome(receipt=None, rejection=rejection)
        command = AdvancePhase(
            observed_fingerprint=observed_fingerprint,
            **self._base(agent_actor()),
        )
        return self._apply(command, CommitExtras(reason=reason))

    def wait(self, reason: str) -> ApplyOutcome:
        command = Suspend(
            target="waiting_user",
            reason=reason,
            **self._base(agent_actor()),
        )
        return self._apply(command, CommitExtras(reason=reason))

    def block(self, external_code: str, reason: str) -> ApplyOutcome:
        command = Suspend(
            target="blocked_external",
            reason=f"[{external_code}] {reason}",
            **self._base(agent_actor()),
        )
        return self._apply(command, CommitExtras(reason=reason))

    def resume(self, reason: str) -> ApplyOutcome:
        command = Resume(**self._base(agent_actor()))
        return self._apply(command, CommitExtras(reason=reason))

    def fail(
        self,
        code: str,
        reason: str,
        evidence_refs: tuple[str, ...],
        tool: str | None = None,
    ) -> ApplyOutcome:
        fingerprint_digest = hashlib.sha256(f"{code}\n{reason}".encode()).hexdigest()
        command = RecordFailure(
            objective=code,
            failure_fingerprint=fingerprint_digest,
            evidence_refs=evidence_refs,
            **self._base(agent_actor()),
        )
        return self._apply(
            command, CommitExtras(reason=reason, failure_message=reason, failure_tool=tool)
        )

    def cancel(self, reason: str) -> ApplyOutcome:
        command = Cancel(reason=reason, **self._base(agent_actor()))
        return self._apply(command, CommitExtras(reason=reason))

    def complete(self, reason: str | None = None) -> ApplyOutcome:
        command = Complete(**self._base(agent_actor()))
        return self._apply(command, CommitExtras(reason=reason))

    # -- generations and artifacts -----------------------------------------

    def create_generation(self, reason: str | None = None) -> ApplyOutcome:
        command = CreateGeneration(
            generation_id=GenerationId.from_uuid(uuid.uuid4()),
            **self._base(agent_actor()),
        )
        return self._apply(command, CommitExtras(reason=reason))

    def close_generation(
        self,
        generation_id: GenerationId,
        outcome: str,
        baseline_hash: str | None,
        failure_id: EventId | None = None,
        reason: str | None = None,
    ) -> ApplyOutcome:
        command = CloseGeneration(
            generation_id=generation_id,
            outcome=outcome,
            baseline_hash=baseline_hash,
            failure_id=failure_id,
            **self._base(agent_actor()),
        )
        return self._apply(command, CommitExtras(reason=reason))

    def record_artifact(
        self,
        generation_id: GenerationId,
        role: ArtifactRole,
        content_hash: str,
        parent_ids: tuple[ArtifactId, ...] = (),
        relative_path: str | None = None,
        size_bytes: int | None = None,
        tool_version: str | None = None,
    ) -> ApplyOutcome:
        command = RecordArtifact(
            artifact_id=ArtifactId.from_uuid(uuid.uuid4()),
            generation_id=generation_id,
            role=role,
            content_hash=content_hash,
            parent_ids=parent_ids,
            **self._base(agent_actor()),
        )
        return self._apply(
            command,
            CommitExtras(
                artifact_relative_path=relative_path,
                artifact_size_bytes=size_bytes,
                artifact_tool_version=tool_version,
            ),
        )

    # -- approvals (trust boundary) -----------------------------------------

    def record_technical_validation(
        self,
        target: ApprovalTarget,
        decision: ApprovalDecision,
        reason: str | None = None,
    ) -> ApplyOutcome:
        """Technical validation may be recorded by the agent actor."""
        command = RecordApproval(
            approval_type=ApprovalType.TECHNICAL_VALIDATION,
            decision=decision,
            target=target,
            **self._base(agent_actor()),
        )
        return self._apply(
            command,
            CommitExtras(
                reason=reason,
                approval=ApprovalProvenanceExtras(
                    provenance_type="agent_technical_check",
                    request_id=None,
                    evidence_id=None,
                ),
            ),
        )

    def record_human_approval(
        self,
        approval_type: ApprovalType,
        target: ApprovalTarget,
        decision: ApprovalDecision,
        *,
        request_id: str,
        challenge_response: str,
        evidence_id: str,
        expected_challenge: str,
        request_target_sha256: str | None,
        interactive: bool,
        provenance_type: str = "interactive_local_cli",
    ) -> ApplyOutcome:
        """Record a human decision behind the frozen trust boundary.

        Frozen provenance for this stage: an interactive local CLI challenge
        executed by the user. Non-interactive callers (agent sessions) are
        refused; without a verifiable adapter the project stays waiting_user.
        """
        if not interactive:
            raise ApprovalTrustError(
                "human approvals require the user's interactive session; "
                "agent sessions cannot record them (leave the project in "
                "waiting_user instead)"
            )
        if challenge_response != expected_challenge:
            raise ApprovalTrustError("challenge mismatch; approval refused")
        if (
            request_target_sha256 is not None
            and target.content_hash is not None
            and request_target_sha256 != target.content_hash
        ):
            raise ApprovalTrustError(
                "approval target hash changed after the request; approval refused"
            )
        command = RecordApproval(
            approval_type=approval_type,
            decision=decision,
            target=target,
            **self._base(human_actor(evidence_id, provenance_type)),
        )
        return self._apply(
            command,
            CommitExtras(
                approval=ApprovalProvenanceExtras(
                    provenance_type=provenance_type,
                    request_id=request_id,
                    evidence_id=evidence_id,
                ),
            ),
        )


def new_challenge() -> str:
    """One-time challenge for an approval request (application layer only)."""
    return secrets.token_hex(8)
