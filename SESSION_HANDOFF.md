# Agent Core Maintainer 현재 상태

- 목적: 다음 세션이 검증된 단계와 첫 미완료 행동부터 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤.
- 책임: 작업 에이전트가 현재 단계만 갱신하고 사용자가 승인 경계를 소유한다.
- 상태: 원격 사용 검증 완료. 실제 Host 검증 대상 대기.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: `AGENT_CORE_REMAINING_WORK_PLAN.md`.
- 활성 단계 설계: 없음.
- handoff mode: `same-workspace`.
- uncommitted dependency: 없음.

## 현재 목표

게시된 Core·Maintainer 후보를 첫 실제 Host에 적용해 Codex·Claude 재개를 검증한다.

## 핵심 용어와 입력

- `Core`: `core/` submodule. 선택 기능: `shared_data v1`.
- 승인 정본 ID: `creator-video-creative-delegation-v1` in `PROJECT_RULES.md`.
- 단계 0 기준: Core `07d9bd1c`, 부모 `34349482`, 설계 SHA-256 `42D1E22EEDF7FBA483C7026FE63CC2F658F3670825B34D1E7C3B051ACA84EC17`.
- 외부 복구: `D:\AI Agent\Sandbox\Agent-Core-Maintainer-Recovery\core-07d9bd1c.bundle`, verify·복원 HEAD 일치.

## 현재 단계

- 완료: `P0`, 단계 0~4.
- 단계 1 commit: Core `210aeea`, 부모 `08dbc12`.
- 단계 2 완료:
  - 선택 capability 계약과 Creator 승인 정본·정적 계약 검사를 추가하고 기존 Host 호환을 유지했다.
- 단계 2 commit: Core `e1c7c63`, 부모 `dd900fb`.
- 단계 3: `scripts/run_test_inventory.py`를 추가하고 Runtime·inventory·긴 stdout·local/remote scope·보호 경로 선제 제외·작업 트리 무부작용을 구현했다.
- 종료 개선: clone 임시 루트 Node 사전 확인과 bootstrap 실패 뒤 의존 verify 조기 중단을 추가했다.
- 단계 3 commit: 부모 `2f17b8f`.
- 단계 4 오염 탐지: `.tmp`는 비어 있고 `extension/work`에는 추적용 `.gitkeep`만 있어 삭제 대상이 없다.
- 단계 4 후보 commit: 부모 `b9d07bb`, Core gitlink `e1c7c63`.
- 원격 단계: Core `codex/legacy-rule-absorption`과 Maintainer `codex/agent-core-integration` 게시·도달성 확인, 실제 원격 재귀 clone 통과.

## 구현·검증 상태

- 완료: `R0`~`R5`, `R6`의 검증 전후 오염 탐지.
- 단계 1: Python 3.10.20 설치·완전 부재 gate 통과, 부분 결손은 `preflight-contract` 실패, 필수 107·선택 65 테스트 통과.
- 단계 3: Python 3.10.20 Core 112·선택 65, Python 3.12.13 Extension 152 테스트 통과. inventory 누락·예외·skip 0.
- 단계 4: ASCII·한글·공백 경로 commit snapshot clean clone과 각 복제본 전체 gate 통과, 원본·복제본 작업 트리 무오염.
- 원격 clean clone: 부모 `5255009`, Core `e1c7c63`, Core 112·선택 65·Extension 156, 작업 트리 무오염 통과.

## 직전 게이트

- `pass`: Host 읽기 전용 Deploy Key를 사용한 실제 원격 `clone --recurse-submodules`와 clone 내부 통합 gate.

## 승인 상태

- 승인됨: 전체 설계 단계 0~4, Core·Maintainer 후보 push와 원격 검증.
- 보류: main 반영·태그·릴리스는 실제 Host 검증 결과 보고 뒤 결정.
- 미승인: 보호 경로 접근.

## 차단

- 첫 실제 Host 저장소가 현재 작업공간에 지정되어 있지 않다.

## 실패 기록

| 목표 | 원인 | 연속 | 재시작 조건 |
|---|---|---:|---|
| 비례 검증 | 전체 gate·clean clone의 일률 적용 | 2+ | `P0` 완료, 단계별 관련 검사만 선택 |
| Stage 2 Consumer gate | handoff 예산·과거 판정 누적 | 1 | 축약 후 재실행 통과, 종료 |

## 알려진 위험

- Creator 승인 fixture는 정적 계약이며 실제 Agent 자연어 재현은 아니다.
- 실제 Host와 서로 다른 두 번째 Host의 Codex·Claude 재개는 미검증이다.

## 첫 다음 행동

1. 첫 실제 Host 저장소가 지정되면 `consumer_role: host` 계약과 진입 파일을 구성한다.
2. Host 읽기 전용 Core 연결과 통합 gate를 실행한다.
3. Codex·Claude 새 세션 재개를 검증한 뒤 두 번째 Host로 전환한다.

## 다음 세션 시작 prompt

시작 3문서를 읽고 보호 경로에 접근하지 않는다. 로컬·원격 사용 검증은 완료됐으며 다음은 통합 설계 §12의 첫 실제 Host 검증이다. 대상 Host가 없으면 임의 프로젝트를 만들지 말고 정확한 대상부터 확인한다.
