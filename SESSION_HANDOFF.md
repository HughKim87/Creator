# 프로젝트 재구축 핸드오프

- 역할: 채팅 기억 없이 다음 세션이 검증된 체크포인트에서 재개하는 단일 상태 문서.
- 기준: `feature/refactoring` HEAD `d5f5fb5` + 미커밋 Stage 02 신규 파일들.
- 읽기 순서: `AGENTS.md` -> `PROJECT_RULES.md` -> 이 문서 ->
  `docs/rebuild/AGENT_EXECUTION_PLAN.md` -> 승인된 현재 단계 문서.

## 현재 상태

- Stage 00·01·02·03·04 구현 완료(전부 2026-07-17, 미커밋). 각
  `docs/rebuild/stage-0X/STAGE_REPORT.md` 참조. Stage 05(실제 영상 파일럿) 미착수.
- 구현 위치: 도메인 `src/video_workflow/domain/`(순수), 저장
  `src/video_workflow/storage/`(SQLite 단일 정본), 서비스
  `src/video_workflow/services/`(state/source_registration/artifact/views),
  어댑터 `src/video_workflow/adapters/`(media_probe/sync_check/premiere_xml),
  CLI `workflow state|approval|artifact`.
- `BACKUP_MANIFEST.json`은 사용자 승인으로 schema v3(git blob 콘텐츠 sha256)
  재작성 → clean-clone에서 full check **완전 rc=0**.
- 최종 통합 검증(Stage 04 말, Linux clean clone, Python 3.12.3): **전 항목 0**
  — tests 159 passed·1 skipped, mypy strict 33파일, baseline 86/86
  (`docs/rebuild/stage-04/evidence/`).
- 보호 상태: `backup/` 변경 0, 금지 경로 접근 0, 커밋·푸시 0, 실제 미디어·실제
  사용자 작업 공간 사용 0.
- 테스트 정책(사용자 지시): 스테이지당 통합 테스트 1회, 재구축 우선.
  `PROJECT_RULES.md`의 `Test Execution Policy` 참조.

## 사용자 결정 기록과 대기

- 승인됨(2026-07-17): ① "진행해" — Stage 02 의미 승인(현 구현 채택)+Stage 03
  착수. ② "매니페스트 재작성하고 Stage 04 진행해" — BACKUP_MANIFEST v3 재작성
  +Stage 04 착수. clean-clone 게이트는 통과 완료.
- 대기 1: **Git 커밋 승인**(Stage 02+03+04 산출물 일괄). `.git/index.lock`
  잔존으로 샌드박스 커밋 불가 — Windows에서 삭제 필요(아래 주의).
- 대기 2: **원격 CI 실행**(커밋·푸시 승인에 종속).
- 대기 3: 독립 QA/레드팀 재실행 여부(계획 4절, Stage 02~04 공통 pending).
- 대기 4: Stage 05 착수 승인 — **실제 영상 파일럿**이므로 실제 미디어 사용·
  Premiere 수동 확인·사람 A/V 승인이 필요(자동으로 대체 불가).

## 해결된 실패 원장

| objective | attempts | confirmed result/cause | count | next condition |
|---|---:|---|---:|---|
| Windows 실제 훅 | 127×3, 0 | MSYS suffix 보정 + `cygpath`로 해결 | 0 | 회귀 테스트 유지 |
| 중첩 훅 테스트 격리 | 9, 9, 0 | 격리 PATH에 `cygpath` fixture 제공 | 0 | fixture 유지 |
| Stage 01 부정 QA | 누락, 21 PASS | 번호 매트릭스+완전성 가드 | 0 | 검사·테스트 동시 변경 |
| 샌드박스 Python 3.12 | 다운로드 차단 | archive.ubuntu.com orig.tar 소스 빌드(`/tmp/py312`) | 0 | 세션마다 `/tmp` 소멸 가능, 재빌드 절차는 stage-02 COMMAND_RESULTS 참조 |
| pytest 직접 실행 시 stage01 시나리오 실패 | 1 | `UV_PROJECT_ENVIRONMENT` 미전파. `uv run workflow check` 사용으로 회피 | 0 | 단일 진입 명령만 사용 |

## 다음 행동

1. 커밋 승인이 나면 `.git/index.lock` 제거 후 Stage 02+03+04 산출물을 커밋하고,
   푸시 승인 시 원격 CI 결과를 기록한다.
2. Stage 05 착수 승인 시
   `docs/rebuild/stage-05/AGENT_STAGE_05_SHADOW_PILOT.md`를 읽는다. 실제 영상
   병행 파일럿이므로 사용자의 실제 미디어 제공·MP4 생성 승인·사람 A/V 승인이
   필수다. 테스트는 스테이지 말 통합 1회.
3. Windows 세션이면 실제 환경에서 `workflow check --scope full` 1회를 다음
   스테이지 통합 테스트에 겸해 재확인한다(특히 os.replace·한글 경로·
   git cat-file 동작).

## 주의

- `.git/index.lock` 0바이트 잔존 파일이 남아 있을 수 있다(샌드박스 mount 권한
  문제로 git이 unlink하지 못함). Windows에서 git이 "index.lock exists"로 거부하면
  해당 파일을 수동 삭제하면 된다. 조회성 git 명령은 정상 동작 확인됨.

다음 세션 시작 문구: `PROJECT_RULES.md와 SESSION_HANDOFF.md를 읽고 현재 승인된 단계만 진행해.`
