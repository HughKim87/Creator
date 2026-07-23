# Claude Stage 10 교차검증 감사 보고서

- 작성일: 2026-07-23
- 문서 유형: 외부 교차검증 실행·결과·한계 감사 보고
- 목적: 이번 세션에서 Claude에 실제로 전달한 검증 범위, 호출 성공·실패, Claude 지적, Codex 반영, 검증하지 못한 사용자 요구를 분리해 기록한다.
- 사용 시점: Stage 10 교차검증의 신뢰 범위를 판단하거나 재검증 prompt를 설계할 때
- 작성 책임: Codex
- 상태: 작성 완료 — 시점 교차검증 증거이며 현재 판정 정본은 Stage 10 문서
- 관련 작업 보고: [이번 세션 작업 감사 보고서](2026-07-23_codex_이번_세션_작업_감사_보고서.md)

## 1. 결론

Claude 교차검증은 실제로 수행됐다. Claude는 현재 프로젝트 파일을 읽고 실패 지식 fanout, legacy 호환, 문서 권위, 안전 경계, 테스트 공백을 검토했으며, Codex는 지적받은 결합 회귀를 추가·강화했다.

그러나 Claude에게 전달한 검증 질문에 **“프로젝트의 모든 데이터가 문서 기반이어야 하고 모든 작업이 문서 근거로 진행돼야 한다”**는 핵심 사용자 요구가 포함되지 않았다. Claude는 Codex가 축소해 정의한 Stage 10 주장만 검토했다.

따라서 이 교차검증은 다음 범위에서만 유효하다.

- 실패 Markdown의 직접 검증·검색
- per-case projection/source/lifecycle fanout 방지
- legacy 기본 검색 중복 방지
- 문서 지도 권위 축소
- 기존 안전 경계 유지

프로젝트 전체의 문서 기반 데이터 운영과 사용자 요구 전체 충족을 검증한 결과로는 유효하지 않다.

## 2. 사용한 검증 수단

- 스킬: `delegate-to-claude`
- 기본 스크립트: `invoke_claude.ps1`
- 모드: `review`, `verify`, `challenge`
- 허용 도구: `Read,Grep,Glob`
- 변경 권한: 없음
- 직접 폴백에서도 `--safe-mode`, `--permission-mode dontAsk`, 읽기 전용 도구만 사용
- 외부 변경·Git 작업·파일 수정: Claude 수행 0건

## 3. 호출별 실행 기록

| 순서 | 방식 | 목적 | 결과 | 사용 가능성 |
|---:|---|---|---|---|
| 1 | 스킬 `review` | 전체 Stage 10 diff 검토 | 120초 timeout | 결과 없음 |
| 2 | 스킬 `review`, 4 turns | 범위 축소 재검토 | 약 188초 뒤 exit 1 | 결과 없음 |
| 3 | 스킬 `verify`, 3 turns | 핵심 코드·계약·테스트 확인 | 출력이 컨텍스트 한도를 초과해 보존 실패 | 판정에 사용하지 않음 |
| 4 | 스킬 `verify`, 1 turn | 최고 위험 1건 확인 | 장시간 응답 없어 중단 | 결과 없음 |
| 5 | 스킬 `challenge`, Haiku | 핵심 파일 3개 반례 탐색 | 약 181초 뒤 exit 1 | 결과 없음 |
| 6 | 스킬 evidence packet | 파일 탐색 없는 독립 논리검토 | timeout | 결과 없음 |
| 7 | 외부 승인 후 스킬 `review`, 8 turns | 실제 프로젝트 전체 검토 | 73초 뒤 exit 1 | 결과 없음 |
| 8 | Claude 최소 호출 | 인증·네트워크·모델 상태 분리 | exit 0, `cross-check runtime ok` | 실행 환경 정상 확인 |
| 9 | 스킬 `review`, 20 turns | 실제 프로젝트 전체 검토 재시도 | 121초 뒤 exit 1 | 결과 없음 |
| 10 | 동일 안전 옵션의 Claude 직접 read-only | 실제 프로젝트 파일 검토 | exit 0 | 주 교차검증 결과 |
| 11 | 스킬 `challenge` | 첫 보완 뒤 closure evidence 검토 | `status: completed` | 후속 지적에 사용 |
| 12 | 스킬 최종 challenge | 강화된 결합 흐름 재검토 | exit 1 | 결과 없음 |
| 13 | Claude 직접 no-tool challenge | 최종 요약 증거 판정 | exit 0이지만 원시 출력 부재를 이유로 판단 유보 | 완료 근거로 사용하지 않음 |

스킬 래퍼 실패를 Claude 검증 성공으로 계산하지 않았다. 실제 findings는 10번과 11번의 성공 결과에서만 가져왔다.

## 4. Claude 실제 파일 review 결과

Claude는 검증 시점의 다음 파일을 읽었다.

- `AGENTS.md`
- `PROJECT_RULES.md`
- `SESSION_HANDOFF.md`
- `rules/document-work.md`
- `rules/failure-records.md`
- `rules/stage-work.md`
- `docs/build/stage-10-agent-autonomy-structure-optimization.md`
- `docs/INFORMATION_ARCHITECTURE.md`
- `docs/obsidian/DOCUMENT_MAP.md`
- `src/file_data/knowledge.py`
- `src/file_data/lifecycle.py`
- `src/file_data/context.py`
- `src/file_data/maintenance.py`
- 관련 테스트 4개와 CLI

### 4.1 지적 1 — Stage 10 owner 상태가 실제 구현보다 오래됨

- 심각도: High
- Claude 판단: Stage 10 실행표가 모두 `진행 전`, 점수표가 `대기`인데 코드는 이미 구현돼 문서와 작업 상태가 충돌한다.
- Codex 판정: 수용
- 조치: Stage 10 문서에 실행 결과, Claude 지적, 검증, 점수표를 갱신했다.
- 현재 재판정: 이후 발견된 전체 문서 기반 요구 누락 때문에 이 문서의 `완료`와 `97점`은 다시 무효다.

### 4.2 지적 2 — canonical과 legacy 공존 중복 결합 테스트 부재

- 심각도: Medium
- Claude 판단: context와 maintenance 코드가 legacy를 제외하는 것은 확인되지만 동일 canonical Markdown과 legacy source/failure pair가 함께 있을 때 기본 검색·scan이 정확히 한 건만 반환하는 결합 테스트가 없다.
- 검증 시점 근거:
  - `context.py`의 `_is_legacy_failure_source`, `filter_records`, canonical 후보 추가
  - `maintenance.py`의 legacy source·failure projection drift 제외
- Codex 판정: 수용
- 조치: `test_legacy_failure_coexists_without_default_search_or_drift_duplication`을 추가했다.

### 4.3 지적 3 — legacy source 무결성 변화가 더 이상 보고되지 않음

- 심각도: Medium residual risk
- Claude 판단: maintenance와 lifecycle audit가 `failures/` legacy source를 건너뛰므로 legacy 파일 변경·삭제는 보고되지 않는다.
- Codex 판정: 의도된 정책 경계로 수용
- 근거: legacy projection은 현재성 owner가 아니며 canonical Markdown이 현재 정본이라는 규칙
- 남은 위험: legacy history가 알려진 stale 상태인지 별도로 보여주는 기능은 없다.

### 4.4 긍정 확인 — public CLI가 legacy 생성기를 노출하지 않음

- 심각도: Low positive
- Claude 판단:
  - public `failure-import`와 `lifecycle-refresh-failure`는 `stored: false` 경로만 호출한다.
  - fanout을 만드는 `_import_legacy_failure_knowledge`는 private compatibility test용이며 CLI에서 접근할 수 없다.
- 판정: 실패 지식 범위에서 유효

### 4.5 긍정 확인 — 문서 지도 권위 축소

- 심각도: Low positive
- Claude 판단:
  - `DOCUMENT_MAP`은 owner와 category entry만 소유한다.
  - 전체 경로는 생성 inventory에 위임한다.
  - 정보 구조 문서가 실패 Markdown 직접 파싱·검색·검증을 설명한다.
- 판정: 문서 탐색 구조 범위에서 유효

### 4.6 긍정 확인 — 기존 안전 경계 유지

- 심각도: Informational
- Claude 판단: 삭제·이동·push·install·외부 쓰기와 보호 경로 승인 경계가 약화되지 않았다.
- 판정: 유효

### 4.7 긍정 확인 — 무증식 대표 경로 테스트

- 심각도: Informational
- Claude 판단:
  - public import 전후 record 파일 불변
  - refresh 전후 record와 lifecycle event 불변
  - 검색·scan에서 별도 projection 생성 없음
- 판정: 실패 지식 범위에서 유효

### 4.8 긍정 확인 — legacy 직접 ID 읽기 호환

- 심각도: Informational
- Claude 판단: 기존 legacy record를 ID로 직접 읽는 unit test와 refresh 뒤 기존 상태 불변 검사가 있다.
- 판정: 유효

## 5. 첫 보완 뒤 Claude challenge 결과

스킬 `challenge`가 정상 완료됐고 다음을 지적했다.

1. 추가 테스트가 현재 상태의 중복 없음만 확인하고 생성·개정 흐름에서 중복이 다시 생기는지 충분히 검증하지 않을 수 있다.
2. maintenance가 결과 상태만 확인하면 write-time 방지를 증명하지 못할 수 있다.
3. legacy ID가 기본 후보에 없다는 결과만으로 lifecycle 경계를 충분히 증명하지 못할 수 있다.

두 번째 지적 중 “maintenance가 중복을 정리해 결함을 숨길 수 있다”는 표현은 실제 구현과 맞지 않았다. maintenance scan은 read-only이며 중복을 자동 정리하지 않는다. 그러나 전체 흐름을 한 테스트에서 보여 달라는 핵심 요구는 보수적으로 수용했다.

## 6. challenge 반영 내용

결합 테스트를 다음 순서로 강화했다.

1. canonical `failures/case.md` 생성
2. private compatibility 경로로 legacy source/failure pair 1개 생성
3. legacy lifecycle state 등록
4. 모든 `data/records` filename과 모든 event JSONL bytes snapshot
5. public `import_failure_knowledge` 호출 후 `stored: false` 확인
6. canonical Markdown 개정
7. legacy ID로 refresh 호출 후 `stored: false` 확인
8. context filter·search가 개정된 canonical ref 하나만 반환하는지 확인
9. maintenance scan이 `ok`, drift 0, canonical 1인지 확인
10. record filename과 event bytes가 snapshot과 같은지 확인

보완 뒤 전체 99개 테스트와 maintenance scan·verify가 성공했다. 실제 저장소에서도 canonical 26개, legacy 39개, 기본 후보 26개, unique ref 26개, legacy ID 후보 0을 확인했다.

## 7. Claude에 전달하지 않은 핵심 요구

실제 review prompt의 다섯 질문은 다음에 한정됐다.

1. canonical failure Markdown 무증식
2. legacy 직접 읽기와 기본 검색 중복 방지
3. 에이전트 자율성 경계의 안전성
4. 문서 authority 축소
5. 테스트가 위 주장을 증명하는지

다음 질문은 전달하지 않았다.

> 프로젝트의 모든 데이터가 문서 기반인가?

> 에이전트의 모든 작업이 문서 정본을 읽고 그 문서를 갱신하는 흐름으로 강제되는가?

> `data/records/*.json`, lifecycle snapshot, work snapshot, event JSONL은 문서에서 재생성 가능한 파생물인가, 아니면 독립 정본인가?

> 문서 기반 원칙과 JSON 정본 구조가 충돌하지 않는가?

이 누락 때문에 Claude는 사용자의 실제 핵심 요구 위반을 발견할 기회를 받지 못했다. 이는 Claude의 검토 실패가 아니라 Codex가 검증 범위를 잘못 설정한 실패다.

## 8. 교차검증 결과의 유효 범위

| 주장 | 판정 |
|---|---|
| 새 실패 import·refresh가 projection/source/state/event를 만들지 않음 | 검증됨 |
| canonical과 legacy 공존 시 기본 failure 후보가 중복되지 않음 | 검증됨 |
| legacy 직접 ID 읽기 호환 | 검증됨 |
| 문서 지도와 생성 inventory 권위 분리 | 검증됨 |
| 보호·외부·파괴 경계 유지 | 검증됨 |
| 프로젝트의 모든 데이터가 문서 기반 | 검증하지 않음 |
| 모든 작업이 문서 정본 기반으로 진행 | 검증하지 않음 |
| 전체 사용자 요구 충족 | 검증하지 않음 |
| Stage 10 최종 점수 97/100 | 지지할 수 없음 |
| Stage 10 완료 | 지지할 수 없음 |

## 9. 최종 판정

이번 Claude 교차검증은 **실패 지식 fanout 개선에 대한 유효한 부분 검증**이다. 프로젝트 전체 문서 기반 데이터 운영에 대한 검증은 아니다.

따라서 다음 표현은 사용하면 안 된다.

- “Claude가 사용자 요구 전체를 검증했다.”
- “Claude 교차검증 결과 Stage 10이 완료됐다.”
- “Claude 검증을 포함해 97점을 확정했다.”

정확한 표현은 다음과 같다.

> Claude는 축소된 실패 지식·문서 탐색·안전 경계 범위를 검토했고 결합 테스트 공백을 찾아냈다. Codex는 그 공백을 보완했지만, 프로젝트 전체의 문서 기반 데이터 원칙은 prompt와 구현 모두에서 누락돼 아직 교차검증되지 않았다.

## 10. 재교차검증 필수 조건

1. 사용자의 문서 기반 데이터 원문을 검증 prompt 첫 항목에 그대로 포함한다.
2. 사용자 문장별 요구사항 → 규칙 → owner 문서 → 구현 → 테스트 → 게이트 추적표를 제공한다.
3. 모든 활성 데이터 유형과 소비 경로를 Claude가 읽을 수 있게 범위를 설정한다.
4. JSON·JSONL이 문서 파생물인지 독립 정본인지 각 유형별로 판정하게 한다.
5. Claude 지적을 Codex가 실제 파일·테스트로 재현한 뒤 전체 게이트를 반복한다.
6. 미검증 요구가 하나라도 있으면 점수와 완료 상태를 부여하지 않는다.

이 조건을 만족하는 재교차검증 전에는 이번 보고서의 부분 검증 결과를 전체 승인으로 확대해서는 안 된다.

## 11. 근거

- [이번 세션 작업 감사 보고서](2026-07-23_codex_이번_세션_작업_감사_보고서.md)
- [Stage 10 계획·실행 문서](../docs/build/stage-10-agent-autonomy-structure-optimization.md)
- [프로젝트 상시 규칙](../PROJECT_RULES.md)
- [실패 기록 규칙](../rules/failure-records.md)
- [문서 작업 규칙](../rules/document-work.md)
- [실패 fanout 사례](../failures/derived-failure-projection-fanout.md)

## 12. 10R-A 후속 교차검증

현재 10R-A의 판정 owner는 [Stage 10 계획·실행 문서](../docs/build/stage-10-agent-autonomy-structure-optimization.md)이며, 이 보고서는 외부 검증의 시점 증거만 소유한다.

- 대상: Stage 10 계획 문서와 `SESSION_HANDOFF.md`
- 모드: `delegate-to-claude` 읽기 전용 `verify`
- 결과: `FINAL VERDICT: PASS`
- findings: High 0, Medium 0, Low 1
- 확인: 이전 완료·97점 철회, 현재 점수 없음, 10R-A~10R-H의 단계별 Claude 선행 게이트, 미구현 migration·code 비완료 표시
- Low: 이 보고서와 Codex 세션 감사 보고서가 활성 owner처럼 남을 수 있는 위험
- Codex 판정: 수용. 두 보고서에 시점 증거·현재 owner 경계를 명시하고, Codex가 추가 발견한 세션 감사 §8의 오래된 현재 상태 문장을 교정했다.
- 보완 후 재검증: PASS, High 0, Medium 0. 첫 Low의 owner 중복 위험 해소 확인
- 재검증 Low: Stage 10 문서 상단 상태가 실제 10R-A 진행 수준보다 모호함
- Codex 후속 조치: 상단 상태에 10R-A 재검증 단계와 10R-B~10R-H 대기를 명시
- 마지막 최소 범위 확인: PASS, High 0, Medium 0. 명시적 게이트 상태 표기 Low는 Stage 10 행·상단·핸드오프 동시 갱신으로 해소
- Codex 기각: 결과가 실제 외부 호출이 아닐 수 있다는 추정성 위험 문구는 `delegate-to-claude` 실행 로그의 `status: completed`, `terminal_reason: completed`, 파일 변경 0과 충돌
- 현재 상태: 10R-A 성공 게이트 통과, 10R-B 요구·규칙 추적 진행 전
