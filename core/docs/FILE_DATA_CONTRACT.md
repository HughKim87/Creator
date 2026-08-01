# 파일 데이터 저장 계약

- 목적: 도메인 의미가 없는 구조화 기록을 파일로 식별·검증·저장하는 공통 계약을 정의한다.
- 읽는 시점: 공통 기록 파일·스키마·저장 코드를 만들거나 기록 유형을 추가할 때.
- 책임: `core/schemas/common-record-v1.schema.json`이 외피 구조, `core/src/file_data/record.py`가 실행 검증·저장 동작을 소유한다.
- 상태: 활성 계약.
- 관련 권위: [정보·문서 책임 구조](INFORMATION_ARCHITECTURE.md).

## 형식 책임

| 사용 형태 | 권장 형식 | 현재 책임 |
|---|---|---|
| 단일 현재 객체·작은 정본 | UTF-8 JSON | 공통 외피와 원자 저장을 구현 |
| 추가 전용 이벤트 | 한 줄 한 객체의 UTF-8 JSONL | append·복구는 공통 기록 I/O 계약이 소유 |
| 사람이 검토하는 서술 정본 | 표준 Markdown | 보이는 최소 메타데이터만 사용 |
| 재생성 가능한 파생 데이터 | UTF-8 JSON 또는 JSONL | 정본과 분리하고 삭제 후 재생성 가능해야 함 |

SQLite, YAML 전용 파서, Obsidian 전용 속성, 외부 데이터베이스는 도입하지 않는다.

## 공통 기록 v1

| 필드 | 계약 |
|---|---|
| `id` | 소문자 canonical UUIDv4. 기록 유형이나 시간을 ID에 인코딩하지 않음 |
| `record_type` | 소문자 snake case 유형 이름. 공통 fixture는 중립 `example`만 사용 |
| `schema_version` | 정수 `1`. 알 수 없는 버전은 거부 |
| `created_at` | UTC RFC 3339, 초 정밀도, `Z` 표기 |
| `updated_at` | 같은 표준이며 `created_at`보다 이를 수 없음 |
| `payload` | JSON 객체. 유형별 필드는 후속 단계가 소유 |
| `content_hash` | `content_hash`를 제외한 canonical JSON의 SHA-256, `sha256:<64 lowercase hex>` |

저장된 `valid` 상태를 기록 자체가 주장하게 하지 않는다. 유효성은 엄격한 UTF-8, JSON 문법, 중복 키, 정확한 필드 집합, ID·버전·시간·NUL·JSON 값·내용 해시를 실행 검증한 결과다.

## 인코딩·경로 계약

- 입력은 BOM 없는 엄격한 UTF-8 JSON으로 해석하며 잘못된 바이트와 NUL을 거부한다.
- JSON 객체의 중복 키, 추가 외피 필드, 비유한 숫자, 문자열이 아닌 키를 거부한다.
- 공통 기록의 단일 주소는 `extension/data/records/<id>.json`이며 파일명 UUID가 기록의 `id`와 정확히 같아야 한다.
- 이 주소 규칙으로 같은 ID는 같은 경로에만 대응하며 기본 덮어쓰기 거부가 중복 ID를 막는다. 별도 디렉터리 전역 열거는 하지 않는다.
- 저장 대상은 존재하는 프로젝트 루트 아래의 정규화된 상대 경로만 허용한다.
- 경로의 어느 구간에도 `.git`, `.obsidian`, `backup`, `inputs`, `outputs`가 있으면 거부한다.
- 절대 경로, `.`·`..`, 프로젝트 루트 탈출, 승인 없이 새 부모 폴더를 만드는 동작을 거부한다.
- Unicode와 공백이 있는 프로젝트·파일 경로를 그대로 지원한다.

## 쓰기·복구 계약

1. 메모리 기록을 먼저 완전히 검증하고 결정적 UTF-8 JSON으로 인코딩한다.
2. 대상과 같은 디렉터리에 전용 임시 파일을 만들고 flush와 `fsync`를 수행한다.
3. 임시 파일을 다시 읽어 전체 기록과 해시를 검증한다.
4. 같은 파일시스템의 `os.replace`로 단일 원자 교체한다.
5. 교체 전 오류는 임시 파일을 지우고 기존 파일을 유지한다.

기존 경로는 기본적으로 덮어쓰지 않는다. 명시적 `overwrite=True`에서도 기존 기록과 새 기록의 ID가 다르거나 파일명이 ID와 다르면 거부한다. 교체 성공 뒤의 별도 버전 백업, 잠금, 낙관적 동시성, 자동 stale 임시 파일 복구는 이 계약의 범위가 아니다.

## 실행 환경

- Python 3.12 표준 라이브러리만 사용한다.
- 패키지 설치와 네트워크가 필요하지 않다.
- 테스트는 번들 Python으로 `-m unittest discover -s tests -v`를 실행한다.

## 연계 계약

- [공통 기록 I/O 계약](RECORD_IO_CONTRACT.md)은 이 외피와 안전 경로·원자 저장 함수를 재사용한다.
- 작업 상태·지식 유형·수명주기 계약이 `payload` 내부의 유형별 필드를 소유한다.
- 동시 작성과 자동 유지보수는 각 전용 계약에서 명시한 범위만 허용한다.

## 문서 소유 파생 artifact

아래 block이 공통 외피 schema와 중립 fixture의 exact 정본이다. `ArtifactService`는 승인된 기존 경로에만 이를 재생성한다.

<!-- project-artifact:v1 path=core/schemas/common-record-v1.schema.json verify=json-semantic -->
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"project://core/schemas/common-record-v1.schema.json","title":"Common Record v1","description":"Domain-neutral file record envelope.","type":"object","additionalProperties":false,"required":["id","record_type","schema_version","created_at","updated_at","payload","content_hash"],"properties":{"id":{"type":"string","format":"uuid","pattern":"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"},"record_type":{"type":"string","pattern":"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"},"schema_version":{"const":1},"created_at":{"type":"string","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"},"updated_at":{"type":"string","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"},"payload":{"type":"object"},"content_hash":{"type":"string","pattern":"^sha256:[0-9a-f]{64}$"}}}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=core/tests/fixtures/file_data/valid/neutral-record.json verify=json-semantic -->
```json
{"content_hash":"sha256:4533820fa597a429c82eb1b4ab95418cb6bd9f9d380a30091b350ff4cd240360","created_at":"2026-07-23T00:00:00Z","id":"123e4567-e89b-42d3-a456-426614174000","payload":{"message":"중립 예제"},"record_type":"example","schema_version":1,"updated_at":"2026-07-23T00:00:00Z"}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=core/tests/fixtures/file_data/invalid/missing-field.json verify=json-semantic -->
```json
{"created_at":"2026-07-23T00:00:00Z","id":"123e4567-e89b-42d3-a456-426614174000","payload":{},"record_type":"example","schema_version":1,"updated_at":"2026-07-23T00:00:00Z"}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=core/tests/fixtures/file_data/invalid/tampered-content.json verify=json-semantic -->
```json
{"content_hash":"sha256:4533820fa597a429c82eb1b4ab95418cb6bd9f9d380a30091b350ff4cd240360","created_at":"2026-07-23T00:00:00Z","id":"123e4567-e89b-42d3-a456-426614174000","payload":{"message":"변조됨"},"record_type":"example","schema_version":1,"updated_at":"2026-07-23T00:00:00Z"}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=core/tests/fixtures/file_data/invalid/wrong-id.json verify=json-semantic -->
```json
{"content_hash":"sha256:0000000000000000000000000000000000000000000000000000000000000000","created_at":"2026-07-23T00:00:00Z","id":"not-a-uuid","payload":{},"record_type":"example","schema_version":1,"updated_at":"2026-07-23T00:00:00Z"}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=core/tests/fixtures/file_data/invalid/wrong-version.json verify=json-semantic -->
```json
{"content_hash":"sha256:0000000000000000000000000000000000000000000000000000000000000000","created_at":"2026-07-23T00:00:00Z","id":"123e4567-e89b-42d3-a456-426614174000","payload":{},"record_type":"example","schema_version":2,"updated_at":"2026-07-23T00:00:00Z"}
```
<!-- /project-artifact -->
