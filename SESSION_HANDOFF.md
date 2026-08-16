# Agent Core Maintainer 현재 상태

- 목적: 이 Maintainer 저장소의 현재 단계·승인·차단·첫 다음 행동만 소유한다.
- 읽는 시점: Core 정책과 소비 정책을 읽은 뒤 현재 작업을 시작·재개할 때.
- 책임: 현재 작업 에이전트가 검증된 상태로 갱신하고 사용자가 단계 전환을 승인한다.
- 상태: 7A 선택적 공통 데이터 흡수 계약 로컬 완료. 사용자 단계 확인 대기.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 활성 단계 설계가 있을 때의 해당 설계.
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; 원격 미게시 Core revision에 의존하지만 uncommitted 파일에는 의존하지 않는다.

## 현재 단계

- `legacy-absorption-7a-contract`: 공통 데이터 기능을 필수 Kernel과 분리된 L7 흡수 승인 범위로 확정하고, 구현 전에는 공개 기능으로 주장하지 않는 호환 경계를 완료했다.

## 직전 게이트

- `pass`: Core 100개 회귀, Core gate, Maintainer 소비 gate와 Core 후보 commit clean-clone 검증을 통과했다. 선택 기능은 아직 등록되지 않아 의도대로 `not_applicable`이다.

## 승인 상태

- 7A의 Core 범위·계층·호환성 문서, 관련 회귀와 Core·부모 로컬 커밋이 승인됐다.
- 후속 Legacy Runtime 구현, 정책·규칙의 외부 모델 서비스 전송과 모든 push·원격 조작은 승인되지 않았다.

## 차단

- 없음.

## 알려진 위험

- 현재 Core revision은 원격에 게시되지 않아 다른 PC의 일반 clone으로 아직 복원할 수 없다.
- `optional_capabilities`는 아직 비어 있으며 승인된 공통 데이터 기능은 구현되거나 공개되지 않았다.
- 일부 Creator 코드와 문서가 `legacy-core`의 `file_data` 계약을 직접 사용하므로 기능별 이전이 끝날 때까지 활성 통합 검증기는 실패한다.
- 실제 Maintainer 원격과 실제 Host의 읽기 전용 사용은 아직 검증하지 않았다.
- 자연어 route 의미와 실제 Codex·Claude 진입 동작은 외부 전송을 하지 않아 검증하지 않았다.

## 첫 다음 행동

1. 사용자가 7A 완료를 확인하면 7B에서 공통 record 외피·경로 안전·원자적 저장과 해당 schema·계약·회귀 테스트만 L7 선택 계층으로 흡수한다.

## 다음 session 시작 prompt

1. `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 이 문서를 순서대로 읽고 첫 다음 행동보다 넓은 작업은 사용자 확인 없이 시작하지 않는다.
