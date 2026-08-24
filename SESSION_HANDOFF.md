# Agent Core Maintainer 현재 상태

- 목적: 다음 세션이 검증된 단계와 첫 미완료 행동부터 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤.
- 책임: 작업 에이전트가 현재 단계만 갱신하고 사용자가 승인 경계를 소유한다.
- 상태: 단계 2 완료. 단계 3 진입 준비.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: `AGENT_CORE_REMAINING_WORK_PLAN.md`.
- 활성 단계 설계: 같은 문서 §9 `단계 3 — 검증기 신뢰성`.
- handoff mode: `same-workspace`.

## 현재 목표

단계 3에서 `R2·R5·R6`의 Runtime 판정, 테스트 inventory, local/remote scope, 검증 무부작용을 구현한다.

## 핵심 용어와 입력

- `Core`: `core/` submodule. 선택 기능: `shared_data v1`.
- 승인 정본 ID: `creator-video-creative-delegation-v1` in `PROJECT_RULES.md`.
- 단계 0 기준: Core `07d9bd1c`, 부모 `34349482`, 설계 SHA-256 `42D1E22EEDF7FBA483C7026FE63CC2F658F3670825B34D1E7C3B051ACA84EC17`.
- 외부 복구: `D:\AI Agent\Sandbox\Agent-Core-Maintainer-Recovery\core-07d9bd1c.bundle`, verify·복원 HEAD 일치.

## 현재 단계

- 완료: `P0`, 단계 0, 단계 1.
- 단계 1 commit: Core `210aeea`, 부모 `08dbc12`.
- 단계 2 완료:
  - contract v2 선택 key `required_core_capabilities`와 Consumer capability 판정 추가.
  - Maintainer가 `{"shared_data": 1}`을 요구하고 key 없는 Host는 호환 유지.
  - Creator 정책에 승인 정본 ID를 추가하고 두 스킬·두 참고문서의 독자 trigger·권위 문구 제거.
  - `extension/tests/fixtures/creative-delegation-v1.json`과 정적 계약 검사 추가.
- 단계 2 Core commit: `e1c7c63`. 부모 gitlink·정책·스킬·fixture·handoff는 현재 단계 커밋 대상이다.

## 구현·검증 상태

- 완료: `R0`, `R1`, `R3`, `R4`, 단계 1 범위의 `R2` Python 3.10 호환.
- 단계 1: Python 3.10.20 설치·완전 부재 gate 통과, 부분 결손은 `preflight-contract` 실패, 필수 107·선택 65 테스트 통과.
- 단계 2: Consumer capability 11개, Creator 승인·기존 패키지 관련 21개 테스트 통과.

## 직전 게이트

- `pass`: Core+Consumer gate. Core 검사 12종, Consumer 검사 8종, startup context 10,279/20,000자, 양쪽 무부작용.

## 승인 상태

- 승인됨: 전체 설계 단계 0~4 권장안, 단계별 Core·부모 commit.
- 미승인: 추가 push·원격 조작, 태그·릴리스, 실제 Host 적용, 보호 경로 접근.

## 차단

- 원격 검증은 Core SSH key 부재로 불가하며 조건부 원격 단계는 별도 push 승인 대상이다.

## 실패 기록

| 목표 | 원인 | 연속 | 재시작 조건 |
|---|---|---:|---|
| 비례 검증 | 전체 gate·clean clone의 일률 적용 | 2+ | `P0` 완료, 단계별 관련 검사만 선택 |
| Stage 2 Consumer gate | handoff 예산·과거 판정 누적 | 1 | 축약 후 재실행 통과, 종료 |
| Core 원격 읽기 | SSH public key 부재 | 1 | 승인된 key 또는 사용자의 외부 확인 |

## 알려진 위험

- Creator 승인 fixture는 정적 계약이며 실제 Agent 자연어 재현은 아니다.
- 단계 3의 Runtime inventory·local/remote scope·작업 트리 무부작용 구현은 미시작이다.

## 첫 다음 행동

1. 단계 3의 현재 검증 entry와 실행 스크립트를 조사한다.
2. Runtime·inventory·scope·작업 트리 비교의 직접 관련 구현과 결함 주입 검사를 수정한다.
3. 단계 3 gate와 commit 뒤 §10 단계 4로 전환한다.

## 다음 세션 시작 prompt

시작 3문서를 읽고 보호 경로에 접근하지 않는다. 단계 2까지 완료됐고 활성 단계는 통합 설계 §9 단계 3이다. 검증 entry의 Runtime·inventory·scope·무부작용 표면만 조사한다. push는 하지 않는다.
