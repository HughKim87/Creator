# Stage 01 파일 범위

## 루트 실제 구현

- 환경·패키지: `.python-version`, `pyproject.toml`, `uv.lock`, `src/video_workflow/`
- 검증: `tests/unit/`, `tests/contract/`, `tests/smoke/`
- 집행: `.githooks/pre-commit`, `.github/workflows/ci.yml`
- 진입·정책: `README.md`, `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`
- Git 경계: `.gitignore`, `.gitattributes`

## 구축 문서

- 총괄 계획: `docs/rebuild/AGENT_EXECUTION_PLAN.md`
- 구조 분석: `docs/rebuild/research/`
- 단계 지시·보고: `docs/rebuild/stage-00/`부터 `docs/rebuild/stage-08/`

루트에는 `AGENT_EXECUTION_PLAN.md`, `AGENT_STAGE_XX_*.md`,
`PROJECT_STRUCTURE_RESEARCH.md` 같은 구축 설계·분석 문서를 남기지 않는다.

QA 수정의 핵심 파일은 `.githooks/pre-commit`, `src/video_workflow/cli.py`,
`src/video_workflow/checks/repository.py`, `tests/contract/test_pre_commit_hook.py`,
`tests/contract/test_required_negative_matrix.py`다.

## 보호 범위

- `backup/` 수정 0
- 사용자 데이터 읽기·복사·해시·stage 0
- 체크포인트 commit/push: 이 문서를 포함한 `feature/refactoring` 커밋으로 수행
- tag 생성 0
- 검증용 추가 worktree 0
