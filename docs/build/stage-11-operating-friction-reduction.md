# Stage 11 — 운영 마찰·인지 복잡성 축소

- 문서 유형: 활성 단계 계획·진단·실행·최종 보고 단일 owner
- 목적: 실제 도메인 작업 전에 과도해진 필수 읽기, 승인·검증 게이트, 실패 기록, 활성 문서 표면을 줄여 안전 경계 안에서 에이전트가 더 빠르게 자율 작업하도록 만든다.
- 읽는 시점: Stage 11 착수·단계 전환·성공 게이트·최종 보고·재개 시
- 책임: 프로젝트 에이전트가 사용자의 2026-07-24 지시에 따라 계획·구현·검증·커밋한다.
- 상태: **11C 완료 준비·경계 커밋 대기**
- 현재 상태 정본: [SESSION_HANDOFF](../../SESSION_HANDOFF.md)
- 상위 순서: [마스터 구축 계획](MASTER_BUILD_PLAN.md)

## 1. 사용자 지시와 권장 기본값

사용자는 실제 프로젝트 작업이 시작되지 않았는데 문서와 규칙이 너무 많고, 간단한 작업도 오래 걸리는 원인을 분석해 개선 계획을 세우고 실행하라고 지시했다. 필요 이상으로 강제하는 규칙·기능은 제거하고, 에이전트의 추론과 자율성을 방해하는 규칙은 같은 안전 목적을 유지하면서 자율적인 결과로 수정해야 한다.

이번 작업은 다음 사용자 지시를 하나의 연속 승인으로 사용한다.

- 구현 전에 plan 문서를 작성한다.
- 우선순위와 단계를 정하고, 각 단계 시작 전에 해당 작업 규칙을 다시 읽는다.
- 각 단계에 성공 게이트를 두고 자체 재검증으로 완료를 확인한다.
- 각 단계가 끝날 때마다 실제 작업 내용을 설명하는 Git 커밋을 남긴다.
- 모든 구현 뒤 이 문서에 최종 작업 보고와 자체 점수를 기록한다.
- 보고 뒤 이번 세션의 재사용 교훈을 규칙 문서에 반영하고 별도 커밋한다.
- 모든 작업·검증·커밋이 끝난 뒤 컴퓨터 전원을 종료한다.
- 별도 선택이 필요하면 안전하고 가역적인 권장안을 사용한다.

권장 기본값은 다음과 같다.

1. 기존 기반 전체를 철거하지 않고 일상 작업의 기본 경로에서 필수로 읽거나 실행하는 제어면을 먼저 줄인다.
2. 보호 데이터, legacy record·event bytes, `backup/`, 실제 유튜브 도메인 기능은 변경하지 않는다.
3. 새 계획·진단·실행·최종 보고는 이 문서 하나가 소유한다. 별도 진단 보고서나 단계별 보고서를 만들지 않는다.
4. 완료된 역사 문서는 보존하되 기본 작업 경로와 현재 상태 화면에서 분리한다.
5. 독립 서브에이전트 검증은 이번 사용자 지시에 없으므로 사용하지 않고, 각 게이트에서 주 작업 에이전트가 전체 diff와 실제 검증 결과를 재확인한다.

## 2. 작성 전 기준선

기준선은 보호 경로 segment를 제외한 `git ls-files`와 실제 파일 읽기로 측정했다.

| 항목 | 기준값 | 해석 |
|---|---:|---|
| 추적 파일 | 349개 | JSON 231, Markdown 89, Python 25, JSONL 2, 저장소 설정 2 |
| 유지 Markdown | 89개·920,687 bytes·10,295줄 | 실제 도메인 운영 전 제어·구축·보고 문서가 이미 큰 표면을 형성 |
| `docs/` | 38개·418,269 bytes·4,975줄 | 계약과 11개 구축 단계 owner가 누적 |
| `reports/` | 14개·352,283 bytes·3,529줄 | 기본 실행 지시는 아니지만 전체 문서 표면에 함께 노출 |
| `failures/` | 27개·90,630 bytes·1,188줄 | 사소한 검증 명령 실수까지 재발 이력으로 누적될 수 있음 |
| 세션 시작 3문서 | 38,739 bytes·412줄 | `SESSION_HANDOFF.md` 하나가 28,258 bytes·302줄 |
| Stage 10 owner | 137,011 bytes·1,133줄 | 완료된 개선의 재시도·finding 역사가 한 파일에 누적 |
| 작업 규칙 | 6개·14,216 bytes·121줄 | 행동이 겹치면 여러 규칙과 마스터 게이트가 연쇄 적용 |
| Git 기준선 | `feature/refactorying_4th_extra`, clean | 보호·무관 사용자 변경 없음 |

## 3. 원인 분석

### C1. 현재 상태 문서가 역사 보고서가 됨

`SESSION_HANDOFF.md`의 목적은 현재 단계·blocker·첫 다음 행동을 재구성하는 것이지만, 완료된 Stage 10의 체크포인트·실패·교차검증 역사가 302줄로 남아 있다. 동일한 상세 근거는 Stage 10 owner와 Git 이력에도 존재한다. 모든 새 세션이 이 중복 역사를 필수로 읽으므로 가장 직접적인 시작 지연이다.

### C2. 구축 단계용 통제가 일상 작업에도 전파됨

`stage-work`와 마스터 계획은 번호 단계마다 마스터·현재 단계 owner 완독, 네 가지 공통 확인, 실패 원장 조정, 100점 채점, 상태 갱신, 경계 커밋을 요구한다. 대규모 구축에는 유용하지만 간단한 문서·코드 수정에도 같은 절차가 적용되면 작업 결과보다 통제 기록이 커진다.

### C3. 검증이 위험이 아니라 쓰기 횟수에 비례함

`document-work`는 매 write 뒤 UTF-8·NUL·절·링크·공백·전체 diff를 다시 확인하도록 하고, 단계 종료 규칙은 다시 전체 게이트를 실행한다. 논리적 변경 묶음이 아니라 파일 저장 횟수마다 검증 비용이 발생한다.

### C4. 실패 기록의 승격 기준이 너무 낮음

현재 `failure-records`는 작업 중 발생한 모든 실패를 분류하고 해결된 실패를 장기 정본에 반영하도록 한다. `windows-validation-command-assumptions.md`는 단발성 옵션·인용·경로 실수까지 긴 재발 표로 누적됐다. 재사용 가치가 낮은 한 번의 도구 실수가 새 문서 갱신·색인·직접 검증·커밋 범위를 만든다.

### C5. 현재·참조·역사가 한 화면에 섞임

생성 inventory는 완료 단계와 시점 보고서를 포함한 모든 Markdown을 한 목록에 둔다. Stage 00~09용 수동 Obsidian 단계 보기 11개는 Stage 10에서 이미 read-only legacy로 판정됐고 새 generator도 없지만 계속 유지된다. 사용자가 “지금 필요한 문서”와 “과거 근거”를 구분하기 어렵다.

### C6. 자율성 규칙과 절차가 서로 반대 방향으로 작동함

상시 정책은 안전하고 가역적인 세부를 에이전트가 자율 결정하라고 하지만, 하위 절차는 광범위한 사전 기록·고정 게이트·세부 실패 승격을 강제한다. 결과적으로 에이전트가 합리적인 기본값을 선택해 바로 검증하기보다 규칙 준수 문서를 먼저 생산하게 된다.

## 4. 목표 운영 모델

### 4.1 세 가지 작업 등급

| 등급 | 적용 조건 | 기본 산출물·검증 |
|---|---|---|
| `quick` | 한두 파일의 안전하고 가역적인 로컬 수정, 정책·보호·외부 영향 없음 | 관련 owner와 한 작업 규칙만 읽고, 대상 diff·직접 관련 검사만 수행. 별도 plan·점수·실패 문서 없음 |
| `standard` | 여러 파일 또는 동작 변경이지만 보호·외부·비가역 경계 없음 | 짧은 실행 계획, 관련 테스트·문서 검증, 현재 상태가 바뀔 때만 handoff 갱신. 번호 Stage와 100점표는 기본 요구 아님 |
| `controlled` | 정책·구조·보호 데이터·삭제·외부 영향·복구 비용이 크거나 사용자가 단계·게이트를 명시 | 단일 initiative owner, 명시 성공 게이트, 통합 검증, 필요 시 점수·경계 커밋 |

이번 Stage 11은 규칙 변경·문서 제거·단계별 커밋을 포함하고 사용자가 full gate를 명시했으므로 `controlled`다. 이후 일상 작업은 가장 낮은 충분 등급을 에이전트가 선택하고 이유를 간단히 보고한다.

### 4.2 완료 목표

- 세션 시작 3문서를 합쳐 20,000 bytes·200줄 이하로 줄인다.
- `SESSION_HANDOFF.md`는 12,000 bytes·140줄 이하에서 현재 work·blocker·첫 다음 행동만 소유한다.
- 일반 `quick` 작업은 마스터 계획·완료 stage owner·100점표·경계 커밋·독립 검증을 기본으로 요구하지 않는다.
- 문서 검증은 매 저장이 아니라 논리적 변경 묶음의 완료 checkpoint에서 수행한다.
- 장기 실패 문서는 재발 가능하고 일반화 가능한 원인, 또는 작업을 실제 차단한 중대한 실패만 승격한다.
- 완료된 수동 Obsidian 단계 보기 11개를 제거하고, 마스터 계획과 stage owner가 역사를 소유한다.
- 현재 문서와 역사·참조 문서를 사용자 진입 화면에서 명확히 분리한다.
- 보호 경계, 비밀정보 금지, 외부·비가역 행동 승인, unrelated change 보존은 약화하지 않는다.
- 전체 회귀·maintenance·문서 링크·Git 보호 경계가 최종 통과한다.

## 5. 범위와 정확한 제거 대상

### 포함

- `AGENTS.md`, `PROJECT_RULES.md`, `rules/*.md`의 라우팅·자율성·게이트·실패 승격 기준
- `docs/build/MASTER_BUILD_PLAN.md`의 완료된 구축 체계와 향후 작업 등급 경계
- `SESSION_HANDOFF.md`의 현재 상태 전용 축약
- `README.md`, 정보 구조·Obsidian router·유지보수 계약의 현재/역사 구분
- 생성 inventory 재생성
- 이번 계획·실행·최종 보고·점수와 세션 교훈

### 제거 대상

다음 11개 link-only 과거 단계 보기는 각 stage owner와 Git 이력으로 대체되므로 삭제한다.

- `docs/obsidian/stages/stage-00.md`
- `docs/obsidian/stages/stage-01.md`
- `docs/obsidian/stages/stage-01-5.md`
- `docs/obsidian/stages/stage-02.md`
- `docs/obsidian/stages/stage-03.md`
- `docs/obsidian/stages/stage-04.md`
- `docs/obsidian/stages/stage-05.md`
- `docs/obsidian/stages/stage-06.md`
- `docs/obsidian/stages/stage-07.md`
- `docs/obsidian/stages/stage-08.md`
- `docs/obsidian/stages/stage-09.md`

### 제외

- `inputs/`, `outputs/` 열거·열람
- `backup/` 열람·수정
- `data/records`, `data/events`의 삭제·수정·이관
- 실제 유튜브·콘텐츠·운영 기능의 착수
- 새 플러그인·DB·검색 서비스·CI·예약 작업
- branch 생성·push·배포·외부 게시
- 완료 단계 owner와 시점 보고서의 대량 이동·삭제

## 6. 우선순위와 단계

| 순서 | 단계 | 핵심 작업 | 성공 게이트 | 경계 커밋 |
|---:|---|---|---|---|
| 1 | 11A 진단·plan | 기준선·원인·등급·범위·정확한 제거 대상·게이트를 이 owner에 확정하고 master·handoff 연결 | plan이 구현보다 먼저 존재, 기준값 재현, 범위·제외·복구 경로 명시, 문서·inventory 검증 통과 | `docs: Stage 11 운영 단순화 계획 수립` |
| 2 | 11B 규칙·게이트 경량화 | 자율성 우선 작업 등급, batch 검증, 중요 실패만 승격, 일상 작업의 stage/점수/subagent 비강제화 | 보호·외부·파괴 경계 유지, quick 대표 흐름이 startup+관련 rule만으로 결정 가능, 중복·충돌 0, 관련 검증 통과 | `refactor: Stage 11 작업 규칙과 게이트 경량화` |
| 3 | 11C 활성 문서 표면 축소 | handoff 축약 검증, 과거 stage view 11개 제거, 사용자 router의 현재/역사 분리, 과도한 실패 이력 축약 | 삭제 대상 exact 11개 외 삭제 0, startup 목표 달성, 끊어진 링크 0, inventory 일치, 대표 재개 흐름 성공 | `refactor: Stage 11 활성 문서 표면 축소` |
| 4 | 11D 통합 검증·최종 보고 | 전체 회귀·maintenance·보호 경계·Git diff·전후 지표를 재검증하고 이 문서에 보고·점수 기록 | 모든 필수 검사 성공, High·Medium 미해결 0, 자체 점수 95 이상, 실패 정리 완료 | `docs: Stage 11 최종 보고와 자체 평가` |
| 5 | 11E 세션 교훈 규칙 반영 | 실제 실행에서 확인된 남은 마찰만 규칙 owner에 최소 반영하고 상태 종료 | 새 규칙이 기존 11B 의미를 복제하지 않음, 전체 관련 검증 재통과, handoff 완료·next action null, worktree 경계 확인 | `docs: Stage 11 실행 교훈 규칙 반영` |
| 6 | 전원 종료 | 11A~11E commit 객체·포함 경로·보호 경로 0·최종 worktree를 확인한 뒤 종료 | 모든 커밋 성공과 최종 상태 확인 전에는 실행하지 않음 | 커밋 없음 |

사용자의 현재 지시는 11A~11E 연속 진행과 각 성공 게이트 뒤 경계 커밋을 승인한다. 범위가 보호 데이터·외부 쓰기·legacy 삭제·실제 도메인 작업으로 확대되면 이 승인을 사용하지 않는다.

## 7. 단계 공통 자체 재검증

각 단계 시작 전에 `stage-work`, `failure-records`, `document-work`, `version-control`의 현재 버전을 다시 읽는다. 규칙이 11B에서 바뀐 뒤에는 새 버전을 사용한다.

각 성공 게이트 직전 다음을 한 번의 논리적 checkpoint로 수행한다.

1. 사용자 목적과 실제 diff를 대조한다.
2. 단계에 직접 관련된 대표 정상·실패 흐름을 실행한다.
3. 보호·역사·외부·삭제 범위와 무관 변경이 없는지 확인한다.
4. 발생한 실패를 현재 유효한 승격 기준으로 분류한다.
5. 변경 문서의 strict UTF-8, NUL 0, 후행 공백, 로컬 링크, generated inventory를 확인한다.
6. `git diff --check`와 단계 경계에 맞는 테스트를 실행한다.
7. 자체 검토에서 발견한 in-scope 결함을 고친 뒤 동일 checkpoint를 처음부터 다시 실행한다.
8. gate 통과 뒤에만 해당 단계 파일을 명시적으로 stage하고 commit 객체·포함 경로·보호 경로 0을 검증한다.

## 8. 복구 전략

- 모든 변경은 단계별 Git 커밋으로 분리한다.
- 삭제할 11개 문서는 각 `docs/build/stage-*.md`와 Git 이력에 동일한 역사 진입점이 있는지 먼저 확인한다.
- 규칙 변경 뒤 대표 quick 흐름이 모호하거나 안전 경계가 약해지면 11B 안에서 문구를 보정하고 전체 11B 게이트를 반복한다.
- maintenance나 전체 회귀가 실패하면 원인을 해결하기 전 다음 단계로 진행하지 않는다.
- legacy data bytes와 보호 경로는 복구 대상이 생기지 않도록 처음부터 쓰지 않는다.

## 9. 실행 기록

### 11A 진단·plan

- 이 문서를 첫 persistent write로 생성한 뒤에만 master·handoff 연결을 변경했다.
- 기준선은 Markdown 89개·920,687 bytes·10,295줄, 세션 시작 3문서 38,739 bytes·412줄, handoff 28,258 bytes·302줄로 재현했다.
- 완료된 Stage 10의 상세 이력을 기존 Stage 10 owner와 Git에 남기고, handoff는 Stage 11 현재 work 중심 5,698 bytes·113줄로 정규화했다.
- master에 Stage 11 한 행과 이 owner 링크만 추가하고, generated inventory를 12,692 bytes로 재생성했다.
- 첫 Git 기준선 조회의 `safe.directory` 누락과 첫 stage 호출의 공백 경로 인용 누락은 기존 `windows-validation-command-assumptions`의 동일 Windows Git 인수 원인으로 분류하고 해결 이력 한 행에 합쳤다.

11A 성공 게이트:

| 확인 | 결과 |
|---|---|
| plan 선행 | 통과 — 계획 owner가 다른 Stage 11 구현 변경보다 먼저 생성됨 |
| 범위·복구 | 통과 — exact 제거 11개, 보호·legacy·외부 제외, 단계별 Git 복구 경계 명시 |
| 문서 데이터 | 통과 — `project-data:v1` 6 blocks, work 1과 kind count 일치 |
| 실패 정본 | 통과 — 갱신한 canonical failure 직접 검증 성공 |
| maintenance | 통과 — documents 90, links 655, errors·drift·duplicates 0, inventory 일치, runtime warning 없음 |
| Git·문서 품질 | 통과 — `git diff --check`, strict UTF-8·NUL·후행 공백·링크 검사가 오류 0 |
| 자체 finding | High 0·Medium 0·Low 0 |

**11A 판정: 완료 준비.** 경계 커밋이 성공하기 전 11B를 시작하지 않는다.

11A 경계 커밋은 `5c322cdfae6764080a29a0fd71679c92b26c6cc9`이며 포함 경로 5개, 보호 경로 0, 커밋 후 clean을 확인했다.

### 11B 규칙·게이트 경량화

- `AGENTS.md`와 상시 정책에 `quick / standard / controlled`를 도입하고 가장 낮은 충분 등급을 기본값으로 고정했다.
- `quick`·`standard`에서는 번호 Stage, master, 점수, subagent, 별도 보고서, 경계 commit을 자동 요구하지 않는다.
- 문서 검증은 file save마다가 아니라 logical batch checkpoint에서 수행하고 full maintenance는 controlled 구조 작업 또는 exact plan 요구로 제한했다.
- failure 정본은 재발·안전/정확성 영향·비자명한 해결·실질 차단 중 하나를 충족할 때만 승격하며, 일회성 오타·인용·option·path 실수는 기본적으로 transient가 됐다.
- master는 번호 controlled stage에만 적용하도록 20,438 bytes·255줄에서 8,968 bytes·137줄로 축약했다.
- startup router·상시 정책·task rules 6개의 합계는 24,697 bytes·231줄에서 16,186 bytes·210줄로 줄었다. 안전 전용 `history-review`와 `user-data-work`는 변경하지 않았다.
- 최신 요구 기준의 UR-12·16·17·19와 O-09·Stage 11 지도를 새 기본 경로에 맞췄다.

11B 성공 게이트:

| 확인 | 결과 |
|---|---|
| quick 대표 흐름 | 통과 — 안전한 로컬 문서 수정은 startup+`document-work`만으로 결정, master·score·subagent·commit 비강제 |
| controlled 안전 흐름 | 통과 — 정책·삭제·보호·외부·복구 비용은 controlled 또는 사전 확인 |
| 계약 정적 검사 | 통과 — 11개 자율성·batch·failure threshold·안전 assertion 전부 true |
| 문서 데이터 | 통과 — 6 blocks, work 1과 kind count 일치 |
| maintenance | 통과 — documents 90, links 657, errors·drift·duplicates 0, inventory 일치, runtime warning 없음 |
| 범위 | 통과 — legacy data·보호 경로·외부 변경·코드 변경 0 |
| 실패·자체 finding | material failure 없음, High 0·Medium 0·Low 0 |

**11B 판정: 완료 준비.** 경계 커밋이 성공하기 전 11C를 시작하지 않는다.

11B 경계 커밋은 `153758f68cdec69f52ba72f3e6c4296406cec8b6`이며 포함 경로 10개, 보호 경로 0, 커밋 후 clean을 확인했다.

### 11C 활성 문서 표면 축소

- 계획에 exact 승인된 Stage 00~09 link-only Obsidian 보기 11개만 제거했다. 각 실제 stage owner와 master owner 표, Git 이력은 보존했다.
- `START_HERE`는 현재 work·현재 initiative·startup 정책을 먼저 보여주고, 전체 inventory와 완료 역사는 필요할 때만 연결한다.
- generated inventory의 이름과 계약을 “활성 문서”에서 “전체 추적 문서”로 교정해 완료 stage·시점 보고서가 active owner로 오인되지 않게 했다.
- `README`, `DOCUMENT_MAP`, Obsidian 계약, 정보 구조, maintenance 계약을 current/history 경계에 맞게 축약했다.
- `windows-validation-command-assumptions`는 18,929 bytes·122줄에서 3,149 bytes·48줄로 줄이고 공통 원인·대표 recurrence·검증·재사용 규칙만 보존했다.
- startup 3문서는 38,739 bytes·412줄 기준선에서 10,086 bytes·151줄로 감소했다. handoff는 28,258 bytes·302줄에서 2,783 bytes·49줄로 감소해 두 목표를 모두 통과했다.
- 전체 Markdown은 89개·920,687 bytes·10,295줄에서 79개·856,433 bytes·9,838줄로 감소했다. Stage 11 단일 owner 1개를 추가한 상태의 순감소다.

11C 성공 게이트:

| 확인 | 결과 |
|---|---|
| exact 삭제 | 통과 — 승인된 11개와 actual delete set exact match, 그 밖의 삭제 0 |
| current/history | 통과 — current는 START_HERE·handoff·Stage 11, 전체 tracked history는 inventory·master로 분리 |
| startup 목표 | 통과 — 10,086 bytes ≤20,000, 151줄 ≤200; handoff 2,783 bytes·49줄 |
| failure compaction | 통과 — canonical parser 성공, 원인·해결·검증·예방·근거 유지 |
| targeted 회귀 | 통과 — `test_maintenance.py` 15 tests OK, artifact 20 drift 0 |
| maintenance | 통과 — documents 79, links 421, errors·drift·duplicates 0, inventory 11,942 bytes 일치 |
| 문서 데이터·Git | 통과 — 6 blocks·work 1, `git diff --check`, 보호·legacy·외부 변경 0 |
| 자체 finding | 초기 startup lines 초과 Low 1을 handoff 재축약으로 보완, 최종 High 0·Medium 0·Low 0 |

**11C 판정: 완료 준비.** 경계 커밋이 성공하기 전 11D를 시작하지 않는다.

11A~11E의 이후 실제 변경, 검증 결과, 실패·판정, 커밋은 이 절에 계속 누적한다. 같은 사실을 별도 단계 보고서로 복제하지 않는다.

## 10. 최종 작업 보고·자체 점수

모든 구현이 끝난 뒤 전후 지표, 제거·수정 내용, 검증 수준, 잔여 위험, 실패 정리와 100점 자체 평가를 이 절에 기록한다. 점수 항목은 사용자 목적 정합성, 실제 검증 신뢰도, 안전·범위, 문서 일관성, 유지보수성·인지 복잡성을 각 20점으로 사용하며 차단 결함이 있으면 점수와 무관하게 실패다.

## 11. 이번 세션의 규칙 반영

최종 보고 커밋 뒤, 실행 과정에서 실제로 재발한 마찰만 기존 rule owner에 최소 반영한다. 계획만으로 추정한 규칙을 새 파일로 만들지 않는다.
