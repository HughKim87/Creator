# 지식 유형·실패 정본 직접 재사용 계약

- 목적: 작업 기록과 분리된 장기 재사용 데이터를 출처·단일 지식 주장·결정 record로 관리하고, 해결 실패는 canonical Markdown을 저장 projection 없이 직접 검증·재사용한다.
- 읽는 시점: source·knowledge·decision record를 생성·조회·검증하거나 해결 실패 문서를 기록·검색할 때.
- 책임: `src/file_data/knowledge.py`가 의미 검증과 참조 무결성, `schemas/*-payload-v1.schema.json`이 저장 record 구조, `failures/*.md`가 실패 사례의 사람·기계 공통 정본을 소유한다.
- 상태: 활성 계약.
- 선행 계약: [공통 기록 I/O](RECORD_IO_CONTRACT.md), [작업 기록·현재 상태](WORK_STATE_CONTRACT.md).

## 유형과 정본 책임

| record type | 소유 정보 | 소유하지 않는 정보 |
|---|---|---|
| `source` | 출처 종류·위치·관찰 시각·확인 상태·증거 역할·버전 또는 hash | 원문 전체, 보호 데이터 사본, 신뢰 점수 |
| `knowledge` | 한 줄의 주요 주장 하나·분류·적용 범위·source 참조·검증 상태와 주체 | 작업 전문, 복수 주장, 태그·검색 점수·검토 일정 |
| `decision` | 문제·요구조건·검토 선택지·선택·이유·영향·source·승인·결정 시각 | 현재 실행 상태, 승인되지 않은 대리 결정 |
| transient failure view | `failures/*.md` 정본을 실행 시 구조적으로 읽은 비저장 view | 별도 정본, lifecycle 대상, 장기 저장 projection |

작업 요청·event·snapshot은 장기 지식 record로 복제하지 않는다. 일반 지식은 명시적 create 명령에서만 생성되며 자동 추출·승격은 없다. 실패 view는 정본을 읽을 때만 메모리에서 만들어지고 저장하지 않는다.

## 05A 출처 기록

허용 종류는 `local_document`, `local_data`, `command_result`, `web_page`, `user_statement`다. 증거 역할은 `primary`, `supporting`, `contextual`, 확인 상태는 `observed`, `verified`, `unavailable`이다.

- 로컬 출처는 정규화된 프로젝트 상대 경로만 허용하고 `backup`, `inputs`, `outputs`, `.git`, `.obsidian`을 거부한다.
- 로컬 파일 생성 시 실제 bytes의 SHA-256을 계산해 `verified`로 저장한다.
- `source-show`와 `source-list`는 당시 관찰 record를 읽는다. `source-verify`는 현재 bytes를 다시 계산하며 저장 hash와 다르면 `source_integrity`로 실패한다.
- web source는 `http` 또는 `https` locator만 기록한다. 이 계층은 외부 내용을 가져오거나 권위를 자동 판정하지 않는다.
- user statement는 원문을 복사하지 않고 승인된 `request://...` 참조만 기록할 수 있다.

## 05B 지식 항목

분류는 `fact`, `inference`, `procedure`, `constraint`, 상태는 `candidate`, `verified`다.

- `statement`는 줄바꿈 없는 500자 이하 문자열 하나다. 의미상 복수 주장은 사용자 검토에서 분리한다.
- source ID는 최소 한 개이며 모두 존재하는 `source` record여야 한다.
- `unavailable` source는 지식 생성에 사용할 수 없다.
- `candidate`는 `verified_by`를 가질 수 없고 `verified`는 검증 주체가 필수다.
- 참조한 로컬 source가 바뀌어도 당시 지식 record 조회는 보존되지만 `source-verify`는 실패한다. 현재도 유효한지의 갱신·대체 판정은 수명주기 계약이 소유한다.

## 05C 결정 기록

결정은 최소 두 선택지를 검토하고 `selected_option`이 그 label 중 하나여야 한다. 요구조건·영향·source가 각각 최소 하나 필요하다.

- 승인 종류는 `user`, `standing_policy`, `agent_in_scope`다.
- `requires_user_approval=true`이면 `user` 또는 `standing_policy`만 허용한다.
- `approved_by`와 `decided_at`을 항상 기록한다.
- 결정 시각은 record 생성 시각보다 미래일 수 없다.
- 설치·외부 게시·보호 데이터·삭제·이동·비용·실질적 범위 확대는 기존 상시 안전 경계를 그대로 따른다.

## 해결 실패 정본 직접 재사용

`failures/*.md`가 해결 실패 사례 본문과 현재 유효성의 유일한 정본이다. parser는 다음 필드를 실행 시 읽어 transient view를 만들며 파일로 저장하지 않는다.

- 제목, 정본 문서 경로와 SHA-256
- 증상, 적용 범위, 확인된 원인
- 해결, 검증, 재사용 규칙
- 정본 문서 자체의 해결 상태

검증은 `failures/README.md`를 제외하고 상태에 `해결`이 있으며 `증상`, `확인된 원인`, `해결과 검증`, `재사용 규칙` 절이 모두 있는 사례만 받는다. `해결과 검증` 절의 첫 목록 항목을 해결, 나머지를 검증 근거로 읽는다. strict UTF-8, NUL 0, SHA-256과 필수 의미를 매번 정본 bytes에서 계산한다.

정본 Markdown이 갱신되면 다음 읽기부터 새 내용이 즉시 사용된다. 별도 source·projection·lifecycle snapshot을 갱신하지 않는다. 파일 이력은 Git이, 재발·해결 이력은 Markdown 본문이 보존한다.

외부에서 이전 `failure_knowledge`·실패 전용 source·lifecycle record를 가져온 경우에만 명시 direct read 호환을 제공한다. 현재 프로젝트는 이를 저장하지 않으며 기본 목록·검색·maintenance current 판정에도 사용하지 않는다.

## 승인된 진입점

- Library: `file_data.KnowledgeService`
- Source CLI: `source-create`, `source-show`, `source-list`, `source-verify`
- Knowledge CLI: `knowledge-create`, `knowledge-show`, `knowledge-list`
- Decision CLI: `decision-create`, `decision-show`, `decision-list`
- Failure CLI: `failure-validate`, `failure-list`
- Legacy compatibility: `failure-show --id`, 비저장 검증 alias `failure-import`

복합 decision payload는 PowerShell에서 UTF-8 stdin과 `--payload-stdin`을 사용한다. 모든 record는 common-record v1 외피와 `data/records/<id>.json` 단일 주소를 재사용한다.

## 구조 계약

- `schemas/source-payload-v1.schema.json`
- `schemas/knowledge-payload-v1.schema.json`
- `schemas/decision-payload-v1.schema.json`
- `schemas/failure-knowledge-payload-v1.schema.json` — legacy stored projection read compatibility

Python 검증기가 구조 스키마보다 강한 교차 필드·참조·hash 검증을 수행한다. 테스트는 두 필드 집합과 enum이 일치하는지 확인한다.

## 연계·제외

- source·knowledge·decision record 검토·대체·폐기·충돌·사건 기반 검토 트리거는 [지식 수명주기 계약](KNOWLEDGE_LIFECYCLE_CONTRACT.md)이 소유한다.
- 검색·순위·관계 탐색·컨텍스트 조립은 [컨텍스트 계약](CONTEXT_PACKAGE_CONTRACT.md)이 소유한다.
- 실패 정본 직접 검증과 중복 제목 탐지는 [유지보수 계약](MAINTENANCE_AUTOMATION_CONTRACT.md)이 소유한다.
- 도메인 전용 필드와 영상 제작 연결은 도메인 계약에서만 정의한다.

## 문서 소유 파생 artifact

아래 block이 legacy source·knowledge·decision·failure projection schema의 exact 정본이다. 현재 failure 지식은 위 Markdown direct parser 계약을 사용한다.

<!-- project-artifact:v1 path=schemas/source-payload-v1.schema.json verify=json-semantic -->
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:kim-silver-youtube:schema:source-payload:v1","title":"Source Payload v1","type":"object","additionalProperties":false,"required":["source_kind","locator","observed_at","verification_status","evidence_role","version_or_hash"],"properties":{"source_kind":{"enum":["local_document","local_data","command_result","web_page","user_statement"]},"locator":{"type":"string","minLength":1},"observed_at":{"type":"string","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"},"verification_status":{"enum":["observed","verified","unavailable"]},"evidence_role":{"enum":["primary","supporting","contextual"]},"version_or_hash":{"type":["string","null"]}}}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=schemas/knowledge-payload-v1.schema.json verify=json-semantic -->
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:kim-silver-youtube:schema:knowledge-payload:v1","title":"Knowledge Payload v1","type":"object","additionalProperties":false,"required":["statement","classification","scope","source_ids","verification_status","verified_by"],"properties":{"statement":{"type":"string","minLength":1,"maxLength":500,"pattern":"^[^\\r\\n]+$"},"classification":{"enum":["fact","inference","procedure","constraint"]},"scope":{"type":"string","minLength":1},"source_ids":{"type":"array","minItems":1,"uniqueItems":true,"items":{"type":"string","format":"uuid"}},"verification_status":{"enum":["candidate","verified"]},"verified_by":{"type":["string","null"]}}}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=schemas/decision-payload-v1.schema.json verify=json-semantic -->
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:kim-silver-youtube:schema:decision-payload:v1","title":"Decision Payload v1","type":"object","additionalProperties":false,"required":["problem","requirements","options","selected_option","rationale","impacts","source_ids","requires_user_approval","approval_kind","approved_by","decided_at"],"properties":{"problem":{"type":"string","minLength":1},"requirements":{"type":"array","minItems":1,"uniqueItems":true,"items":{"type":"string","minLength":1}},"options":{"type":"array","minItems":2,"items":{"type":"object","additionalProperties":false,"required":["label","impact"],"properties":{"label":{"type":"string","minLength":1},"impact":{"type":"string","minLength":1}}}},"selected_option":{"type":"string","minLength":1},"rationale":{"type":"string","minLength":1},"impacts":{"type":"array","minItems":1,"uniqueItems":true,"items":{"type":"string","minLength":1}},"source_ids":{"type":"array","minItems":1,"uniqueItems":true,"items":{"type":"string","format":"uuid"}},"requires_user_approval":{"type":"boolean"},"approval_kind":{"enum":["user","standing_policy","agent_in_scope"]},"approved_by":{"type":"string","minLength":1},"decided_at":{"type":"string","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"}}}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=schemas/failure-knowledge-payload-v1.schema.json verify=json-semantic -->
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:kim-silver-youtube:schema:failure-knowledge-payload:v1","title":"Failure Knowledge Projection Payload v1","type":"object","additionalProperties":false,"required":["title","canonical_doc_ref","document_hash","source_id","symptom","conditions","confirmed_cause","resolution","verification","prevention","projection_status","projected_by","projected_at"],"properties":{"title":{"type":"string","minLength":1},"canonical_doc_ref":{"type":"string","pattern":"^failures/[^/]+\\.md$"},"document_hash":{"type":"string","pattern":"^sha256:[0-9a-f]{64}$"},"source_id":{"type":"string","format":"uuid"},"symptom":{"type":"string","minLength":1},"conditions":{"type":"array","minItems":1,"uniqueItems":true,"items":{"type":"string","minLength":1}},"confirmed_cause":{"type":"string","minLength":1},"resolution":{"type":"array","minItems":1,"uniqueItems":true,"items":{"type":"string","minLength":1}},"verification":{"type":"array","minItems":1,"uniqueItems":true,"items":{"type":"string","minLength":1}},"prevention":{"type":"array","minItems":1,"uniqueItems":true,"items":{"type":"string","minLength":1}},"projection_status":{"const":"resolved"},"projected_by":{"type":"string","minLength":1},"projected_at":{"type":"string","pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"}}}
```
<!-- /project-artifact -->
