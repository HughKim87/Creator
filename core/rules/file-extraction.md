# File Knowledge Extraction

- Purpose: preserve reusable rules, failure knowledge, current state, lineage, and evidence from files in their canonical owners without authorizing cleanup.
- Read when: extracting reusable information from files without deleting them, or examining file knowledge before cleanup, deletion, move, or rename.
- Authority: `PROJECT_RULES.md` is higher authority and selects any additional document, failure, protected-data, domain, or boundary owner.

## FEX01 — 추출 범위와 owner 판정

- 조건: 파일 또는 목적상 직접 연결된 자료에서 이후 작업에 재사용할 내용을 추출하려 한다.
- 행동:
  1. exact 대상, 접근 목적, 허용 읽기·쓰기 범위, 추출 결과의 독자를 먼저 고정한다.
  2. 지정된 파일과 목적상 직접 필요한 연결 자료만 읽는다. 보호 경로는 exact 대상의 부분집합만 접근하고 sibling을 넓게 열거하지 않는다.
  3. 내용을 `active rule`, `candidate`, `verified failure`, `current state`, `source lineage`, `task fact`, `historical detail`, `disposable derivative`로 분류한다.
  4. 재사용 가능한 판단은 특정 작업명·파일명·일회성 수치를 제거하고 `조건 / 행동 / 예외 / 검증`으로 압축해 상위 route가 선택한 가장 좁은 기존 owner에 반영한다.
  5. 기존 owner가 서로 다른 trigger와 책임을 섞게 만들 때만 새 owner를 검토한다. 생성 전에 foundation/domain 계층과 정확한 router를 확정한다.
  6. 단일 작업의 수치·프레임·파일명·해시·절대 경로·개별 선호는 active rule로 승격하지 않고 현재 task evidence 또는 기존 candidate owner에 둔다.
  7. 추출만 요청된 경우 삭제·이동·이름 변경을 예약하거나 실행하지 않는다.
- 예외:
  - 사용자 승인·현재 상태·source lineage를 입증하는 유일한 자료는 중복이나 완료 상세로 분류하지 않는다.
  - 원인·해결·검증이 끝난 범용 실패만 상위 route가 선택한 failure owner로 승격을 검토한다.
  - candidate owner가 없거나 승격 근거가 부족하면 새 문서를 자동 생성하지 않고 추출 결과를 보고한다.
- 검증:
  - 추출 항목마다 evidence label, canonical owner, 승격·보류·미추출 이유를 지정한다.
  - 새 active rule은 `Purpose / Read when / Authority`와 `조건 / 행동 / 예외 / 검증`을 가진다.
  - 정확한 rule route가 존재하고 기존 rule·candidate·failure owner와 중복되지 않는다.
  - 보호 자료의 내용, 비밀, 사용자 원본, task-specific 사실을 규칙·보고서·캐시에 복제하지 않는다.

## 추출 결과의 owner

| 추출 내용 | 보존 owner |
|---|---|
| 반복되고 일반화된 조건부 행동 | 상위 route가 선택한 가장 좁은 기존 active rule owner |
| 단일 작업에서만 확인된 판단 | 현재 task evidence 또는 기존 candidate owner |
| 범용 원인·해결·검증이 끝난 실패 | 상위 route가 선택한 failure owner |
| 현재 작업·blocker·첫 다음 행동 | `PROJECT_RULES.md`가 선택한 current-state owner |
| 파일명·해시·사용자 승인 등 task fact | 원래 검수·보호 자료 또는 현재 task owner |
| 완료 과정·명령 상세·중복 보고 | Git 이력 또는 사용자 요청 보고서 |
