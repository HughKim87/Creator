# 영상 편집 입력·지시 규칙

- 목적: 영상 편집의 exact 범위와 사용자의 실제 결과 요구를 고정하고 불필요한 재확인을 줄인다.
- 읽는 시점: 새 편집을 시작하거나 입력 범위를 바꾸고, 사용자 지시·피드백·수치를 해석할 때.
- 책임: 영상 편집 작업 에이전트가 범위·지시 판정을 유지하고 사용자가 결과와 보호 데이터 접근을 승인한다.
- 상태: 활성 소비 도메인 규칙.
- 관련 권위: `PROJECT_RULES.md`와 `extension/docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md`가 상위 권위다.

### R01 — 증상·방법·수치 분리

- 조건: 사용자가 불편한 결과와 함께 해결 방법이나 길이·비율을 말한다.
- 행동: 발언을 `증상`, `제안 방법`, `수치`로 나누고 증상을 결과 계약으로 삼는다. 방법은 후보로 비교하며 수치는 `[사용자확정]`, `[calibration]`, `[증상]`으로 분류한다. 원문의 구두점·표 머리글·수식어를 보존해 시간값이 source 좌표인지 편집 timeline 좌표인지, 한 점인지 범위인지, 단위가 초·프레임·분 중 무엇인지, 표현이 권장·예시인지 금지·필수인지, 길이가 예상 예산인지 hard cap인지 구분하며 서로 자동 변환하지 않는다. 한 해석이 결과를 크게 바꾸는 모호한 시간값은 실행 전에 `좌표계 / 단위 / 적용 범위`로 정규화해 사용자에게 되짚고, 이미 같은 대화에서 교정된 표기는 그 교정을 우선한다. 정규화한 시간 지시와 사용자 교정은 editorial evidence로 보존해 `editorial_fingerprint`에 결속한다. 사용자 확정이 없는 측정 길이·과거 결과 길이·평균 컷 길이는 목표·상한·합격 기준으로 사용하지 않는다.
- 예외: 사용자가 수치를 명시적으로 합격 기준으로 확정하면 `[사용자확정]`으로 적용한다.
- 검증: 다른 방법으로도 증상을 해결할 수 있는지, 수치를 제거해도 목표가 같은지, 원문이 hard constraint를 실제로 명시하는지 설명한다. 실행 기록에 정규화한 좌표계·단위가 있고 사용자 교정과 충돌하지 않는지, source에 없는 coverage·비율·상한을 자체 합격 지표로 추가하지 않았는지 확인한다.

### R02 — 최신 지시와 충돌 경계

- 조건: 새 지시가 이전 계획·브리프·수정본과 다르게 보인다.
- 행동: 결과가 명확한 최신 지시를 우선 적용한다.
- 예외: 보호 경계, 명시된 스파인 기능, 사용자 수정본, 되돌리기 어려운 결과와 실질적으로 충돌하면 `충돌 지점 / 잃는 것 / 최소 선택지`를 먼저 보고한다.
- 검증: 적용한 지시와 보류한 충돌을 작업 상태에서 한 문장으로 구분한다.

### R03 — 단계 계획과 보호 데이터

- 조건: 원본·자막·파생 결과를 새로 열거나 다음 편집 단계에 진입한다.
- 행동: exact 항목·목적·산출물·종료 조건을 먼저 확정하고 지정 범위만 접근한다. 산출물 계약에는 종류·개수·연속 재생 단위·허용 sidecar를 포함하며, `XML 하나`처럼 사용자가 전달 형식을 한정하면 내부 재현 자료를 영구 전달물로 자동 추가하지 않는다. 편집을 시작할 때 `video-edit-timeline-v2` 하나에 작업 profile, 정규화한 시간 좌표, exact source byte hash·size, sequence, 사건·microbeat·피드백 근거, revision·승인·검수와 delivery를 기록한다. 기존 문법이나 기준본을 사용할 때는 `baseline_reference` 또는 `calibration_reference`에 exact evidence owner, artifact ID, editorial fingerprint, source manifest fingerprint와 사용자 결정 근거를 함께 고정하며 임의 hash나 self-reported 승인 표지만 받지 않는다. 참조가 있는 작업은 authoritative latest owner/resolver가 제공한 payload bundle을 필수 입력으로 받고, direct reference와 반복 가능한 bundle을 `payload_fingerprint`와 `task_payload_fingerprint` 양쪽으로 색인한 graph에서 재귀 해소한다. `new_full_edit`·`approved_delta`가 소비하는 calibration pointer와 baseline pointer는 referenced task payload fingerprint를 가리키고, calibration artifact 자신의 approval만 자기 payload fingerprint를 가리킨다. 선언된 참조 누락, 순환, 같은 payload identity에 서로 다른 state object가 대응하는 모호성은 차단한다. validator는 제공된 bundle 밖에서 숨겨진 후속 승인·반려·대체 상태를 발견할 수 없으므로 caller는 bundle의 owner·최신성·완전성을 증명하고 bundle-relative 결과를 absolute latest로 보고하지 않는다. `new_full_edit`, `calibration`, `approved_delta`, `format_regeneration` 중 실제 작업에 맞는 최소 profile만 적용한다. `calibration.required`는 유효한 사용자 승인 문법이 없거나 최신 교정이 그 문법을 무효화했을 때만 true이며, false 또는 `not_required`는 `artifact_id / approved_payload_fingerprint / approved_by=user / approval_evidence / checked_at`가 모두 있고 actual calibration task state의 동일 source·approved revision·semantic pass·`entire_revision` 사용자 승인과 일치할 때만 허용한다. 이 checked_at은 referenced calibration의 최신 활성 whole-revision 승인 시각과 같고 소비 revision은 그 승인보다 이전일 수 없다. `format_regeneration`은 exact `current` 또는 `approved` 기준본의 editorial fingerprint를 보존하고 delivery만 바꾼다. 창작 방향이 정해지지 않은 `new_full_edit`에서만 방향을 고정하지 않은 1차 내용 분석을 먼저 수행한 뒤 실제 근거가 다른 최대 3개의 방향을 비교한다. 에이전트 추천은 사용자 방향 승인으로 간주하지 않는다.
- 예외: 같은 승인 계획 안에서 exact 범위가 변하지 않는 연속 작업은 다시 묻지 않는다.
- 검증: 접근 항목과 생성 항목이 승인 목록의 부분집합인지 확인하고, v2 `delivery`와 실제 XML 경로·profile·개수가 일치하며 task payload가 사용자 전달 sidecar로 새지 않는지 대조한다. baseline/calibration reference는 authoritative owner bundle의 exact task state·artifact·editorial fingerprint·source manifest·latest `entire_revision` 결정·승인 시각과 재귀 교차검증하고, dangling·cycle·ambiguous reference가 하나라도 있으면 차단한다. `not_required`와 소비 revision chronology를 actual reference와 대조하며, owner bundle provenance나 완전성을 증명하지 못하면 latest 승인 검증을 통과로 높이지 않는다. required calibration 미승인 상태의 전체 확장과 editorial fingerprint가 달라진 format regeneration도 차단한다. 각 방향이 원본 사건·반응·공간 근거에 연결되는지와 사용자의 최종 선택·다음 단계가 구분되어 있는지 확인한다. 근거가 부족하면 3개를 억지로 채우지 않는다.

## 재현 사례

| ID | 상황 | 기대 판정 |
|---|---|---|
| TC01 | 사용자가 지루한 구간을 특정 길이로 줄이는 방법을 예시함 | 지루함을 계약으로 받고 길이는 명시 확정 전 `[증상]`으로 둔다 |
| TC02 | 새 지시가 오래된 계획과 다르지만 보호·결과 충돌은 없음 | 최신 지시를 적용하고 재확인하지 않는다 |
| TC03 | exact 원본 지정 없이 다음 단계 진행 요청 | 항목·목적을 확인하기 전 보호 데이터를 열지 않는다 |
