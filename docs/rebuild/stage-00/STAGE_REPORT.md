# Stage 00 기준선 동결 보고서

- 역할: Stage 00 결과와 다음 행동의 단일 단계 보고서.
- 읽는 시점: Stage 00 검증·재개 또는 Stage 01 승인 판단 시.
- 보존 조건: 신규 구조 전환 안정화 전까지; 세부 절차는 상위 규칙을 참조한다.
- 데이터 경계 정본: `PROJECT_RULES.md`의 `User Data Boundary`.

## 1. 현재 판정

| 범위 | 판정 |
|---|---|
| Git 추적 프레임워크 인벤토리 | 완료·구조 검증됨 |
| 이식 카탈로그와 정적 결함 기준선 | 완료·구조 검증됨 |
| legacy 테스트·래퍼 실제 실행 | 45개 통과·29개 안전정책상 실행 불가 |
| 래퍼 종료 코드 기준선 | 자식 `7`이 최종 `0`으로 바뀌는 거짓 성공 재현 |
| 독립 읽기 전용 검증 | PASS |
| 신규 구현과 Stage 01 | 미착수 |

## 2. 기준 상태

- 브랜치: `feature/refactoring`
- HEAD: `dc7f18b4715bff99b806872f742bf1602e2d0418`
- `backup/` Git worktree/index 변경: 0
- 현재 변경: 루트 규칙·실행 문서와 Git 가시화된 `docs/rebuild/stage-00/` 기록
- legacy 실행 worktree: `8a6ce44068a348c65f21ca69f6cf857aa51fc79b`에서 검증 후 제거
- commit/tag/push: 수행하지 않음

## 3. 사용자 데이터 경계 정정

초기 Stage 00 생성기는 `backup/` 파일시스템 전체를 열거해 사용자 데이터의 파일별
메타데이터를 보고서에 저장했다. 이는 사용자 원칙 위반이었다.

정정 사항:

1. 초기 매니페스트와 스냅샷은 같은 경로에서 schema version 2로 덮어썼다.
2. 생성기 입력을 `git ls-files -- backup`의 추적 프레임워크 파일로 제한했다.
3. 금지 경로 세그먼트와 민감 패턴은 파일 접근 전에 차단한다.
4. ignored·미추적 파일시스템을 재귀 열거하지 않는다.
5. 현재 보고서·증거에는 실제 사용자 데이터의 경로·이름·수·크기·해시가 없다.

## 4. 프레임워크 기준선

| 역할 | 파일 수 |
|---|---:|
| code | 30 |
| test | 10 |
| contract | 22 |
| doc | 24 |
| 합계 | 86 |

- 86개 모두 SHA-256 보유, 경로 중복 0
- 매니페스트 2회 전체 JSON SHA-256 일치
- `backup/` 사전·사후 Git 변경 0

## 5. 동작 기준선

- 실제 Python 직접 실행: 허용된 45개 테스트 통과, 실패 0
- `run_python.bat` 실행: 같은 45개가 출력상 통과
- 전체 74개 중 29개는 테스트 또는 대상 도구가 금지 데이터 경로를 만들거나 조회하므로
  실행하지 않고 `UNAVAILABLE_POLICY_BOUNDARY`로 분류
- 자식 종료 코드 비교: 직접 `7`, `run_python.bat` 최종 `0`
- 원인: 괄호 블록 안의 `%ERRORLEVEL%`이 자식 실행 전에 확장되어 이전 값 `0`을 전달
- 격리 worktree와 `backup/`의 실행 후 Git 변경: 각각 0

## 6. 알려진 결함 기준선

- `run_python.bat`은 비정상 자식 종료 코드를 성공으로 바꾸는 것이 실제 재현됐다.
- 현재 pre-commit은 검사기 또는 Python 결손을 성공으로 처리한다.
- 현재 CI는 루트에 없는 검사·테스트 경로를 참조한다.
- remux 래퍼는 자식 실패를 최종 코드로 보존하지 않을 가능성이 있다.
- 일부 XML 생성 경로는 probe 실패를 기본값으로 대체한다.
- 승인 provenance와 `default_deny` 강제 검사가 부족하다.

세부 근거와 검증 수준은 `BASELINE_TESTS.md`와 `KNOWN_FAILURES.md`를 따른다.

## 7. 검증 수준

- 생성됨: 매니페스트, 이식 카탈로그, 정적 동작 기준선, 골든 픽스처 계획
- 파싱됨: JSON schema version 2 문서
- 구조 검증됨: 필수 문서, 역할 집계, 경로 고유성, 해시, UTF-8, NUL, 참조
- 도구 검증됨: 생성기 결정성, 허용 테스트 45개 직접 실행, 래퍼 실행, 자식 `7` 비교
- 정책상 실행 불가: doccheck, preflight, projectctl verify, 실제 workflow gate와 29개 테스트
  (금지 데이터 경로 접근을 요구함)
- 독립 검증됨: schema v2 86개 해시·역할, 45/29 분류, 종료코드 `7→0`, 두 작업공간
  clean, UTF-8/NUL/참조를 재확인해 PASS
- 앱 검증·사용자 품질 승인: 수행하지 않음

## 8. 실패 원장

| objective | attempt | result/cause | consecutive count | next condition |
|---|---|---|---:|---|
| 초기 인벤토리 | v1 | 사용자 데이터 경계를 어기고 전체 파일시스템 메타데이터를 저장 | 0, v2 정정·금지 참조 0으로 reset | schema v2만 활성 |
| v2 생성기 실행 | 1 | 로컬 PowerShell 실행 정책으로 직접 실행 거부 | 0, 승인된 우회 실행 성공으로 reset | `-ExecutionPolicy Bypass -File` 사용 |
| 테스트 환경 탐색 | 1 | 시스템 `py -3`에 설치된 Python 없음 | 0, 제공된 독립 Python으로 성공해 reset | 독립 runtime 사용 |
| worktree Git 조회 | 1 | sandbox 계정의 safe-directory 검사로 거부 | 0, 명령별 `safe.directory` 지정 후 성공 | 전역 설정 변경 없음 |

## 9. 다음 행동

1. Stage 00은 독립 검증 PASS로 닫는다.
2. Stage 01은 사용자 별도 승인 후 현재 규칙을 저장소 검사·테스트·훅으로 강제한다.
3. 격리 worktree와 runtime 임시 폴더는 검증 후 제거했으며 다시 만들려면 별도 승인이 필요하다.
4. 이 보고서와 재현 가능한 작은 증거는 프로젝트의 순차 구축 기록으로 Git 추적한다.

## 10. 주요 산출물

- `REPOSITORY_BASELINE.md`: 추적 프레임워크 기준선
- `BACKUP_MANIFEST.json`: 활성 schema v2 매니페스트
- `MIGRATION_CATALOG.md`: 이식 분류
- `BASELINE_TESTS.md`: 실제 실행·안전상 미실행 동작 기준선
- `KNOWN_FAILURES.md`: 결함과 검증 공백
- `evidence/behavior_execution_results.txt`: 명령·종료코드·테스트 수 증거
- `evidence/final_validation.txt`: 최종 검증 요약

중복 백업은 만들지 않았다. 단계 문서·증거는 `docs/rebuild`로 분리했고, 실제 프로젝트
구현은 루트에서만 진행한다. 유일한 전체 복제본이던 임시 legacy worktree는 제거했다.
