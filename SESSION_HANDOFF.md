# 세션 핸드오프

- 기준일: 2026-07-18
- 상태: active — 현재 단계·첫 다음 행동 단일 정본.
- 역할: 채팅 기억 없이 다음 세션이 검증된 현재 상태에서 재개하기 위한 문서.
- 읽기 순서: `AGENTS.md` → `PROJECT_RULES.md` → 이 문서 → 승인된 경우에만 `docs/REBUILD_PLAN.md`의 현재 레이어 절.
- 현재 단계: **L0 — 정본·자료·기준선 정리 완료, 사용자 확인 게이트**
- 현재 목표: 사용자가 L0의 정본 구조를 확인하고 L1 진행 여부를 결정한다.
- 실행 제한: L1 승인 전에는 규칙 확장, 검사 구현, 코드 복원, 데이터 이행, 설치를 시작하지 않는다.

## 핵심 용어와 방향

- `기반층`: L1 규칙 → L2 파일 기반 데이터 구조 → L3 문서·파일 I/O 최적화 → L4 파일 관리 규칙.
- `목적층`: L5 워크플로 규칙 → L6 워크플로 구조 → L7 프레임워크·도구 → L8 스킬 정비.
- `보강`: 기존 체계를 전면 교체하지 않고 필요한 계약·코드·테스트만 선별 회수하는 방식.
- 실행 원칙: 문서는 상세하게, 구현은 레이어별 2~4시간 범위로 작게 하며 각 레이어를 독립 검증한다.

## L0 착수 판단

| 질문 | 답 |
|---|---|
| 실제 불편 | 활성 계획과 역사 계획이 함께 보여 새 세션이 폐기된 실행 방향을 따를 위험이 있었다. |
| 빨라지거나 덜 틀리는 것 | 시작 라우팅과 상태 라벨을 고정해 정본 재탐색과 잘못된 구현 착수를 줄인다. |
| 기존 자산과 실제 델타 | `AGENTS.md`·규칙·핸드오프·계획·승계 지도는 이미 있었다. 상태 라벨 통일과 현재 프레임워크 기준선 기록만 추가했다. |
| 시간 범위 | 문서 변경과 정적 검증만으로 2~4시간 안에 끝나는 범위였다. |

## 근거 자료와 상태

| 경로 | 역할 | 상태 |
|---|---|---|
| `PROJECT_RULES.md` | 운영 규칙 단일 정본 | active |
| `SESSION_HANDOFF.md` | 현재 단계·첫 다음 행동 단일 정본 | active |
| `docs/REBUILD_PLAN.md` | 분석·설계·작업 분류·L0~L8 실행 계획 단일 정본 | active, L0 완료 |
| `docs/INHERITANCE_MAP.md` | 기존 자산 승계 판단 단일 정본 | active |
| `PROJECT_STRUCTURE_ANALYSIS.md` | legacy·스냅샷·현재 루트 구조 분석 | active / supporting analysis |
| `docs/REBUILD_EXECUTION_REPORT.md` | 첫 미디어 구현 후보 교차검증 | historical / superseded, 실행 금지 |
| `backup/root_snapshot_2026-07-18/docs/improvement/LAYER_PLAN.md` | 사용자 L0~L8 순서와 원문을 복구한 근거 | historical evidence, read-only |
| `backup/root_snapshot_2026-07-18/docs/rebuild/stage-00/KNOWN_FAILURES.md` | 기존 도구·검사 실패 원장 | historical evidence, read-only |

`backup/` 문서 내부의 `active` 표기는 당시 스냅샷 시점의 라벨이다. 현재 실행 정본 여부는
위 표와 현재 루트 문서가 결정하며, 백업 원문은 수정하지 않는다.

## L0 재개 체크포인트

- 2026-07-18 사용자가 “진행하자”라고 지시해 통합 계획과 L0 착수를 승인했다.
- 시작 라우팅은 `AGENTS.md` → `PROJECT_RULES.md` → `SESSION_HANDOFF.md` → 승인된 현재 레이어로 단일화되어 있다.
- 규칙·상태·계획·승계 판단의 정본은 각각 하나이며 역할이 겹치지 않는다.
- `docs/REBUILD_EXECUTION_REPORT.md`는 historical/superseded 상태를 유지한다.
- README나 `docs/INDEX.md`가 없어도 현재 3개 진입 문서에서 L0 계획에 도달하므로 복구하지 않았다.
- 코드·도구·스킬·사용자 데이터는 변경하지 않았고, `backup/`도 수정하지 않았다.
- 첫 미착수 작업은 **L1 — 기본 프로젝트 규칙**이며 사용자 승인 대기다.

## 프레임워크 기준선

사용자 데이터와 `backup/`을 제외한 현재 워킹트리 프레임워크는 9개다.

- Git 추적 8개: `.gitattributes`, `.gitignore`, `AGENTS.md`, `PROJECT_RULES.md`,
  `PROJECT_STRUCTURE_ANALYSIS.md`, `SESSION_HANDOFF.md`, `docs/INHERITANCE_MAP.md`,
  `docs/REBUILD_PLAN.md`.
- Git 미추적 1개: `docs/REBUILD_EXECUTION_REPORT.md` — historical/superseded 분석 자료.
- 현재 브랜치: `feature/refactoring_simple`.
- 커밋·스테이징·푸시는 사용자 요청 범위가 아니어서 수행하지 않았다.

## 완료한 작업과 현재 Git 상태

- 기존 프로젝트 프레임워크 86개와 재구축 스냅샷 약 130개를 사용자 데이터 제외 범위에서 비교했다.
- Claude·GPT·Gemini 청사진, 교차검증 문서, 변경 제안 0001·0002, Stage 00~04 보고서와 Git 이력을 대조했다.
- 스냅샷 `LAYER_PLAN.md`에서 사용자의 L0~L8 순서와 비용 상한을 복구했다.
- `docs/REBUILD_PLAN.md`를 통합 계획 정본으로, `docs/INHERITANCE_MAP.md`를 승계 판단 정본으로 확정했다.
- L0에서 활성 문서 상태 라벨, 승인 기록, 시작 라우팅, 프레임워크 기준선을 정리했다.
- 현재 변경: `AGENTS.md`, `PROJECT_RULES.md`, `PROJECT_STRUCTURE_ANALYSIS.md`,
  `SESSION_HANDOFF.md`, `docs/INHERITANCE_MAP.md`, `docs/REBUILD_PLAN.md` 수정;
  `docs/REBUILD_EXECUTION_REPORT.md` 미추적.

## 검증 상태

| 대상 | 확인 수준 | 결과 |
|---|---|---|
| L0 문서 | 파일·구조 검증 | UTF-8 정상, NUL 없음, 상태 라벨 확인, `git diff --check` 통과. |
| 시작 라우팅 | 새 세션 읽기 시뮬레이션 | `AGENTS.md`에서 규칙→핸드오프→승인된 현재 레이어로 도달하며 경로가 모두 존재한다. |
| 프레임워크 기준선 | Git 추적 목록 | 8개 추적 + 1개 미추적 historical 문서로 기록했다. |
| `backup/` | Git 변경 확인 | 변경 없음. |
| 통합 계획 | 사용자 확인 | 2026-07-18 승인됨. |
| 기존 legacy 테스트 | 도구 검증 일부 | 74개 중 72개 통과, 2개는 Git safe-directory 환경 실패. |
| 재구축 스냅샷 현재 환경 | 도구 검증 미완료 | 3회 시도 뒤 113 passed, 14 failed, 33 errors; 재시도 금지. |
| 실제 사용자 미디어·Premiere | 미검증 | L0 범위가 아니며 사용자 지정 자료·앱 검증 없음. |

## 실패 원장

| 목표 | 시도/버전 | 결과·확인 원인 | 연속 횟수 | 다음 조건 |
|---|---|---|---:|---|
| 현재 환경에서 스냅샷 전체 테스트 재현 | 1: bundled Python | pytest 미설치로 실행 불가 | 1 | 다른 런타임 사용 |
| 같은 목표 | 2: snapshot venv | package import 경로 미설정 | 2 | 명시적 `PYTHONPATH` |
| 같은 목표 | 3: venv + `PYTHONPATH` | 113 pass, 14 fail, 33 error; Git safe-directory·pytest temp 권한 영향 | 3 | 환경 소유권/임시 경로 변경 또는 별도 clean clone 전 재시도 금지 |
| 현재 환경에서 legacy 테스트 확인 | 1: unittest 74개 | 72 pass, 2 fail; Git safe-directory 영향 | 1 | Git 안전 경로가 설정된 환경에서만 재확인 |
| `CODEX_` 분석 문서 위치 확인 | 파일시스템+전체 Git 이름 이력 | 해당 접두어 문서 없음; 내용·시점·스냅샷 경로로 복구 | 1 | 사용자가 별도 경로를 제공하면 추가 대조 |

## 활성 차단과 위험

- 현재 차단은 **L1 사용자 승인 대기**다.
- `inputs/`·`outputs/` 내부는 열거·열기·해시하지 않았다. 실제 데이터 이행 대상과 최신본은 미확정이다.
- L1에서 기존 한글 경로를 소급 변경하지 않고 신규 machine-facing ID 범위만 결정해야 한다.
- legacy 도구 회수 시 wrapper 종료 코드, ffprobe 기본값, 비원자적 자산 생성, fail-open 검사도 함께 회수될 수 있다.
- 외부 플러그인·SQLite·Worktree·강제 gate는 효과가 측정되기 전에는 활성화하지 않는다.

## 첫 다음 행동

1. 사용자에게 L0 정본 구조 확인과 L1 진행 승인을 받는다.
2. 승인되면 `docs/REBUILD_PLAN.md`의 L1 절만 읽는다.
3. L1의 범위·완료 조건·검증·롤백과 `docs/INHERITANCE_MAP.md` 관련 항목을 확인한 뒤 L1만 수행한다.

## 이후 사용자 결정 시점

- L1: machine-facing 이름과 기존 한글 경로의 명명 범위.
- L2: 상태 스키마와 실제 이행할 사용자 지정 샘플 1건.
- L3: 실제 자주 하는 문서·파일 작업 3개와 도구 필요성.
- L4: 승인 상태 축소안.
- L7: 회수할 기존 도구와 Premiere/OS 사용 환경.
- L8: 스킬 11개의 유지·보류·폐기 후보 분류.

## 다음 세션 시작 문구

```text
PROJECT_RULES.md와 SESSION_HANDOFF.md를 읽고 현재 승인 상태를 확인해.
L1이 승인되지 않았다면 구현하지 말고,
승인됐다면 docs/REBUILD_PLAN.md의 L1 절만 진행해.
```
