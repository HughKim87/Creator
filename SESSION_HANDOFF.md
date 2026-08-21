# Agent Core Maintainer 현재 상태

- 목적: 이 Maintainer 저장소의 현재 단계·승인·차단·첫 다음 행동만 소유한다.
- 읽는 시점: Core 정책과 소비 정책을 읽은 뒤 현재 작업을 시작·재개할 때.
- 책임: 현재 작업 에이전트가 검증된 상태로 갱신하고 사용자가 단계 전환을 승인한다.
- 상태: 7H Legacy 종료 감사 후보. 활성 의존과 고유 소유권 이전을 마쳤고 후보 커밋·clean clone 검증을 진행한다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 활성 단계 설계가 있을 때의 해당 설계.
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; 원격 미게시 Core revision에 의존하지만 uncommitted 파일에는 의존하지 않는다.

## 현재 단계

- `legacy-absorption-7h-termination-audit`: `legacy-core`의 공통 기능은 흡수·대체됐고 `.obsidian/app.json` 정본도 활성 Maintainer로 이전됐다. 디렉터리는 삭제 승인 전 source lineage만 보존한다.

## 직전 게이트

- `pass`: 현재 작업 트리에서 Core 165건, Extension 143건, Core 소비 계약, 정본 artifact 4건을 통과했고 활성 Legacy `file_data` import가 0건이다.

## 승인 상태

- 남은 Legacy 흡수 설계인 작업 상태 Runtime, 공개 선택 기능·CLI, 기존 `file_data` 의존 전환과 단계별 로컬 커밋을 사용자가 연속 진행하도록 승인했다.
- 정책·규칙의 외부 모델 서비스 전송, 보호 데이터 접근과 모든 push·원격 조작은 승인되지 않았다.

## 차단

- 없음.

## 알려진 위험

- 현재 Core revision은 원격에 게시되지 않아 다른 PC의 일반 clone으로 아직 복원할 수 없다.
- `legacy-core/`는 동결된 종료 후보지만 정확한 전체 경로에 대한 별도 삭제 승인을 받지 않아 유지 중이다.
- `extension/work/CORE_CHANGE_FAILURES.md`는 활성 의존이 없는 과거 실패 기록이지만 이번 Legacy 디렉터리 감사의 삭제 범위에는 포함하지 않았다.
- 실제 Maintainer 원격과 실제 Host의 읽기 전용 사용은 아직 검증하지 않았다.
- 자연어 route 의미와 실제 Codex·Claude 진입 동작은 외부 전송을 하지 않아 검증하지 않았다.

## 첫 다음 행동

1. 7H 변경 파일만 후보 커밋으로 만들고 clean clone에서 artifact 4건, 활성 Legacy import 0건과 공식 통합 게이트를 다시 검증한다.

## 다음 session 시작 prompt

1. `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 이 문서를 순서대로 읽고 첫 다음 행동보다 넓은 작업은 사용자 확인 없이 시작하지 않는다.
