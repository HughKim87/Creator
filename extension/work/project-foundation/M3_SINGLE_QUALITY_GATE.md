# M3 단일 품질 gate 설계

- 문서 역할: `phase-design`
- 단계 ID: `M3`
- lifecycle: `planned`
- 목적: 사람이 명령을 기억하지 않아도 비보호 결정론적 품질 검사가 같은 진입점에서 실행되게 한다.
- 상위 설계: [재현 가능한 프로젝트 기반 전체 설계](../PROJECT_FOUNDATION_DESIGN.md)
- 현재 상태: [세션 핸드오프](../../../SESSION_HANDOFF.md)

## 단계 결과

local과 승인된 CI가 같은 single verify를 사용해 Core·Extension·Node·maintenance·clean-clone Q0~Q3을 검증한다.

## Entry gate

- `M3-E1`: M2 exit gate 전건 통과
- `M3-E2`: bootstrap과 dependency 계약이 clean clone에서 재현됨
- `M3-E3`: CI·hook·외부 변경은 exact 사용자 승인 확보

## 포함 범위

- single verify owner와 exit code
- Python Core·Extension·Node·maintenance 집계
- arbitrary-path clean-clone conformance
- setup·contract·test·external failure 분류
- local·CI 동일 진입점

## 제외 범위

- 보호 데이터 내용 검사
- browser·NotebookLM·유료 서비스 실행
- 실제 사용자 승인 자동화
- 영상 workflow runner

## Execution slices와 slice gate

### M3-S1 — verify composition

현재 독립 명령을 한 진입점에서 순서·결과·복구 행동과 함께 집계한다.

Gate `M3-S1-G`: 누락된 suite가 없고 미실행을 pass로 표시하지 않는다.

### M3-S2 — failure taxonomy

환경 준비, 계약 drift, test 결함, 외부 capability를 구분한다.

Gate `M3-S2-G`: 실패 결과만으로 다음 복구 행동을 선택할 수 있다.

### M3-S3 — clean-clone gate

새 tracked checkout에서 bootstrap부터 verify까지 합성 경로로 실행한다.

Gate `M3-S3-G`: ASCII·한글·공백 경로가 같은 결과를 낸다.

### M3-S4 — local·CI parity

승인된 경우 CI가 local과 같은 명령을 실행하고 보호·외부 gate는 제외한다.

Gate `M3-S4-G`: CI가 보호 경로·계정·유료 작업을 읽거나 실행하지 않는다.

## Exit gate

- `M3-X1`: clean checkout에서 한 명령으로 Q0~Q3 결과 재현
- `M3-X2`: Python·Node·maintenance·manifest·clone gate 누락 0
- `M3-X3`: setup·contract·test·external failure 구분
- `M3-X4`: local·CI 명령 parity
- `M3-X5`: 보호·외부 작업 실행 0

## 중단·복구 조건

- CI 부재나 외부 capability 부재를 성공으로 처리하면 중단한다.
- single verify가 대형 선택 dependency를 기본 설치하면 분리한다.
- local과 CI가 다른 명령을 사용하면 owner를 하나로 복구한다.

## Transition gate

verify 시간, 실패 원인 해석 시간, 수동 명령 수를 baseline과 비교한다. 운영 비용이 더 커지면 M4 전에 실행 범위를 축소한다.

## 첫 활성화 행동

M1 bootstrap과 현재 검증 명령 목록을 기준으로 single verify의 입력·출력·failure taxonomy를 설계한다.
