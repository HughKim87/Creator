# Agent Core 남은 작업 통합 설계

- 목적: 규칙 거버넌스 개선을 최우선으로 두고 Agent Core와 Maintainer에 남은 필수 결함, 검증 게이트, 조건부 원격·Host 작업을 하나의 실행 기준으로 고정한다.
- 읽는 시점: 새 구현 단계를 설계하거나 시작할 때, 단계 완료와 프로젝트 종료 수준을 판정할 때.
- 책임: 작업 에이전트가 이 문서의 단계·게이트·범위만 구현하고, 사용자가 정책 의미·Core 변경·commit·외부 쓰기·원격 게시·Host 적용을 승인한다.
- 상태: 로컬 구현 후보 완료. 단계 4 최종 clean-clone gate 대기.
- 문서 분류: `overall-design`
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, `core/docs/ARCHITECTURE.md`, `core/docs/COMPATIBILITY.md`, `core/docs/VERIFICATION.md`.
- 종료 조건: 필수 단계가 끝나면 완료 설계로 전환하며, 완료 과정은 Git이 소유한다.

---

## 1. 설계 책임과 경계

이 문서는 전체 단계 구성, 의존 순서, 요구사항 추적, 단계별 성공 조건만 소유한다.

- 현재 단계·승인·차단·첫 다음 행동은 `SESSION_HANDOFF.md`가 소유한다.
- 단계별 정확한 변경 경로·명령·복구 방법은 단계 진입 시 별도 활성 단계 설계로 확정한다.
- 공통 정책과 작업 절차는 Core 정책·route된 규칙을 참조하고 이 문서에 복제하지 않는다.
- 완료된 Core contract v2 구현과 과거 실행 상세는 Core 정본과 Git 이력이 소유한다.
- 설계 승인 뒤 내용이 바뀌면 새 fingerprint를 기준으로 다시 승인받는다.

단계 실행 승인 시 이 파일의 SHA-256 또는 동등한 결정론적 fingerprint를 `SESSION_HANDOFF.md`에 기록한다. 승인 기준 fingerprint와 실행 결과는 `SESSION_HANDOFF.md`와 Git 이력이 소유하며, 현재 별도 활성 단계 설계는 없다.

## 2. 완료된 기준선

다음 설계·구현은 완료된 기준선이며 다시 수행하지 않는다.

- 순수 Core와 Consumer의 정책·상태·진입 책임 분리
- Core contract v2와 Core/Consumer 이중-root 검사
- Core 내부 `AGENTS.md`, `CLAUDE.md`, `SESSION_HANDOFF.md` 제거
- `AGENT_ENTRY`, `CONSUMER_GUIDE`, Consumer 계약 도입
- Core 0.3.0 / contract 2 공개 계약
- H1 환경변수 우회, H2 실행 보고, H3 route 결정론 수정
- Git 이력 정제와 원격 closeout

구조 검사의 통과는 최소 Python, 전체 회귀, 실제 원격 clone, 실제 Host 사용을 자동으로 증명하지 않는다.

## 3. 남은 필수 요구사항

| ID | 요구 | 확인된 실패 모드 | 소유 단계 | 완료 게이트 |
|---|---|---|---|---|
| `R0` | 규칙은 반복 작업의 품질 재현과 Agent 간 작업 방법 공유를 우선하고, 행동 제한은 꼭 필요한 위험 경계에만 둔다 | 규칙이 작업 방법보다 행동 제한과 검증 의무를 중심으로 작성되어 단순 작업에도 과도한 절차가 반복된다 | `P0` | 규칙 작성 원칙 승인, 공통 정본·route·자유도·제한 예외 기준 확정, 기존 규칙 영향 감사 |
| `R1` | L7 `shared_data`가 없어도 필수 Core가 성립한다 | 완전 부재와 부분 결손을 구분하지 못해 Core 전체가 실패하거나 손상 설치를 통과시킨다 | 1 | 완전 설치·완전 부재·부분 결손의 정상/경계/실패 경로 |
| `R2` | Core가 선언한 최소 Python에서 실제 동작한다 | `datetime.UTC` import 실패, Runtime 부재 세탁, 테스트 수집 누락 | 1 · 3 | 실제 최소 Runtime 통과, 부재·실행 실패·수집 누락은 전체 실패 |
| `R3` | Core 선택 기능과 Consumer 필수 의존성을 구분한다 | 특정 Consumer의 요구가 모든 Host 계약을 조인다 | 2 | key 없는 Host 통과, capability 없는 Maintainer 실패, `shared_data v1` Maintainer 통과 |
| `R4` | 사용자 승인 조건은 소비 정책 한 곳만 소유한다 | 두 실행 스킬이 서로 다른 위임 조건을 적용하거나 자체 권위를 주장한다 | 2 | 정본 조항·fixture 일치, 독자 트리거·권위 상승 결함 주입 실패 |
| `R5` | 로컬 검증과 실제 원격 도달성을 구분한다 | 로컬 URL clone 성공을 원격 사용 가능으로 확대 보고한다 | 3 · 원격 단계 | 결과 scope 분리, 원격 부재 탐지, 실제 원격 검증은 게시 뒤에만 통과 |
| `R6` | 검증 실행이 작업 트리를 오염시키지 않는다 | 저장소 내부 임시 디렉터리가 남아도 게이트가 통과한다 | 3 · 4 | 검증 전후 추적·비추적 상태 동일, 기존 부산물은 탐지기 적용 뒤 정리 |

`R0`은 다른 모든 미완료 작업보다 먼저 해결한다. `R1`~`R6` 위반은 새 개선 제안이 아니라 미완료 결함이다. 종료 뒤 발견돼도 해당 요구와 소유 단계를 미통과로 되돌리고 반례를 회귀 검사에 추가한다.

## 4. 고정 설계 결정

아래 결정 중 검증 의무와 Agent 행동 제한에 해당하는 6~8번은 `P0`의 규칙 작성 원칙에 맞춰 갱신했다. 사용자가 `P0` 결과를 확인하기 전에는 이를 근거로 후속 구현을 시작하지 않는다.

1. Core Kernel 최소 Python은 3.10으로 유지한다.
2. Maintainer 최소 Python은 3.11로 유지하고 `pyproject.toml`을 정본으로 삼는다.
3. `shared_data`는 물리적으로 제거 가능한 L7 선택 기능으로 유지한다.
4. Maintainer는 선택 key `required_core_capabilities: {"shared_data": 1}`로 의존성을 선언한다. key가 없는 기존 Host는 요구 없음이며 contract version은 2를 유지한다.
5. 창작 승인 조건은 `PROJECT_RULES.md`의 안정적인 조항 ID 한 곳만 소유한다. 스킬은 절차와 정본 참조만 소유한다.
6. 필수 게이트는 사용자 요청과 실제 변경 영향에 따라 선택된 검사만 뜻한다. 선택된 게이트의 `not_run`은 그 완료 수준의 실패이며, 선택되지 않은 검사는 게이트로 기록하지 않는다. 계약상 비해당인 경우는 `not_applicable`로 구분한다.
7. 구현 단계는 검토·복구 가능한 commit 경계를 유지한다. commit snapshot clean clone은 릴리스 후보, 재현성·패키징·submodule 도달성 확인이 필요한 단계에서만 선택한다.
8. 실제 원격 검증 실패와 검증기의 결함 주입 검사는 다른 상태다. 로컬 완료 단계는 원격 부재를 정확히 탐지하는 synthetic 검사만 요구하고, 실제 remote gate는 게시 승인 뒤 실행한다.
9. 테스트 수집 완전성은 현재 발견 파일의 동적 개수가 아니라 유지되는 기대 모듈·case inventory와 대조한다.
10. bootstrap stdout은 원본을 파싱하고 표시용 결과만 절단한다. 선택 테스트 실행 여부는 명령 별칭이 아니라 실제 의존성 import로 판정한다.

## 5. 최우선 선행 과제 P0 — 규칙을 위한 규칙 개선

### 목표

규칙을 Agent 통제 장치가 아니라 서로 다른 Agent가 반복 작업에서 일정한 품질을 재현하도록 작업 방법을 공유하는 장치로 재정의한다. 이 과제를 마치기 전에는 단계 0과 그 이후 작업을 시작하지 않는다.

### 설계 원칙

1. 반복되는 작업에서 일정한 품질의 결과물을 만들기 위한 검증된 방법을 미리 정의한다.
2. `CLAUDE.md`, `AGENTS.md` 등 서로 다른 Agent 진입점은 규칙을 복제하지 않고 명시적 키워드와 작업 의도를 통해 동일한 정본을 공유한다.
3. 규칙은 작업을 수행할 수 있는 방법, 판단 기준, 품질 기준과 확인 방법을 중심으로 작성한다.
4. Agent의 도구 선택, 세부 절차와 문제 해결 판단의 자유도를 기본적으로 제한하지 않는다.
5. 데이터 손실, 보호 정보, 외부 효과, 비용, 되돌리기 어려운 변경처럼 명확한 위해를 예방하는 데 꼭 필요한 경우에만 행동 제한을 둔다.

### 범위

- `core/rules/rule-governance.md`를 규칙 작성·배치·공유·제한 판단의 최상위 방법 정본으로 개선한다.
- 명시적 키워드 호출과 의미 기반 route가 하나의 규칙 정본으로 수렴하는 방법을 정의한다.
- 모든 제한 조항이 예방하는 구체적 위해, 적용 조건, 자유도를 덜 제한하는 대안의 부족을 설명하도록 한다.
- `core/PROJECT_RULES.md`, `core/docs/VERIFICATION.md`, `core/rules/core-change-control.md` 등 기존 규칙에서 작업 방법을 넘어 불필요하게 행동을 제한하는 조항을 감사한다.
- 실제 규칙 변경 전에 정확한 대상, 변경 문장, 유지할 제한과 이유, 검증 방법을 사용자에게 먼저 보고한다.
- 승인된 범위만 수정하고, 후속 단계의 검증·완료 설계가 개선된 거버넌스와 충돌하면 이 전체 설계를 먼저 갱신한다.

### 구현 상태

- `core/rules/rule-governance.md`에 품질 재현, 공통 정본, 작업 방법 중심 작성, Agent 자유도, 최소 제한 원칙을 반영했다.
- `core/PROJECT_RULES.md`, `core/docs/VERIFICATION.md`, `core/rules/core-change-control.md`, `core/rules/version-control.md`, `core/rules/staged-work-design.md`의 일률적인 전체 gate·clean clone 의무를 변경 영향에 따른 검증 선택 방법으로 개선했다.
- 활성 route와 trigger는 변경하지 않았다.
- 규칙 구조·링크·상호 일치 확인과 사용자 승인을 거쳐 `P0`를 완료했다.

### 게이트

- 사용자가 다섯 설계 원칙이 규칙 거버넌스 정본에 정확히 반영됐음을 확인한다.
- 서로 다른 Agent 진입점이 규칙 본문을 복제하지 않고 동일한 정본으로 route된다.
- 작업 방법·품질 기준과 강제 제한이 구분되며, 유지되는 각 제한에는 구체적 위해와 적용 조건이 있다.
- 과잉 검증 사례에 대해 Agent를 일률적으로 금지하지 않고, 작업 규모와 위험에 맞는 검증 방법 및 범위 확대 전 보고 방법을 제공한다.
- `P0`의 규칙 변경과 기존 설계 영향이 승인되기 전에는 단계 0으로 전환하지 않는다.

## 6. 단계 0 — 실행 기준과 복구 경계

### 목표

첫 Core 변경 전에 승인된 설계 fingerprint, 정확한 기준 snapshot, 복구 방법을 고정한다.

### 범위

- 이 문서의 fingerprint와 단계 1 진입 승인을 상태 정본에 기록한다.
- Core와 Maintainer의 현재 branch·HEAD를 실행 시점에 직접 측정한다.
- Core 후보가 원격에서 복구되지 않는 경우 저장소 밖의 정확한 승인 경로에 Git bundle을 만들고 복원 clone으로 검증한다.
- bundle ref가 승인되지 않은 보호 데이터를 복제하지 않는지, 생성 전 route된 보호·버전 관리 규칙으로 판정한다.
- 단계 1의 정확한 변경 경로·명령·검증·복구 방법을 활성 단계 설계로 확정한다.

### 게이트

- 정상: 승인된 snapshot과 복구 clone의 commit이 일치한다.
- 실패: bundle verify·복원 clone·commit 대조 중 하나라도 실패하면 단계 1로 전환하지 않는다.
- 경계: 원격에서 이미 복구 가능한 snapshot이면 외부 bundle은 `not_applicable`이고 근거를 기록한다.
- 원본 저장소와 보호 경로에 새 부산물이나 외부 ref 변경이 없다.

## 7. 단계 1 — L7 격리와 Python 3.10 복구

### 목표

`R1`, `R2`를 Core 자체 범위에서 해결한다.

### 범위

- 선택 기능 설치 상태를 완전 설치, 완전 부재, 부분 결손으로 구분한다.
- 호환성 선언, 모듈 계층, Kernel 문서 링크, 선택 테스트 배치의 L7 결합을 함께 분리한다.
- `datetime.UTC`를 Python 3.10 호환 표현으로 교체하고 관련 구현·테스트 import를 함께 수정한다.
- Kernel이 L7을 역방향 import하지 않는지 검사한다.
- 유지되는 기대 테스트 inventory로 수집 누락을 탐지한다.

### 게이트

- 정상: L7 완전 설치 상태에서 공개 계약과 전체 관련 테스트가 통과한다.
- 실패: 구현·계약·schema·계층·선택 테스트 중 일부만 결손이면 gate가 실패한다.
- 경계: L7 완전 부재 상태에서 Core `verify`, `gate`, Kernel 테스트가 통과하고 선택 기능은 `not_applicable`이다.
- 실제 Python 3.10에서 Core 범위가 통과하며 import·수집 누락이 0이다.

## 8. 단계 2 — Consumer capability와 승인 정책

### 목표

`R3`, `R4`를 Core·Maintainer 통합 범위에서 해결한다.

### 범위

- Consumer 계약의 선택 capability key와 양의 버전 검증을 추가한다.
- 기존 key 부재 Host의 계약을 조이지 않는다.
- Maintainer 통합 gate가 `shared_data v1` 의존성을 검사한다.
- `PROJECT_RULES.md`의 창작 승인 조항에 안정적인 ID를 부여한다.
- `coordinate-video-production`, `youtube-title-thumbnail`은 정본 링크만 사용하고 독자 트리거·`supersedes` 권위를 제거한다.
- 대표 발화·기대 mode·정본 조항 ID를 가진 정적 fixture와 결함 주입 검사를 둔다.

### 게이트

- 정상: `shared_data v1` Maintainer와 모든 승인 fixture가 통과한다.
- 실패: capability 누락·잘못된 ID·0 이하 버전·스킬 독자 트리거·권위 상승 문장을 주입하면 실패한다.
- 경계: capability key가 없는 일반 Host는 통과하고, key가 있으나 capability가 없는 Maintainer는 정확한 누락을 보고한다.
- 정적 fixture 통과를 실제 Agent 자연어 동작 검증으로 확대 보고하지 않는다.

## 9. 단계 3 — 검증기 신뢰성

### 목표

`R2`, `R5`, `R6`의 조용한 생략·범위 혼합·부작용 경로를 닫는다.

### 범위

- 절대경로로 확인한 Python 3.10에서 Core 범위만 실행하는 필수 단계를 둔다.
- Core 3.10과 Maintainer 3.11 하한을 서로 다른 정본에서 읽고 구분해 보고한다.
- 원본 stdout 파싱, 테스트 inventory, module 수집 결과, 실행·skip 수, skip 이름·이유를 보고한다.
- 선택 테스트는 실제 의존성 import 가능 여부로 판정한다.
- fixture는 시스템 임시 경로를 사용하거나 확정적 cleanup을 등록한다.
- 로컬 clone과 실제 원격 clone 결과 schema에 각각 `local`, `remote` scope를 둔다.
- 검증 전후 Git 상태를 보호 경로를 열거하지 않는 방식으로 비교한다.

### 게이트

- 정상: 지원 Runtime에서 모든 필수 검사와 기대 테스트 inventory가 통과한다.
- 실패: Runtime 부재·실행 실패·수집 누락·원격 commit 부재·새 부산물은 전체 실패로 보고된다.
- 경계: 2,000자를 넘는 유효 JSON, 실행 파일 별칭 차이, 선택 테스트 의존성 부재가 정확히 판정된다.
- 원격 부재 synthetic fixture가 명시적으로 실패하는 것을 메타 게이트의 성공으로 기록하되 실제 remote 결과를 `pass`로 기록하지 않는다.

## 10. 단계 4 — 로컬 마감

### 목표

단계 0~3의 검증된 후보 commit을 통합 상태에서 재검증하고 `로컬 구현 완료`를 판정한다.

### 범위

- 오염 탐지기를 먼저 적용한 뒤 `extension/work`의 기존 테스트 부산물을 정확한 경로와 생성 패턴으로 재측정한다.
- 삭제 대상은 exact path 승인 뒤에만 정리한다.
- Core·Maintainer 전체 테스트, Core 자체 gate, Core+Consumer gate를 실행한다.
- Python 3.10 Core 범위와 Python 3.11 이상 Maintainer 범위를 분리해 실행한다.
- ASCII·한글·공백 경로의 commit snapshot clean clone을 검증한다.
- 각 단계 commit과 최종 gitlink가 의도한 의존 순서를 가리키는지 확인한다.

### 게이트

- 정상: 모든 필수 단계가 `pass`, `not_run` 0, 두 작업 트리 clean이다.
- 실패: checkout과 commit snapshot 결과가 다르거나 보호 경로·미추적 파일에 의존하면 완료가 아니다.
- 경계: 원격 게시가 승인되지 않았으면 `로컬 구현 완료·원격 게시 대기`로만 보고한다.
- 새로운 commit을 원격에 push하지 않는다.

## 11. 조건부 원격 단계

별도 push 승인 뒤에만 실행한다.

1. Core 후보 branch를 push하고 원격 ref 도달성을 확인한다.
2. Maintainer가 원격에서 가져올 수 있는 Core commit을 가리키게 한다.
3. Maintainer 후보 branch를 push한다.
4. 로컬 URL override 없이 실제 원격 URL로 `clone --recurse-submodules`를 실행한다.
5. 원격 clean clone에서 전체 gate를 실행한다.
6. main 반영·태그·릴리스는 결과 보고 뒤 별도 결정한다.

실제 원격 clone과 전체 gate가 통과한 경우에만 `원격 사용 검증 완료`다.

## 12. 로컬 완료 뒤의 운영 backlog

다음은 현재 로컬 구현 완료를 막지 않는다.

| 작업 | 필요 조건 | 완료 주장 |
|---|---|---|
| 전용 Agent-Core-Maintainer 원격 구성 | 이 저장소를 장기 공식 Maintainer로 운영하기로 결정 | Maintainer 운영 경로 구성 |
| 쓰기·읽기 Deploy Key 분리 | 실제 Maintainer/Host 권한을 원격에서 강제할 때 | 권한 분리 검증 |
| 첫 실제 Host와 Codex·Claude 재개 검증 | 실제 Host 사용 가능성을 주장할 때 | 실제 Host 검증 |
| 서로 다른 두 번째 Host 검증 | 범용 Host 사용성을 주장할 때 | 범용 Host 검증 |

이 backlog는 원격 생성, 자격 증명, 실제 프로젝트 접근, 외부 쓰기를 자동 승인하지 않는다.

## 13. 현재 완료 범위에서 제외

- 프로젝트 package 이름·설명의 일반 정리
- Markdown 형식 일괄 통일
- Node 지원 범위 중복 제거
- 점수 상승 목적 리팩터링과 신규 기능
- 실제 Creator 프로젝트 적용
- main 병합, 태그, 릴리스, 게시
- 영상 편집 규칙 후보의 반복 근거 없는 승격

제외 항목이 `R1`~`R6`을 실제로 막는 반례가 재현되면 범위를 자동 확장하지 않고 사용자에게 설계 변경을 요청한다.

## 14. 완료 수준

| 수준 | 필수 조건 |
|---|---|
| 로컬 구현 완료 | `P0`와 단계 0~4 통과, 단계 4에서 선택한 최종 후보 commit clean-clone 통과, 작업 트리 clean |
| 원격 사용 검증 완료 | 조건부 원격 단계 통과, 실제 원격 submodule clone과 전체 gate 통과 |
| 실제 Host 검증 | 첫 실제 Host에서 Core 변경 없이 실제 작업·재개 통과 |
| 범용 Host 검증 | 서로 다른 실제 Host 2개에서 Core 변경 없이 통과 |

상위 수준의 이름으로 실행하지 않은 하위·외부 검증을 대체하지 않는다.

## 15. 통합 출처와 처분

다음 이전 문서의 현재 유효한 판단은 이 문서, Core 정본, `SESSION_HANDOFF.md`로 흡수했다. 원문과 완료 과정은 부모 저장소 Git 이력이 소유하며 활성 트리에서는 제거한다.

| 이전 문서 | 흡수 결과 |
|---|---|
| `CORE_COMPLETION_PLAN_2026-08-22.md` | `R1`~`R6`, 단계·완료 수준·사후 결함 환류를 이 문서로 이전 |
| `CORE_COMPLETION_PLAN_REVIEW_2026-08-22.md` | L7 결합, 최소 Runtime, fixture, 검증기 누락을 관련 요구·단계로 이전 |
| `MAINTAINER_STRUCTURE_REVIEW_2026-08-22.md` | 필수 결함을 `R1`~`R6`으로 이전하고 비필수 정리는 제외 목록으로 판정 |
| `docs/Agent-Core_순수화_및_분리구조_단계설계.md` | 완료된 Core 순수화는 기준선, 미완료 Maintainer·Host 작업은 운영 backlog로 이전 |
| `docs/Agent-Core_단계2_순수_Core_공개계약_설계.md` | 구현된 contract v2는 Core 정본이 소유하고 재실행 대상에서 제외 |

`SESSION_HANDOFF.md`, Core·Consumer 정책과 정본, 영상 편집 후보 ledger, Git 이력 정제 source-lineage 보고서는 통합·삭제 대상이 아니다.

## 16. 다음 진입 조건

`P0`와 단계 0~3은 승인된 순서와 commit 경계로 완료됐다. 단계 4에서는 다음 조건만 확인한다.

1. 오염 탐지 결과 삭제할 기존 검증 부산물이 없음을 유지한다.
2. 최종 후보 commit에서 로컬 clean-clone gate를 통과한다.
3. 두 작업 트리와 Core gitlink가 완료 commit을 정확히 가리킨다.
4. 결과를 `SESSION_HANDOFF.md`에 기록하고 로컬 완료 commit을 만든다.

push, 실제 원격 clone, 태그·릴리스, 실제 Host 적용은 이 승인에 포함되지 않는다.
