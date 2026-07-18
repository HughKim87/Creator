# Stage 04 보고서: 첫 편집 수직 흐름 이식

- 작업일: 2026-07-17 (동일 세션 연속: Stage 02→03→매니페스트 재작성→04)
- HEAD/브랜치: `d5f5fb5` / `feature/refactoring` (전체 산출물 미커밋, 커밋 승인 대기)
- 사용자 승인: "매니페스트 재작성하고 Stage 04 진행해" (2026-07-17)
- 담당: 구현·통합 검증 — 본 세션 에이전트. 독립 QA/레드팀 — 미실행(대기).
- 실제 미디어: 미사용(전부 임시 파일·StaticMediaProbe). MP4 생성 없음.

## 선행 게이트: 매니페스트 재작성과 clean-clone 게이트

- `BACKUP_MANIFEST.json`을 schema_version 3으로 재작성: 해시 기준을 Windows
  worktree 바이트에서 **HEAD의 git blob 콘텐츠 sha256**으로 변경(체크아웃 줄바꿈
  독립). 86개 항목·role 보존. `checks/baseline.py`가 `git cat-file blob`으로
  검증하도록 갱신. worktree 드리프트는 기존 `backup_git_unchanged`가 계속 잡는다.
- clean-clone 게이트: fresh clone에서 `workflow check --scope full` **rc=0 완전
  통과** (`evidence/clean_clone_gate_full_check.json`). 원격 CI 실행은 커밋·푸시
  승인 대기로 미실행(핸드오프 결정 대기 항목).

## 이식 범위와 상태 (분리 보고)

| 작업 | 상태 |
|---|---|
| 04-1 구체계 특성 테스트 동결 | 완료 — 레거시 `tests/test_make_premiere_xml.py`(d5f5fb5) 단언을 1:1 이식(9케이스), 기대값 무변경 |
| 04-2 source identity 이식 (`services/source_registration.py`) | 완료 — 이중 해시로 등록 중 변경 감지, 부분 레코드 0, 금지 경로 차단 |
| 04-3 동기화 검사 이식 (`adapters/sync_check.py`) | 완료 — 순수 계산(numpy 제거: 시간·SRT 파싱, RMS 윈도, lag 스코어링) + ffmpeg 추출 어댑터 분리. 구조화 결과(scope/status/metrics/evidence/failure_code), insufficient_data ≠ 성공 |
| 04-4 Premiere XML 이식 (`adapters/premiere_xml.py`) | 완료 — 레거시 알고리즘·XML 구조 보존(특성 테스트 9/9 PASS). MediaProbe 포트 (`adapters/media_probe.py`, 동결) 경유, uuid 주입 가능(동일 입력→byte-identical 테스트 추가) |
| 04-5 산출물 장애 일관 승격 (`services/artifact_service.py`) | 완료 — staging 생산→검증→DB 기록→os.replace→재검증→ready 프로토콜, 경계별 실패 주입 테스트, `workflow artifact reconcile` CLI |
| 수직 스모크 3회 연속 | PASS (등록→동기화 분석→XML 생성→산출물 ready, 한글·공백 경로) |
| 독립 QA·레드팀 | 대기 |
| 구/신 실제 미디어 골든 비교 | 대기 — 실제 영상 파일럿은 Stage 05 범위. 현 골든은 레거시 테스트 기대값 기준 |

## 레거시 대비 의도된 변경 (은폐 없이 기록)

1. ffprobe 부재·실패 시 레거시는 기본값(30fps/1920×1080)으로 조용히 진행 →
   신규 `FfprobeMediaProbe`는 구조화 실패(`MediaProbeError`). fail-closed 원칙.
2. XML 내 uuid를 주입 가능하게 변경(기본은 레거시와 같은 uuid4).
3. sync 계산의 numpy 의존 제거(의존성 추가 없이 순수 파이썬 동일 수식).
4. 소스 등록의 크기+mtime 기반 레거시 동일성 검사 → SHA-256 지문(도메인 계약).
5. 금지 소스 경로 검사에서 OS 임시 루트는 제외(프로젝트 내 temp/출력 경로 대상).

## 통합 검증 결과 (스테이지 말 1회, Linux clean clone, Python 3.12.3)

`evidence/check_full_after_stage04_clean_clone.json` (SHA-256 01d486df…):
**전 항목 rc=0** — doctor 8/8, lock, format, lint, mypy strict(33파일), tests
**159 passed·1 skipped**(신규 24: 특성 9+결정성 1, sync·probe 9, 수직 슬라이스 5),
backup_baseline(재작성 후 86/86 매치), documents, git diff. 실패 0.

## 완료 기준 대비

- 신규 코드의 `backup/` import·실행 참조 0 (doctor `runtime_backup_boundary` PASS)
- `backup/`·원본 입력 변경 0 (`backup_git_unchanged` PASS; 매니페스트는 stage-00
  문서 파일이며 사용자 승인으로 재작성)
- 실패가 성공으로 보고된 사례 0, ready인데 파일 없음/해시 불일치 0(테스트 보장)
- 미격리 orphan·미해결 staging 0(리컨실 테스트), 산출물 계보 조회 가능
- 잔여: 독립 QA·레드팀 승인, 실제 미디어 골든 비교(Stage 05), 원격 CI(커밋 후)

## 다음 단계에서 금지할 행동

- 신규 runtime의 `backup/` import, 실제 미디어의 무승인 생성·외부 전송
- 특성 테스트 기대값을 신규 구현에 맞춰 변경
- reconcile의 자동 삭제 추가(격리까지만; 삭제는 사용자 승인)

## 롤백

- 지점 `d5f5fb5`. Stage 04 산출물: `src/video_workflow/adapters/`,
  `services/{source_registration,artifact_service}.py`, storage artifact 메서드,
  CLI artifact 명령, 신규 테스트 4파일 삭제 + `checks/baseline.py`·
  `BACKUP_MANIFEST.json`은 `git checkout`으로 복원.

## 버전

- 애플리케이션 0.1.0, DB schema 1, 도메인 직렬화 v2, BACKUP_MANIFEST schema 3.
- 의존성 추가 0건(uv.lock 무변경).
