# 단계 03 작업 지시서: SQLite 단일 상태 정본

## 1. 단계 목적

분산된 JSON, 핸드오프, 편집 메모리, 현재 포인터가 각각 상태 원본처럼 동작하던 문제를
제거한다. 프로젝트별 `workflow.sqlite`를 유일한 영속 상태 정본으로 사용하고,
JSON·Markdown 상태 문서는 DB에서 생성되는 읽기 전용 보기로 만든다.

## 2. 시작 게이트

- 단계 01의 fail-closed 검증이 통과했다.
- 단계 02의 도메인 계약과 사용자 의미 승인이 완료됐다.
- 외부 작업 공간 경계가 승인됐다.
- 실제 사용자 작업 공간 생성 여부를 별도 확인했다. 승인 전에는 임시 작업 공간만 쓴다.

## 3. 역할과 소유권

### 저장소 에이전트

- `src/video_workflow/storage/**`
- `src/video_workflow/storage/migrations/**`
- `tests/unit/storage/**`
- `tests/migration/**`

### 상태 서비스 에이전트

- `src/video_workflow/services/state_service.py`
- `src/video_workflow/services/state_views.py`
- 해당 단위 테스트

### QA 에이전트

- `tests/integration/state/**`
- `tests/golden/state/**`

### 레드팀 에이전트

- 기본 읽기 전용
- 동시 writer, 부분 커밋, 생성 문서 변조, 손상 DB, 미래 스키마를 공격한다.

저장소 인터페이스를 총괄 에이전트가 먼저 동결한 뒤 서비스 구현을 시작한다. DB 스키마와
공용 CLI는 둘 이상의 에이전트가 동시에 수정하지 않는다.

## 4. 금지 사항

- `backup/` 수정 또는 구체계 상태 파일 import
- SQLite 외 별도 JSON 상태 정본
- DB가 없을 때 읽기 명령이 묵시적으로 새 DB 생성
- 생성 `status.json`이나 핸드오프의 수동 편집을 입력으로 사용
- 기술 테스트 결과로 사람 A/V 승인 자동 생성
- 전역 단일 활성 작업 잠금
- 네트워크 공유 경로에서 검증 없이 WAL 사용
- PostgreSQL, Redis, Temporal, Cognee 등 추가
- 실제 사용자 작업 DB를 승인 없이 생성·삭제·덮어쓰기

## 5. 작업 공간 경계

```text
<workspace>/projects/<project_id>/
├─ workflow.sqlite
├─ inputs/
├─ artifacts/
├─ approvals/
└─ generated/
   ├─ status.json
   └─ SESSION_HANDOFF.md
```

- 저장소에는 코드, 테스트, 스키마, 문서만 둔다.
- 실제 작업 공간에는 DB, 원본 참조, 산출물, 생성 상태 보기를 둔다.
- 초기 명령은 `--workspace`를 명시적으로 받는다.
- 불명확한 기본 경로에 자동 생성하지 않는다.
- 원본은 읽기 전용으로 열고 DB에는 지문과 프로젝트 기준 locator를 저장한다.

## 6. 최소 스키마

### `schema_meta`

- `schema_version`
- `applied_at`
- `application_version`

### `projects`

- `project_id`
- `source_id`
- `lifecycle_status`
- `current_phase`
- `state_version`
- `created_at`, `updated_at`
- `last_event_id`

### `workflow_events`

- `event_id`
- `command_id`
- `project_id`
- `event_type`
- 이전·다음 status와 phase
- `actor`, `reason`
- 결정적으로 직렬화한 `payload_json`
- `occurred_at`

이 테이블은 append-only이며 `command_id`는 중복 적용을 차단한다.
DB trigger 또는 동등한 저장소 제한으로 일반 실행 계정의 직접 `UPDATE`, `DELETE`를
거부한다. `command_id`에는 정규화한 action/payload 지문을 연결해 같은 ID와 다른
요청의 재사용을 충돌로 처리한다.

### `sources`

- `source_id`, `project_id`
- 지문 알고리즘과 값
- `size_bytes`
- 작업 공간 기준 locator
- 미디어 메타데이터
- `registered_at`

### `artifacts`

- `artifact_id`, `project_id`, `source_id`, `generation_id`
- `role`, `relative_path`
- SHA-256, 크기, 생성 도구 버전
- 검증 상태, artifact lifecycle(`staging`, `ready`, `failed`, `quarantined`), 부모 계보
- `created_at`

승인 상태의 정본은 아래 `approvals`뿐이다. artifact 승인 여부가 필요한 조회는
`approvals`에서 파생하며 `artifacts`에 두 번째 정본으로 저장하지 않는다.

### `approvals`

- `approval_id`, `project_id`, `generation_id`
- `scope`, `decision`, `actor`, `actor_kind`, 승인 provenance
- 승인 대상 해시 또는 기준선
- 증거와 `created_at`

### `failures`

- `failure_id`, `project_id`, `phase`
- `failure_code`, `fingerprint`, `message`, `tool`
- 재시도 횟수와 연결 이벤트
- 발생·해결 시각

모든 외래키, 유일성, 필수값, 허용 enum에는 DB 제약조건과 서비스 계층 검증을 함께
둔다.

## 7. SQLite 운영 계약

- 연결마다 `foreign_keys`를 활성화한다.
- 명시적 트랜잭션을 사용한다.
- 쓰기 작업은 `BEGIN IMMEDIATE` 또는 동등한 단일 writer 규칙을 적용한다.
- 합리적인 `busy_timeout`을 설정하되 잠김을 성공으로 바꾸지 않는다.
- `state_version`으로 낙관적 동시성 제어를 한다.
- 초기 내구성 설정은 안전 우선으로 정한다.
- 초기 버전은 UNC·네트워크 공유 작업 공간을 기본 거부한다. 예외를 지원해야 하면
  사용자 승인 후 `journal_mode=DELETE`를 강제하고 연결 시 실제 journal mode를 검사한다.
  경고만 출력하고 WAL을 계속 사용하는 경로는 금지한다.
- 스키마 마이그레이션 전 SQLite backup API로 일관된 사본을 만든다.
- DB 손상·미지원 미래 스키마는 새 DB로 초기화하지 않고 실패한다.

## 8. 최소 CLI 계약

```text
workflow state init --workspace ... --project ...
workflow state status
workflow state wait --reason ...
workflow state resume --reason ...
workflow state block --external-code ... --reason ...
workflow state unblock --reason ...
workflow state fail --code ... --reason ...
workflow state retry --reason ...
workflow state advance --to ... --reason ...
workflow state complete --reason ...
workflow state verify
workflow state export
workflow approval request --scope ... --artifact-id ... --artifact-sha256 ...
workflow approval record --request-id ... --decision ... --evidence-id ...
workflow approval verify --approval-id ...
```

- `init`만 DB와 프로젝트 디렉터리를 만든다.
- `status`, `verify`, `export`는 DB가 없으면 비정상 종료한다.
- 모든 쓰기 명령은 `command_id`, `actor`, `reason`을 기록한다.
- 동일 `command_id` 재시도는 이중 적용하지 않는다.
- 잘못된 전이는 DB를 바꾸지 않고 비정상 종료한다.
- 에이전트가 사람 승인 actor를 가장해 입력하지 못하게 한다.

`wait/resume`은 사용자 결정을 기다리는 lifecycle에만 사용하고 `block/unblock`은 렌더러,
스토리지, 권한 같은 외부 조건에만 사용한다. 둘 다 현재 phase를 보존한다.

### 사람 승인 신뢰 경계

- 에이전트는 `approval request`로 검토 대상 artifact ID·해시·scope와 일회용 challenge를
  만들 수 있다.
- `approval record`에는 임의 `--actor human` 옵션을 제공하지 않는다. 대상과 challenge가
  일치하는 사용자 통제 입력의 evidence ID가 필수다.
- 허용 provenance는 플랫폼이 제공하는 사용자 메시지/승인 UI의 검증 가능한 이벤트 ID
  또는 사용자가 직접 실행한 interactive local CLI challenge 응답이다. 구현 전에 실제
  환경이 어느 방식을 지원하는지 확인하고 하나를 동결한다.
- 플랫폼의 사용자 이벤트를 검증할 어댑터가 없고 사용자가 직접 CLI를 실행하지 않은
  경우 승인 기록은 `waiting_user`로 남긴다. 에이전트의 자유 형식 메모를 사람 승인으로
  변환하지 않는다.
- 저장 레코드에는 `actor_kind=HUMAN`, provenance type, evidence ID·해시, request ID,
  artifact ID·해시, decision, UTC 시각을 기록한다. 증거 원문의 비밀값은 저장하지 않는다.
- evidence ID 재사용, challenge 불일치, 대상 해시 변경, agent credential/session에서의
  직접 record 호출은 모두 거부한다.

## 9. 세부 작업

### 작업 03-1: 저장소 포트 정의

도메인 계층이 의존할 저장소 인터페이스를 먼저 정의한다. SQLite 구현 세부사항이 도메인
타입이나 상태 의미에 새어 나오지 않게 한다.

### 작업 03-2: 초기 마이그레이션

- `0001_initial.sql`과 스키마 버전 검사를 만든다.
- 마이그레이션은 순서, 적용 여부, 애플리케이션 버전을 기록한다.
- 미래 스키마를 오래된 코드가 열면 실패한다.
- 마이그레이션이 중간 실패하면 이전 DB를 계속 사용할 수 있어야 한다.

### 작업 03-3: 원자적 상태 변경

한 명령에서 다음을 하나의 트랜잭션으로 처리한다.

1. 현재 상태와 `state_version` 확인
2. 도메인 전이 검증
3. 이벤트 삽입
4. 현재 상태 갱신
5. 승인·실패·산출물 관련 레코드 갱신
6. 커밋

중간 하나라도 실패하면 모두 롤백한다.

### 작업 03-4: 생성 상태 보기

`state export`는 다음을 생성한다.

```text
generated/status.json
generated/SESSION_HANDOFF.md
```

필수 메타데이터:

- `DO NOT EDIT — generated from workflow.sqlite`
- `schema_version`, `project_id`, `state_version`, `last_event_id`
- 생성 시각과 생성 애플리케이션 버전

임시 파일에 완전히 쓴 뒤 원자적으로 교체한다. 다음 명령은 이 파일을 읽어 상태를
결정하지 않는다.

### 작업 03-5: 상태 무결성 검사

`workflow state verify`는 다음을 검사한다.

- 현재 상태와 마지막 이벤트 일치
- 이벤트 체인의 이전·다음 상태 일치
- 누락·중복 command ID
- 같은 command ID에 서로 다른 action/payload 지문
- 승인과 세대·해시 일치
- 산출물 파일과 DB 해시 일치
- 생성 뷰와 DB 버전 일치
- 원본 지문 무결성
- event append-only 제약과 snapshot-event 일치. 불일치 시 자동 수선하지 않고 실패

## 10. 필수 테스트

### 상태 전이

- 허용 전이 성공
- 단계 건너뛰기 실패
- `waiting_user` 진입 시 phase 유지
- resume 후 올바른 phase 복귀
- 승인 없이 complete·delivery 거부
- 완료 후 일반 상태 변경 거부

### 원자성

이벤트 삽입과 상태 갱신 사이에 의도적 오류를 발생시킨다. 이벤트만 남거나 상태만
변경되면 실패이며 둘 다 롤백돼야 한다.

### 동시성

같은 `state_version`을 읽은 두 writer가 동시에 갱신할 때 정확히 하나만 성공하고 다른
하나는 구조화된 충돌을 반환해야 한다.

### 멱등성

동일 `command_id`로 같은 명령을 두 번 실행해 이벤트와 상태 변경이 한 번만 발생하는지
확인한다. 동일 `command_id`로 다른 action 또는 payload를 보내면 충돌로 실패해야 한다.

### 결손·손상

- DB 없음에서 읽기 명령 실패와 자동 생성 없음
- 스키마 없음, 미래 스키마, 손상 DB 실패
- 외래키·CHECK·UNIQUE 위반 실패
- `workflow_events` 직접 `UPDATE`·`DELETE` 거부
- snapshot과 이벤트 체인 불일치 시 자동 수선 없이 실패

### 승인 분리

- 기술 검증만으로 콘텐츠 승인 생성 금지
- actor, scope, generation, 기준선 누락 거부
- 이전 세대 승인 재사용 거부
- 에이전트 actor가 사람 승인 레코드를 만드는 시도 거부
- approval 정본과 artifact 파생 승인 조회의 불일치 탐지
- agent session에서 `approval record` 직접 호출 거부
- evidence ID 재사용, challenge 불일치, artifact 해시 변경 후 승인 거부
- 검증 가능한 사용자 이벤트 어댑터 부재 시 자동 승인 대신 `waiting_user`

### 산출물 계보

- 다른 `source_id`의 artifact 연결 거부
- 존재하지 않는 generation 또는 parent artifact 거부
- 순환 부모 계보 거부

### 생성 보기

- 같은 DB에서 두 번 생성한 정규화 결과 동일
- 수동 수정한 생성 파일을 DB에서 재생성 가능
- 생성 파일을 바꿔도 DB가 변하지 않음
- 쓰기 중 오류에서 반쪽 파일이 남지 않음

### 경로·복구

- 한글·공백 경로에서 init, 전이, export, verify 통과
- 마이그레이션 전 백업, 중간 실패, 원본 복구 통과
- 네트워크 공유 경로는 기본 거부됨. 승인된 예외에서는 실제
  `journal_mode=DELETE`가 강제되고 WAL이 아님

## 11. 완료 기준

- 영속 상태 정본이 프로젝트별 SQLite 하나임
- JSON·Markdown을 읽어 상태를 판단하는 코드 0건
- 불법 전이와 승인 없는 완료 성공 0건
- 동시 writer 이중 상태 변경 0건
- 부분 커밋 0건
- 동일 command 중복 적용 0건
- DB 결손 시 자동 생성 0건
- 생성 보기 결정성·무변조성 검증 통과
- 마이그레이션 백업·복구 시험 통과
- `backup/`과 원본 변경 0건
- 검증·레드팀 에이전트 승인

## 12. 중단 조건

- DB와 생성 문서의 양방향 동기화가 필요함
- 두 번째 수동 상태 파일이 필요함
- 마이그레이션 전 안전한 백업을 만들 수 없음
- 실제 사용자 작업 DB를 시험 대상으로 사용해야 함
- 기술 테스트로 사람 승인 자동 생성 경로가 생김
- 동시성 실패를 단순 재시도로 숨김

## 13. 롤백

- 코드 롤백과 작업 DB 롤백을 분리한다.
- 스키마 변경 전 일관된 DB 백업을 만든다.
- 마이그레이션 실패 시 신규 writer를 비활성화하고 이전 DB를 복원한다.
- 생성 JSON·Markdown은 정본에서 다시 만들며 수동 병합하지 않는다.
- 실제 작업 DB를 사용자 승인 없이 삭제하거나 덮어쓰지 않는다.
- 상태 모델 실패 시 단계 02 마지막 통과 지점으로 돌아가며 구체계는 수정하지 않는다.
