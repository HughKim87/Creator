# File Cleanup and Deletion

- Purpose: classify and mutate only files whose knowledge extraction, ownership, dependency, approval, and recovery checks are complete.
- Read when: reviewing project files, documents, evidence, reports, caches, or derivatives for retention, cleanup, deletion, move, rename, or removal from the active tree.
- Authority: `PROJECT_RULES.md` is higher authority and selects any additional extraction, document, version-control, protected-data, domain, or boundary owner.

## FCL01 — 추출 완료 후 정리

- 조건: 파일을 필요없음·중복·역사 자료·재생성 가능 자료로 분류하거나 삭제·이동 후보로 만들 때.
- 행동:
  1. exact 대상, 실제 변화, 삭제·이동 권한, 복구 수단, 보존 목적을 먼저 고정한다.
  2. 상위 router가 함께 선택한 파일 추출 규칙을 먼저 적용해 추출 결과와 canonical owner를 확인한다. 추출 결과가 없으면 `추출 없음`의 근거와 확인 범위를 남긴다.
  3. active rule·현재 상태·사용자 승인·source lineage·유일한 검수 증거·재생성 경로·남은 링크를 확인한다.
  4. 각 파일을 `유지`, `활성 트리 제외 후보`, `재생성 가능 후보`, `삭제 승인 대기` 중 하나로 분류한다. 서로 다른 파일을 한 번에 묶어 판단하지 않는다.
  5. 링크·라우팅·테스트·문서 무결성을 검증한 뒤, 사용자가 exact 삭제·이동 대상을 승인한 경우에만 mutation을 실행한다.
- 예외:
  - 경로 segment가 `inputs`·`outputs`인 원본·파생물은 exact 대상과 목적, 삭제·이동 승인 없이는 열거·읽기·삭제하지 않는다.
  - 사용자 승인·현재 상태·source lineage를 유일하게 증명하는 파일은 규칙 추출이 완료되어도 삭제하지 않는다.
  - 완료 상세를 보관하기 위해 repository-local backup/archive 복제본을 만들지 않는다. Git 이력 또는 사용자가 지정한 외부 보존 경계를 사용한다.
  - `.pyc`, `__pycache__`, 임시 렌더처럼 재생성 가능한 파일도 활성 참조와 재생성 경로를 확인하기 전에는 삭제하지 않는다.
- 검증:
  - 정리 판정마다 exact path, owner, 추출 완료 여부, 남은 참조, 복구 방법, 승인 상태를 확인한다.
  - 삭제·이동 전 scoped diff와 대상 목록이 사용자가 승인한 범위와 일치하는지 확인한다.
  - active rule route에 고아 링크가 없고, 삭제 대상이 테스트·계약·현재 상태 owner에 필요하지 않은지 확인한다.
  - strict UTF-8, NUL 0, trailing whitespace 0, 관련 회귀 테스트와 유지보수 검증을 통과시킨다.

## FCL02 — 문서 삭제 전 지식 추출과 의존성 해제

- 조건: 계획·보고서·handoff·검수 기록·증거 index·과거 작업 guide를 삭제 후보로 확정하려 할 때.
- 행동:
  1. 파일 추출 규칙으로 문서의 성공한 절차·검증 기준·재사용 가능한 실패·현재 상태·사용자 승인·source lineage를 분류한다.
  2. 성공 지식은 특정 작업명·파일명·일회성 수치를 제거하고 `조건 / 행동 / 예외 / 검증`으로 압축해 가장 좁은 기존 active owner에 반영한다. 반복 근거가 부족하면 기존 candidate owner에 둔다.
  3. 실패 지식은 `증상 / 확인된 원인 / 실패한 접근 / 해결 / 검증 / 예방`이 갖춰지고 재발 방지 가치가 확인된 경우에만 상위 route가 선택한 기존 failure owner에 합친다. 일회성 추측이나 미검증 해석은 규칙으로 승격하지 않는다.
  4. 현재 상태·승인·source lineage의 유일한 증거는 삭제하지 않는다. 계속 필요하면 현재 owner로 이전하고, 이전할 수 없으면 삭제 대상에서 제외한다.
  5. inbound link·router·테스트 fixture·build script·startup·handoff 참조를 검색하고, 삭제 문서가 맡던 실행·검증·탐색 의존성을 현재 owner 또는 중립 fixture로 이전한다.
  6. Git tracked 문서는 복구 가능한 commit을 확인한다. untracked 문서는 사용자가 승인한 외부 복구 경계가 없으면 삭제 후보로 확정하지 않는다.
  7. 추출·owner 반영·참조 이전을 검증한 뒤 exact 삭제 목록, 추출 결과, 복구 방법을 보고하고 사용자가 해당 목록을 승인한 경우에만 삭제한다.
- 예외:
  - 0-byte이면서 참조가 없는 문서는 `추출 없음`으로 기록할 수 있지만 참조·복구·승인 검사는 생략하지 않는다.
  - 상호 참조하는 과거 보고서는 같은 checkpoint에서 링크를 해제하고 유일한 승인·상태·계보 증거가 남는 경우에만 묶어서 삭제 후보로 제시한다.
  - 분석·보고·추출만 요청받은 작업은 삭제 권한을 포함하지 않는다.
  - 삭제 근거를 남기기 위한 sidecar 추출 보고서를 새로 만들지 않는다. 재사용할 지식은 canonical owner에 반영하고 완료 상세는 Git 이력 또는 사용자 지정 외부 경계에 둔다.
- 검증:
  - 각 삭제 후보에 exact path, 추출 결과, 반영 owner, 미추출 항목, inbound 참조, 테스트 의존성, 복구 commit 또는 외부 복구 경계, 승인 상태가 있다.
  - active rule·candidate·검증된 실패·현재 상태·사용자 승인·source lineage가 삭제 대상에만 남아 있지 않다.
  - 링크·고아 문서·관련 회귀·유지보수 검증을 통과하며, 삭제된 경로와 보호 경로가 staged diff에 섞이지 않는다.

## 정리 판정의 경계

| 파일 상태 | 기본 판정 |
|---|---|
| 현재 정책·계약·규칙·schema·검증 코드 | 유지 |
| 현재 상태·승인·source lineage의 유일한 owner | 유지 |
| 추출 완료된 중복 보고·완료 과정 | Git 또는 사용자 승인에 따라 활성 트리 제외 후보 |
| 재생성 가능한 cache·임시 산출물 | 재생성 경로 확인 후 삭제 승인 대기 |
| 보호 원본·보호 파생물 | exact 대상·목적·삭제 승인 전까지 유지 |
