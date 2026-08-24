# Agent Core Maintainer 현재 상태

- 목적: 새 세션이 Agent Core 남은 작업의 정확한 중단점부터 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤 어떤 작업보다 먼저.
- 책임: 작업 에이전트가 검증된 상태를 갱신하고 사용자가 승인 경계를 소유한다.
- 상태: 설계 통합 완료. 새 전체 설계 승인 대기.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: `AGENT_CORE_REMAINING_WORK_PLAN.md`.
- 활성 단계 설계: 없음.
- handoff mode: `same-workspace`.
- uncommitted dependency: 기존 검증 부산물은 단계 4의 오염 탐지·정리가 소유한다.

## 현재 목표

통합 설계 승인 뒤 단계별 후보 commit과 clean-clone 검증으로 필수 결함 `R1`~`R6`을 완료한다. 로컬·원격·실제 Host·범용 Host 검증을 서로 다른 수준으로 유지한다.

## 핵심 용어와 입력

- `Core`: `core/` submodule. `shared_data`: 일반 Host에는 선택, Maintainer에는 `v1`이 필요한 capability 후보.
- 활성 설계: `AGENT_CORE_REMAINING_WORK_PLAN.md`.
- Core 정본: `core/docs/ARCHITECTURE.md`, `core/docs/COMPATIBILITY.md`, `core/docs/VERIFICATION.md`.
- 별도 유지: `extension/docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md`, `extension/reports/2026-08-01_GIT_HISTORY_SANITIZATION_FINAL_REPORT.md`.

## 현재 단계

- 단계: `consolidated-plan-awaiting-approval`.
- 기존 설계 5개의 유효 내용을 단일 전체 설계로 통합했고 완료된 contract v2 작업은 재실행 범위에서 제외했다.
- 구현 단계 0~4와 조건부 원격 단계는 미시작이다.
- 통합 설계의 필수 범위·고정 결정·정상/실패/경계 게이트를 승인받기 전에는 단계 0을 시작하지 않는다.

## 구현·검증 상태

- 완료: 순수 Core/Consumer 분리, contract v2, 이중-root 검사, Core 진입·상태 분리, Git 이력 정제.
- 남음: `R1` L7, `R2` Python 3.10, `R3` capability, `R4` 승인 정본, `R5` local/remote, `R6` 무부작용.

## 직전 게이트

- `pass`: 현재 checkout의 Core+Consumer 구조 verify, 위반 없음.
- `not_run`: 새 설계의 구현·회귀·clean-clone·실제 원격 검증.
- `fail — 과거 원격 게시`: Core 쓰기 인증이 없어 push가 거부됐다.

## 승인 상태

- 승인됨: 기존 설계 5개를 새 단일 설계로 통합하고 활성 트리에서 제거.
- 미승인: 새 설계 실행, Core 변경, stage·commit, 외부 bundle, push·원격 조작, 태그·릴리스, 실제 Host 적용.
- 보호 경로 접근은 미승인이다.

## 차단

- 구현은 설계 승인·fingerprint 기록·단계 0/1 설계·정확한 Core 변경과 commit 위임 전까지 시작할 수 없다.
- 원격 게시에는 별도 승인과 Core 쓰기 인증이 필요하다.

## 실패 기록

| 목표 | 원인 | 연속 | 재시작 조건 |
|---|---|---:|---|
| Core 완료 판정 | 검증 범위 불충분 | 1 | 통합 추적표·반사실 게이트 승인 |
| 완료 계획 | 단계 commit·remote·inventory 경계 불명확 | 1 | 통합 설계 승인·fingerprint 고정 |
| Core push | `Permission denied (publickey)` | 1 | 쓰기 인증과 push 별도 승인 |

## 알려진 위험

- Core가 원격에서 복구되지 않으면 첫 변경 전에 승인된 복구 지점이 필요하다.
- 로컬 clone은 실제 원격 사용성을 증명하지 않는다.
- 기존 검증 부산물은 오염 탐지기 적용 전에 삭제하지 않는다.
- 실제 Agent 의미·Host·원격 clone은 미검증이다.

## 첫 다음 행동

1. `AGENT_CORE_REMAINING_WORK_PLAN.md`를 실행 설계로 승인할지 결정한다.
2. 승인 시 fingerprint와 단계 0의 정확한 복구 경로·명령·판정 조건을 기록한다.
3. 단계 1의 정확한 Core 변경과 commit 위임 뒤에만 구현한다.

## 다음 세션 시작 prompt

Core 정책, 소비 정책, 이 문서를 순서대로 읽는다. 보호 경로에 접근하지 말고 통합 설계 승인 상태부터 확인한다. 승인 전에는 단계 0, Core 변경, commit, push를 시작하지 않는다.
