---
doc_id: doc.project_status
kind: user_status
domain: user_status
lifecycle: active
authority: derived from SESSION_HANDOFF.md for the current user-facing milestone
audience: user
language: ko
validation: tool_validated
purpose: 사용자가 현재 진행 단계, 완료 작업, 검증 결과와 다음 결정을 한글로 확인한다.
scope: 사용자 확인용 요약만 포함하며 에이전트 실행 규칙이나 현재 상태 정본으로 사용하지 않는다.
read_when: 사용자가 현재 상태를 확인하거나 단계 완료 보고를 받을 때.
write_when: 사용자에게 보고할 만한 단계나 문서 구조가 변경됐을 때 SESSION_HANDOFF.md를 근거로 갱신한다.
---
# 프로젝트 현재 상태

## 현재 단계

- 프로젝트 공통 기반 L0~L4와 옵시디언 문서 탐색 기반 L3.1~L3.3이 완료됐다.
- 다음 단계는 실제 영상 제작 워크플로우 규칙을 만드는 L5이며 아직 승인되지 않았다.
- Graphify는 실패 분석 후 제외됐다. 옵시디언 공식 CLI, Properties, Bases만 활성 탐색 수단이다.

## 옵시디언용 문서 구조

| 위치 | 용도 |
|---|---|
| `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md` | 매 작업의 직접 시작 경로·전역 규칙·현재 상태 |
| `docs/agent/navigation/` | 문서 배치·분류 규칙과 자동 생성 Base 인덱스 |
| `docs/agent/rebuild/` | 재구축 원칙·계획·기능 결정 |
| `docs/agent/workflow/` | 제작 워크플로우와 편집 품질 요구사항 |
| `docs/agent/tooling/` | 재사용 도구와 스킬 요구사항 |
| `docs/agent/state/` | 상태 모델, 정상 입출력·생명주기, JSON Schema |
| `docs/user/` | 현재 사용자용 문서 |
| `docs/reports/` | 한 시점의 분석과 실패 증거; 실행 정본이 아님 |

모든 관리 대상 노트에는 목적, 범위, 권한, 읽기·수정 시점, 생명주기, 도메인을 YAML Properties로 기록했다. `AGENT_DOCUMENTS.base`는 이 속성으로 화면을 만들 뿐 별도 정본이 아니다.

## 탐색 방식

- 알려진 작업은 `AGENTS.md`의 직접 경로를 사용하므로 옵시디언 검색 비용이 없다.
- 처음 보는 작업만 가장 좁은 Base 도메인 화면이나 도메인 폴더를 검색한다.
- 후보는 최대 3개이며 `purpose`와 `authority`를 비교한 뒤 정확한 원자 문서 하나만 읽는다.
- 실패·무결과·모호함·보호 경로 위험은 자동 우회하지 않고 보고한다.

## 문서 분리 결과

- 문서의 위치·이름·분할·이동은 `DOCUMENT_PLACEMENT.md`, 문서 분류 속성은 `DOCUMENT_REGISTRY.md`가 담당한다.
- 정상 상태 파일 읽기·쓰기·승격은 `STATE_OPERATIONS.md`, 상태 데이터 모델과 스키마 변경은 `VIDEO_TASK_STATE.md`가 담당한다.
- 사람이 수동으로 유지하던 전체 문서 목록을 없애고 Base가 Properties에서 화면을 자동 생성하도록 바꿨다.

## 검증과 측정

- 실제 옵시디언 Base에서 활성 문서, 탐색, 상태, 역사 보고서 화면의 분류 결과를 확인했다.
- 문서 이동과 상태 처리 검색은 각각 정확한 원자 문서를 선택했고 관련 없는 문서를 읽지 않았다.
- Properties, 폴더 배치, Base 범위, 직접 라우팅, 링크, 상태 스키마, Graphify 제외, 제어 문서 크기를 통합 테스트로 검사한다.
- 같은 세 작업을 기존 직접 라우팅, 기존 문서에 옵시디언만 적용, 옵시디언용 문서 최적화 조건으로 비교한 결과는 `docs/reports/2026-07-20_옵시디언_전면_도입_토큰_비교.md`에 기록했다.
- 토큰값은 실제 청구량이 아니라 동일한 `ceil(문자 수 / 4)` 추정식으로 비교한 문서 컨텍스트다.

## 다음 결정

다음 구축 단계는 L5다. 여기부터 영상 제작 순서, 단계별 완료 조건, 사용자 결정 지점 같은 실제 워크플로우 규칙을 구축한다. 별도 승인이 있어야 시작한다.
