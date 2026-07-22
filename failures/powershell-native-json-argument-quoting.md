# PowerShell 외부 프로세스 JSON 인수의 따옴표 손실

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 04 실제 프로젝트 작업 기록 생성
- 마지막 검증: 2026-07-23
- 적용 범위: Windows PowerShell에서 Python CLI에 JSON 객체를 전달하는 명령

## 증상

`ConvertTo-Json -Compress` 결과를 `--request-json` 인수로 전달했지만 CLI는 `Expecting property name enclosed in double quotes` 입력 오류를 반환했다. 앞선 `init`만 성공했고 작업 event와 snapshot은 생성되지 않았다.

## 확인된 원인

Windows PowerShell의 native command 인수 변환 과정에서 JSON 내부 큰따옴표가 Python 프로세스에 그대로 전달되지 않았다. Python `subprocess`의 argv 직접 전달 테스트는 shell 재해석을 거치지 않아 이 결함을 드러내지 못했다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 04 실제 `work-create` | PowerShell 변수의 JSON을 `--request-json`으로 전달해 입력 오류, event·snapshot 미생성 | 1 | `--payload-stdin`·`--request-stdin` 진입점을 추가하고 UTF-8 stdin 회귀 테스트 및 실제 명령으로 검증 |

## 해결과 검증

- create·update·append는 `--payload-json` 또는 `--payload-stdin` 중 하나를 받는다.
- work-create는 `--request-json` 또는 `--request-stdin` 중 하나를 받는다.
- stdin·stdout·stderr를 UTF-8 strict로 구성한다.
- 한글 JSON을 stdin으로 보낸 CLI 회귀 테스트와 실제 프로젝트 작업 생성 결과를 함께 확인한다.

## 재사용 규칙

- shell을 경유하는 구조화 payload는 복잡한 인수 escaping보다 UTF-8 stdin을 우선한다.
- argv 직접 전달 테스트와 실제 사용 shell 테스트를 구분한다.
- 일부 명령이 먼저 성공할 수 있으므로 복합 실행 실패 뒤 생성된 경로와 정본 기록 유무를 각각 확인한다.

## 근거

- [공통 기록 I/O 계약](../docs/RECORD_IO_CONTRACT.md)
- [작업 기록·현재 상태 계약](../docs/WORK_STATE_CONTRACT.md)
- [CLI 구현](../src/file_data/cli.py)
- [Stage 04 계획](../docs/build/stage-04-work-state.md)
