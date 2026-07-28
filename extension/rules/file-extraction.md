# 파일 추출 규칙

- Purpose: 파일에서 재사용 가능한 규칙·실패 지식·현재 상태·계보 정보를 분리해 canonical owner에 보존한다.
- Read when: 파일을 삭제하지 않고 규칙·지식·검수 근거만 추출하거나, 과거 영상 자료를 재활용 가능한 규칙 후보로 분석할 때.
- Authority: `PROJECT_RULES.md`와 `extension/README.md`가 상위 routing owner이며, cross-boundary 작업은 상위 route가 선택한 boundary procedure를 따른다.

## FEX01 — 추출 범위와 owner 판정

- 조건: 파일 또는 같은 영상 spine의 직접 연결 자료에서 이후 작업에 재사용할 내용을 추출하려 한다.
- 행동:
  1. exact 대상, 접근 목적, 허용 읽기·쓰기 범위, 추출 결과의 독자를 먼저 고정한다.
  2. 지정된 파일과 목적상 직접 필요한 연결 자료만 읽는다. 보호 경로는 exact 대상의 부분집합만 접근하고 sibling을 넓게 열거하지 않는다.
  3. 내용을 `active rule`, `candidate`, `verified failure`, `current state`, `source lineage`, `task fact`, `historical detail`, `disposable derivative`로 분류한다.
  4. 재사용 가능한 판단은 조건·행동·예외·검증으로 압축해 가장 좁은 기존 rule owner에 추가한다. 기존 owner가 책임을 섞게 만들 때만 새 rule을 만든다.
  5. 단일 영상의 수치·프레임·파일명·해시·절대 경로·사용자별 취향은 active rule로 승격하지 않고 영상별 후보·검수 자료의 근거로 남긴다.
  6. 추출 작업만 요청된 경우 삭제·이동·이름 변경을 예약하거나 실행하지 않는다.
- 예외:
  - 사용자 승인·현재 상태·source lineage를 입증하는 유일한 자료는 중복으로 처리하지 않는다.
  - 원인·해결·검증이 끝난 범용 실패만 상위 route가 선택한 failure owner로 승격을 검토하며, foundation 변경은 별도 승인 경계를 따른다.
  - 영상별 미승격 판단은 `VIDEO_EDITING_RULE_CANDIDATES.md`에 보류 지식으로 둔다.
- 검증:
  - 추출 항목마다 evidence label, canonical owner, 승격/보류 이유를 지정한다.
  - 새 active rule은 `Purpose / Read when / Authority`와 `조건 / 행동 / 예외 / 검증`을 가진다.
  - 정확한 rule route가 존재하고 기존 rule·candidate·failure owner와 중복되지 않는다.
  - 보호 자료의 내용, 비밀, 사용자 원본을 extension 규칙·보고서·캐시에 복사하지 않는다.

## 추출 결과의 owner

| 추출 내용 | 보존 owner |
|---|---|
| 반복되고 일반화된 영상 편집 조건 | 기존 `extension/rules/` owner |
| 단일 영상에서만 확인된 판단 | `extension/docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md` |
| 범용 원인·해결·검증이 끝난 실패 | 상위 route가 선택한 failure owner 검토 |
| 현재 작업·blocker·첫 다음 행동 | `PROJECT_RULES.md`가 선택한 current-state owner |
| 프레임·파일명·해시·사용자 승인 등 task fact | 원래 검수·보호 자료 |
| 완료 과정·명령 상세·중복 보고 | Git 이력 또는 사용자 요청 보고서 |
