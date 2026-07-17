# Stage 03 명령 실행 결과 (2026-07-17)

환경: Stage 02와 동일(Linux 샌드박스, CPython 3.12.3 `/tmp/py312`,
`/tmp/vw-clone` 검증 사본, `uv sync --frozen`). 테스트 정책에 따라 스테이지 말
통합 실행 1회.

| 명령 | 종료 코드 | 결과 |
|---|---:|---|
| `uv run --frozen workflow check --scope full --json` | 1 | doctor 8/8, lock/format/lint/type/tests 모두 0 (135 passed, 1 skipped), `backup_baseline`만 기존 결함으로 실패 (`evidence/check_full_after_stage03_clean_clone.json`) |

개발 중 중간 실행: 없음(정책 준수). 테스트 작성 직후 대상 축소 1회 실행에서
approval_requests FK 미생성으로 통합테스트 4건 실패 → 테스트 픽스처에 요청 행
생성 추가로 해결 후 통합 실행 통과.

보호 상태: `backup/` 변경 0(`backup_git_unchanged` PASS), 금지 경로 접근 0,
커밋·푸시 0, 실제 사용자 작업 공간 생성 0.
