# Agent Core Maintainer 현재 상태

- 목적: 다음 세션이 검증된 단계와 첫 미완료 행동부터 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤.
- 책임: 작업 에이전트가 현재 단계만 갱신하고 사용자가 승인 경계를 소유한다.
- 상태: 단계 3 완료. 단계 4 로컬 마감 진입 준비.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: `AGENT_CORE_REMAINING_WORK_PLAN.md`.
- 활성 단계 설계: 없음.
- handoff mode: `same-workspace`.
- uncommitted dependency: 단계 3 검증기 변경과 현재 핸드오프 갱신이 작업 트리에 있다.

## 현재 목표

단계 4에서 단계 0~3 후보를 로컬 완료 상태로 통합 확인하고 정확한 기존 검증 부산물만 정리한다.

## 핵심 용어와 입력

- `Core`: `core/` submodule. 선택 기능: `shared_data v1`.
- 승인 정본 ID: `creator-video-creative-delegation-v1` in `PROJECT_RULES.md`.
- 단계 0 기준: Core `07d9bd1c`, 부모 `34349482`, 설계 SHA-256 `42D1E22EEDF7FBA483C7026FE63CC2F658F3670825B34D1E7C3B051ACA84EC17`.
- 외부 복구: `D:\AI Agent\Sandbox\Agent-Core-Maintainer-Recovery\core-07d9bd1c.bundle`, verify·복원 HEAD 일치.

## 현재 단계

- 완료: `P0`, 단계 0~3.
- 단계 1 commit: Core `210aeea`, 부모 `08dbc12`.
- 단계 2 완료:
  - contract v2 선택 key `required_core_capabilities`와 Consumer capability 판정 추가.
  - Maintainer가 `{"shared_data": 1}`을 요구하고 key 없는 Host는 호환 유지.
  - Creator 정책에 승인 정본 ID를 추가하고 두 스킬·두 참고문서의 독자 trigger·권위 문구 제거.
  - `extension/tests/fixtures/creative-delegation-v1.json`과 정적 계약 검사 추가.
- 단계 2 commit: Core `e1c7c63`, 부모 `dd900fb`.
- 단계 3: `scripts/run_test_inventory.py`를 추가하고 Runtime·inventory·긴 stdout·local/remote scope·보호 경로 선제 제외·작업 트리 무부작용을 구현했다. 변경은 현재 부모 커밋 대상이다.

## 구현·검증 상태

- 완료: `R0`~`R5`, `R6`의 검증 전후 오염 탐지.
- 단계 1: Python 3.10.20 설치·완전 부재 gate 통과, 부분 결손은 `preflight-contract` 실패, 필수 107·선택 65 테스트 통과.
- 단계 3: Python 3.10.20 Core 112·선택 65, Python 3.12.13 Extension 152 테스트 통과. inventory 누락·예외·skip 0.

## 직전 게이트

- `pass`: `scripts/verify.py --no-clone`. Runtime·Core+Consumer·inventory·maintenance·작업 트리 무부작용 통과, local/remote 미실행 scope 분리.

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
- 실제 원격과 실제 Host는 미검증이며 별도 승인 대상이다.

## 첫 다음 행동

1. 단계 3 변경을 부모 commit으로 만든다.
2. 단계 4에서 기존 검증 부산물의 정확한 경로와 생성 패턴을 측정해 삭제 대상을 보고한다.
3. 승인된 대상 정리 뒤 최종 후보 local clone conformance를 실행한다.

## 다음 세션 시작 prompt

시작 3문서를 읽고 보호 경로에 접근하지 않는다. 단계 3까지 완료됐고 다음은 통합 설계 §10 단계 4다. 기존 검증 부산물은 정확한 경로를 보고한 뒤 정리하고 최종 local clone conformance를 실행한다. push는 하지 않는다.
