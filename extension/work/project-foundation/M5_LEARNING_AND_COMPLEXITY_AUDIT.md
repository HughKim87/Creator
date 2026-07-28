# M5 실제 결과 학습·복잡성 감사 설계

- 문서 역할: `phase-design`
- 단계 ID: `M5`
- lifecycle: `planned`
- 목적: 실제 영상 작업의 시간·채택·재작업·규칙 효과를 측정하고 과잉 시스템을 조기에 축소한다.
- 상위 설계: [재현 가능한 프로젝트 기반 전체 설계](../PROJECT_FOUNDATION_DESIGN.md)
- 현재 상태: [세션 핸드오프](../../../SESSION_HANDOFF.md)

## 단계 결과

장문 작업 보고서를 만들지 않고도 실제 영상 3건에서 자동화 순효과와 규칙의 예방·오탐을 계산할 수 있다.

## Entry gate

- `M5-E1`: M4 synthetic exit gate 통과
- `M5-E2`: 실제 작업의 보호 데이터·외부 행동 승인
- `M5-E3`: KPI 수집 항목과 비영구 aggregate owner 확정

## 포함 범위

- baseline·actual 수동 시간과 사용자 수정 시간
- 첫 결과 채택과 재작업 원인
- 규칙 trigger·예방 결함·오탐
- 자동·수동 단계와 approval wait
- 성공 절차·실패·candidate 추출 checkpoint
- 비영구 complexity audit

## 제외 범위

- 보호 원본·세션 전문·raw 로그의 영구 저장
- 규칙 자동 승격·자동 삭제
- 단일 영상 취향의 Core 승격
- KPI를 품질 의미의 대체물로 사용

## Execution slices와 slice gate

### M5-S1 — KPI 계약

작업별 최소 측정값, owner, retention을 확정한다.

Gate `M5-S1-G`: 보호 원문 없이 시간·채택·재작업·단계 수를 재계산할 수 있다.

### M5-S2 — 실제 영상 3건 측정

동일 기준으로 baseline과 actual을 수집한다.

Gate `M5-S2-G`: 각 결과가 작업 ID·측정 시점·사용자 승인과 연결되고 누락값이 pass로 계산되지 않는다.

### M5-S3 — 지식 환류

성공 절차·해결 실패·domain candidate·task evidence를 분류한다.

Gate `M5-S3-G`: task-specific 사실이 active Core rule로 직접 승격되지 않는다.

### M5-S4 — 복잡성 감사

추가된 문서·규칙·설정·승인 비용과 줄어든 단계·오류를 비교한다.

Gate `M5-S4-G`: 순효과가 없는 자동화와 규칙이 축소·보류 후보로 표시된다.

## Exit gate

- `M5-X1`: 실제 영상 3건의 시간·채택·재작업 지표 확보
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

실제 작업 3건에 적용할 최소 KPI 표와 보호·retention 경계를 사용자에게 승인 요청한다.
