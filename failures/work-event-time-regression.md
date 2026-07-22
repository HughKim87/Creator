# 작업 event 시각의 snapshot 역행

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 04 첫 통합 테스트
- 마지막 검증: 2026-07-23
- 적용 범위: 작업 event, snapshot `updated_at`, 고정 fixture 시각, append 전 검증

## 증상

고정된 작업 생성 시각보다 실행 환경의 현재 UTC가 앞선 테스트에서 전이 event는 원장에 append됐지만 snapshot 갱신이 `updated_at < created_at`로 거부돼 projection pending 상태가 됐다.

## 확인된 원인

event 구조와 상태 전이는 append 전에 검사했지만 새 event 시각이 현재 snapshot 시각보다 단조 증가하는지는 snapshot을 쓸 때까지 검사하지 않았다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 04 첫 31개 테스트 | blocked 전이 event append 후 snapshot 시간 순서 검증 실패 | 1 | 전이 시각을 UTC 초 정밀도로 정규화하고 현재 `updated_at`보다 이르면 append 전에 거부 |
| Stage 04 입력 선검증 보강 테스트 | 고정 생성 시각 뒤의 호출에 실행 시점 기본값을 사용해 기대한 형식 오류보다 시각 회귀 오류가 먼저 발생 | 1 | 후속 호출 시각을 `03:01Z`로 고정하고 기대 예외도 `InputContractError`로 좁혀 33개 테스트 통과 |

## 해결과 검증

- timezone-aware event 시각을 append 전에 검증한다.
- snapshot 시각보다 이른 event는 `invalid_transition`으로 원장 변경 없이 거부한다.
- 명시적으로 증가하는 시각을 사용한 전체 31개 테스트가 성공했다.

## 재사용 규칙

- event 정본을 먼저 쓰는 구조에서는 projection만이 아니라 event 자체의 시간 단조성을 append 전에 검사한다.
- 고정 시각 fixture와 실제 clock을 섞을 때 순서를 명시한다.
- 고정 시각으로 snapshot을 만드는 테스트의 후속 event에도 명시적 시각을 사용해 실행 시각 의존성을 없앤다.
- projection 실패로 뒤늦게 발견할 수 있는 조건은 가능한 한 원장 쓰기 전 계약으로 승격한다.

## 근거

- [작업 기록·현재 상태 계약](../docs/WORK_STATE_CONTRACT.md)
- [WorkStateService](../src/file_data/work_state.py)
- [Stage 04 계획](../docs/build/stage-04-work-state.md)
