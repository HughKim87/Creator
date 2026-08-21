# Agent Core Maintainer 현재 상태

- 목적: 이 Maintainer 저장소의 현재 단계·승인·차단·첫 다음 행동만 소유한다.
- 읽는 시점: Core 정책과 소비 정책을 읽은 뒤 현재 작업을 시작·재개할 때.
- 책임: 현재 작업 에이전트가 검증된 상태로 갱신하고 사용자가 단계 전환을 승인한다.
- 상태: 승인된 Legacy 원본·과거 실패 기록 정리 완료 후보. 검증·커밋 뒤 Core와 Maintainer 게시를 진행한다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 활성 단계 설계가 있을 때의 해당 설계.
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; 원격 미게시 Core revision에 의존하지만 uncommitted 파일에는 의존하지 않는다.

## 현재 단계

- `legacy-cleanup-and-publish`: 흡수 완료된 Legacy 원본과 과거 실패 기록을 제거했다. Git 이력이 복구를 소유하며 게시 전 최종 검증을 진행한다.

## 직전 게이트

- `pass`: 흡수 완료 상태 커밋 `e6cdad0`의 ASCII·한글·공백 경로 clean clone 3종에서 전체 통합 게이트가 통과했다.

## 승인 상태

- Legacy 흡수·의존 전환, `legacy-core/`와 `extension/work/CORE_CHANGE_FAILURES.md` 삭제, 단계별 로컬 커밋과 Core·Maintainer push를 사용자가 승인했다.
- 보호 데이터 접근, main 병합, force push, 태그·릴리스 게시와 그 밖의 원격 조작은 승인되지 않았다.

## 차단

- 없음.

## 알려진 위험

- 삭제 변경은 아직 후보 커밋과 clean clone 검증을 거치지 않았다.
- 현재 Core와 Maintainer 작업 브랜치는 아직 원격에 게시되지 않았다.
- 실제 Maintainer 원격과 실제 Host의 읽기 전용 사용은 아직 검증하지 않았다.
- 자연어 route 의미와 실제 Codex·Claude 진입 동작은 외부 전송을 하지 않아 검증하지 않았다.

## 첫 다음 행동

1. 삭제·참조 해제 변경의 공식 직접 게이트를 실행하고 정확한 변경만 커밋한 뒤 clean clone을 통과하면 Core 브랜치부터 Maintainer 브랜치 순서로 push한다.

## 다음 session 시작 prompt

1. `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 이 문서를 순서대로 읽고 첫 다음 행동보다 넓은 작업은 사용자 확인 없이 시작하지 않는다.
