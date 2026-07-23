# Stage 10 — 에이전트 자율 운영·구조 최적화

- 문서 유형: 활성 단계 계획·진단·완료 근거
- 목적: 사람의 수동 생산 작업을 없애고 에이전트가 승인 범위 안에서 조사·설계·구현·검증·복구를 자율 수행하도록 운영 경계를 보정하며, 모든 지속 데이터를 문서 정본으로 소유하고 기계 파일은 파생물 또는 legacy로 제한해 같은 사실이 여러 파일과 record로 증식하는 구조를 줄인다.
- 사용 시점: Stage 10 착수·체크포인트·종료, 운영 권한 또는 실패 지식 구조를 변경할 때
- 작성 책임: 프로젝트 에이전트
- 승인 근거: 사용자의 2026-07-23 범위 승인과 2026-07-24 검증 방식 변경
- 상태: **완료 준비** — 후속 High 1을 수정하고 active project root·CLI 우회·타 root 권한 재사용 거부 회귀와 전체 120 tests·통합 게이트를 통과해 자체 96점·차단 결함 0을 재확인함. 사용자 완료 확인과 경계 커밋은 아직 남음
- 현재 상태 정본: [SESSION_HANDOFF](../../SESSION_HANDOFF.md)
- 공통 게이트: [마스터 구축 계획 §6](MASTER_BUILD_PLAN.md#6-공통-승인-게이트)

> **상태 교정 — 2026-07-23:** 이 문서의 이전 `완료·97/100` 판정은 사용자의 “모든 지속 데이터는 문서가 정본이며 프로젝트 작업도 그 문서를 기반으로 진행” 요구를 누락한 상태에서 확정됐으므로 철회한다. §10의 부분 구현 증거는 보존하지만 전체 완료 근거로 사용하지 않는다. 현재 실행 권위는 §13~§23의 문서 기반 데이터 구조 교정 계획이다.

## 1. 최신 사용자 의도와 단계 목표

사용자가 이번 단계에서 명시한 최상위 의도는 다음과 같다.

> “사람의 수동작업이 없이 모든작업을 agent 의 자율성에 맡겨 생산성을 극한으로 끌어올리기 위함”

> “프로젝트의 데이터구성은 agent 가 작업을 명확하게 하기 위한 방향으로 최적화되어있어야 하고, 작업 과정들에 대해 사람에게 보고하고 요청하고 확인받아야 된다는 얘기”

따라서 데이터 기반 지식 운영 기반은 최종 목적 자체가 아니라 **에이전트가 채팅 기억과 사람의 수동 실행에 의존하지 않고 정확히 일하기 위한 수단**이다. 사람은 목표·금지·보호·외부 영향·되돌리기 어려운 결정과 결과 확인을 맡고, 에이전트는 그 경계 안의 가역적 로컬 작업과 실패 복구를 스스로 수행한다.

완료 후에는 다음이 가능해야 한다.

1. 에이전트가 안전한 기본값과 구현 세부를 스스로 선택하고 근거와 결과를 보고한다.
2. 새 사람 승인 없이 진행하면 안 되는 경계가 위험·권한·범위 기준으로 명확하다.
3. 한 개선 작업의 진단·계획·구현·점수·독립 검증이 이 문서 하나에서 이어진다.
4. 해결된 실패 Markdown은 별도 source·projection·lifecycle record 없이 직접 검증·검색·재사용된다.
5. 새 단계와 실패가 생겨도 수동 파생 문서와 구조화 파일 수가 불필요하게 증가하지 않는다.
6. 모든 지속 프로젝트 데이터는 사람이 읽을 수 있는 문서 하나를 활성 정본으로 가지며 기계 파일에만 존재하는 활성 사실이 없다.
7. 에이전트는 관련 문서 정본을 읽고 작업을 시작하며, 완료 전에 요구·결정·근거·결과·실패·검증·다음 행동을 해당 문서 owner에 반영한다.

## 2. 선행조건과 입력

- Stage 00~09 성공 게이트와 경계 커밋 완료
- 사용자 최신 지시가 Stage 10 전체와 내부 단계의 연속 진행, 독립 교차검증, 95점 이상 보완을 승인
- 시작 규칙, 관련 작업 규칙, 현재 핸드오프 완독
- 보호된 `inputs/`·`outputs/` 접근 없음
- `backup/`은 아래 대표 증거만 읽고 활성 지시로 사용하지 않음
- 기존 미커밋 `runtime-discovery-system-python` 및 관련 projection 변경은 사용자 변경으로 보존

## 3. 진단 근거

### 3.1 현재 활성 구조에서 확인한 사실

| 관찰 | 확인값 | 의미 |
|---|---:|---|
| 활성 Markdown | 85개 | 현재 규모에서는 동작하지만 수동 지도·단계 보기의 지속 증식 위험이 있음 |
| 해결 실패 정본 | 25개 | 원인별 Markdown 한 파일은 고유한 장기 목적을 가짐 |
| `failure_knowledge` record | 39개 | 정본보다 projection revision이 14개 더 많음 |
| source record | 48개 | 실패 Markdown 자체 경로·hash가 projection에도 있는데 별도 source가 추가됨 |
| lifecycle snapshot | 97개 | 실패 source와 projection 각각의 상태가 별도 snapshot을 가짐 |
| lifecycle event | 149개 | 감사 이력은 유효하지만 파생 대상 두 개를 각각 전이해 사건도 확산됨 |
| baseline 자동 검증 | 95개 테스트, scan·verify 통과 | 현재 구조는 일관되지만 최소 구조라는 뜻은 아님 |

### 3.2 역사 증거에서 확인한 사실

| 세대·대표 근거 | 확인된 문제 | 현재 채택 판단 |
|---|---|---|
| `backup/origin/...project_ops_diagnosis...` | 새 문서 생성 게이트가 있었지만 운영 구조가 다시 커짐 | 생성 게이트만으로 부족하며 실제 생성 경로를 줄여야 함 |
| `backup/refactorying_snapshot_1/.../stage-00/STAGE_REPORT.md` | 한 단계가 보고서·명령 결과·파일 변경·위험·증거 묶음으로 분산 | 단계별 진단·계획·검증·결론은 한 owner 안에 누적 |
| `backup/refactorying_snapshot_3/...document-authority-duplication.md` | 단계·에이전트·재검증 회차별 완결형 보고서가 권위 충돌과 토큰 낭비를 만듦 | 새 회차 자체는 새 문서 사유가 아님 |
| `backup/refactorying_snapshot_3/...프로젝트_구조_분석...` | `context/` 요청·payload·work가 128파일까지 증가 | 사건 추적은 한 event 원장과 bounded snapshot만 사용 |
| `backup/refactorying_snapshot_3/SESSION_HANDOFF.md` | 재개 문서에 완료 역사·평가 수치·장문 위험이 누적 | 핸드오프는 현재 목표·검증 상태·첫 행동만 유지 |

역사 자료의 규칙과 경로는 활성화하지 않았다. 위 표는 반복 원인을 판정하기 위한 읽기 전용 증거다.

### 3.3 확정 문제와 원인

| ID | 문제 | 확인된 원인 |
|---|---|---|
| P-10-01 | 현재 문서가 데이터 기반 지식 운영 기반을 최상위 목적으로 설명해 최신 사용자 의도를 충분히 표현하지 못함 | 프로젝트의 수단과 최종 운영 목적을 분리하지 않음 |
| P-10-02 | 불명확한 기술·정책·수치를 넓게 사용자 질문 대상으로 두어 안전한 구현 세부까지 사람이 결정해야 함 | 결정 위험과 단순 불확실성을 구분하지 않음 |
| P-10-03 | 단계마다 수동 Obsidian 보기와 교차검증 보고서가 늘어날 수 있음 | 전체 inventory와 탐색 router의 책임을 수동 완전 목록이 함께 소유 |
| P-10-04 | 실패 Markdown 한 번의 개정이 새 source·failure projection·두 lifecycle snapshot을 만듦 | Markdown이 이미 소유한 경로·hash·해결 상태를 범용 source/lifecycle 모델에 중복 투영 |
| P-10-05 | 핸드오프에 완료 단계 전체 근거와 실패 역사가 누적됨 | 현재 상태와 시점 복기·장기 실패 지식의 소유 경계가 약해짐 |

## 4. 목표 구조와 설계 결정

### 4.1 사람과 에이전트의 역할

| 구분 | 에이전트 자율 수행 | 사람에게 사전 요청·확인 |
|---|---|---|
| 조사·설계 | 승인 목적 안의 읽기, 비교, 안전한 기본값, 가역적 설계 | 목표·성공 기준이 여러 방향으로 갈리고 합리적 기본값이 의도를 바꿀 때 |
| 구현·검증 | 승인 범위의 로컬 편집, 테스트, 실패 수정, 95점 보완 | 삭제·이동, 보호 데이터, 외부 쓰기, 설치·비용, 보안·권한, 실질적 범위 확대 |
| 단계 전환 | 사용자가 정확한 단계 묶음과 성공 게이트를 상시 승인한 경우 자동 진행 | 새 단계가 기존 승인 경계를 넘어설 때 |
| 보고 | 중요한 선택·진행·실패·게이트 결과를 간결하게 알림 | 결과 승인이나 창작·정책 판단처럼 사람 판단 자체가 산출물일 때 |

### 4.2 문서와 폴더

- 하나의 개선 initiative는 원칙적으로 **단계 계획·진단·실행 근거·점수·외부 교차검증 owner 한 파일**을 사용한다.
- 별도 보고서는 독립 독자·보존 목적·의사결정 경계가 기존 owner로 충족되지 않을 때만 만든다.
- 자동 inventory가 모든 활성 문서의 완전 목록을 소유하고, 수동 `DOCUMENT_MAP`은 시작 owner와 범주 router만 소유한다.
- Stage 00~09 수동 보기 파일은 역사 파생물로 유지하지만 Stage 10 이후에는 새 단계 보기 파일을 만들지 않는다.
- 삭제·이동은 이번 승인 범위에서 제외하고, 기존 중복은 신규 생성 중단과 owner 축약으로 먼저 안정화한다.

### 4.3 실패 지식

- `failures/*.md`가 본문·경로·현재 해결 상태·재발 이력의 유일한 정본이다.
- `KnowledgeService`는 정본을 실행 시 strict UTF-8로 파싱해 transient view를 만들고 저장하지 않는다.
- `ContextService`는 해결된 실패 Markdown을 current 문서 후보로 직접 검색·선택한다.
- `MaintenanceService`는 모든 실패 Markdown의 필수 절·상태를 직접 검증한다.
- 기존 `failure_knowledge`·실패 전용 source·lifecycle data는 삭제하지 않고 legacy history로 읽기 호환만 유지한다.
- 새 `failure-import`와 `lifecycle-refresh-failure` 생성 경로는 비저장 검증 경로로 대체하거나 명시적으로 중단한다.

이 결정으로 새 원인 하나는 Markdown 정본 한 파일만 만들고, 같은 원인의 재발·개정은 그 파일 하나만 갱신한다. event나 bounded work snapshot은 작업 상태가 실제로 바뀔 때만 사용한다.

## 5. 인과관계에 따른 내부 단계

| 순서 | 내부 단계 | 선행 이유 | 구현 | 성공 게이트 |
|---:|---|---|---|---|
| 1 | 10A 목적·권한 경계 | 자율성 기준이 먼저 고정돼야 이후 구조 결정의 권한을 판정할 수 있음 | 상시 규칙·요구사항·단계 절차·README 정합화 | 사람/에이전트 책임 표가 충돌 없이 연결되고 보호·외부 경계가 약해지지 않음 |
| 2 | 10B 문서·탐색 구조 | owner와 생성 규칙을 먼저 줄여야 구현 과정 자체가 새 문서를 늘리지 않음 | 문서 생성 게이트, Obsidian router, 단계 보기 정책 보정 | 이 initiative의 새 maintained 문서가 이 파일 1개뿐이고 모든 활성 문서가 inventory로 발견됨 |
| 3 | 10C 실패 직접 재사용 | 운영·문서 owner가 확정돼야 저장 projection 제거 범위를 정할 수 있음 | knowledge/context/maintenance/CLI·계약·테스트 변경 | 실패 개정 대표 흐름에서 새 record·lifecycle 파일 0개, 검색·검증 성공, legacy 직접 선택 유지 |
| 4 | 10D 통합 검증·교차검증 | 실제 전체 diff가 있어야 독립 검증과 점수 평가가 유효함 | 전체 회귀·maintenance·독립 review/challenge·보완 | 네 가지 확인 통과, 독립 지적 판정·보완, 자체 총점 95점 이상 |
| 5 | 10E 정합화·경계 종료 | 검증된 결과만 현재 상태와 Git 경계에 반영해야 함 | 핸드오프·실패 원장·inventory·diff·commit | 미해결 실패 0 또는 명시 blocker, 보호 변경 0, Stage 10 독립 커밋 검증 |

사용자의 이번 지시는 위 내부 단계 전체를 성공 게이트 뒤 연속 진행하는 상시 전환 승인이다. 각 게이트 결과는 같은 work와 이 문서에 남기고 범위가 달라지면 멈춰 확인한다.

## 6. 예상 산출물과 제외 범위

### 예상 산출물

- 이 Stage 10 단일 owner
- 갱신된 운영 규칙·요구사항·마스터 계획·정보 구조·Obsidian router
- 실패 정본 직접 검증·검색 구현과 회귀 테스트
- 간결한 현재 핸드오프와 재생성된 inventory
- 이 문서 안의 독립 교차검증·네 가지 확인·최종 점수

### 제외

- `backup/` 수정·이관·실행 의존
- `inputs/`, `outputs/` 열거·열람
- 기존 legacy record 삭제·병합·대량 이관
- 기존 미커밋 `runtime-discovery-system-python` projection 변경 편집
- 새 DB·검색 엔진·플러그인·예약·CI·외부 앱
- 유튜브 제작 기능 확장
- push·branch·배포·게시

## 7. 검증 계획

1. 변경 전 baseline 95개 테스트와 maintenance scan·verify 결과를 보존한다.
2. 운영 문서에서 최신 목적, 자율 실행, 사전 확인 경계를 문자열·링크·diff로 대조한다.
3. 임시 프로젝트에서 해결 실패 Markdown을 만들고 검증·검색·context package를 실행한다.
4. 같은 Markdown을 개정한 전후 `data/records`와 `data/events` 파일 집합이 모두 같음을 확인한다.
5. unresolved·필수 절 누락·invalid UTF-8 실패 문서가 fail-closed인지 확인한다.
6. legacy failure record 직접 선택이 계속 동작하고 새 기본 검색에는 중복되지 않는지 확인한다.
7. 전체 unittest, maintenance scan·verify, inventory 재생성 일치를 수행한다.
8. 전체 diff를 독립 검증자의 `review`와 `challenge` 관점으로 각각 읽기 전용 교차검증한다.
9. Codex가 각 지적을 재현 가능한 근거로 판정하고 필요한 보완 뒤 전체 게이트를 반복한다.

## 8. 완료 조건

- 10A~10E 성공 게이트가 순서대로 통과
- 새 진단·계획·독립 검증 보고 문서가 이 파일 외 0개
- 실패 정본 개정 대표 흐름의 새 구조화 파일 0개
- canonical failure search가 legacy projection 없이 작동
- 보호·역사·외부·삭제 경계 위반 0
- 전체 회귀와 maintenance 오류 0
- 발생 실패가 원인별 정본에 정리되고 미해결 blocker가 정확히 표시
- 마스터 계획 §6.3 네 가지 확인 전부 통과
- 최종 자체 점수 95/100 이상이며 차단 결함 0
- Stage 10 변경만 포함한 경계 커밋 성공

## 9. 사용자 결정 기록

| 결정 | 사용자 근거 | 적용 |
|---|---|---|
| 최상위 목적은 사람의 수동 생산 작업 없이 에이전트 자율성으로 생산성을 극대화하는 것 | 2026-07-23 최신 지시 | 10A와 모든 후속 운영 기준 |
| 데이터 구성은 에이전트가 명확히 일하기 위한 방향으로 최적화 | 2026-07-23 최신 지시 | 10B·10C |
| 모든 지속 데이터는 문서가 정본이고 프로젝트 작업도 그 문서를 기반으로 진행 | 2026-07-23 후속 명시 지시 | 10R-A~10R-H 전체와 최종 완료 게이트 |
| 에이전트는 과정·중요 판단·실패·결과를 사람에게 보고하고 필요한 요청·확인을 수행 | 2026-07-23 최신 지시 | 10A·10D·10E |
| 개선 plan을 인과 순서로 나누고 구현→Claude 교차검증→성공 게이트를 95점 이상까지 반복 | 2026-07-23 최신 지시 | Stage 10 전체 연속 진행 |
| Claude 세션 한계 뒤 이번 세션의 남은 검증자를 Codex 서브에이전트로 교체 | 2026-07-23 최신 지시 | 10R-C~10R-H 독립 검증 수단 |

현재 구현을 차단하는 미확정 결정은 없다. 삭제·이동·legacy 대량 이관처럼 이번 범위를 넘는 행동은 제외했다.

## 10. 이전 부분 구현 기록 — 전체 완료 근거로 사용 금지

아래 기록은 실패 지식 fanout과 문서 탐색 구조를 개선한 실제 이력이다. 문서 기반 전체 데이터 요구를 검증하지 않았으므로 각 `완료`는 해당 부분 구현에만 적용되고 Stage 10 전체 완료를 뜻하지 않는다.

| 내부 단계 | 상태 | 핵심 근거 |
|---|---|---|
| 10A 목적·권한 경계 | 완료 | `PROJECT_RULES`, 요구사항 기준서, README, 단계·문서·실패 규칙에 사람의 수동 생산 작업 최소화와 에이전트 자율 실행 목적을 연결하고 보호·외부·파괴·실질 범위 확대 경계는 유지 |
| 10B 문서·탐색 구조 | 완료 | initiative owner를 이 파일 하나로 유지하고 수동 `DOCUMENT_MAP`을 router로 축약, 자동 inventory가 전체 경로를 소유, Stage 10 파생 보기·별도 Claude 보고서 생성 0 |
| 10C 실패 직접 재사용 | 완료 | canonical Markdown 직접 검증·검색·package·maintenance 경로 구현, public import·legacy refresh 비저장화, legacy 직접 ID 읽기 호환 유지 |
| 10D 통합·Claude 검증 | 완료 | Claude 실제 파일 검토와 challenge 수행, 지적한 공존·생성·개정 결합 회귀를 보강한 뒤 99개 테스트·scan·verify·실저장소 대조 통과 |
| 10E 정합화·경계 종료 | 완료 | 규칙·계약·요구사항·inventory·실패 색인·현재 핸드오프·work 상태 정합화, 보호 경로 변경 0, Stage 10 경계 커밋 대상으로 분리 |

### 10.1 구현 결과

- baseline 25개였던 해결 실패 정본은 이 단계에서 새 구조 사례 1개를 더해 26개다.
- 기존 39개 `failure_knowledge`와 관련 source·lifecycle data는 삭제하지 않고 legacy history로 보존했다.
- 새 `failure-import`는 strict UTF-8·필수 절·해결 상태를 검증한 transient view만 반환하고 `stored: false`를 명시한다.
- legacy `lifecycle-refresh-failure`도 정본을 다시 검증할 뿐 source·projection·snapshot·event를 만들지 않는다.
- context 기본 filter·search는 legacy failure/source를 제외하고 canonical 26개만 current 후보로 직접 제공한다.
- maintenance는 canonical 26개를 직접 fail-closed 검증하고 legacy projection drift를 현재 오류로 중복 보고하지 않는다.
- 수동 문서 지도는 모든 경로 목록을 소유하지 않으며 자동 inventory와 시작 owner로 연결하는 router만 유지한다.

### 10.2 Claude 교차검증과 판정

| Claude 지적·판정 | Codex 재현·판정 | 조치와 최종 근거 |
|---|---|---|
| 높음: 이 문서의 실행표·점수가 실제 구현보다 오래돼 단계 완료를 선언할 수 없음 | 수용 | §10~§11을 실제 diff·검증 결과로 갱신 |
| 중간: canonical과 같은 legacy pair가 함께 있을 때 기본 검색·scan 중복 방지 결합 테스트가 없음 | 수용 | `test_legacy_failure_coexists_without_default_search_or_drift_duplication` 추가 |
| 후속 challenge: 결합 테스트가 상태만 확인하고 생성·개정 흐름을 다루지 않을 수 있음 | 보수적으로 수용 | 한 테스트 안에서 legacy pair 생성→public import 비저장→Markdown 개정→legacy refresh 비저장→검색 1건→scan→record/event bytes 불변을 연속 검증 |
| 중간 위험: legacy failure source hash drift를 audit·scan이 보고하지 않음 | 의도된 경계로 수용 | legacy는 읽기 호환용 역사이며 현재성 owner가 아님을 `rules/failure-records.md`와 계약에 명시; 삭제·대량 이관은 이번 범위에서 제외 |
| 낮음·정보: public CLI가 private legacy 생성기를 노출하지 않고 안전 경계·문서 권위 축소가 실제 코드와 문서에 반영됨 | 확인 | 별도 조치 없음 |

`delegate-to-claude` 래퍼는 전체 프로젝트 검토에서 구조화 결과를 내기 전 종료 코드 1을 반환해, 같은 Claude CLI의 읽기 전용 안전 옵션으로 실제 파일 검토 결과를 회수했다. 이후 스킬 challenge가 한 차례 정상 완료돼 생성·개정 흐름 공백을 지적했고 그 지적까지 보강했다. 마지막 래퍼 재호출의 종료 오류는 프로젝트 구현 결함과 분리한 도구 계층 잔여 위험이며, Claude가 확인한 코드 결함을 미해결로 남기지는 않았다.

### 10.3 최종 검증 근거

| 검사 | 결과 |
|---|---|
| 번들 Python 전체 회귀 | `Ran 99 tests ... OK` |
| `maintenance-scan` | `ok=true`, drift 0, duplicates 0, inventory match |
| `maintenance-verify` | `ok=true`, errors 0, Markdown 87개·링크 624개·Python 14개·schema 13개 |
| 실제 저장소 공존 대조 | canonical 26, legacy 39, 기본 failure 후보 26, unique ref 26, legacy ID 후보 0, canonical ref 집합 일치 |
| 무증식 결합 회귀 | import·개정·refresh·검색·scan 전후 record filename과 모든 event bytes 동일 |
| 보호·외부 경계 | `inputs/`·`outputs/`·`backup/` 쓰기, 외부 쓰기, 삭제·이동·push·배포 0 |

## 11. 이전 네 가지 확인과 97점 — 철회

| 이전 주장 | 현재 판정 | 철회 이유 |
|---|---|---|
| 사용자 목적 정합성 통과 | 실패 | 모든 지속 데이터의 문서 정본 원칙을 요구사항·구현·검증에서 누락 |
| 실제 기능 작동 통과 | 부분 유효 | 실패 fanout 흐름은 작동하지만 프로젝트 전체 문서 기반 흐름은 미구현 |
| 미래 단계 선행 유입 방지 통과 | 재검토 필요 | 기존 JSON 정본을 유지한 채 문서 기반 완료를 선언해 목표 구조 경계를 잘못 설정 |
| 과거 실패 패턴 재발 방지 통과 | 부분 유효 | failure projection fanout은 방지했지만 machine-only authority 문제는 남음 |
| 총점 97/100 | 철회 | 축소된 요구만 채점했으며 알려진 핵심 결함이 있어 점수로 완료를 주장할 수 없음 |

위 철회 시점에는 현재 점수를 부여하지 않았다. 교정 작업 뒤 2026-07-24 최종 자체 재검토에서 새로 산정한 현재 점수는 이 문서 마지막 점수표의 96점이며, 이전 97점과 별개다.

## 12. 이전 인계 폐기

“Stage 10 완료 뒤 새 기능을 기다린다”는 이전 인계는 폐기됐다. 문서 기반 데이터 구조 교정은 아래 실행 기록과 자체 재검토를 거쳐 `완료 준비`에 도달했으며, 사용자 확인·경계 커밋 전 정확한 다음 행동은 `SESSION_HANDOFF.md`가 소유한다.

## 13. 교정 요구와 목표

### 13.1 사용자 원문

> 모든 지속 데이터는 문서가 정본이어야 하며 프로젝트 작업도 그 문서를 기반으로 진행해야 한다.

> 각 단계별로 성공게이트 통과하기 전 Claude와 교차검증을 거쳐서 성공 여부를 판별한다.

> 클로드의 세션이 100% 사용으로 한계에 도달했다. 이번 세션에서 앞으로 작업의 교차검증은 Codex 서브에이전트를 통해서 검증하도록 수정한다.

> 서브 에이전트를 너무 남발하지 말고, 1개의 작업에 1개의 서브에이전트만 교차검증 용도로 사용한다.

> 검증을 위한 서브에이전트는 항상 과거에 대한 내용을 모르는 상태로 결과물만 가지고 교차검증하는 데 사용한다.

> 이번 작업에서는 실행 중인 서브에이전트를 중단하고 교차검증을 제외해 주 작업 Codex가 스스로 재검토한다.

### 13.2 목표 상태

1. 계획, 요구, 현재 상태, 지식, 결정, 실패, 출처 메타데이터, 작업 근거는 사람이 읽을 수 있는 문서 하나가 활성 정본으로 소유한다.
2. JSON·JSONL·schema·record·event·snapshot·index·inventory는 문서에서 결정적으로 재생성 가능한 파생물 또는 명시된 read-only legacy다.
3. 기계 파일에만 존재하는 활성 사실은 0개다.
4. 에이전트는 정확한 문서 owner를 읽고 작업을 시작하며 완료 전에 같은 owner에 결과·근거·실패·검증·다음 행동을 반영한다.
5. 기존 기계 데이터는 삭제하지 않고 정보 손실 없는 migration 검증 전까지 legacy로 보존한다.
6. 독립 교차검증이 적용되는 작업은 성공 게이트보다 먼저 이를 통과한다. 2026-07-24 사용자는 현재 Stage 10 잔여 종료 작업에 한해 실행 중 서브에이전트를 중단하고 교차검증을 주 작업 Codex 자체 재검토로 대체했다.

## 14. 데이터 분류 계약

| 분류 | 정의 | 허용 조건 | 금지 |
|---|---|---|---|
| 문서 정본 | 사람이 읽고 에이전트가 직접 작업 근거로 사용하는 유일한 활성 owner | 목적·읽는 시점·소유 데이터·갱신 조건 명시 | 같은 활성 사실의 두 번째 정본 |
| 문서 파생물 | 문서에서 결정적으로 다시 만들 수 있는 기계 파일 | owner link·생성 규칙·재생성 검증 존재 | 문서에 없는 활성 사실 저장 |
| legacy 역사 | 이전 구조의 감사·호환용 read-only 데이터 | 기본 작업 경로 제외·쓰기 중단·보존 이유 명시 | 새 활성 사실 추가, 현재성 판단 |
| 일시 실행 데이터 | 작업 중에만 존재하고 안전하게 폐기 가능한 데이터 | 재개·감사·지식·현재 상태에 사용하지 않음 | 지속 owner 또는 완료 근거로 사용 |

## 15. 단계 공통 실행·독립 검증·게이트 순서

10R-A~10R-H의 각 단계는 예외 없이 다음 순서를 따른다.

1. 해당 단계의 문서 owner·범위·제외·입력·보호 경계를 확인하고 정확한 owner를 읽는다. `(UR-19)`
2. 승인 범위 안의 작업을 수행하고 결과·실패·검증 근거·보고·요청·확인 상태를 이 문서에 기록한다. `(SR-11; UR-13, UR-15, UR-17, UR-19)`
3. 구현·보완과 로컬 통합 검증을 모두 끝낸 최종 결과에 한해, 과거 대화가 상속되지 않은 신규 Codex 서브에이전트 **한 명만** 읽기 전용 검증자로 만든다.
4. 검증자에게는 현재 요구·범위·성공 게이트, 최종 결과물 또는 diff, 완료된 테스트 증거, 현재 명시한 미해결 위험과 판정 계약만 제공한다. 과거 findings·수정·재시도 이력이나 원하는 판정은 제공하지 않는다.
5. 독립 findings를 주 작업 Codex가 실제 파일·코드·테스트로 재현해 `수용 / 기각 / 잔여 위험`으로 판정한다.
6. High·Medium 지적이 수용되면 게이트를 실패로 기록하고 자동 수정→재검증 반복을 중단한다. 결과물을 바꾼 뒤 검증이 다시 필요하면 그것은 새 검증 작업이며, 같은 검증자를 재사용하지 않고 별도 권한 안에서 새 blind 검증자 한 명을 사용한다.
7. 독립 검증 High·Medium 미해결 지적 0, 검증 실패 0, 미기록 실패 0일 때만 해당 단계 성공 게이트를 판정한다.
8. 사용 가능한 독립 검증 결과가 없으면 교차검증 미실행으로 처리하고 성공 게이트를 통과시키지 않는다.

각 검증 작업의 독립 결과와 주 작업 Codex 판정은 이 문서의 해당 실행 기록에 누적한다. 검증 작업 하나에 서브에이전트를 둘 이상 사용하지 않는다. 과거 Claude·Codex 결과는 검증자 입력이 아니라 당시 시점의 역사 증거로만 보존한다. 별도 보고서는 사용자가 명시적으로 요구하거나 독립 감사 독자가 필요한 경우에만 만든다.

현재 Stage 10 잔여 종료 작업은 사용자 최신 예외에 따라 위 독립 검증 단계를 적용하지 않는다. 시작된 신규 blind 서브에이전트는 결과를 반환하기 전에 중단했고 그 판단을 게이트 근거로 사용하지 않는다. 대신 주 작업 Codex가 전체 최종 diff, 활성 요구, 보호 경계, 문서 정합, 로컬 회귀와 점수표를 직접 재검토한다. 이 예외는 다른 작업으로 자동 확대하지 않는다.

## 16. 10R-A~10R-H 인과 작업 계획

| 순서 | 단계 | 선행 이유 | 작업 | 검증 초점 | 성공 게이트 | 현재 상태 |
|---:|---|---|---|---|---|---|
| 1 | 10R-A 상태 진실화 | 잘못된 완료 상태를 먼저 제거해야 후속 판단이 오염되지 않음 | Stage 10·핸드오프·감사 보고서의 완료·97점 철회, 유효·무효 증거 분리 | 모든 현재 owner가 같은 상태를 말하는지, 숨은 완료 주장이 남았는지 | 상태 충돌 0, 현재 점수 없음, 첫 다음 행동 일치 | **통과** — Claude 최종 PASS·High 0·Medium 0, Low 보완 완료 |
| 2 | 10R-B 요구·규칙 추적 | 전체 데이터 조사 기준이 먼저 고정돼야 분류가 흔들리지 않음 | 사용자 원문을 요구사항 기준서에 추가하고 `PROJECT_RULES`·라우팅·데이터 작업 규칙과 일대일 연결 | 원문 축소·예외 확대·규칙 중복 여부 | 사용자 원문→요구→규칙→게이트 추적 누락 0 | **통과** — 1/2 PASS·High 0·Medium 0·Low 0, 2/2 지적 보완·최종 파일 결함 High 0·Medium 0 |
| 3 | 10R-C 활성 데이터 전수 분류 | 목표 구조·migration은 현재 owner와 소비자를 알아야 설계 가능 | 보호·역사 경계를 지키며 활성 Markdown·JSON·JSONL·schema·inventory의 owner·writer·reader·고유 사실 전수표 작성 | 누락 데이터 유형, machine-only 사실, 잘못된 정본 분류 | 활성 지속 데이터 100%가 네 분류 중 하나, 미분류 0 | **통과** — 최종 독립 PASS·High 0·Medium 0·Low 0, 346/346경로·322 지속 데이터·211 record·193 event·X01 11/22·미분류 0 |
| 4 | 10R-D 목표 구조·migration 설계 | 분류 결과가 있어야 정보 손실 없는 순서를 결정 가능 | 문서 owner 모델, 파생 생성 규칙, legacy 격리, 호환·rollback, migration 단계 설계 | 복수 정본·정보 손실·새 fanout·숨은 수동 작업 | machine-only 활성 사실 0을 달성할 실행 가능한 mapping, 삭제 없는 rollback 검증 | **통과** — 1차 FAIL H0/M6/L1과 재검증 FAIL H0/M1/L0 전부 보완, 같은 검증자 최종 PASS H0/M0/L0 |
| 5 | 10R-E 문서 우선 코드·CLI·테스트 | 목표 구조가 확정된 뒤에만 writer·reader를 변경 가능 | 문서 parser/writer, doc-first CLI, 파생 rebuild, machine-only write 차단, 대표 회귀 구현 | 우회 쓰기 경로, 문서 없는 상태 생성, 재생성 불가능성 | 대표 작업이 문서 읽기→문서 갱신→파생 재생성으로 성공, 우회 쓰기 실패 | **통과** — 1차 FAIL H1/M4·재검증 FAIL H0/M2 전부 보완, 같은 검증자 최종 PASS H0/M0/L0, 115 tests |
| 6 | 10R-F legacy 격리·문서 이관 | 새 경로가 먼저 작동해야 기존 데이터를 안전하게 전환 가능 | 기존 JSON을 보존한 채 read-only legacy 표식, 문서 정본 이관, 기본 경로 legacy 의존 제거 | ID·관계·시간·근거 손실, 기본 경로의 숨은 legacy read | 정보 손실 0, 기본 writer/read 의존 0, legacy 새 쓰기 0, rollback 가능 | **통과** — test capability를 검증된 임시 root에 결합하고 active source project·타 root 재사용을 fail-closed로 거부함 |
| 7 | 10R-G 전체 사용자 요구 검증 | 모든 실제 diff와 migration 결과가 있어야 전체 검증 가능 | SR-01~SR-27 추적표와 전체 활성 경로를 검증 | 문서 기반 전체 운영, 자율성, 보고, fanout, 역사 실패 재발 | High·Medium 미해결 0, 모든 지적 판정 완료 | **통과** — 사용자 예외에 따른 최종 자체 재검토 High 0·Medium 0·Low 0 |
| 8 | 10R-H 최종 게이트·종료 | 부분 게이트가 모두 통과한 뒤에만 전체 점수와 상태를 닫을 수 있음 | 네 가지 확인, 전체 회귀, maintenance, 문서·work·Git 정합화, 95점 이상 재산정 | 완료 주장과 실제 증거의 마지막 반례 | 미검증 요구 0, 차단 결함 0, 총점 95 이상, 사용자 확인, 경계 커밋 성공 | **완료 준비** — 자체 96점·차단 결함 0. 사용자 확인과 경계 커밋 대기 |

10R-G는 원래 전체 범위 최종 교차검증 단계였으나 2026-07-24 사용자 최신 지시에 따라 현재 작업에서 제외됐고 전체 diff 자체 재검토로 대체됐다. 이 현재 작업 예외는 기존 역사 판정을 바꾸거나 다른 작업의 blind 검증 정책을 폐기하지 않는다.

## 17. 10R-C 전수 분류표 계약

각 활성 지속 데이터 대상은 다음 열을 모두 가져야 한다.

| 필드 | 기록 내용 |
|---|---|
| 경로·유형 | Markdown, JSON, JSONL, schema, inventory, source code/config |
| 현재 소유 사실 | 해당 파일만 알고 있는 요구·상태·관계·근거 |
| 현재 writer·reader | 생성·갱신·소비 코드와 CLI |
| 현재 권위 | active canonical, derived, legacy, temporary 중 실제 동작 |
| 목표 분류 | §14의 네 분류 중 하나 |
| 문서 owner | 사람이 읽을 수 있는 정확한 정본 경로 |
| trace·rebuild | 문서에서 파생물을 재생성하고 검증하는 방법 |
| migration action | 유지, 파생화, legacy 격리, 문서 이관 |
| 보호·삭제 경계 | 접근 금지, read-only, 승인 필요 여부 |
| 검증 증거 | 테스트·hash·count·대표 흐름 |

전수 분류는 `inputs/`, `outputs/`, 비밀정보를 열거하거나 읽지 않는다. `backup/`은 새 조사가 필요한 특정 근거가 없으면 추가 열람하지 않는다.

## 18. migration 원칙

- 문서 owner를 먼저 만들고 검증한 뒤 writer를 문서 우선으로 전환한다.
- 기존 JSON·JSONL은 삭제·덮어쓰기하지 않고 legacy read-only로 보존한다.
- ID, 시간, 출처, 관계, 대체 이력, 승인 근거의 정보 손실 여부를 유형별로 검증한다.
- 기본 read·write 경로에서 legacy 의존을 제거한 뒤에만 정리 후보를 보고한다.
- 파생물은 문서에서 같은 bytes 또는 의미적으로 같은 validated payload를 재생성할 수 있어야 한다.
- migration 중 dual-write를 영구 구조로 만들지 않는다. 불가피한 임시 dual-read는 종료 조건과 제거 테스트를 먼저 가진다.
- 실패 시 Git과 보존 legacy로 이전 동작을 재구성할 수 있어야 한다.
- 삭제·이동·대량 변환은 이 계획 작성만으로 승인된 것이 아니며 실제 필요 시 정확한 대상·영향을 확인한다.

## 19. 대표 검증 시나리오

1. 새 작업: 요구 문서 읽기 → 단계 owner에 계획 기록 → 작업 → 결과·검증·다음 행동 갱신 → 파생 상태 재생성.
2. 새 지식: 문서 owner에 출처·주장·상태 기록 → 검색 파생물 재생성 → 다음 세션에서 문서 근거로 재사용.
3. 실패 재발: 기존 실패 Markdown 갱신 → 직접 검증·검색 → 새 projection/source/state/event 0.
4. 결정 변경: 이전 결정 문서를 보존하고 대체 문서·링크 갱신 → 파생 index에서 current 하나만 선택.
5. 세션 재개: startup 3문서만으로 현재 목표·blocker·첫 행동 재구성 → 기계 snapshot 고유 사실 0.
6. 파생 재생성: 생성 대상의 현재 내용을 별도 비교 위치에서 다시 만들고 정본과 의미·hash 대조.
7. legacy 차단: public CLI가 legacy에 새 active fact를 쓰지 못하고 기본 검색·현재성 판단이 문서 owner만 사용.

## 20. 단계별 독립 검증 계약

각 단계 prompt는 다음을 반드시 포함한다.

- 통합 요구사항 기준서 §2.3의 최신 사용자 원문 전체와 해당 단계의 SR·UR 요구 추적표
- 해당 단계 목표·범위·제외·성공 게이트
- 변경 전후 문서 owner와 machine artifact mapping
- 최종 결과물 또는 실제 diff와 완료된 테스트 결과
- 실패·우회·미검증·보호 경계·미확정 위험
- “요구를 축소하지 말고 반례와 누락을 우선 찾으라”는 지시
- 과거 대화·이전 findings·수정·재시도 이력과 원하는 verdict를 제공하지 않는다는 입력 제한

위 입력의 위험 분류는 다음 계약을 사용한다.

| 분류 | 판정 기준 | 독립 검증자에 제공할 내용 |
|---|---|---|
| 실패 | 시도한 명령·도구·작업이 기대 결과를 만들지 못함 | 증상, 시도, 실제 결과, 현재 상태 |
| 우회 | 원래 계약을 충족하지 않고 다른 경로로 결과만 얻음 | 우회 경로, 원 계약 미충족 부분, 제거 조건 |
| 미검증 | 구현·주장이 존재하지만 필수 검사나 재현을 실행하지 않음 | 미실행 검사, 이유, 필요한 증거 |
| 보호 경계 | 보호 데이터·외부·파괴·비용·권한 때문에 접근이나 행동이 제한됨 | 정확한 경계, 제외 범위, 현재 승인 상태 |
| 미확정 위험 | 범위·권한·보호·설계·증거·검증 중 확인되지 않은 요소가 결과나 게이트 판정을 바꿀 수 있음 | 근거 공백, 가능한 영향, 해소 방법, 사용자 결정 필요 여부 |

하나의 사실이 여러 분류에 해당하면 모두 표시한다. 단순히 가능성이 있다는 이유만으로 미확정 위험을 만들지 않고, 결과나 게이트가 바뀔 수 있는 구체적 근거 공백이 있을 때만 기록한다.

독립 검증 결과는 severity, file, line 또는 정확한 근거, 재현 방법, 남은 위험을 가져야 한다. 주 작업 Codex는 결과를 자동 수용하지 않고 실제 근거로 판정한다. 단, 근거 없는 기각도 허용하지 않는다. 이번 세션에는 Claude 추가 호출을 하지 않는다. 최종 결과가 준비된 뒤 과거 맥락을 상속하지 않은 신규 Codex 서브에이전트 한 명만 사용하며, 검증 뒤 결과물이 바뀌면 같은 검증자를 재사용하지 않는다.

## 21. 작업별 성공 게이트

각 10R 단계는 §15의 적용 가능한 검증을 통과한 뒤 다음 공통 항목을 확인한다. 현재 잔여 종료 작업은 사용자 최신 예외에 따라 독립 검증 대신 주 작업 Codex 자체 재검토를 적용한다.

| 확인 | 통과 조건 |
|---|---|
| 요구 정합성 | 해당 단계 활성 SR 전체가 산출물·테스트와 연결 |
| 실제 작동 | 대표 정상·실패 흐름을 활성 경로에서 실행 |
| 문서 정본 | 10R-A~10R-D는 해당 범위의 기존 machine-only debt·owner gap 100% 공개와 새 machine-only fact 0, 10R-E는 문서 우선 대표 흐름과 새 우회 write 0, 10R-F~10R-H는 machine-only active fact 0과 owner·trace·rebuild 확인 |
| 범위·안전 | 보호·역사·외부·삭제 경계 위반 0 |
| 실패 재발 | 관련 canonical failure와 회귀 검증 연결 |
| 검증 판정 | 독립 검증 적용 시 High·Medium 미해결 0. 현재 사용자 예외 작업은 전체 diff 자체 재검토에서 High·Medium·Low 미해결 0과 예외 근거 기록 |
| 상태 정합성·보고 `(SR-11; UR-13, UR-15, UR-17, UR-19)` | 단계 owner·핸드오프·파생 상태가 같은 사실을 표현하고 중요한 진행·실패·게이트·위험·사용자 결정 필요 여부를 보고 |

한 항목이라도 실패면 그 단계는 `통과`가 아니며 다음 단계에 의존 결과를 넘기지 않는다.

## 22. 전체 완료·점수 게이트

- 10R-A~10R-H의 적용 가능한 검증과 성공 게이트가 모두 통과한다. 현재 잔여 종료 작업의 독립 교차검증은 사용자 최신 예외로 자체 재검토가 대체한다.
- 활성 지속 데이터 전수 분류 100%, 미분류 0, machine-only active fact 0을 확인한다.
- 대표 시나리오 7개와 전체 회귀·maintenance가 성공한다.
- SR-01~SR-27에 미구현·미검증 항목이 없다.
- 현재 사용자 예외에 따른 전체 diff 자체 재검토의 High·Medium·Low 미해결 지적이 0이다.
- 마스터 계획 §6.3 네 가지 확인을 새 증거로 다시 수행한다.
- 마스터 계획 §6.4 점수를 처음부터 다시 산정하고 95점 이상이어야 한다.
- 알려진 차단 결함은 점수와 무관하게 실패다.
- 사용자 확인과 버전 관리 규칙에 따른 Stage 10 교정 경계 커밋이 성공한 뒤에만 `완료`를 기록한다.

## 23. 범위·현재 다음 행동

### 포함

- 활성 규칙·요구사항·계획·현재 상태·계약·코드·CLI·테스트
- 보호 경계를 제외한 활성 Markdown·JSON·JSONL·schema·inventory의 owner·writer·reader 분류
- 문서 정본·파생 rebuild·legacy 호환 설계와 검증
- 적용 가능한 단계의 독립 읽기 전용 교차검증과 현재 사용자 예외 작업의 전체 diff 자체 재검토

### 제외

- `inputs/`, `outputs/` 열거·열람
- `backup/` 수정·활성 의존
- 검증 전 legacy 삭제·병합·덮어쓰기
- push·배포·외부 게시
- 새 DB·검색 서비스·플러그인·예약 작업의 선행 도입
- 유튜브 제작 기능 확장

### 첫 다음 행동

2026-07-23 교차검증 호출 기록:

- 첫 호출은 호출자가 스킬의 `ExecutionPolicy Bypass` 형식을 누락해 PowerShell이 래퍼를 로드하지 못했다. 이는 사용자 작업 승인이나 프로젝트 결함이 아니다.
- 형식을 바로잡은 읽기 전용 Claude 호출은 제한된 실행 환경에서 120초 동안 결과 없이 종료됐다.
- 외부 네트워크 승인 경로 재시도는 지정 프로젝트 문서를 외부 Claude 서비스에 전송하는 정확한 payload에 대한 별도 명시 동의가 없다는 승인 검토 결과로 거절됐다.
- 사용자 재지시 뒤 두 현재 owner만 대상으로 최소화한 후속 호출은 외부 실행 셀 제한 시간을 넘겼지만, 종료 출력 안에 `status: completed`, `terminal_reason: completed`, `FINAL VERDICT: PASS`인 구조화 결과를 반환했다. 파일 변경은 없고 High 0·Medium 0·Low 1이다.
- Claude는 완료·97점 철회, 현재 점수 없음, 8단계별 Claude 선행 게이트, 미구현 migration 비완료 표시가 두 owner에서 일치한다고 판정했다.
- Low 1건은 두 감사 보고서가 활성 owner처럼 남을 수 있다는 위험이다. Codex는 두 보고서를 끝까지 다시 읽었고, `reports/`는 시점 감사 증거이며 현재 상태 owner가 아니라는 경계를 각 보고서에 명시한다.
- Codex 독립 재현에서 Claude가 부분 열람으로 놓친 감사 보고서 §8의 오래된 “Stage 10 문서·핸드오프에 완료 표시가 남음” 문장을 발견해 현재 사실로 교정한다.
- 보완 후 Claude 재검증은 다시 PASS, High 0·Medium 0이며 1차 Low의 owner 중복 위험이 해소됐다고 판정했다.
- 재검증의 새 Low 1건은 이 문서 상단 상태가 “계획 완료·구현 전”으로만 표시돼 실제 10R-A 진행 수준보다 모호하다는 지적이다. Codex는 이를 수용해 10R-A 재검증 단계와 10R-B~10R-H 대기 상태를 상단에 명시했다.
- Codex 전수 검색에서 유지관리 문서의 Stage 10 `완료·97점` 표현은 모두 철회·금지·과거 시점 문맥이고, `DOCUMENT_MAP`은 이 문서만 현재 initiative owner로 지정하며 생성 inventory는 두 보고서를 단순 전체 목록으로만 포함한다.
- 마지막 최소 범위 Claude 확인도 PASS, High 0·Medium 0이다. 새 Low는 10R-A 행에 명시적 게이트 상태가 없다는 지적이며, 이 행과 상단·핸드오프를 함께 `통과`로 갱신해 해소했다.
- Claude 결과의 “이 확인이 실제 외부 호출이 아닐 수 있다”는 위험 문구는 실행 사실과 충돌해 기각했다. 이 검증은 `delegate-to-claude` 스킬의 실제 외부 읽기 전용 호출로 수행됐고 `status: completed`, `terminal_reason: completed`, 파일 변경 0인 구조화 결과를 반환했다.

10R-A 성공 게이트 판정은 **통과**다. 근거는 상태 충돌 0, 현재 점수 없음, 첫 다음 행동 일치, Claude 최종 PASS, High·Medium 미해결 0, Low 보완 완료다.

### 10R-B 작업 기록

- 통합 요구사항 기준서의 최신 사용자 원문에 폴더·파일·문서 연결 최적화, 모든 데이터의 문서 기반 작업, 단계별 Claude 선행 검증 발언을 추가했다.
- UR-18은 모든 지속 데이터의 문서 정본과 machine-only active fact 0, UR-19는 문서 owner 읽기·갱신 기반 실행과 보고·요청·확인, UR-20은 현재·역사 구조와 fanout 최적화, UR-21은 단계별 Claude·Codex·게이트·95점 반복을 소유한다.
- SR-01~SR-24를 활성 의미·UR·규칙·절차 owner·Stage 10 게이트에 전부 연결했다.
- 조건부였던 다중 에이전트 QA O-09를 Stage 10에만 활성화하고 다른 단계 일반 확대는 금지했다.
- 요구사항 기준서 끝의 동적 “Stage 00~09 완료” 소유를 제거하고 현재 상태는 `SESSION_HANDOFF.md`, Stage 10 내부 실행 상태는 이 문서가 소유하도록 교정했다.
- `PROJECT_RULES.md`의 purpose/document-based data/authority/verification, `AGENTS.md`의 stage·document·history·failure routing, `rules/document-work.md`의 owner-first·trace·rebuild 절차가 UR-18~UR-21을 실행할 수 있어 추가 규칙 복제는 하지 않았다.
- 로컬 구조 확인은 UR 21행, SR 24행, UR-18~UR-21 존재, 동적 상태 owner 제거, UTF-8 NUL 0을 확인했다.
- Claude 10R-B 1/2는 SR 24행 존재와 원문 보존을 확인했지만, UR-21에 Claude 입력으로 사용자 원문 전체·요구 추적표를 제공한다는 조건이 빠졌다고 Medium 1을 판정했다. SR-04의 “선택한 역사 증거”가 문제 범위를 축소할 수 있고 최종 문서·handoff·work·Git 정합성이 UR-21에 재진술되지 않았다는 Low 2도 제시했다.
- Codex는 세 지적을 모두 수용해 UR-21 수용 기준과 SR-04 활성 의미를 보완했다. 이 변경은 같은 원문→요구 범위의 Claude 재검증 전에는 통과로 계산하지 않는다.
- Claude 10R-B 1/2 재검증은 PASS, High 0·Medium 0·Low 0으로 세 지적의 해소와 SR 24행 전체 추적을 확인했다.
- Claude 10R-B 2/2는 UR-18~UR-20 연결과 모든 인용 파일의 존재를 확인했지만, 강화된 UR-21의 “최신 사용자 원문 전체·요구 추적표”가 이 문서 §15·§20 Claude 입력 계약에 전파되지 않았다고 Medium 1을 판정했다. SR-11 게이트 인용의 모호성, 상시 원칙과 task procedure의 중복 가능성, 기준서의 축약된 규칙 제목 인용을 Low 3으로 판정했다.
- Codex는 Medium을 수용해 §15·§20을 UR-21과 정확히 동기화했다. Low 3도 수용해 SR-11을 §15·§21에 연결하고, 기준서의 모든 `PROJECT_RULES.md` 인용을 실제 절 제목으로 고치며, `rules/document-work.md`는 상시 원칙을 복사하지 않고 artifact 분류·owner·rebuild를 기록하는 절차로 축약했다.
- Codex는 `rules/history-review.md`와 `rules/failure-records.md`를 끝까지 다시 읽어 SR-04·SR-07 인용이 실제 선별 역사 검토·fanout 방지 절차와 일치함을 확인했다.
- 2/2 보완 재검증은 같은 목표에서 Sonnet 래퍼 종료 코드 1·구조화 결과 없음이 세 번 연속 발생했다. 첫 재시도는 전체 6문서, 두 번째는 네 지적만, 세 번째는 기준서·Stage 10 두 문서로 범위를 줄였지만 각각 사용 가능한 결과가 없었다. 최고 연속 실패 수는 3이다.
- 확정된 사실은 Claude Code 프로세스가 결과 schema를 반환하기 전에 nonzero로 끝났고 래퍼가 원시 출력을 보존하지 않는다는 점이다. 근본 원인은 아직 확정하지 않았으며 보완 자체를 통과로 처리하지 않는다.
- 즉시 위험은 Medium 1이 실제로 해소됐는지 외부 검증되지 않은 상태에서 10R-B를 닫을 수 있다는 것이다. 재시작 조건은 같은 문서와 네 질문을 유지하되 더 작은 Claude 모델로 구조화 판정만 먼저 회수하고, Codex가 Sonnet의 원 지적과 직접 대조하는 것이다.
- 더 작은 Claude 모델의 최소 구조화 검증은 정상 완료돼 재시작 조건을 충족했다. 다만 결과 요약의 심각도 수와 실제 findings 배열의 심각도 수가 서로 달라 Codex는 각 finding을 파일 근거로 개별 판정했다.
- Codex 수용: §20에 `미확정 위험` 명시, §15·§21에 SR-11·UR-19의 보고·요청·확인 역참조와 게이트 조건 추가, document-work 첫 규칙을 owner 경로·읽은 절·결과 기록 절차로 축약.
- Codex 기각: “Sonnet 검증 실패 때문에 현재 보완 확인 불가”는 이 Haiku 호출 자체가 성공한 뒤에도 과거 상태를 현재 blocker로 사용한 자기모순이다. Sonnet 세 실패는 도구 위험 이력으로 보존하지만 이 성공 결과의 파일 검증을 무효화하지 않는다.
- 후속 Haiku challenge는 구조화 결과를 반환했고 `미확정 위험`의 식별·보고 계약 부재, SR-11이 근거로 삼는 UR-13·UR-15·UR-17·UR-19 전체의 역참조 부족, document-work에 남은 문서 생성·배치·중복 금지 정책 문장을 지적했다.
- Codex는 해당 지적을 수용해 §20에 실패·우회·미검증·보호 경계·미확정 위험 분류 계약을 추가하고, §15 step 1에 owner 읽기, step 2와 §21에 SR-11 및 네 UR 전체를 연결했다. document-work는 `PROJECT_RULES.md`의 정책 절을 참조하고 update/new-document/directory 선택 증거를 기록하는 절차만 소유하도록 다시 축약했다.
- Sonnet 최종 검증은 위험 분류와 SR-11 전체 연결을 PASS로 확인했지만, document-work가 migration debt와 disposable runtime 상시 정책을 두 줄 더 재서술한다고 Medium 2를 판정했다. 핸드오프 §7의 동일한 다음 행동 두 줄도 Low 1로 확인했다.
- Codex는 Medium 2를 수용해 document-work가 artifact owner 경로·rebuild command·verification method·evidence gap 정지 절차만 기록하도록 바꾸고 disposable runtime 정책 복사를 제거했다. Low 1도 수용해 핸드오프 중복 다음 행동을 삭제했다.
- 마지막 Claude review는 실제 `rules/document-work.md`가 절차만 소유하고 `SESSION_HANDOFF.md` §7 중복이 제거됐음을 직접 확인했다. 동시에 “Claude 재검증이 아직 실행되지 않았다”는 이유로 High·Medium을 부여했으나, 현재 `status: completed` review가 그 재검증 자체이므로 해당 process-state findings는 자기모순으로 기각했다.
- 같은 review의 “현재 maintenance 미실행” finding도 마지막 변경 뒤 maintenance-verify `documents 89`, `links 647`, Python 14, schema 13, errors·drift·duplicates 0, inventory match와 diff-check PASS를 실제 실행했으므로 기각했다.
- 10R-B 최종 판정: 사용자 원문→UR-18~UR-21→SR-01~SR-24→실제 규칙 절→Stage 10 §15~§22 추적 누락 0, 유효한 파일 결함 High 0·Medium 0, 기록된 Low 보완 완료.

10R-B 성공 게이트 판정은 **통과**다.

10R-B 통과 직후의 다음 행동은 10R-C에서 보호·역사 경계를 지키며 활성 Markdown·JSON·JSONL·schema·inventory의 현재 owner·writer·reader·고유 사실을 전수 분류하는 것이었다. 그 분류표는 §10R-C에 작성됐고, 현재는 독립 Codex 서브에이전트 교차검증과 주 작업 Codex 보완 전이므로 10R-C를 통과시키지 않는다.

### 10R-C 전수 분류 실행 기록

#### 조사 방법과 경계

- 파일 표면은 `git ls-files`와 `git ls-files --others --exclude-standard`에서 시작했다.
- 경로를 출력하거나 파일을 읽기 전에 segment가 `inputs`, `outputs`, `backup`인 항목을 제외했다.
- 보호 경계 밖 활성 경로는 346개다: Markdown 89, JSON 231, JSONL 2, Python 22, 저장소 설정 2.
- 유지 문서 89개는 root 4, `rules/` 6, `docs/*.md` 8, `docs/build/` 13, `docs/domain/` 1, 수동 Obsidian 4, 생성 inventory 1, Stage 00~09 Obsidian 보기 11, `failures/` 27, `reports/` 14로 분해했다.
- `data/records` 211개는 공통 외피와 payload shape를 모두 파싱했다. 유형은 decision 1, failure_knowledge 39, knowledge 11, lifecycle_state 101, source 50, work_state 9다.
- `data/events`는 work 36행, lifecycle 157행이다. 실패 projection ID와 source ID 관계로 lifecycle 114행을 legacy failure 계열, 43행을 나머지 계열로 분리했다.
- 분류에서 source code·test·repository config도 빠짐없이 경로 표면에 포함하지만, 지속 프로젝트 데이터가 아니라 구현 artifact로 별도 표시한다.

#### 경로 표면 전수표

같은 owner·writer·reader·분류 계약을 가진 경로만 한 행으로 묶었다. `C`는 문서 정본, `D`는 문서 파생, `L`은 read-only legacy, `I`는 지속 프로젝트 데이터가 아닌 구현 artifact다. `D-gap`은 목표가 문서 파생이지만 현재 generator 또는 rebuild가 없어 migration debt인 상태다.

| ID | 경로·유형·수 | 현재 소유 사실 | writer·reader | 현재 권위 | 목표 분류·문서 owner | trace·rebuild | migration action·경계·증거 |
|---|---|---|---|---|---|---|---|
| C01 | root Markdown 4 | startup routing, 상시 규칙, 현재 상태, entry map | 사용자·에이전트 / session startup | `C` | `C`; 각 파일이 헤더에 선언한 고유 책임 | 수동 유지·상호 링크·maintenance | 유지. `AGENTS`, `PROJECT_RULES`, `SESSION_HANDOFF`, `README`; UTF-8·링크 검증 |
| C02 | `rules/*.md` 6 | stage·failure·document·history·version-control·user-data task 절차 | 사용자 승인 정책·에이전트 / routed task | `C` | `C`; 각 rule 파일 | `AGENTS.md` routing에서 선택 | 유지. 상시 원칙 복제 금지; 실제 파일 6 확인 |
| C03 | `docs/*.md` 8 | 정보 구조와 file/work/knowledge/lifecycle/context/maintenance 계약 | 에이전트 / code·test·stage work | `C` | `C`; 각 contract | code·schema·test가 링크·대조 | 유지. 계약별 schema·runtime mapping은 10R-D에서 확정 |
| C04 | `docs/build/*.md` 13 | master 순서와 Stage 00~10 결정·계획·검증·점수 역사 | 에이전트 / stage work·resume | `C` | `C`; master와 각 stage owner | Git·handoff·문서 링크 | 유지. 동적 current는 handoff만 소유 |
| C05 | `docs/domain/**/*.md` 1 | YouTube evidence request·pack 계약 | 에이전트 / youtube adapter·test | `C` | `C`; `YOUTUBE_EVIDENCE_PACK_CONTRACT.md` | schema·runtime test 대조 | 유지. 도메인 확장 금지 |
| C06 | 수동 Obsidian Markdown 4: `START_HERE`, `DOCUMENT_MAP`, `OBSIDIAN_REVIEW_CONTRACT`, `stages/README` | 시작 router, category owner map, review 계약, stage view 설명 | 에이전트 / 사용자·agent navigation | `C` router/contract | `C`; 각 파일의 navigation 책임 | canonical owner로 링크만 보유 | 유지. 현재 사실 복제 금지 |
| C07 | generated inventory Markdown 1 | 활성 Markdown path·H1 전체 목록 | `MaintenanceService.write_inventory` / maintenance·navigation | `D` | `D`; owner `docs/MAINTENANCE_AUTOMATION_CONTRACT.md` | maintenance write/verify로 bytes 재생성 | 유지. 현재 12,535 bytes match |
| C08 | `docs/obsidian/stages/stage-*.md` 보기 11 | Stage 00~09의 link-only 완료 시점 보기 | 과거 stage close / Obsidian navigation | `D-gap` | 10R-D 결정으로 `L`; owner 각 `docs/build/stage-*.md` | 새 generator 없음 | 완료 시점 역사 보기로 read-only 유지, 현재 상태 판단 금지, Stage 10 이후 새 보기 0 |
| C09 | `failures/*.md` 27 | index 1과 resolved failure canonical body 26 | 에이전트·failure parser / context·maintenance | `C` | `C`; 각 failure Markdown | direct parse·validate·search | 유지. per-case projection 새 생성 0 |
| C10 | `reports/*.md` 14 | 요구 기준 1과 시점 분석·감사 증거 | 에이전트 / audit·decision support | `C` 시점 증거 | `C`; 각 report의 고유 audit 범위 | 현재 상태 owner로 사용 금지, owner link | 유지. 활성 요구 기준서는 요구만 소유 |
| C11 | `data/records/*.json` 211 | ID·시간·payload·관계·상태·근거 locator | `RecordStore`, knowledge/lifecycle/work services·CLI / context·maintenance | `L`과 invalid machine authority 혼재 | 전부 `L` 목표; 세부 owner는 아래 D01~D09 | 현재 JSON에서만 재생 가능한 사실 존재 | 새 write 차단·문서 이관 뒤 read-only 격리. 삭제·덮어쓰기 금지 |
| C12 | `data/events/*.jsonl` 2 | work 36·lifecycle 157 사건과 순서·시간·actor | `RecordStore.append_event`, work/lifecycle services / replay·maintenance | invalid active machine canonical | 전부 `L` 목표; 세부 owner는 아래 D04·D09·D11 | append-only replay만 존재, 문서 rebuild 없음 | 새 write 차단·문서 이관 뒤 read-only 격리. bytes 보존 |
| C13 | `schemas/*.json` 13 | 공통·work·knowledge·lifecycle·context·YouTube payload 구조 | 수동 schema edit / tests·maintenance | `D-gap` | `D`; owner C03·C05의 해당 contract | runtime 상수와 test 대조만 있고 doc→schema generator 없음 | 10R-D에서 generator 또는 검증 가능한 mapping 설계 |
| C14 | `.obsidian/app.json` 1 | shared preview·ignore filter 설정 | 수동 config / Obsidian | `D-gap` | `D`; owner `OBSIDIAN_REVIEW_CONTRACT.md`와 보호 규칙 | generator 없음 | 문서→config mapping·rebuild 설계, local UI state 제외 유지 |
| C15 | `examples/**/*.json` 1 | Stage 09 대표 request의 video·document·record 선택값 | 수동 example / youtube adapter·test·user example | machine-only example | `D-gap`; owner Stage 09 문서·YouTube contract | schema validation만 있고 doc owner/rebuild 없음 | 사람 읽는 example owner 또는 legacy 분류를 10R-D에서 결정 |
| C16 | `tests/fixtures/**/*.json` 5 | valid/invalid record byte fixtures | test author / file-data tests | machine-only test fixture | `D-gap`; owner `FILE_DATA_CONTRACT.md`와 test case | test에서 직접 read, generator 없음 | fixture builder 또는 명시적 contract mapping 설계 |
| C17 | `src/**/*.py` 14 + `tests/*.py` 8 | 실행 구현·검증·enum·transition·CLI | developer agent / runtime·tests | `I` | `I`; C03·C05 contract trace 필수 | AST·unit tests | 지속 데이터 분류 분모에서 제외, machine-only 정책 사실은 10R-D debt |
| C18 | `.gitattributes`, `.gitignore` 2 | EOL·binary·보호·runtime ignore 실행 설정 | 에이전트 / Git | `I` config | `I`; owner `PROJECT_RULES.md` 보호·구조 정책 | Git behavior | 지속 데이터 분모에서 제외, 정책과 drift 검사 유지 |

경로 coverage 합계는 `89 + 211 + 2 + 13 + 1 + 1 + 5 + 22 + 2 = 346`이다. C01~C16의 지속 데이터 경로 322개는 모두 `C / D / L / D-gap`으로 분류됐고 미분류 경로는 0이다. C17~C18의 구현 artifact 24개도 owner trace 필요 여부를 표시했다.

#### `data/` 내용 전수 분류

| ID | 내용 cohort·수 | 고유 machine 사실 | 현재 writer·reader | 목표 분류·문서 owner | migration·검증 |
|---|---|---|---|---|---|
| D01 | `failure_knowledge` 39 | projection ID·source ID·hash·projected time | legacy direct read; public import는 `stored:false` | `L`; 각 `failures/*.md` | 새 write 0, canonical direct validate/search 유지 |
| D02 | failure projection이 참조한 source 39 | source ID·locator·observed time·hash | legacy direct read·lifecycle | `L`; 각 `failures/*.md`와 안전 source ref | D01 관계·ID·bytes 보존 |
| D03 | D01·D02 target lifecycle_state 78 | state·revision·approval·conflict·replacement | `LifecycleService` direct read·CLI | `L`; target failure Markdown은 의미 owner, ID·시간·actor·revision은 legacy-only | current 판단에서 제외, read-only. `last_reason` 의미 손상 6개를 아래 X01에 포함 |
| D04 | D01·D02 target lifecycle event 114행 | register·review·supersede 역사·actor·time | `LifecycleService` replay·CLI·maintenance cost | `L`; target failure Markdown은 의미 owner, 사건 metadata는 legacy-only | stream bytes 보존, 기본 current 경로 제외. `reason` 손상 10행을 X01에 포함 |
| D05 | 나머지 source 11 | source ID·locator·observed time·verification | `KnowledgeService.create/get/list/verify_source`, source CLI / lifecycle·context·maintenance, YouTube adapter의 context 경유 | `L`; `docs/CONTEXT_PACKAGE_CONTRACT.md` 3, `docs/INFORMATION_ARCHITECTURE.md` 6, `reports/2026-07-23_stage09_유튜브_근거_패키지_검증_보고서.md` 1, `request://stage05-recommended-auto-selection` 1은 exact 문서 owner gap | 정확한 세 문서 locator bytes는 보존. request source는 active 문서 원문 부재를 10R-D migration 입력으로 넘기고 새 source write 차단 |
| D06 | knowledge 11 | statement·classification·source 관계·verification | `KnowledgeService.create/get/list_knowledge`, knowledge CLI / lifecycle·context·maintenance, YouTube adapter의 context 경유 | `L`; `docs/INFORMATION_ARCHITECTURE.md` 계열 6, `docs/CONTEXT_PACKAGE_CONTRACT.md` 계열 4, Stage 09 report 계열 1 | current 2·candidate 1·superseded 8. 동일 statement 중복과 손상 statement 1개를 보존·구분해 문서 owner로 이관 |
| D07 | decision 1 | failure 정본 선택·option·rationale·approval | `KnowledgeService.create/get/list_decision`, decision CLI / lifecycle·context·maintenance | `L`; 결론 의미는 `rules/failure-records.md`·이 문서 §4.3에 있으나 option·rationale·approval과 request source의 exact 문서 owner는 gap | current decision과 candidate request source 관계를 보존하고 10R-D에서 exact owner를 지정 |
| D08 | D05~D07 lifecycle_state 23 | state·revision·conflict·승인 관계 | `LifecycleService` write/rebuild/read·CLI / context·maintenance, YouTube adapter의 context 경유 | `L`; target 의미 문서는 D05~D07, ID·시간·actor·revision의 exact 문서 owner는 gap | current 6·candidate 2·superseded 15를 분리. `last_reason` 손상 2개를 X01에 포함 |
| D09 | D05~D07 lifecycle event 43행 | register·review·supersede history | writer·semantic reader는 `LifecycleService` append/replay와 lifecycle CLI, `MaintenanceService`는 count만 읽음. `ContextService`·YouTube adapter는 event가 아니라 D08 파생 상태를 소비 | `L`; target 의미 문서는 D05~D07, 사건 metadata의 exact 문서 owner는 gap | D08 재구성용 bytes 보존. `reason` 손상 6행을 X01에 포함 |
| D10 | work_state 9 | request·status·completed items·blocker·next action·evidence | `WorkStateService` create/transition/rebuild/read·work CLI / resume·maintenance cost | `L`; Stage 04~10 문서는 결과 의미 owner지만 work ID·전체 request·event projection의 exact 문서 owner는 gap | 모두 `completed`; Stage 10 잘못된 완료는 역사로 한정. Stage 06·07 snapshot 2개의 손상 필드를 X01에 포함 |
| D11 | work event 36행 | request·checkpoint·completion actor/time/order | `WorkStateService` append/replay·history·rebuild·work CLI / maintenance cost | `L`; D10 stage/report는 결과 의미 owner지만 append-only 사건 metadata의 exact 문서 owner는 gap | event bytes 보존, 새 current 상태는 문서 owner만 사용. Stage 06·07의 손상 6행·59개 field value를 X01에 포함 |

record coverage는 `39 + 39 + 78 + 11 + 11 + 1 + 23 + 9 = 211`, event coverage는 `114 + 43 + 36 = 193`이다. record·event 내용도 미분류 0이다.

#### 기존 의미 손상 cohort

| ID | 영향 범위 | 확인된 손상 | 현재 판정 | 10R-D 이후 조치 |
|---|---|---|---|---|
| X01 | record 11개·event 22행 | knowledge statement 1, lifecycle_state `last_reason` 8, lifecycle event `reason` 16행, completed work_state 2개의 request·허용·제외·완료 필드, work event 6행의 59개 field value에 연속 `??` 존재 | migration 전에 이미 발생한 의미 손실. 현재 hash·schema·UTF-8은 유효하므로 maintenance와 99개 테스트가 탐지하지 못하며, 원인·당시 대응은 [Windows CLI 표준 입출력 인코딩 불일치](../../failures/windows-cli-utf8-stdio.md)가 소유 | bytes를 수정·삭제하지 않고 legacy 증거로 보존. 활성 문서·Git 이력에서 원문 복구 가능성을 조사하고, 복구 가능/불가를 필드별 표시한 뒤 문서 owner로 이관. 복구 불가 항목은 기존 확인된 정보 손실로 명시하며 `정보 손실 0`은 migration이 추가 손실을 만들지 않았다는 뜻과 구분 |

X01의 위치 분해는 D03 6개, D04 10행, D06 1개, D08 2개, D09 6행, D10 2개, D11 6행이다. 합계는 record `6 + 1 + 2 + 2 = 11`, event `10 + 6 + 6 = 22`다.

#### 10R-C에서 확인된 결함과 다음 검증

- 기존 `data/`에는 문서에 없는 ID·timestamp·revision·actor·관계·event 순서가 존재한다. 활성 저장 경로에서 권위로 사용되는 비실패 machine artifact는 record 55개·event 79행이며 UR-18을 위반한다. 55개가 모두 current target이라는 뜻은 아니며 lifecycle target은 current 6·candidate 2·superseded 15, work_state 9개는 completed다.
- source 11·knowledge 11에는 같은 문서에서 나온 동일 statement가 중복 저장돼 단일 owner 원칙과 fanout 위험을 실제로 재현한다.
- D05~D11의 의미 owner와 machine metadata owner를 분리한 결과 request source 1, decision 세부, lifecycle metadata, work ID·전체 사건 metadata에는 exact 문서 owner가 없다는 gap이 확인됐다.
- X01의 11 record·22 event행은 migration 전에 이미 의미가 손상됐다. 정보 손실 0 검증은 이 기준선을 숨기지 않고 복구 가능성·추가 손실을 분리해야 한다.
- schema 13, Obsidian config 1, example 1, fixture 5는 목표가 문서 파생이지만 doc→artifact rebuild가 없어 `D-gap`이다.
- Stage view 11은 link-only 파생이지만 현재 generator가 없다. 기존 파일은 read-only로 보존하고 새 view를 만들지 않는다.
- 이 단계는 분류만 수행했으며 JSON·JSONL·schema·config·fixture·code를 수정하지 않았다. 기존 사용자 미커밋 data 변경도 그대로 보존했다.
- 최초 교차검증 준비에서 10R-C 하나에 Codex 서브에이전트 3명을 시작했으나, 사용자가 단계 작업 하나당 한 명만 사용하도록 범위를 교정했다. 결과를 내기 전 2명을 즉시 중단했고, 남은 1명에게 C01~C18·D01~D11·요구 추적 전체 범위를 통합했다. 이후 단계도 같은 제한을 적용한다.
- 단일 Codex 서브에이전트 1차 교차검증은 수치와 요구 전환을 확인했지만 손상 cohort 누락과 exact owner 부재 은폐를 Medium 2, C08 glob·reader/writer 축약·55개 표현을 Low 3으로 판정해 전체 FAIL을 반환했다. 주 작업 Codex는 실제 파일과 코드에서 모두 재현해 다섯 지적을 수용하고 위 표와 X01로 보완했다.
- 같은 검증자의 재검증은 PASS, High 0·Medium 0·Low 1로 1차 Medium 2와 Low 2의 해소, 경로 346·지속 데이터 322·record 211·event 193행·미분류 0·X01 11/22를 확인했다. 남은 Low는 D09가 event 직접 reader와 D08 상태 소비자를 혼합한 표현이어서 주 작업 Codex가 수용해 직접 reader·count-only reader·파생 상태 소비자를 분리했다.
- 같은 검증자의 마지막 최소 범위 확인은 PASS, High 0·Medium 0·Low 0이며 D09 Low 해소와 상단·실행 기록·핸드오프 정합성을 확인했다.

#### 10R-C 성공 게이트

| 확인 | 결과·근거 |
|---|---|
| 요구 정합성 | SR-01·02·04·06·07·08·10·11·15·17·18·19·20·21·25를 C01~C18·D01~D11·X01과 연결. 문서 정본·구조 최적화·보고·단계당 단일 검증자 요구 축소 0 |
| 실제 작동 | `core.quotepath=false` 경로 집계 346/346·미분류 0, JSON 211개·JSONL 193행 전수 파싱, ID·cohort·state·event revision 대조, 전체 unittest 99개 성공 |
| 문서 정본 | 10R-C 범위의 machine-only debt·exact owner gap과 확인된 기존 손상을 공개하고 새 machine-only fact 0 확인. 최종 0 달성은 인과 계획대로 10R-F~10R-H가 소유 |
| 범위·안전 | `inputs/`·`outputs/`·`backup/` 열거·열람 0, data bytes 수정·삭제 0, 보호·외부·설치·비용 행동 0 |
| 실패 재발 | X01 원인을 `failures/windows-cli-utf8-stdio.md`, fanout 원인을 `failures/derived-failure-projection-fanout.md`에 연결 |
| 자동 검증 | `maintenance-verify` PASS: documents 89, links 648, Python 14, schemas 13, errors·drift·duplicates 0, inventory 12,535 bytes match. `git diff --check` PASS |
| 독립 검증 | 같은 Codex 서브에이전트 한 명의 1차 FAIL H0/M2/L3 → 전부 수용·보완 → 재검증 PASS H0/M0/L1 → 문구 보완 → 최종 PASS H0/M0/L0 |
| 상태 정합성·보고 | Stage 10·핸드오프가 10R-C 통과와 10R-D 첫 행동을 동일하게 표시 |

10R-C 성공 게이트 판정은 **통과**다. 다음 행동은 이 분류와 gap을 입력으로 10R-D 문서 owner 모델, 파생 생성 규칙, legacy 격리, 손상 복구 가능성, 호환·rollback을 설계하는 것이다.

### 10R-D 문서 기반 목표 구조·migration 설계

#### 설계 결정

1. 활성 요구·상태·작업·지식·결정·출처·승인·검증 근거는 기존 Markdown owner 안에서만 갱신한다.
2. 정밀한 구조가 필요한 데이터는 Markdown 안의 엄격한 `project-data:v1` JSON block이 소유한다. block은 사람이 직접 읽을 수 있는 문서 본문이며 별도 JSON record가 아니다.
3. 같은 값을 주변 설명이나 다른 block에 복제하지 않는다. 설명은 block을 링크하고, exact 값은 block 하나만 소유한다.
4. `data/records/*.json`과 `data/events/*.jsonl`의 기존 bytes는 모두 legacy history로 동결한다. 새 record·event·snapshot을 만들거나 기존 bytes를 정규화하지 않는다.
5. schema·Obsidian shared config·example·test fixture는 `project-artifact:v1` block에서 결정적으로 추출되는 파생물로 전환한다.
6. 실행 중 계산되는 검색 결과·context package·검증 결과는 stdout 또는 메모리에만 두고, 재개·감사·현재 상태가 필요할 때만 해당 Markdown owner를 갱신한다.
7. migration은 dual-write를 사용하지 않는다. 문서 shadow-read 대조가 끝나면 legacy baseline을 다시 검증하고 production legacy writer를 먼저 차단한 뒤 reader를 문서로 전환한다.

| 목표 분류 | 경로 수 | 구성 |
|---|---:|---|
| 문서 정본 `C` | 77 | 활성 Markdown 89에서 generated inventory 1과 legacy stage view 11을 제외 |
| 문서 파생 `D` | 21 | inventory 1 + schema 13 + Obsidian config 1 + example 1 + fixture 5 |
| legacy `L` | 224 | record 211 + event stream 2 + Stage 00~09 view 11 |
| 일시 실행 데이터 `T` | 0 persistent path | stdout·메모리·비교 임시 위치는 작업 종료 뒤 폐기 |
| 구현 `I` | 24, 지속 데이터 분모 밖 | Python 22 + repo config 2, 문서 계약 trace 필수 |

지속 데이터 합계는 `77 + 21 + 224 = 322`, 미분류는 0이다.

#### canonical data block 계약

````markdown
<!-- project-data:v1 kind=<work|knowledge|decision|legacy-baseline> key=<stable-slug> -->
```json
{
  "key": "stable-slug",
  "kind": "knowledge",
  "status": "current",
  "source_refs": ["docs/INFORMATION_ARCHITECTURE.md#1-기본-원칙"],
  "payload": {
    "statement": "활성 정보마다 단일 소유자를 둔다."
  }
}
```
<!-- /project-data -->
````

- block은 strict UTF-8, NUL 0, JSON duplicate key 0, 정확한 top-level field 집합을 사용한다.
- `key`는 문서 안에서 안정적인 lowercase slug이며 무작위 UUID를 새로 만들지 않는다.
- 모든 block은 `key`, `kind`, `status`, `source_refs`, `payload`를 공통 top-level field로 가진다. `kind`별 payload는 기존 계약의 필요한 의미만 보존한다. 저장 외피의 `content_hash`, projection ID처럼 legacy에만 필요한 필드는 활성 block으로 복제하지 않는다.
- `source_refs`는 원칙적으로 한 개 이상이며 `legacy-baseline`만 빈 배열을 허용한다. marker의 kind·key와 JSON의 kind·key는 정확히 같아야 한다.
- `source_refs`는 보호 경계를 통과한 프로젝트 상대 Markdown link 또는 승인된 web ref다. `request://` 같은 machine-only source는 사용자 원문이 있는 요구 문서 anchor로 대체하고, 원문이 없으면 legacy-only로 남긴다.
- `status`는 문서의 현재 의미를 직접 표현한다. 대체는 기존 block을 역사로 무한 누적하지 않고 문서 본문·Git 이력·명시 replacement link로 표현한다.
- work block은 요청·승인 범위·제외·보호 경계·현재 상태·완료 항목·blocker·첫 다음 행동·evidence와 중요한 checkpoint만 가진다. 모든 명령과 미세 event를 저장하지 않는다.
- canonical marker는 줄 시작 column 0에 있어야 하며 CommonMark fenced code와 indented code 밖에서만 유효하다. parser는 0~3칸 들여쓴 3개 이상 backtick 또는 tilde fence, 같은 문자·시작 이상 길이의 닫는 fence, 4칸 이상 indented code를 추적해 그 안의 marker를 무시한다. 닫는 marker 누락, 중복 key, owner 밖 target, 알 수 없는 kind를 fail-closed로 거부하고 backtick·tilde·중첩 길이·들여쓰기 회귀를 고정한다.

#### `project-data:v1` kind별 exact 계약

| kind | 허용 owner | status | payload exact fields | 교차 조건 |
|---|---|---|---|---|
| `work` | 활성 block은 `SESSION_HANDOFF.md` 하나 | `requested`, `in_progress`, `failed`, `blocked`, `completed` | `desired_outcome`, `authorized_actions`, `excluded_scope`, `input_refs`, `protection_boundaries`, `required_decisions`, `verification_levels`, `completed_items`, `blockers`, `next_action`, `evidence_refs`, `checkpoints` | 모든 목록은 중복 없는 문자열 배열. `blocked`는 blocker≥1, `in_progress`는 next_action 필수, `completed`는 next_action `null`. checkpoint는 `at`, `actor`, `summary`, `evidence_refs` exact fields와 UTC `Z` 시각 |
| `knowledge` | `docs/*.md`, `docs/domain/**/*.md`; failure는 기존 direct parser만 사용 | `candidate`, `current` | `statement`, `classification`, `scope`, `verification_status`, `verified_by`, `replaces_legacy_ids` | statement는 줄바꿈 없는 1~500자. classification=`fact/inference/procedure/constraint`, verification=`candidate/verified`. verified면 verified_by 필수, candidate면 `null`; source_refs≥1. replaces는 신규 문서 지식이면 빈 목록, 이관이면 실제 nonterminal legacy knowledge UUID exact 목록이며 미존재·terminal·타 유형·복수 block 중복 claim은 실패 |
| `decision` | `docs/build/stage-*.md` | `current` | `problem`, `requirements`, `options`, `selected_option`, `rationale`, `impacts`, `requires_user_approval`, `approval_kind`, `approved_by`, `decided_at`, `replaces_legacy_id` | requirements·impacts·source_refs≥1, options≥2이고 각 option은 `label`, `description`; selected는 label 중 하나. approval=`user/standing_policy/agent_in_scope`, 사용자 승인 필요 시 앞의 두 종류만. decided_at은 UTC `Z`; replaces는 UUID 또는 `null` |
| `legacy-baseline` | 이 Stage 10 owner의 이 절 하나 | `current` | `data_root_entries`, `events`, `records` | source_refs만 빈 배열 허용. exact allowlist·count·hash·entry type을 모두 만족 |

공통 `key`는 정규식 `[a-z0-9]+(?:-[a-z0-9]+)*`, 1~100자이며 활성 Markdown 전체에서 유일하다. `source_refs`의 로컬 값은 `/` 구분 프로젝트 상대 경로와 선택 anchor만 허용하고 Unicode NFC로 정규화한다. 절대 경로, `.`·`..`, backslash, `.git`·`.obsidian`·`backup`·`inputs`·`outputs` segment, 존재하지 않는 owner를 거부한다. web ref는 승인된 `https`만 허용한다. marker kind·key와 JSON kind·key가 다르거나 추가·누락 field가 있으면 실패한다.

#### owner 이관표

| 현재 cohort | 활성 의미의 목표 문서 owner | legacy로만 남는 것 | 기본 소비 경로 |
|---|---|---|---|
| work request·state·event | 활성 상태·blocker·첫 다음 행동의 유일한 owner는 `SESSION_HANDOFF.md` work block. stage owner는 목표·범위·계획·결정·검증·게이트 시점 증거만 소유 | D10 9개 snapshot, D11 36행의 UUID·세부 사건·시간·actor | checkpoint 증거를 stage owner에 먼저 기록한 뒤 handoff는 그 evidence ref와 현재 상태만 갱신; 같은 exact 값 복제 금지 |
| source | source가 가리키는 실제 contract·stage·report의 link와 근거 절 | D02·D05의 source ID·observed time·과거 hash; owner 없는 request source | `DocumentDataService`가 link·현재 bytes를 검증 |
| knowledge | `docs/INFORMATION_ARCHITECTURE.md`, `docs/CONTEXT_PACKAGE_CONTRACT.md`, `docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md`, 각 failure Markdown | D01·D06의 superseded body·record ID·projection metadata | 문서 block·failure direct parser를 검색·선택 |
| decision | 결정이 발생한 `docs/build/stage-*.md`; 새 failure direct-parser 결정은 이 문서 §4.3의 새 block | 기존 D07은 `markdown_canonical_hash_projection`을 선택한 과거 결정 전체로 legacy 보존 | 새 block이 기존 ID를 `replaces_legacy_id`로 가리키고 현재 사용자 원문·Stage 10 승인 trace를 소유 |
| lifecycle state·event | owner 문서의 `status`, 승인 근거, replacement link, 중요한 checkpoint | D03·D04·D08·D09의 revision·event ID·세부 actor/time/order | 문서 상태가 current 판단을 소유; legacy는 explicit audit만 |
| failure | 기존 `failures/*.md` 직접 정본 | 기존 failure projection/source/lifecycle 전부 | 현재 direct validate/search, legacy ID explicit read |
| context·YouTube package | 호출 요청·stdout의 일시 데이터; 재사용 정책은 해당 contract | 기존 package schema와 Stage 09 machine example의 과거 bytes | 문서 ref 기반 비영구 package |

현재 current/candidate 의미 검토 대상은 source 4, knowledge 3, decision 1이다. source는 별도 활성 record를 만들지 않고 해당 문서 link로 흡수한다. superseded source 7·knowledge 8과 모든 machine event는 history 가치만 가지므로 legacy에 보존한다. 기존 current decision 1도 목표 결정과 의미가 달라 과거 legacy로 보존하고, 새 direct-parser decision block을 현재 결정으로 만든다. 활성 work의 current 필드는 handoff만 소유하며 Stage 10은 계획·결정·게이트 증거만 소유한다.

| 현재 활성 의미 | exact target |
|---|---|
| current local source 3 | `docs/INFORMATION_ARCHITECTURE.md`, `docs/CONTEXT_PACKAGE_CONTRACT.md`, `reports/2026-07-23_stage09_유튜브_근거_패키지_검증_보고서.md`의 실제 근거 절 link |
| candidate request source 1 | 원문이 없는 `request://stage05-recommended-auto-selection` 자체는 legacy-only. current decision은 이 문서 §4.3과 통합 요구사항 기준서의 현재 사용자 원문을 새 source trace로 사용 |
| current knowledge 2 | 단일 owner 주장은 `docs/INFORMATION_ARCHITECTURE.md`, 결정론적 context 주장은 `docs/CONTEXT_PACKAGE_CONTRACT.md`의 canonical block |
| candidate knowledge 1 | `docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md` §8의 candidate block |
| 기존 current decision 1 | 선택 `markdown_canonical_hash_projection`과 당시 approval을 legacy로 보존. 이 문서 §4.3에 `transient_direct_parser`를 선택한 새 current decision block을 만들고 기존 UUID를 replacement로 추적 |

아래 block은 기존 D07을 수정하거나 현재 결정으로 오인하지 않고, 사용자의 최신 문서 정본 요구와 §4.3 구현 방향을 소유하는 새 현재 결정이다.

<!-- project-data:v1 kind=decision key=failure-knowledge-transient-direct-parser -->
```json
{
  "key": "failure-knowledge-transient-direct-parser",
  "kind": "decision",
  "payload": {
    "problem": "실패 Markdown 정본을 활성 기계 projection 없이 에이전트가 검증·검색·재사용하는 방법",
    "requirements": [
      "모든 지속 데이터는 문서가 정본이어야 한다",
      "실패 한 건이 여러 활성 파일을 새로 만드는 fanout을 제거해야 한다",
      "기존 구조화 데이터는 삭제하거나 수정하지 않고 legacy read-only로 보존해야 한다"
    ],
    "options": [
      {
        "label": "markdown_canonical_hash_projection",
        "description": "Markdown 정본과 hash 고정 구조화 projection을 함께 유지한다"
      },
      {
        "label": "transient_direct_parser",
        "description": "실행 시 Markdown 정본을 직접 strict 파싱하고 저장하지 않는 transient view만 만든다"
      }
    ],
    "selected_option": "transient_direct_parser",
    "rationale": "문서 정본을 실행 입력으로 직접 사용하면 현재 사실의 이중 저장과 실패별 source·projection·lifecycle fanout을 제거하면서 기존 history의 명시적 읽기 호환을 유지할 수 있다.",
    "impacts": [
      "새 실패와 개정은 해당 failure Markdown만 갱신한다",
      "기본 검색과 context는 failure Markdown direct parser를 사용한다",
      "기존 failure 관련 record와 event는 explicit legacy audit에서만 읽는다"
    ],
    "requires_user_approval": true,
    "approval_kind": "standing_policy",
    "approved_by": "user:2026-07-23-document-canonical-directive",
    "decided_at": "2026-07-23T14:25:36Z",
    "replaces_legacy_id": "51c05c01-1c72-4f66-91f6-c763d7f3050c"
  },
  "source_refs": [
    "reports/2026-07-22_프로젝트_의도_통합_요구사항_기준서.md",
    "docs/build/stage-10-agent-autonomy-structure-optimization.md#9-사용자-결정-기록"
  ],
  "status": "current"
}
```
<!-- /project-data -->

#### 문서 파생 artifact 계약

````markdown
<!-- project-artifact:v1 path=<approved-relative-path> verify=json-semantic -->
```json
{
  "document_owned": true
}
```
<!-- /project-artifact -->
````

| 대상 | owner | 생성·검증 |
|---|---|---|
| `schemas/common-record-v1.schema.json` | `docs/FILE_DATA_CONTRACT.md` artifact block | JSON을 canonical UTF-8로 추출, runtime field·enum과 의미 대조 |
| `schemas/work-request-payload-v1.schema.json`, `work-event-payload-v1.schema.json`, `work-state-payload-v1.schema.json` | `docs/WORK_STATE_CONTRACT.md` artifact block 3개 | 같은 방식 |
| `schemas/source-payload-v1.schema.json`, `knowledge-payload-v1.schema.json`, `decision-payload-v1.schema.json`, `failure-knowledge-payload-v1.schema.json` | `docs/KNOWLEDGE_TYPES_CONTRACT.md` artifact block 4개 | failure schema는 legacy read compatibility로 표시 |
| `schemas/lifecycle-event-payload-v1.schema.json`, `lifecycle-state-payload-v1.schema.json` | `docs/KNOWLEDGE_LIFECYCLE_CONTRACT.md` artifact block 2개 | 같은 방식 |
| `schemas/context-package-v1.schema.json` | `docs/CONTEXT_PACKAGE_CONTRACT.md` artifact block | 비영구 package 구조 |
| `schemas/youtube-evidence-request-v1.schema.json`, `youtube-evidence-pack-v1.schema.json` | `docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md` artifact block 2개 | 기존 request 외피와 공개 명령 이름은 유지한다. `documents[]`에 선택 `data_key`를 허용해 기본 문서 참조를 표현하고 `records[]` UUID는 explicit `--legacy`에서만 유효하도록 runtime mode와 함께 검증 |
| `.obsidian/app.json` | `docs/obsidian/OBSIDIAN_REVIEW_CONTRACT.md` | 안전 shared filter block만 추출; workspace·UI·plugin 상태 금지 |
| `examples/youtube/stage09-foundation-evidence.request.json` | YouTube contract | 보호 데이터 없는 request example block 추출 |
| `tests/fixtures/file_data/valid/neutral-record.json`, `tests/fixtures/file_data/invalid/missing-field.json`, `tests/fixtures/file_data/invalid/tampered-content.json`, `tests/fixtures/file_data/invalid/wrong-id.json`, `tests/fixtures/file_data/invalid/wrong-version.json` | `docs/FILE_DATA_CONTRACT.md` artifact block 5개 | valid/invalid fixture 추출; invalid 목적과 기대 오류를 문서가 소유 |
| generated inventory 1 | `docs/MAINTENANCE_AUTOMATION_CONTRACT.md`와 활성 Markdown 집합 | 기존 `maintenance-inventory` 결정론 유지 |
| Stage 00~09 Obsidian view 11 | 각 stage owner | 10R-D에서 `L`로 확정. 완료 시점 역사 보기로 read-only 보존하고 새 생성 0 |

공통 extractor는 marker의 `path`만 target으로 사용하고 `schemas/`, `.obsidian/app.json`, `examples/`, `tests/fixtures/`의 기존 승인 경로만 허용한다. `data/`, `inputs/`, `outputs/`, `backup/`, 저장소 밖 경로는 target으로 거부한다. target 중복, owner 중복, 알 수 없는 format, 현재 artifact와 semantic mismatch는 실패한다. 재생성 출력은 `ensure_ascii=false`, LF, final newline, 결정적 key ordering을 사용하며 먼저 비교 위치에서 검증한 뒤 승인된 파생 파일만 원자 교체한다.

위 표의 exact target 집합을 allowlist로 사용하며 prefix만 맞는 새 경로는 거부한다. contract의 기존 prose·표가 artifact block의 exact field·enum을 다시 소유하면 해당 prose·표를 설명·link로 축약하거나 block에서 생성된 검증 대상으로 바꾼다. “테스트로 일치한다”는 이유만으로 두 exact owner를 영구 유지하지 않는다.

#### legacy 동결 기준선

아래 block은 10R-C가 분류한 현재 bytes의 문서 정본 기준선이다.

<!-- project-data:v1 kind=legacy-baseline key=stage10-data-legacy-baseline -->
```json
{
  "key": "stage10-data-legacy-baseline",
  "kind": "legacy-baseline",
  "payload": {
    "data_root_entries": [
      "events",
      "records"
    ],
    "events": {
      "allowed_files": [
        "lifecycle_events.jsonl",
        "work_events.jsonl"
      ],
      "file_count": 2,
      "files": {
        "lifecycle_events.jsonl": {
          "rows": 157,
          "sha256": "6f5b78deb6933c0b5896eb17bc3180b376da78b62eb808d49c9ceae426f34509"
        },
        "work_events.jsonl": {
          "rows": 36,
          "sha256": "4ac0896fa68db9fa4cf798b0328117219d7f15280be63aa5a38a840ab3d6f0e8"
        }
      }
    },
    "records": {
      "allowed_suffix": ".json",
      "count": 211,
      "manifest_bytes": 22577,
      "subdirectories_allowed": false,
      "tree_sha256": "ce04599703237158b949c52e64de898a7112c77d6c14038de83c54d35cfe34b4"
    }
  },
  "source_refs": [],
  "status": "current"
}
```
<!-- /project-data -->

records tree hash는 파일명을 오름차순 정렬하고 각 행을 `<filename><TAB><lowercase file sha256><LF>`로 만든 UTF-8 manifest의 SHA-256이다. verifier는 `data/` root의 entry가 `events`, `records` 두 디렉터리뿐인지, events가 exact 두 파일뿐인지, records가 하위 디렉터리·non-JSON 없이 211개인지 먼저 확인한 뒤 hash를 계산한다. 예상 밖 lock·temp·stream·파일·디렉터리도 drift다.

legacy read-only는 OS 속성만 믿지 않고 세 겹으로 강제한다.

1. production `RecordStore` 기본값은 read-only다. 내부 write capability는 OS temp 아래의 격리 root이고 `PROJECT_RULES.md`·active work marker·legacy baseline marker가 모두 없을 때만 생성한다. maintenance 회귀용 임시 Git 저장소와 active block이 없는 fixture handoff는 허용하지만 활성 프로젝트나 baseline이 있는 root는 항상 거부한다.
2. 실제 프로젝트 CLI의 create·update·append·source/knowledge/decision/lifecycle/work write 명령은 `legacy_read_only`로 실패한다.
3. maintenance가 exact data root entry·event file allowlist·records entry type·count·tree·stream hash를 모두 대조한다.

legacy direct read는 명시 `--legacy` 또는 legacy 전용 library 경로에서만 허용하고, default list·search·current·context·work resume은 문서 owner를 사용한다.

#### X01 복구 계약

| 대상 | 예비 복구 판정 | 허용 조치 | 금지 |
|---|---|---|---|
| 손상 knowledge statement 1 | 정확한 UTF-8 replacement와 Stage 07 실패 기록이 있어 의미·문구 복구 가능 | current 문서 owner block에 정확한 statement를 한 번 기록 | superseded JSON byte 수정 |
| Stage 06·07 work_state 2와 work event 6행 | stage owner에서 목표·결과의 의미 복구 가능, 개별 손상 field의 원문은 미확정 | stage owner의 검증된 목표·결과만 canonical work 의미로 채택하고 `semantic_recovery` 표시 | `?` 길이로 문장을 추측하거나 원문 복구를 주장 |
| lifecycle_state 8·event 16행 | failure·stage 문서에서 일부 이유 의미는 복구 가능, exact reason 원문은 미확정 | target owner와 기존 failure 사례에 확인된 의미만 연결, event bytes는 legacy 보존 | actor·reason·time을 재작성 |

Git 예비 대조에서 손상 knowledge/work record 3개는 각 최초 blob부터 `??`를 포함했다. event stream의 더 오래된 정상 blob은 해당 손상 행 생성 전이며 현재까지 정확한 원문 blob은 확인되지 않았다. 10R-F는 각 영향 필드를 `exact_recovered / semantic_recovered / unrecoverable_exact`로 분류하고 근거 경로를 기록한다. `정보 손실 0` 게이트는 migration이 새로운 손실을 만들지 않았음을 byte hash와 의미 대조로 입증하며, migration 전에 이미 존재한 `unrecoverable_exact`을 복구 성공으로 가장하지 않는다.

#### 목표 service·CLI

| 책임 | 목표 실행점 | 전환 |
|---|---|---|
| 문서 data 검증·조회 | `DocumentDataService`, `document-data-validate/list/show` | Markdown marker·JSON block·source link·status를 strict 검증 |
| 문서 work 갱신 | `DocumentWorkService`, `document-work-checkpoint` | active work block owner는 handoff 한 파일뿐이며 expected hash로 atomic update·재읽기 검증. stage evidence는 별도 책임의 선행 입력이고 handoff가 link만 보유 |
| 파생 artifact | `ArtifactService`, `artifact-check`, `artifact-rebuild --target <exact-path>` | owner block에서 비교 위치 생성→semantic/byte 검증→원자 교체 |
| legacy 무결성 | `LegacyDataVerifier`, `legacy-data-verify` | Stage 10 baseline block과 count·tree·stream hash 대조 |
| context·YouTube | 기존 public 이름 유지, 내부 document reader 사용 | record UUID 대신 document ref·data key를 선택; legacy ID는 explicit compatibility만 |

기존 `RecordStore`, `KnowledgeService`, `LifecycleService`, `WorkStateService`는 legacy audit read와 임시 fixture test에서만 유지한다. production write entry point를 조용히 우회하지 않고 명시 오류로 닫는다. schema 검증기는 문서 artifact block을 owner로 읽고 추출된 schema와 runtime validator의 field·enum을 대조한다.

공개 context·YouTube 요청의 파일명·명령 이름·version 외피는 그대로 유지한다. 요청 schema의 `documents[]` 항목은 기존 `ref`, `reason`에 선택 `data_key`를 추가하고, `records[]` 항목은 기존 UUID 구조를 보존한다. 다만 실행 mode가 의미를 분리한다.

- 기본 mode는 `documents[].ref`와 선택 `data_key`만 current authority로 해석하고 `records[]`가 하나라도 있으면 `legacy_mode_required`로 실패한다.
- `--legacy` mode는 기존 UUID `records[]`를 읽기 전용으로 허용하지만 문서 current authority로 승격하거나 새 record를 만들지 않는다.
- cutover 전 shadow mode는 동일 요청 의미를 document ref와 legacy UUID 양쪽으로 읽어 결과를 비교하되 어느 쪽에도 쓰지 않는다.
- M2에서 request schema artifact와 example을 이 union 계약으로 함께 재생성한 뒤 runtime validator와 semantic 대조를 통과시킨다. 따라서 reader 전환 시점에 구 schema/example와 새 기본 요청이 불일치하는 구간이 없다.

#### 인과 migration 순서

| 순서 | 실행 | 전환 게이트 | 실패 시 rollback |
|---:|---|---|---|
| M1 | `DocumentDataService`와 exact kind schema, CommonMark-aware marker parser, strict validation을 구현하고 기존 runtime에 document ref 해석을 추가하되 기본 reader는 바꾸지 않음 | 기존 문서 변경 없이 sample block 정상·오류, backtick·tilde·길이·들여쓰기·중복·owner·source-ref 거부 테스트 | code만 제거, legacy 영향 0 |
| M2 | exact allowlist의 artifact block을 owner 계약에 이관하고 extractor·`artifact-check`를 구현한다. YouTube request schema는 `documents[].data_key`와 기존 `records[]` union을 소유하고 example은 기본 document ref 형태로 재생성 | schema 13·config 1·example 1·fixture 5가 block과 semantic match, runtime validator가 default/legacy mode를 구분, 계약 안 exact 중복 0 | 아직 reader를 전환하지 않고 artifact는 block에서 직전 semantic으로 재생성 |
| M3 | current/candidate source·knowledge와 active work 의미를 정확한 owner block에 이관하고, 기존 D07은 legacy로 둔 채 위 새 current decision block의 replacement link를 검증 | source 4 검토 결과가 local link 3·legacy-only request 1로 닫히고 knowledge 3·기존 decision legacy 1·새 decision current 1·handoff active work 누락 0 | block을 Git으로 되돌리고 legacy reader 유지 |
| M4 | doc-first reader를 shadow mode로 실행해 document ref와 legacy UUID 대표 입력을 함께 비교하되 쓰기는 모두 금지 | 같은 대표 context·failure·YouTube·resume 의미 결과, 차이 전수 설명, legacy baseline 일치 | default reader 전환 금지 |
| M5 | cutover 직전 baseline을 다시 검증하고 production `RecordStore`·모든 legacy writer·event append를 먼저 read-only guard로 차단한다. 이때 기존 legacy reader는 계속 기본 경로 | 모든 production write 명령 fail-closed, 새 record/event/snapshot 0, exact allowlist·count·hash 일치 | reader는 바뀌지 않는다. guard 결함을 수정하고 baseline 불일치면 즉시 중단; legacy bytes에는 쓰지 않음 |
| M6 | default reader를 문서로 전환한다. 기본 요청은 document ref/data key만 허용하고 UUID `records[]`는 `--legacy` 없이는 거부하며 explicit legacy read는 유지 | 기본 경로 legacy read 의존 0, 기본 UUID 요청 fail-closed, document request 성공, explicit legacy read 성공 | reader routing만 legacy로 복구하되 M5 writer guard와 baseline 검증은 유지 |
| M7 | 모든 artifact를 문서 block에서 재검증·재생성하고 기본 실행 경로의 숨은 legacy 의존을 정적·동적으로 검사 | 삭제 후 또는 비교 위치에서 동일 semantic payload 재생성, artifact drift 0, data exact allowlist·hash 유지 | 파생물만 block에서 다시 재생성; M5 guard 유지 |
| M8 | X01 복구 등급을 확정하고 전체 dependency를 닫음 | exact/semantic/unrecoverable 합계 11 record·22 event행, 숨은 기본 reader/writer 0 | legacy bytes와 기존 stage/failure owner로 재구성; 추정 복원 금지 |

M1~M4는 10R-E, M5~M8은 10R-F가 소유한다. shadow-read는 허용하지만 dual-write는 금지한다. 각 단계가 실패하면 다음 단계로 넘어가지 않으며, legacy 기준 hash가 달라지면 migration을 즉시 중단한다.

#### 10R-D 설계 성공 조건과 미확정 위험

- 기존 persistent path 322개가 owner, derived generator, legacy baseline 중 하나에 연결된다.
- current/candidate source 4의 local owner 3·legacy-only 1, knowledge 3, 기존 decision legacy 1·새 decision current 1, active work의 exact target owner가 지정된다.
- schema 13·config 1·example 1·fixture 5·inventory 1의 rebuild 방식이 지정된다.
- legacy records 211·event 193행의 read-only enforcement·explicit compatibility·rollback이 정의된다.
- X01 11 record·22 event행의 복구 등급과 금지된 추정이 정의된다.
- migration 어느 단계도 기존 data byte 삭제·수정이나 permanent dual-write를 요구하지 않는다.
- 미확정 위험은 손상된 개별 field의 exact 복구 가능성이다. 기존 public legacy read 이름은 Stage 10 종료까지 유지하고 write 이름은 read-only 오류로 닫으며, 이후 제거는 별도 범위로 보고한다. Stage view 11은 완료 시점 legacy로 확정해 설계 분기를 남기지 않는다.

10R-D 독립 1차 검증은 **FAIL, High 0·Medium 6·Low 1**이었다. Codex는 전부 수용해 (1) kind별 exact 계약과 CommonMark marker 경계, (2) active work의 handoff 단일 owner, (3) 기존 D07과 새 current decision의 replacement 관계, (4) exact legacy allowlist·hash와 production/test write 경계, (5) writer guard 선행 cutover, (6) request schema·example·runtime의 default/legacy 호환 순서를 보완했고, Low의 fence 규칙도 회귀 조건으로 고정했다.

같은 검증자의 재검증은 **FAIL, High 0·Medium 1·Low 0**이었다. 1차 7건 중 6건은 해소됐으나 상위 설계 결정에 남은 “reader 전환 뒤 writer 차단” 문장이 상세 M5 writer guard→M6 reader cutover와 충돌했다. Codex는 이를 수용해 상위 결정도 `shadow 대조 → baseline 재검증 → production writer 차단 → reader 전환`으로 통일했다.

같은 검증자의 마지막 확인은 **PASS, High 0·Medium 0·Low 0**이다. 상위 결정, M4 shadow-write 금지, M5 baseline 재검증·writer 선차단·reader 유지, M6 reader 전환이 같은 인과 순서이며 반대 문구는 과거 실패 설명에만 남고 실행 권위가 아님을 확인했다. 새 finding은 없다.

**10R-D 성공 게이트: 통과.** 기존 persistent 322개 전부의 목표 분류, current/candidate exact owner, artifact exact target, legacy exact baseline·격리·rollback, X01 복구 등급, writer-first migration 순서가 지정됐고 독립 High·Medium·Low 미해결은 0이다. 다음 실행 권위는 10R-E M1~M4다.

### 10R-E 문서 우선 코드·CLI·테스트 구현

#### M1 — document data parser·조회

- `src/file_data/document_data.py` 한 파일에 `DocumentDataService`와 공통 block parser를 구현했다. 새 문서나 별도 결과 보고서는 만들지 않았다.
- parser는 strict UTF-8·NUL·duplicate JSON key·exact top-level/kind fields·enum·교차 조건·owner·전역 key 유일성·NFC source ref·보호 경계를 fail-closed로 검증한다.
- 보호 디렉터리는 경로를 만든 뒤 거르는 방식이 아니라 `scandir` entry 이름 단계에서 재귀 전에 차단하며 symlink도 따라가지 않는다.
- CommonMark 0~3칸 backtick/tilde fence의 시작·같은 문자와 시작 이상 길이의 종료, backtick info string의 backtick 금지, 4칸/tab indented code 안 marker를 검증한다. marker prefix가 보이지만 정확한 문법과 일치하지 않으면 조용히 무시하지 않고 실패한다.
- CLI `document-data-validate/list/show`를 기존 `file_data` 진입점에 추가했다.
- 실제 owner block은 work 1, knowledge current 2·candidate 1, decision current 1, legacy baseline 1로 총 6개다.
- `DocumentWorkService`와 `document-work-show/checkpoint`를 추가했다. checkpoint는 stage evidence를 먼저 요구하고, handoff의 단일 work block을 예상 해시로 다시 읽은 뒤 전용 잠금·동일 디렉터리 임시 파일 검증·`os.replace`·전체 재읽기 검증 순서로만 갱신한다. stale hash와 replace 실패는 원본을 보존한다.

#### M2 — document-owned artifact·요청 호환

- `ArtifactService`, `artifact-check`, exact allowlist의 `artifact-rebuild --target`을 같은 service·CLI에 추가했다.
- 계약 문서 7개 안에 schema 13·Obsidian shared config 1·YouTube 기본 example 1·중립 fixture 5의 `project-artifact:v1` exact block 20개를 이관했다.
- artifact check는 owner·target 중복·미승인 경로·누락·semantic drift를 거부하고, rebuild는 같은 디렉터리 임시 파일 검증 뒤 승인된 기존 target 하나만 원자 교체한다.
- 격리 temp root에서 20개 semantic match를 확인하고 `common-record` 파생물을 삭제한 뒤 block에서 재생성해 다시 drift 0을 확인했다.
- YouTube request v1의 `documents[]`에 선택 `data_key`를 추가하고 기본 mode의 `records[]`는 `legacy_mode_required`로 거부한다. 기존 UUID는 공개 명령 이름을 바꾸지 않고 explicit `--legacy`에서만 읽기 전용으로 허용한다.

#### M3 — current owner block 이관

| 의미 | 새 current/candidate owner | legacy |
|---|---|---|
| 활성 work | `SESSION_HANDOFF.md`의 `stage10-document-canonical-migration` block | 기존 work snapshot 9·event 36행 |
| 단일 정보 owner constraint | `docs/INFORMATION_ARCHITECTURE.md`의 `active-information-single-owner` | 같은 statement의 과거 knowledge/source/lifecycle |
| context 결정론 constraint | `docs/CONTEXT_PACKAGE_CONTRACT.md`의 `context-package-deterministic-derived-view` | 같은 statement의 과거 knowledge/source/lifecycle |
| YouTube procedure candidate | YouTube contract의 `youtube-evidence-pack-review-required` | Stage 09 candidate record/source/lifecycle |
| failure direct parser 결정 | 이 문서의 `failure-knowledge-transient-direct-parser` | D07 UUID `51c05c01-1c72-4f66-91f6-c763d7f3050c` |

maintenance는 문서 block의 명시적 `replaces_legacy_ids`와 기존 nonterminal record ID, statement·classification·scope·verification 상태·lifecycle 상태가 모두 정확히 일치할 때만 migrated legacy로 식별한다. source drift 억제도 문서 `source_refs`가 정확한 local locator를 가리키고 그 source의 모든 nonterminal consumer가 이관된 경우에만 허용한다. 공유 source에 이관되지 않은 consumer가 하나라도 있으면 source와 그 dependency drift를 계속 보고한다.

#### M4 — shadow read와 비증식 근거

| 검사 | 결과 |
|---|---|
| document data | block 6, kind count `work 1 / knowledge 3 / decision 1 / legacy-baseline 1` |
| artifact | exact 20, semantic drift 0 |
| work resume | `stage10-document-canonical-migration`, `in_progress` |
| failure current | canonical Markdown 26개 direct list, 새 projection 0 |
| YouTube 기본 | example이 `context-package-deterministic-derived-view`를 `data_key`로 선택, UUID 0 |
| YouTube legacy shadow | explicit `--legacy` current UUID `35ed5523-d970-48eb-a2fe-716b111e970c` 선택 |
| 의미 대조 | 기본 document block statement와 legacy record statement exact 일치 |
| legacy bytes | 실행 전후 record 211 tree `ce045997...34b4`, lifecycle/work stream hash 불변 |

첫 전체 회귀는 106개 중 105개가 통과했고 shadow 테스트가 이미 superseded된 Stage 08 UUID를 current로 기대해 1개 실패했다. 실제 lifecycle에서 replacement `35ed5523-d970-48eb-a2fe-716b111e970c`를 확인해 테스트 입력만 교정했고, 다시 **106개 전부 통과**했다. 프로젝트 data는 수정하지 않았다.

`maintenance-verify`는 document data·artifact 검사를 포함해 errors·drift·duplicates 0, inventory match, scan runtime warning 없음으로 통과했다. 전체 verify 시간은 약 6.1초라 verify metrics에 경고가 있지만 계약의 5초 관측 기준인 scan 자체는 약 4.2초로 경고가 없다. `git diff --check`도 통과했다.

#### 10R-E 1차 독립 교차검증과 보완

이 단계에 배정한 Codex 서브에이전트 한 명의 읽기 전용 1차 판정은 **FAIL, High 1·Medium 4·Low 0**이었다. 주 작업 Codex는 아래 다섯 건을 실제 코드·테스트·계약과 대조해 전부 수용했다.

| 심각도 | 확인된 결함 | 판정과 보완 |
|---|---|---|
| High | 문서를 읽는 서비스만 있고 active work를 문서에서 충돌 안전하게 갱신하는 `DocumentWorkService`·`document-work-checkpoint`가 없음 | 수용. expected hash·exclusive lock·strict temp validation·atomic replace·reread를 구현하고 성공·stale hash·replace failure 회귀를 추가 |
| Medium | 문자열은 검사할 때만 trim하고 원래 값을 반환해 `" same-key "` 같은 key가 marker·중복 경계를 우회할 수 있음 | 수용. 모든 nonempty string의 선행·후행 공백을 fail-closed로 거부하고 회귀 추가 |
| Medium | `root.rglob` 뒤 필터라 보호 디렉터리를 열거한 뒤 제외함 | 수용. `os.scandir` 기반 prefilter 재귀로 바꾸고 `inputs/`에 재귀 호출이 발생하지 않는 mock 회귀 추가 |
| Medium | migrated legacy 억제가 statement 중심이라 부정확한 replacement와 공유 source drift를 숨길 수 있음 | 수용. exact replacement ID·전체 의미 필드·lifecycle·source locator·모든 consumer 조건을 강제하고 exclusive/shared/mismatch 회귀 추가 |
| Medium | marker-like 오타가 조용히 무시되고 backtick info string의 금지 backtick을 fence로 오인해 뒤의 정상 block을 숨길 수 있음 | 수용. malformed data/artifact marker 거부와 CommonMark invalid opener 뒤 정상 block 인식 회귀 추가 |

보완 뒤 전체 회귀는 **113개 전부 통과**했다. 실제 project-data block 6개와 artifact 20개는 drift 0이고 maintenance scan도 errors·drift·duplicates 0, inventory match, runtime warning 없음으로 통과했다. 기존 records tree·event stream baseline은 변하지 않았다.

이 시점의 10R-E는 보완과 로컬 재검증까지만 완료된 상태였으며, 같은 검증자의 재확인 전에는 성공 게이트를 통과시키지 않았다.

#### 10R-E 같은 검증자 재검증과 2차 보완

같은 검증자는 1차 H1/M4의 직접 반례가 모두 해소됐고 전체 113 tests, document block 6, artifact 20, maintenance, legacy baseline이 통과했다고 확인했다. 그러나 새 경계 두 건을 찾아 최종 판정은 **FAIL, High 0·Medium 2·Low 0**이었다.

| 심각도 | 새 결함 | 판정과 보완 |
|---|---|---|
| Medium | `<!-- project-data:v1kind=...`·`project-artifact:v1path=...`처럼 v1 뒤 공백이 빠진 명백한 marker-like 문장이 block 0 성공으로 무시됨 | 수용. column 0의 전체 `<!-- project-data:v1`·`<!-- project-artifact:v1` prefix를 먼저 감지하고 exact 정규식 불일치를 모두 거부하는 회귀 추가 |
| Medium | 모든 knowledge가 legacy replacement를 최소 1개 요구해 신규 문서 지식이 불가능한 반면, 미존재 UUID는 maintenance가 조용히 건너뜀 | 수용. 신규 지식은 빈 목록을 허용하고, 목록이 있으면 실제 lifecycle state·nonterminal·knowledge type을 강제하며 미존재·terminal·타 유형·복수 block 중복 claim을 모두 document-data 오류로 닫는 회귀 추가 |

보완 뒤 전체 회귀는 **115개 전부 통과**했다. project-data 6·artifact 20 drift 0, maintenance errors·drift·duplicates 0과 inventory match, `git diff --check`를 다시 확인했다. 이 변경은 아직 성공 게이트가 아니다. 새 검증자를 만들지 않고 같은 10R-E 검증자가 두 Medium과 전체 회귀를 마지막으로 재확인해야 한다.

#### 10R-E 마지막 확인과 성공 게이트

같은 단일 검증자의 마지막 판정은 **PASS, High 0·Medium 0·Low 0**이다. 두 Medium의 최소 반례, 기존 H1/M4 해소 유지, 전체 115 tests, project-data 6, artifact 20, maintenance, inventory, diff와 legacy 기준선 불변을 독립 재현했고 새 finding은 없었다.

**10R-E 성공 게이트: 통과.** 대표 작업은 문서 읽기→expected-hash 문서 checkpoint→재읽기로 성공하고, artifact는 문서 block에서 재생성되며, 기본 YouTube 문서 선택과 explicit legacy 호환이 분리됐다. malformed·보호 경로·부정확 migration 억제 우회도 회귀로 닫혔다. 다음 실행 권위는 M5~M8을 소유한 10R-F다.

### 10R-F legacy 격리·기본 reader 전환

#### M5 — baseline 재검증과 production writer 선차단

- `LegacyDataVerifier`와 `legacy-data-verify`를 구현해 Stage 10의 문서 baseline block을 실제 `data/` root entry, event allowlist·row·SHA-256, record suffix·count·manifest bytes·tree hash와 대조한다. maintenance verify도 baseline block이 있으면 이 검사를 필수로 실행한다.
- 실제 결과는 records 211·manifest 22,577 bytes·tree `ce045997...34b4`, lifecycle 157행 `6f5b78...f34509`, work 36행 `4ac089...f0e8`로 baseline과 일치한다.
- `RecordStore.initialize/create/update/append_event`는 production에서 모두 `legacy_read_only`로 먼저 실패한다. 공개 저수준 record writer는 제거했고 store 내부 writer도 test 전용 capability의 정확한 identity 없이는 쓸 수 없다.
- 격리 테스트는 `RecordStore._for_test(...)`와 test-only CLI entry가 capability를 명시 주입한다. OS temp 경로·marker heuristic으로 capability를 자동 발급하지 않으며 context의 legacy read와도 결합하지 않는다.
- create·update·append를 경유하는 Knowledge·Lifecycle·Work 서비스와 production CLI도 같은 guard 밖에서 쓸 수 없다. reader 전환 전에 writer를 닫았고 실제 legacy data bytes는 바뀌지 않았다.

#### M6 — 기본 reader 문서 전환

- `ContextService.filter_records/search/build_package` 기본 mode는 current document knowledge·decision block과 canonical failure Markdown만 사용한다. 실제 기본 knowledge 결과는 `active-information-single-owner`, `context-package-deterministic-derived-view` 두 data key이며 UUID가 없다.
- 기본 context package의 `records[]`는 `legacy_mode_required`로 실패하고, YouTube의 explicit `--legacy`만 `legacy=True`를 전달한다.
- generic record/event, source·knowledge·decision, lifecycle, work snapshot의 production CLI read는 전역 `--legacy-read` 없이는 실패한다. 공개 command 이름은 유지하되 호환 의도를 명시해야 한다.
- 격리 fixture는 내부 test capability가 있는 동안에만 기존 legacy 회귀를 실행한다. production 기본 경로의 reader 의미에는 영향을 주지 않는다.

#### M7 — 파생 재생성과 숨은 의존 검사

- artifact 20개는 owner block과 semantic drift 0이며, 격리 root에서 각 target을 하나씩 삭제하고 rebuild한 뒤 매회 전체 20개 drift 0을 확인한다.
- maintenance는 document-data, artifact, legacy baseline을 함께 검사한다. 기본 context·YouTube에는 legacy UUID가 없고 explicit 호환 경로만 legacy를 읽는다.

#### M8 — X01 복구 등급 확정

아래 표는 기존 bytes에서 `??`가 실제 포함된 위치를 다시 전수 파싱한 결과다. legacy bytes는 수정하지 않았고 exact 원문을 추정하지 않는다. 배열 경로의 `[a..b]`는 wildcard가 아니라 `a`부터 `b`까지 모든 정수 index를 포함하는 정확한 집합 표기다.

| 종류·stream row | full UUID | 손상 field path | 복구 등급·한계 | 문서 의미 owner |
|---|---|---|---|---|
| record knowledge | `303f4141-cd17-43ac-8c75-97ca9142829c` | `$.payload.statement` | `exact_recovered` | `docs/CONTEXT_PACKAGE_CONTRACT.md`; 원인·대응은 `failures/windows-cli-utf8-stdio.md` |
| record lifecycle_state | `13a84800-d8d5-4683-b4ae-df1d19ca56f6` | `$.payload.last_reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `51b05b01-1c72-4f66-91f6-c763d7f3050b` → `docs/INFORMATION_ARCHITECTURE.md` |
| record lifecycle_state | `204bdd94-0a0a-437e-9c15-97479c1318d0` | `$.payload.last_reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `51a05a01-1c72-4f66-91f6-c763d7f3050a` → `docs/INFORMATION_ARCHITECTURE.md` |
| record lifecycle_state | `2d863053-2748-42a8-9c65-326e42139da2` | `$.payload.last_reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `61813ebc-00c6-40ae-a09e-f0ce06a9a95d` → `failures/test-fixture-contract-shape-assumption.md` |
| record lifecycle_state | `5b7f2db1-7eea-4663-9c36-e511f655a50a` | `$.payload.last_reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `a59e4133-4a84-4785-8a91-77b4b980d8f2` → `failures/windows-cli-utf8-stdio.md` |
| record lifecycle_state | `5faf8779-d42f-4ffc-aee5-76c5f90dc3f5` | `$.payload.last_reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `9091355d-0aef-42ec-b356-ad9f1f5ff87d` → `failures/windows-cli-utf8-stdio.md` |
| record lifecycle_state | `9c1b9ffc-1e83-4052-ac17-0a0f1a04c02d` | `$.payload.last_reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `625c61b6-f5a3-4b5d-afec-4f3fdf3c78da` → `failures/test-fixture-contract-shape-assumption.md` |
| record lifecycle_state | `9f533a6f-bde4-44b4-9e8f-403f7bd32292` | `$.payload.last_reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `2e5deb97-ab06-4f89-8638-7138a4e86166` → `failures/windows-validation-command-assumptions.md` |
| record lifecycle_state | `e2228871-5297-4be8-9570-b984f81d208b` | `$.payload.last_reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `33810c76-fc27-4d14-9d2c-e6fe5d7cc22d` → `failures/windows-validation-command-assumptions.md` |
| record work_state | `52d329d3-2868-4e7c-900d-4979ea3a68f5` | `$.payload.completed_items[0..2]`; `$.payload.request.authorized_actions[0..3]`; `$.payload.request.desired_outcome`; `$.payload.request.excluded_scope[0..7]` | `semantic_recovered`; 16 exact 값 `unrecoverable_exact` | `docs/build/stage-07-context-retrieval.md` |
| record work_state | `a8fed7c6-fe3d-4915-a972-af56f85fdfcc` | `$.payload.completed_items[0..19]`; `$.payload.request.authorized_actions[0..3]`; `$.payload.request.desired_outcome`; `$.payload.request.excluded_scope[0..8]` | `semantic_recovered`; 34 exact 값 `unrecoverable_exact` | `docs/build/stage-06-knowledge-lifecycle.md` |
| lifecycle event row 51 | `30dd0264-5b83-49e0-b800-b6e4a00a7996` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `f5d5ecd6-43bd-4dd7-8f3e-2e769be44493` → `docs/INFORMATION_ARCHITECTURE.md` |
| lifecycle event row 52 | `7853d235-bd24-4e11-877c-c5b9ba7cef37` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `bdbffc75-b328-4b22-a390-ea5ac7316653` → `docs/INFORMATION_ARCHITECTURE.md` |
| lifecycle event row 53 | `1ddaa2ab-a11a-44a1-8694-1dfc7254a90f` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `51a05a01-1c72-4f66-91f6-c763d7f3050a` → `docs/INFORMATION_ARCHITECTURE.md` |
| lifecycle event row 54 | `c76d02f5-a5c2-483c-a300-60e8fa37057f` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `51b05b01-1c72-4f66-91f6-c763d7f3050b` → `docs/INFORMATION_ARCHITECTURE.md` |
| lifecycle event row 55 | `fead82e3-d664-43e2-95d4-cca85fa4b7fb` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `aff1d799-7e79-45f2-9f13-d2b750e8e464` → `failures/windows-validation-command-assumptions.md` |
| lifecycle event row 56 | `fd0c87b8-3c58-48f6-9e4f-ad97c65b3241` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `ef88600e-5cf6-491a-bcca-7f1e884a91f7` → `failures/windows-validation-command-assumptions.md` |
| lifecycle event row 57 | `33960dc5-fb43-44a6-8916-d64692bdae10` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `33810c76-fc27-4d14-9d2c-e6fe5d7cc22d` → `failures/windows-validation-command-assumptions.md` |
| lifecycle event row 58 | `e8f4525e-2413-4350-a2c8-e680d8e1f1c0` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `2e5deb97-ab06-4f89-8638-7138a4e86166` → `failures/windows-validation-command-assumptions.md` |
| lifecycle event row 61 | `d36ad288-d9ec-44d1-ad4c-6c6ccca060e2` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `ca2b8928-2af8-41da-99a5-ae7495f764fb` → `failures/windows-cli-utf8-stdio.md` |
| lifecycle event row 62 | `f03c8692-f759-431c-9650-70165773294a` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `26b60808-1f0d-4536-b596-7d634db506d6` → `failures/windows-cli-utf8-stdio.md` |
| lifecycle event row 63 | `0d86aa01-e319-4914-8e8d-a152bed8dc3e` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `a59e4133-4a84-4785-8a91-77b4b980d8f2` → `failures/windows-cli-utf8-stdio.md` |
| lifecycle event row 64 | `0acdf812-2654-404a-9fd4-28a3d0ffba58` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `9091355d-0aef-42ec-b356-ad9f1f5ff87d` → `failures/windows-cli-utf8-stdio.md` |
| lifecycle event row 65 | `145e07af-b7ce-460d-badf-901a6fc1fb4c` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `625c61b6-f5a3-4b5d-afec-4f3fdf3c78da` → `failures/test-fixture-contract-shape-assumption.md` |
| lifecycle event row 66 | `1cce1cd0-afbb-4ee4-9289-e0780ad21e14` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `61813ebc-00c6-40ae-a09e-f0ce06a9a95d` → `failures/test-fixture-contract-shape-assumption.md` |
| lifecycle event row 67 | `742b9567-16da-4227-8441-8cb403252de7` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `9f2d950b-eadf-4fb8-91fe-b955049ceef2` → `docs/CONTEXT_PACKAGE_CONTRACT.md` |
| lifecycle event row 68 | `35733a6e-b9e3-434c-ac95-6e4d7188a534` | `$.payload.reason` | `semantic_recovered`; exact 문구 `unrecoverable_exact` | target `303f4141-cd17-43ac-8c75-97ca9142829c` → `docs/CONTEXT_PACKAGE_CONTRACT.md` |
| work event row 11 | `9353aec7-df2f-4a36-bfd8-130c314f05a6` | `$.payload.next_action`; `$.payload.request.authorized_actions[0..3]`; `$.payload.request.desired_outcome`; `$.payload.request.excluded_scope[0..8]` | `semantic_recovered`; 15 exact 값 `unrecoverable_exact` | work `a8fed7c6-fe3d-4915-a972-af56f85fdfcc` → `docs/build/stage-06-knowledge-lifecycle.md` |
| work event row 12 | `e76c4f4e-1835-483c-b3db-10a6a45ad86f` | `$.payload.action`; `$.payload.completed_items[0..2]`; `$.payload.next_action` | `semantic_recovered`; 5 exact 값 `unrecoverable_exact` | work `a8fed7c6-fe3d-4915-a972-af56f85fdfcc` → `docs/build/stage-06-knowledge-lifecycle.md` |
| work event row 13 | `d0397581-f772-47d0-9479-4d6f9a776815` | `$.payload.action`; `$.payload.completed_items[0..7]`; `$.payload.next_action` | `semantic_recovered`; 10 exact 값 `unrecoverable_exact` | work `a8fed7c6-fe3d-4915-a972-af56f85fdfcc` → `docs/build/stage-06-knowledge-lifecycle.md` |
| work event row 14 | `0d5a856f-aa66-4f4b-8317-43fb340ed479` | `$.payload.action`; `$.payload.completed_items[0..8]` | `semantic_recovered`; 10 exact 값 `unrecoverable_exact` | work `a8fed7c6-fe3d-4915-a972-af56f85fdfcc` → `docs/build/stage-06-knowledge-lifecycle.md` |
| work event row 15 | `c82d72ab-7a95-4191-8b43-6a63f331191b` | `$.payload.next_action`; `$.payload.request.authorized_actions[0..3]`; `$.payload.request.desired_outcome`; `$.payload.request.excluded_scope[0..7]` | `semantic_recovered`; 14 exact 값 `unrecoverable_exact` | work `52d329d3-2868-4e7c-900d-4979ea3a68f5` → `docs/build/stage-07-context-retrieval.md` |
| work event row 16 | `d989d893-3065-4127-ba6f-be36ac916a65` | `$.payload.action`; `$.payload.completed_items[0..2]`; `$.payload.next_action` | `semantic_recovered`; 5 exact 값 `unrecoverable_exact` | work `52d329d3-2868-4e7c-900d-4979ea3a68f5` → `docs/build/stage-07-context-retrieval.md` |

영향 합계는 record 11개·event 22행이고, 등급상 exact record 1 + semantic record 10 + semantic event 22다. work event의 손상 field value 합계는 `15 + 5 + 10 + 10 + 14 + 5 = 59`다. `unrecoverable_exact`은 별도 row를 더하는 수가 아니라 semantic 대상에 남은 exact 문자열 한계다. 따라서 migration이 새 손실을 만들지 않았다는 정보 손실 0과 기존 exact 원문 미복구를 동시에 공개한다.

10R-F 로컬 검증은 전체 119 tests, document-data 6, artifact 20, maintenance errors·drift·duplicates 0, inventory match, legacy baseline 불변, `git diff --check`를 요구한다. 독립 검증 요구는 2026-07-24 사용자 최신 예외 전의 계약이며, 현재 판정은 아래 자체 재검토가 소유한다.

#### 10R-F 1차 독립 교차검증

이 단계 전용 Codex 서브에이전트 한 명의 판정은 **FAIL, High 1·Medium 5·Low 1**이다. 주 작업 Codex는 실제 코드·문서·반례와 일치하는 일곱 건을 전부 수용했으며 이 시점에는 성공 게이트를 통과시키지 않는다.

| 심각도 | 확인된 결함 | 보완 방향 |
|---|---|---|
| High | package에 공개된 `atomic_write_record`가 production `RecordStore` guard 밖에서 data record를 쓸 수 있음 | 저수준 writer 공개 제거와 동일 capability 강제, production direct-call 회귀 |
| Medium | `maintenance-evaluate`가 명시 option 없이 내부 `legacy=True` 사용 | CLI·service에 명시 legacy opt-in 전달, 기본 false |
| Medium | test write capability가 OS temp·marker heuristic으로 자동 발급되고 context legacy 의미와 결합 | test-only factory의 명시 capability 주입, root heuristic·context 자동 연동 제거 |
| Medium | artifact 20개 중 한 target만 삭제→rebuild 회귀 | exact 20 target 각각 삭제→rebuild→전체 drift 0 반복 |
| Medium | X01 knowledge UUID 한 글자 오류와 나머지 11/22 full 추적 부재 | full UUID·stream row·field path·등급·owner 전수표로 교체 |
| Medium | handoff 하단에 끝난 10R-E blocker와 이미 수행한 M5 첫 행동 잔존 | active work next action과 하단 재개 문구 동기화 |
| Low | full document 직접 선택 뒤 같은 문서 data block 검색이 중복될 수 있음 | bare document ref로 중복 차단하고 회귀 추가 |

#### 10R-F 보완 완료·자체 재검토

- 공개 저수준 writer를 제거하고 private writer에도 명시 test capability를 강제했다. production direct call, 공개 symbol 부재, temp-root heuristic 부재를 회귀로 고정했다.
- maintenance·generic CLI의 legacy read는 `--legacy` 또는 `--legacy-read`가 없으면 실패하고 test capability가 context legacy mode를 켜지 않는다.
- artifact 20개 전부를 개별 삭제→rebuild→전체 drift 0으로 확인하며, full document와 같은 문서 data block의 중복 선택 회귀를 추가했다.
- X01은 위 11 record·22 event행의 full UUID·row·field path·등급·owner를 전수 추적한다.
- 전체 `python -m unittest discover -s tests -v` 119개가 2026-07-24 통과했다.

신규 blind 검증자 한 명을 시작했으나 사용자가 실행 중 중단과 현재 작업의 교차검증 제외를 지시했다. 검증자는 결과를 반환하기 전에 중단했고 결과를 사용하지 않았다. 아래 자체 재검토가 10R-F·10R-G와 10R-H 완료 준비 판정을 소유한다.

#### 10R-F~10R-H 최종 자체 재검토

자체 재검토 범위는 최종 전체 diff, SR-01~SR-27, production writer·reader 경계, 문서 block·artifact, X01 legacy trace, handoff current block, 보호·역사 경계, 전체 회귀·maintenance와 마스터 계획 §6.4 점수표다.

- 공개 `atomic_write_record` symbol은 package와 record module에 없고, private writer는 test capability의 exact identity 없이는 `legacy_read_only`로 실패한다. production service·CLI create/update/append도 동일하게 차단된다.
- test write는 `_for_test` 또는 test-only entry에서 명시 capability를 주입한다. root·marker heuristic과 context legacy 자동 연동은 없다. 자체 검토 중 invalid capability가 unhashable 값일 때 내부 `TypeError`가 날 수 있는 비교를 identity 검사로 바꿨다.
- maintenance/context/YouTube와 generic read CLI는 명시 `--legacy` 또는 `--legacy-read`가 없는 기본 경로에서 document owner를 사용하거나 legacy 요청을 거부한다.
- artifact 20개는 각각 격리 root에서 삭제→rebuild→매회 전체 drift 0으로 검증된다. full document 직접 선택과 같은 문서 data block 검색 중복도 회귀로 차단된다.
- X01 자동 대조 결과는 실제 손상 33행과 문서 표 33행, missing 0, extra 0, JSONPath mismatch 0이다. 이는 record 11개·event 22행과 work event 손상 값 59개를 정확히 포함한다.
- 자체 검토 중 `ContextService.build_package`의 과도한 중첩 들여쓰기를 정상화했다. 동작 변화는 없지만 다음 유지보수자의 분기 오독 위험을 제거했다.
- 보호 `inputs/`, `outputs/`, `backup/`은 이 작업에서 열거·열람하지 않았다. legacy data는 읽기 검증만 했고 삭제·덮어쓰기하지 않았다.
- 최종 자체 finding은 **High 0·Medium 0·Low 0**이다. 위 두 자체 발견은 수정 후 전체 회귀를 다시 통과했으므로 잔여 finding이 아니다.

실패 지식 조정:

- 첫 `document-data-validate` 호출은 `PYTHONPATH=src` 누락으로 module discovery에 실패했고, failure 정본 검증의 첫 호출은 내부 destination 이름을 option으로 오인해 `--canonical-doc-ref`를 사용했다. 둘 다 사용자 승인·네트워크 문제가 아니다. 정확한 환경과 `failure-validate --help`의 공개 `--doc` option으로 재실행해 성공했으며, 동일한 “검증 명령 환경·공개 option을 확인하지 않고 실행” 원인은 `failures/windows-validation-command-assumptions.md`의 재발 이력에 병합했다.
- 중단된 blind 검증은 도구 실패가 아니라 사용자의 검증 방식 변경이며 결과를 만들지 않았으므로 실패 지식으로 승격하지 않는다.

최종 검증 증거:

- `python -m unittest discover -s tests -v`: 119 tests, OK
- `document-data-validate`: block 6
- `artifact-check`: artifact 20, drift 0
- `legacy-data-verify`: records 211·manifest 22,577 bytes·tree `ce045997...34b4`, lifecycle 157행·work 36행 baseline 일치
- `maintenance-verify`: errors·drift·duplicates 0, inventory match, runtime warning 없음
- `git diff --check`: 통과

| 평가 항목 | 배점 | 자체 점수 | 근거 | 감점 원인·조치 |
|---|---:|---:|---|---|
| 사용자 목적·요구사항 정합성 | 20 | 20 | 문서 정본·에이전트 자율 실행·보고·현재 self-review 예외를 SR-01~SR-27과 실제 산출물에 연결 | 없음 |
| 실제 기능·검증 신뢰도 | 20 | 19 | 119 tests와 5개 통합 검증군, 실제 production 실패 경로, X01 자동 대조 통과 | 사용자 지시로 이번 작업의 독립 교차검증이 제외돼 자체 검토만 사용 `-1` |
| 단계 범위·안전 경계 | 20 | 20 | 보호 경계 접근 0, legacy 쓰기·삭제 0, 외부 게시·push 0 | 없음 |
| 단일 정본·문서 일관성 | 20 | 19 | active fact는 문서 owner, artifact 20 rebuild, handoff current block 단일 상태 owner | exact 원문을 복구할 수 없는 legacy 역사 값은 문서 의미 owner와 별개로 frozen bytes에 남음 `-1` |
| 유지보수성·인지 복잡성 | 20 | 18 | public 우회 제거, 명시 opt-in, 실패 fanout 0, 다음 행동 단일화 | read-only legacy 호환층과 긴 Stage 10 역사 owner를 당장 삭제·분할하지 않아 비용 잔존 `-2` |
| **총점** | **100** | **96** | 차단 결함 0, 잔여 감점은 공개된 승인 제외·legacy 역사 비용 | **완료 준비** |

**판정:** 10R-F는 통과다. 10R-G는 사용자 최신 예외로 독립 교차검증을 제외하고 전체 자체 재검토로 대체해 통과했다. 10R-H는 새 자체 점수 96점과 차단 결함 0으로 `완료 준비`다. Stage 10 전체 `완료` 표시는 사용자 확인과 §6.5 경계 커밋 성공 뒤에만 가능하다.

#### 2026-07-24 사용자 요청 선행 자체 재검토 — 현재 판정

사용자가 Claude 교차검증보다 먼저 주 작업 Codex의 자체 검증을 지시해, 이전 자체 판정이나 테스트 통과 수를 전제로 삼지 않고 요구사항 기준서, 전체 Stage 10 owner, 실제 diff, writer·reader 경계와 로컬 통합 게이트를 다시 대조했다.

현재 finding:

| 심각도 | 근거 | 영향 | 현재 판정 |
|---|---|---|---|
| High | `RecordStore._for_test(project_root)`는 전달된 root가 active project인지 격리 fixture인지 확인하지 않고 private write capability를 발급한다. `tests/test_cli_entry.py`도 같은 capability를 `file_data.cli.main()`에 주입하면서 임의 `--root`를 그대로 받는다. 실제 프로젝트 root로 `_for_test`를 생성하고 `_require_writable_test_root()`를 호출한 무변경 반례가 성공했다. | 테스트 코드나 잘못된 호출이 실제 `data/records`·`data/events`에 새 legacy 사실을 쓸 수 있다. 따라서 production 기본 writer 차단만으로 `legacy 새 쓰기 0`, `기본 writer 의존 0`, 보호 경계 위반 0을 증명할 수 없다. | **미해결·완료 차단**. capability 발급자가 active project root를 fail-closed로 거부하고 격리 fixture임을 구조적으로 증명하도록 보완한 뒤, 실제 root 거부와 임시 fixture 성공 회귀가 필요하다. |
| Medium | `SESSION_HANDOFF.md` 상단·work block은 완료 준비와 blocker 0을 말하면서 §5 첫 문장은 “현재 Stage 10 완료를 막는 핵심 요구 누락이 있다”고 말했다. | 단일 현재 상태 owner가 서로 다른 완료 상태를 표현했다. | **수용·문서 판정 갱신으로 해소**. 핸드오프 전체를 현재 High 1과 보완 대기로 통일한다. |

재실행한 로컬 증거:

- 전체 회귀: `Ran 119 tests ... OK`
- `document-data-validate`: block 6
- `artifact-check`: artifact 20, drift 0
- `legacy-data-verify`: records 211, lifecycle 157행, work 36행, baseline 일치
- `maintenance-scan`: drift 0, duplicates 0, inventory match
- `maintenance-verify`: errors 0, 문서 89, 링크 648, Python 15, schema 13
- `git diff --check`: 추적 변경 통과
- 미추적 Stage 10 문서·Python의 별도 trailing whitespace·strict UTF-8·NUL 검사: 오류 0

통과한 로컬 검증은 현재 저장소가 이미 손상됐다는 뜻이 아니라, 기존 테스트가 위 capability 발급 우회를 포함하지 않는다는 증거다. 차단 finding을 점수로 상쇄하지 않는다.

| 평가 항목 | 배점 | 현재 점수 | 근거 | 감점 원인·조치 |
|---|---:|---:|---|---|
| 사용자 목적·요구사항 정합성 | 20 | 18 | 문서 정본·자율 운영·보고 구조는 구현됨 | 핵심 `legacy 새 쓰기 0`이 모든 호출 경로에서 강제되지 않음 `-2` |
| 실제 기능·검증 신뢰도 | 20 | 17 | 전체 119 tests와 5개 통합 검증군 통과 | 회귀가 test-only capability의 active root 사용을 검출하지 못함 `-3` |
| 단계 범위·안전 경계 | 20 | 15 | 기본 production 서비스·CLI는 read-only로 실패 | test factory·test CLI를 통한 실제 root write capability 발급 가능 `-5` |
| 단일 정본·문서 일관성 | 20 | 19 | 문서 block·artifact·legacy baseline은 일치 | 핸드오프 상태 충돌을 이번 검토에서 발견·교정 `-1` |
| 유지보수성·인지 복잡성 | 20 | 19 | 문서 owner와 explicit legacy read 경로가 분리됨 | capability 안전성이 이름·호출 규율에 의존 `-1` |
| **총점** | **100** | **88** | 로컬 게이트는 통과했지만 High 1 미해결 | **실패·보완 필요** |

**현재 판정:** 이전 10R-F·10R-G 통과와 10R-H 96점·완료 준비 판정은 이 후속 자체 재검토로 철회한다. 현재는 High 1을 보완하고 관련 회귀와 전체 게이트를 다시 통과하기 전까지 Stage 10을 완료하거나 경계 커밋할 수 없다.

#### 2026-07-24 후속 High 1 보완·최종 자체 재검토

사용자가 보완 작업의 계속 진행을 명시해, 위 자체 재검토에서 확인한 test-only write capability 우회를 구현·회귀·통합 게이트·문서 판정 순서로 보완했다. 이번 최종 판정은 사용자 최신 예외에 따라 Claude와 Codex 서브에이전트 교차검증을 사용하지 않고 주 작업 Codex의 전체 diff 자체 재검토가 소유한다.

구현과 회귀:

- 전역 test capability를 writer가 곧바로 신뢰하지 않고, 시스템 임시 디렉터리 아래의 exact fixture root에 결합한 `_BoundIsolatedTestWriteCapability`로 전환했다.
- 현재 source project root 또는 그 하위는 실행 위치와 관계없이 거부하고, 결합된 capability를 다른 임시 root에 재사용하는 경우도 `legacy_read_only`로 실패한다.
- `RecordStore._for_test`, test CLI 주입 경로, private atomic writer가 같은 binding 검사를 사용한다. production의 capability 없음 경로는 계속 read-only다.
- 회귀는 active project root의 `_for_test` 거부, `tests/test_cli_entry.py --root <active-root> init`의 exit 2·`legacy_read_only`, 두 임시 root 사이 capability 재사용 거부를 직접 확인한다. 기존 임시 fixture create/update/event와 임시 Git maintenance fixture는 유지된다.

보완 중 첫 경계안은 fixture가 프로젝트 문서 또는 `.git`을 가질 수 없다고 과도하게 가정해 maintenance 15건을 거부했다. 실제 fixture 계약을 확인한 뒤 이름·marker heuristic을 제거하고 `Path(__file__)`로 확인되는 source project tree와 시스템 임시 root의 구조적 관계만 사용하도록 교정했다. 별도 집중 테스트와 전체 회귀를 처음부터 다시 실행해 해결을 확인했다.

최종 diff 자체 검토에서는 active root 회귀가 현재 Windows 오류 문구만 단언해 source checkout 자체가 시스템 임시 경로 아래인 환경에서 올바른 다른 거부 문구를 실패로 오인할 수 있음을 찾았다. 회귀를 `LegacyReadOnlyError` 유형과 CLI의 `legacy_read_only` kind에 고정하고 전체 게이트를 다시 통과시켜 환경 의존 Low 1도 해소했다.

최종 검증 증거:

- `python -m unittest discover -s tests -v`: **120 tests, OK**
- active root 무변경 반례: `_for_test`와 test CLI 모두 `legacy_read_only`
- `document-data-validate`: block 6
- `artifact-check`: artifact 20, drift 0
- `legacy-data-verify`: records 211·manifest 22,577 bytes·tree `ce045997...34b4`, lifecycle 157행·work 36행 baseline 일치
- `maintenance-scan`: drift 0, duplicates 0, inventory 12,527 bytes match, runtime warning 없음
- `maintenance-verify`: errors 0, documents 89, links 648, Python 15, schema 13
- `git diff --check`: 통과
- 보호 `inputs/`·`outputs/`·`backup/` 추가 접근 0, legacy data 쓰기·삭제 0, 외부 변경 0

| 평가 항목 | 배점 | 최종 자체 점수 | 근거 | 감점 원인 |
|---|---:|---:|---|---|
| 사용자 목적·요구사항 정합성 | 20 | 20 | 문서 정본·에이전트 자율 실행·보고·legacy 새 쓰기 0을 실제 경로와 회귀에 연결 | 없음 |
| 실제 기능·검증 신뢰도 | 20 | 19 | 120 tests, active root·CLI·타 root 반례, 5개 통합 검증군 통과 | 사용자 지시로 이번 작업의 독립 교차검증 제외 `-1` |
| 단계 범위·안전 경계 | 20 | 20 | production read-only, test root binding, 보호 경계·legacy bytes 보존 | 없음 |
| 단일 정본·문서 일관성 | 20 | 19 | 문서 block·artifact·handoff 현재 상태 일치 | 복구 불가능한 legacy exact 역사 값 잔존 `-1` |
| 유지보수성·인지 복잡성 | 20 | 18 | root-bound capability와 단일 공통 guard, 실패 재사용 기록 | read-only legacy 호환층과 긴 Stage 10 역사 owner 비용 잔존 `-2` |
| **총점** | **100** | **96** | **High 0·Medium 0·Low 0, 차단 결함 0** | **완료 준비** |

**최종 판정:** 10R-F와 10R-G는 통과했고 10R-H는 96점·차단 결함 0으로 `완료 준비`다. Stage 10의 공식 `완료`는 사용자 확인과 §6.5 경계 커밋 성공 뒤에만 표시한다.
