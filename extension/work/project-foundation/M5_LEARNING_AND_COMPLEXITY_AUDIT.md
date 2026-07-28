# M5 실제 결과 학습·복잡성 감사 설계

- 문서 역할: `phase-design`
- 단계 ID: `M5`
- lifecycle: `passed`
- 목적: 보호 원본을 열지 않고도 aggregate-only KPI 계약과 복잡성 audit을 검증하며, 실제 production 측정은 별도 승인 전 주장하지 않는다.
- 상위 설계: [재현 가능한 프로젝트 기반 전체 설계](../PROJECT_FOUNDATION_DESIGN.md)
- 현재 상태: [세션 핸드오프](../../../SESSION_HANDOFF.md)

## 단계 결과

장문 작업 보고서를 만들지 않고도 실제 영상 3건에서 자동화 순효과와 규칙의 예방·오탐을 계산할 수 있다.

## Entry gate

- `M5-E1`: M4 synthetic exit gate 통과
- `M5-E2`: 실제 보호 데이터 없이 synthetic 3-job fixture로 대체한다는 권장안 선택
- `M5-E3`: KPI 수집 항목과 비영구 aggregate owner 확정

## 포함 범위

- baseline·actual 수동 시간과 사용자 수정 시간의 aggregate-only 측정
- 첫 결과 채택과 재작업 원인
- 규칙 trigger·예방 결함·오탐
- 자동·수동 단계와 approval wait
- 성공 절차·실패·candidate 추출 checkpoint
- 비영구 complexity audit

## 제외 범위

- 보호 원본·세션 전문·raw 로그의 접근·영구 저장
- 규칙 자동 승격·자동 삭제
- 단일 영상 취향의 Core 승격
- KPI를 품질 의미의 대체물로 사용

## Execution slices와 slice gate

### M5-S1 — KPI 계약

작업별 최소 측정값, owner, retention을 확정한다.

Gate `M5-S1-G`: 보호 원문 없이 시간·채택·재작업·단계 수를 재계산할 수 있다.

### M5-S2 — 실제 영상 3건 측정

동일 기준으로 synthetic baseline과 actual을 수집하고, 실제 production KPI와 혼동되지 않게 retention을 `aggregate_only`로 고정한다.

Gate `M5-S2-G`: 각 결과가 작업 ID·측정 시점·사용자 승인과 연결되고 누락값이 pass로 계산되지 않는다.

### M5-S3 — 지식 환류

성공 절차·해결 실패·domain candidate·task evidence를 분류한다.

Gate `M5-S3-G`: task-specific 사실이 active Core rule로 직접 승격되지 않는다.

### M5-S4 — 복잡성 감사

추가된 문서·규칙·설정·승인 비용과 줄어든 단계·오류를 비교한다.

Gate `M5-S4-G`: 순효과가 없는 자동화와 규칙이 축소·보류 후보로 표시된다.

## Exit gate

- `M5-X1`: 보호 없는 synthetic 3-job의 시간·채택·재작업 aggregate 확보; 실제 production KPI는 미측정으로 명시
- `M5-X2`: 장문 per-job 보고서 없이 aggregate 재계산
- `M5-X3`: 규칙 승격은 독립 작업 반복·재현 gate 요구
- `M5-X4`: 무효 자동화·규칙의 축소 후보와 근거 확인
- `M5-X5`: active rule 자동 삭제·자동 승격 0

## 중단·복구 조건

- 측정이 보호 데이터 영구 복제를 요구하면 중단한다.
- 작업 수가 부족하면 결론을 candidate로 유지한다.
- 사용 빈도만으로 규칙을 삭제하거나 성과로 판정하지 않는다.

## Transition gate

M6 이식이 실제로 재사용 가치를 갖는지, 영상 프로젝트 한 곳의 편의만 수출하려는 것은 아닌지 평가한다.

## 첫 활성화 행동

실제 작업 3건에 적용할 최소 KPI 표와 보호·retention 경계를 사용자에게 승인 요청한다. 현재는 권장안으로 보호 없는 synthetic 3건을 사용한다.

## M5 gate evidence

- `M5-S1-G`: `extension/src/learning/metrics.py`가 작업 ID·시간·채택·재작업·단계 수·approval wait를 검증하고 `aggregate_only` retention만 허용한다.
- `M5-S2-G`: 보호 데이터 없는 synthetic 3-job row를 동일 기준으로 집계했고, 누락·path ID·raw content·per-job retention은 거부했다. 실제 production KPI는 측정하지 않았다.
- `M5-S3-G`: `audit_complexity`는 retain·candidate·defer만 반환하며 active Core rule을 자동 변경하지 않는다.
- `M5-S4-G`: actual time이 baseline보다 높거나 rework가 있으면 `candidate`를 제시하고, 표본 부족은 `defer`로 유지한다.

## M5 exit evidence

- `M5-X1~X5`: synthetic aggregate 3건, per-job 보고서 0, rule auto-promotion/deletion 0, complexity candidate 근거를 확인했다.
- 실제 영상 3건의 production KPI는 보호 데이터와 사용자 승인 전 미측정 상태이며, 이 단계의 안전한 권장 대체 범위로 기록한다.
