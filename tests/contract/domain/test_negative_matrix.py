"""Stage 02 mandatory negative matrix.

Mirrors section 9 of AGENT_STAGE_02_DOMAIN_CONTRACTS.md as numbered cases.
A completeness guard fails if any required case number is missing, so new
mandatory checks must be added here together with their implementation.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import pytest

from tests.support.domain_factories import (
    BASELINE_DIGEST,
    FIXED_NOW,
    Driver,
    agent_actor,
    fingerprint,
    human_actor,
)
from video_workflow.domain import (
    Actor,
    ActorKind,
    AdvancePhase,
    ApprovalDecision,
    ApprovalTarget,
    ApprovalType,
    ArtifactRole,
    Cancel,
    CloseGeneration,
    Complete,
    CreateGeneration,
    DomainValidationError,
    LifecycleStatus,
    Phase,
    ProjectId,
    RecordApproval,
    RecordArtifact,
    RecordFailure,
    RegisterSource,
    Resume,
    SerializationError,
    SourceFingerprint,
    Suspend,
    TransitionAccepted,
    TransitionRejected,
    canonical_json_bytes,
    deserialize,
    serialize,
    transition,
)

REQUIRED_CASES = frozenset(range(1, 19))

_REGISTRY: dict[int, Callable[[], None]] = {}


def case(number: int) -> Callable[[Callable[[], None]], Callable[[], None]]:
    def register(func: Callable[[], None]) -> Callable[[], None]:
        assert number not in _REGISTRY, f"duplicate case {number}"
        _REGISTRY[number] = func
        return func

    return register


def _expect_rejection(result: object, code: str) -> TransitionRejected:
    assert isinstance(result, TransitionRejected), f"expected rejection, got {result!r}"
    assert result.code == code, f"expected {code}, got {result.code}: {result.message}"
    return result


@case(1)
def _same_fingerprint_second_source_id() -> None:
    """같은 지문에 다른 source_id: 재등록은 거부된다."""
    driver = Driver()
    driver.register_source()
    other_source = driver.ids.source()
    command = driver.build(RegisterSource, source_id=other_source, fingerprint=driver.fingerprint)
    _expect_rejection(transition(driver.state, command), "source_already_registered")


@case(2)
def _same_source_id_different_fingerprint() -> None:
    """같은 source_id에 다른 지문: 재등록은 거부된다."""
    driver = Driver()
    driver.register_source()
    command = driver.build(
        RegisterSource,
        source_id=driver.source_id,
        fingerprint=fingerprint(digest="f" * 64),
    )
    _expect_rejection(transition(driver.state, command), "source_already_registered")


@case(3)
def _generation_without_approval() -> None:
    """승인 없는 generating 진입."""
    driver = Driver()
    driver.to_editing()
    command = driver.build(CreateGeneration, generation_id=driver.ids.generation())
    _expect_rejection(transition(driver.state, command), "approval_missing")
    # A second generation also needs its own approval: one approval is consumed
    # by one generation.
    driver.open_generation()
    driver.record_draft_artifact()
    driver.complete_generation()
    second = driver.build(CreateGeneration, generation_id=driver.ids.generation())
    _expect_rejection(transition(driver.state, second), "approval_missing")


@case(4)
def _approval_reuse_for_other_generation() -> None:
    """다른 세대에 대한 승인 재사용."""
    driver = Driver()
    driver.to_delivery()
    first_generation = driver.generation_id
    assert first_generation is not None
    # Manufacture a second completed generation without its own HUMAN_AV.
    driver.with_state(phase=Phase.EDITING)
    driver.open_generation()
    driver.record_draft_artifact()
    driver.complete_generation()
    driver.with_state(phase=Phase.HUMAN_APPROVAL)
    # Advance to delivery must now fail: the old approval targets generation 1.
    command = driver.build(AdvancePhase, observed_fingerprint=driver.fingerprint)
    _expect_rejection(transition(driver.state, command), "approval_missing")


@case(5)
def _fingerprint_drift_after_approval() -> None:
    """승인 후 입력 해시 변경: 관측 지문이 다르면 진행 불가."""
    driver = Driver()
    driver.to_editing()
    drifted = fingerprint(digest="d" * 64)
    command = driver.build(AdvancePhase, observed_fingerprint=drifted)
    _expect_rejection(transition(driver.state, command), "fingerprint_drift")


@case(6)
def _completed_generation_overwrite() -> None:
    """완료 세대 덮어쓰기."""
    driver = Driver()
    driver.to_editing()
    generation_id = driver.open_generation()
    driver.record_draft_artifact()
    driver.complete_generation()
    command = driver.build(
        CloseGeneration,
        generation_id=generation_id,
        outcome="completed",
        baseline_hash="e" * 64,
        failure_id=None,
    )
    _expect_rejection(transition(driver.state, command), "generation_already_closed")


@case(7)
def _waiting_user_is_not_completion() -> None:
    """waiting_user를 완료로 변환."""
    driver = Driver()
    driver.to_delivery()
    suspend = driver.build(Suspend, target="waiting_user", reason="user review")
    result = transition(driver.state, suspend)
    assert isinstance(result, TransitionAccepted)
    driver.state = result.state
    complete = driver.build(Complete)
    _expect_rejection(transition(driver.state, complete), "not_active")
    assert driver.state.lifecycle is LifecycleStatus.WAITING_USER


@case(8)
def _failed_entry_requires_evidence() -> None:
    """실패 증거 없이 failed 진입."""
    driver = Driver()
    driver.to_editing()
    with pytest.raises(DomainValidationError):
        driver.build(
            RecordFailure,
            objective="render",
            failure_fingerprint="0" * 64,
            evidence_refs=(),
        )
    generation_id = driver.open_generation()
    command = driver.build(
        CloseGeneration,
        generation_id=generation_id,
        outcome="failed",
        baseline_hash=None,
        failure_id=driver.ids.event(),  # not an existing failure record
    )
    _expect_rejection(transition(driver.state, command), "failure_evidence_missing")


@case(9)
def _missing_parent_artifact() -> None:
    """존재하지 않는 부모 산출물."""
    driver = Driver()
    driver.to_editing()
    generation_id = driver.open_generation()
    command = driver.build(
        RecordArtifact,
        artifact_id=driver.ids.artifact(),
        generation_id=generation_id,
        role=ArtifactRole.DRAFT,
        content_hash="9" * 64,
        parent_ids=(driver.ids.artifact(),),
    )
    _expect_rejection(transition(driver.state, command), "parent_not_found")


@case(10)
def _cyclic_lineage() -> None:
    """순환 산출물 계보: 자기 참조와 전방 참조 모두 불가."""
    driver = Driver()
    driver.to_editing()
    generation_id = driver.open_generation()
    artifact_id = driver.ids.artifact()
    with pytest.raises(DomainValidationError):
        # Self-cycle is rejected at record construction level.
        from video_workflow.domain import ArtifactRecord

        ArtifactRecord(
            artifact_id=artifact_id,
            project_id=driver.project_id,
            generation_id=generation_id,
            source_id=driver.source_id,
            role=ArtifactRole.DRAFT,
            content_hash="9" * 64,
            parent_ids=(artifact_id,),
            recorded_at=FIXED_NOW,
        )
    # Forward references cannot exist: parents must already be recorded.
    command = driver.build(
        RecordArtifact,
        artifact_id=artifact_id,
        generation_id=generation_id,
        role=ArtifactRole.DRAFT,
        content_hash="9" * 64,
        parent_ids=(artifact_id,),
    )
    result = transition(driver.state, command)
    assert isinstance(result, TransitionRejected)


@case(11)
def _invalid_hash_and_id() -> None:
    """잘못된 해시 길이와 잘못된 ID."""
    with pytest.raises(DomainValidationError):
        SourceFingerprint("sha256", "abc", 1)
    with pytest.raises(DomainValidationError):
        SourceFingerprint("sha256", "G" * 64, 1)
    with pytest.raises(DomainValidationError):
        ProjectId.parse("prj-invalid")
    with pytest.raises(DomainValidationError):
        ProjectId.parse("src-" + "0" * 36)


@case(12)
def _implicit_type_conversion_refused() -> None:
    """문자열 숫자 등 암묵적 타입 변환 거부."""
    with pytest.raises(DomainValidationError):
        SourceFingerprint("sha256", "0" * 64, "1024")  # type: ignore[arg-type]
    with pytest.raises(DomainValidationError):
        SourceFingerprint("sha256", "0" * 64, True)  # type: ignore[arg-type]
    with pytest.raises(DomainValidationError):
        ProjectId.parse(12345)


@case(13)
def _duplicate_command_replay() -> None:
    """같은 전이 명령의 중복 전송은 멱등하게 거부된다."""
    driver = Driver()
    command = driver.build(
        RegisterSource, source_id=driver.source_id, fingerprint=driver.fingerprint
    )
    first = transition(driver.state, command)
    assert isinstance(first, TransitionAccepted)
    replay = transition(first.state, command)
    rejection = _expect_rejection(replay, "duplicate_command_id")
    assert "idempotent" in rejection.message


@case(14)
def _same_command_id_different_payload() -> None:
    """동일 요청 ID와 다른 action 또는 payload 조합."""
    driver = Driver()
    command = driver.build(
        RegisterSource, source_id=driver.source_id, fingerprint=driver.fingerprint
    )
    first = transition(driver.state, command)
    assert isinstance(first, TransitionAccepted)
    conflicting = Suspend(
        command_id=command.command_id,  # reused id
        event_id=driver.ids.event(),
        occurred_at=FIXED_NOW,
        actor=agent_actor(),
        target="waiting_user",
        reason="conflict probe",
    )
    _expect_rejection(transition(first.state, conflicting), "command_id_conflict")


@case(15)
def _unknown_schema_version_and_fields() -> None:
    """알 수 없는 스키마 버전과 정책 밖 알 수 없는 필드."""
    driver = Driver()
    driver.to_delivery()
    envelope = serialize(driver.state)
    tampered_version = json.loads(json.dumps(envelope))
    tampered_version["schema_version"] = 99
    with pytest.raises(SerializationError):
        deserialize(tampered_version)
    tampered_fields = json.loads(json.dumps(envelope))
    tampered_fields["data"]["injected"] = "value"
    with pytest.raises(SerializationError):
        deserialize(tampered_fields)


@case(16)
def _agent_cannot_forge_human_approval() -> None:
    """에이전트 actor가 HUMAN 승인 provenance를 위조하는 시도."""
    driver = Driver()
    driver.to_editing()
    generation_id = driver.open_generation()
    driver.record_draft_artifact()
    driver.complete_generation()
    forged = driver.build(
        RecordApproval,
        actor=agent_actor(),  # kind=AGENT regardless of claimed strings
        approval_type=ApprovalType.HUMAN_AV,
        decision=ApprovalDecision.APPROVED,
        target=ApprovalTarget(generation_id=generation_id, content_hash=BASELINE_DIGEST),
    )
    _expect_rejection(transition(driver.state, forged), "human_actor_required")
    # Claiming HUMAN kind without provenance fails structurally.
    with pytest.raises(DomainValidationError):
        Actor(kind=ActorKind.HUMAN, actor_id="fake-human", provenance=None)


@case(17)
def _suspension_preserves_phase() -> None:
    """waiting_user와 failed 진입·재개 중 phase 손실 금지."""
    driver = Driver()
    driver.to_editing()
    phase_before = driver.state.phase
    suspend = driver.build(Suspend, target="waiting_user", reason="question")
    suspended = transition(driver.state, suspend)
    assert isinstance(suspended, TransitionAccepted)
    assert suspended.state.phase is phase_before
    resumed = transition(suspended.state, driver.build(Resume))
    assert isinstance(resumed, TransitionAccepted)
    assert resumed.state.phase is phase_before
    assert resumed.state.lifecycle is LifecycleStatus.ACTIVE
    failure = driver.build(
        RecordFailure,
        objective="render",
        failure_fingerprint="1" * 64,
        evidence_refs=("docs/rebuild/stage-02/evidence/example.txt",),
    )
    failed = transition(resumed.state, failure)
    assert isinstance(failed, TransitionAccepted)
    assert failed.state.phase is phase_before
    assert failed.state.lifecycle is LifecycleStatus.FAILED
    recovered = transition(failed.state, driver.build(Resume))
    assert isinstance(recovered, TransitionAccepted)
    assert recovered.state.phase is phase_before


@case(18)
def _determinism_no_internal_clock_or_uuid() -> None:
    """내부 시계나 UUID 사용으로 같은 입력 결과가 달라지는 시도."""
    first = Driver()
    first.to_delivery()
    second = Driver()
    second.to_delivery()
    assert canonical_json_bytes(first.state) == canonical_json_bytes(second.state)
    # Event identity comes from the command, not from a generator.
    driver = Driver()
    command = driver.build(
        RegisterSource, source_id=driver.source_id, fingerprint=driver.fingerprint
    )
    result_a = transition(driver.state, command)
    result_b = transition(driver.state, command)
    assert isinstance(result_a, TransitionAccepted)
    assert isinstance(result_b, TransitionAccepted)
    assert canonical_json_bytes(result_a.state) == canonical_json_bytes(result_b.state)
    assert [serialize(event) for event in result_a.events] == [
        serialize(event) for event in result_b.events
    ]
    assert result_a.events[0].event_id == command.event_id
    assert result_a.events[0].occurred_at == command.occurred_at


def test_matrix_is_complete() -> None:
    assert set(_REGISTRY) == set(REQUIRED_CASES), (
        f"missing cases: {sorted(REQUIRED_CASES - set(_REGISTRY))}; "
        f"extra: {sorted(set(_REGISTRY) - REQUIRED_CASES)}"
    )


@pytest.mark.parametrize("number", sorted(REQUIRED_CASES))
def test_negative_case(number: int) -> None:
    _REGISTRY[number]()


def test_cancel_is_terminal_and_timezone_matrix_guard() -> None:
    """Extra guards: cancelled projects accept nothing; non-UTC times refused."""
    driver = Driver()
    driver.to_editing()
    cancelled = transition(driver.state, driver.build(Cancel, reason="stop"))
    assert isinstance(cancelled, TransitionAccepted)
    follow_up = driver.build(AdvancePhase, observed_fingerprint=driver.fingerprint)
    _expect_rejection(transition(cancelled.state, follow_up), "terminal_state")
    with pytest.raises(DomainValidationError):
        RegisterSource(
            command_id=driver.ids.command(),
            event_id=driver.ids.event(),
            occurred_at=datetime(2026, 7, 17, 5, 0, tzinfo=timezone(timedelta(hours=9))),
            actor=agent_actor(),
            source_id=driver.ids.source(),
            fingerprint=driver.fingerprint,
        )
    assert human_actor().kind is ActorKind.HUMAN
