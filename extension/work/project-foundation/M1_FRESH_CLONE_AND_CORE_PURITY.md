# M1 Fresh Clone·Core 순수성 설계

- 문서 역할: `phase-design`
- 단계 ID: `M1`
- lifecycle: `draft`
- 목적: 임의 경로의 tracked clone에서 기반 검증을 재현하고 Core의 domain 역의존을 제거한다.
- 상위 설계: [재현 가능한 프로젝트 기반 전체 설계](../PROJECT_FOUNDATION_DESIGN.md)
- 현재 상태: [세션 핸드오프](../../../SESSION_HANDOFF.md)

## 단계 결과

새 컴퓨터의 ASCII·한글·공백 경로에서 bootstrap 후 Q0~Q3이 통과하고, Core가 현재 YouTube 프로젝트의 identity와 artifact owner를 직접 소유하지 않는다.

## Entry gate

- `M1-E1`: M0 exit gate 전건 통과
- `M1-E2`: 지원 runtime·dependency·Q0~Q3 정의 승인
- `M1-E3`: exact `core/**` 변경 경로·이유·검증에 대한 현재 대화의 사용자 승인
- `M1-E4`: 설치·CI·hook이 필요하면 각각 별도 승인

## 포함 범위

- Python·Node runtime 및 dependency 계약
- bootstrap·single verify 진입점 설계
- arbitrary-path source-root 안전 판정
- project-neutral schema namespace와 compatibility
- neutral storage interface
- Extension-owned artifact registry
- 빈 Extension과 clean-clone conformance

## 제외 범위

- 보호 데이터·외부 계정·브라우저 실행
- 실제 영상 의미 품질
- M2 작업 phase contract와 M3 이후 자동화
- 게임 extension 구현

## Execution slices와 slice gate

### M1-S1 — 환경 계약

runtime 버전, 필수·선택 dependency, bootstrap preflight를 고정한다.

Gate `M1-S1-G`: host 전역 package 없이 필요한 행동과 외부 capability 상태가 구분된다.

### M1-S2 — arbitrary-path 안전

repository identity와 isolated fixture를 구분하도록 source-root 판정과 회귀를 수정한다.

Gate `M1-S2-G`: 현재 workspace와 임의 경로 clone에서 Core 회귀가 통과하고 실제 repository root 쓰기는 계속 거부된다.

### M1-S3 — namespace·storage

project URN을 중립화하고 storage convention 또는 injection owner를 확정한다.

Gate `M1-S3-G`: 승인된 compatibility alias 외 Core project identity가 0이고 기존 artifact 의미가 유지된다.

### M1-S4 — artifact registry 방향

YouTube artifact 직접 목록을 Core에서 제거하고 Extension-owned 등록 interface로 이전한다.

Gate `M1-S4-G`: Core가 YouTube path·owner를 알지 않으며 Extension drift 검증과 빈 Extension conformance가 통과한다.

### M1-S5 — clone conformance

ASCII·한글·공백 경로에서 bootstrap과 Q0~Q3을 같은 진입점으로 검증한다.

Gate `M1-S5-G`: clean checkout에서 환경·계약·test·external failure가 구분된다.

## Exit gate

- `M1-X1`: 임의 경로 clone의 bootstrap·Q0~Q3 전건 통과
- `M1-X2`: Core code·schema의 project·YouTube identity 0 또는 승인된 compatibility alias만 존재
- `M1-X3`: Core의 Extension artifact 직접 열거 0
- `M1-X4`: 현재 영상 Extension 회귀 유지
- `M1-X5`: 보호·외부 capability를 deterministic 성공으로 오인하지 않음

## 중단·복구 조건

- schema migration이 기존 데이터를 파괴하거나 자동 변환을 요구하면 중단한다.
- dependency가 사용하지 않는 대형 runtime을 필수 설치하면 설계를 축소한다.
- Core 순수성 개선이 Extension 검증 제거로 바뀌면 중단한다.
- 같은 objective가 세 번 연속 실패하면 handoff에 원인·횟수·재시작 조건을 남긴다.

## Transition gate

clone-to-green 시간, 사용자 행동 수, 추가 설정·script·test 수, 잔여 domain leakage를 재평가한다. M2가 여전히 최소 다음 단계일 때만 활성화한다.

## 첫 활성화 행동

M0 결정표를 읽고 M1-S1의 exact root·Core·Extension 변경 경로와 이유를 산출한다. Core 변경은 현재 대화에서 exact 범위가 승인되기 전까지 실행하지 않는다.
