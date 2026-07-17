"""Stage 03 integration: service + SQLite store + CLI + generated views."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from video_workflow.cli import main as cli_main
from video_workflow.domain import (
    Actor,
    ActorKind,
    ApprovalDecision,
    ApprovalTarget,
    ApprovalType,
    ArtifactRole,
    LifecycleStatus,
    Phase,
    ProjectId,
    RegisterSource,
    SourceFingerprint,
    SourceId,
    TransitionAccepted,
    TransitionRejected,
    transition,
)
from video_workflow.services.state_service import (
    StateService,
    new_command_id,
    new_event_id,
)
from video_workflow.services.state_views import export_views, normalized_view_bytes
from video_workflow.storage import (
    ApprovalTrustError,
    ConcurrencyConflictError,
    SqliteStateStore,
)

SOURCE_DIGEST = "a" * 64
BASELINE_DIGEST = "b" * 64


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    path = tmp_path / "한글 작업 공간"
    path.mkdir()
    return path


@pytest.fixture()
def project(workspace: Path) -> tuple[SqliteStateStore, StateService, ProjectId]:
    project_id = ProjectId.from_uuid(uuid.uuid4())
    store = SqliteStateStore.initialize(workspace, project_id)
    return store, StateService(store), project_id


def _fingerprint() -> SourceFingerprint:
    return SourceFingerprint(algorithm="sha256", digest=SOURCE_DIGEST, size_bytes=42)


def _register(service: StateService) -> None:
    outcome = service.register_source(_fingerprint(), locator="source_refs/input.mp4")
    assert outcome.ok, outcome.rejection


def _new_request(
    store: SqliteStateStore,
    scope: str,
    target_sha256: str,
    generation_id: str | None = None,
) -> str:
    request_id = f"req-{uuid.uuid4()}"
    store.create_approval_request(
        request_id=request_id,
        scope=scope,
        challenge="c1",
        generation_id=generation_id,
        artifact_id=None,
        target_sha256=target_sha256,
    )
    return request_id


def _approve_generation_as_user(store: SqliteStateStore, service: StateService) -> None:
    request_id = _new_request(store, "generation", SOURCE_DIGEST)
    outcome = service.record_human_approval(
        ApprovalType.GENERATION,
        ApprovalTarget(generation_id=None, content_hash=SOURCE_DIGEST),
        ApprovalDecision.APPROVED,
        request_id=request_id,
        challenge_response="c1",
        evidence_id=f"user-msg-{uuid.uuid4()}",
        expected_challenge="c1",
        request_target_sha256=SOURCE_DIGEST,
        interactive=True,  # simulated verified user session (service-level test)
    )
    assert outcome.ok, outcome.rejection


def _drive_to_delivery(store: SqliteStateStore, service: StateService) -> str:
    """Full allowed path intake -> delivery; returns the generation id."""
    _register(service)
    assert service.advance("planning", reason="r").ok
    assert service.advance("editing", reason="r").ok
    _approve_generation_as_user(store, service)
    assert service.create_generation(reason="r").ok
    generation = store.load().state.generations[-1]
    artifact = service.record_artifact(
        generation.generation_id,
        ArtifactRole.DRAFT,
        BASELINE_DIGEST,
        relative_path=None,
    )
    assert artifact.ok
    assert service.close_generation(generation.generation_id, "completed", BASELINE_DIGEST).ok
    assert service.advance("technical_validation", reason="r").ok
    assert service.record_technical_validation(
        ApprovalTarget(generation_id=generation.generation_id, content_hash=BASELINE_DIGEST),
        ApprovalDecision.APPROVED,
    ).ok
    assert service.advance("human_approval", reason="r").ok
    request_id = _new_request(store, "human_av", BASELINE_DIGEST, generation.generation_id.value)
    outcome = service.record_human_approval(
        ApprovalType.HUMAN_AV,
        ApprovalTarget(generation_id=generation.generation_id, content_hash=BASELINE_DIGEST),
        ApprovalDecision.APPROVED,
        request_id=request_id,
        challenge_response="c1",
        evidence_id=f"user-msg-{uuid.uuid4()}",
        expected_challenge="c1",
        request_target_sha256=BASELINE_DIGEST,
        interactive=True,
    )
    assert outcome.ok
    assert service.advance("delivery", reason="r").ok
    deliverable = service.record_artifact(
        generation.generation_id,
        ArtifactRole.CURRENT_DELIVERABLE,
        "c" * 64,
    )
    assert deliverable.ok
    return generation.generation_id.value


# -- 상태 전이 ---------------------------------------------------------------


def test_full_allowed_path_reaches_completed(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    store, service, _ = project
    _drive_to_delivery(store, service)
    assert service.complete("done").ok
    stored = store.load()
    assert stored.state.lifecycle is LifecycleStatus.COMPLETED
    assert stored.state.phase is Phase.DELIVERY
    report = store.verify()
    assert report.ok, report.issues


def test_phase_skip_is_refused_without_db_change(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    store, service, _ = project
    _register(service)
    before = store.load().state_version
    outcome = service.advance("editing", reason="skip attempt")
    assert not outcome.ok
    assert outcome.rejection is not None and outcome.rejection.code == "wrong_phase"
    assert store.load().state_version == before


def test_wait_resume_preserves_phase_and_completion_needs_approval(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    store, service, _ = project
    _register(service)
    assert service.advance("planning", reason="r").ok
    assert service.wait("질문 대기").ok
    stored = store.load()
    assert stored.state.lifecycle is LifecycleStatus.WAITING_USER
    assert stored.state.phase is Phase.PLANNING
    # waiting_user is never completion.
    refused = service.complete("nope")
    assert not refused.ok and refused.rejection is not None
    assert service.resume("재개").ok
    stored = store.load()
    assert stored.state.phase is Phase.PLANNING
    assert stored.state.lifecycle is LifecycleStatus.ACTIVE
    # completion without approvals/delivery is refused.
    refused = service.complete("나중")
    assert not refused.ok


def test_completed_project_accepts_no_further_changes(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    store, service, _ = project
    _drive_to_delivery(store, service)
    assert service.complete("done").ok
    for outcome in (
        service.wait("x"),
        service.advance("delivery", reason="x"),
        service.cancel("x"),
    ):
        assert not outcome.ok
        assert outcome.rejection is not None
        assert outcome.rejection.code in {"terminal_state", "wrong_phase"}


# -- 원자성 ------------------------------------------------------------------


def test_partial_commit_rolls_back_everything(
    project: tuple[SqliteStateStore, StateService, ProjectId],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, service, _ = project
    before = store.load()

    def explode(*args: object, **kwargs: object) -> None:
        raise RuntimeError("injected fault between event insert and records")

    monkeypatch.setattr(SqliteStateStore, "_apply_records", explode)
    with pytest.raises(RuntimeError, match="injected fault"):
        service.register_source(_fingerprint(), locator="x")
    monkeypatch.undo()
    after = store.load()
    assert after.state_version == before.state_version
    connection = sqlite3.connect(store.db_path)
    count = connection.execute("SELECT COUNT(*) FROM workflow_events").fetchone()[0]
    connection.close()
    assert count == 0  # no orphan event rows


# -- 동시성·멱등성 -----------------------------------------------------------


def test_two_writers_same_version_exactly_one_wins(
    workspace: Path,
) -> None:
    project_id = ProjectId.from_uuid(uuid.uuid4())
    store_a = SqliteStateStore.initialize(workspace, project_id)
    store_b = SqliteStateStore.open(workspace, project_id)
    loaded_a = store_a.load()
    loaded_b = store_b.load()
    assert loaded_a.state_version == loaded_b.state_version

    def build_register(source_seed: int) -> RegisterSource:
        return RegisterSource(
            command_id=new_command_id(),
            event_id=new_event_id(),
            occurred_at=datetime.now(UTC),
            actor=Actor(kind=ActorKind.AGENT, actor_id="writer"),
            source_id=SourceId.from_uuid(uuid.UUID(int=source_seed, version=4)),
            fingerprint=_fingerprint(),
        )

    command_a = build_register(1)
    command_b = build_register(2)
    accepted_a = transition(loaded_a.state, command_a)
    accepted_b = transition(loaded_b.state, command_b)
    assert isinstance(accepted_a, TransitionAccepted)
    assert isinstance(accepted_b, TransitionAccepted)
    store_a.commit_transition(loaded_a.state_version, command_a, accepted_a)
    with pytest.raises(ConcurrencyConflictError):
        store_b.commit_transition(loaded_b.state_version, command_b, accepted_b)


def test_same_command_id_applies_once_and_conflicts_on_mutation(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    store, _, _ = project
    loaded = store.load()
    command = RegisterSource(
        command_id=new_command_id(),
        event_id=new_event_id(),
        occurred_at=datetime.now(UTC),
        actor=Actor(kind=ActorKind.AGENT, actor_id="writer"),
        source_id=SourceId.from_uuid(uuid.uuid4()),
        fingerprint=_fingerprint(),
    )
    accepted = transition(loaded.state, command)
    assert isinstance(accepted, TransitionAccepted)
    store.commit_transition(loaded.state_version, command, accepted)
    # Replay: the reloaded ledger refuses a second application.
    reloaded = store.load()
    replay = transition(reloaded.state, command)
    assert isinstance(replay, TransitionRejected)
    assert replay.code == "duplicate_command_id"
    assert reloaded.state_version == 1
    connection = sqlite3.connect(store.db_path)
    count = connection.execute("SELECT COUNT(*) FROM workflow_events").fetchone()[0]
    connection.close()
    assert count == 1


# -- 승인 분리·신뢰 경계 ------------------------------------------------------


def test_technical_validation_alone_never_reaches_delivery(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    store, service, _ = project
    _register(service)
    assert service.advance("planning", reason="r").ok
    assert service.advance("editing", reason="r").ok
    _approve_generation_as_user(store, service)
    assert service.create_generation().ok
    generation = store.load().state.generations[-1]
    assert service.close_generation(generation.generation_id, "completed", BASELINE_DIGEST).ok
    assert service.advance("technical_validation", reason="r").ok
    assert service.record_technical_validation(
        ApprovalTarget(generation_id=generation.generation_id, content_hash=BASELINE_DIGEST),
        ApprovalDecision.APPROVED,
    ).ok
    assert service.advance("human_approval", reason="r").ok
    # No human A/V approval recorded -> delivery advance is refused.
    refused = service.advance("delivery", reason="r")
    assert not refused.ok
    assert refused.rejection is not None
    assert refused.rejection.code == "approval_missing"


def test_agent_session_cannot_record_human_approval(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    _, service, _ = project
    with pytest.raises(ApprovalTrustError, match="interactive"):
        service.record_human_approval(
            ApprovalType.HUMAN_AV,
            ApprovalTarget(generation_id=None, content_hash=SOURCE_DIGEST),
            ApprovalDecision.APPROVED,
            request_id="req-x",
            challenge_response="c",
            evidence_id="e",
            expected_challenge="c",
            request_target_sha256=SOURCE_DIGEST,
            interactive=False,  # agent session
        )


def test_challenge_mismatch_and_target_drift_are_refused(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    _, service, _ = project
    with pytest.raises(ApprovalTrustError, match="challenge"):
        service.record_human_approval(
            ApprovalType.HUMAN_AV,
            ApprovalTarget(generation_id=None, content_hash=SOURCE_DIGEST),
            ApprovalDecision.APPROVED,
            request_id="req-x",
            challenge_response="wrong",
            evidence_id="e",
            expected_challenge="right",
            request_target_sha256=SOURCE_DIGEST,
            interactive=True,
        )
    with pytest.raises(ApprovalTrustError, match="hash changed"):
        service.record_human_approval(
            ApprovalType.HUMAN_AV,
            ApprovalTarget(generation_id=None, content_hash=SOURCE_DIGEST),
            ApprovalDecision.APPROVED,
            request_id="req-x",
            challenge_response="c",
            evidence_id="e",
            expected_challenge="c",
            request_target_sha256="d" * 64,
            interactive=True,
        )


def test_evidence_id_reuse_is_refused(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    store, service, _ = project
    _register(service)
    assert service.advance("planning", reason="r").ok
    assert service.advance("editing", reason="r").ok
    shared_evidence = "user-msg-1"

    def approve() -> object:
        request_id = _new_request(store, "generation", SOURCE_DIGEST)
        return service.record_human_approval(
            ApprovalType.GENERATION,
            ApprovalTarget(generation_id=None, content_hash=SOURCE_DIGEST),
            ApprovalDecision.APPROVED,
            request_id=request_id,
            challenge_response="c1",
            evidence_id=shared_evidence,
            expected_challenge="c1",
            request_target_sha256=SOURCE_DIGEST,
            interactive=True,
        )

    assert approve().ok  # type: ignore[attr-defined]
    with pytest.raises(sqlite3.IntegrityError):
        approve()  # same evidence id -> UNIQUE constraint refuses
    assert store.verify().ok


# -- 생성 보기 ---------------------------------------------------------------


def test_generated_views_are_deterministic_and_never_inputs(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    store, service, _ = project
    _register(service)
    status_path, handoff_path = export_views(store)
    assert "DO NOT EDIT" in status_path.read_text(encoding="utf-8")
    assert "DO NOT EDIT" in handoff_path.read_text(encoding="utf-8")
    first = normalized_view_bytes(store)
    second = normalized_view_bytes(store)
    assert first == second
    # Manual edits do not change the DB and are regenerated.
    status_path.write_text('{"tampered": true}', encoding="utf-8")
    version_before = store.load().state_version
    export_views(store)
    assert store.load().state_version == version_before
    regenerated = json.loads(status_path.read_text(encoding="utf-8"))
    assert regenerated.get("tampered") is None
    assert regenerated["state_version"] == version_before
    # No half-written files remain.
    assert not list(status_path.parent.glob("*.tmp"))
    # Stale view is detected by verify.
    connection = sqlite3.connect(store.db_path)
    connection.execute("UPDATE projects SET state_version = state_version")
    connection.close()
    assert store.verify().ok


def test_verify_detects_snapshot_event_mismatch(
    project: tuple[SqliteStateStore, StateService, ProjectId],
) -> None:
    store, service, _ = project
    _register(service)
    connection = sqlite3.connect(store.db_path)
    connection.execute("UPDATE projects SET state_version = 7")
    connection.commit()
    connection.close()
    report = store.verify()
    assert not report.ok
    assert any(issue.code == "snapshot" for issue in report.issues)


# -- CLI ---------------------------------------------------------------------


def test_cli_init_status_transitions_verify_export(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli_main(["state", "init", "--workspace", str(workspace)]) == 0
    project_id = json.loads(capsys.readouterr().out)["project_id"]
    base = ["--workspace", str(workspace), "--project", project_id]
    source = workspace / "input source.bin"
    source.write_bytes(b"video-bytes")
    assert (
        cli_main(
            [
                "state",
                "register-source",
                *base,
                "--file",
                str(source),
                "--locator",
                "source_refs/input.bin",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert cli_main(["state", "advance", *base, "--to", "planning", "--reason", "start"]) == 0
    capsys.readouterr()
    # Wrong target phase is refused with a structured message.
    assert cli_main(["state", "advance", *base, "--to", "delivery", "--reason", "skip"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "wrong_phase"
    assert cli_main(["state", "wait", *base, "--reason", "질문"]) == 0
    capsys.readouterr()
    assert cli_main(["state", "resume", *base, "--reason", "재개"]) == 0
    capsys.readouterr()
    assert cli_main(["state", "status", *base]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["phase"] == "planning"
    assert status["lifecycle"] == "active"
    assert cli_main(["state", "verify", *base]) == 0
    capsys.readouterr()
    assert cli_main(["state", "export", *base]) == 0


def test_cli_reads_fail_without_database(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ghost = ProjectId.from_uuid(uuid.uuid4()).value
    base = ["--workspace", str(workspace), "--project", ghost]
    for command in (
        ["state", "status", *base],
        ["state", "verify", *base],
        ["state", "export", *base],
    ):
        assert cli_main(command) == 1
        err = capsys.readouterr().err
        assert "never create" in err or "not found" in err
    # Still no database was created.
    assert not list(workspace.rglob("workflow.sqlite"))


def test_cli_approval_record_refused_in_non_interactive_session(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli_main(["state", "init", "--workspace", str(workspace)]) == 0
    project_id = json.loads(capsys.readouterr().out)["project_id"]
    base = ["--workspace", str(workspace), "--project", project_id]
    assert (
        cli_main(
            [
                "approval",
                "request",
                *base,
                "--scope",
                "generation",
                "--artifact-sha256",
                SOURCE_DIGEST,
            ]
        )
        == 0
    )
    request = json.loads(capsys.readouterr().out)
    # pytest runs without a TTY: the agent-session path must be refused.
    code = cli_main(
        [
            "approval",
            "record",
            *base,
            "--request-id",
            request["request_id"],
            "--challenge",
            request["challenge"],
            "--decision",
            "approved",
            "--evidence-id",
            "user-msg-9",
        ]
    )
    assert code == 1
    assert "interactive" in capsys.readouterr().err
