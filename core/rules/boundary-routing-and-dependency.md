# Boundary Routing and Dependency Rules

- Purpose: keep foundation and domain work independently navigable while making every cross-boundary dependency explicit, classified, and testable.
- Read when: adding, changing, removing, or auditing a cross-boundary document link, rule route, schema reference, runtime import, storage path, artifact owner, or boundary test.
- Authority: `PROJECT_RULES.md` is higher authority; the exact active owner of the affected interface or domain remains responsible for its content.

## BND01 — 상위 라우터를 통한 읽기

- 조건: 작업이 foundation 영역과 domain extension 영역의 문서·규칙·현재 상태를 함께 읽거나 연결해야 한다.
- 행동: 사용자의 진입점에서 `PROJECT_RULES.md`를 먼저 읽고, 거기서 선택한 foundation rule과 extension entry point·active owner만 읽는다. foundation과 extension 문서가 서로의 규칙이나 owner를 직접 라우팅하지 않게 한다.
- 예외: `PROJECT_RULES.md`와 root 사용자 안내는 양쪽 영역을 연결할 수 있다. 테스트는 경계를 검사할 수 있지만 active owner나 routing source가 될 수 없다.
- 검증: active foundation·extension Markdown 사이의 직접 navigation link와 rule route가 0개이고, 각 active rule의 상위 route가 정확히 하나인지 확인한다.

## BND02 — 참조 유형 분리

- 조건: 양쪽 영역 사이의 참조가 필요해 보인다.
- 행동: 참조를 `navigation`, `rule-routing`, `machine-schema`, `runtime-api`, `storage`, `test-only` 중 하나로 분류한다. navigation과 rule-routing은 상위 router로 이동시키고, machine/runtime/storage 참조는 interface owner와 compatibility gate를 별도로 확인한다.
- 예외: 승인된 foundation runtime API를 extension이 사용하는 일방향 의존은 사용자-facing routing link와 구분해 유지할 수 있다. foundation이 domain extension을 import하거나 소유하는 방향은 허용하지 않는다.
- 검증: 직접 참조가 필요한 이유·owner·방향·재현 검사가 기록되어 있고, navigation link를 runtime dependency라는 이름으로 숨기지 않았는지 확인한다.

## BND03 — 새 경계 참조의 생성 gate

- 조건: 기존 owner로 표현되지 않는 cross-boundary link, schema, import, storage path, 또는 test가 필요하다.
- 행동: 기존 interface와 router를 검색하고, 새 참조의 trigger·owner·수명·삭제/대체 경로를 정한다. shared schema나 API가 양쪽에서 필요하면 양쪽 중 한쪽에 복사하지 말고 중립 interface owner를 검토한다.
- 예외: 단일 영상·단일 보고서·단일 파일의 사실은 경계 interface나 active rule로 승격하지 않고 해당 작업 owner에 둔다.
- 검증: 새 참조가 이 규칙의 분류에 맞고, 상위 router·active owner·회귀 테스트·문서 무결성 검사에 반영되었는지 확인한다.

## BND04 — 경계 변경의 읽기 순서

- 조건: cross-boundary 변경을 구현하거나 완료 판정을 내린다.
- 행동: `PROJECT_RULES.md` → 현재 상태 owner → 이 boundary rule → affected foundation rule/interface → affected extension owner 순서로 읽고, 각 문서는 EOF까지 한 번만 읽는다.
- 예외: protected data는 exact 대상·목적 승인 없이는 읽지 않는다. machine schema만 검증하는 경우에도 해당 schema의 owner와 compatibility test만 읽는다.
- 검증: 변경한 쪽의 direct reference scan, 반대쪽의 orphan route scan, 관련 Core/Extension 회귀를 모두 실행한다.

## BND05 — 새 도구 경로의 최소 성공 호출

- 조건: 승인된 작업에 새 외부 tool, API, agent, CLI, MCP server 또는 interface route를 연결하려 한다.
- 행동: 실제 연결을 채택하기 전에 최소 1회의 read-only 또는 별도 승인된 성공 호출로 auth, 호출 경로, 옵션명, 출력 형태, 설치 버전 동작, 실패 비용을 확인한다. 작업에 필요하지 않은 새 경로는 추가하지 않는다.
- 예외: 이미 검증된 동일 route·버전·호출 계약을 재사용할 때는 기존 검증 기록을 직접 확인하고 중복 호출을 만들지 않는다. 상태 변경 호출은 이 규칙만으로 승인되지 않는다.
- 검증: 최소 호출의 대상·시점·결과와 route owner를 기록하고, 실패·권한 부족·출력 계약 불일치를 성공으로 보고하거나 active route로 남기지 않는다.
