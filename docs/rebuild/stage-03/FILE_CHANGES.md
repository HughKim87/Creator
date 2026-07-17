# Stage 03 변경 파일 (미커밋)

## 신규

| 파일 | 의도 |
|---|---|
| `src/video_workflow/storage/errors.py` | 저장 계층 typed 오류(fail-closed) |
| `src/video_workflow/storage/port.py` | 동결된 저장소 인터페이스(`StateStore`, `CommitExtras` 등) |
| `src/video_workflow/storage/migrations/0001_initial.sql` | 초기 스키마(append-only 트리거, FK/CHECK/UNIQUE) |
| `src/video_workflow/storage/sqlite_store.py` | SQLite 구현: init/open/migrate(백업·복원)/load/commit_transition/verify/approval_requests |
| `src/video_workflow/storage/{__init__,migrations/__init__}.py` | 패키지·재수출 |
| `src/video_workflow/services/state_service.py` | 명령 조립(UUID·시각 생성은 이 계층만), 승인 신뢰 경계 |
| `src/video_workflow/services/state_views.py` | 생성 뷰 export(원자적 쓰기, DO NOT EDIT) |
| `src/video_workflow/services/__init__.py` | 패키지 |
| `tests/unit/storage/test_sqlite_store.py` | 스키마 안전·append-only·마이그레이션 7개 |
| `tests/integration/state/test_state_service.py` | 전이·원자성·동시성·멱등성·승인 경계·뷰·CLI 17개 |
| `tests/{unit/storage,integration,integration/state}/__init__.py` | 패키지 |

## 수정

| 파일 | 내용 |
|---|---|
| `src/video_workflow/cli.py` | `workflow state ...`·`workflow approval ...` 하위 명령 추가(기존 doctor/check 무변경) |
| `pyproject.toml` | `[tool.setuptools.package-data]`에 마이그레이션 SQL 포함(의존성 무변경, uv.lock 영향 없음) |

`backup/` 변경: 없음. 사용자 데이터 접근: 없음(모든 테스트는 pytest 임시 경로).
