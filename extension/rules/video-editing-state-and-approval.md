# 영상 편집 상태·승인 규칙

- 목적: 하나의 현재 편집본에서 작업을 재개하고 사용자 수정·승인의 유효 범위를 정확히 보존한다.
- 읽는 시점: 작업을 재개하거나 revision을 전환하고, 사용자 수정본·부분 수정 지시·source 변경을 반영할 때.
- 책임: 영상 편집 작업 에이전트가 현재 revision과 승인 범위를 유지하고 사용자가 수정·승인 결정을 소유한다.
- 상태: 활성 소비 도메인 규칙.
- 관련 권위: `PROJECT_RULES.md`의 단일 정보 owner 원칙과 영상 편집 workflow 계약이 상위 권위다.

### R11 — 사용자 수정본과 승인 범위

- 조건: 사용자가 직접 수정한 timeline이나 XML을 제공하거나 승인된 범위의 경계를 다시 편집한다.
- 행동: 사용자 수정 범위를 우선 보존하되 editorial 내용이 바뀌면 revision-level `entire_revision` 승인을 무효화한다. 사용자 평가에서 잘된 점·고칠 점·건드리지 않을 범위를 각각 `positive_lock / defect / untouched`로 기록하며, 다음 revision은 이를 baseline+delta 계약으로 사용한다. revision-level 승인은 v2에서 `artifact_id / approved_scope=entire_revision / source_manifest_hash / decision / invalidated_by / approved_by / checked_at / reviewed_editorial_fingerprint`로 추적하며, 결함·보존 범위는 feedback의 clip scope가 별도로 소유한다. 유효 판정은 authoritative owner bundle 안에서 current `artifact_id / source_manifest_hash / editorial_fingerprint`와 정확히 일치하는 결정만 모아 가장 최신 `checked_at`을 사용한다. 최신 결정이 `rejected`이면 revision은 `use_prohibited`, `superseded`이면 `historical`이어야 하고 둘 다 export를 차단한다. 최신 timestamp에 서로 다른 decision·invalidation·approver·scope 상태가 묶이면 `approval_decision_conflict`로 중단하며, 최신 approved 결정이라도 `invalidated_by`가 비어 있지 않으면 활성 승인이 아니다. `editorial_fingerprint`는 timeline version·source manifest·sequence·editorial evidence를 포함하되 feedback의 baseline payload pointer는 중립화하고, workflow profile·timeline ID·revision 상태·approval·validation·delivery는 제외한다. exact 기준본 owner가 없거나 current editorial fingerprint와 다르면 승인은 자동 무효다. delivery 형식만 바뀌는 것은 승인 범위를 바꾸지 않지만 editorial 내용이 하나라도 바뀌면 revision 전체 승인을 다시 받아야 한다.
- 예외: 최신 명시 지시와 사용자 수정본이 결과를 바꿀 정도로 충돌하면 자동 복원하지 않고 R02의 충돌 보고를 사용한다.
- 검증: self-reported `preserved` 표지가 아니라 exact baseline owner의 clip·event·microbeat·인접 경계와 새 revision을 실제 diff하고, source manifest, 아직 유효한 승인 범위와 positive lock을 대조한다. `approved_scope`가 literal `entire_revision`인지, authoritative bundle 안 exact 대상의 최신 결정만 활성화되는지, reject·supersede·invalidated approval·동시각 충돌이 각각 정해진 revision 상태와 export 차단으로 이어지는지 확인한다. bundle 밖 후속 결정을 탐지했다고 주장하지 않는다. 사용자가 긍정한 특성이 이유 없이 사라진 경우 새 revision을 전달하지 않는다.

### R13 — 현재 편집본 checkpoint와 이전 revision 동결

- 조건: 새 revision이 생성·채택되거나 중단된 편집 작업을 재개한다.
- 행동: v2 revision의 `working_candidate / current / approved / use_prohibited / historical`을 구분하고 한 state owner에서 `state_owner_id / source_manifest / editorial_fingerprint / payload_fingerprint / task_payload_fingerprint / validation / checked_at / supersedes`를 유지한다. XML 생성 가능한 working candidate를 사용자 채택 전 current로 승격하지 않는다. `current` 또는 `approved` revision은 최신 활성 `entire_revision` 사용자 승인을 가진 경우 후속 delta의 exact protected baseline이 될 수 있다. 소비 revision의 `checked_at`은 referenced calibration과 baseline의 latest approval time보다 이전일 수 없다. exact 대상의 최신 사용자 rejection은 revision을 `use_prohibited`, superseded 결정은 `historical`로 동결하며 둘 다 새 revision의 편집 source나 export에 사용하지 않는다. 사용자 결함은 변하는 timeline 시각만으로 남기지 않고 source anchor·사건 ID·증상·필수 복원 기능으로 기록해 후속 revision의 회귀 목록으로 유지한다. 이전 revision은 읽기 전용으로 동결한다.
- 예외: 사용자가 exact 비교·복구·분기 목적과 대상을 지정하면 이전 revision을 별도 작업 입력으로 사용할 수 있다.
- 검증: 후속 편집과 XML이 같은 활성 revision artifact와 exact task state를 참조하는지 확인한다. XML 후보는 `working_candidate`, 사용자 채택본은 `current` 또는 `approved`여야 하며, `working_candidate` XML 생성만으로 current·approved 승격이 발생하지 않는다. baseline status와 latest active whole-revision approval, 소비 revision chronology를 actual owner bundle과 대조한다. 이전 revision의 content hash가 바뀌지 않았고, 전달 전 모든 미해결 결함 ID에 `해결 / 의도적 보류 / 재현 불가` 판정과 근거가 있으며, 반려본을 source로 참조한 항목은 0개인지 확인한다.

### R14 — 상태 owner 충돌 중단

- 조건: handoff, 작업 brief, timeline, 생성기 metadata가 서로 다른 current artifact나 source fingerprint를 가리킨다.
- 행동: handoff와 v2 `revision.state_owner_id`, exact baseline owner reference, `editorial_fingerprint`, `payload_fingerprint`, `task_payload_fingerprint`, source manifest의 실제 주장을 비교해 충돌을 계산한다. `editorial_fingerprint`는 편집 동일성을 소유한다. `payload_fingerprint`는 identity·profile·source·sequence·editorial evidence·revision을 결속하고 approval·validation·delivery를 제외한다. `task_payload_fingerprint`는 이 payload fingerprint에 approval과 validation을 더해 exact reference state를 결속하며, `delivery_fingerprint`는 task payload fingerprint와 delivery를 결속한다. baseline/calibration 소비 pointer는 referenced task fingerprint로 resolve하고 calibration artifact의 self-approval만 자기 payload fingerprint를 사용한다. direct payload와 authoritative owner/resolver bundle은 두 fingerprint를 모두 색인한 registry에서 transitive하게 해소하며 dangling·cycle 또는 같은 payload identity에 서로 다른 state object가 있으면 상태 충돌로 중단한다. validator의 latest 판정은 제공 bundle 안에서만 유효하므로 caller는 owner bundle을 필수 입력으로 제공하고 숨겨진 후속 상태가 없다는 provenance·완전성을 별도로 증명한다. payload 안의 self-reported boolean으로 충돌 없음 상태를 선언하지 않는다. 충돌이 있으면 `state_owner_conflict` 또는 해당 reference error로 편집·승인·XML 생성을 중단하고 하나의 owner를 복구한다. 역사·계획·보고서는 첫 10줄 안에 literal `active / historical / superseded`와 만료 조건을 표시하고 current owner가 아닌 문서는 다음 행동이나 후보 상태를 독립적으로 소유하지 않는다. handoff에는 commit 뒤 즉시 낡는 HEAD·dirty 목록 같은 동적 Git 상태를 복제하지 않는다.
- 예외: 명시적인 병렬 variant 작업이면 각 variant의 owner와 목적을 분리하고 서로의 승인을 공유하지 않는다.
- 검증: 재개 전 모든 활성 참조가 같은 artifact, baseline owner, editorial fingerprint, task state와 source manifest를 가리키며, authoritative bundle의 transitive 해소 뒤 dangling·cycle·ambiguous reference와 owner 충돌 수가 모두 0인지 확인한다. payload·task·delivery fingerprint의 소유 필드가 뒤섞이지 않았고, reference 결과가 bundle-relative임을 명시했는지도 확인한다. current owner 밖의 active 후보·다음 행동 주장, literal 상태·만료 표시 없는 역사 지시, handoff의 동적 Git snapshot이 각각 0개인지 확인한다.

## 재현 사례

| ID | 상황 | 기대 판정 |
|---|---|---|
| TC11 | 승인 revision의 일부 clip을 사용자가 직접 수정함 | revision 전체 승인을 무효화하고, feedback의 `positive_lock / defect / untouched` 범위는 새 baseline+delta 검증에 유지한다 |
| TC13 | 새 revision이 current로 채택됨 | checkpoint를 즉시 갱신하고 이전 revision은 읽기 전용으로 둔다 |
| TC14 | 두 활성 문서가 서로 다른 current revision을 가리킴 | `state_owner_conflict`로 생성과 완료 보고를 중단한다 |
