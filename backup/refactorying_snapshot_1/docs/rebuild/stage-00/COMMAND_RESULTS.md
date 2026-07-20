# Stage 00 명령·검증 결과

- 역할: 실제 실행·미실행 명령과 종료 상태 기록.
- 읽는 시점: Stage 00 검증 또는 실패 재현 시.
- 보존 조건: Stage 00 보고서와 함께 유지.

## 1. 실행 결과

| 목적 | 결과 | 상태 |
|---|---|---|
| 브랜치·HEAD 조회 | `feature/refactoring`, `dc7f18b4715bff99b806872f742bf1602e2d0418` | 성공 |
| `core.hooksPath` 조회 | `.githooks` | 성공 |
| `backup/` worktree/index diff | 각 0건 | 성공 |
| 추적 프레임워크 목록 | `git ls-files -- backup`, 86개 | 성공 |
| 매니페스트 pass 1/2 | 전체 JSON SHA-256 동일 | 성공 |
| 매니페스트 schema | version 2 | 파싱 성공 |
| 금지 경로 선접근 차단 | 생성기 정적 검사와 결과 검색 | 성공 |
| 구체계 이동 직전 SHA 조회 | `8a6ce44068a348c65f21ca69f6cf857aa51fc79b` | 성공 |
| detached legacy worktree 생성 | 위 SHA, 실행 후 clean | 성공 |
| 안전 테스트 직접 실행 | 45 pass, 0 fail, exit 0 | 성공 |
| 같은 테스트 Python 래퍼 실행 | 출력상 45 pass, exit 0 | 성공·종료코드 신뢰 불가 |
| 자식 종료 `7` 직접 실행 | exit 7 | 성공 |
| 자식 종료 `7` 래퍼 실행 | exit 0 | 거짓 성공 재현 |
| 독립 읽기 전용 검증 | 86개 매니페스트·74개 테스트 분류·`7→0`·clean 상태 재확인 | PASS |
| 임시 legacy worktree 정리 | Git worktree 등록과 디렉터리 제거, 빈 runtime 폴더 제거 | 성공 |

매니페스트 SHA-256:
`87d9bfe3938c42b04bcf1234bc48dce4c0823f44277ed74e7938b6d2546c4f54`

## 2. 정책상 실행하지 않은 표면

- 전체 74개 중 금지 경로 fixture를 요구하는 29개 테스트
- doccheck, preflight, projectctl verify, 실제 workflow gate
- FFmpeg·Premiere 생성 및 앱 검증
- 원격 CI

미실행은 실패가 아니라 `UNAVAILABLE_POLICY_BOUNDARY` 또는 `NOT_APP_VALIDATED`다.

## 3. 실행 중 문제

| objective | attempt | 결과 | 처리 |
|---|---|---|---|
| v2 생성기 실행 | 1 | 시스템 PowerShell 실행 정책이 스크립트 직접 실행을 거부 | 파일 변경 없음 확인 |
| v2 생성기 실행 | 2 | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File`로 성공 | 결정성 검증 통과 |
| 테스트 환경 탐색 | 1 | 시스템 `py -3` 사용 불가 | 독립 Python으로 전환 후 성공 |
| worktree Git 조회 | 1 | sandbox safe-directory 검사로 거부 | 명령별 safe.directory 지정 후 성공 |

같은 objective의 연속 실패는 성공 후 0으로 reset됐다.

## 4. 범위 보호

- 원격 주소·네트워크·외부 시스템을 조회하지 않았다.
- 사용자 데이터 파일시스템을 열거하거나 해시하지 않았다.
- commit, tag, push를 수행하지 않았다.
- 승인 범위의 detached legacy worktree만 만들었고 실행 후 clean 상태다.
- 독립 검증 완료 후 해당 worktree와 빈 runtime 임시 폴더를 제거했다.
- 변경은 현재 규칙·실행 문서와 `docs/rebuild/stage-00/` 정정본에 한정된다.
