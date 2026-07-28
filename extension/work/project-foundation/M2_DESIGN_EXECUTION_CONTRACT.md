# M2 설계·실행 계약 설계

- 문서 역할: `phase-design`
- 단계 ID: `M2`
- lifecycle: `planned`
- 목적: 작업 크기에 맞는 설계를 실행보다 먼저 고정하고 사용자 교정 시 기존 설계를 무효화한다.
- 상위 설계: [재현 가능한 프로젝트 기반 전체 설계](../PROJECT_FOUNDATION_DESIGN.md)
- 현재 상태: [세션 핸드오프](../../../SESSION_HANDOFF.md)

## 단계 결과

quick·standard·controlled 작업이 서로 다른 문서 비용을 가지면서도 controlled mutation은 승인 가능한 설계와 success gate 없이는 시작되지 않는다.

## Entry gate

- `M2-E1`: M1 exit gate 전건 통과
- `M2-E2`: clean clone에서 현재 설계 규칙과 회귀를 재현
- `M2-E3`: work request·state 계약을 변경할 exact Core 범위 승인

## 포함 범위

- `design / execution / verification / learning` phase
- 설계 fingerprint와 invalidation
- 결과·입력·보호·승인·acceptance·recovery 계약
- quick·standard·controlled 표현 비용
- 사용자 교정과 재승인 범위

## 제외 범위

- 영상 제작 runner
- CI·hook 구현
- 실제 작업 KPI 집계
- 모든 quick 작업의 영구 plan

## Execution slices와 slice gate

### M2-S1 — phase 계약

기존 work request·state와 문서 규칙에 최소 phase 표현을 설계한다.

Gate `M2-S1-G`: 기존 owner를 복제하지 않고 ready design 판정이 한 곳에 존재한다.

### M2-S2 — 설계 invalidation

목표·범위·gate 변경을 감지해 queued mutation을 차단하고 재승인 범위를 계산한다.

Gate `M2-S2-G`: 사용자 교정 replay가 이전 design을 성공으로 재사용하지 않는다.

### M2-S3 — 작업 등급 비용

quick은 대화 계약, standard는 비영구 plan, controlled는 bounded phase design을 사용한다.

Gate `M2-S3-G`: quick 작업에 새 plan file이 생성되지 않고 controlled 작업에는 exact gate가 있다.

### M2-S4 — 회귀·migration

기존 active work와 handoff가 새 계약에서도 단일 상태 owner를 유지하게 한다.

Gate `M2-S4-G`: 완료 상세가 startup 문서에 누적되지 않고 이전 work를 안전하게 읽는다.

## Exit gate

- `M2-X1`: ready design 없는 controlled mutation 차단
- `M2-X2`: 사용자 교정 시 fingerprint 무효화와 필요한 재승인 확인
- `M2-X3`: quick 영구 계획 생성 0
- `M2-X4`: handoff·work state·phase design의 상태 중복 0
- `M2-X5`: Core·Extension 전체 회귀 유지

## 중단·복구 조건

- 모든 작업에 같은 장문 schema를 강제하려 하면 중단한다.
- 상태를 handoff와 work snapshot에 중복 저장하면 단일 owner부터 복구한다.
- phase 계약이 사용자 승인보다 높은 권한을 갖게 되면 중단한다.

## Transition gate

설계 때문에 추가된 수동 입력·문서·승인 수와 차단한 오류를 비교한다. 순효과가 없으면 M3 전에 계약을 축소한다.

## 첫 활성화 행동

M1 결과와 기존 work request schema를 대조해 최소 추가 필드와 호환 전략을 제시한다.
