# R-3 resolver/writer 일반화 및 유지보수 구현 결과

- 작성일: 2026-07-21
- 상태: R-3 구현·구조 검증·자동 검증 완료 / R-4 착수 가능
- 목적: 승인된 R-3 범위의 file/unit adapter, lifecycle writer, 실패 복구, 지식·source 검토, 결정적 resolver를 구현하고 단계 완료 게이트의 실제 결과를 보존한다.
- 사용 시점: R-3 구현을 정확히 감사하거나 R-4 검색 평가의 baseline 능력을 확인할 때만 사용한다.
- 작성·검증 주체: 프로젝트 에이전트가 구현·자동 검증하고 사용자가 현재 명령에서 R-3~R-5 실행을 승인했다.
- 언어: 한국어.
- 저장 위치: `docs/reports/2026-07-21_R-3_resolver_writer_일반화_결과.md`.
- 연결 관계: [승인 설계](2026-07-20_R-1.1_지식_시스템_설계_보정.md), [지식 계약](../agent/KNOWLEDGE_SYSTEM.md), [검색 계약](../agent/CONTEXT_RETRIEVAL.md), [유지보수 계약](../agent/KNOWLEDGE_MAINTENANCE.md), [현재 체크포인트](../../SESSION_HANDOFF.md).
- 권위·보존 상태: `retained-evidence`; 구현 권위는 연결된 기술 계약과 활성 코드가 소유하며 이 보고서는 R-3 시점의 delta와 검증만 보존한다.

## 1. 단계 시작 게이트

### 목표와 범위

- Markdown 중심 R-2A writer를 등록된 text/code/config/test/binary 종류로 일반화한다.
- 새 파일·이동·삭제, before file/unit hash 충돌, 부분 실패 rollback과 연결된 retry를 처리한다.
- knowledge candidate·review·revision·supersession과 source hash 변경·검토를 append-only history로 남긴다.
- session summary와 handoff를 구조 데이터에서 생성할 수 있게 한다.
- exact·metadata·verified one-hop relation 선택과 동일 revision의 selection fingerprint를 제공한다.

### 제외 범위

- ranked text search, SQLite FTS5, index 평가·재구축은 R-4다.
- cold start, protected task namespace 종합 인수, 실제 작업 3종 누출 평가는 R-5다.
- vector, graph database, Obsidian은 추가하지 않았다.
- decision·case lifecycle writer와 자동 review scheduler/queue는 승인 설계에 없는 R-3 요구로 추가하지 않았다.

### 구현 전 정의한 테스트와 예상 결과

- code/config/test/binary adapter: stable symbol/key/sidecar locator와 hash 생성.
- lifecycle: 계약에 포함된 create/write/move/delete만 성공하고 stale before hash는 무변경 거부.
- failure recovery: 두 번째 적용 실패 후 모든 대상 원복, failed event 기록, 같은 계약 retry 성공.
- maintenance: candidate는 기본 검색 제외, 검토 후 verified, supersession은 이전 record 보존과 replacement candidate 생성.
- source review: hash 변경 시 source와 종속 knowledge가 `needs_review`, 명시 검토 후에만 source active 복귀.
- resolver: metadata fixture가 code/test와 verified context knowledge 및 active one-hop relation만 선택하고 fingerprint를 기록.
- 회귀: 기존 R-2A/R-2B 10개 테스트, 29-rule mapping, corpus trace, protected prefilter, orphan/hash/event chain 유지.

## 2. 구현 결과

### unit adapter와 catalog lifecycle

- Python AST 기반 `code_symbol`·`test_symbol`, TOML/INI/simple-YAML `key_path`, binary hash+sidecar metadata adapter를 추가했다.
- planned→active 생성, stable file ID를 유지하는 move와 `moved_from`, 마지막 hash를 보존하는 deleted 상태를 구현했다.
- catalog `observed_at`은 내용이 같을 때 보존돼 동일 revision이 불필요하게 변하지 않는다.

### transactional writer와 실패 복구

- writer는 file hash와 unit hash를 모두 preflight하고 text/JSON/JSONL/Python/config/binary 내용을 형식별로 검증한다.
- 모든 touched path snapshot을 보존한 뒤 적용하며 중간 실패 시 전체를 원복하고 `write_failed` event에 원인·적용 수·rollback 결과를 기록한다.
- retry는 같은 contract의 failed/rejected event만 참조할 수 있고 성공 시 `write_retried`로 연결된다.

### record/source maintenance와 closure 생성

- `maintain-knowledge`가 candidate 생성, hash/revision gated review·revise·supersede와 pending supersedes relation을 처리한다.
- `knowledge/reviews.jsonl`과 `knowledge/revisions.jsonl`은 각각 append-only hash chain이다.
- `check-sources`는 source 변경을 감지해 종속 knowledge까지 `needs_review`로 바꾸며, `maintain-source`는 감지 후 다시 변하지 않은 current hash만 명시적으로 수락한다.
- 구조 데이터에서 session summary와 single handoff를 생성하는 writer operation을 추가했다.

### deterministic resolver

- 명시적 file/record metadata filter를 추가했고 candidate·비검증 knowledge는 기본 metadata 선택에서 제외한다.
- context마다 catalog/rule/unit/record/source/relation revision과 선택 ID 집합, selection fingerprint를 기록한다.
- R-3 metadata fixture fingerprint는 `4bee8e779c94f3bd61eb75c9ed7333c2405741d8671ba46a2f04d34c5f775375`이며 code/test, `knowledge.context.shared-work-context`, D-14, 2개 source, active one-hop relation만 선택했다.

## 3. 검증 결과

| 검증 | 실행 명령 | 기대 결과 | 실제 결과 |
|---|---|---|---|
| Python 문법 | bundled Python `-m py_compile tools/context/context_system.py tests/context/test_context_system.py` | compile 오류 0 | 통과 |
| 단위·회귀 테스트 | bundled Python `-m unittest tests.context.test_context_system` | 기존 10개+R-3 6개 전부 통과 | 16개 통과 |
| 통합 구조 검증 | bundled Python `tools/context/context_system.py validate` | error 0, orphan 0, 8+21 rule, corpus/event/history 정상 | `ok=true`, error 0, orphan 0 |
| R-3 source 폐루프 | `check-sources` 후 `maintain-source`·`maintain-knowledge` | 변경 감지→review→source/knowledge 재검증 | source 2개·knowledge 4개 전환 후 모두 재검증 |
| metadata fixture | `resolve r3_metadata_retrieval.json` | exact scope의 code/test+verified record+1-hop relation | 기대 ID만 선택, fingerprint 기록 |

통합 검증 시점 수량은 active file 88, unit 11,911, event 29, review 12, revision 12, decision 17, knowledge 4, case 1, source 7, relation 6, local link 234였다. 종료 요청·보고서 자체는 이후 catalog에 추가되며 같은 검증을 다시 실행한다.

## 4. 자체 검토와 개선

- 발견: 최초 구현은 source hash 변경을 감지했지만 reviewed current hash를 active로 복귀시키는 명시 동작이 없었다.
- 개선: `maintain-source`를 추가하고 expected record hash, 재변경 검사, review/revision history, atomic rollback을 구현했다.
- 발견: metadata record가 선택돼도 relation 확장이 exact request ID만 seed로 사용했다.
- 개선: exact와 metadata 선택 ID를 동일한 verified one-hop seed로 통합했다.
- 발견: catalog sync마다 `observed_at`이 바뀌어 revision 재현성이 약해질 수 있었다.
- 개선: 내용과 상태가 같으면 기존 observed time을 보존하고 fingerprint에서 volatile 관측 시각을 제외했다.
- 발견: source maintenance의 여러 canonical store 쓰기가 부분 실패할 수 있었다.
- 개선: source/items/review/revision snapshot과 전체 rollback을 추가했다.
- 경계 검토: search ranking/index/cold-start acceptance는 구현하지 않아 R-4/R-5를 앞당기지 않았다.

## 5. 실패 기록

| 목표 | 시도 | 원인·결과 | 연속 수 | 다음 조건 |
|---|---|---|---:|---|
| resolver 실행 | 1 | system `python`이 PATH에 없음; bundled Python으로 전환 후 성공 | 0 | bundled runtime 경로 유지 |
| schema 편집 | 1 | 대형 apply patch가 장시간 응답 없음; 변경 여부 확인 후 작은 patch로 분할해 성공 | 0 | schema patch를 작은 단위로 유지 |
| source review 폐루프 | 1 | 감지는 성공했으나 accept writer 누락을 자체 검토에서 발견; 구현·실사용·회귀 통과 | 0 | source 변경 뒤 명시 review 필수 |
| 통합 검증 격리 | 1 | 작업 중 별도 프로세스가 untracked `blog_images/`를 생성; 파일을 건드리지 않고 R-3 변경만 복제한 격리 작업트리에서 검증 성공 | 0 | 동시 사용자 파일을 stage/catalog/commit하지 않음 |

## 6. 주요 변경 파일

- 구현·테스트: `tools/context/context_system.py`, `tests/context/test_context_system.py`
- 계약·schema: `docs/agent/{WORKFLOW,KNOWLEDGE_SYSTEM,CONTEXT_RETRIEVAL,KNOWLEDGE_MAINTENANCE}.md`, `schemas/{file,unit,task_request,work_context,write_contract,event,knowledge,source,review,revision}.schema.json`
- canonical history: `knowledge/reviews.jsonl`, `knowledge/revisions.jsonl`
- fixtures/evidence: `context/requests/r3_*.json`, `context/work/r3_*.json`, `context/payloads/r3_*.json`, `records/work/events.jsonl`
- projections/closure: `catalog/*.jsonl`, `docs/agent/DOCUMENT_MAP.md`, `SESSION_HANDOFF.md`, 이 보고서

## 7. 완료 게이트와 잔여 위험

- R-3 요구사항 구현: 충족.
- 정의된 단위·통합·구조·회귀 테스트: 전부 통과.
- 자체 검토 필수 개선: 전부 반영 후 재검증.
- R-4/R-5 경계 선행 구현: 0건.
- 잔여 위험: decision/case lifecycle와 scheduled review는 미구현이며 현재 승인 설계상 R-3 비범위다.
- 잔여 위험: 원본 작업공간의 untracked `blog_images/`는 동시 사용자 작업으로 판단해 읽기·수정·catalog·commit에서 제외했다. R-3 커밋 범위의 격리 복제본은 orphan 0으로 통과했다.
- 판정: R-3 완료 게이트 통과. 사용자가 이미 승인한 R-4의 고정 평가셋과 측정 기준 확정으로 진행한다.
