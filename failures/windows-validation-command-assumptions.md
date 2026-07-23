# Windows 문서 검증 명령의 환경·문구 가정

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 00 커밋 전 완성 게이트
- 마지막 검증: 2026-07-24
- 적용 범위: Windows PowerShell, `rg`, 문서 링크·문구 단언 검사

## 증상

문서 내용은 정상인데 커밋 전 검증 명령이 Windows 경로 처리와 특정 문구 가정 때문에 중단됐다.

## 확인된 원인

- 네이티브 `rg` 호출에서 `stage-*.md`가 셸에 의해 확장될 것으로 가정했다.
- 루트 파일의 부모 경로가 빈 문자열일 수 있음을 처리하지 않았다.
- 영문 규칙 문서에 한글 문구를 찾았다.
- 의미가 같은 문장을 검증하면서 특정 어순만 허용했다.
- 스테이징 전 `git diff --check`가 추적되지 않은 신규 파일을 검사하지 않는다는 범위를 별도로 보완하지 않았다.
- 긴 PowerShell 검증문을 압축하면서 `foreach`의 변수·`in`·컬렉션 사이 필수 공백까지 제거했다.
- 설치된 Windows PowerShell의 .NET 런타임에 `System.IO.Path.GetRelativePath`가 있다고 가정했다.
- 여러 경로를 한 번에 확인하는 `git diff -- <경로...>`를 추적·미추적 파일이 섞인 상태에서도 파일별 변경 조회처럼 사용할 수 있다고 가정했다.
- sandbox 소유권이 다른 저장소에서 `git check-ignore`를 실행하면서 `safe.directory`를 생략하거나 공백이 있는 경로를 변수 인수로 전달해도 Git이 그대로 인식한다고 가정했다.
- 짧은 진단 반복문으로 줄이면서 닫는 중괄호 하나를 누락했다.
- 오류 종료 상태가 모두 CLI 파일의 literal `return N`으로 구현될 것이라고 가정해 예외 클래스가 소유한 상태를 놓쳤다.
- 완료된 work 재구축을 확인하는 임시 검사기에서 실제 service 메서드명과 반환 record 구조를 먼저 확인하지 않고 축약명과 중첩 hash 위치를 가정했다.
- Stage 08 컨텍스트 평가 사전 검색에서 `context-search`의 실제 옵션을 확인하지 않고 내부 개념명에 가까운 `--query`를 CLI 인수로 가정했다.
- Stage 09 첫 도메인 문서 추가 뒤 maintenance inventory가 Git의 기본 untracked 디렉터리 축약을 파일 목록으로 오인해 중첩된 새 Markdown을 놓쳤다.
- Stage 09 candidate 거부 경로 검증에서 예상된 native stderr까지 `$ErrorActionPreference='Stop'`이 PowerShell 오류로 승격해 의도한 exit code 단언 전에 스크립트를 중단했다.
- 최종 복기 보고서 교차검사에서 단계 표의 `01.5` 행을 구조로 세지 않고 literal `Stage 01.5` 문구가 반드시 존재한다고 가정했다.
- 실패 projection 갱신 준비에서 `lifecycle-current --help`와 실제 조회를 병렬 실행해 도움말 결과를 확인하기 전에 존재하지 않는 `--target-type` 옵션을 추측했다.
- lifecycle 교체 검증에서 `lifecycle-show`의 실제 반환이 `result.lifecycle.payload`와 `result.record`로 나뉘는지 먼저 관찰하지 않고 `result.payload`를 가정했다.
- 최종 문서 검증에서 Windows PowerShell 5.1의 `foreach` 문 출력을 괄호나 변수 없이 바로 pipe할 수 있다고 가정했다.
- Stage 10 문서 데이터 검증에서 source-layout package의 module discovery에 필요한 `PYTHONPATH=src`를 생략해 현재 Python이 `file_data`를 자동 발견할 것이라고 가정했다.
- Stage 10 실패 정본 검증에서 parser 내부 destination 이름 `canonical_doc_ref`를 공개 CLI option으로 오인해 실제 `--doc` 대신 존재하지 않는 `--canonical-doc-ref`를 사용했다.
- Stage 10 후속 자체 재검토에서 Git 조회의 기존 `safe.directory` 요구를 첫 명령에 반영하지 않았고, PowerShell 보간 문자열의 변수 바로 뒤 `:`를 `${name}` 없이 사용해 parser 오류를 냈다.
- 같은 후속 파일 검사에서 정규식 문자 클래스에 PowerShell backtick을 잘못 사용해 문자 `t`까지 trailing whitespace로 오인했고, `rg`의 binary detection 상태에서 NUL 정규식이 그대로 동작할 것이라고 가정했다.
- Stage 10 High 1 보완 집중 검증에서 `tests`가 import package이고 모든 test module이 단독 discovery에서도 source root를 설정할 것이라고 가정했다.
- Stage 10 공식 종료 문서 확인에서 PowerShell 큰따옴표 안의 `\"`가 따옴표 escape로 유지될 것이라고 가정해 `rg` pattern이 여러 경로 인수로 분해됐다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| 사전 단계 문서 검색 | `stage-*.md` 경로 구문 오류 | 별도 검색 1 | 셸 와일드카드 대신 `rg -g 'stage-*.md'` 사용 후 성공 |
| 완성 게이트 1차 | 루트 파일의 빈 부모 경로를 `Join-Path`에 전달 | 1 | 빈 부모를 `.`으로 정규화 |
| 완성 게이트 2차 | 영문 `PROJECT_RULES.md`에 한글 패턴 적용 | 2 | 실제 권위 문서의 영문 의미 문구로 단언 |
| 완성 게이트 3차 | Stage 01 정지점의 특정 어순을 가정 | 3 | 착수 승인과 구현 전 확인 의미를 별도 단언으로 확인 |
| 다음 사용자 실행 요청 | 보정된 21개 파일 게이트 전체 종료 코드 0 | 0 | UTF-8, NUL, 공백, 링크, 라우팅, 승인, 단계 점수, 보호 경계, diff 검사 성공 |
| 31개 파일 캐시 패치 검사 | 신규 파일 12개의 EOF 빈 줄을 스테이징 전 검사에서 놓침 | 1 | EOF 빈 줄을 제거하고 스테이징된 전체 패치에 `git diff --cached --check` 적용 |
| Stage 01 통합 게이트 1차 | 압축된 PowerShell의 `foreach` 토큰 경계가 사라져 파서 오류 | 1 | 검증문을 줄·공백이 보존된 읽기 가능한 형식으로 복원하고 38개 단언 전체 성공 |
| Stage 01 실패 지식 보정 검사 1차 | `Get-Content`의 `-Raw -Encoding` 사이 공백을 제거해 존재하지 않는 매개 변수로 해석 | 1 | 매개 변수를 줄·공백이 보존된 형식으로 복원하고 같은 검사 성공 |
| Stage 01.5 문서 지도 확인 | 추적 파일과 미추적 파일을 한 `git diff --` 호출에 넣어 의도와 달리 두 작업트리 파일을 직접 비교 | 별도 조회 1 | 추적 파일은 `git diff -- <경로>`, 미추적 파일은 직접 읽기로 분리 |
| Stage 01.5 구조 게이트 1차 | 구형 .NET에 없는 `Path.GetRelativePath` 호출 | 1 | 루트 내부 여부를 먼저 단언한 뒤 루트 접두사 제거 방식으로 상대 경로 계산 |
| Stage 01.5 구조 게이트 2차 | 루트 Markdown 파일의 빈 부모 경로를 `Join-Path`에 전달 | 2 | 빈 부모를 `.`으로 정규화한 공통 링크 해석 함수 사용 |
| Stage 01.5 보호 링크 진단 | 줄 범위를 순회하는 짧은 PowerShell에 닫는 중괄호 누락 | 별도 진단 1 | 반복문과 조건문을 여러 줄로 분리하고 각 블록의 닫힘을 확인 |
| Stage 01.5 구조 게이트 재개 2차 | `git check-ignore`가 sandbox 소유권 보호로 거부됨 | 2 | 호출별 `safe.directory` 지정을 시도했으나 다음 시도에서도 인수 해석 실패 |
| Stage 01.5 구조 게이트 재개 3차 | 공백이 포함된 변수형 `safe.directory` 인수가 Git에 적용되지 않음 | 3 | Git 호출을 제거하고 `.gitignore`의 일반 제외와 `app.json` 예외를 직접 단언하는 방식으로 변경해 전체 게이트 성공 |
| Stage 03 예비 게이트 1차 | 종료 상태 2·3·4를 `cli.py`의 literal return으로만 검색해 예외 클래스의 `exit_status` 소유를 놓침 | 1 | store 예외의 2·3·4와 CLI 직접 매핑 5~8, 공통 dispatch를 분리 단언해 1,542개 전체 게이트 성공 |
| Stage 05 경계 게이트 1차 | Git 상태 조회에 검증된 고정 `safe.directory` 인수를 누락해 sandbox 소유권 검사에서 중단 | 1 | 이후 모든 Git 조회에 저장소 절대 경로의 호출별 옵션을 적용 |
| Stage 05 경계 게이트 2차 | work service에 존재하지 않는 `rebuild` 축약 메서드를 호출 | 2 | 구현과 회귀 테스트에서 실제 공개 메서드 `rebuild_snapshot`을 확인해 호출 변경 |
| Stage 05 경계 게이트 3차 | 재구축 record의 hash를 존재하지 않는 `integrity.content_hash`에서 조회 | 3 | 단언을 더 추측하지 않고 반환 객체의 key와 값을 먼저 관찰해 최상위 `content_hash`로 교정한 뒤 전체 게이트 재개 |
| Stage 06 구현 파일 조사 | Windows `rg`에 `src/file_data/*.py` 경로 와일드카드를 직접 전달해 잘못된 경로 구문으로 중단 | 별도 조사 1 | 기존 재사용 규칙대로 검색 루트와 `-g '*.py'` 필터를 분리해 같은 조사를 성공 |
| Stage 08 컨텍스트 평가 사전 검색 | `context-search --query`가 필수 `--text` 누락으로 입력 계약 오류 반환 | 별도 조회 1 | `context-search --help`의 공개 인수를 확인하고 `--text`로 재실행해 새 지식·실패 지식이 각각 정확히 1건 검색됨을 검증 |
| Stage 09 중첩 도메인 문서 inventory | 기본 `git status --short`가 `?? docs/domain/`만 반환해 새 계약 파일을 개별 경로로 수집하지 못하고 오래된 inventory를 일치로 오판 | 별도 게이트 1 | `--untracked-files=all`을 명시하고 중첩 미추적 Markdown 회귀를 추가해 불일치 탐지→재생성→일치 검증 |
| Stage 09 knowledge candidate 경계 검사 | noncurrent candidate의 CLI exit 2·구조화 stderr는 정상인데 전역 `ErrorActionPreference=Stop` 때문에 검증 스크립트 자체가 조기 중단 | 별도 검사 1 | 예상 비성공 구간에서는 native stderr와 `$LASTEXITCODE`를 직접 수집해 exit 2와 원인 문구를 단언하고 성공 |
| Stage 00~09 최종 보고 교차검사 | 표에 `| 01.5 | 98 |` 행이 있지만 literal `Stage 01.5`가 없다는 이유로 검사기만 실패 | 별도 검사 1 | 실제 Markdown 표 행 정규식과 단계 점수 행 11개 count로 보정해 교차검사 성공 |
| 실패 projection 갱신 준비 | `lifecycle-current --help`와 `--target-type failure_knowledge` 조회를 병렬 실행해 조회가 입력 오류로 종료 | 별도 조회 1 | 도움말 출력을 먼저 확인한 뒤 실제 공개 옵션 `--type failure_knowledge`로 재실행해 current 실패 projection 25건과 대상 ID 2건을 정상 조회 |
| lifecycle 교체 상태 검증 | 여덟 대상의 `lifecycle-show` 결과를 실제 한 건 관찰 없이 `result.payload`로 읽어 상태 표가 빈 값으로 출력됨 | 별도 검증 1 | 한 대상의 원시 JSON에서 `result.lifecycle.payload` 구조를 확인하고 그 경로로 상태·대체 ID 검증을 다시 구성 |
| 최종 문서 검증 | `foreach (...) { ... } | Format-Table` 구문이 Windows PowerShell 5.1에서 빈 pipe 요소 파서 오류로 중단 | 별도 검증 1 | `foreach` 결과를 변수에 먼저 저장한 뒤 별도 문장에서 `Format-Table`로 전달하는 호환 구문으로 변경 |
| Stage 10 문서 데이터 최종 검증 | `python -m file_data`를 `PYTHONPATH` 없이 실행해 `No module named file_data`로 중단 | 별도 검증 1 | `PYTHONPATH=src`를 명시해 document-data 6, artifact 20, legacy baseline, maintenance 전체를 재실행하고 성공 |
| Stage 10 실패 정본 최종 검증 | `failure-validate --canonical-doc-ref`가 필수 `--doc` 누락으로 입력 오류 반환 | 별도 검증 1 | `failure-validate --help`를 먼저 확인하고 공개 옵션 `--doc`로 재실행해 canonical failure 검증 성공 |
| Stage 10 후속 자체 재검토 Git 조회 | 저장소별 `safe.directory` 누락으로 첫 status·diff 조회 중단 | 별도 조회 1 | 저장소 절대 경로를 호출별 `-c safe.directory=...`로 고정해 branch·status·diff 조회 성공 |
| Stage 10 후속 변경 파일 직접 검사 | `${name}` 없는 `"$name:"` parser 오류 → 잘못된 `[ `t]` 문자 클래스로 대량 거짓 양성 → binary mode의 `rg \\x00` 제약으로 NUL 검사 실패 | 3 | trailing whitespace는 `rg --pcre2 '[\\x20\\t]+$'`, strict UTF-8·NUL은 .NET strict decoder와 byte 검사로 분리해 대상 미추적 문서·Python 5개 오류 0 확인 |
| Stage 10 High 1 집중 회귀 | `python -m unittest tests.test_record_io`는 `test_support`를 찾지 못했고, maintenance 단독 discovery는 `file_data`를 찾지 못함 | 목적별 별도 명령 각 1 | 파일 패턴 discover는 테스트의 실제 import 경계를 확인해 사용하고, 최종 권위 명령 `python -m unittest discover -s tests -v`로 120건 전체 성공 |
| Stage 10 공식 종료 상태 확인 | 큰따옴표 pattern의 `\"next_action\"` 등이 PowerShell에서 분해돼 `rg`가 pattern 일부를 잘못된 파일 경로로 처리 | 별도 검증 1 | 각 문서의 pattern을 작은 단일 인용 명령으로 분리해 완료·commit·completed/null·자동 착수 금지 상태를 다시 확인 |

## 해결과 검증

- Windows 파일 선택은 `rg -g` 또는 명시적 파일 배열을 사용한다.
- 루트 상대 경로의 빈 부모는 현재 디렉터리 `.`으로 정규화한다.
- 문구 단언은 권위 문서의 실제 언어와 의미 단위에 맞춘다.
- 새 사용자 실행 요청에서 보정된 전체 게이트가 성공해 연속 실패 횟수를 0으로 재설정했다.
- 신규 파일을 포함한 최종 패치 검증은 스테이징 뒤 `git diff --cached --check`로 수행한다.
- 임시 검사기의 API명과 반환 구조는 구현·테스트 또는 실제 무변경 조회로 먼저 확인한 뒤 완료 단언을 작성한다.
- CLI 하위 명령의 자연어 개념명과 공개 옵션명을 동일하다고 가정하지 않고, 처음 호출하기 전에 해당 하위 명령의 `--help`를 확인한다.
- `--help` 조회와 첫 실제 호출을 병렬 실행하지 않는다. 도움말 출력을 확인한 뒤 그 결과로 실제 명령을 구성해야 사전 확인으로 인정한다.
- `--help`는 인수 계약만 확인한다. 응답을 파싱하는 검증기는 실제 무변경 응답 한 건의 key와 중첩 구조를 관찰한 뒤 작성한다.
- Windows PowerShell 5.1에서 statement 출력을 pipe로 넘길 때는 지원 여부를 추측하지 말고 결과를 변수에 저장한 뒤 별도 pipeline으로 전달한다.
- Git status를 파일 inventory로 사용할 때는 untracked 디렉터리 축약 정책을 기본값에 맡기지 않고 `--untracked-files=all`을 명시한다.
- 실패 경로를 검증할 때 예상된 stderr를 예외로 취급하지 말고 native exit code·구조화 payload를 먼저 수집한 뒤 기대한 비성공인지 판정한다.
- 구조화 표의 의미를 검증할 때 임의의 주변 문구를 요구하지 말고 header와 행 pattern·개수를 직접 단언한다.
- source-layout Python package의 module CLI를 실행할 때는 repository contract에 맞는 module search path를 먼저 확인하고 이 프로젝트에서는 `PYTHONPATH=src`를 명시한다.
- PowerShell 보간 문자열에서 변수 바로 뒤에 `:` 같은 이름 문자가 올 수 있으면 `${name}` 형식을 사용한다.
- PowerShell backtick 이스케이프와 정규식 이스케이프를 섞지 않는다. 공백·탭 검사는 검증된 PCRE2 문자 코드 `[\x20\t]`로 분리하고, NUL·strict UTF-8은 byte 검사와 strict decoder로 검증한다.

## 재사용 규칙

- 검증기는 문서 구현과 독립된 코드이므로 검사기 실패와 산출물 실패를 구분한다.
- 문자 그대로의 문장 전체보다 필요한 의미 조건을 작은 단언으로 나눈다.
- 동일 게이트가 연속 실패하면 각 시도의 확인된 원인을 기록하고 프로젝트 중단 규칙을 적용한다.
- 보정 뒤에는 실패 지점만이 아니라 전체 게이트를 처음부터 다시 실행한다.
- 스테이징 전 직접 파일 검사와 스테이징 후 캐시 패치 검사를 모두 수행하고 두 검증의 범위를 혼동하지 않는다.
- 검증문은 명령 길이를 줄이기 위해 문법 토큰 사이 공백을 제거하지 말고, 반복문과 조건을 줄 단위로 유지한다.
- PowerShell cmdlet 이름, 인수, 매개 변수 사이 공백도 문법의 일부로 취급하고 압축하지 않는다.
- Windows PowerShell 런타임 버전을 확인하지 않은 채 최신 .NET API를 사용하지 않는다. 상대 경로는 루트 이탈 검사를 선행하는 호환 구현을 사용한다.
- `git diff`에는 추적 상태가 같은 경로만 넣고, 미추적 파일은 직접 검사하거나 의도적으로 스테이징한 뒤 캐시 diff로 검증한다.
- sandbox에서 Git 메타데이터 조회가 핵심 목적이 아니면 권위 설정 파일을 직접 검사한다. Git 실행이 필요하면 이미 검증된 고정 `safe.directory` 호출 형식을 사용한다.
- 한 줄 진단문도 반복문·조건문의 여는 블록과 닫는 블록 수를 확인하고, 압축으로 블록 경계를 생략하지 않는다.
- 계약 값 검증은 특정 파일·문법 모양을 가정하지 말고 실제 소유자와 dispatch 경로를 함께 확인한다.
- 처음 사용하는 CLI는 완료된 `--help` 결과에 나온 옵션만 사용하며 내부 변수명이나 유사 명령의 옵션을 전용하지 않는다.
- 구조화 응답을 일괄 파싱하기 전에 원시 응답 한 건에서 실제 경로를 확인하고, 필수 값이 비어 있으면 성공으로 보고하지 않는다.
- 검증용 PowerShell은 현재 런타임에서 파싱 가능한 작은 문장으로 나누고, 한 문장에 statement와 pipeline을 압축하지 않는다.
- 연속 검사 실패 시 추측을 한 번 더 덧붙이지 말고 실제 객체 구조를 출력하는 최소 무변경 관찰로 접근법을 전환한다.
- 검증 명령을 실행하기 전에 같은 명령의 테스트·문서가 요구하는 환경 변수와 module root를 확인하며, module discovery 실패를 네트워크나 사용자 승인 문제로 분류하지 않는다.
- 같은 파일 검증 목적에서 검사기 자체가 연속 실패하면 정규식을 계속 덧붙이지 않고, trailing whitespace와 encoding/NUL을 서로 다른 검증 수단으로 분리한다.
- 테스트 일부만 실행할 때는 전체 suite의 선행 import가 `sys.path`를 우연히 보정한다고 가정하지 말고 해당 테스트의 import 계약을 먼저 확인한다. 완료 판정은 저장소가 정한 전체 discover 명령으로 다시 검증한다.
- PowerShell 큰따옴표 안에서 backslash를 quote escape로 사용하지 않는다. literal 큰따옴표가 필요한 `rg` pattern은 작은따옴표로 감싸고 여러 목적의 pattern은 별도 명령으로 분리한다.

## 근거

- [세션 핸드오프](../SESSION_HANDOFF.md)
- [Stage 00 계획](../docs/build/stage-00-project-kernel.md)
