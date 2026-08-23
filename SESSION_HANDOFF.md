# Agent Core Maintainer 현재 상태

- 목적: 새 세션이 Agent Core 완료 작업의 정확한 중단점부터 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`를 읽은 뒤 어떤 작업이든 시작하기 전.
- 책임: 작업 에이전트가 검증된 상태만 갱신하고 사용자가 승인 경계를 소유한다.
- 상태: 완료 계획 보완 완료. 구현 0단계 진입 승인 대기.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: `CORE_COMPLETION_PLAN_2026-08-22.md` — 보완 완료. 검토 보고와 승인 뒤 실행 기준이 된다.
- 활성 단계 설계: 없음.
- handoff mode: `same-workspace` — `extension/work` 테스트 부산물만 비추적이다.

## 현재 목표

필수 요구사항·현재 구현·과거 실패·검증 게이트를 구현 전에 연결하고 그 범위를 한 번에 구현·검증한다. 기존 요구 위반은 새 개선이 아니라 미완료 결함으로 처리한다.

## 핵심 용어

- `Core`: `core/` submodule, 원격 `HughKim87/Agent-Core`. `Maintainer`: 현재 부모 저장소, 원격 `HughKim87/creator`.
- `shared_data`: 일반 Host에는 선택, Maintainer에는 `v1`이 필요한 capability 후보.

## 현재 단계

- `completion-plan-revised-awaiting-entry-approval`.
- H1 환경변수 우회, H2 실행 보고, H3 route 결정론은 로컬 commit으로 수정·검증했다.
- 이후 L7 제거, Python 3.10, Consumer capability, 승인 정본, 검증 생략·오염·clone 범위 문제가 확인됐다.
- 응답 형식 규칙을 Core 문서 작업 규칙 정본에 흡수하고 Maintainer 작업 브랜치 head를 원격 main으로 승격했다.
- 완료 계획에 요구사항 추적표 `R1`~`R6`, 실패 모드, 정상·실패·경계 게이트 규칙, 사후 결함 환류 절을 추가하고 분석 억제 문구를 제거했다.
- 0~4단계와 원격 단계는 모두 미시작이다.

## 재개 지점

보완된 계획이 구현 시작 가능한 상태인지 검토해 보고하고 승인을 받는다. 승인 전에는 0단계를 시작하지 않는다. Core 원격 push는 사용자 결정으로 보류됐으므로 재개 조건이 아니다.

## 직전 게이트

- `pass`: core+consumer `verify` 19종, findings 0.
- `fail — Core 원격 게시`: SSH 키가 Core 원격에 등록되지 않아 push가 거부됐다.
- 회귀는 Python 3.10에서 `test_shared_*`의 `datetime.UTC` 의존으로 실패한다. 계획 1단계가 소유한다.

## 승인 상태

- 응답 형식 규칙 흡수, 원격 main 승격, push 잠금 해제는 승인·집행됐다.
- Core 원격 push는 인증 실패 후 사용자 결정으로 쓰기 Deploy Key 생성 작업까지 보류한다.
- 태그·릴리스·실제 Host 적용은 별도 승인 전까지 금지다.
- 보호 경로 `inputs`, `outputs`, `extension/inputs`, `extension/outputs` 접근은 미승인이다.

## 차단

- 외부 차단은 없다. 계획의 완전성을 검증하기 전에는 구현을 시작할 수 없다.

## 실패 기록

| 목표 | 시도 | 확인된 원인 | 연속 | 재시작 조건 |
|---|---|---|---:|---|
| Core 완료 판정 | H1~H3 후보 | 검증 범위 불충분 | 1 | 추적표와 반사실 게이트 사전 확정 |
| 완료 계획 | 현재 계획 | 분석 억제가 요구와 충돌 | 1 | 사전 완전성·사후 환류로 교체 |
| Core 원격 push | 기본 SSH 키 | `Permission denied (publickey)` | 1 | 쓰기 Deploy Key 생성 작업에서 재시도 |

## 알려진 위험

- 원격 main의 Core gitlink가 원격에 없다. `clone --recurse-submodules`가 실패한다. Deploy Key 작업 시 Core push로 해소한다.
- Maintainer 전용 원격이 없어 저장소 이름과 내용이 어긋난다. 단계 설계 7의 미완료 항목이다.
- `extension/work` 부산물은 오염 탐지 전 삭제하지 않는다.
- 로컬 URL clone은 원격 재현성을 증명하지 않는다.
- 원격 작업 브랜치가 `541b9b7`, 로컬이 `6e0c3b2`로 한 커밋 어긋나 있다.
- Cowork 원격 세션의 device bridge는 파일 삭제가 차단돼 있다. 그 세션이 git 쓰기를 하면 `HEAD.lock`, `index.lock`, `tmp_obj_*`가 남는다. `core.createObject=rename`, `gc.auto=0`, `maintenance.auto=false`를 이 저장소에 설정해 일부를 줄였고 나머지는 사용자가 직접 지운다.

## 첫 다음 행동

1. 보완된 완료 계획의 `R1`~`R6` 추적표가 각 단계 게이트와 빠짐없이 연결되는지 검토하고 구현 시작 가능 여부를 보고해 승인을 받는다.
2. 승인 뒤 0단계를 실행한다. 저장소 밖 경로에 Core와 Maintainer 후보의 `git bundle`을 만들고 복원 검증한다.
3. 로컬 `6e0c3b2`를 원격 작업 브랜치로 push해 어긋남을 없앤다. main 승격 여부는 별도 판단한다.
4. 쓰기 Deploy Key 생성 작업에서 Core 작업 브랜치를 push해 gitlink 도달성을 회복한다.

## 다음 세션 시작 prompt

Core 정책, 소비 정책, 이 문서를 순서대로 읽는다. 보호 경로에 접근하지 말고 보완된 완료 계획을 검토해 구현 시작 가능 여부부터 보고한다. 태그·릴리스·실제 Host 적용은 별도 승인 전까지 금지한다.
