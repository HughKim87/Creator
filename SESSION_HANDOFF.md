# Agent Core Maintainer 현재 상태

- 목적: 이 Maintainer 저장소의 현재 단계·승인·차단·첫 다음 행동만 소유한다.
- 읽는 시점: Core 정책과 소비 정책을 읽은 뒤 현재 작업을 시작·재개할 때.
- 책임: 현재 작업 에이전트가 검증된 상태로 갱신하고 사용자가 단계 전환을 승인한다.
- 상태: 7G Maintainer의 Legacy `file_data` 직접 의존 제거 후보. 직접 게이트를 통과했고 후보 커밋·clean clone 검증을 진행한다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 활성 단계 설계가 있을 때의 해당 설계.
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; 원격 미게시 Core revision에 의존하지만 uncommitted 파일에는 의존하지 않는다.

## 현재 단계

- `legacy-absorption-7g-maintainer-migration`: Maintainer의 공통 데이터 처리는 Core 공개 `shared_data` v1 CLI로, Extension artifact 검증은 Maintainer 소유의 최소 의미 일치 검사기로 전환했다.

## 직전 게이트

- `pass`: 현재 작업 트리에서 Core 165건, Extension 143건, Core 소비 계약, Extension 정본 artifact 3건을 통과했고 `scripts`와 `extension`의 활성 Legacy `file_data` 직접 import가 0건이다.
- `not_run`: 7G 후보 커밋의 clean clone 게이트.

## 승인 상태

- 남은 Legacy 흡수 설계인 작업 상태 Runtime, 공개 선택 기능·CLI, 기존 `file_data` 의존 전환과 단계별 로컬 커밋을 사용자가 연속 진행하도록 승인했다.
- 정책·규칙의 외부 모델 서비스 전송, 보호 데이터 접근과 모든 push·원격 조작은 승인되지 않았다.

## 차단

- 없음.

## 알려진 위험

- 현재 Core revision은 원격에 게시되지 않아 다른 PC의 일반 clone으로 아직 복원할 수 없다.
- `legacy-core`는 활성 import에서는 분리됐지만 남은 파일의 흡수·대체·보존 분류와 삭제 가능 판정은 아직 끝나지 않았다.
- 실제 Maintainer 원격과 실제 Host의 읽기 전용 사용은 아직 검증하지 않았다.
- 자연어 route 의미와 실제 Codex·Claude 진입 동작은 외부 전송을 하지 않아 검증하지 않았다.

## 첫 다음 행동

1. 정확한 7G 변경을 후보 커밋으로 만들고 임시 clean clone에서 Core submodule 초기화, 공식 직접 게이트와 활성 `file_data` import 0건을 다시 검증한다.

## 다음 session 시작 prompt

1. `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 이 문서를 순서대로 읽고 첫 다음 행동보다 넓은 작업은 사용자 확인 없이 시작하지 않는다.
