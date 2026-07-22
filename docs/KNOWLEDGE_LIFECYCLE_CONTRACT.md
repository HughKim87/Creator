# 지식 수명주기 계약과 사용법

- 목적: Stage 05 지식 record의 원본을 덮어쓰지 않고 검토·현재 채택·충돌·대체·거부·폐기 상태와 이유를 추적한다.
- 읽는 시점: 지식의 현재 사용 가능 여부를 판단하거나 source drift, 정본 개정, 충돌, 대체를 처리할 때.
- 책임: `data/events/lifecycle_events.jsonl`이 전이 정본, `lifecycle_state` record가 재구축 가능한 현재 projection, Stage 05 record가 당시 내용의 원본을 소유한다.
- 상태: Stage 06 활성 계약.
- 선행 계약: [지식 유형 계약](KNOWLEDGE_TYPES_CONTRACT.md), [공통 기록 I/O](RECORD_IO_CONTRACT.md).

## 상태와 의미

| 상태 | 의미 | 기본 현재 목록 |
|---|---|---|
| `candidate` | 아직 현재 채택 승인을 받지 않은 후보 | 제외 |
| `current` | 검토 근거와 승인 경계가 충족된 현재 사용 가능 record | 포함 |
| `review_required` | source drift·검증 실패·충돌·사용자 요청으로 재검토가 필요한 record | 제외 |
| `superseded` | 새 record가 같은 책임을 대체한 과거 record | 제외, 원본·이력 보존 |
| `rejected` | 검토 결과 채택하지 않은 record | 제외, 원본·이력 보존 |
| `retired` | 한때 current였으나 더 이상 사용하지 않는 record | 제외, 원본·이력 보존 |

`reviewed`는 현재 상태로 두지 않는다. 누가 무엇을 근거로 검토해 어떤 결과를 냈는지는 추가 전용 event에 남고 결과 상태가 현재 projection에 반영된다.

## 대상과 초기 등록

대상 유형은 `source`, `knowledge`, `decision`, `failure_knowledge`다. Stage 05에서 이미 검증된 source·knowledge는 `current`, 관찰·후보 상태는 `candidate`, 승인 근거가 있는 decision과 해결된 failure projection은 `current`로 등록한다.

- 기존 payload는 수정하지 않는다.
- 한 대상에는 하나의 lifecycle snapshot만 존재한다.
- 초기 `current` 등록도 `user` 또는 `standing_policy` 승인 증거가 필요하다.
- 일괄 등록은 아직 lifecycle이 없는 현재 Stage 05 record만 처리하며 반복 실행해도 새 event를 만들지 않는다.

## 전이와 승인 경계

| action | 허용 전이 | 승인 경계 |
|---|---|---|
| `request_review` | candidate/current → review_required | 사건을 관찰한 승인 범위 내 agent 가능 |
| `approve_current` | candidate/review_required → current | user 또는 standing_policy 필수 |
| `declare_conflict` | candidate/current/review_required → review_required | agent 가능, 같은 유형의 양쪽 record에 관계와 검토 필요를 기록 |
| `supersede` | candidate/current/review_required → superseded | user 또는 standing_policy, 같은 유형의 current replacement 필수 |
| `reject` | candidate/review_required → rejected | user 또는 standing_policy 필수 |
| `retire` | current/review_required → retired | user 또는 standing_policy 필수 |

`superseded`, `rejected`, `retired`는 terminal이다. 되살리지 않고 필요한 내용을 새 record로 생성해 새 lifecycle을 시작한다. 모든 전이는 기대 snapshot hash를 요구해 오래된 판단의 덮어쓰기를 거부한다.

## 검토·개정·충돌 보존

- event는 대상, 이전·다음 상태, actor, action, 이유, 승인 종류, 확인 source, 관련 current decision, 충돌 대상, replacement를 함께 보존한다.
- 개정은 기존 payload update가 아니라 새 Stage 05 record 생성과 `supersede` 관계로 표현한다.
- 충돌은 같은 유형의 record를 모두 보존하고 양쪽을 `review_required`로 만든다. 자동 병합하거나 임의로 하나를 current로 고르지 않는다.
- current 선택은 `lifecycle-current`가 담당하며 candidate·review_required·terminal record를 기본 결과에서 제외한다.
- 삭제 명령은 제공하지 않는다. 원본, event, snapshot은 프로젝트 보존 정책과 Git 이력 안에서 계속 유지한다.

## 사건 기반 검토 트리거

`lifecycle-audit`는 현재 프로젝트 bytes만 읽어 다음 실제 사건을 검출한다.

- local source의 저장 hash와 현재 bytes 불일치 또는 소실
- failure Markdown 정본과 hash 고정 projection 불일치
- drift source를 참조하는 knowledge·decision·failure projection

검출된 활성 record는 `review_required`가 되며 이유와 관련 source가 event에 남는다. 이미 review_required인 대상에는 중복 event를 추가하지 않는다. 주기 일정, LLM 자동 승인, 근거 없는 자동 병합은 이 단계에 없다.

## 실패 projection 개정

실패 Markdown은 계속 사람용 정본이다. 정본이 바뀌면 기존 source와 `failure_knowledge`를 수정하지 않고 다음 순서로 개정한다.

1. 현재 Markdown hash로 새 source와 새 projection을 만든다.
2. 둘을 승인된 `current`로 등록한다.
3. 옛 source와 projection을 새 record로 `superseded` 처리한다.
4. 옛 record와 event를 보존하고 current 목록에는 새 projection만 표시한다.

이 동작은 수명주기 개정이며 Stage 08의 자동 유지보수·일괄 재생성과 구분한다.

## 승인된 진입점

- Library: `file_data.LifecycleService`
- 등록·조회: `lifecycle-register`, `lifecycle-register-existing`, `lifecycle-show`, `lifecycle-list`
- 현재 선택·이력: `lifecycle-current`, `lifecycle-history`
- 전이·복구: `lifecycle-transition`, `lifecycle-rebuild`
- 사건 처리: `lifecycle-audit`, `lifecycle-refresh-failure`

구조 계약은 `schemas/lifecycle-event-payload-v1.schema.json`과 `schemas/lifecycle-state-payload-v1.schema.json`이다. Python 검증기는 허용 전이, 승인 종류, 참조 record 유형, replacement 현재 상태 같은 교차 조건을 추가로 검사한다.

## 제외와 후속

- current record의 직접 선택·구조화 필터·제한된 컨텍스트 package는 [Stage 07 계약](CONTEXT_PACKAGE_CONTRACT.md)이 소유한다.
- 주기 실행·중복 탐지·비용 관측·일괄 재생성은 Stage 08 범위다.
- 도메인 전용 상태와 영상 제작 연결은 Stage 09 범위다.
- 보호 데이터, `backup/` 전체 이관, 사용자 승인 없는 삭제는 계속 제외한다.
