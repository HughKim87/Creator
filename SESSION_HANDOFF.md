# 프로젝트 재구축 핸드오프

- 역할: 채팅 기억 없이 다음 세션이 검증된 체크포인트에서 재개하는 단일 상태 문서.
- 기준: `feature/refactoring` HEAD `d5f5fb5` + 미커밋 Stage 02 신규 파일들.
- 읽기 순서: `AGENTS.md` -> `PROJECT_RULES.md` -> 이 문서 ->
  `docs/rebuild/AGENT_EXECUTION_PLAN.md` -> 승인된 현재 단계 문서.

## 현재 상태

- Stage 00·01: 완료. Stage 02: 완료(의미 승인 포함,
  `docs/rebuild/stage-02/STAGE_REPORT.md`). Stage 03: **구현·통합 검증 완료,
  미커밋** (`docs/rebuild/stage-03/STAGE_REPORT.md`).
- 구현 위치: 도메인 `src/video_workflow/domain/`(순수), 저장
  `src/video_workflow/storage/`(SQLite 단일 정본, append-only 이벤트, 낙관적
  동시성), 서비스 `src/video_workflow/services/`, CLI `workflow state/approval`.
- 통합 검증(2026-07-17, Linux clone, Python 3.12.3): full check에서
  lock/format/lint/type/tests 전부 0 — **135 passed, 1 skipped**(설계된 가드).
  유일 실패 `backup_baseline`은 매니페스트의 clean-clone 줄바꿈 휴대성
  결함(콘텐츠는 blob 동일; 아래 결정 대기).
- 보호 상태: `backup/` 변경 0, 금지 경로 접근 0, 커밋·푸시 0, 실제 사용자 작업
  공간 생성 0.
- 테스트 정책(사용자 지시): 스테이지당 통합 테스트 1회, 재구축 우선.
  `PROJECT_RULES.md`의 `Test Execution Policy` 참조.

## 사용자 결정 기록과 대기

- 승인됨(2026-07-17 "진행해"): Stage 02 의미 승인(현 구현 채택 — 단일 editing,
  승인 무효화 전면, completed 재진입 금지, 실패 증거 무기한) 및 Stage 03 착수.
  상세는 `docs/rebuild/stage-02/STAGE_REPORT.md`의 승인 결과 절.
- 대기 1: **BACKUP_MANIFEST.json 휴대성 결함 처리**(fresh clone에서
  `backup_baseline` 실패; blob OID 기준 재작성 등 정책 결정).
- 대기 2: **Git 커밋 승인**(Stage 02+03 산출물). 현재 `.git/index.lock` 잔존으로
  샌드박스 커밋 불가 — Windows에서 삭제 필요(아래 주의 참조).
- 대기 3: 독립 QA/레드팀 재실행 여부(계획 4절, 미실행=pending).
- 대기 4: clean-clone·원격 CI 통합 게이트(기존 결정 유지).

## 해결된 실패 원장

| objective | attempts | confirmed result/cause | count | next condition |
|---|---:|---|---:|---|
| Windows 실제 훅 | 127×3, 0 | MSYS suffix 보정 + `cygpath`로 해결 | 0 | 회귀 테스트 유지 |
| 중첩 훅 테스트 격리 | 9, 9, 0 | 격리 PATH에 `cygpath` fixture 제공 | 0 | fixture 유지 |
| Stage 01 부정 QA | 누락, 21 PASS | 번호 매트릭스+완전성 가드 | 0 | 검사·테스트 동시 변경 |
| 샌드박스 Python 3.12 | 다운로드 차단 | archive.ubuntu.com orig.tar 소스 빌드(`/tmp/py312`) | 0 | 세션마다 `/tmp` 소멸 가능, 재빌드 절차는 stage-02 COMMAND_RESULTS 참조 |
| pytest 직접 실행 시 stage01 시나리오 실패 | 1 | `UV_PROJECT_ENVIRONMENT` 미전파. `uv run workflow check` 사용으로 회피 | 0 | 단일 진입 명령만 사용 |

## 다음 행동

1. Stage 04 착수 승인 시
   `docs/rebuild/stage-04/AGENT_STAGE_04_VERTICAL_SLICE_MIGRATION.md`를 읽고
   첫 편집 수직 흐름 이식을 시작한다(테스트는 스테이지 말 통합 1회).
   주의: 계획 6절상 첫 수직 이식 전 clean-clone·원격 CI 통합 게이트가 도래하며,
   이는 BACKUP_MANIFEST 결함 처리(결정 대기 1)를 선행 요구한다.
2. Windows 세션이면 실제 환경에서 `workflow check --scope full` 1회를 다음
   스테이지 통합 테스트에 겸해 재확인한다.
3. 커밋 승인이 나면 `.git/index.lock` 제거 후 Stage 02+03 산출물을 커밋한다.

## 주의

- `.git/index.lock` 0바이트 잔존 파일이 남아 있을 수 있다(샌드박스 mount 권한
  문제로 git이 unlink하지 못함). Windows에서 git이 "index.lock exists"로 거부하면
  해당 파일을 수동 삭제하면 된다. 조회성 git 명령은 정상 동작 확인됨.

다음 세션 시작 문구: `PROJECT_RULES.md와 SESSION_HANDOFF.md를 읽고 현재 승인된 단계만 진행해.`
