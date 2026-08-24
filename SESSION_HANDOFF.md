# Creator 영상 Host 현재 상태

- 목적: 다음 세션이 영상 제작 Host의 현재 단계와 첫 미완료 행동부터 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤.
- 책임: 작업 에이전트가 현재 단계만 갱신하고 사용자가 영상 결과와 승인 경계를 소유한다.
- 상태: 저장소 역할 분리 단계 5 차단. Creator 작업공간 사용 중.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: `REPOSITORY_ROLE_SEPARATION_DESIGN.md`.
- 활성 단계 설계: `REPOSITORY_ROLE_SEPARATION_STAGE_5.md`.
- handoff mode: `same-workspace`.
- uncommitted dependency: 단계 5 설계 route와 현재 핸드오프 갱신.

## 현재 목표

현재 작업공간 잠금이 해제된 뒤 검증된 Creator와 Maintainer를 최종 로컬 폴더 이름으로 전환한다.

## 핵심 용어와 입력

- `Core`: `core/`의 읽기 전용 submodule.
- `Extension`: 영상·YouTube·게임 도메인 구현과 계약.
- `Skills`: 실제 도구 사용 절차.
- 보호 경로: `inputs`, `outputs`, `extension/inputs`, `extension/outputs`.
- 분리 설계 fingerprint: `B1B6BA4E2239F9C1D6959792C838251C9AFF328100AD64A9F5BC23AE8A5DC146`.

## 현재 단계

- 단계 0~2: 분리표와 독립 Maintainer 구성·재현성 완료.
- 단계 3: Host 소비 계약·Creator gate 전환과 Maintainer 실행기 제거 완료.
- 단계 4: `pass`; Core 연결·역할·상호 의존·최종 Host gate 확인.
- 단계 5: `blocked`; Creator source 이동이 활성 작업공간 사용으로 거부됨.
- 단계 6: `not_run`.

## 구현·검증 상태

- Host 정책·README·dependency·검증기 전환과 관련 회귀 통과.
- Maintainer 전용 clean-clone 실행기와 운영 참조 제거 완료.
- 실제 영상 사용 검증: 사용자 운영 대상, 자동 gate 아님.

## 직전 게이트

- `fail`: Windows가 사용 중인 Creator source 폴더의 첫 이동을 거부함.

## 승인 상태

- 승인됨: 전체 로컬 단계의 권장 구현·단계별 local commit·승인된 정확한 파일 정리·폴더 전환.
- 미승인: 원격 생성·push, main·태그·릴리스, 보호 경로 접근.

## 차단

- 현재 Codex 작업이 Creator source를 사용 중이다. 이 작업을 종료해 폴더 handle이 해제되어야 한다.
- 잘못 중첩된 Maintainer 후보는 원래 임시 경로로 복구됐고 두 저장소는 clean이다.

## 실패 기록

| 목표 | 원인 | 연속 | 재시작 조건 |
|---|---|---:|---|
| Maintainer clean clone | Git helper PATH와 handoff 문자열 판정 | 0 | consumer verify 선행 후 재실행 통과 |
| 단계 5 폴더 전환 | 활성 작업공간 lock, 첫 이동 오류가 비종료 처리됨 | 1 | 현재 작업 종료 후 `-ErrorAction Stop`으로 첫 이동 성공 시에만 두 번째 이동 |

## 알려진 위험

- 실제 영상 사용성은 자동 검사로 판정하지 않으며 사용자가 운영 중 확인한다.
- 현재 로컬 폴더 이름은 아직 이전 Maintainer 이름이며 단계 5에서 전환한다.

## 첫 다음 행동

1. 사용자가 현재 Creator 작업공간을 사용하는 Codex 작업·프로세스를 종료한다.
2. 부모 PowerShell에서 단계 5 표의 첫 이동을 `-ErrorAction Stop`으로 실행한다.
3. 첫 이동 성공 시에만 두 번째 이동을 실행하고 새 경로의 Git 상태를 대조한다.

## 다음 세션 시작 prompt

시작 3문서, 전체 설계, `REPOSITORY_ROLE_SEPARATION_STAGE_5.md`를 읽고 보호 경로에 접근하지 않는다. 현재 작업공간 lock 해제 전에는 폴더 이동을 재시도하지 않고 원격 작업도 시작하지 않는다.
