# Stage 02 보고서: 도메인 계약과 상태 전이

- 작업일: 2026-07-17 (오후 세션)
- HEAD/브랜치: `d5f5fb5` / `feature/refactoring` (Stage 02 산출물은 미커밋 신규 파일)
- 사용자 승인 범위: "재구축 작업을 이어서 계속 진행" 지시(2026-07-17)를 Stage 02
  착수 승인으로 기록. 커밋·푸시·의미 확정은 별도 승인 대기.
- 담당: 구현·자가검증 — 본 세션 에이전트(Claude).
  독립 QA/레드팀 — **미실행(대기)**. 계획 4절에 따라 별도 역할 필요.

## 상태 요약 (분리 보고)

| 구분 | 상태 |
|---|---|
| 작업 02-1 계약 대응표 | 완성(이전 세션 초안 보존·검토). 사용자 승인 항목 7건 식별 |
| 작업 02-2 순수 전이 함수 | 구현 완료, 자가검증 통과 |
| 작업 02-3 계약 직렬화 | 구현 완료(schema v2, fail-closed), 자가검증 통과 |
| 작업 02-4 속성 테스트 | 구현 완료(시드 고정, 외부 의존성 없음), 통과 |
| 필수 부정 매트릭스(지시서 9절 18항) | 18/18 구현·통과 + 완전성 가드 |
| 독립 QA·레드팀 재실행 | 대기(미실행 = pending, 실패 아님) |
| 사용자 의미 승인(지시서 10절) | 대기 — Stage 03 차단 게이트 |
| clean-clone·원격 CI 통합 게이트 | 대기(핸드오프의 후속 게이트 결정 유지) |

## 구현 요지

- 이축 모델: `Phase`(작업 위치, 초안 명칭 intake→planning→editing→
  technical_validation→human_approval→delivery)와 `LifecycleStatus`(진행 가능성,
  active/waiting_user/blocked_external/failed/completed/cancelled)를 분리.
  suspend/fail/resume은 phase를 절대 잃지 않음(테스트 보장).
- 전역 단일 활성 상태 없음: 프로젝트·세대 단위 상태만 존재.
- 기본 거부: 허용 목록 밖 전이는 전부 구조화된 거부(`TransitionRejected(code,
  message)`)를 반환. 예외로 성공을 위장할 수 없음.
- 세대 생성 잠금: HUMAN `generation` 승인 1건이 세대 1개만 허용하며 현재 원본
  지문에 바인딩. 승인 없는 생성 경로 0건(부정 테스트 3, 속성 불변조건).
- 승인 신선도: 승인은 대상 세대·기준선 해시에 바인딩되고, 대상이 바뀌면
  재사용 불가(부정 테스트 4). `technical_validation`과 `human_av`는 별도 타입,
  human 전용 승인은 `ActorKind.HUMAN`+provenance 강제(부정 테스트 16).
- 원본 지문: 등록 후 불변, 관측 지문 표류 시 진행 차단(부정 테스트 1·2·5).
- 실패: 증거 없는 failed 진입 불가, 실패 기록 append-only, 실패 세대 산출물의
  current_deliverable 승격 금지(부정 테스트 8, 속성 불변조건).
- 멱등성: 동일 `command_id` 재전송은 멱등 거부, 동일 ID+다른 payload는 충돌
  거부(부정 테스트 13·14).
- 결정성: UUID·시각은 명령이 공급. 동일 입력→byte-identical 결과(부정 테스트 18,
  속성 테스트 5시드 반복).
- 직렬화: schema_version 2, 미지 버전·미지 필드·naive datetime 거부, canonical
  JSON. 로그·payload에 원본 콘텐츠 없음(해시·ID만).
- 순수성: 도메인 패키지에 파일시스템·SQLite·subprocess·clock·random import 0건
  (AST 기반 테스트로 강제). doctor의 `runtime_backup_boundary`도 PASS 유지.

## 실행한 검증과 종료 코드

`COMMAND_RESULTS.md` 참조. 요약: 체크포인트 게이트 doctor 0, full 1
(`backup_baseline` 한정, 줄바꿈 휴대성 결함으로 규명); 구현 후 full 재실행에서
lock/format/lint/type/tests 모두 0 (tests 111 passed, 1 skipped(설계된 조건부
가드)). 실패한 검증 중 미해결로 남긴 것: `backup_baseline`의 clean-clone
휴대성(Stage 00 정책 결정 필요, `RISKS_AND_ROLLBACK.md` 1항).

## backup/ 및 사용자 데이터 보호 증거

- `backup_git_unchanged` PASS(worktree·index 변경 0) — 두 full 실행 모두.
- `tracked_data_boundary`·`runtime_backup_boundary` PASS.
- `inputs`/`outputs` 경로 열람·저장 0건. 프레임워크 인벤토리는 `git ls-files`
  기반 검사만 사용.

## 사용자 의미 승인 결과 (2026-07-17)

사용자 지시 "진행해"(7문항·현 구현 채택 제안에 대한 응답)를 다음 승인으로 기록한다:
단일 `editing` phase + 세대 정책, 현 구현의 승인 무효화 범위(대상 해시·세대 변경 시
전부 무효), completed 재진입 금지(새 작업=새 세대), 실패 증거 무기한 append-only,
상태 구분·scope 명칭은 초안 채택. Stage 03 착수 승인 포함. 보류 항목: Git 커밋
승인(명시 대기), BACKUP_MANIFEST 재작성, 독립 QA 실행 여부.

## 사용자 의미 승인 게이트 질문 (지시서 10절, 원문 보존)

`CONTRACT_MAPPING.md` 11절과 동일. 핵심 7문항:

1. Phase 구조: 구체계 `edit_calibration`/`edit_full` 2단을 phase로 유지할지,
   현 구현처럼 단일 `editing` + 세대 정책으로 둘지. (현 구현: 단일 editing)
2. 보정 체크포인트(`user_direction_checkpoint`)의 위치.
3. `blocked_external`/`waiting_user`/`failed`/실행 단위 `aborted` 구분 의미 확정.
4. 승인 무효화 범위: 대상 해시·세대 변경 시 전부 무효(현 구현) 유지 여부.
5. 완료 후 재개 정책: 현 구현은 completed 재진입 전면 금지(새 세대=새 작업).
6. 실패 세대·증거 보존 기간(현 구현: 무기한 append-only).
7. 검증 scope 5종 명칭(Stage 02 타입에는 미포함, Stage 03 전 확정).

## 다음 단계에서 금지할 행동

- 사용자 의미 승인 전 Stage 03(SQLite 저장) 착수 금지.
- 도메인 모듈에 I/O·시계·UUID 생성 도입 금지(순수성 테스트가 차단).
- `BACKUP_MANIFEST.json`을 사용자 결정 없이 재작성 금지.
- 승인 없는 커밋·태그·푸시 금지.

## 롤백

`RISKS_AND_ROLLBACK.md` 참조 (롤백 지점 `d5f5fb5`, 신규 파일 삭제로 충분).

## 버전 정보

- 애플리케이션: video-workflow 0.1.0 (uv.lock 변경 없음, 의존성 추가 없음)
- DB schema: 없음(Stage 03 전). 도메인 직렬화 schema_version: 2
- 검증 인터프리터: CPython 3.12.3 (Linux 샌드박스 clone), Windows 재확인 대기
