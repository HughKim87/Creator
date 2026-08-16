# Agent Core Maintainer 현재 상태

- 목적: 이 Maintainer 저장소의 현재 단계·승인·차단·첫 다음 행동만 소유한다.
- 읽는 시점: Core 정책과 소비 정책을 읽은 뒤 현재 작업을 시작·재개할 때.
- 책임: 현재 작업 에이전트가 검증된 상태로 갱신하고 사용자가 단계 전환을 승인한다.
- 상태: Maintainer consumer contract v2 로컬 전환 완료. 사용자 단계 확인 대기.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 활성 단계 설계가 있을 때의 해당 설계.
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; 원격 미게시 Core revision에 의존하지만 uncommitted 파일에는 의존하지 않는다.

## 현재 단계

- `maintainer-consumer-contract-v2`: 루트 진입 포인터, 소비 정책, 상태와 도메인 route를 Core contract v2에 맞추고 로컬 결정론적 게이트를 완료했다.

## 직전 게이트

- `pass`: Maintainer 소비 통합 gate, 관련 회귀와 후보 commit clean-clone 검증을 통과했다. 외부 콜드 Agent 의미 검증은 사용자 결정에 따라 `not_run`이다.

## 승인 상태

- 이번 단계의 로컬 문서·route·관련 테스트 수정과 로컬 커밋이 승인됐다.
- 정책·규칙의 외부 모델 서비스 전송, Core submodule 내용 변경과 모든 push·원격 조작은 승인되지 않았다.

## 차단

- 없음.

## 알려진 위험

- 현재 Core revision은 원격에 게시되지 않아 다른 PC의 일반 clone으로 아직 복원할 수 없다.
- 일부 Creator 코드와 문서가 `legacy-core`의 `file_data` 계약을 직접 사용하며 다음 단계에서 별도로 이전해야 한다.
- 실제 Maintainer 원격과 실제 Host의 읽기 전용 사용은 아직 검증하지 않았다.
- 자연어 route 의미와 실제 Codex·Claude 진입 동작은 외부 전송을 하지 않아 검증하지 않았다.

## 첫 다음 행동

1. 사용자가 이 단계의 완료를 확인하면 `scripts/`, `extension/src/`, `extension/tests/`의 `legacy-core/file_data` 직접 의존을 분류해 다음 단계의 정확한 이전 범위와 게이트를 확정한다.

## 다음 session 시작 prompt

1. `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 이 문서를 순서대로 읽고 첫 다음 행동보다 넓은 작업은 사용자 확인 없이 시작하지 않는다.
