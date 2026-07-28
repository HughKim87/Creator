# M0 기준·목표 계약 설계

- 문서 역할: `phase-design`
- 단계 ID: `M0`
- lifecycle: `passed`
- 목적: M1 구현 전에 재현성·품질·검증 범위와 승인 경계를 하나의 측정 가능한 계약으로 확정한다.
- 상위 설계: [재현 가능한 프로젝트 기반 전체 설계](../PROJECT_FOUNDATION_DESIGN.md)
- 현재 상태: [세션 핸드오프](../../../SESSION_HANDOFF.md)
- 선택 근거: [방향 분석 1·3·5·11절](../../reports/codex_2026-07-28_재현가능한_프로젝트_기반_방향분석과_개선계획.md)

## 단계 결과

사용자와 다음 실행 세션이 “M1이 무엇을 고쳐야 하고 어떤 상태를 성공으로 부를지”를 같은 기준으로 판정할 수 있다.

## Entry gate

- `M0-E1`: 전체 목표가 특정 영상 한 편이 아니라 재사용 가능한 프로젝트 기반임이 확인되어 있다.
- `M0-E2`: 전체 설계·현재 phase·현재 상태 owner가 분리되어 있다.
- `M0-E3`: M0에서는 M1 코드 변경, dependency 설치, CI, 보호 데이터 접근, commit·push를 실행하지 않는다.

하나라도 충족하지 않으면 M0 결정 확정을 시작하지 않는다.

## 포함 범위

- Q0~Q5 품질 계층과 각 owner
- clone-to-green의 환경·경로 조건
- 자동 검증과 사용자·외부 capability gate의 경계
- 현재 baseline과 확인된 재현성 gap
- M1에서 결정할 설계 질문과 exact Core 승인 경계

## 제외 범위

- M1 구현과 schema migration
- dependency 설치·lock 생성
- CI·hook·single verify 구현
- 보호 `inputs/`·`outputs/` 접근
- M2~M6 상세 설계와 실행

## 결정할 기준

### 재현 가능

- tracked checkout을 임의 ASCII·한글·공백 경로에 둔다.
- 선언된 runtime과 bootstrap 외의 host 전역 package에 의존하지 않는다.
- 보호 데이터와 외부 계정 없이 Q0~Q3을 한 진입점에서 검증한다.
- 외부 capability는 Q4에서 `ready / needs_user / unavailable`로 분리한다.
- 실제 의미 품질과 사용자 채택은 Q5로 분리하며 clone gate로 위장하지 않는다.

### 품질 owner

| 수준 | 판정 대상 | owner |
|---|---|---|
| Q0 | encoding·link·schema·routing·보호 경계 | maintenance |
| Q1 | function·state·validator 불변식 | Core·Extension 회귀 |
| Q2 | domain synthetic workflow | vertical acceptance |
| Q3 | arbitrary-path clone·bootstrap | clone conformance |
| Q4 | browser·계정·외부 도구 capability | preflight와 사용자 gate |
| Q5 | 실제 결과의 의미·채택 | replay·검수·사용자 승인·production metric |

낮은 수준의 통과를 높은 수준의 통과로 보고하지 않는다.

## Execution slices와 slice gate

### M0-S1 — baseline 재확인

- 현재 HEAD·dirty 범위와 기존 Core·Extension·maintenance 결과를 다시 측정한다.
- clean-clone source-root 실패와 미선언 Pillow 의존이 현재도 같은 조건인지 구분한다.

Gate `M0-S1-G`: 결과마다 실행 환경·명령·pass/fail·확인 원인이 있고 미실행 검사를 pass로 기록하지 않는다.

### M0-S2 — 성공 정의 승인

- 위 재현성 정의, Q0~Q5 owner, 외부 capability 경계를 사용자에게 한 번에 제시한다.

Gate `M0-S2-G`: 사용자가 성공 정의를 승인하거나 수정했고, 수정 사항이 이 문서에 반영되어 있다.

### M0-S3 — M1 설계 입력 고정

- 지원 Python·Node 범위
- 필수·선택 dependency 구분
- bootstrap·single verify owner
- project-neutral namespace migration
- storage convention 또는 injection
- Extension-owned artifact registry interface
- arbitrary-path clone fixture
- CI의 비보호 실행 경계

Gate `M0-S3-G`: 각 질문의 결정 owner, 필요한 exact 파일 범위, 검증 방법과 미승인 항목이 구분되어 있다.

### M0 결정표

| 질문 | 권장 선택 | owner·exact 범위 | 검증·미승인 경계 |
|---|---|---|---|
| runtime | Python 3.11+ (3.12 검증), Node 20 LTS. Core·deterministic Extension은 표준 라이브러리 우선 | root `pyproject.toml`, `package.json`, `scripts/bootstrap.py`, `scripts/verify.py` | clone preflight와 버전 출력. dependency 설치는 M1 별도 승인 |
| dependency | Pillow는 `thumbnail` 선택 그룹. faster-whisper·모델·Chrome profile은 필수에서 제외 | root manifest와 optional preflight | `python -S`에서 optional unavailable을 명시. 설치·lock 생성은 M1 별도 승인 |
| bootstrap·single verify | domain-neutral root `scripts/bootstrap.py`와 `scripts/verify.py`가 Q0~Q3을 집계 | root scripts, maintenance contract와 회귀 | 현재는 설계만 확정. CI 생성은 범위 밖·미승인 |
| namespace | `project://core/schemas/<file>`로 중립화하고 기존 `urn:kim-silver-youtube:*`는 migration compatibility alias로만 판독 | Core schema·document artifact block 후보 일체 | Core exact path 승인 후 semantic drift·legacy alias 회귀 |
| storage | root composition에서 storage root을 주입하고 test fixture만 isolated temp에 쓴다 | `core/src/file_data/store.py`와 compatibility tests 후보 | 실제 repository root 거부·isolated fixture 허용 회귀. Core 변경 미승인 |
| artifact registry | YouTube 목록은 Extension owner가 제공하고 Core는 neutral registry/verifier interface만 소유 | `core/src/file_data/document_data.py` 및 Core test, YouTube contract/test 후보 | Core의 YouTube 직접 열거 0, Extension drift 유지. Core 변경 미승인 |
| clone fixture | ASCII·한글·공백 경로를 모두 사용하는 tracked clean clone | root conformance runner와 Core/Extension test 후보 | 보호 데이터 없이 clone·Q0~Q3 실행. temp clone은 검증 후 disposable |
| CI 경계 | 로컬 single verify와 동일한 비보호 gate만 향후 CI에서 실행. 외부·보호·사용자 승인은 제외 | 향후 `.github/workflows` 후보 | CI·hook 생성은 M1 이후 별도 승인 |

`M0-S2-G`: 최신 사용자 지시의 “권장안 자동선택”에 따라 Q0~Q5·재현성 정의를 승인된 기준으로 확정했다. `M0-S3-G`: 위 표에 결정 owner·exact 후보 범위·검증·미승인 경계를 기록했다.

## Exit gate

- `M0-X1`: Q0~Q5와 재현 가능 정의가 사용자에게 승인됐다.
- `M0-X2`: current와 clean-clone baseline의 pass·fail·환경 조건이 재측정됐다.
- `M0-X3`: M1 설계 질문과 Core·설치·CI·외부·보호 경계가 구분됐다.
- `M0-X4`: 전체 설계와 M0 문서가 읽기 예산을 지키고 장문 근거가 required-read 경로에서 빠졌다.

모든 항목에 증거가 있어야 `passed`로 전이한다.

## 중단·복구 조건

- M0 판단에 보호 데이터나 외부 계정 접근이 필요해지면 중단한다.
- 성공 정의가 구현 편의를 위해 낮아지면 사용자에게 차이를 보고한다.
- M1 mutation이 필요해지면 실행하지 않고 exact 경로·이유·gate를 승인 요청한다.
- 사용자 교정이 전체 목표를 바꾸면 lifecycle을 `invalidated`로 바꾸고 상위 설계부터 갱신한다.

## Transition gate

M0 통과 뒤 다음을 재평가한다.

1. M1이 여전히 최소 다음 단계인가.
2. M1을 더 작은 phase로 나눠야 하는가.
3. 새 문서·규칙·자동화가 줄이는 수동 단계가 명확한가.
4. 현재 required-read 전체가 읽기 예산 안에 있는가.

통과한 경우에만 [M1 planned 설계](M1_FRESH_CLONE_AND_CORE_PURITY.md)를 `draft`로 전환하고 `SESSION_HANDOFF.md`의 활성 단계 링크를 교체한다.

## 첫 다음 행동

M0-S1~S3와 M0-X1~X4를 통과했다. 다음은 M1 entry gate이며, Core exact 경계 승인 전에는 Core를 변경하지 않는다.
