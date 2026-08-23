# Agent Core Maintainer 현재 상태

- 목적: 새 세션이 Agent Core 완료 작업의 정확한 중단점부터 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`를 읽은 뒤 어떤 작업이든 시작하기 전.
- 책임: 작업 에이전트가 검증된 상태만 갱신하고 사용자가 승인 경계를 소유한다.
- 상태: 완료 계획 보완 대기. Core 원격 push는 Deploy Key 작업까지 보류한다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: `CORE_COMPLETION_PLAN_2026-08-22.md` — 최신 요구를 반영하기 전에는 실행 기준으로 쓰지 않는다.
- 활성 단계 설계: 없음.
- handoff mode: `same-workspace` — `extension/work` 테스트 부산물만 비추적이다.

## 현재 목표

필수 요구사항·현재 구현·과거 실패·검증 게이트를 구현 전에 연결하고 그 범위를 한 번에 구현·검증한다. 기존 요구 위반은 새 개선이 아니라 미완료 결함으로 처리한다.

## 핵심 용어

- `Core`: `core/` submodule, 원격 `HughKim87/Agent-Core`. `Maintainer`: 현재 부모 저장소, 원격 `HughKim87/creator`.
- `shared_data`: 일반 Host에는 선택, Maintainer에는 `v1`이 필요한 capability 후보.

## 현재 단계

- `completion-plan-completeness-revision-required`.
- H1 환경변수 우회, H2 실행 보고, H3 route 결정론은 로컬 commit으로 수정·검증했다.
- 이후 L7 제거, Python 3.10, Consumer capability, 승인 정본, 검증 생략·오염·clone 범위 문제가 확인됐다.
- 완료 계획은 작성됐지만 `추가 분석 억제` 방식이 최신 요구와 충돌한다. 0~4단계와 원격 단계는 모두 미시작이다.
- 응답 형식 규칙을 Core 문서 작업 규칙 정본에 흡수하고 Maintainer 작업 브랜치 head를 원격 main으로 승격했다.

## 재개 지점

0단계를 시작하지 말고 계획 보완부터 한다. Core 원격 push는 사용자 결정으로 보류됐으므로 재개 조건이 아니다.

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
| Core 원격 push | 기본 SSH 키 | `Permission denied (publickey)` | 1 | 인증 방식 확정 후 재시도 |

## 알려진 위험

- 원격 main의 Core gitlink가 원격에 없다. `clone --recurse-submodules`가 실패한다. Deploy Key 작업 시 Core push로 해소한다.
- Maintainer 전용 원격이 없어 저장소 이름과 내용이 어긋난다. 단계 설계 7의 미완료 항목이다.
- `extension/work` 부산물은 오염 탐지 전 삭제하지 않는다.
- 로컬 URL clone은 원격 재현성을 증명하지 않는다.

## 첫 다음 행동

1. Maintainer 작업 브랜치를 원격 같은 이름 브랜치로 push해 main과의 어긋남을 없앤다.
2. 완료 계획에 추적표·실패 모드·정상/실패/경계 검증·사후 결함 환류 규칙을 추가하고 분석 억제 문구를 제거한다.
3. 계획 검토 결과와 구현 시작 가능 여부를 보고하고 승인을 받는다. 그 전에는 0단계를 시작하지 않는다.
4. 쓰기 Deploy Key 생성 작업에서 Core 작업 브랜치를 push해 gitlink 도달성을 회복한다.

## 다음 세션 시작 prompt

Core 정책, 소비 정책, 이 문서를 순서대로 읽는다. 보호 경로에 접근하지 말고 완료 계획부터 보완한다. 태그·릴리스·실제 Host 적용은 별도 승인 전까지 금지한다.
