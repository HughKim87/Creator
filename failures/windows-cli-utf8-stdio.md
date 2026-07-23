# Windows CLI 표준 입출력 인코딩 불일치

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 03 CLI 통합 테스트
- 마지막 검증: 2026-07-23
- 적용 범위: Windows 파일 읽기·자식 프로세스, JSON CLI, 한글 stdout·stderr, UTF-8 계약

## 증상

CLI가 한글 payload를 포함한 성공 JSON을 출력했지만 Windows 자식 프로세스 stdout이 기본 CP949 바이트를 사용했다. UTF-8 계약대로 읽는 통합 테스트의 reader thread가 디코딩 오류로 중단돼 stdout 결과가 사라졌다.

## 확인된 원인

파일·pipe·프로세스 경계마다 UTF-8을 명시해야 하는데 일부 경계만 고정하고 나머지를 운영체제 기본값에 맡겼다. 최초 실패에서는 프로세스 표준 출력·오류의 `TextIOWrapper`가 기본 CP949를 사용했고, 이번 재발에서는 Windows PowerShell 5.1의 bare `Get-Content`가 BOM 없는 UTF-8 Markdown을 기본 코드 페이지로 해석했다. `json.dumps(..., ensure_ascii=False)`의 실제 한글 출력과 `SESSION_HANDOFF.md`의 한글 본문에서 같은 플랫폼 의존성이 드러났다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 03 첫 24개 테스트 | CLI 한글 성공 흐름에서 CP949 bytes를 UTF-8로 읽어 `UnicodeDecodeError` | 1 | CLI 시작 시 stdout·stderr를 UTF-8 strict와 LF로 재설정하고 전체 24개 테스트 성공 |
| Stage 05 실패 문서 절 분석 | PowerShell here-string의 한글 정규식이 native Python stdin에서 `?`로 변형돼 정규식 컴파일 실패 | 1 | 파이프 전 `$OutputEncoding`을 UTF-8 without BOM으로 지정하고 같은 20개 문서 분석 성공 |
| Stage 06 문서 통합 게이트 | here-string 안의 한글 저장소 절대 경로가 Python stdin에서 `?`로 변형돼 Git `safe.directory`가 무효화 | 별도 게이트 1 | 한글 절대 경로를 pipe로 전달하지 않고 Python의 `Path.cwd()`에서 계산하며 `$OutputEncoding`도 UTF-8로 고정해 71개 문서·489개 링크 검사 성공 |
| Stage 07 실패 재사용 질의 탐색 | 여러 query를 전달한 here-string에서 `$OutputEncoding`을 생략해 한글 query 한 건이 `?`로 변형 | 별도 탐색 1 | ASCII 고유 문구로도 current 실패 record 1건을 확인하고, 이후 native Python stdin 호출의 공통 prefix에 UTF-8 `$OutputEncoding`을 다시 적용 |
| Stage 07 새 지식 실제 생성 | 한글 statement를 포함한 here-string에서 `$OutputEncoding`을 생략해 `?` 문자열이 유효한 verified knowledge로 저장 | 별도 생성 1 | lifecycle로 손상 record를 review_required·superseded 보존하고, UTF-8 pipe를 고정한 새 knowledge의 정확한 statement와 검색 성공을 검증 |
| 2026-07-23 세션 필수 문서 읽기 | Windows PowerShell 5.1에서 bare `Get-Content -Raw`로 BOM 없는 UTF-8 `SESSION_HANDOFF.md`를 읽어 한글이 mojibake로 표시됨 | 별도 시작 읽기 1 | `-Encoding utf8`로 즉시 다시 읽어 정상 본문을 확인하고, `AGENTS.md`의 필수 시작 절차에 세 문서의 UTF-8 명시 읽기를 고정 |

## 해결과 검증

- CLI의 stdout과 stderr가 `reconfigure`를 지원하면 `encoding="utf-8"`, `errors="strict"`, `newline="\n"`을 명시한다.
- 성공과 오류 JSON은 각각 stdout과 stderr에 한 줄 UTF-8로 출력한다.
- 한글 create·get·update CLI 흐름과 구조화 오류 흐름을 subprocess가 UTF-8로 읽어 검증했다.
- Windows PowerShell 5.1.26100.8875와 BOM 없는 `SESSION_HANDOFF.md`를 확인하고, `Get-Content -LiteralPath <path> -Raw -Encoding utf8` 재읽기에서 한글 본문이 정상 복원됨을 검증했다.
- `AGENTS.md`의 `Required startup`이 Windows PowerShell의 bare `Get-Content`를 금지하고 세 필수 시작 문서에 UTF-8 명시 읽기를 요구하는지 확인했다.

## 재사용 규칙

- 파일 UTF-8 계약과 CLI pipe 인코딩 계약을 별도로 검증한다.
- Windows PowerShell에서 Markdown과 제어 문서를 읽을 때는 `-Encoding utf8`을 명시하며, 특히 세션 필수 시작 문서에 bare `Get-Content`를 사용하지 않는다.
- Windows subprocess 통합 테스트는 ASCII만 사용하지 말고 실제 Unicode 값을 포함한다.
- PowerShell에서 한글 스크립트·JSON을 native process stdin으로 보낼 때는 `$OutputEncoding`도 UTF-8로 명시한다.
- JSON을 사람이 읽는 문자로 출력하면 stdout·stderr 인코딩을 운영체제 기본값에 맡기지 않는다.

## 근거

- [공통 기록 I/O 계약](../docs/RECORD_IO_CONTRACT.md)
- [CLI 구현](../src/file_data/cli.py)
- [Stage 03 계획](../docs/build/stage-03-record-io.md)
- [에이전트 시작 진입점](../AGENTS.md)
