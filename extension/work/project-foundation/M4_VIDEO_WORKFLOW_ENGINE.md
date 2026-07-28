# M4 영상 제작 workflow 실행 엔진 설계

- 문서 역할: `phase-design`
- 단계 ID: `M4`
- lifecycle: `passed`
- 목적: 검증된 단계 계약 위에서 영상 제작의 다음 단계를 선택·실행·검증·재개한다.
- 상위 설계: [재현 가능한 프로젝트 기반 전체 설계](../PROJECT_FOUNDATION_DESIGN.md)
- 현재 상태: [세션 핸드오프](../../../SESSION_HANDOFF.md)

## 단계 결과

합성 `VIDEO_JOB`이 research부터 upload package까지 같은 상태 전이를 사용하고 사용자 승인 단계에서 반드시 멈춘다.

## Entry gate

- `M4-E1`: M3 exit gate 전건 통과
- `M4-E2`: 기존 영상 skill·artifact·approval owner 확정
- `M4-E3`: 외부 browser·NotebookLM 실행은 exact 작업 승인과 capability 확보

## 포함 범위

- `VIDEO_JOB` next-step selector
- 단계별 preflight·execute·verify·transition interface
- local deterministic adapter와 external agent adapter 분리
- artifact hash·승인 상태 기반 resume
- synthetic end-to-end fixture

## 제외 범위

- 창작 방향 자동 승인
- 보호 원본을 CI fixture로 사용
- 사용자 계정·쿠키·profile 복제
- 실제 게시·업로드 자동 실행

## Execution slices와 slice gate

### M4-S1 — 상태·다음 단계

현재 artifact와 gate로 실행 가능한 다음 단계 하나를 결정한다.

Gate `M4-S1-G`: 준비되지 않은 단계가 선택되지 않고 `needs_user / unavailable`이 성공과 구분된다.

### M4-S2 — 단계 interface

research·video·caption·title/thumbnail·upload package를 같은 interface로 감싼다.

Gate `M4-S2-G`: 각 단계가 input·output·verification·recovery를 명시한다.

### M4-S3 — adapter 경계

결정론적 local 작업과 browser·NotebookLM agent 작업을 분리한다.

Gate `M4-S3-G`: 외부 adapter unavailable이 local 성공을 오염시키지 않는다.

### M4-S4 — resume

artifact hash와 승인 상태로 중단 뒤 재개한다.

Gate `M4-S4-G`: 검증된 단계를 재실행하지 않고 변조된 artifact는 재검증한다.

### M4-S5 — synthetic vertical acceptance

보호 데이터 없는 fixture로 전체 workflow를 실행한다.

Gate `M4-S5-G`: 승인 단계에서 `needs_user`, 최종 네 파일 계약에서 ready가 된다.

## Exit gate

- `M4-X1`: 합성 job 전체 상태 전이 통과
- `M4-X2`: review gate 자동 통과 0
- `M4-X3`: interruption 뒤 검증 단계 중복 실행 0
- `M4-X4`: external unavailable 오승인 0
- `M4-X5`: 현재 최종 output 네 파일 계약 유지

## 중단·복구 조건

- agent가 사용자 창작 결정을 자동 승인하면 중단한다.
- 보호 데이터가 synthetic test에 필요해지면 fixture 설계를 복구한다.
- 외부 adapter 실패를 무한 반복하지 않고 blocker와 재시작 조건을 handoff에 남긴다.

## Transition gate

실제 작업 전 synthetic 실행 시간·수동 gate·복구 가능성을 검토한다. 엔진이 skill 직접 실행보다 복잡하면 범위를 축소한다.

## 첫 활성화 행동

현재 VIDEO_JOB과 단계별 skill 계약을 읽고 next-step selector가 필요한 최소 상태 필드를 확정했다. M4 synthetic acceptance를 통과했으므로 다음은 M5 learning·complexity audit이다.

## M4 gate evidence

- `M4-S1-G`: `WorkflowEngine.next_step()`이 첫 pending 또는 기존 active stage 하나만 선택하고 `needs_user`·`blocked`를 성공으로 승격하지 않는다.
- `M4-S2-G`: `preflight`·`execute`·`verify`·`transition` 인터페이스가 입력 job, 결과 artifact, 검증·복구 상태를 분리해 반환한다.
- `M4-S3-G`: `LocalSyntheticAdapter`와 `ExternalAgentAdapter`를 분리했고 external unavailable은 blocked boundary로 기록되며 synthetic success가 되지 않는다.
- `M4-S4-G`: `artifact_hashes`를 재검증해 동일 artifact를 재실행하지 않고, hash drift는 adapter 실행 전에 차단한다.
- `M4-S5-G`: 보호 데이터 없는 v3 `VIDEO_JOB` fixture에서 research·video·captions를 진행하고 title/thumbnail user approval에서 `needs_user`로 멈춘 뒤 승인 후 다섯 단계 complete와 `next_action: none`을 확인했다.

## M4 exit evidence

- `M4-X1~X5`: 5개 synthetic engine 테스트와 실제 `validate_video_job` 결합, Core 137개·Extension 126개·maintenance 20개 artifact 회귀가 통과했다.
- external boundary는 `unavailable`, 사용자 승인 boundary는 `needs_user`로 남겼으며 브라우저·NotebookLM·보호 데이터는 실행하지 않았다.
