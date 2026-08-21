# Agent Core Maintainer 현재 상태

- 목적: 이 Maintainer 저장소의 현재 단계·승인·차단·첫 다음 행동만 소유한다.
- 읽는 시점: Core 정책과 소비 정책을 읽은 뒤 현재 작업을 시작·재개할 때.
- 책임: 현재 작업 에이전트가 검증된 상태로 갱신하고 사용자가 단계 전환을 승인한다.
- 상태: 7E 작업 상태·실행 호환 Runtime 로컬 완료. 남은 설계 작업을 연속 진행 중이다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 활성 단계 설계가 있을 때의 해당 설계.
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; 원격 미게시 Core revision에 의존하지만 uncommitted 파일에는 의존하지 않는다.

## 현재 단계

- `legacy-absorption-7e-work-runtime`: 불변 작업 요청, append-only event 정본, 재생 가능한 bounded snapshot과 controlled 단계 설계 fingerprint를 비활성 L7 호환 Runtime으로 일반화했다.

## 직전 게이트

- `pass`: work·execution 직접 회귀 11건, 관련 L7 회귀 26건, Core 전체 161건, Core gate와 Maintainer 소비 gate를 통과했다. 선택 기능은 아직 등록되지 않아 의도대로 `not_applicable`이다.

## 승인 상태

- 남은 Legacy 흡수 설계인 작업 상태 Runtime, 공개 선택 기능·CLI, 기존 `file_data` 의존 전환과 단계별 로컬 커밋을 사용자가 연속 진행하도록 승인했다.
- 정책·규칙의 외부 모델 서비스 전송, 보호 데이터 접근과 모든 push·원격 조작은 승인되지 않았다.

## 차단

- 없음.

## 알려진 위험

- 현재 Core revision은 원격에 게시되지 않아 다른 PC의 일반 clone으로 아직 복원할 수 없다.
- record·저장 기반과 지식·수명주기는 `implemented_private`이며 `optional_capabilities`가 비어 있어 아직 외부 공개 기능이 아니다.
- 흡수된 L7 기능은 모두 `implemented_private`라 소비자가 사용할 versioned CLI가 아직 없다.
- 일부 Creator 코드와 문서가 `legacy-core`의 `file_data` 계약을 직접 사용하므로 기능별 이전이 끝날 때까지 활성 통합 검증기는 실패한다.
- `scripts/verify.py`는 시작 시 `legacy-core/src`를 import 경로에 넣지 않은 채 `file_data`를 import하므로 현재 격리 환경에서 기존 import 실패가 재현된다. 7G 의존 전환이 이 원인을 제거해야 한다.
- 실제 Maintainer 원격과 실제 Host의 읽기 전용 사용은 아직 검증하지 않았다.
- 자연어 route 의미와 실제 Codex·Claude 진입 동작은 외부 전송을 하지 않아 검증하지 않았다.

## 첫 다음 행동

1. 7F에서 흡수된 L7 기능을 하나의 versioned 선택 기능·CLI·schema 경계로 공개하고 호환성 선언과 소비 안내를 같은 snapshot에서 검증한다.

## 다음 session 시작 prompt

1. `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 이 문서를 순서대로 읽고 첫 다음 행동보다 넓은 작업은 사용자 확인 없이 시작하지 않는다.
