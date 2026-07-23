# Stage 10 — 에이전트 자율 운영·구조 최적화

- 문서 유형: 활성 단계 계획·진단·완료 근거
- 목적: 사람의 수동 생산 작업을 없애고 에이전트가 승인 범위 안에서 조사·설계·구현·검증·복구를 자율 수행하도록 운영 경계를 보정하며, 같은 사실이 여러 파일과 record로 증식하는 구조를 줄인다.
- 사용 시점: Stage 10 착수·체크포인트·종료, 운영 권한 또는 실패 지식 구조를 변경할 때
- 작성 책임: 프로젝트 에이전트
- 승인 근거: 사용자의 2026-07-23 최신 지시
- 상태: 완료
- 현재 상태 정본: [SESSION_HANDOFF](../../SESSION_HANDOFF.md)
- 공통 게이트: [마스터 구축 계획 §6](MASTER_BUILD_PLAN.md#6-공통-승인-게이트)

## 1. 최신 사용자 의도와 단계 목표

사용자가 이번 단계에서 명시한 최상위 의도는 다음과 같다.

> “사람의 수동작업이 없이 모든작업을 agent 의 자율성에 맡겨 생산성을 극한으로 끌어올리기 위함”

> “프로젝트의 데이터구성은 agent 가 작업을 명확하게 하기 위한 방향으로 최적화되어있어야 하고, 작업 과정들에 대해 사람에게 보고하고 요청하고 확인받아야 된다는 얘기”

따라서 데이터 기반 지식 운영 기반은 최종 목적 자체가 아니라 **에이전트가 채팅 기억과 사람의 수동 실행에 의존하지 않고 정확히 일하기 위한 수단**이다. 사람은 목표·금지·보호·외부 영향·되돌리기 어려운 결정과 결과 확인을 맡고, 에이전트는 그 경계 안의 가역적 로컬 작업과 실패 복구를 스스로 수행한다.

완료 후에는 다음이 가능해야 한다.

1. 에이전트가 안전한 기본값과 구현 세부를 스스로 선택하고 근거와 결과를 보고한다.
2. 새 사람 승인 없이 진행하면 안 되는 경계가 위험·권한·범위 기준으로 명확하다.
3. 한 개선 작업의 진단·계획·구현·점수·Claude 검증이 이 문서 하나에서 이어진다.
4. 해결된 실패 Markdown은 별도 source·projection·lifecycle record 없이 직접 검증·검색·재사용된다.
5. 새 단계와 실패가 생겨도 수동 파생 문서와 구조화 파일 수가 불필요하게 증가하지 않는다.

## 2. 선행조건과 입력

- Stage 00~09 성공 게이트와 경계 커밋 완료
- 사용자 최신 지시가 Stage 10 전체와 내부 단계의 연속 진행, Claude 교차검증, 95점 이상 보완을 승인
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
| 4 | 10D 통합 검증·교차검증 | 실제 전체 diff가 있어야 독립 검증과 점수 평가가 유효함 | 전체 회귀·maintenance·Claude review/challenge·보완 | 네 가지 확인 통과, Claude 지적 판정·보완, 자체 총점 95점 이상 |
| 5 | 10E 정합화·경계 종료 | 검증된 결과만 현재 상태와 Git 경계에 반영해야 함 | 핸드오프·실패 원장·inventory·diff·commit | 미해결 실패 0 또는 명시 blocker, 보호 변경 0, Stage 10 독립 커밋 검증 |

사용자의 이번 지시는 위 내부 단계 전체를 성공 게이트 뒤 연속 진행하는 상시 전환 승인이다. 각 게이트 결과는 같은 work와 이 문서에 남기고 범위가 달라지면 멈춰 확인한다.

## 6. 예상 산출물과 제외 범위

### 예상 산출물

- 이 Stage 10 단일 owner
- 갱신된 운영 규칙·요구사항·마스터 계획·정보 구조·Obsidian router
- 실패 정본 직접 검증·검색 구현과 회귀 테스트
- 간결한 현재 핸드오프와 재생성된 inventory
- 이 문서 안의 Claude 교차검증·네 가지 확인·최종 점수

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
8. 전체 diff를 Claude `review`와 `challenge` 모드로 각각 읽기 전용 교차검증한다.
9. Codex가 각 지적을 재현 가능한 근거로 판정하고 필요한 보완 뒤 전체 게이트를 반복한다.

## 8. 완료 조건

- 10A~10E 성공 게이트가 순서대로 통과
- 새 진단·계획·Claude 보고 문서가 이 파일 외 0개
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
| 에이전트는 과정·중요 판단·실패·결과를 사람에게 보고하고 필요한 요청·확인을 수행 | 2026-07-23 최신 지시 | 10A·10D·10E |
| 개선 plan을 인과 순서로 나누고 구현→Claude 교차검증→성공 게이트를 95점 이상까지 반복 | 2026-07-23 최신 지시 | Stage 10 전체 연속 진행 |

현재 구현을 차단하는 미확정 결정은 없다. 삭제·이동·legacy 대량 이관처럼 이번 범위를 넘는 행동은 제외했다.

## 10. 실행 기록

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

## 11. 네 가지 확인과 최종 점수

| 확인 항목 | 판정 | 확인 근거 | 남은 위험·후속 조치 |
|---|---|---|---|
| 사용자 목적 정합성 | 통과 | 최상위 목적·역할·보고·사전 확인 경계를 규칙·요구사항·단계 owner에 연결 | 삭제·대량 이관처럼 새 범위는 계속 별도 승인 |
| 실제 기능 작동 | 통과 | 99개 회귀, scan·verify, 실제 26:39 공존 대조, 무증식 결합 회귀 | legacy data 자체는 보존 |
| 미래 단계 선행 유입 방지 | 통과 | Stage 10 이후 파생 단계 보기 중단, 새 기능·DB·CI·외부 앱·유튜브 도메인 확장 0 | 다음 기능 단계는 자동 생성하지 않음 |
| 과거 실패 패턴 재발 방지 | 통과 | 단일 initiative owner, 자동 inventory, canonical failure 직접 parser, 파생 projection 생성 경로 차단 | Claude 래퍼 종료 오류는 별도 도구 개선 후보 |

| 평가 항목 | 배점 | 자체 점수 | 근거 | 감점 원인·조치 |
|---|---:|---:|---|---|
| 사용자 목적·요구사항 정합성 | 20 | 20 | 최신 의도와 역할·보고·승인 경계를 상위 owner에 연결 | 없음 |
| 실제 기능·검증 신뢰도 | 20 | 20 | 99개 회귀와 실제 저장소 공존 대조, Claude 지적 결합 회귀 통과 | 없음 |
| 단계 범위·안전 경계 | 20 | 20 | 보호·역사·외부·파괴 경계 위반 0, 미래 기능 유입 0 | 없음 |
| 단일 정본·문서 일관성 | 20 | 19 | initiative owner 1개, 실패 Markdown 직접 정본, 자동 inventory | legacy projection 39개는 역사 보존으로 남음 |
| 유지보수성·인지 복잡성 | 20 | 18 | 새 실패의 구조화 fanout 0, 수동 지도 축약, fail-closed 검증 | legacy read 호환 분기와 Claude 래퍼 불안정성 잔존 |
| **총점** | **100** | **97** | 네 가지 확인·Claude 교차검증·전체 자동 게이트 통과 | **95점 기준 충족, 차단 결함 0** |

## 12. 다음 단계 인계 조건

Stage 10 완료 뒤 새 기능 단계를 자동 생성하지 않는다. `SESSION_HANDOFF.md`는 검증된 운영 목적, 새 실패 지식 경로, 남은 legacy·Claude 래퍼 위험, 첫 다음 행동만 요약하고 이 문서의 완료 근거를 링크한다.
