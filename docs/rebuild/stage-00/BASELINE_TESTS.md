# Stage 00 구체계 동작·테스트 기준선

## 1. 실행 경계

- 대상: legacy SHA `8a6ce44068a348c65f21ca69f6cf857aa51fc79b`의 detached worktree
- 환경: 제공된 독립 Python, `PYTHONDONTWRITEBYTECODE=1`, Stage 00 전용 임시 폴더
- 금지: `backup/` 실행, 사용자 데이터 경로 조회, 미디어 생성, 외부 전송
- 분류: `PASS`, `FAIL`, `UNAVAILABLE_POLICY_BOUNDARY`, `NOT_APP_VALIDATED`

## 2. 테스트 결과

| 구분 | 테스트 수 | 직접 Python | `run_python.bat` 출력 | 판정 |
|---|---:|---:|---:|---|
| 안전 실행 가능 | 45 | 45 pass, exit 0 | 45 pass, exit 0 | `PASS` |
| 데이터 경계 충돌 | 29 | 미실행 | 미실행 | `UNAVAILABLE_POLICY_BOUNDARY` |
| 전체 정적 발견 | 74 | - | - | 10개 파일 |

안전 실행 45개는 프레임 자산, 등록, XML, 편집 메모리, 품질 감사, guard, 스킬 문서,
폴더/Python 수명 규칙, Python·Git 래퍼를 포함한다. 실패 테스트는 0개다.

미실행 29개:

- `test_projectctl.py` 8개: 공통 `setUp`이 금지 경로 세그먼트를 생성
- `test_workflow_gate.py` 17개: 공통 `setUp`이 금지 경로 트리를 생성
- `test_skill_asset_lifecycle.py` 3개: 개별 임시 fixture가 금지 경로를 생성
- `test_tool_wrappers.py` preflight 1개: 실제 루트에서 금지 경로 존재 여부를 조회

## 3. 종료 코드 기준선

| 명령 | 실제 종료 코드 | 판정 |
|---|---:|---|
| 독립 Python `-c "raise SystemExit(7)"` | 7 | 정상 전달 |
| `run_python.bat -c "raise SystemExit(7)"` | 0 | 거짓 성공 재현 |

`run_python.bat`의 괄호 블록 안 `%ERRORLEVEL%`이 자식 실행 전에 확장되어 이전 값 `0`을
사용한다. 따라서 래퍼를 거친 45개 통과 출력은 참고 가능하지만, 래퍼 종료 코드 자체는
신뢰할 수 없다. 직접 Python 결과가 기준이다.

## 4. 실행하지 않은 명령

| 표면 | 상태 | 이유 |
|---|---|---|
| 전체 unittest discovery | `UNAVAILABLE_POLICY_BOUNDARY` | 위 29개 fixture가 금지 경로 생성/조회 |
| `project_preflight` | `UNAVAILABLE_POLICY_BOUNDARY` | 후보 경로에 금지 세그먼트를 포함해 존재 조회 |
| doccheck / `run_doccheck.bat` | `UNAVAILABLE_POLICY_BOUNDARY` | 실제 금지 트리를 재귀 조회하는 코드 경로 포함 |
| workflow gate audit | `UNAVAILABLE_POLICY_BOUNDARY` | 실제 금지 트리의 상태 파일을 열도록 설계됨 |
| `projectctl verify` | `UNAVAILABLE_POLICY_BOUNDARY` | doccheck, workflow gate, 전체 discovery를 묶어 실행 |
| FFmpeg/remux | `NOT_APP_VALIDATED` | 승인된 합성 fixture가 없고 사용자 미디어 사용 금지 |
| Premiere/원격 CI/사람 A/V | `NOT_APP_VALIDATED` | Stage 00 로컬 코드 기준선 범위 밖 |

## 5. 보존 영역 결과

| 영역 | 실행 증거 | 남은 공백 |
|---|---|---|
| 소스 프레임·등록 | 9개 통과 | 실제 FFmpeg/JPEG 미검증 |
| 원본 시간·ID 계약 | 프레임 7개와 스킬 문서 4개 통과 | 콘텐츠 해시 계약 없음 |
| Premiere XML | 9개 통과 | 실제 Premiere import 미검증 |
| 편집 품질 감사 | 4개 통과 | `REVIEW` 종료 코드 정책 미분리 |
| 편집 메모리 | 8개 통과 | 사람 승인 provenance 없음 |
| guard | 3개 통과 | fail-open 예외 경로는 정적 결함으로 유지 |
| 문서·수명 규칙 | 안전한 10개 통과 | 금지 경로 fixture 3개 미실행 |
| 래퍼 | 기능 확인 2개 통과, 자식 `7` 별도 재현 | 종료 코드 fail-open |
| workflow/project control | 실행 불가 | 신규 구조에서 데이터 비의존 fixture로 재설계 필요 |
| sync/remux | 전용 테스트 없음 | Stage 04 합성 fixture 필요 |

## 6. 실행 후 무변경

- legacy worktree Git status: 0
- `backup/` tracked status: 0
- 사용자 데이터 열거·해시·복사·입력 사용: 0
- 상세 명령과 수: `evidence/behavior_execution_results.txt`
