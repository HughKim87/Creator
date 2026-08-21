# Agent Core Maintainer 현재 상태

- 목적: 이 Maintainer 저장소의 현재 단계·승인·차단·첫 다음 행동만 소유한다.
- 읽는 시점: Core 정책과 소비 정책을 읽은 뒤 현재 작업을 시작·재개할 때.
- 책임: 현재 작업 에이전트가 검증된 상태로 갱신하고 사용자가 단계 전환을 승인한다.
- 상태: 7F `shared_data` v1 공개 선택 기능 로컬 완료. Maintainer 의존 전환을 진행한다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 활성 단계 설계가 있을 때의 해당 설계.
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; 원격 미게시 Core revision에 의존하지만 uncommitted 파일에는 의존하지 않는다.

## 현재 단계

- `legacy-absorption-7f-public-capability`: 흡수된 L7 기반을 `shared_data` v1의 `info`·`invoke` JSON CLI와 versioned schema로 공개하고 Core 0.3.0 호환성 선언에 등록했다.

## 직전 게이트

- `pass`: 공개 CLI 대표 흐름 4건, Core 전체 165건, Core gate와 Maintainer 소비 gate를 통과했다. `optional-features`는 공개 기능 1종을 실행 검증해 `pass`다.

## 승인 상태

- 남은 Legacy 흡수 설계인 작업 상태 Runtime, 공개 선택 기능·CLI, 기존 `file_data` 의존 전환과 단계별 로컬 커밋을 사용자가 연속 진행하도록 승인했다.
- 정책·규칙의 외부 모델 서비스 전송, 보호 데이터 접근과 모든 push·원격 조작은 승인되지 않았다.

## 차단

- 없음.

## 알려진 위험

- 현재 Core revision은 원격에 게시되지 않아 다른 PC의 일반 clone으로 아직 복원할 수 없다.
- `shared_data` v1은 공개됐지만 Maintainer의 기존 Extension과 검증 script는 아직 Legacy `file_data`를 직접 import한다.
- 일부 Creator 코드와 문서가 `legacy-core`의 `file_data` 계약을 직접 사용하므로 기능별 이전이 끝날 때까지 활성 통합 검증기는 실패한다.
- `scripts/verify.py`는 시작 시 `legacy-core/src`를 import 경로에 넣지 않은 채 `file_data`를 import하므로 현재 격리 환경에서 기존 import 실패가 재현된다. 7G 의존 전환이 이 원인을 제거해야 한다.
- 실제 Maintainer 원격과 실제 Host의 읽기 전용 사용은 아직 검증하지 않았다.
- 자연어 route 의미와 실제 Codex·Claude 진입 동작은 외부 전송을 하지 않아 검증하지 않았다.

## 첫 다음 행동

1. 7G에서 Maintainer의 `scripts/verify.py`, Extension registry·YouTube domain이 직접 import하는 Legacy `file_data` 의존을 분류하고 새 Core 공개 경계 또는 소비 소유 구현으로 전환한다.

## 다음 session 시작 prompt

1. `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 이 문서를 순서대로 읽고 첫 다음 행동보다 넓은 작업은 사용자 확인 없이 시작하지 않는다.
