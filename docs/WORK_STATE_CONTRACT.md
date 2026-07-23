# 작업 기록·현재 상태 계약

- 목적: 사용자 요청, 승인·제외 범위, 작업 사건과 개별 작업의 현재 상태를 채팅 기억과 독립적으로 재구성한다.
- 읽는 시점: 작업 단위를 시작·전이·재개하거나 `SESSION_HANDOFF.md`에 활성 work 포인터를 갱신할 때.
- 책임: `work_events`가 작업 사건의 추가 전용 정본, `work_state`가 복구 가능한 현재 작업 snapshot, `SESSION_HANDOFF.md`가 프로젝트 전체 현재 단계·첫 다음 행동 정본이다.
- 상태: Stage 04 활성 계약.
- 선행 계약: [공통 기록 I/O 계약](RECORD_IO_CONTRACT.md).

## 정본 분리

| 정보 | 정본 | 파생·연결 |
|---|---|---|
| 프로젝트 전체 현재 단계·첫 다음 행동 | `SESSION_HANDOFF.md` | 활성 work ID·snapshot hash만 연결 |
| 작업 요청·상태 전이 사건 | `data/events/work_events.jsonl` | 한 사건 한 common-record v1 줄 |
| 개별 작업 현재 상태 | `data/records/<work_id>.json`의 `work_state` | event replay로 삭제 후 재생성 가능 |
| 장기 지식 | 아직 없음 | 작업 경험은 Stage 05 승인 전 자동 승격 금지 |

핸드오프와 work snapshot이 같은 프로젝트 상태 본문을 각각 소유하지 않는다. 핸드오프는 활성 작업을 식별하고, 작업 요청·진행·실패·근거는 구조화 기록을 가리킨다.

## 작업 요청

하나의 work는 사용자가 원하는 하나의 검증 가능한 결과 단위다. 첫 `requested` event만 다음 필드를 소유하며 이후 event에서 변경할 수 없다.

- `desired_outcome`
- `authorized_actions`
- `excluded_scope`
- `input_refs`
- `protection_boundaries`
- `required_decisions`
- `verification_levels`

보호 데이터 원문, 전체 명령 출력, 채팅 전문은 저장하지 않고 승인된 참조만 기록한다.

## 상태와 전이

| 현재 | 허용 다음 상태 |
|---|---|
| `requested` | `in_progress`, `failed`, `blocked` |
| `in_progress` | `in_progress` 진행 체크포인트, `completed`, `failed`, `blocked` |
| `failed` | `in_progress`, `blocked` |
| `blocked` | `in_progress`, `failed` |
| `completed` | 없음 |

- `blocked`는 blocker가 최소 1개 있어야 한다.
- `completed`는 `next_action`이 없어야 한다.
- `in_progress → in_progress`는 완료 항목·근거·첫 다음 행동을 갱신하는 성공 체크포인트에만 사용한다.
- event 시각은 현재 snapshot 시각보다 이를 수 없다.
- 기대 snapshot `content_hash`가 다르면 event를 append하지 않는다.
- `rejected` outcome은 상태를 바꾸지 않으며 거부 사실만 남긴다.
- 완료는 사용자 확인 또는 현재 단계 성공 게이트에 의해 권한을 받은 actor만 기록한다.

## event와 snapshot 복구

1. 전이 전 기대 snapshot hash와 허용 전이를 검사한다.
2. `work_events`에 사건을 원자 append한다.
3. 해당 work의 사건을 처음부터 replay해 bounded snapshot을 만든다.
4. snapshot 쓰기가 실패해도 event는 보존하고 `projection_pending` 오류를 반환한다.
5. `work-rebuild`가 event 정본에서 snapshot을 복구한다.

snapshot에는 요청, 현재 status, 중복 제거된 완료 항목·관련 ID·근거 참조, 현재 blocker, 첫 다음 행동, 마지막 event ID만 둔다. 과거 event 본문과 로그를 누적 복사하지 않는다.

## 승인 진입점

- Library: `file_data.WorkStateService`
- CLI: `work-create`, `work-show`, `work-transition`, `work-rebuild`
- 구조 계약: `schemas/work-request-payload-v1.schema.json`, `schemas/work-event-payload-v1.schema.json`, `schemas/work-state-payload-v1.schema.json`

PowerShell에서는 요청 JSON을 UTF-8 stdin으로 보내고 `work-create --request-stdin`을 사용한다. `--request-json`과 `--request-stdin`은 상호 배타적이다.

직접 event 줄이나 snapshot을 편집하는 것은 승인된 경로가 아니다.

## 세션 독립 재개

새 세션은 startup 3문서를 읽은 뒤 핸드오프의 활성 work ID로 `work-show`를 실행한다. 다음을 확인할 수 있어야 한다.

- 사용자가 원하는 결과와 승인·제외 범위
- 현재 작업 상태와 검증된 완료 항목
- 차단 요소와 첫 다음 행동
- 관련 기록 ID와 근거 위치

동적 Git 상태와 파일 개수는 snapshot에 고정 저장하지 않고 필요할 때 다시 조회한다.

## 문서 소유 파생 artifact

아래 세 block이 legacy read 호환용 work request·event·snapshot schema의 exact 정본이다.

<!-- project-artifact:v1 path=schemas/work-request-payload-v1.schema.json verify=json-semantic -->
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:kim-silver-youtube:schema:work-request-payload:v1","title":"Work Request Payload v1","type":"object","additionalProperties":false,"required":["desired_outcome","authorized_actions","excluded_scope","input_refs","protection_boundaries","required_decisions","verification_levels"],"properties":{"desired_outcome":{"type":"string","minLength":1},"authorized_actions":{"type":"array","items":{"type":"string","minLength":1}},"excluded_scope":{"type":"array","items":{"type":"string","minLength":1}},"input_refs":{"type":"array","items":{"type":"string","minLength":1}},"protection_boundaries":{"type":"array","items":{"type":"string","minLength":1}},"required_decisions":{"type":"array","items":{"type":"string","minLength":1}},"verification_levels":{"type":"array","items":{"type":"string","minLength":1}}}}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=schemas/work-event-payload-v1.schema.json verify=json-semantic -->
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:kim-silver-youtube:schema:work-event-payload:v1","title":"Work Event Payload v1","type":"object","additionalProperties":false,"required":["work_id","actor","action","outcome","from_status","to_status","request","completed_items","blockers","next_action","related_record_ids","evidence_refs"],"properties":{"work_id":{"type":"string","format":"uuid"},"actor":{"type":"string","minLength":1},"action":{"type":"string","minLength":1},"outcome":{"enum":["success","failure","blocked","rejected"]},"from_status":{"type":["string","null"],"enum":["requested","in_progress","completed","failed","blocked",null]},"to_status":{"type":["string","null"],"enum":["requested","in_progress","completed","failed","blocked",null]},"request":{"oneOf":[{"$ref":"work-request-payload-v1.schema.json"},{"type":"null"}]},"completed_items":{"type":"array","items":{"type":"string","minLength":1}},"blockers":{"type":"array","items":{"type":"string","minLength":1}},"next_action":{"type":["string","null"]},"related_record_ids":{"type":"array","items":{"type":"string","minLength":1}},"evidence_refs":{"type":"array","items":{"type":"string","minLength":1}}}}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=schemas/work-state-payload-v1.schema.json verify=json-semantic -->
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:kim-silver-youtube:schema:work-state-payload:v1","title":"Work State Payload v1","type":"object","additionalProperties":false,"required":["work_id","request","status","completed_items","blockers","next_action","related_record_ids","evidence_refs","last_event_id"],"properties":{"work_id":{"type":"string","format":"uuid"},"request":{"$ref":"work-request-payload-v1.schema.json"},"status":{"enum":["requested","in_progress","completed","failed","blocked"]},"completed_items":{"type":"array","items":{"type":"string","minLength":1}},"blockers":{"type":"array","items":{"type":"string","minLength":1}},"next_action":{"type":["string","null"]},"related_record_ids":{"type":"array","items":{"type":"string","minLength":1}},"evidence_refs":{"type":"array","items":{"type":"string","minLength":1}},"last_event_id":{"type":"string","format":"uuid"}}}
```
<!-- /project-artifact -->
