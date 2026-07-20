"""Stage 04 vertical slice: registration -> sync -> XML -> artifact promotion.

Covers the mandatory negative registration cases, promotion failure
injection at each protocol boundary, reconciliation detection, and the
3-run vertical smoke, all in Korean/space temp paths.
"""

from __future__ import annotations

import json
import uuid
from fractions import Fraction
from pathlib import Path

import pytest

from video_workflow.adapters.media_probe import MediaInfo, StaticMediaProbe
from video_workflow.adapters.premiere_xml import (
    Cut,
    SourceInfo,
    build_xml,
    seconds_to_frames,
    xml_bytes,
)
from video_workflow.adapters.sync_check import analyze_clip
from video_workflow.cli import main as cli_main
from video_workflow.domain import ArtifactRole, ProjectId
from video_workflow.services.artifact_service import (
    ArtifactPromotionError,
    ArtifactService,
)
from video_workflow.services.source_registration import (
    SourceRegistrationError,
    register_source_file,
    validate_source_path,
)
from video_workflow.services.state_service import StateService
from video_workflow.storage import SqliteStateStore

MEDIA = MediaInfo(5000.0, 1920, 1080, Fraction(60, 1), 48000, 2)


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    path = tmp_path / "한글 작업 공간"
    path.mkdir()
    return path


@pytest.fixture()
def project(workspace: Path) -> tuple[SqliteStateStore, StateService]:
    store = SqliteStateStore.initialize(workspace, ProjectId.from_uuid(uuid.uuid4()))
    return store, StateService(store)


def _make_source(store: SqliteStateStore, name: str = "원본 소스.mp4") -> Path:
    path = store.project_dir / "source_refs" / name
    path.write_bytes(b"video-bytes-" + name.encode("utf-8"))
    return path


def _register(store: SqliteStateStore, service: StateService) -> Path:
    source = _make_source(store)
    result = register_source_file(
        service,
        StaticMediaProbe(MEDIA),
        source,
        locator=f"source_refs/{source.name}",
    )
    assert result.outcome.ok, result.outcome.rejection
    assert result.media == MEDIA
    return source


# -- 04-2 소스 등록 ----------------------------------------------------------


def test_registration_negative_matrix(
    project: tuple[SqliteStateStore, StateService], tmp_path: Path
) -> None:
    store, service = project
    probe = StaticMediaProbe(MEDIA)
    # 존재하지 않는 파일
    with pytest.raises(SourceRegistrationError, match="does not exist"):
        register_source_file(service, probe, tmp_path / "없는 파일.mp4", locator="x")
    # 0바이트
    empty = tmp_path / "빈 파일.mp4"
    empty.write_bytes(b"")
    with pytest.raises(SourceRegistrationError, match="0 bytes"):
        register_source_file(service, probe, empty, locator="x")
    # 금지 경로 (outputs/temp/backup)
    for segment in ("outputs", "temp", "backup"):
        forbidden_dir = tmp_path / segment
        forbidden_dir.mkdir(exist_ok=True)
        forbidden = forbidden_dir / "클립.mp4"
        forbidden.write_bytes(b"x")
        with pytest.raises(SourceRegistrationError, match="not registrable"):
            validate_source_path(forbidden)
    # 정상 등록 후 재등록(지문·ID 충돌)은 도메인이 거부
    _register(store, service)
    duplicate = register_source_file(
        service,
        probe,
        _make_source(store, "다른 소스.mp4"),
        locator="source_refs/다른 소스.mp4",
    )
    assert not duplicate.outcome.ok
    rejection = duplicate.outcome.rejection
    assert rejection is not None and rejection.code == "source_already_registered"
    # 등록 중 파일 변경 → 실패, 부분 레코드 없음
    changing = tmp_path / "변하는 소스.mp4"
    changing.write_bytes(b"first")

    class MutatingProbe:
        def probe(self, path: Path) -> MediaInfo:
            path.write_bytes(b"second-content")
            return MEDIA

    second_workspace = tmp_path / "ws2"
    second_workspace.mkdir()
    fresh_store = SqliteStateStore.initialize(second_workspace, ProjectId.from_uuid(uuid.uuid4()))
    fresh_service = StateService(fresh_store)
    with pytest.raises(SourceRegistrationError, match="changed while"):
        register_source_file(fresh_service, MutatingProbe(), changing, locator="x")
    assert fresh_store.load().state.source_id is None  # no partial record


# -- 04-5 산출물 승격·복구 ----------------------------------------------------


def _to_editing_with_generation(
    store: SqliteStateStore, service: StateService
) -> tuple[ArtifactService, str]:
    from tests.integration.state.test_state_service import _new_request

    _register(store, service)
    assert service.advance("planning", reason="r").ok
    assert service.advance("editing", reason="r").ok
    stored = store.load()
    assert stored.state.source_fingerprint is not None
    digest = stored.state.source_fingerprint.digest
    from video_workflow.domain import (
        ApprovalDecision,
        ApprovalTarget,
        ApprovalType,
    )

    request_id = _new_request(store, "generation", digest)
    outcome = service.record_human_approval(
        ApprovalType.GENERATION,
        ApprovalTarget(generation_id=None, content_hash=digest),
        ApprovalDecision.APPROVED,
        request_id=request_id,
        challenge_response="c1",
        evidence_id=f"user-msg-{uuid.uuid4()}",
        expected_challenge="c1",
        request_target_sha256=digest,
        interactive=True,
    )
    assert outcome.ok
    assert service.create_generation().ok
    generation = store.load().state.generations[-1]
    return ArtifactService(store, service), generation.generation_id.value


def test_promotion_happy_path_and_vertical_smoke_three_runs(
    workspace: Path,
) -> None:
    """수직 스모크 3회: 등록 → 동기화 분석 → XML 생성 → 산출물 ready."""
    for run in range(3):
        store = SqliteStateStore.initialize(workspace, ProjectId.from_uuid(uuid.uuid4()))
        service = StateService(store)
        artifact_service, generation_id = _to_editing_with_generation(store, service)

        # 동기화 검사 (순수 계산, 구조화 결과)
        sync = analyze_clip(
            [0.5 if 10 <= i <= 30 else 0.001 for i in range(400)],
            [(0.5, 1.5, "대사")],
            f"run{run}",
            0.0,
            "generated/sync.json",
        )
        assert sync.status in ("ok", "insufficient_data")

        # Premiere XML 생성 → 산출물 승격
        source_info = SourceInfo(
            1, Path("원본 소스.mp4"), MEDIA, seconds_to_frames(MEDIA.duration, MEDIA.fps)
        )
        root = build_xml(
            "김실버",
            "러프컷",
            [Cut(1, 0.0, 2.0, "인트로", source="원본 소스.mp4", cut_id="C1", order=1)],
            {"원본 소스.mp4": source_info},
            candidates=False,
            uuid_factory=lambda: "00000000-0000-4000-8000-000000000001",
        )
        payload = xml_bytes(root)

        from video_workflow.domain import GenerationId

        receipt = artifact_service.promote(
            GenerationId.parse(generation_id),
            ArtifactRole.DRAFT,
            "roughcut.xml",
            lambda path, data=payload: path.write_bytes(data),
            tool_version="premiere_xml-port-1",
        )
        assert receipt.lifecycle == "ready"
        final = store.project_dir / receipt.relative_path
        assert final.is_file()
        row = store.artifact_row(receipt.artifact_id)
        assert row is not None and row["artifact_lifecycle"] == "ready"
        # 계보·검증: verify와 reconcile 모두 깨끗함
        assert store.verify().ok
        report = artifact_service.reconcile()
        assert report.clean, report.findings


def test_promotion_failure_injection_each_boundary(
    project: tuple[SqliteStateStore, StateService],
) -> None:
    store, service = project
    artifact_service, generation_id = _to_editing_with_generation(store, service)
    from video_workflow.domain import GenerationId

    generation = GenerationId.parse(generation_id)

    # 생산자가 파일을 만들지 않음
    with pytest.raises(ArtifactPromotionError, match="did not create"):
        artifact_service.promote(generation, ArtifactRole.DRAFT, "none.xml", lambda path: None)
    # 0바이트 산출물
    with pytest.raises(ArtifactPromotionError, match="empty"):
        artifact_service.promote(
            generation, ArtifactRole.DRAFT, "empty.xml", lambda path: path.write_bytes(b"")
        )
    # 생산자 예외 → staging 파일만 남고 DB 레코드 없음 → reconcile이 orphan 아님(스테이징 제외)
    with pytest.raises(RuntimeError, match="producer blew up"):
        artifact_service.promote(
            generation,
            ArtifactRole.DRAFT,
            "boom.xml",
            lambda path: (_ for _ in ()).throw(RuntimeError("producer blew up")),
        )
    # DB 등록 거부(잘못된 세대) → 파일은 스테이징에 남고 실패
    with pytest.raises(ArtifactPromotionError, match="registration refused"):
        artifact_service.promote(
            GenerationId.from_uuid(uuid.uuid4()),
            ArtifactRole.DRAFT,
            "ghost.xml",
            lambda path: path.write_bytes(b"data"),
        )
    # 성공 사례는 여전히 동작
    receipt = artifact_service.promote(
        generation, ArtifactRole.DRAFT, "ok.xml", lambda path: path.write_bytes(b"<xml/>")
    )
    assert receipt.lifecycle == "ready"


def test_reconcile_detects_each_mismatch_class(
    project: tuple[SqliteStateStore, StateService],
) -> None:
    store, service = project
    artifact_service, generation_id = _to_editing_with_generation(store, service)
    from video_workflow.domain import GenerationId

    generation = GenerationId.parse(generation_id)
    receipt = artifact_service.promote(
        generation, ArtifactRole.DRAFT, "a.xml", lambda path: path.write_bytes(b"<a/>")
    )
    # 해시 불일치: ready 파일 변조 → quarantined + 구조화 발견 (파일은 보존)
    final = store.project_dir / receipt.relative_path
    final.write_bytes(b"<tampered/>")
    report = artifact_service.reconcile()
    codes = {finding.code for finding in report.findings}
    assert "hash_mismatch" in codes
    assert final.read_bytes() == b"<tampered/>"  # nothing deleted
    row = store.artifact_row(receipt.artifact_id)
    assert row is not None and row["artifact_lifecycle"] == "quarantined"

    # 파일만 있고 DB 레코드 없음 → orphan_file
    orphan = store.project_dir / "artifacts" / generation_id / "orphan.bin"
    orphan.write_bytes(b"stray")
    report = artifact_service.reconcile()
    assert any(f.code == "orphan_file" for f in report.findings)
    assert orphan.is_file()  # not deleted

    # staging 레코드만 있고 파일 없음: staging 승격 후 파일 제거 시나리오
    receipt2 = artifact_service.promote(
        generation, ArtifactRole.DRAFT, "b.xml", lambda path: path.write_bytes(b"<b/>")
    )
    store.set_artifact_lifecycle(receipt2.artifact_id, "staging", expected_current="ready")
    (store.project_dir / receipt2.relative_path).unlink()
    report = artifact_service.reconcile()
    assert any(f.code == "staging_without_file" for f in report.findings)

    # 자동 복구는 파일·해시가 확정된 staging→ready만
    receipt3 = artifact_service.promote(
        generation, ArtifactRole.DRAFT, "c.xml", lambda path: path.write_bytes(b"<c/>")
    )
    store.set_artifact_lifecycle(receipt3.artifact_id, "staging", expected_current="ready")
    report = artifact_service.reconcile()
    assert receipt3.artifact_id in report.auto_fixed
    row3 = store.artifact_row(receipt3.artifact_id)
    assert row3 is not None and row3["artifact_lifecycle"] == "ready"


def test_cli_artifact_reconcile(
    project: tuple[SqliteStateStore, StateService],
    capsys: pytest.CaptureFixture[str],
) -> None:
    store, service = project
    artifact_service, generation_id = _to_editing_with_generation(store, service)
    from video_workflow.domain import GenerationId

    artifact_service.promote(
        GenerationId.parse(generation_id),
        ArtifactRole.DRAFT,
        "cli.xml",
        lambda path: path.write_bytes(b"<cli/>"),
    )
    base = [
        "--workspace",
        str(store.project_dir.parent.parent),
        "--project",
        store.project_id.value,
    ]
    assert cli_main(["artifact", "reconcile", *base]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["clean"] is True
    # 변조 후에는 비정상 종료 + 구조화 발견
    final = next((store.project_dir / "artifacts").rglob("cli.xml"))
    final.write_bytes(b"<evil/>")
    assert cli_main(["artifact", "reconcile", *base]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert any(f["code"] == "hash_mismatch" for f in payload["findings"])
