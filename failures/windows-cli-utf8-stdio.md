# Windows CLI 표준 입출력 인코딩 불일치

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 03 CLI 통합 테스트
- 마지막 검증: 2026-07-23
- 적용 범위: Windows 자식 프로세스, JSON CLI, 한글 stdout·stderr, UTF-8 계약

## 증상

CLI가 한글 payload를 포함한 성공 JSON을 출력했지만 Windows 자식 프로세스 stdout이 기본 CP949 바이트를 사용했다. UTF-8 계약대로 읽는 통합 테스트의 reader thread가 디코딩 오류로 중단돼 stdout 결과가 사라졌다.

## 확인된 원인

파일 인코딩만 UTF-8로 고정하고 프로세스 표준 출력·오류의 `TextIOWrapper` 인코딩은 운영체제 기본값에 맡겼다. `json.dumps(..., ensure_ascii=False)`가 실제 한글 문자를 쓰면서 플랫폼 차이가 드러났다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 03 첫 24개 테스트 | CLI 한글 성공 흐름에서 CP949 bytes를 UTF-8로 읽어 `UnicodeDecodeError` | 1 | CLI 시작 시 stdout·stderr를 UTF-8 strict와 LF로 재설정하고 전체 24개 테스트 성공 |
| Stage 05 실패 문서 절 분석 | PowerShell here-string의 한글 정규식이 native Python stdin에서 `?`로 변형돼 정규식 컴파일 실패 | 1 | 파이프 전 `$OutputEncoding`을 UTF-8 without BOM으로 지정하고 같은 20개 문서 분석 성공 |
| Stage 06 문서 통합 게이트 | here-string 안의 한글 저장소 절대 경로가 Python stdin에서 `?`로 변형돼 Git `safe.directory`가 무효화 | 별도 게이트 1 | 한글 절대 경로를 pipe로 전달하지 않고 Python의 `Path.cwd()`에서 계산하며 `$OutputEncoding`도 UTF-8로 고정해 71개 문서·489개 링크 검사 성공 |

## 해결과 검증

- CLI의 stdout과 stderr가 `reconfigure`를 지원하면 `encoding="utf-8"`, `errors="strict"`, `newline="\n"`을 명시한다.
- 성공과 오류 JSON은 각각 stdout과 stderr에 한 줄 UTF-8로 출력한다.
- 한글 create·get·update CLI 흐름과 구조화 오류 흐름을 subprocess가 UTF-8로 읽어 검증했다.

## 재사용 규칙

- 파일 UTF-8 계약과 CLI pipe 인코딩 계약을 별도로 검증한다.
- Windows subprocess 통합 테스트는 ASCII만 사용하지 말고 실제 Unicode 값을 포함한다.
- PowerShell에서 한글 스크립트·JSON을 native process stdin으로 보낼 때는 `$OutputEncoding`도 UTF-8로 명시한다.
- JSON을 사람이 읽는 문자로 출력하면 stdout·stderr 인코딩을 운영체제 기본값에 맡기지 않는다.

## 근거

- [공통 기록 I/O 계약](../docs/RECORD_IO_CONTRACT.md)
- [CLI 구현](../src/file_data/cli.py)
- [Stage 03 계획](../docs/build/stage-03-record-io.md)
