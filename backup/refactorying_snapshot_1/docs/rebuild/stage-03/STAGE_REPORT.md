# Stage 03 보고서: SQLite 단일 상태 정본

- 작업일: 2026-07-17 (Stage 02와 같은 세션에서 연속 수행)
- HEAD/브랜치: `d5f5fb5` / `feature/refactoring` (Stage 02+03 산출물 미커밋)
- 사용자 승인: 2026-07-17 "진행해" — Stage 02 의미 승인 + Stage 03 착수.
  테스트 정책: 스테이지 말 통합 1회(`PROJECT_RULES.md` Test Execution Policy).
- 담당: 구현·통합 검증 — 본 세션 에이전트. 독립 QA/레드팀 — 미실행(대기).

## 상태 요약 (분리 보고)

| 구분 | 상태 |
|---|---|
| 03-1 저장소 포트 동결 (`storage/port.py`) | 완료 |
| 03-2 초기 마이그레이션 (`migrations/0001_initial.sql` + 러너·백업·복원) | 완료 |
| 03-3 원자적 상태 변경 (단일 트랜잭션, BEGIN IMMEDIATE, 낙관적 동시성) | 완료 |
| 03-4 생성 상태 보기 (`state export` → status.json/SESSION_HANDOFF.md) | 완료 |
| 03-5 상태 무결성 검사 (`state verify`) | 완료 |
| 최소 CLI 계약 (`workflow state ...`, `workflow approval ...`) | 완료 |
| 스테이지 통합 검증 | 완료 — 아래 결과 |
| 독립 QA·레드팀 | 대기 |
| 실제 사용자 작업 공간 생성 | 미실행 — 테스트는 전부 임시 디렉터리만 사용 |

## 구현 요지

- 프로젝트별 `<workspace>/projects/<project_id>/workflow.sqlite`가 유일한 영속
  정본. `status.json`·`SESSION_HANDOFF.md`는 DB에서 생성되는 읽기 전용 보기이며
  어떤 명령도 이를 입력으로 읽지 않는다(수동 편집은 재생성 시 무시, 테스트 보장).
- 스키마: `schema_meta`, `projects`, `workflow_events`(append-only 트리거,
  `command_id` UNIQUE + request digest), `sources`, `generations`, `artifacts`,
  `approvals`(승인 정본), `approval_requests`, `failures`. FK·CHECK·UNIQUE 제약
  + 서비스 계층 검증 이중화.
- 원자성: 상태 확인→도메인 전이→이벤트 삽입→스냅숏 갱신→부속 레코드를 한
  트랜잭션으로. 주입 오류 시 전부 롤백(테스트 보장). 거부된 전이는 DB 무변경.
- 동시성: `BEGIN IMMEDIATE` + `state_version` 낙관적 제어. 같은 버전을 읽은 두
  writer 중 정확히 하나만 성공, 나머지는 구조화된 충돌(테스트 보장).
- 멱등성: 동일 `command_id` 재적용은 도메인 원장+UNIQUE 제약이 이중 차단.
- fail-closed: DB 없음(자동 생성 금지)·미래 스키마·손상(무 schema_meta,
  integrity_check)·네트워크 공유 경로 전부 즉시 실패. 마이그레이션은 backup API
  사본 생성 후 실패 시 이전 DB 자동 복원.
- 사람 승인 신뢰 경계(동결): interactive local CLI challenge 방식.
  `approval request`가 일회용 challenge 발급, `approval record`는 TTY(사용자
  대화형 세션) + challenge 일치 + 대상 해시 불변 + evidence ID 미사용을 요구.
  `--actor human` 같은 우회 옵션 없음. 비대화형(에이전트) 세션은 거부되어
  `waiting_user` 유지. 기술 검증 승인만 에이전트 actor로 기록 가능하며 그것만으로
  delivery 진입 불가(테스트 보장).

## 통합 검증 결과 (2026-07-17, Linux clone, Python 3.12.3)

`evidence/check_full_after_stage03_clean_clone.json` (SHA-256 96ba9cdb…):
doctor 8/8 PASS, lock 0, format 0, lint 0, mypy strict 0(27파일), tests 0
(**135 passed, 1 skipped** — Stage 03 신규 24개 포함: 상태 전이 4, 원자성 1,
동시성·멱등성 2, 승인 분리·신뢰 경계 4, 생성 보기 2, 스키마 안전 7, CLI 3,
한글·공백 경로는 전 시나리오 공통 적용). 유일 실패 `backup_baseline`은 Stage 02
보고서에 기록된 기존 clean-clone 줄바꿈 결함(사용자 결정 대기)으로 Stage 03과
무관.

## 지시서 대비 미구현·연기 항목

- UNC 예외 승인 경로(`journal_mode=DELETE` 강제)는 기본 거부만 구현. 예외 지원은
  실제 필요 시 사용자 승인과 함께 추가.
- `workflow state retry`는 `resume`과 동일 처리(실패 카운터는 도메인 실패 원장
  기반, 별도 카운터 테이블 없음).
- 생성·산출물 CLI 하위 명령은 §8 최소 계약 외라 서비스 계층 API로만 제공
  (Stage 04 수직 이식 시 CLI 노출 결정).

## 다음 단계에서 금지할 행동

- 생성 보기(status.json 등)를 상태 입력으로 읽는 코드 추가 금지.
- 두 번째 상태 정본(JSON 파일 등) 도입 금지.
- 실제 사용자 작업 DB의 무승인 생성·삭제·덮어쓰기 금지.
- 기술 검증 결과로 사람 승인 레코드 자동 생성 금지.

## 롤백

- 코드: Stage 03 산출물은 전부 신규 파일 + `cli.py`·`pyproject.toml` 수정.
  `git checkout -- src/video_workflow/cli.py pyproject.toml` 후 신규 디렉터리
  (`storage/`, `services/`, `tests/unit/storage`, `tests/integration`) 삭제.
- 데이터: 실제 작업 DB 미생성이므로 데이터 롤백 없음.

## 버전

- 애플리케이션 0.1.0, DB schema_version 1(`0001_initial.sql`), 도메인 직렬화 v2,
  생성 뷰 schema v1. 검증 인터프리터 CPython 3.12.3(Linux clone), Windows 재확인
  대기.
