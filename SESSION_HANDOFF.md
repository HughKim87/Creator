# Agent Core Maintainer 현재 상태

- 목적: 이 Maintainer 저장소의 현재 단계·승인·차단·첫 다음 행동만 소유한다.
- 읽는 시점: Core 정책과 소비 정책을 읽은 뒤 현재 작업을 시작·재개할 때.
- 책임: 현재 작업 에이전트가 검증된 상태로 갱신하고 사용자가 단계 전환을 승인한다.
- 상태: Legacy 흡수·의존 전환·원본 정리와 Core·Maintainer 작업 브랜치 게시를 완료했다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 활성 단계 설계가 있을 때의 해당 설계.
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; 검증된 Core와 Maintainer revision이 각각 원격 작업 브랜치에 게시됐으며 uncommitted 파일에는 의존하지 않는다.

## 현재 단계

- `legacy-cleanup-and-publish-complete`: 흡수 완료된 Legacy 원본과 과거 실패 기록을 제거하고 Git 이력에 복구 가능성을 남긴 뒤 Core와 Maintainer 작업 브랜치를 게시했다. 활성 구현 단계는 없다.

## 직전 게이트

- `pass`: 정리 완료 후보의 ASCII·한글·공백 경로 clean clone 3종에서 Core 165개·Maintainer 확장 143개 테스트와 계약·산출물 게이트가 통과했다.

## 승인 상태

- Legacy 흡수·의존 전환, `legacy-core/`와 `extension/work/CORE_CHANGE_FAILURES.md` 삭제, 단계별 로컬 커밋과 Core·Maintainer 작업 브랜치 push 승인을 모두 집행했다.
- 보호 데이터 접근, main 병합, force push, 태그·릴리스 게시와 그 밖의 원격 조작은 승인되지 않았다.

## 차단

- 없음.

## 알려진 위험

- 게시 대상은 작업 브랜치뿐이며 main 병합은 수행하지 않았다.
- 실제 원격 Host의 읽기 전용 Core 사용은 아직 검증하지 않았다.
- 자연어 route 의미와 실제 Codex·Claude 진입 동작은 외부 전송을 하지 않아 검증하지 않았다.

## 첫 다음 행동

1. 새 요청이 오면 Core와 Maintainer의 원격 작업 브랜치 상태를 먼저 조회하고 main 병합이나 실제 Host 적용은 별도 승인 뒤 시작한다.

## 다음 session 시작 prompt

1. `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 이 문서를 순서대로 읽고 첫 다음 행동보다 넓은 작업은 사용자 확인 없이 시작하지 않는다.
