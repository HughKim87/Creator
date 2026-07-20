# Video Workflow

이 저장소는 영상 작업 데이터와 분리된 재사용 가능한 워크플로 프레임워크를 구축한다.
구축 설계·분석·단계 기록은 `docs/rebuild/`에 두고, 실제 패키지와 테스트는 저장소 루트의
`src/`와 `tests/`에 순차적으로 누적한다.

## 현재 상태

- Stage 00: 기준선 동결·독립 검증 완료
- Stage 01: 루트 최소 골격과 fail-closed 검사 체계 완료·독립 QA PASS
- 사용자 데이터: 어느 깊이의 `inputs/`·`outputs/`도 읽기·기록·Git 저장하지 않음
- 임시 worktree·runtime: 저장소 밖에서만 생성

## 개발 환경

Python 3.12와 uv 0.11.28을 사용한다. Windows에서 uv를 사용자 도구 폴더에 설치한 경우
다음처럼 실행 파일을 명시한다.

```powershell
$uv = "$HOME\.local\bin\uv.exe"
$env:VIDEO_WORKFLOW_UV = $uv
& $uv sync --locked --dev
& $uv run --locked workflow doctor --json
& $uv run --locked workflow check --scope fast
& $uv run --locked workflow check --scope full
```

검사 순서는 doctor, lock, format, lint, type, 테스트, Stage 00 `backup/` 기준선, 문서 구조,
Git whitespace 검사다. 검사 도구나 필수 파일이 없거나 검사 하나가 실패하면 종료 코드 0을
반환하지 않는다. pre-commit은 fast, CI는 full 진입점을 사용한다.

Stage 01은 2026-07-17 사용자 승인 로컬 독립 QA 기준으로 완료했다. clean-clone과 원격
CI 실행 이력은 첫 수직 기능 이식 전 또는 기본 브랜치 통합 전의 후속 게이트로 관리한다.
