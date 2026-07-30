# 규칙 무손실 통합 개선 전체 설계

- 문서 분류: `overall-design`
- 상태: `active`
- 결과: 작업하며 쌓인 문서의 재사용 가능한 의미를 canonical owner로 흡수하고 규칙·검증 구조를 정리한 뒤, 역할이 끝난 원본 문서를 제거한다.
- 1차 목표와 실행 순서: 이 이니셔티브의 1차 목표는 문서 제거다. 의미 보존·규칙 통합·검증·참조 해제는 손실 없이 제거하기 위한 선행 작업이며, 실제 제거는 이 선행 작업이 모두 끝난 뒤 별도 승인 단계에서 수행한다.
- 삭제 원칙(사용자 지시): 선행 개선 단계 M0~M3에서는 파일을 삭제·이동하지 않고 후보 목록만 누적한다. M3가 통과해 개선 작업이 모두 끝난 뒤 exact 목록으로 사용자 승인을 받고 M4에서 한 번에 처분한다.
- 독자: 현재 개선을 실행하거나 다음 세션에서 재개하는 프로젝트 에이전트와 승인자.
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`가 상위 권위이며, 이 문서는 정책이나 Core 변경 승인이 아니다.
- 프로젝트 방향: [장기 사용자 결과와 선택 기준](../../PROJECT_DIRECTION.md)
- 현재 상태 owner: `SESSION_HANDOFF.md`
- 활성 단계: [M1 보존 검증·최소 변경안](rule-preservation/M1_PRESERVATION_VALIDATION_AND_MINIMAL_CHANGE.md)
- M0 evidence: [M0 규칙 보존 지도](rule-preservation/M0_RULE_CONSERVATION_MAP.md) — optional reference, startup-required 아님
- reference-evidence: [Claude 규칙 손실 이력 분석](../reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md)

## 사용자 의도와 확정 방향

- 1차 목표는 역할이 끝난 문서를 활성 트리에서 제거하는 것이다. 과거 경험의 보호 의미를 잃지 않고 더 명확한 owner와 검증 구조로 이전하는 일은 제거 전 필수 조건이다.
- 과거 문구를 모두 보존하지 않는다. 현재도 유효한 `trigger / protected outcome / action / exception / verification`만 보존하고, 충돌·중복·위험·과업 전용 의미는 근거를 남겨 폐기하거나 보류한다.
- 개선을 반복할수록 규칙이 자동 증가해서도, 축약 과정에서 의미가 자동 소실되어서도 안 된다. 새 규칙보다 기존 owner 강화, 문구 수보다 행동·구조 검증을 우선한다.
- 다른 agent는 보고서의 제안이나 이전 대화의 승인을 현재 권위로 추정하지 않는다. 최신 사용자 지시, 현재 router, exact 승인 상태를 다시 확인한다.
- 규칙 축소 전에 현재·과거 의미의 보존 지도를 만든다. 문장 일치가 아니라 `trigger / protected outcome / action / exception / verification / owner / lineage`를 비교한다.
- 전체 189개 커밋을 같은 깊이로 읽지 않는다. 현재 활성 규칙 표면의 직접 계보를 우선하고, 삭제·rename된 선행 owner와 확인된 의미 공백에만 범위를 확장한다.
- 과거 규칙·보고서·backup은 evidence이지 현재 authority가 아니다. 보호 `inputs/`·`outputs/`는 이 작업 범위 밖이다.
- 새 Core 규칙 파일을 만들어 규칙 팽창을 해결하지 않는다. 기존 owner의 최소 수정·통합을 우선한다.
- 절대 단어 수 상한, 특정 문구 정규식 존재 검사, 자동 Git 덮어쓰기 복구는 손실 방지 장치로 사용하지 않는다.
- Core 변경 전에는 exact 경로·이유·extension-only 대안·보존 지도를 제시하고 현재 대화의 사용자 승인을 받는다.
- 현재 미커밋 사용자 변경은 별도 lineage로 보존하며 승인 없이 restore·stage·commit하지 않는다.

## 교차검증으로 확정한 기준

| 항목 | evidence | 설계 반영 |
|---|---|---|
| `PROJECT_RULES.md`의 팽창·0단어 재구축 6사이클 | direct remeasurement | 재작성 전 의미 보존 gate를 둔다 |
| 현재 활성 규범 37파일·18,844단어 | unresolved | corpus 정의·재현 명령이 없어 근거에서 제외한다. M0-S1이 corpus를 재정의·재측정한 값만 기준으로 쓴다 |
| 외부 입력 불신·최소 권한·도구 최소 호출·출처 규율의 활성 owner 공백 | direct remeasurement | M0에서 현재 적용성과 owner를 판정 |
| 도구 성공과 콘텐츠 승인 분리 | direct remeasurement | `document-work`와 domain validation에 의미가 생존하므로 중복 복원 금지 |
| 과거 자료 열람·검증 등급·쓰기 안전 | direct remeasurement | 전손이 아니라 부분 승계로 분류하고 공백만 검토 |
| 3연속 실패 뒤 대기→범위 내 방법 변경 | direct remeasurement | 최신 자율성 정책과 충돌하므로 과거 문구 자동 복원 금지 |
| failures 8,358단어 압축 | shared-source agreement | 개수 기준과 나머지 표본의 의미 보존은 M0 미해결 항목 |

## 불변 경계

- 보존하기로 한 의미는 통합 전후 정확히 한 canonical owner에 있어야 한다.
- 삭제·병합·강등되는 의미는 `preserved / migrated / superseded / task-specific / unsafe-outdated / candidate-loss` 중 하나로 근거와 함께 분류한다.
- 완료 phase·보고서·원시 명령 기록을 startup-required read로 만들지 않는다.
- 한 작업의 선호·수치·문구를 foundation 규칙으로 자동 승격하지 않는다.
- 구조·동작 테스트는 owner·route·실제 gate를 검증하고 자연어 문장 조각을 고정하지 않는다.
- 단계 전환 때마다 `PROJECT_RULES.md`에서 현재 행동에 맞는 규칙을 다시 선택하고 active phase에 적용 owner와 검증을 기록한다.

## 산출물·위임 계약

| artifact | 수 | owner·독자·보존 |
|---|---:|---|
| overall-design | 1 | 이 문서; 전체 방향과 단계 의존성을 읽는 agent·승인자; 작업 종료 때 historical |
| active phase-design | 1 | 현재 단계 문서; 실행 agent; 단계 통과 뒤 active route에서 제거 |
| phase reference-evidence | 1 | M0 보존 지도; M0~M2의 판정·검증과 M4 처분 판정 독자; M4 종료 때 historical |
| current-state | 1 | `SESSION_HANDOFF.md`; 다음 session; 검증된 현재 상태만 유지 |

- Claude 보고서는 사용자 제공 교차검증 자료이며 위 artifact budget 밖의 기존 reference다. 새 보고서나 미래 phase 상세 문서는 만들지 않는다.
- `PROJECT_DIRECTION.md`는 initiative 밖의 안정된 방향 reference이며 이 설계의 상태·gate·evidence를 소유하지 않는다.
- 현재 handoff mode는 `portable`이다. 필수 방향·설계·evidence와 승인된 규칙 변경을 같은 Git checkpoint에 보존하며, 후속 agent는 해당 commit을 기준선으로 사용한다.
- 상태 문서는 목표·현재 단계·첫 행동·blocker만 소유한다. 보존 지도는 판정 행과 baseline을, Git은 원문 diff와 완료 이력을 소유한다.
- 위임 전에는 다른 agent가 chat 없이 목표, 금지사항, 승인 경계, 첫 행동, gate를 재진술할 수 있는지 확인한다. 새 대화에서 필요한 Core 승인은 다시 exact 범위로 받는다.

## 단계 지도

| 단계 | 의존성 | 한 줄 결과 |
|---|---|---|
| M0 규칙 계보·손실 감사 | 없음 | 손실 후보와 현재 의미가 evidence label·현재 owner·lineage로 분류된 보존 지도가 완성됨 |
| M1 보존 검증·최소 변경안 | M0 passed·`M0-T1`이 필요 판정 | 문구 고정 없이 손실을 탐지하는 검증과 extension-only 대안·exact 변경 범위가 확정됨 |
| M2 복원·통합 단일 체크포인트 | M1 passed·해당 대화의 exact Core 승인 | 승인된 손실만 복원하고 중복을 상쇄 압축해 의미 누락·중복 owner가 0이 됨 |
| M3 시작 경로·회귀·종료 | M2 passed 또는 `M0-T1`이 M1·M2 불필요로 판정 | startup read가 활성 작업만 가리키고 Core·Extension·maintenance 회귀와 음성 대조가 통과함 |
| M4 완료 후 문서 처분 | M3 passed·선행 개선 작업 종료·exact 삭제 목록 사용자 승인 | 지식·참조·복구 검증이 끝난 문서만 제거되고 고아 링크와 유일 evidence 손실이 0임 |

M0 결과 candidate-loss가 0이면 복원할 손실이 없으므로 M1·M2를 건너뛰고 M3로 전환한다. M4는 이 분기와 무관하게 모든 선행 개선 작업이 끝난 뒤에만 시작한다. 단계는 자동으로 이어지지 않으며 각 전환 gate가 필요성을 다시 판정한다.

## 전체 성공 기준

- M0 보존 지도의 모든 유지 항목이 최종 diff에서 정확히 한 owner로 추적된다.
- 복원하지 않은 과거 항목은 폐기·대체·보류 근거가 있으며 과거 권위를 현재 권위로 오인하지 않는다.
- 활성 규칙과 startup-required 문서의 읽기 비용이 M0-S1의 재현 가능한 기준보다 증가하지 않는다. 재현 명령과 파일 목록이 없는 수치는 합격 근거로 쓰지 않는다.
- M3에서 완료된 이전 이니셔티브 설계 8건의 지식 추출·참조 해제·복구 검증과 exact 처분 목록이 완성된다.
- M4에서 사용자가 승인한 exact 목록만 제거되고, 완료 문서가 시작 경로에 남지 않으며 유일 evidence·승인·계보 손실이 0이다.
- literal phrase 존재만 검사하는 신규 테스트가 없고, 기존 관련 테스트는 구조·동작 검증으로 대체된다.
- 승인된 Core 변경 gate와 Extension 회귀, 문서 무결성, scoped diff가 모두 통과한다.
- 보호 데이터 접근, 외부 효과, dependency 설치, push는 별도 승인 없이는 수행하지 않는다.

## 다음 실행

`M0`의 exit/transition gate는 통과했다. 다음 실행은 [M1 보존 검증·최소 변경안](rule-preservation/M1_PRESERVATION_VALIDATION_AND_MINIMAL_CHANGE.md)의 `M1-S1`이며, L01~L05·L08~L10을 의미 단위로 재검증한 뒤 M2 exact 변경 범위를 확정한다. M1 검증이 끝나기 전에는 규칙 본문을 변경하지 않는다.
