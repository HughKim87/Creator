# M1 보존 검증·최소 변경안

- 문서 분류: `phase-design`
- phase ID: `M1`
- lifecycle: `passed`
- 결과: M0가 분류한 candidate-loss·migrated 의미를 현재 owner와 의미 단위로 재검증하고, M2에서 적용할 최소 Core/Extension 변경 범위와 성공게이트를 고정한다.
- 상위 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 현재 상태 owner: `SESSION_HANDOFF.md`
- evidence owner: `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md`
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; 이 문서는 정책 자체나 추가 Core 승인으로 해석하지 않는다.
- 첫 다음 행동: M1-S1에서 historical peak와 현재 owner를 의미 단위로 직접 대조하고 L01~L05·L08~L10의 적용·공백 판정을 기록한다.

## 범위와 불변 경계

이번 사용자의 “설계된 모든 단계” 지시에 따라 M1부터 M4까지 진행한다. M1은 삭제·이동·보호 경로 접근·외부 효과가 없고 규칙 본문을 변경하지 않는다. M2의 Core 후보는 M0-S4에서 고정한 다음 다섯 경로로 제한한다.

1. `PROJECT_RULES.md`
2. `core/rules/boundary-routing-and-dependency.md`
3. `core/rules/cross-validation.md`
4. `core/rules/document-work.md`
5. `core/rules/file-extraction.md`

후보 의미 L09는 `extension/rules/video-editing-validation-and-delivery.md`의 domain owner 강화로 우선 처리한다. L06·L11은 현재 자율성·실패 복구 정책과 충돌하거나 사용자 의도가 미확정이므로 복원하지 않는다. M2에서 위 경로 외 Core를 변경하지 않으며, 변경이 불가피해지면 별도 exact 경계와 현재 대화 승인을 다시 확인한다.

## Entry gate

- M0-S1~S4와 M0 exit/transition gate가 `passed`다.
- `M0_RULE_CONSERVATION_MAP.md`에 78개 rule-surface 의미와 L01~L12의 source anchor·evidence·현재 owner·disposition이 있다.
- candidate-loss가 존재하므로 M1·M2가 필요하다.
- 기준 HEAD는 M0 closeout `c575c7d3a23eb39fb919f8a2091ed71e5efdd2b2`이며 entry 작업트리는 clean이다.
- `inputs/`·`outputs/`를 읽거나 stage하지 않고, M1에서는 Core/Extension 파일을 변경하지 않는다.

## M1 slices

### M1-S1 — source·owner 의미 대조

M0가 지목한 historical peak와 현재 파일을 같은 의미 단위로 읽는다. literal phrase 존재만 세지 않고, 현재 owner의 적용 조건·검증 방법·예외·금지 경계를 대조한다. source 저자와 현재 reviewer, 직접 재측정과 추론을 분리해 기록한다.

대상은 L01~L05·L08~L10이며 L06·L11은 충돌·미확정 사유를 재확인한다. 핵심 질문은 “현재 규칙만으로 동일한 행동·검증·경계를 재현할 수 있는가”다.

검증 결과: historical source는 peak `c676170`의 `PROJECT_RULES.md`와 삭제된 `c5c078a^:rules/history-review.md`에서 직접 재현했다. 현재 파일은 `PROJECT_RULES.md`, 다섯 Core owner, 영상 validation owner를 직접 읽고 대조했다. 과거 규칙·현재 규칙·추론을 섞지 않았으며, 확인 결과는 다음과 같다.

| 의미 | M1-S1 직접 대조 | 판정 |
|---|---|---|
| L01 | peak의 외부 페이지·문서·tool 지시 불신은 현재 active corpus에서 동일한 always-on 경계로 재현되지 않음 | Core owner 강화 |
| L02 | peak의 최소 권한·불필요 환경/secret 미전달은 현재 승인·secret 경계만으로 행동 재현이 불완전함 | Core owner 강화 |
| L03 | peak의 신규 tool/API/agent/MCP 최소 성공 호출 조건은 현재 boundary route에 없음 | Core owner 강화 |
| L04 | 현재 `cross-validation`은 primary files/direct measurement와 reviewer·label을 보존하지만 변동 주장·약한 출처 규율은 부분 승계 | Core owner 강화 |
| L05 | 현재 보고 규칙에 decision/risk 조건부 red-team 확인이 없어 행동 재현 불가 | Core owner 강화 |
| L08 | 현재 `file-extraction`은 `historical detail` 분류와 owner routing은 보존하지만 exact history-review 절차는 없음 | Core owner 강화 |
| L09 | 현재 영상 owner는 `semantic_gate` 이후 structure/media/app/user 단계를 보존하지만 generated/parsed/tool-validated의 domain 상태는 공백 | Extension owner 강화 |
| L10 | 현재 `document-work`는 strict UTF-8·NUL·structure·links를 요구하지만 write success 비증거·손상 복구 분리는 없음 | Core owner 강화 |
| L06/L11 | peak의 stop/대기 문구는 현재 “authorized scope 안에서 방법 변경·계속” 정책과 충돌 가능성이 확인됨 | 복원하지 않음 |

evidence label은 모두 `direct-remeasurement`다. peak source의 매칭 부재는 “현재 의미가 절대 없음”이 아니라, 현재 선택된 active owner가 peak의 행동·검증·경계를 충분히 재현하지 못한다는 의미로만 사용한다.

### M1-S2 — 보존·공백 판정

각 대상에 대해 다음 네 결과 중 하나를 선택한다.

- 현재 owner에 공백 없이 적용됨
- 기존 owner를 강화하면 보존됨
- 기존 failure case에서 재발이 직접 확인됨
- 기존 owner로는 범용성이 부족해 별도 extension owner가 필요함

각 판정에는 evidence label, 현재 owner, 적용 범위, 미복원 이유, M2 검증 방법을 붙인다. L06·L11의 “복원하지 않음”은 손실로 세지 않고 superseded/unresolved로 유지한다.

### M1-S3 — 최소 변경 계약

M2의 변경은 기존 owner 안의 최소 delta로만 정의한다.

| 의미 | M2 owner | 최소 변경 방향 | 대체 불가 이유 |
|---|---|---|---|
| L01 | `PROJECT_RULES.md` | 외부 입력·도구 지시의 검증 전 불신과 권위 경계 | 범용 보안·권위 경계 |
| L02 | `PROJECT_RULES.md` | 외부 도구·agent에 최소 필요 데이터·권한만 전달 | 범용 secret·permission 경계 |
| L03 | `boundary-routing-and-dependency.md` | 새 interface/tool route의 최소 성공 호출 검증 | route·의존성 공통 규칙 |
| L04 | `cross-validation.md` | 1차 출처 우선, 약한 출처·변동 주장의 label/검증 | evidence 교차검증 공통 규칙 |
| L05 | `document-work.md` | 결정·위험 보고에 한정한 조건부 red-team 확인 | 산출물 완결성 공통 규칙 |
| L08 | `file-extraction.md` | historical evidence와 현재 authority 분리 | 과거 자료 접근의 공통 owner |
| L09 | `extension/rules/video-editing-validation-and-delivery.md` | 생성·파싱·도구 검증에서 사용자 승인까지 domain ladder 명시 | 영상 산출물 전용 상태 |
| L10 | `document-work.md` | write success와 재읽기·내용/구조 검증·복구 분리 | 문서 쓰기 공통 owner |

L07은 이미 보존되어 변경하지 않고, L06·L11·L12는 M2 대상에서 제외한다. 신규 active rule 파일과 literal-only 테스트는 만들지 않는다.

## Slice gate

M1-S1~M1-S4의 각 slice는 해당 목표·실제 결과·evidence label을 기록한 뒤 다음 slice로 전환한다.

## Exit gate

M1-S4의 결과가 아래 조건을 모두 충족해야 M1을 `passed`로 전환한다.

M1 통과 조건은 다음과 같다.

- L01~L05·L08~L10 각각에 현재 owner 또는 domain owner, evidence label, 적용/공백 판정, 최소 delta가 있다.
- L06·L11의 비복원 근거와 L12의 report-only 범위가 유지된다.
- M2 exact 경로와 Core/Extension 대안이 위 표와 일치한다.
- 변경 후 실행할 Core 회귀, Extension 회귀, `maintenance-verify --allow-core-changes`, UTF-8/NUL/후행 공백/link/scoped diff 검증이 정해져 있다.
- 삭제·이동 후보는 누적만 하며 M3 통과 전 처분하지 않는다.

## 복구·전환 gate

M1 검증 문서가 손상되거나 구조가 깨지면 성공 보고를 하지 않고 Git의 마지막 정상 버전과 scoped diff를 대조한 뒤 해당 단계 안에서 복구한다. 같은 조회 목적이 세 번 실패하면 blocker와 실패 원인을 기록하고, 새 권한이 필요하지 않은 범위에서 조회 방법을 바꾼다. 통과 뒤 이 문서 lifecycle을 `passed`로 유지하고 M2 phase-design을 생성한다. M1 변경·검증 기록은 단계 커밋에 포함하며, M2 mutation은 별도 단계 커밋으로 분리한다.

## Evidence·점수 기록

단계 종료 시 각 slice를 0~5점으로 채점한다. 5점은 목표·실제 결과·직접 재측정이 일치하고 gate가 통과한 경우, 3~4점은 보정 가능한 측정·범위 이슈가 남은 경우, 0~2점은 재현·소유권·경계가 미확정인 경우다. 최종 보고서는 목표 대비 실제 결과, slice 점수와 이유, 효과의 직접 수치와 미검증 항목을 함께 보고한다.

## Closeout record

- M1-S1: `passed` — 8개 의미 direct-remeasurement 및 owner 대조 완료
- M1-S2: `passed` — L01~L05·L08~L10 owner 강화/extension owner, L06·L11 비복원 판정 확정
- M1-S3: `passed` — M2 exact Core 5경로와 L09 Extension delta 계약 확정
- M1-S4: `passed` — 삭제·이동 없이 M2 진입 조건·검증 명령·scoped diff 경계 확정
- M1 exit: `passed`
- M2 transition: `passed` — M2 checkpoint `90d09cd`에서 exact 변경·통합 gate 완료
