# 유튜브 촬영 전 근거 패키지 계약

- 목적: 첫 유튜브 도메인 작업으로 명시된 영상 목표와 current 근거를 연결해 촬영 전 검토용 비영구 evidence pack을 만든다.
- 읽는 시점: 유튜브 영상의 근거 패키지를 만들거나 도메인 adapter의 입력·결과·승인 경계를 검토할 때.
- 책임: `youtube_domain.YouTubeEvidenceService`가 도메인 입력·절감 지표를 검증하고 Core 공개 `shared_data` v1이 근거 선택·경계·fingerprint를 소유한다.
- 상태: 활성 도메인 계약.
- 관련 권위: `PROJECT_RULES.md`가 선택한 공통 context·work-state interface와 이 도메인 계약.

## 1. 선택한 도메인과 첫 작업

사용자의 권장안 자동 선택 승인과 활성 요구사항의 “기반 이후 첫 소비자는 영상 제작” 근거에 따라 첫 도메인을 유튜브 제작으로 정했다. 첫 작업은 전체 제작 파이프라인이 아니라 **촬영 전 근거 패키지 생성** 하나다.

이 작업은 작업 제목·대상 시청자·설명 목표와 명시 evidence를 입력받아 current 문서·record만 선택하고, 출처 상태·제외 이유·문자·byte·절감률·fingerprint를 포함한 패키지를 반환한다. 대본·썸네일·촬영·편집·게시를 수행하지 않는다.

## 2. 책임 경계

| 정보·행동 | 소유자 | 경계 |
|---|---|---|
| 작업 제목·시청자·목표·evidence 선택 | 호출 요청 | 서비스가 정규화하지만 자동 보강·저장하지 않음 |
| record·lifecycle·context 선택 | Core 공개 `shared_data` v1 | 도메인 필드를 공통 record schema에 추가하지 않음 |
| 유튜브 작업 의미·승인 gate·pack fingerprint | `youtube_domain` | 공통 기반을 수정하거나 domain 결과를 current 지식으로 만들지 않음 |
| 창작 방향·작업 제목 승인 | 사용자 | 결과는 항상 `review_required`; adapter가 승인하지 않음 |
| 사용자 원본 | `inputs/` 보호 경계 | 이번 작업에서 열거·열람·이동·저장하지 않음 |
| 파생 evidence pack | 호출 stdout | 기본 비영구. `outputs/` 저장은 정확한 대상·목적의 별도 사용자 승인 필요 |
| 검증 결과 | 실행 응답과 Git | pack 본문을 장기 보고서로 복제하지 않음 |

## 3. 요청 계약

요청은 [youtube-evidence-request-v1](../../../schemas/youtube-evidence-request-v1.schema.json)을 따르며 다음 필드만 허용한다.

- `video`: lowercase ASCII slug ID, 작업 제목, 대상 시청자, 설명 목표
- `documents`: `ref`, 선택 이유, 필요하면 같은 문서 안 `project-data:v1`의 `data_key`를 지정하는 기본 current 목록
- `records`: `shared_data` v1 record UUID와 선택 이유. lifecycle `current`가 아니면 부분 성공 없이 실패
- `search`: 선택적 current 문자열 후보. 사용하지 않으면 `null`
- `char_limit`: 1~12,000 Unicode 문자
- `baseline_characters`: 비교 기준선의 양의 Unicode 문자 수

직접 evidence나 검색 중 하나는 반드시 있어야 한다. 중복 직접 선택, 알 수 없는 필드, 빈 문자열, 상한 초과는 입력 오류다. 보호 경로는 공통 컨텍스트 경계에서 읽기 전에 거부한다.

## 4. 결과 계약

결과는 [youtube-evidence-pack-v1](../../../schemas/youtube-evidence-pack-v1.schema.json)을 따르는 비영구 JSON이다.

- `domain: youtube`, `task: preproduction_evidence_pack`
- 정규화한 `video`
- 사용자 소유 `approval_gate`와 `review_required` 상태
- 공통 `context_package` 전체와 그 fingerprint
- 요청 baseline과 Core 선택 문자 수로 계산한 도메인 `selection_metrics`
- 도메인 pack 전체의 별도 SHA-256 fingerprint

요청한 direct record가 current 선택 결과에 없으면 부분 pack을 성공으로 반환하지 않는다. 동일한 정본·요청에서 byte가 같은 JSON과 같은 두 fingerprint를 반환해야 한다.

## 5. 작업 흐름

1. 명시 JSON과 허용 필드·길이·중복·evidence 존재를 검증한다.
2. 목적·문서·선택 `data_key`·record ID·검색·문자 상한을 공개 `shared_data context.build` 요청으로 변환한다.
3. 공통 기반이 보호 경계, current 상태, source trace, 크기와 제외를 검증한다.
4. 모든 direct record가 실제 selected current인지 다시 확인하고 baseline 대비 절감 지표를 도메인 결과로 계산한다.
5. 사용자 소유 `review_required` gate와 도메인 fingerprint를 추가한다.
6. stdout으로만 반환하고 package·영상 원본·도메인 상태를 저장하지 않는다.
7. 실제 실행의 fingerprint와 측정값은 현재 작업에 필요할 때만 checkpoint에 연결한다.

## 6. 실행점과 검증 수준

```powershell
$request = Get-Content -LiteralPath 'extension/examples/youtube/foundation-evidence.request.json' -Raw -Encoding UTF8
$request | python -m youtube_domain --root . evidence-pack --request-stdin
```

PowerShell에서 native stdin으로 한글 JSON을 보낼 때는 `$OutputEncoding`과 `PYTHONUTF8=1`을 UTF-8로 설정한다.

| 수준 | 이번 검증 | 판정 경계 |
|---|---|---|
| 구조 | runtime 필드와 JSON schema, 문서 링크, 공통/도메인 책임 | 자동 검증 |
| 도구 | library·CLI 정상/실패·결정론·비영구성 | 자동 검증 |
| 도메인 결과 | 명시 예시에서 current evidence·source trace·비용·approval gate 확인 | 실제 로컬 실행 |
| 앱 | 이 첫 작업은 외부 앱이 필요하지 않음 | `해당 없음`; 앱 검증을 통과로 가장하지 않음 |
| 사용자 | 작업 제목과 창작 방향 승인 | `review_required`; 이번 evidence 생성 완료와 구분 |

## 7. 실패와 복구

- 입력·보호 경계·noncurrent direct record·크기 초과는 구조화 오류와 비성공 exit status로 반환한다.
- 오류 시 pack이나 event를 부분 저장하지 않는다.
- noncurrent record는 current replacement를 확인해 새 요청으로 다시 실행한다.
- char limit 초과는 필수 evidence 범위를 줄이거나 사용자와 상한을 재결정한다. 조용히 자르지 않는다.
- 외부 앱이나 사용자 원본이 필요한 후속 작업은 이 adapter에 얹지 않고 별도 승인된 도메인 작업으로 정의한다.

## 8. 지식 환류

실제 결과에서 재사용 가치가 확인된 절차만 `youtube:evidence-pack` 범위 knowledge candidate로 만들 수 있다. candidate는 자동 current 승격하지 않으며 다음 작업의 기본 context 검색에도 포함되지 않는다. 사용자 또는 standing policy가 재사용 필요를 승인한 경우에만 lifecycle 전이를 별도로 수행한다.

<!-- project-data:v1 kind=knowledge key=youtube-evidence-pack-review-required -->
```json
{
  "key": "youtube-evidence-pack-review-required",
  "kind": "knowledge",
  "payload": {
    "statement": "유튜브 촬영 전 근거 패키지는 current 근거만 선택하고 작업 제목과 창작 방향을 사용자 review_required로 남긴다.",
    "classification": "procedure",
    "scope": "youtube:evidence-pack",
    "verification_status": "verified",
    "verified_by": "agent:document-cleanup",
    "replaces_legacy_ids": []
  },
  "source_refs": [
    "extension/docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md#8-지식-환류"
  ],
  "status": "candidate"
}
```
<!-- /project-data -->

## 9. 제외와 후속

- 전체 영상 제작 워크플로와 과거 구현 복원
- 제목·창작 방향 자동 승인
- 대본·자막·편집 자료·썸네일 생성
- YouTube Studio·Premiere·외부 API 호출
- 원본·파생 결과 자동 저장
- 공통 record schema의 유튜브 필드 추가
- 도메인 경험의 전역 지식 자동 승격

## 10. 문서 소유 파생 artifact

아래 block이 YouTube request·pack schema와 보호 데이터 없는 기본 문서 참조 example의 exact 정본이다.

<!-- project-artifact:v1 path=extension/schemas/youtube-evidence-request-v1.schema.json verify=json-semantic -->
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"project://extension/schemas/youtube-evidence-request-v1.schema.json","title":"YouTube pre-production evidence request v1","type":"object","additionalProperties":false,"required":["video","documents","records","search","char_limit","baseline_characters"],"properties":{"video":{"type":"object","additionalProperties":false,"required":["id","working_title","audience","goal"],"properties":{"id":{"type":"string","pattern":"^[a-z0-9]+(?:-[a-z0-9]+)*$","maxLength":80},"working_title":{"type":"string","minLength":1,"maxLength":200},"audience":{"type":"string","minLength":1,"maxLength":500},"goal":{"type":"string","minLength":1,"maxLength":1000}}},"documents":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["ref","reason"],"properties":{"ref":{"type":"string","minLength":1,"maxLength":200},"data_key":{"type":"string","pattern":"^[a-z0-9]+(?:-[a-z0-9]+)*$","maxLength":100},"reason":{"type":"string","minLength":1,"maxLength":500}}}},"records":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["id","reason"],"properties":{"id":{"type":"string","format":"uuid","maxLength":200},"reason":{"type":"string","minLength":1,"maxLength":500}}}},"search":{"type":["string","null"]},"char_limit":{"type":"integer","minimum":1,"maximum":12000},"baseline_characters":{"type":"integer","minimum":1}}}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=extension/schemas/youtube-evidence-pack-v1.schema.json verify=json-semantic -->
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"project://extension/schemas/youtube-evidence-pack-v1.schema.json","title":"YouTube pre-production evidence pack v1","type":"object","additionalProperties":false,"required":["pack_version","domain","task","video","approval_gate","context_package","selection_metrics","fingerprint"],"properties":{"pack_version":{"const":1},"domain":{"const":"youtube"},"task":{"const":"preproduction_evidence_pack"},"video":{"type":"object","additionalProperties":false,"required":["id","working_title","audience","goal"],"properties":{"id":{"type":"string","pattern":"^[a-z0-9]+(?:-[a-z0-9]+)*$","maxLength":80},"working_title":{"type":"string","minLength":1,"maxLength":200},"audience":{"type":"string","minLength":1,"maxLength":500},"goal":{"type":"string","minLength":1,"maxLength":1000}}},"approval_gate":{"type":"object","additionalProperties":false,"required":["status","owner","decision","reason"],"properties":{"status":{"const":"review_required"},"owner":{"const":"user"},"decision":{"const":"working_title_and_creative_direction"},"reason":{"type":"string","minLength":1}}},"context_package":{"$ref":"../../core/experimental/shared_data/schemas/context-package-v1.schema.json"},"selection_metrics":{"type":"object","additionalProperties":false,"required":["baseline_characters","selected_characters","reduction_characters","reduction_ratio"],"properties":{"baseline_characters":{"type":"integer","minimum":1},"selected_characters":{"type":"integer","minimum":0},"reduction_characters":{"type":"integer","minimum":0},"reduction_ratio":{"type":"number","minimum":0,"maximum":1}}},"fingerprint":{"type":"string","pattern":"^sha256:[0-9a-f]{64}$"}}}
```
<!-- /project-artifact -->

<!-- project-artifact:v1 path=extension/examples/youtube/foundation-evidence.request.json verify=json-semantic -->
```json
{"baseline_characters":315497,"char_limit":12000,"documents":[{"reason":"선택적 근거 구성의 현재 계약","ref":"core/experimental/shared_data/EVIDENCE_CONTEXT_CONTRACT.md"}],"records":[],"search":null,"video":{"audience":"반복 제작에서 AI 작업 기억의 비용을 줄이고 싶은 1인 크리에이터","goal":"전체 문서를 매번 읽지 않고 current 근거만 선택해 재현 가능한 작업 문맥을 만드는 방식을 설명한다.","id":"foundation-context","working_title":"AI 작업 기억을 가볍게 만드는 선택적 컨텍스트"}}
```
<!-- /project-artifact -->

후속 작업은 사용자의 별도 선택으로 새 범위를 정의한다.
