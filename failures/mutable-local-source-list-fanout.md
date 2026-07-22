# 변경된 로컬 출처 한 건의 전체 목록 실패 전파

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 05 실제 failure projection 후 source 전체 검증
- 마지막 검증: 2026-07-23
- 적용 범위: hash가 고정된 로컬 source record의 역사 조회와 현재 locator 재검증

## 증상

05A에서 등록한 `INFORMATION_ARCHITECTURE.md`가 같은 단계 문서화 중 변경된 뒤 `source-list`가 `source_integrity` 오류로 전체 실패했다. failure projection 20건은 성공했지만 source 총개수를 확인할 수 없었다.

## 확인된 원인

과거 시점의 관찰 record를 읽는 기능과 locator의 현재 bytes가 당시 hash와 같은지 재검증하는 기능을 같은 기본 동작으로 묶었다. 한 source의 정상적인 후속 변경이 무관한 모든 source의 역사 조회까지 차단했다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 05 실제 source 전체 목록 | 20개 failure projection 성공 뒤 기존 로컬 source hash 불일치로 source-list 실패 | 1 | show/list는 저장 관찰을 검증해 반환하고 explicit source-verify만 현재 bytes 불일치를 거부하도록 책임 분리 |

## 해결과 검증

- source show/list는 common-record와 source payload의 저장 무결성을 검증한다.
- source verify는 로컬 locator 존재와 현재 SHA-256 일치를 별도로 검사한다.
- knowledge·decision의 역사 조회는 당시 source 참조를 유지한다.
- failure projection은 현재 Markdown 정본과의 일치가 의미 자체이므로 계속 강제 검증한다.

## 재사용 규칙

- 불변 관찰 record의 조회와 가변 외부 대상의 현재 상태 검증을 같은 성공 조건으로 묶지 않는다.
- 목록 한 항목의 외부 drift가 무관한 역사 record 탐색 전체를 차단하지 않게 한다.
- 현재성·대체·폐기 판단은 명시적 수명주기 단계가 소유하게 하고 조회 시 암묵적으로 변경하지 않는다.

## 근거

- [지식 유형 계약](../docs/KNOWLEDGE_TYPES_CONTRACT.md)
- [KnowledgeService](../src/file_data/knowledge.py)
- [Stage 05 계획](../docs/build/stage-05-knowledge-types.md)
