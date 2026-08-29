# Creator 백룸 영상 편집 현재 상태

- 목적: 새 세션이 백룸 편집을 검증된 상태에서 재개하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 다음.
- 책임: 에이전트는 근거·revision·검증을 유지하고 사용자는 방향·채택·Git 작업을 결정한다.
- 상태: v2 규칙·schema·runtime·회귀 보강 완료. 영상 current / approved / final 후보는 없음.
- 관련 권위: 시작 정책과 `extension/rules/` 영상 편집 owner.
- handoff mode: `same-workspace`.
- uncommitted dependency: 없음.

## 현재 단계

목표는 v2로 microcut·인과·자연스러운 A/V 경계를 만족하는 CS6 XML이다. 고정 길이는 없다. 다음은 calibration XML과 사용자 방향 검수다.

- 활성 전체 설계: 없음.
- 활성 단계 설계: 없음.

## 입력과 보호 경계

승인된 정확한 입력:

- `inputs/2026-06-30 00-23-03.mp4`: 원본 영상·음성.
- `inputs/2026-06-30 00-23-03.srt`: 발화·의미 경계 보조.
- `inputs/2026-06-30 00-23-03.full-edit-v18.xml`: 장면 위치·CS6 구조 참고. 승인본이나 기준본 아님.

그 밖의 `inputs`, `outputs`, `extension/inputs`, `extension/outputs`는 정확한 경로·목적 승인 없이 열거·읽기 금지다. 기존 결과를 덮어쓰지 않는다.

## 검증된 구현 상태

- `payload_fingerprint`는 content/revision, `task_payload_fingerprint`는 payload+approval+validation, `delivery_fingerprint`는 task+delivery를 결속한다.
- calibration/baseline은 actual transitive task-state reference closure로 검증한다. dangling·cycle·같은 payload의 상충 state·malformed/unused reference는 차단한다.
- revision 승인은 literal `entire_revision`이며 최신 반려·대체·무효화·동시각 충돌과 calibration/baseline 승인 이전 revision을 차단한다. baseline은 latest whole-revision 승인이 있는 `current` 또는 `approved`다.
- retained clip은 event와 microbeat 각각 하나에만 귀속된다. A/B/A 교차, 선언된 인과 anchor 누락, 미완료 microbeat·경계 검수를 XML 전에 차단한다. 창작상 과삭제 여부는 정상 속도 의미 검수가 별도로 판정한다.
- guarded writer는 absolute canonical source/output, exact source hash·size, Windows mandatory source handle, publish 직전 drift, atomic no-clobber를 검사하며 실패 시 XML·임시 파일을 남기지 않는다.
- v1 직접 XML/rule gate는 금지한다. `migrate-v1`은 event 경계 clip을 결정적으로 분할하고 승인·boundary를 pending, 의미 검수를 `not_run`으로 reset한다.
- reference bundle은 64개로 제한한다. authoritative bundle 밖에 숨겨진 후속 state는 runtime이 발견할 수 없고 저장소 내 canonical owner resolver도 아직 없으므로, caller가 최신·완전한 bundle을 제공해야 한다. 검증 결과는 bundle-relative다.

## 직전 게이트

- `pass`: `python -B scripts/verify.py` — 216 tests와 전체 gate 통과. v2 adversarial 40/40 포함.
- Core·main worktree 변경 없음. 비보호 임시 파일 0개.

## 승인 상태

- v20-r8 / v21-r1 / v21-r2는 인과 과삭제·내부 경계 누락·긴 통편집으로 `use_prohibited`; 재사용 금지.
- 승인됨: 위 세 입력의 백룸 편집·source 검증 사용과 새 calibration XML 생성.
- 별도 승인 필요: 전체 편집 확장, current·approved·final 승격, push, 삭제.

## 차단

- 구현 차단 없음. 사용자 calibration 지시만 남았다.

## 알려진 위험

- 합성 검증은 실제 Premiere import·정상 속도 의미 검수·사용자 승인을 대신하지 않는다.
- canonical state-owner resolver는 아직 구현되지 않았다. dependency가 있는 payload의 latest 판정은 caller가 제공한 64개 이하 bundle에 상대적이다.

## 재개 checkpoint

원본 `36:22.380~38:23.500`의 괴물 발견 → 추격 → 안전실 진입 → 문 차단 → 재확인 → 후퇴 → 문 규칙 이해를 calibration으로 사용한다. 사건 anchor와 필요한 무음은 유지하고 혼잣말·반복·죽은 이동은 줄인다. J/L cut·action/movement match·source handle은 문제별로만 적용한다.

## 첫 다음 행동

1. 사용자 지시 후 위 checkpoint의 v2 calibration을 새 non-overwrite XML로 만든다.
2. Premiere 정상 속도 검수와 사용자 방향 승인 전에는 전체 편집으로 확장하지 않는다.
3. push는 별도 사용자 지시를 기다린다.

## 시작 prompt

첫 다음 행동부터 재개한다.
