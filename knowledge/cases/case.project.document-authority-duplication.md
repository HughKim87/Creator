# 사례: 중복 문서의 권위 충돌과 반복 생성

- 사례 ID: `case.project.document-authority-duplication`
- 스키마 버전: `manual-case-1.0.0` — JSON Schema와 자동 validator가 없는 수동 bootstrap 형식
- 종류: 문제·실패·해결 사례
- 상태: `resolved`
- 검색 적격성: `active` — 문서 생성, 보고, 권위, 보존 또는 컨텍스트 중복 작업에 한해 직접 라우팅
- 신뢰도: `high`
- 신뢰도 근거: 사용자가 증상을 직접 보고했고, 중복 문서의 원본·현재 파일·Git 객체·변경 결과를 저장소에서 구조적으로 검증했다.
- 작성일: `2026-07-20T22:50:40+09:00`
- 수정일: `2026-07-20T23:16:47+09:00`
- 작성자: Codex project agent
- 검증자: Codex project agent — structural validation; 사용자는 문제와 기록 필요성을 확인했으며 사례 본문의 최종 승인은 아직 별도로 표시하지 않았다.
- 언어: 한국어
- 유효 범위: 이 프로젝트의 maintained document 생성·수정·검증·보존 작업
- 마지막 확인: `2026-07-20T23:16:47+09:00`
- 검토 정책: `event_driven`
- 정기 검토 기한: `review_due_at=null`
- 검토 기한 근거: 사용자가 2026-07-20에 정기 기한을 두지 않고 필요할 때 즉시 검토하도록 명시했다.
- 목적: 같은 주제의 보고서가 단계마다 새 완결형 문서로 반복 생성되어 권위 충돌과 컨텍스트 낭비가 생긴 문제, 원인, 해결, 검증과 재발 방지 규칙을 누적 가능한 사례로 보존한다.
- 사용 시점: 새 문서·보고서·설계 제안을 만들기 전, 현재 제안이 둘 이상이거나 과거 보고서가 기본 컨텍스트에 포함되는 문제가 발견됐을 때, 또는 사용자가 이 사례의 재검토를 요청할 때 사용한다.
- 작성·수정 주체: 프로젝트 에이전트가 저장소 증거로 갱신한다. 상태·정책·검토 방식의 중요한 변경은 사용자가 승인한다.
- 저장 위치: `knowledge/cases/case.project.document-authority-duplication.md`.
- 연결 관계: [프로젝트 규칙](../../PROJECT_RULES.md), [문서 생성 게이트](../../docs/agent/WORKFLOW.md#document-creation-gate), [문서 지도](../../docs/agent/DOCUMENT_MAP.md), [검색 계약](../../docs/agent/CONTEXT_RETRIEVAL.md), [유지보수 계약](../../docs/agent/KNOWLEDGE_MAINTENANCE.md), [R-1.1 현재 제안](../../docs/reports/2026-07-20_R-1.1_지식_시스템_설계_보정.md), [현재 인수인계](../../SESSION_HANDOFF.md)에 연결된다.

## case.project.document-authority-duplication

아래 JSON은 R-2B부터 resolver와 schema validator가 사용하는 정식 레코드다. 본문의 수동 bootstrap 기록과 revision history는 증거 보존을 위해 유지한다.

```json
{
  "schema_version": "1.0.0",
  "record_kind": "case",
  "case_id": "case.project.document-authority-duplication",
  "title": "중복 문서의 권위 충돌과 반복 생성",
  "status": "resolved",
  "symptom": {
    "state": "confirmed",
    "summary": "같은 지식 시스템 설계가 단계별 완결형 보고서로 반복 생성되어 현재 권위와 수치가 충돌했다.",
    "evidence": [
      {"source_id": "source.repo.r1.1", "locator": "§1 사례 요약과 §2 사용자 관찰"},
      {"source_id": "source.history.overview", "locator": "문서 중심 프로젝트 변천사와 반복 실패 요약"}
    ]
  },
  "resolution": {
    "state": "resolved",
    "summary": "단일 owner, 문서 생성 게이트, authority/preservation/default-context 상태 분리와 exact routing을 적용했다.",
    "evidence": [
      {"source_id": "source.repo.project-rules", "locator": "1. Authority and scope"},
      {"source_id": "source.repo.workflow", "locator": "Document creation gate"}
    ]
  },
  "confidence": "high",
  "source_refs": [
    {"source_id": "source.repo.r1.1", "locator": "§11과 승인 경계"},
    {"source_id": "source.repo.project-rules", "locator": "1. Authority and scope"},
    {"source_id": "source.repo.workflow", "locator": "Document creation gate"},
    {"source_id": "source.history.overview", "locator": "프로젝트 전체 변천사 요약"}
  ],
  "relation_ids": ["relation.case.document-authority.resolved-by.knowledge.single-owner"],
  "confirmed_at": "2026-07-20T22:50:40+09:00",
  "resolved_at": "2026-07-20T23:16:47+09:00",
  "last_verified_at": "2026-07-21",
  "review_policy": "event_driven",
  "review_due_at": null,
  "review_triggers": [
    "같은 주제의 current proposal이 둘 이상 발견됨",
    "새 maintained document에 고유 owner가 없음",
    "대체된 보고서가 active instruction으로 선택됨"
  ],
  "retrieval_eligible": true,
  "task_tags": ["case", "documentation", "authority", "failure", "resolution"]
}
```

## 1. 사례 요약

`F` 같은 지식 시스템 설계를 다루는 최종 교차검증, R-1, 착수 전 의도 검증과 R-1.1 문서가 각각 272줄, 648줄, 444줄, 596줄의 완결형 보고서로 존재했다.

`F` R-1은 11개 상시 규칙과 18개 조건부 규칙을 제안했고 R-1.1은 이를 8개와 21개로 보정했다. 두 제안이 전체 설계와 다음 단계 범위를 각각 설명하면서 현재 권위가 어느 문서에 있는지 혼동할 수 있었다.

`I` 문장 자체의 완전 일치보다 같은 책임을 새 표현으로 반복한 의미 중복이 핵심 문제였다. 이 상태는 검색 결과 중복, 컨텍스트 증가, 오래된 제안의 현재 지시 오인 가능성을 만들었다.

## 2. 사용자 관찰과 영향

### 사용자 관찰

- “왜 자꾸 같은 문서 내용이 반복되면서 새로운 파일이 생성되는거 같지?”
- “중복 문서의 권위와 보존 상태를 정리하는 문서 구조 정상화 진행해”
- “같은문제가 생기지 않도록 규칙도 추가해둬야지”

현재 work-event 저장소가 구현되지 않아 위 대화에는 durable event ID가 없다. 이 사례가 원문과 날짜를 보존하는 수동 근거이며, R-2B에서 event/source record로 이관할 때 stable source ID를 부여해야 한다.

### 영향

- 어떤 설계가 현재 제안인지 추가 비교 없이는 판단하기 어려웠다.
- 기본 컨텍스트가 대체된 보고서까지 불러올 가능성이 있었다.
- 동일 내용을 다시 작성하면서 문서 수와 토큰 비용이 증가했다.
- 11/18과 8/21처럼 대체 전후 수치가 함께 노출돼 잘못된 구현 근거가 될 수 있었다.

## 3. 확인된 원인

1. `confirmed` 단계 완료 보고를 새 파일 생성 의무로 과도하게 해석했다.
2. `confirmed` 보고서를 시점 증거이면서 전체 설계 소유자로도 사용해 authority와 evidence 역할을 섞었다.
3. `confirmed` 독립적으로 읽히는 문서를 만들겠다는 이유로 기존 owner를 링크하지 않고 전체 배경과 설계를 다시 작성했다.
4. `confirmed` 단일 owner 원칙은 있었지만 새 문서 생성 전에 중복·현재 제안 수·Git 보존 가능성을 거부 조건으로 검사하는 실행 게이트가 없었다.

### 배제한 원인

- `rejected` 사용자가 각 단계마다 전체 설계를 새 문서에 반복하라고 요구한 것이 아니다.
- `rejected` 과거 원문을 보존하려면 활성 작업 트리에 전체 복사본이 반드시 필요했던 것이 아니다. Git commit과 blob으로 복원할 수 있었다.

## 4. 적용한 해결

1. [문서 지도](../../docs/agent/DOCUMENT_MAP.md)에 모든 활성 Markdown 문서의 authority state, preservation state와 default-context behavior를 등록했다.
2. R-1과 착수 전 의도 검증의 현재 파일은 보존 표식으로 축약하고 전체 원문은 Git commit·blob·SHA-256으로 보존했다.
3. 정상화 당시 [R-1.1](../../docs/reports/2026-07-20_R-1.1_지식_시스템_설계_보정.md)만 `current-proposal`로 남겼고, 사용자 채택 후에는 이를 R-2A의 `accepted-decision-source`로 전환했다. 현재 이 주제의 pending proposal은 없다.
4. 보고서와 대체된 제안은 startup/default context에서 제외하고 정확한 비교·감사 요청 때만 열도록 했다.
5. [프로젝트 규칙](../../PROJECT_RULES.md)의 기존 단일 owner 규칙을 강화해 단계·버전·에이전트·재검증을 중복 문서 사유로 인정하지 않게 했다.
6. [작업 절차](../../docs/agent/WORKFLOW.md#document-creation-gate)에 문서 생성 게이트와 문서 전용 검증 조건을 추가했다.
7. 이번 사례부터 문제·원인·해결·검증·재발 방지를 독립 case record로 누적한다.

## 5. 검증 결과

| 검증 | 결과 |
|---|---|
| 활성 Markdown 등록 | 정상화 시점 17개 전부 문서 지도 등록 |
| 제안·승인 상태 | 정상화 당시 current proposal은 R-1.1 한 개; 사용자 채택 후 pending proposal 0개, accepted R-2A source 1개 |
| R-1 중복 축약 | 648줄·35,882바이트 → 36줄 보존 표식 |
| 의도 검증 중복 축약 | 444줄·28,292바이트 → 39줄 보존 표식 |
| 원문 복구 | Git blob 두 개 존재, 원래 byte 크기 확인 |
| 링크·형식 | 정상화 후 로컬 링크 170개, UTF-8·NUL·후행 공백 검사 문제 0건 |
| 저장소 경계 | `backup/` 변경 0건, 구현 경로 추가 없음 |
| Git 검사 | `git diff --check` 통과 |

검증 수준은 `structural`이다. 사용자가 문제와 기록 필요성을 직접 확인했지만, 사례 내용 전체를 `user-approved`로 과장하지 않는다.

## 6. 재발 방지 규칙

- 새 단계·버전·에이전트·검증 회차만으로 새 문서를 만들지 않는다.
- 새 문서 생성 전에 기존 owner와 current proposal을 확인한다.
- 동일 주제의 current proposal은 하나만 허용한다.
- 새 파일은 고유 목적, authority class, preservation state, default-context behavior와 기존 문서가 소유할 수 없는 이유를 가져야 한다.
- 시점 보고서는 delta, evidence, validation, unresolved risk와 approval boundary만 기록한다.
- 대체된 전체 원문은 Git으로 보존하고 활성 작업 트리에는 필요한 경우 짧은 marker만 둔다.
- 문서 검증에서 registry 누락, current proposal 중복, Git 보존 식별자와 링크를 검사한다.

## 7. 즉시 검토 trigger

정기 날짜는 설정하지 않는다. 다음 중 하나가 발생하면 이 사례를 즉시 검토한다.

1. 사용자가 이 사례나 문서 중복 문제의 검토를 요청한다.
2. 같은 주제의 `current-proposal`이 둘 이상 발견된다.
3. 고유 owner·문서 지도 등록 없이 새 maintained document가 생성된다.
4. 단계 번호나 에이전트 이름만 다른 완결형 보고서가 생성된다.
5. `PROJECT_RULES.md`, `WORKFLOW.md`, `DOCUMENT_MAP.md`의 문서 권위·생성 규칙이 변경된다.
6. 보존 표식에 기록된 Git commit·blob·SHA-256 중 하나를 확인할 수 없다.
7. 대체된 보고서가 startup 또는 기본 작업 context에 선택된다.

trigger가 발생하면 먼저 상태를 `needs_review`로 바꾸고 원인·영향·해결 유효성을 다시 확인한 뒤, 결과와 revision을 아래 이력에 추가한다.

## 8. 출처와 추적성

| source ID | 종류 | locator | 확인일 | 지원 내용 |
|---|---|---|---|---|
| `src.user.session.20260720.document-duplication` | 사용자 직접 보고 | 현재 세션의 §2 인용문; event store 미구현으로 durable event ID 대기 | 2026-07-20 | 증상, 정상화 요청, 재발 방지 규칙 요청 |
| `src.git.commit.f1d7c66` | Git commit | `f1d7c66d5fe70c2b6b3858d1f47c80cafa00f659` | 2026-07-20 | 정상화 전 전체 파일 상태 |
| `src.git.blob.r1-design` | Git blob | `683e594e5fac886f348f7703296dad113b227af2`; SHA-256 `CD0CF3F3BC66DBF1A0590F03C1CF450CEAED54D5C80F45A56BA1D03B7CBDC5D7` | 2026-07-20 | R-1 전체 원문과 11/18 제안 |
| `src.git.blob.intent-audit` | Git blob | `e44fe4d3d9af0d675ca872f7e77d22c31efe89b4`; SHA-256 `7694818D60AF39FCA432006D523DA953BF923C444841FCA3F9DD99419087039A` | 2026-07-20 | 444줄 의도 검증 원문과 보정 근거 |
| `src.repo.project-rules#authority-1.4` | 활성 규칙 | `PROJECT_RULES.md` → `1. Authority and scope` → rule 4; SHA-256 `8C9DD078DCD6A7EC3EAE65981D347C96BF585C1079FB45664C0D06EF81BC5B8B` | 2026-07-20 | 단일 owner와 중복 문서 금지 |
| `src.repo.workflow#document-creation-gate` | 활성 절차 | `docs/agent/WORKFLOW.md` → `Document creation gate`; SHA-256 `60E86CB8448D1A739C26CE77C3F49F6D955D340B5A103063FF7DB4357FC24128` | 2026-07-20 | 생성 전 거부 조건과 검증 |
| `src.repo.document-map#preservation` | 활성 router | `docs/agent/DOCUMENT_MAP.md` → `Preservation and default-context states`; SHA-256 `1FC159165DDFC9D64FA791BD8B2A74D674DEE1088EF57484AD93AD94872F4800` | 2026-07-20 | 문서 권위·보존·기본 context 상태, R-1.1 승인 경로와 session record 분리 |
| `src.repo.maintenance#event-driven-review` | 활성 유지보수 계약 | `docs/agent/KNOWLEDGE_MAINTENANCE.md` → `Event-driven review without a periodic deadline`; SHA-256 `BAC25CD82F02261E160CB44DA0E88F11E3FD425C914E51F95EC3E28789725108` | 2026-07-20 | 정기 기한 없는 즉시 trigger 검토 방식 |
| `src.repo.r1.1#accepted-r2a` | 승인된 설계 근거 | `docs/reports/2026-07-20_R-1.1_지식_시스템_설계_보정.md` → metadata와 §14; SHA-256 `84FF62BF2AB9D0B3178032166A6E57FAFE059B40DBE4C4A53FFBD7040B6018FF` | 2026-07-20 | 사용자가 채택한 R-2A 권위와 다음 단계 경계 |

## 9. 관련 항목

| 관계 | 대상 | 의미 |
|---|---|---|
| `resolved_by` | `PROJECT_RULES.md` rule 1.4 | 전역 단일 owner invariant |
| `resolved_by` | `WORKFLOW.md#document-creation-gate` | 문서 생성 전 실행 게이트 |
| `resolved_by` | `DOCUMENT_MAP.md` preservation/report routing | 권위와 기본 context 분리 |
| `supersedes_behavior` | 단계별 새 완결형 보고서 생성 | 동일 주제는 기존 owner/current proposal 갱신 |
| `related_to` | `case.project.document-authority-duplication` | 현재 사례 자체의 후속 revision |
| `related_to` | `session.2026-07-20.r1-r1.1-document-governance` | 현재 상태를 복제하지 않는 별도 역사 세션 기록 |

## 10. 갱신 이력

| revision | 시각 | 행위자 | 변경 | 근거 | 검증 |
|---:|---|---|---|---|---|
| 1 | 2026-07-20T22:50:40+09:00 | Codex project agent | 첫 수동 case record 생성; 문제·원인·해결·재발 방지·event-driven 검토 정책 기록 | 사용자 직접 요청과 저장소 정상화 결과 | structural, 사용자 내용 승인 대기 |
| 2 | 2026-07-20T23:02:59+09:00 | Codex project agent | `DOCUMENT_MAP.md`의 R-1.1 상태가 current proposal에서 accepted R-2A source로 바뀌어 `needs_review` trigger 처리 후 `resolved` 복귀; 예방 규칙은 변경 없이 유효하고 source hash·관계를 갱신 | 사용자 R-2A 인수인계 요청, R-1.1 승인 상태 정합성 검증 | structural |
| 3 | 2026-07-20T23:16:47+09:00 | Codex project agent | 별도 closed session record를 등록하면서 `DOCUMENT_MAP.md` 변경 trigger 처리 후 `resolved` 복귀; session history와 current handoff의 owner가 분리돼 중복 방지 규칙은 계속 유효하며 source hash·relation을 갱신 | 사용자 세션 대화·작업 기록 요청, document creation gate | structural |

## 11. 알려진 한계와 다음 조건

- case JSON Schema, writer, event store, relation store와 자동 index는 아직 없다.
- 사용자 대화 source는 durable event ID가 없어 이 문서에 수동 인용으로 보존했다.
- R-2B에서 이 기록을 정식 schema와 source/event/relation record로 이관하되 stable case ID와 revision history를 유지해야 한다.
- 현재 문서는 수동 정본이며 검색 projection이 없어 문서 지도와 직접 경로로만 선택한다.
