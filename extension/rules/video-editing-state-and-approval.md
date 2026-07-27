# 영상 편집 상태·승인 규칙

- Purpose: 하나의 현재 편집본에서 작업을 재개하고 사용자 수정·승인의 유효 범위를 정확히 보존한다.
- Read when: 작업을 재개하거나 revision을 전환하고, 사용자 수정본·부분 승인·source 변경을 반영할 때.
- Authority: `PROJECT_RULES.md`의 단일 정보 owner 원칙과 영상 편집 workflow 계약이 상위 권위다.

### R11 — 사용자 수정본과 승인 범위

- 조건: 사용자가 직접 수정한 timeline이나 XML을 제공하거나 승인된 범위의 경계를 다시 편집한다.
- 행동: 사용자 수정 범위를 우선 보존하고 그 범위와 인접 경계의 이전 승인을 무효화한다. 승인은 최소한 `artifact_id / approved_scope / source_manifest_hash / decision / invalidated_by`로 추적한다.
- 예외: 최신 명시 지시와 사용자 수정본이 결과를 바꿀 정도로 충돌하면 자동 복원하지 않고 R02의 충돌 보고를 사용한다.
- 검증: 변경된 clip, 인접 경계, source fingerprint, 아직 유효한 승인 범위를 diff로 대조한다.

### R13 — 현재 편집본 checkpoint와 이전 revision 동결

- 조건: 새 revision이 생성·채택되거나 중단된 편집 작업을 재개한다.
- 행동: 한 owner에서 `current_artifact_id / source_manifest_hash / validation_status / checked_at / supersedes`를 갱신하고 그 revision만 후속 편집 입력으로 사용한다. 이전 revision은 읽기 전용으로 동결한다.
- 예외: 사용자가 exact 비교·복구·분기 목적과 대상을 지정하면 이전 revision을 별도 작업 입력으로 사용할 수 있다.
- 검증: 후속 편집과 XML이 같은 current artifact를 참조하고, 이전 revision의 content hash가 바뀌지 않았는지 확인한다.

### R14 — 상태 owner 충돌 중단

- 조건: handoff, 작업 brief, timeline, 생성기 metadata가 서로 다른 current artifact나 source fingerprint를 가리킨다.
- 행동: `state_owner_conflict`로 편집·승인·XML 생성을 중단하고, 각 주장과 마지막 검증 시점을 비교해 하나의 current owner를 복구한다.
- 예외: 명시적인 병렬 variant 작업이면 각 variant의 owner와 목적을 분리하고 서로의 승인을 공유하지 않는다.
- 검증: 재개 전 모든 활성 참조가 같은 artifact와 source fingerprint를 가리키며 충돌 수가 0인지 확인한다.

## 재현 사례

| ID | 상황 | 기대 판정 |
|---|---|---|
| TC11 | 승인 구간을 사용자가 직접 수정함 | 수정 clip과 인접 경계의 이전 승인만 무효화하고 독립 범위 승인은 유지한다 |
| TC13 | 새 revision이 current로 채택됨 | checkpoint를 즉시 갱신하고 이전 revision은 읽기 전용으로 둔다 |
| TC14 | 두 활성 문서가 서로 다른 current revision을 가리킴 | `state_owner_conflict`로 생성과 완료 보고를 중단한다 |
