# Stage 02 명령 실행 결과 (2026-07-17 세션)

검증 환경: Linux 샌드박스, CPython 3.12.3(소스 빌드 `/tmp/py312`), uv 잠금 환경
`uv sync --frozen`(UV_PROJECT_ENVIRONMENT=/tmp/vw-env3). 저장소 밖 검증 사본은
체크포인트 `d5f5fb5`의 `git clone --depth 1`(`/tmp/vw-clone`)이며 원본 저장소
worktree는 검사 대상 파일 복사 외에 변경하지 않았다.

## 착수 전 게이트 (체크포인트 d5f5fb5, 변경 전)

| 명령 | 종료 코드 | 결과 |
|---|---:|---|
| `uv run --frozen workflow doctor --json` | 0 | 8/8 체크 PASS (`evidence/gate_doctor_clean_clone.json`) |
| `uv run --frozen workflow check --scope full --json` | 1 | lock/format/lint/type/tests 모두 0, `backup_baseline`만 실패 (`evidence/gate_check_full_baseline_clean_clone.json`) |

`backup_baseline` 실패 분석: manifest_hashes 불일치 71건 전부가 fresh clone의
줄바꿈 정규화(CRLF→LF) 산물임을 확인했다. 대표 파일(`backup/AGENTS.md` 등)은
git blob 해시가 HEAD와 동일하고, Windows 원본 worktree 파일은 매니페스트와
바이트 단위로 일치한다(`sha256sum` 대조). 즉 콘텐츠 훼손이 아니라
`BACKUP_MANIFEST.json`이 Windows worktree 바이트 기준이어서 clean clone으로
이식되지 않는 Stage 00 산물의 휴대성 결함이다. `RISKS_AND_ROLLBACK.md` 참조.

## 구현 후 검증 (Stage 02 파일 추가 후, 동일 clone)

| 명령 | 종료 코드 | 결과 |
|---|---:|---|
| `uv run --frozen workflow check --scope full --json` | 1 | lock 0, format 0, lint 0, type 0(strict, src 19파일), tests 0(111 passed, 1 skipped), `backup_baseline`만 위와 동일 사유로 실패 (`evidence/check_full_after_stage02_clean_clone.json`) |
| `ruff check src tests` | 0 | All checks passed |
| `ruff format --check src tests` | 0 | 41 files already formatted |
| `mypy` (strict) | 0 | no issues in 19 source files |

- 테스트 구성: 기존 45개 + 신규 도메인 66개(단위 21, 부정 매트릭스 18케이스 포함
  계약 20, 속성 13, 직렬화·순수성 12). skipped 1건은
  `test_no_disallowed_lifecycle_pairs_ever_succeed`(시퀀스가 종단 상태로 끝나지
  않으면 건너뛰는 조건부 가드)로 설계된 동작이다.
- pytest를 `uv run` 없이 직접 실행하면 Stage 01의
  `test_02_missing_checker_module_fails`가 lock 단계에서 실패한다. 원인은
  `UV_PROJECT_ENVIRONMENT` 미전파(하위 `uv lock`이 Python 3.12를 못 찾음)로,
  프로젝트 규칙대로 단일 진입 명령 `workflow check`를 사용하면 재현되지 않는다.

## 보호 상태

| 항목 | 결과 |
|---|---|
| `backup/` worktree/index 변경 | 0건 (`backup_git_unchanged` PASS) |
| 금지 경로(`inputs`/`outputs`) 접근·저장 | 0건 |
| Git 커밋/태그/푸시 | 0건 (사용자 승인 대기) |
