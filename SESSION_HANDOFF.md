# Agent Core Maintainer 현재 상태

- 목적: 이 Maintainer 저장소의 현재 단계·승인·차단·첫 다음 행동만 소유한다.
- 읽는 시점: Core 정책과 소비 정책을 읽은 뒤 현재 작업을 시작·재개할 때.
- 책임: 현재 작업 에이전트가 검증된 상태로 갱신하고 사용자가 단계 전환을 승인한다.
- 상태: Core 검증기의 분석된 H1·H2·H3 신뢰성 보강과 로컬 검증을 완료했다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 활성 단계 설계가 있을 때의 해당 설계.
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; 검증된 Core와 Maintainer 후보는 로컬 커밋으로 고정하며 uncommitted 파일에는 의존하지 않는다.

## 현재 단계

- `verifier-reliability-hardening-complete`: H1 환경변수 우회, H2 소비 검사 실행 보고, H3 중복 route 결정론 문제만 수정했고 Core 후보 `cfbd7e2`로 고정했다.

## 직전 게이트

- `pass`: Core 167개·Maintainer 확장 143개 테스트, Core·Consumer 통합 gate와 유지보수 검사를 통과했고 Core 후보의 별도 clean clone gate도 통과했다.

## 승인 상태

- Legacy 흡수·의존 전환, `legacy-core/`와 `extension/work/CORE_CHANGE_FAILURES.md` 삭제, 단계별 로컬 커밋과 Core·Maintainer 작업 브랜치 push 승인을 모두 집행했다.
- Sandbox 테스트 Host 구성과 Agent-Core 읽기 전용 Deploy Key 등록·권한 검증 승인을 모두 집행했다.
- Core 검증기의 분석된 H1·H2·H3만 개선하고 로컬 후보 커밋과 clean clone까지 검증하는 작업을 승인받았다. 작업 중 push는 승인되지 않았다.
- 보호 데이터 접근, main 병합, force push, 태그·릴리스 게시, 실제 프로젝트 Host 적용은 승인되지 않았다.

## 차단

- 없음.

## 알려진 위험

- Agent-Core 작업 브랜치는 main에 아직 포함되지 않았다.
- H1·H2·H3 후보 커밋은 로컬에만 있으며 원격에 push하지 않았다.
- creator main에는 별도 사용자 변경이 반영돼 통합 작업 브랜치와 갈라져 있으므로 병합 전 비교가 필요하다.
- 검증한 Host는 Sandbox 로컬 테스트 전용이며 실제 프로젝트에는 아직 적용하지 않았다.
- 자연어 route 의미와 실제 Codex·Claude 진입 동작은 외부 전송을 하지 않아 검증하지 않았다.

## 첫 다음 행동

1. 사용자가 후보 검토 후 별도로 승인하면 Core와 Maintainer 작업 브랜치의 push 또는 main 반영 순서를 결정한다.

## 다음 session 시작 prompt

1. `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, 이 문서를 순서대로 읽고 첫 다음 행동보다 넓은 작업은 사용자 확인 없이 시작하지 않는다.
