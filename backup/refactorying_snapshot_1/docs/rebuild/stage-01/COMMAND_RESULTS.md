# Stage 01 명령 결과

세부 계약은 `AGENT_STAGE_01_TRUSTED_FOUNDATION.md`, 현재 판정은 `STAGE_REPORT.md`를
정본으로 사용한다.

| 검사 | 실제 종료 코드 | 판정 |
|---|---:|---|
| `uv lock --check --offline --no-cache` | 0 | PASS |
| `workflow doctor --json` | 0 | 8/8 PASS |
| format / lint / mypy | 0 / 0 / 0 | PASS |
| pytest 전체 | 0 | 45 PASS |
| pre-commit fast 테스트 | 0 | 42 PASS |
| 필수 부정 테스트 매트릭스 | 0 | 21 수집·21 PASS, 01~18 완전성 확인 |
| Stage 00 매니페스트·`backup/` 기준선 | 0 | 86개 일치·Git 변경 0 |
| 문서 위치 검사 | 0 | 필수 5개·루트 오배치 0 |
| `workflow check --scope full --json` | 0 | PASS |
| 자식 7 → CLI | 7 | PASS |
| 자식 7 → pre-commit 격리 계약 테스트 | 7 | PASS |
| uv 결손 → pre-commit 격리 계약 테스트 | 127 | PASS |
| 테스트 0개 수집 | 5 | PASS |
| 실제 Windows pre-commit 실패 기준 재현 | 127 | Git Bash uv 경로 형식 결함 재현 |
| `cygpath`만 적용한 훅 | 127 | 확장자 없는 native 경로라 실패 |
| MSYS `-f` 기반 `.exe` 보정 | 127 | MSYS가 확장자 없는 경로도 파일로 인정 |
| suffix 기반 `.exe` 보정 후 실제 훅 | 0 | fast 전체 통과 |
| 독립 QA 공개 full 재실행 | 0 | 9개 command 모두 completed·0 |
| 독립 QA 최종 로컬 구현 판정 | PASS | 실제 훅·부정 매트릭스·Git 경계 통과 |
| 의존성 결손 테스트 silent return 수정 후 재실행 | 0 | 항상 기반 Python으로 실행됨 |
| 체크포인트 첫째·둘째 commit 훅 | 1 / 1 | 격리 PATH에 `cygpath`가 없어 부모 셸에 따라 uv 경로 형식이 달라짐 |
| 결정적 `cygpath` fixture 추가 후 실제 훅 | 0 | fast 42개 PASS |
| 결정적 fixture 추가 후 full 재실행 | 0 | 45개 PASS |

원격 CI와 clean-clone은 실행되지 않았으며 성공이나 실패로 바꾸어 기록하지 않는다.
둘 다 사용자 승인 체크포인트 커밋 이후의 pending 검사다.
