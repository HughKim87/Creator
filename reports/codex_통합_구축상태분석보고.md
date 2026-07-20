# 프로젝트 구축 상태 통합 분석 보고서

- 작성일: 2026-07-20
- 상태: Claude·Codex 보고서 비교 통합 / 사용자 검토 전
- 목적: 두 구축 상태 분석 보고서의 공통 사실, 관점 차이, 충돌과 보완점을 비교하고 하나의 판정·목표 구조·실행 순서로 통합한다.
- 사용 시점: 기존 명령 2 설계와 명령 3 결과를 수정할지 결정하고, 다음 승인 단계를 정할 때 사용한다.
- 작성·수정 주체: 통합 검토 에이전트가 두 원문과 현재 저장소 실측을 근거로 작성하며, 후속 설계·구현의 채택은 사용자가 승인한다.
- 언어: 한국어.
- 저장 위치: `reports/통합_구축상태분석보고.md`.
- 연결 관계: [Claude 보고서](claude_구축상태분석보고.md), [Codex 보고서](codex_구축상태분석보고.md), [프로젝트 규칙](../PROJECT_RULES.md), [문서 지도](../docs/agent/DOCUMENT_MAP.md), [기존 설계](../docs/reports/2026-07-20_프로젝트_기반_및_지식_시스템_설계.md)를 비교 근거로 사용한다.
- 변경 제약: 이 통합 과정에서는 두 원본 보고서를 포함한 기존 파일을 삭제하거나 수정하지 않고 이 파일만 새로 생성한다.
- 권위: 비교·통합 시점 보고서다. 기존 활성 정책이나 승인 설계를 자동 변경하지 않는다.

## 1. 통합 결론

### 최종 점수

| 관점 | 점수 | 의미 |
|---|---:|---|
| Claude 보고서 | 55/100 | 설계가 목표를 이해하고 있고 재구조화할 원료가 충분하다는 점을 크게 반영 |
| Codex 보고서 | 27/100 | 작업별 규칙·전 파일 컨텍스트·쓰기 반영 기능의 실제 구현 여부를 중심으로 평가 |
| **통합 목적 적합도** | **37/100** | 설계·문서 자산은 유효하지만 목표 시스템의 핵심 구조와 동작은 아직 없음 |

두 보고서의 핵심 사실 판단은 충돌하지 않는다. 점수 차이는 무엇을 “현재 구축 성과”로 인정했는지의 차이다.

- Claude 보고서는 상세 계약, 문서 메타데이터, 유효한 링크, 결정 ID와 기존 분석 결과를 재사용 가능한 준-레코드로 인정했다.
- Codex 보고서는 그 자산이 아직 작업별 규칙 레코드, 전 파일 카탈로그, resolver, writer로 작동하지 않는다는 점에 더 큰 가중치를 뒀다.

**통합 판정:** 현재 프로젝트는 목표 시스템의 설계도와 원료는 갖고 있지만, 목표 시스템 자체는 아니다. 기존 Stage 4-A 구현을 바로 시작하지 말고, 먼저 설계를 수정해 규칙·파일·지식·결정·사례·관계·작업 event를 하나의 읽기·쓰기 컨텍스트 흐름으로 묶어야 한다.

## 2. 비교 방법과 판정 표기

| 표기 | 의미 |
|---|---|
| `F` | 두 보고서 또는 현재 저장소에서 직접 확인된 사실 |
| `I` | 확인된 사실을 결합한 통합 추론 |
| `D` | 두 보고서의 판정 차이를 해소한 통합 판단 |
| `R` | 후속 설계·구현 권고. 아직 승인된 결정이 아님 |

비교 절차는 다음과 같다.

1. 두 보고서를 처음부터 끝까지 읽었다.
2. 사용자 의도 해석, 실측 사실, 점수 기준, 목표 구조, 다음 단계, 위험을 항목별로 대조했다.
3. 수치가 다른 항목은 현재 활성 파일에서 다시 계산했다.
4. 공통 사실은 통합하고, 서로 다른 강점은 보완 관계로 채택했다.
5. 구현이 필요한 내용과 설계 수정만 필요한 내용을 분리했다.

보호 대상 `inputs/`, `outputs/`는 열거하거나 읽지 않았다. `backup/`도 추가 탐색하지 않고 기존 승인 분석에 기록된 근거만 사용했다.

## 3. 보고서별 핵심 주장

### 3.1 Claude 보고서

[Claude 보고서](claude_구축상태분석보고.md)의 핵심 명제는 다음과 같다.

> 설계는 목표 구조를 알고 있지만, 구축물이 그 설계를 자기 자신에게 적용하지 않았다.

주요 발견:

- 규칙이 하나의 상시 완독 문서에 남아 있다.
- 지식 단위 ID·상태·신뢰도·출처·검토 기한이 실제 기반 문서에 적용되지 않았다.
- 승인 결정 D-01~D-11이 독립 decision record가 아니라 보고서 속 표에 있다.
- typed relation 대신 본문 Markdown 링크만 존재한다.
- 탐색 단위가 규칙·지식 항목이 아니라 전체 문서다.
- 현재 자산은 버릴 대상이 아니라 원자화·메타데이터화할 좋은 원료다.

강점은 **계약과 실제 자기 적용 사이의 모순**, **승인 결정의 권위 위치 문제**, **인수인계의 복합 책임**을 구체적으로 드러낸 점이다.

### 3.2 Codex 보고서

[Codex 보고서](codex_구축상태분석보고.md)의 핵심 명제는 다음과 같다.

> 현재 체계는 정적 문서 거버넌스이며, 사용자가 원하는 것은 모든 활성 파일이 참여하는 동적 읽기·쓰기 컨텍스트 시스템이다.

주요 발견:

- 최소 안전 커널 외 규칙도 작업별 조건부 레코드로 분류돼야 한다.
- 문서뿐 아니라 코드·설정·스키마·테스트·보고서가 모두 선택 가능한 file node여야 한다.
- `read_when`, `write_when`, owner, validator, consumes/produces, hash를 소유하는 universal file catalog가 없다.
- 기존 규칙·지식·결정·실패 사례가 활성 corpus로 이관되지 않았다.
- 작업 후 파일·event·관계·지식 후보를 갱신하는 writer가 없다.
- 기존 Stage 4-A보다 먼저 설계 정정 단계가 필요하다.

강점은 **모든 파일의 편입**, **쓰기 컨텍스트**, **기존 corpus 선이관**, **단계별 재설계 순서**까지 목표 범위를 확장한 점이다.

## 4. 공통으로 확인된 사실

### 4.1 현재 규칙은 작업별로 선택되지 않는다

`F` 현재 [PROJECT_RULES.md](../PROJECT_RULES.md)는 매 대화 시작에 전체를 읽는 문서다.

현재 재계산 결과:

| 항목 | 현재 값 |
|---|---:|
| 파일 행 수 | 54 |
| 절 수 | 6 |
| 번호 규칙 수 | 29 |

Claude 보고서의 “55행·24개 조항”과 Codex 보고서의 “54행·29개 번호 규칙” 중 현재 저장소 실측은 Codex 수치와 일치한다. 이는 집계 방식 또는 관찰 시점의 차이이며, “모든 규칙이 상시 로드되고 작업별 scope가 없다”는 공통 결론에는 영향이 없다.

`F` 활성 핵심 문서에는 `rule_id`, `applies_when`, `excludes_when`, `write_when`, `content_sha256` 필드가 없다.

### 4.2 계약이 실제 지식 레코드에 적용되지 않았다

`F` [KNOWLEDGE_SYSTEM.md](../docs/agent/KNOWLEDGE_SYSTEM.md)는 stable ID, 상태, 신뢰도, 출처, 관계, 검토 기한, 이력을 요구한다.

`F` 그러나 활성 규칙·결정·사례가 이 계약을 사용하는 독립 정본 레코드로 존재하지 않는다.

`I` 계약 문서는 상세하지만 실제 첫 corpus가 없으므로 스키마의 사용성, 기록 비용, 검색 단위를 실데이터에서 검증할 수 없다.

### 4.3 결정의 권위 위치가 불완전하다

`F` D-01~D-11은 승인된 결정으로 취급되지만 [설계 보고서](../docs/reports/2026-07-20_프로젝트_기반_및_지식_시스템_설계.md) 안의 표에 있다.

`F` [DOCUMENT_MAP.md](../docs/agent/DOCUMENT_MAP.md)는 보고서를 시점별 evidence로 분류하며 자동 실행 정책이 아니라고 정의한다.

`I` 승인 결정은 독립 decision record가 권위를 소유하고 설계 보고서는 그 결정의 근거·보고 문서로 연결되는 편이 자체 권위 모델과 일치한다.

### 4.4 관계가 구조화된 데이터가 아니다

`F` 현재 연결은 Markdown 링크다. 방향, 관계 유형, 상태, 근거를 가진 relation record가 없다.

`I` 링크 무결성은 좋은 출발점이지만 `supported_by`, `applies_to`, `validates`, `supersedes`, `failed_in` 같은 관계를 검색·검증할 수 없다.

### 4.5 모든 활성 파일이 컨텍스트 노드가 아니다

현재 비보호 Git 추적 파일과 문서 레지스트리를 다시 계산했다.

| 항목 | 수량 |
|---|---:|
| 비보호 활성 Git 추적 파일 | 15 |
| `DOCUMENT_MAP.md` 활성 레지스트리 행 | 11 |

`F` `.gitattributes`, `.gitignore`, 문서 지도 자신, 명령 3 보고서가 활성 레지스트리에 없다. 현재 `reports/`의 비교 원본들도 별도 사용자 보고서다.

`F` 모든 활성 파일의 읽기 조건, 쓰기 조건, 소유자, validator, 입출력 관계, hash와 색인 범위를 가진 file catalog가 없다.

### 4.6 기존 지식이 초기 corpus로 이관되지 않았다

`F` 기존 분석에는 영상 제작 순서, 원본 지문, 검증 수준, 프로세스 종료 코드, 보호 경로 선필터, Graphify·fail-open·미디어 기본값 실패 등 재사용 가능한 규칙과 사례가 이미 정리돼 있다.

`F` 이 지식은 긴 보고서와 `backup/` 출처 링크에 있으며 active rule, knowledge, decision, case record로 이관되지 않았다.

### 4.7 읽기·쓰기 폐쇄 루프가 없다

`F` 현재 가능한 것은 문서 단위의 수동 시작 라우팅이다.

`F` 다음은 구현되지 않았다.

- 작업 의도에서 적용 규칙·파일·지식을 선택하는 resolver
- 수정 파일의 owner·write rule·validator 선택
- 변경 후 file hash와 관계 갱신
- 작업 event 기록
- 결과에서 규칙·지식·결정·사례 후보 생성
- 다음 작업 corpus로의 반영

## 5. 두 보고서의 차이와 통합 판정

| 쟁점 | Claude 보고서 | Codex 보고서 | 통합 판정 |
|---|---|---|---|
| 점수 | 55 | 27 | 다른 채점축이므로 평균하지 않고 37로 재산정 |
| 핵심 문제 | 설계의 자기 적용 누락 | 전 파일 읽기·쓰기 시스템 부재 | 둘 다 채택. 자기 적용 범위를 모든 파일과 writer까지 확대 |
| 규칙 단위 | 작업별 규칙 모듈 | 조건부 원자 rule record | 물리적으로 작은 rule pack, 논리적으로 안정 ID를 가진 원자 규칙 |
| 파일 범위 | 주로 문서·지식 구조 | 코드·설정·테스트 포함 모든 활성 파일 | Codex 범위를 채택 |
| 결정 권위 | 보고서 밖 독립 decision record 강조 | D-01~D-11 재판정 강조 | 독립 record와 기존 결정별 유지·수정·철회 검토를 모두 수행 |
| 관계 | Markdown 링크→typed relation | rule/file/knowledge/task 관계 확대 | 모든 노드 유형을 동일 relation 정본에 연결 |
| 인수인계 | 현재 재개점만 남기고 분해 | 쓰기·catalog 루프 중심 | handoff는 현재점만 소유하고 나머지는 정본 record로 연결 |
| 다음 단계 | Stage 4-A를 기존 지식 재편 단계로 재정의 | Stage R-1 설계 정정 후 R-2 이관 | 구현 전 설계 정정 R-1을 먼저 수행하고 R-2에서 재편 |

### 점수 차이 해소

55점은 “설계와 원료의 준비도”, 27점은 “현재 작동하는 시스템의 목적 적합도”에 가깝다. 사용자는 구축 상태를 물었으므로 실제 구조와 동작에 더 큰 비중을 두되, 재사용 가능한 설계·문서 자산도 인정했다.

| 통합 평가 항목 | 배점 | 점수 |
|---|---:|---:|
| 목표 이해와 설계 자산 | 20 | 15 |
| 최소 커널과 작업별 규칙 선택 | 15 | 3 |
| 원자 지식·결정·사례·관계 | 20 | 5 |
| 모든 활성 파일의 읽기·쓰기 컨텍스트 | 20 | 2 |
| 기존 지식의 활성 corpus 이관 | 15 | 3 |
| 안전·출처·검증 위생 | 10 | 9 |
| **합계** | **100** | **37** |

## 6. 통합 목표 구조

### 6.1 최소 부트스트랩

매 세션에 반드시 들어가는 것은 다음으로 제한한다.

- 사용자 지시와 지속 규칙의 우선순위
- 보호 데이터·비밀·외부 변경 경계
- 파괴적 행동과 승인 조건
- context resolver 진입 규칙
- 규칙 충돌 시 안전한 중단 방식

`PROJECT_RULES.md`는 이 커널만 소유한다. 언어, 보고 형식, Git, 인덱싱, 특정 도구, 영상 제작 규칙은 조건부 규칙으로 분리한다.

### 6.2 조건부 규칙

물리 파일을 규칙 한 문장마다 만들 필요는 없다. 함께 적용·검토되는 작은 rule pack으로 저장하되 각 규칙은 논리적 stable ID와 조건을 가진다.

필수 필드:

```text
rule_id, statement, class, priority,
applies_when, excludes_when, applies_to,
required_context, source_refs,
owner, status, review_due_at, relations
```

### 6.3 universal file catalog

모든 비보호 활성 파일을 선택 가능한 file node로 등록한다.

```text
file_id, path, kind, purpose, owner, authority,
read_when, write_when, task_tags,
consumes, produces, depends_on,
validators, sensitivity, index_scope,
content_sha256, updated_at, status
```

- Markdown은 자체 메타데이터를 사용할 수 있다.
- 코드·설정·테스트·바이너리는 manifest/sidecar가 메타데이터를 소유한다.
- 사용자 task 파일은 명시적 작업 scope에서만 별도 namespace로 등록한다.

### 6.4 지식·결정·사례·관계

- 지식: 사실, 추론, 절차, 제약
- 결정: 선택지, 채택 이유, 승인자, 적용 범위, 상태
- 사례: 증상, 원인, 해결, 회귀 검증
- 관계: rule, file, knowledge, decision, case, task, source 사이의 typed edge

D-01~D-11은 첫 decision record가 되고, 기존 분석의 유지 규칙과 실패 사례는 첫 knowledge/case corpus가 된다.

### 6.5 event와 resolver/writer

```text
task request
  → minimal kernel
  → applicable rules
  → target and related files
  → knowledge, decisions, cases
  → bounded read context
  → work
  → owner, write rules, validators
  → file changes and validation
  → event, hash, relation updates
  → new candidates
  → next retrieval corpus
```

## 7. 기존 데이터의 통합 이관 원칙

### 7.1 이관 출처

| 출처 | 우선 이관 대상 |
|---|---|
| `backup/origin` | 영상 도메인 규칙, 작업 순서, 도구 계약, 품질 기준 |
| `backup/refactorying_snapshot_1` | 실패 원장, 회귀 계약, 과도한 구축 사례 |
| `backup/refactorying_snapshot_2` | 직접 라우팅, 파일 상태, 문서 원자화, 도구 도입 판단 |
| 활성 분석·설계·구축 보고서 | 분류 판단, 승인 결정, 검증 결과, 미결 충돌 |

### 7.2 이관 상태

백업 원문은 활성 규칙으로 직접 검색하지 않는다.

```text
historical_source
  → candidate rule/knowledge/decision/case
  → source locator + hash
  → duplicate/conflict review
  → user or contract approval
  → active record
  → default retrieval eligibility
```

### 7.3 첫 corpus

다음 항목을 새 스키마의 첫 실데이터로 사용한다.

1. `PROJECT_RULES.md` 29개 규칙의 커널/조건부 분류
2. D-01~D-11 결정
3. 기존 분석의 유지·개선·폐기 판단
4. handoff와 보고서에 기록된 실패 사례
5. 기존 공식 근거와 저장소 source locator
6. 현재 비보호 활성 파일 15개의 file node

## 8. 통합 실행 순서

### R-1. 설계 정정 — 구현 없음

1. 최소 커널에 남길 규칙을 확정한다.
2. rule, file, knowledge, decision, case, relation, event 스키마를 확정한다.
3. 작업 유형과 `applies_when`/`read_when`/`write_when` 계약을 확정한다.
4. 읽기 resolver와 쓰기 writer가 공유할 manifest를 설계한다.
5. backup migration namespace와 보호 task namespace를 분리한다.
6. 기존 D-01~D-11 중 유지·수정·철회 결정을 사용자 승인 대상으로 제시한다.

### R-2. 기존 기반 재구조화

1. 현재 15개 활성 파일을 universal file catalog에 등록한다.
2. 29개 규칙을 최소 커널과 조건부 rule pack으로 분류한다.
3. D-01~D-11을 독립 decision record로 만든다.
4. 기존 지식·실패 사례·출처를 active 후보로 추출한다.
5. Markdown 링크를 typed relation 후보로 변환한다.
6. handoff에는 현재 재개점만 남기고 다른 지식은 소유 record로 연결한다.

### R-3. 최소 resolver와 writer

1. task request schema를 구현한다.
2. task→rule→file→knowledge 선택을 결정적으로 수행한다.
3. 변경 파일의 owner, write rule, validator를 제공한다.
4. 작업 후 event, hash, relation, candidate를 갱신한다.
5. 새 세션 재개와 동일 컨텍스트 재현을 검증한다.

### R-4. 검색 projection

실제 corpus와 resolver가 동작한 뒤 SQLite FTS5를 추가한다. 벡터 검색, 그래프 DB, Obsidian은 동일 평가셋에서 필요성이 증명될 때만 검토한다.

## 9. 우선순위별 권고

### 반드시 먼저 할 일

1. 기존 Stage 4-A 착수를 중단하고 R-1 설계를 승인받는다.
2. `PROJECT_RULES.md`의 최소 커널 경계를 정한다.
3. universal file catalog를 지식 시스템의 필수 정본으로 추가한다.
4. 읽기뿐 아니라 쓰기·검증·변경 반영 흐름을 계약한다.
5. 기존 지식을 첫 corpus로 이관하는 범위와 승인 절차를 정한다.

### 재구조화 단계에서 할 일

1. 규칙을 작은 pack과 원자 ID로 분리한다.
2. D-01~D-11을 독립 결정으로 승격한다.
3. 실패 사례와 검증 근거를 case·knowledge로 분리한다.
4. 모든 활성 파일에 read/write 조건과 validator를 연결한다.
5. orphan·dangling·conflict·supersedes cycle을 검증한다.

### 나중에 할 일

- SQLite FTS5와 한국어 토크나이저 평가
- 벡터 검색
- 전용 그래프 DB
- Obsidian UI
- 자동 외부 자료 갱신

## 10. 통합 완료 기준

1. 매 세션 상시 컨텍스트가 최소 안전·권위 커널로 제한된다.
2. 보고서 작성 작업은 보고·언어·근거 규칙만 선택한다.
3. 영상 XML 작업은 관련 도메인 규칙·도구·테스트·실패 사례만 선택한다.
4. 모든 비보호 활성 파일이 file catalog에 등록된다.
5. 새 파일 생성 시 owner, read/write 조건, validator가 함께 등록된다.
6. D-01~D-11이 독립 결정으로 조회된다.
7. 기존 규칙·지식 하나가 backup source locator에서 active record까지 추적된다.
8. 상충·대체 규칙이 병존하며 현재 우선순위를 설명한다.
9. 변경 후 file hash, event, relation이 갱신된다.
10. 작업 결과가 새 지식·결정·사례 후보로 돌아간다.
11. 보호 사용자 데이터가 승인 없는 전역 목록·인덱스·로그에 나타나지 않는다.
12. 새 세션이 LLM 기억 없이 동일 작업 컨텍스트를 재현한다.

## 11. 위험과 통합 대응

| 위험 | 통합 대응 |
|---|---|
| 모든 파일을 항상 로드하는 것으로 오해 | 모든 파일은 catalog에 등록하되 task scope로 선택 |
| 규칙 한 문장마다 파일을 만들어 관리비 증가 | 작은 rule pack + 내부 stable rule ID |
| 검색 점수가 규칙 권위를 결정 | authority와 적용 조건을 먼저 계산하고 검색은 후보 보조로 제한 |
| 역사 규칙이 현재 지시로 실행 | migration namespace와 승인 승격 상태 사용 |
| file catalog가 곧 낡음 | writer가 파일 변경과 함께 hash·관계·metadata를 갱신 |
| 코드 내용을 문서에 중복 | file node가 코드·테스트·계약을 연결하고 본문은 소유 파일에 유지 |
| 읽기만 최적화되고 쓰기 반영 누락 | owner·write rule·validator·event를 resolver와 같은 흐름에 포함 |
| 설계 문서만 다시 늘어남 | 첫 corpus와 대표 작업 평가를 R-2 완료 조건으로 강제 |

## 12. 사실·추론·통합 결정

### 확인된 사실

- `F` 두 보고서는 현재 구조가 목표 시스템 그 자체가 아니라는 데 동의한다.
- `F` 현재 규칙은 54행, 6개 절, 29개 번호 규칙이며 전체 시작 로드 대상이다.
- `F` 비보호 활성 추적 파일은 15개이고 문서 레지스트리는 11행이다.
- `F` 조건부 규칙 필드, universal file catalog, 독립 decision/case corpus, typed relation, resolver, writer가 없다.
- `F` 기존 지식과 실패 경험은 보고서와 역사 출처에 존재한다.

### 통합 추론

- `I` 새 내용을 대량 발명하는 것보다 기존 내용을 목표 스키마에 이관하는 것이 우선이다.
- `I` 문서 단위 메타데이터와 유효 링크는 재구조화 비용을 줄이는 좋은 입력이다.
- `I` file catalog와 writer 없이 검색기만 구현하면 읽기·쓰기 컨텍스트 축적 목표를 달성할 수 없다.

### 통합 판단

- `D` 목적 적합도는 37/100으로 본다.
- `D` 현재 자산은 폐기하지 않고 재구조화 원료로 사용한다.
- `D` 다음 단계는 구현이 아니라 설계 정정 R-1이다.
- `D` R-1 승인 전 기존 Stage 4-A, 데이터 이관, resolver, 인덱스 구현을 시작하지 않는다.

## 13. 검증과 변경 보존

- 두 원본 보고서는 전체를 읽어 비교했다.
- 현재 규칙 수, 활성 추적 파일 수, 문서 레지스트리 행 수를 저장소에서 다시 계산했다.
- 신규 통합 문서의 UTF-8, NUL, 공백, Markdown fence, 필수 메타데이터와 로컬 링크를 검증한다.
- [Claude 보고서](claude_구축상태분석보고.md)와 [Codex 보고서](codex_구축상태분석보고.md)는 수정하거나 삭제하지 않는다.
- 기존 활성 문서, handoff, `backup/`도 수정하지 않는다.
- 이 통합 보고서 생성은 설계 변경이나 다음 단계 승인을 의미하지 않는다.
