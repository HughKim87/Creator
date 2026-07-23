# 테스트 fixture의 계약 구조 가정

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 06 결정 참조 수명주기 테스트
- 마지막 검증: 2026-07-24 Stage 10 test write root 격리 회귀
- 적용 범위: 구조화 payload fixture, 임시 프로젝트 fixture, 계약 회귀 테스트, 기존 record 유형 재사용

## 증상

수명주기 event가 승인된 decision을 참조하는 테스트에서 decision 생성이 필드 집합 검증 단계에서 거부됐다. Stage 10에서는 실패 문서 parser가 목록형 `확인된 원인` 절을 원문 그대로 반환하는데 테스트가 목록 기호 없는 평문을 기대해 55개 중 1개가 실패했다. 후속 test write 격리 보완에서는 임시 maintenance fixture가 프로젝트 문서와 자체 `.git`을 가진다는 계약을 확인하지 않고 두 표식을 active project 판별 기준으로 사용해 전체 120건 중 15건을 거부했다.

## 확인된 원인

- 새 테스트 fixture가 기존 Stage 05 decision 계약을 직접 확인하지 않고 승인 필드를 `approval` 중첩 객체로 추측했다.
- 실제 계약은 `requires_user_approval`, `approval_kind`, `approved_by`를 payload 최상위 필드로 소유한다.
- 테스트하려는 새 기능의 오류와 선행 유형 fixture의 계약 불일치를 분리하지 않으면 구현 결함으로 잘못 진단할 수 있다.
- Stage 10 회귀는 실제 fixture 본문과 parser 반환을 먼저 확인하지 않고 기대 문자열의 Markdown 목록 기호를 생략했다.
- test write root의 격리성은 fixture 안의 파일명이나 `.git` 존재 여부로 판별할 수 있다고 가정했다. 실제 maintenance fixture는 inventory·Git 경계를 검증하기 위해 `SESSION_HANDOFF.md`와 임시 Git 저장소를 의도적으로 만든다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 06 decision 참조 테스트 | 중첩 `approval` 객체가 exact field set 검증에서 거부돼 13개 수명주기 테스트 중 1개 오류 | 1 | Stage 05 decision 계약과 validator를 확인해 세 승인 필드를 최상위로 이동하고 13개 수명주기 테스트 전체 성공 |
| Stage 10 legacy failure 비증식 회귀 | `확인된 원인`이 `- 원인 A의 확정된 개정`으로 반환되지만 기대값을 `원인 A의 확정된 개정`으로 작성해 55개 중 1개 실패 | 1 | fixture 원문과 parser 출력 한 건을 대조해 기대값만 보정하고 관련 55개·전체 98개 회귀 성공 |
| Stage 10 test write root 격리 | 문서 marker 차단 뒤 `.git` 차단도 임시 maintenance Git fixture 15건을 `legacy_read_only`로 거부 | 같은 설계 가정의 보정 2 | fixture 구현을 직접 확인하고 marker heuristic을 제거했다. 시스템 임시 root와 실행 source project tree의 구조적 경계 및 exact root binding으로 교체해 전체 120건 성공 |

## 해결과 검증

- 새 단계 fixture를 만들기 전에 재사용하는 선행 record의 현재 계약과 유효 fixture를 확인한다.
- decision 승인 필드를 최상위 계약과 일치시킨 뒤 decision 생성, lifecycle 등록, decision 참조 review event, snapshot `last_decision_id` 단언이 모두 성공했다.
- 누적 전체 회귀 테스트에서도 선행 Stage 05 decision 흐름이 유지됨을 확인했다.
- Stage 10 보정은 구현을 바꾸지 않았고 record·event 비증식 단언을 포함한 관련 55개와 전체 98개 회귀가 통과했다.
- test capability는 시스템 임시 root 아래에서만 발급되고 exact root에 결합된다. 실행 source project tree와 그 하위, 다른 root로의 재사용은 거부하며 임시 Git fixture는 정상 동작한다.

## 재사용 규칙

- 새 기능 테스트가 여러 기존 유형을 조립할 때 각 선행 payload를 기억으로 재작성하지 말고 소유 계약이나 검증된 builder를 확인한다.
- exact field set 실패는 먼저 fixture 구조와 현재 schema·validator의 일치 여부를 비교한다.
- 테스트 대상 기능의 실행 전에 fixture 생성이 실패했다면 두 실패 범위를 분리해 진단한다.
- 반복되는 복합 fixture가 생기면 수동 payload 복제 대신 계약을 소유하는 테스트 helper 사용을 검토한다.
- fixture의 격리성을 파일명·문서 marker·VCS marker 같은 내용 휴리스틱으로 판정하지 않는다. 실제 fixture가 소유한 구조를 먼저 확인하고 실행 source tree·임시 root·capability binding처럼 서로 독립된 구조 경계를 사용한다.

## 근거

- [지식 유형 계약](../docs/KNOWLEDGE_TYPES_CONTRACT.md)
- [지식 수명주기 계약](../docs/KNOWLEDGE_LIFECYCLE_CONTRACT.md)
- [Stage 06 계획](../docs/build/stage-06-knowledge-lifecycle.md)
