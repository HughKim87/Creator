# Stage 01 신뢰 기반 구축 보고서

- 상태: Stage 01 완료 — 사용자 승인 로컬 독립 QA 기준
- 브랜치·기준 HEAD: `feature/refactoring` / `dc7f18b4715bff99b806872f742bf1602e2d0418`
- 실제 구현 위치: 저장소 루트의 `pyproject.toml`, `uv.lock`, `src/`, `tests/`, 훅, CI
- 설계·분석 문서 위치: `docs/rebuild/`
- 사용자 데이터 경계: `PROJECT_RULES.md` 단일 정본

## 구축됨

- Python 3.12, uv 0.11.28, 루트 패키지와 `workflow doctor`·`workflow check` 공개 계약
- lock, format, lint, type, pytest, Stage 00 매니페스트, 문서 구조, Git 검사의 단일 진입점
- Linux full CI와 Windows 한글·공백 경로 smoke 정의
- Stage 01 필수 부정 시나리오 18개를 실제 subprocess 21개 테스트로 고정
- Stage 00 추적 프레임워크 86개 해시·추적 집합 일치와 `backup/` Git 변경 0 검사
- 구축 설계·분석·Stage 00~08 지시서를 `docs/rebuild/` 아래로 이동

## 검증됨

- `workflow doctor --json`: 종료 코드 0, 8개 검사 PASS
- `workflow check --scope full --json`: 종료 코드 0
- pytest 전체: 45개 PASS, pre-commit fast 범위: 42개 PASS
- 필수 부정 테스트 매트릭스: 21개 수집·21개 PASS
- 실제 Windows Git Bash와 설치된 uv를 사용한 pre-commit: 종료 코드 0
- 직접 자식·CLI·pre-commit의 의도적 종료 코드: `7`·`7`·`7`
- uv 결손 pre-commit: 종료 코드 `127`
- format, lint, mypy: 각각 종료 코드 0
- framework 결과물(`uv.lock`, `src/`, `tests/`, `docs/rebuild/`)은 ignore되지 않음
- `.venv`와 어느 깊이의 금지 데이터 디렉터리 규칙은 ignore됨

## 이전 실패와 해결

- 재현: 실제 Windows Git Bash 훅은 정상 설치된 uv를 찾고도 lock 단계에서 127이었다.
- 근본 원인: `command -v uv`가 실제 `uv.exe`를 `/c/.../uv`로 반환했고, MSYS의 `-f`
  판정은 확장자 없는 값도 파일로 인정해 `.exe` 보정을 건너뛰었다. Windows Python은
  변환된 확장자 없는 경로를 파일로 인정하지 않았다.
- 수정: 훅이 경로 suffix를 기준으로 `.exe`를 보정한 뒤 `cygpath -w`로
  `VIDEO_WORKFLOW_UV`만 Windows 경로로 전달한다. 실행은 Git Bash 경로를 유지한다.
- 회귀 방지: 확장자 없는 Git Bash 탐색 결과를 재현하는 Windows 훅 계약 테스트를 추가했다.
- 체크포인트 commit 훅에서 중첩 훅 테스트가 격리 `PATH`에서 `cygpath`까지 제거해 부모
  셸에 따라 uv 경로 형식이 달라지는 비결정적 fixture 결함을 발견했다. `.exe` 입력을
  검증하고 고정 Windows 경로를 반환하는 `cygpath` fixture를 추가한 뒤 실제 훅 42개와
  full 45개를 다시 통과시켰다.
- QA의 부정 테스트 누락 지적은 18개 번호 매트릭스와 완전성 가드로 해결했다.

## 후속 통합 게이트

- 로컬 구현 독립 QA는 PASS이며 Stage 01 완료 조건을 충족했다.
- 2026-07-17 사용자 결정으로 clean-clone과 원격 CI 실행 이력은 초기 Stage 01 완료
  조건에서 제외하고 후속 통합 게이트로 이관했다.
- clean-clone은 첫 수직 기능 이식 전 또는 기본 브랜치 통합 전에 실행한다.
- Stage 02 착수 승인은 별도이며 아직 수행하지 않았다.

따라서 Stage 01은 완료다. Stage 02는 자동 착수하지 않는다.

## 연결 문서

- 작업 계약: `AGENT_STAGE_01_TRUSTED_FOUNDATION.md`
- 명령 결과: `COMMAND_RESULTS.md`
- 파일 범위: `FILE_CHANGES.md`
- 위험·롤백: `RISKS_AND_ROLLBACK.md`
- 간결 증거: `evidence/local_validation.txt`
