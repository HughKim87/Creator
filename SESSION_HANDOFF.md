# Agent Core Maintainer 현재 상태

- 목적: 새 세션이 Agent Core 남은 작업의 정확한 중단점부터 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤 어떤 작업보다 먼저.
- 책임: 작업 에이전트가 검증된 상태를 갱신하고 사용자가 승인 경계를 소유한다.
- 상태: 통합 설계에 최우선 선행 과제 `P0` 추가 완료. 규칙 변경안 보고·승인 대기.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: `AGENT_CORE_REMAINING_WORK_PLAN.md`.
- 활성 단계 설계: 없음.
- handoff mode: `same-workspace`.
- uncommitted dependency: `AGENT_CORE_REMAINING_WORK_PLAN.md`의 `P0` 추가와 이 핸드오프 갱신은 미커밋 상태다. 기존 검증 부산물은 단계 4의 오염 탐지·정리가 소유한다.

## 현재 목표

다른 모든 미완료 작업보다 먼저 `P0 — 규칙을 위한 규칙 개선`을 수행한다. 규칙을 반복 작업의 품질 재현과 Agent 간 작업 방법 공유를 위한 정본으로 재정의하고, 행동 제한은 명확한 위해를 막는 데 꼭 필요한 경우에만 둔다.

## 핵심 용어와 입력

- `Core`: `core/` submodule. `shared_data`: 일반 Host에는 선택, Maintainer에는 `v1`이 필요한 capability 후보.
- 활성 설계: `AGENT_CORE_REMAINING_WORK_PLAN.md`.
- 규칙 거버넌스 정본: `core/rules/rule-governance.md`.
- Core 정본: `core/docs/ARCHITECTURE.md`, `core/docs/COMPATIBILITY.md`, `core/docs/VERIFICATION.md`.
- 별도 유지: `extension/docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md`, `extension/reports/2026-08-01_GIT_HISTORY_SANITIZATION_FINAL_REPORT.md`.

## 현재 단계

- 단계: `P0-rule-governance-change-proposal-pending`.
- 기존 설계 5개의 유효 내용을 단일 전체 설계로 통합했고 완료된 contract v2 작업은 재실행 범위에서 제외했다.
- 사용자가 제시한 다섯 원칙을 `R0`과 `P0`의 목표·범위·게이트로 설계에 반영했다.
- `P0`, 구현 단계 0~4, 조건부 원격 단계는 미시작이다.
- 실제 규칙 변경 전에 정확한 대상·변경 문장·유지할 제한과 이유·검증 방법을 먼저 보고한다.

## 구현·검증 상태

- 완료: 순수 Core/Consumer 분리, contract v2, 이중-root 검사, Core 진입·상태 분리, Git 이력 정제.
- 설계 완료: `R0`과 최우선 `P0`를 통합 설계에 추가.
- 남음: `R0` 규칙 거버넌스 개선 뒤 `R1` L7, `R2` Python 3.10, `R3` capability, `R4` 승인 정본, `R5` local/remote, `R6` 무부작용.

## 직전 게이트

- `pass`: `P0`, `R0`, 다섯 설계 원칙, 후속 단계 차단 문구가 통합 설계에 존재함을 직접 확인.
- 과거 `pass`: 현재 checkout의 Core+Consumer 구조 verify, 위반 없음.
- `not_run`: 실제 규칙 변경과 그 검증, 기존 구현 단계의 회귀·clean-clone·실제 원격 검증.
- `fail — 과거 원격 게시`: Core 쓰기 인증이 없어 push가 거부됐다.

## 승인 상태

- 승인됨: 기존 설계 5개 통합·정리, `P0`를 최우선 과제로 추가, 사용자가 제시한 다섯 원칙의 설계 반영.
- 미승인: 실제 규칙 파일 수정, `P0` 밖의 설계 실행, 그 밖의 Core 변경, stage·commit, 외부 bundle, push·원격 조작, 태그·릴리스, 실제 Host 적용.
- 보호 경로 접근은 미승인이다.

## 차단

- `P0`의 정확한 규칙 변경안을 먼저 보고하고 승인받기 전에는 규칙 파일을 수정하지 않는다.
- `P0` 완료와 전체 설계 재대조 전에는 단계 0 이후 구현을 시작하지 않는다.
- 원격 게시에는 별도 승인과 Core 쓰기 인증이 필요하다.

## 실패 기록

| 목표 | 원인 | 연속 | 재시작 조건 |
|---|---|---:|---|
| 작업 규모에 비례하는 검증 | 규칙이 최소 작업 방법보다 전체 gate·clean clone 의무를 넓게 부과하고 Agent가 이를 기계적으로 확대 적용 | 2+ | `P0` 변경안 보고·승인 뒤 규칙 거버넌스와 영향 규칙 개선 |
| Core 완료 판정 | 검증 범위 불충분 | 1 | 통합 추적표·반사실 게이트 승인 |
| 완료 계획 | 단계 commit·remote·inventory 경계 불명확 | 1 | 통합 설계 승인·fingerprint 고정 |
| Core push | `Permission denied (publickey)` | 1 | 쓰기 인증과 push 별도 승인 |

## 알려진 위험

- Core가 원격에서 복구되지 않으면 첫 변경 전에 승인된 복구 지점이 필요하다.
- 현재 규칙의 일부 검증·Core 변경 조항은 새 다섯 원칙과 충돌할 수 있어 `P0` 감사 전에는 정당한 최종 규칙으로 간주하지 않는다.
- 로컬 clone은 실제 원격 사용성을 증명하지 않는다.
- 기존 검증 부산물은 오염 탐지기 적용 전에 삭제하지 않는다.
- 실제 Agent 의미·Host·원격 clone은 미검증이다.

## 첫 다음 행동

1. `core/rules/rule-governance.md`에 반영할 정확한 변경 문장과 유지할 제한의 이유를 작업 전에 사용자에게 보고한다.
2. 승인된 범위에서만 `P0`를 수행하고 `core/PROJECT_RULES.md`, `core/docs/VERIFICATION.md`, `core/rules/core-change-control.md`의 충돌 조항을 감사한다.
3. `P0` 결과에 따라 통합 설계를 다시 대조하고 승인받은 뒤에만 단계 0 진입을 준비한다.

## 다음 세션 시작 prompt

Core 정책, 소비 정책, 이 문서를 순서대로 읽는다. 보호 경로에 접근하지 않는다. 현재 최우선 과제는 `P0 — 규칙을 위한 규칙 개선`이다. 실제 규칙 수정 전에 정확한 변경안을 먼저 보고하고 승인받는다. `P0` 완료 전에는 단계 0, 그 밖의 Core 변경, commit, push를 시작하지 않는다.
