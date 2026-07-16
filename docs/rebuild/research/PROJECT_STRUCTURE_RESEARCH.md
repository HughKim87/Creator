# 데이터 기반 신규 프로젝트 골격 리서치

- 역할: 백업 프로젝트 실측, 기존 에이전트 청사진, 외부 1차 자료를 결합해 신규 프로젝트의 최소 골격을 제안한다.
- 작성일: 2026-07-16
- 상태: 구조 근거로만 유지; 진입 문서 제안은 2026-07-17 사용자 결정으로 superseded
- 적용 범위: `feature/refactoring` 브랜치의 신규 프레임워크 루트
- 제외 범위: `backup/` 내부 파일 수정, 영상별 워크플로 구현, 기존 도구 이식

## 1. 결론

신규 프로젝트의 0단계는 문서 계층이나 영상 제작 기능을 먼저 만드는 단계가 아니다.
다음 세 조건을 실행 가능하게 증명하는 최소 프레임워크 골격이어야 한다.

1. 이 Git 저장소에는 재사용 가능한 프레임워크만 둔다.
2. Python 코드는 설치 가능한 `src/` 패키지로 격리한다.
3. 저장소 경계와 최소 에이전트 지침을 로컬 훅과 CI가 동일하게 검사한다.

현재 저장소 자체를 프레임워크 저장소로 사용한다. 별도 `studio/` 하위 폴더를
만들지 않는다. 영상별 작업 저장소는 첫 실제 영상 파일럿을 시작할 때 별도 위치에
만들며, 0단계에서는 생성하지 않는다.

## 2. 로컬 실측

2026-07-16 현재 `backup/`을 파일 내용이 아닌 구조와 메타데이터 중심으로 측정했다.

| 항목 | 실측값 |
|---|---:|
| Git 추적 파일 | 86개 |
| Markdown | 38개 |
| Markdown 총량 | 5,637줄, 168,718자 |
| Python | 34개 |
| 기존 기본 시작 문서 | 122줄 |
| 전체 규칙까지 읽는 작업 | 283줄 |
| 사용자 데이터 트리 | 파일별 경로·수·크기·해시 수집 제외 |

추적 파일은 `tools` 25개, `skills` 23개, `tests` 10개, `docs` 8개 순으로
분산돼 있었다. 문제는 지식이나 기능 부족이 아니라 문서·도구·상태의 경계가 여러
폴더에 흩어져 각 세션이 다시 해석해야 했다는 점이다.

현재 루트의 `.githooks/pre-commit`은 `tools/doccheck/check_docs.py`가 없으면
성공으로 종료한다. `.github/workflows/ci.yml`은 현재 루트에 없는 `tools/`와
`tests/`를 실행한다. 따라서 신규 골격의 첫 구현에는 훅과 CI 교체가 포함돼야 한다.

## 3. 기존 에이전트 분석의 교차결론

### GPT 분석

`backup/gpt/project_blueprint_report_2026-07-16.md`는 저장소 정책과 실제 파일
배치의 충돌, 단일 활성 작업 상태, 컨텍스트 예산을 우선 문제로 진단했다.

0단계에 채택할 내용:

- 프레임워크와 영상별 데이터의 저장소 경계를 먼저 확정한다.
- 문서상 금지를 로컬 검사와 CI의 결정적 차단으로 옮긴다.
- `inputs`와 `outputs`를 프레임워크 Git 저장소에 두지 않는다.

### Claude 분석

`backup/claude/project_improvement_blueprint_2026-07-16.md`는 작은 L0 규칙,
계층형 문서, 단일 상태 원본, 프레임워크와 작업 저장소의 분리를 제안했다.

0단계에 채택할 내용:

- 모든 에이전트가 하나의 작은 공통 진입점을 사용한다.
- 현재 저장소는 프레임워크 전용으로 정의한다.
- 지식, 기계 상태, 생성 뷰를 장기적으로 분리한다.

보류할 내용:

- 전체 번호형 문서 계층
- `vid` CLI와 상태 렌더러
- 단계별 계약과 자동 인덱스
- 별도 작업 저장소의 실제 생성

### Gemini 분석

`backup/gemini/blueprint_report.md`는 행동 회귀 검사, 지식 그래프, Git Worktree,
사용자 승인 게이트를 제안했다.

0단계에 채택할 내용:

- 저장소 경계 위반을 고정 테스트로 검증한다.
- 로컬과 CI가 같은 검사 결과를 내야 한다.

보류할 내용:

- Graphify와 지식 그래프
- Worktree 운영 자동화
- 영상 단계의 사람 승인 게이트

이 기능들은 문서와 병렬 작업이 실제로 늘어난 뒤 도입 여부를 측정해야 한다.

## 4. 외부 조사 결과

### 에이전트 지침은 작고 실측 가능해야 한다

최근 연구 결과는 AGENTS 계열 문서의 효과에 대해 일치하지 않는다.

- 12개 저장소, 138개 작업 연구에서는 컨텍스트 파일이 성공률을 유의미하게
  높이지 못하면서 비용을 평균 20~23% 늘렸다. 불필요한 요구를 줄이고 사람이
  작성한 최소 요구사항만 두라고 권고한다.
  [Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988)
- 10개 저장소, 124개 PR 연구에서는 AGENTS.md 사용 시 중앙 실행시간이 28.64%,
  출력 토큰이 16.58% 감소했다.
  [On the Impact of AGENTS.md](https://arxiv.org/abs/2601.20404)

따라서 AGENTS.md를 프로젝트 설명서로 사용하지 않는다. 실행에 필요한 최소 제약,
검사 명령, 문서 라우팅만 기록하고 실제 작업으로 비용과 성공률을 측정한다.

공식 AGENTS.md 규약은 하위 폴더별 중첩 지침과 가장 가까운 파일의 우선 적용을
지원한다. 0단계에는 하위 도메인이 없으므로 루트 `AGENTS.md` 하나만 사용한다.
[AGENTS.md 공식 규약](https://agents.md/)

### Python은 `src/` 레이아웃을 사용한다

PyPA는 `src/` 레이아웃이 루트의 설정 파일이나 개발 중 복사본을 우발적으로 import하는
문제를 줄이고, 실제 설치된 패키지를 검사하게 만든다고 설명한다.
[PyPA src 레이아웃](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)

pytest도 신규 프로젝트에서 `src/` 패키지와 외부 `tests/` 구조를 권장한다.
[pytest 권장 구조](https://docs.pytest.org/en/stable/explanation/goodpractices.html)

`pyproject.toml`은 빌드 시스템, 프로젝트 메타데이터, 테스트 설정의 단일 구성
진입점으로 사용한다.
[PyPA pyproject 가이드](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)

### 대용량 영상 데이터는 코드 저장소 밖에 둔다

Git LFS는 저장소에는 포인터를 두고 대용량 파일 내용은 원격에 보관한다.
[Git LFS](https://git-lfs.com/)

DVC는 데이터 메타정보와 파이프라인 정의를 Git에 기록하고 실제 데이터는 캐시나
원격 저장소에 보관한다.
[DVC 명령 참조](https://dvc.org/doc/command-reference/)

사용자 데이터의 크기와 무관하게 코드 저장소와 영상 데이터의 물리적 경계는 필수다.
파일별 메타데이터를 프레임워크 리서치에 저장하지 않는다. 다중 PC 동기화나 재현 요구가
아직 정의되지 않았으므로 0단계에서 Git LFS나 DVC를 설치하지 않는다.

### 문서·병렬 작업 도구는 필요가 생긴 뒤 도입한다

Diátaxis는 튜토리얼, 절차, 참조, 설명을 분리하도록 제안한다. 문서가 3개뿐인
0단계에는 전체 분류 체계를 도입하지 않고 문서가 늘어날 때 적용한다.
[Diátaxis](https://diataxis.fr/start-here/)

Git Worktree는 한 저장소에서 여러 브랜치를 별도 작업 디렉터리로 동시에 열 수 있다.
실제 병렬 수정이 시작되기 전에는 운영 구조를 만들지 않는다.
[Git Worktree 공식 문서](https://git-scm.com/docs/git-worktree)

GitHub Spec Kit의 `Spec → Plan → Tasks → Implement` 흐름은 기능 설계 단계에서
검토할 가치가 있지만, 전체 초기화는 0단계 최소 골격보다 큰 메타 구조를 만든다.
[GitHub Spec Kit](https://github.github.com/spec-kit/index.html)

## 5. 개선된 0단계 골격

```text
김실버유튜브/
├── AGENTS.md
├── CLAUDE.md
├── GEMINI.md
├── README.md
├── pyproject.toml
│
├── docs/
│   ├── INDEX.md
│   ├── CONSTITUTION.md
│   └── ARCHITECTURE.md
│
├── src/
│   └── video_workflow/
│       ├── __init__.py
│       └── checks/
│           ├── __init__.py
│           └── repository.py
│
├── tests/
│   └── test_repository_contract.py
│
├── .githooks/
│   └── pre-commit
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── .gitattributes
└── backup/
```

## 6. 파일별 책임

| 경로 | 단일 책임 |
|---|---|
| `AGENTS.md` | 공통 최소 안전 규칙, 검사 명령, 문서 라우팅 |
| `CLAUDE.md` | `AGENTS.md`를 읽으라는 Claude용 포인터 |
| `GEMINI.md` | `AGENTS.md`를 읽으라는 Gemini용 포인터 |
| `README.md` | 사람을 위한 프로젝트 목적과 빠른 시작 |
| `pyproject.toml` | 패키지·빌드·테스트 설정의 정본 |
| `docs/INDEX.md` | 문서 역할과 읽는 시점만 안내 |
| `docs/CONSTITUTION.md` | 변경이 어려운 최상위 원칙 |
| `docs/ARCHITECTURE.md` | 프레임워크·작업 데이터·백업 경계 |
| `src/video_workflow/checks/repository.py` | 저장소 구조 계약 검사 |
| `tests/test_repository_contract.py` | 검사기의 위반 탐지 회귀 테스트 |
| `backup/` | 수정하지 않는 역사적 참고 자료 |

현재 진입 구조는 `AGENTS.md` 최소 라우터, `PROJECT_RULES.md` 단일 규칙 정본,
`SESSION_HANDOFF.md` 단일 재개 상태로 확정됐다. 이 리서치의 이전 2단계 진입 제안은
superseded이며 운영 지침으로 사용하지 않는다. 향후 상태 엔진이 도입되면 핸드오프는
생성 뷰로 대체할 수 있다.

## 7. 첫 구조 검사의 계약

`repository.py`는 최소한 다음을 검사한다.

1. 루트 필수 파일과 `src/video_workflow` 패키지가 존재한다.
2. 루트에 `inputs/`, `outputs/`, 영상·음성 파일이 없다.
3. `backup/` 변경이 새 커밋에 포함되지 않는다.
4. `CLAUDE.md`와 `GEMINI.md`에 공통 규칙이 중복되지 않는다.
5. AGENTS 진입 문서 총량이 승인된 예산을 넘지 않는다.
6. 로컬 훅과 CI가 같은 검사와 테스트를 실행한다.
7. 검사기 또는 Python이 없으면 로컬 훅이 성공 처리하지 않는다.

## 8. 0단계에서 만들지 않을 것

- `tools/`, `stages/`, `specs/` 빈 폴더
- Graphify 또는 지식 그래프
- Git Worktree 운영 자동화
- Git LFS 또는 DVC 설정
- `vid` CLI
- 영상별 `state.json`과 HANDOFF 렌더러
- 8단계 워크플로 계약
- 자동 INDEX 생성
- 전체 Spec Kit 구조

실제 코드, 계약, 병렬 작업, 데이터 동기화 요구가 생길 때 각각 별도 제안과 테스트를
통해 도입한다.

## 9. 권장 구현 순서

1. 새 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`를 루트에 생성한다.
2. `docs/INDEX.md`, `docs/CONSTITUTION.md`, `docs/ARCHITECTURE.md`를 생성한다.
3. `pyproject.toml`과 `src/video_workflow` 패키지를 생성한다.
4. 저장소 구조 검사와 회귀 테스트를 작성한다.
5. 기존 pre-commit과 CI를 새 검사기로 교체한다.
6. 설치, 테스트, 훅, CI를 깨끗한 환경에서 검증한다.
7. 0단계 승인 후에만 단일 상태 모델 설계를 시작한다.

## 10. 0단계 완료 기준

- 세 에이전트가 동일한 공통 규칙으로 시작한다.
- 에이전트별 파일에는 공통 규칙이 중복되지 않는다.
- 프레임워크 패키지가 설치된 상태에서만 import된다.
- 루트 영상 데이터와 `backup/` 변경을 자동 검사가 차단한다.
- 로컬 훅과 CI가 동일한 테스트를 통과한다.
- 현재 백업 파일은 수정되지 않는다.
- 신규 구조에 사용되지 않는 빈 폴더나 도구가 없다.

## 11. 위험과 대응

### AGENTS 문서가 다시 비대해질 위험

길이 자체보다 불필요한 요구가 비용을 만든다. 공통 안전 규칙, 검사 명령, 라우팅만
허용하고 프로젝트 개요와 설계 설명은 README와 docs로 분리한다.

### 구조 검사기가 또 다른 거대 도구가 될 위험

0단계 검사기는 저장소 경계와 필수 파일만 검사한다. 문서 품질, 영상 단계, 상태
계약 검사는 해당 기능이 생길 때 추가한다.

### `backup/`이 운영 정본으로 되돌아갈 위험

새 문서가 `backup/`의 운영 절차를 직접 참조하지 않도록 검사한다. 백업 보고서는
설계 근거로만 링크하고 실행 규칙으로 사용하지 않는다.

### 데이터 도구를 너무 늦게 도입할 위험

첫 영상 파일럿 전에 단일 PC, 다중 PC, 원격 협업, 복구 목표를 결정한다. 그 결과에
따라 로컬 외부 작업 폴더, Git LFS, DVC 중 하나를 선택한다.

## 12. 최종 제안

기존 프로젝트의 가장 큰 문제는 기능 부족이 아니라 분산과 검증 공백이었다. 신규
구조는 작은 문서 세트만 만드는 데서 끝나면 안 된다. 설치 가능한 `src/` 패키지와
하나의 저장소 경계 검사를 첫 커밋부터 갖춰야 한다.

0단계 승인 후 다음 작업은 위 골격을 그대로 생성하는 것이다. 기존 도구·스킬·단계
문서는 이 단계에서 이식하지 않는다.
