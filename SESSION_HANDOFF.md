# Creator 영상 Host 현재 상태

- 목적: 다음 세션이 영상 제작 Host의 현재 단계와 첫 미완료 행동부터 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤.
- 책임: 작업 에이전트가 현재 단계만 갱신하고 사용자가 영상 결과와 승인 경계를 소유한다.
- 상태: 저장소 역할 분리 단계 3 Creator Host 전환 중.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: `REPOSITORY_ROLE_SEPARATION_DESIGN.md`.
- 활성 단계 설계: `REPOSITORY_ROLE_SEPARATION_STAGE_3.md`.
- handoff mode: `same-workspace`.
- uncommitted dependency: 분리 설계와 Host 계약·개요·검증기 변경.

## 현재 목표

현재 저장소를 Core 읽기 전용 영상 제작 Host로 전환하고 Maintainer 책임을 독립 저장소에만 남긴다.

## 핵심 용어와 입력

- `Core`: `core/`의 읽기 전용 submodule.
- `Extension`: 영상·YouTube·게임 도메인 구현과 계약.
- `Skills`: 실제 도구 사용 절차.
- 보호 경로: `inputs`, `outputs`, `extension/inputs`, `extension/outputs`.

## 현재 단계

- 단계 0~2: 분리표와 독립 Maintainer 구성·재현성 완료.
- 단계 3: Host 소비 계약·Creator gate 전환 중.
- 단계 4 이후: `not_run`.

## 구현·검증 상태

- Host 정책·README·dependency·검증기 전환과 관련 회귀 통과.
- Maintainer 전용 clean-clone 실행기 제거 전.
- 실제 영상 사용 검증: 사용자 운영 대상, 자동 gate 아님.

## 직전 게이트

- `pass`: Host consumer 계약, Creator inventory 152건, artifact·Node·작업 트리 무부작용.

## 승인 상태

- 승인됨: 전체 로컬 단계의 권장 구현·단계별 local commit·승인된 정확한 파일 정리·폴더 전환.
- 미승인: 원격 생성·push, main·태그·릴리스, 보호 경로 접근.

## 차단

- 없음.

## 실패 기록

| 목표 | 원인 | 연속 | 재시작 조건 |
|---|---|---:|---|
| Maintainer clean clone | Git helper PATH와 handoff 문자열 판정 | 0 | consumer verify 선행 후 재실행 통과 |

## 알려진 위험

- 실제 영상 사용성은 자동 검사로 판정하지 않으며 사용자가 운영 중 확인한다.
- 현재 로컬 폴더 이름은 아직 이전 Maintainer 이름이며 단계 5에서 전환한다.

## 첫 다음 행동

1. Host 계약·개요·검증기 변경을 첫 Creator commit으로 저장한다.
2. 첫 commit이 clean이면 `scripts/clone_conformance.py`의 inbound reference를 검색한다.
3. 참조가 0이면 해당 실행기를 제거하고 두 번째 Creator commit으로 저장한다.

## 다음 세션 시작 prompt

시작 3문서, 전체 설계, `REPOSITORY_ROLE_SEPARATION_STAGE_3.md`를 읽고 보호 경로에 접근하지 않는다. Host gate 통과 전에는 Maintainer 전용 파일 제거 commit을 만들지 않는다.
