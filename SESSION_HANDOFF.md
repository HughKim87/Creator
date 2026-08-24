# Agent Core Maintainer 현재 상태

- 목적: 새 세션이 Agent Core 남은 작업의 정확한 중단점부터 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤 어떤 작업보다 먼저.
- 책임: 작업 에이전트가 검증된 상태를 갱신하고 사용자가 승인 경계를 소유한다.
- 상태: 단계 1 완료. 단계 2 진입 준비.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: `AGENT_CORE_REMAINING_WORK_PLAN.md`.
- 활성 단계 설계: `AGENT_CORE_REMAINING_WORK_PLAN.md` §8 `단계 2 — Consumer capability와 승인 정책`.
- handoff mode: `same-workspace`.
- uncommitted dependency: 단계 1 Core commit은 `210aeea`이며 부모 Core gitlink와 이 핸드오프 갱신은 현재 단계 커밋 대상이다. 기존 검증 부산물은 단계 4의 오염 탐지·정리가 소유한다.

## 현재 목표

단계 2에서 `R3` Consumer capability와 `R4` 사용자 승인 정본을 구현한다. 일반 Host의 기존 계약은 유지하면서 Maintainer의 `shared_data v1` 요구와 Creator 승인 규칙의 단일 정본을 검증한다.

## 핵심 용어와 입력

- `Core`: `core/` submodule. `shared_data`: 일반 Host에는 선택, Maintainer에는 `v1`이 필요한 capability 후보.
- 활성 설계: `AGENT_CORE_REMAINING_WORK_PLAN.md`.
- 규칙 거버넌스 정본: `core/rules/rule-governance.md`.
- Core 정본: `core/docs/ARCHITECTURE.md`, `core/docs/COMPATIBILITY.md`, `core/docs/VERIFICATION.md`.
- 별도 유지: `extension/docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md`, `extension/reports/2026-08-01_GIT_HISTORY_SANITIZATION_FINAL_REPORT.md`.

## 현재 단계

- 단계: `stage-2-entry-ready`.
- 기존 설계 5개의 유효 내용을 단일 전체 설계로 통합했고 완료된 contract v2 작업은 재실행 범위에서 제외했다.
- 사용자가 제시한 다섯 원칙을 `R0`과 `P0`의 목표·범위·게이트로 설계에 반영했다.
- 사용자가 구현된 `P0`와 갱신된 전체 설계의 권장안 실행을 확인했다.
- 단계 0에서 기준 Core HEAD `07d9bd1c675474b4ad42377bbc65082fd45022da`, 부모 HEAD `34349482cc7f845919470c44190d41ca86b4e116`, 설계 fingerprint `42D1E22EEDF7FBA483C7026FE63CC2F658F3670825B34D1E7C3B051ACA84EC17`을 고정했다.
- Core 원격은 SSH 키 부재로 읽기 검증이 불가능해 `D:\AI Agent\Sandbox\Agent-Core-Maintainer-Recovery\core-07d9bd1c.bundle`을 만들고 복원 clone의 HEAD 일치를 확인했다.
- 단계 1에서 L7 설치 상태를 완전 설치·완전 부재·부분 결손으로 구분하고 선택 테스트를 L7 내부로 이동했다.
- `datetime.UTC`를 Python 3.10 호환 표현으로 교체했다.
- 단계 2~4와 조건부 원격 단계는 미시작이다.
- 최초 보고한 규칙 정본 4개를 수정했고, 감사에서 추가 충돌이 확인된 `core/rules/version-control.md`, `core/rules/staged-work-design.md`는 별도 사전 보고 뒤 수정했다.

## 구현·검증 상태

- 완료: 순수 Core/Consumer 분리, contract v2, 이중-root 검사, Core 진입·상태 분리, Git 이력 정제.
- 완료: `R0`, 단계 0, `R1` L7 격리, `R2`의 Python 3.10 호환 구현과 단계 1 실제 Runtime gate.
- 남음: 단계 3의 `R2` Runtime 판정 강화, `R3` capability, `R4` 승인 정본, `R5` local/remote, `R6` 무부작용.

## 직전 게이트

- `pass`: `P0`, `R0`, 다섯 설계 원칙, 후속 단계 차단 문구가 통합 설계에 존재함을 직접 확인.
- `pass`: 수정 파일 8개의 존재, NUL 부재, 필수 문서 메타데이터, 로컬 Markdown 링크, 품질 재현·Agent 자유도·최소 제한·선택 gate·조건부 clean clone 원칙을 정적으로 확인.
- `pass`: 외부 Core bundle verify와 임시 복원 clone의 기준 HEAD 일치.
- `pass`: Python 3.10.20에서 설치 상태 Core gate, 필수 테스트 107개, 선택 테스트 65개.
- `pass`: 임시 실제 트리에서 L7 완전 부재 Core gate와 부분 결손 `preflight-contract` 실패.
- 과거 `pass`: 현재 checkout의 Core+Consumer 구조 verify, 위반 없음.
- `not_run`: 실제 규칙 변경과 그 검증, 기존 구현 단계의 회귀·clean-clone·실제 원격 검증.
- `fail — 과거 원격 게시`: Core 쓰기 인증이 없어 push가 거부됐다.

## 승인 상태

- 승인됨: 기존 설계 통합·정리, `P0` 구현과 확인, 단계 0~4 권장안 실행, 단계별 Core·부모 commit, 단계 0 외부 복구 bundle.
- 미승인: 추가 push·원격 조작, 태그·릴리스, 실제 Host 적용.
- 보호 경로 접근은 미승인이다.

## 차단

- 원격 게시에는 별도 승인과 Core 쓰기 인증이 필요하다.

## 실패 기록

| 목표 | 원인 | 연속 | 재시작 조건 |
|---|---|---:|---|
| 작업 규모에 비례하는 검증 | 규칙이 최소 작업 방법보다 전체 gate·clean clone 의무를 넓게 부과하고 Agent가 이를 기계적으로 확대 적용 | 2+ | `P0` 완료. 후속 단계에서 변경 영향에 맞는 검사만 선택해 재발 여부 확인 |
| Core 완료 판정 | 검증 범위 불충분 | 1 | 통합 추적표·반사실 게이트 승인 |
| 완료 계획 | 단계 commit·remote·inventory 경계 불명확 | 1 | 통합 설계 승인·fingerprint 고정 |
| Core push | `Permission denied (publickey)` | 1 | 쓰기 인증과 push 별도 승인 |

## 알려진 위험

- Core가 원격에서 복구되지 않으면 첫 변경 전에 승인된 복구 지점이 필요하다.
- `P0`는 정적 문서 확인 단계이며 서로 다른 Agent의 실제 반복 작업에서 품질과 자유도가 함께 유지되는지는 아직 미검증이다.
- 로컬 clone은 실제 원격 사용성을 증명하지 않는다.
- 기존 검증 부산물은 오염 탐지기 적용 전에 삭제하지 않는다.
- 실제 Agent 의미·Host·원격 clone은 미검증이다.

## 첫 다음 행동

1. Consumer 계약 parser·schema와 Maintainer 계약 선언을 조사한다.
2. Creator 승인 정본과 `coordinate-video-production`, `youtube-title-thumbnail`의 현재 위임 문구를 대조한다.
3. `R3`, `R4`의 직접 관련 구현·fixture를 수정하고 관련 gate 뒤 단계 2 commit을 만든다.

## 다음 세션 시작 prompt

Core 정책, 소비 정책, 이 문서를 순서대로 읽는다. 보호 경로에 접근하지 않는다. 단계 1까지 완료됐고 활성 단계는 통합 설계 §8의 단계 2다. Consumer capability와 Creator 승인 단일 정본의 현재 표면을 조사한다. 단계별 commit은 승인됐지만 push는 별도 승인 전까지 하지 않는다.
