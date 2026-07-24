# 공통 기록 I/O 계약과 사용법

- 목적: 에이전트가 파일 내부 구현을 직접 다루지 않고 중립 기록을 생성·조회·목록·갱신·추가하는 단일 진입점과 오류를 정의한다.
- 읽는 시점: 공통 기록을 읽거나 쓰고, 새 기록 유형을 연결하거나 I/O 오류를 진단할 때.
- 책임: `core/src/file_data/store.py`가 라이브러리 동작, `core/src/file_data/cli.py`가 명령·종료 상태를 소유한다.
- 상태: 활성 계약.
- 선행 계약: [파일 데이터 저장 계약](FILE_DATA_CONTRACT.md).

## 승인된 진입점

- 라이브러리: `file_data.RecordStore`
- CLI: `python -m file_data --root <project-root> <command>`
- Python: 3.12 표준 라이브러리
- 현재 승인 기록 유형: `example`
- 현재 승인 이벤트 스트림: `example_events`

직접 `open`, 임의 경로 쓰기, 내부 임시 파일 조작은 승인된 사용 경로가 아니다. `init`은 존재하는 프로젝트 루트 아래에 `extension/data/records`와 `extension/data/events`만 만든다.

## 기능 계약

| 기능 | 라이브러리 | CLI | 기대 상태·결과 |
|---|---|---|---|
| 초기화 | `initialize()` | `init` | 승인된 두 데이터 디렉터리 보장 |
| 생성 | `create_record()` | `create` | 새 UUID 또는 지정 UUID의 단일 주소 생성, 중복 거부 |
| 한 건 조회 | `get_record()` | `get` | ID로 엄격 검증된 기록 반환 |
| 유형 목록 | `list_records()` | `list` | 승인 유형만, 파일명 정렬, 손상 한 건도 전체 실패 |
| 기대 갱신 | `update_record()` | `update` | 필수 `expected_content_hash` 일치 때만 payload 교체 |
| 이벤트 추가 | `append_event()` | `append` | 선택적 stream hash 확인, 전체 JSONL 검증 후 원자 교체 |
| 이벤트 목록 | `list_events()` | `list-events` | 전체 이벤트와 현재 stream hash 반환 |

삭제와 이동 기능은 존재하지 않는다. 기대값 불일치나 잠금 충돌은 자동 재시도하지 않고 즉시 반환한다.

## JSONL 내구성

- `extension/data/events/<approved-stream>.jsonl`에 common-record v1 객체를 한 줄씩 저장한다.
- 모든 줄은 stream 이름과 같은 `record_type`, 고유 ID, 유효한 내용 해시를 가져야 한다.
- 빈 줄, 마지막 개행 누락, 중복 ID, 손상된 한 줄, 다른 유형 한 줄을 모두 거부한다.
- 쓰기 전에 대상별 `.lock`을 배타 생성하고 전체 기존 stream을 검증한다.
- 새 전체 bytes를 같은 디렉터리 임시 파일에 쓰고 `fsync`·재읽기 검증·`os.replace`를 수행한다.
- 실패 시 기존 stream을 유지하고 이 프로세스가 만든 임시 파일과 잠금을 정리한다.
- 비정상 종료로 남은 잠금은 자동 삭제하지 않는다. 원인을 확인하기 전 쓰기를 재개하지 않는 fail-closed 신호다.

## 오류·종료 상태

모든 CLI 성공은 stdout의 `{"ok":true,"result":...}`와 종료 상태 0, 실패는 stderr의 `{"ok":false,"error":...}`로 반환한다.

Windows PowerShell처럼 외부 프로세스 인수의 JSON 따옴표를 다시 해석하는 shell에서는 `--payload-json` 대신 UTF-8 JSON을 stdin으로 보내고 `--payload-stdin`을 사용한다. 두 입력 방식은 상호 배타적이며 정확히 하나만 지정한다.

| 종료 상태 | kind | 의미 | 자동 재시도 |
|---:|---|---|---|
| 0 | 성공 | 결과와 실제 파일의 사후 검증 완료 | 해당 없음 |
| 2 | `input_error`, `not_initialized` | 인수·payload·승인 유형·초기화 문제 | 아니요 |
| 3 | `not_found` | 요청한 기록이나 파일이 없음 | 아니요 |
| 4 | `conflict`, `expectation_mismatch`, `concurrent_write` | 중복 ID, 기대 해시 불일치, 잠금 충돌 | 아니요 |
| 5 | `validation_failure` | 스키마·버전·해시·JSONL 손상 | 아니요 |
| 6 | `path_safety` | 승인 경로·보호 경계 위반 | 아니요 |
| 7 | `io_failure` | 접근·flush·교체 같은 파일 I/O 실패 | 원인 확인 뒤 판단 |
| 8 | `internal_error` | 계약에 분류되지 않은 내부 오류 | 아니요 |

## 최소 사용 흐름

번들 Python 실행 경로는 작업 시작 시 조회하고 아래 `<python>`에 넣는다.

```powershell
<python> -m file_data --root . init
'{"message":"neutral"}' | <python> -m file_data --root . create --type example --payload-stdin
<python> -m file_data --root . get --id <uuid>
'{"message":"revised"}' | <python> -m file_data --root . update --id <uuid> --expected-hash <sha256:...> --payload-stdin
'{"message":"event"}' | <python> -m file_data --root . append --stream example_events --payload-stdin
<python> -m file_data --root . list-events --stream example_events
```

실제 프로젝트 루트에서 `init`이나 쓰기 명령을 실행하는 것은 데이터 변경이다. 테스트는 임시 프로젝트 루트에서 수행한다.

## 후속 단계 인계

- 작업 기록·현재 상태 유형은 승인 유형 집합을 확장하되 I/O 구현을 우회하지 않는다.
- 지식 의미·품질·수명주기는 `payload`와 승인 유형 계층이 소유한다.
- stale lock 자동 복구나 대규모 stream 최적화는 별도 요구와 검증 없이 추가하지 않는다.
