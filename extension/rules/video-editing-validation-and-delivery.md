# 영상 편집 검증·전달 규칙

- 목적: 구조·미디어·앱·사용자 검증을 구분하고 실제로 확인한 수준보다 결과를 높여 보고하지 않는다.
- 읽는 시점: validator를 설계·실행하거나 timeline·XML·검토본의 성공과 전달 상태를 보고할 때.
- 책임: 영상 편집 작업 에이전트가 계층별 검증 증거를 유지하고 사용자가 결과를 승인한다.
- 상태: 활성 소비 도메인 규칙.
- 관련 권위: 영상 편집 workflow 계약의 완료 정의와 `PROJECT_RULES.md`의 검증·보호 데이터 경계가 상위 권위다.

### R12 — 기술 gate와 의미 gate 분리

- 조건: 새 timeline, XML 또는 검토본을 성공으로 보고하려 한다.
- 행동: 구조·디코딩·길이·링크 검증과 발화·인과·상태·공간·반복 검수를 별도 결과로 기록한다. 원본 discovery의 전체 coverage는 FFprobe·SRT·scene/motion/luma·silence/RMS·기존 locator 같은 로컬 색인과 가속 탐색으로 우선순위를 만들 수 있으며 원본 전체 1배속 재생은 gate 조건이 아니다. 다만 채택 후보와 양쪽 handle, 원인·행동·결과와 공간 bridge, 발화 경계, 동일 공간 jump 위험, 색인 충돌·불확실 구간은 실제 A/V를 정상 속도로 확인하고, 정상 속도로 보지 않은 구간을 긍정적 사건 근거나 의미 검수 완료로 보고하지 않는다. 의미 gate는 최신 editorial mutation이 반영된 완성 sequence를 처음부터 끝까지 건너뛰지 않고 정상 속도로 최소 한 번 순차 재생하며 `인과·공간`, `템포·반복`, `화면·음성 경계` 세 관점을 각각 판정한다. 세 관점은 별도 판단 record이지 별도 전편 재생이 아니므로 하나의 review run을 공동 근거로 쓸 수 있지만, 각 pass는 공통 run 식별자를 포함한 method·reviewer·checked_at과 관점별 evidence를 따로 갖고 v2 validation의 단일 reviewer와 현재 `editorial_fingerprint`에 결속한다. 새로 만들거나 바꾼 cut boundary는 정상 속도 전후 문맥 A/B로 검수하고, 바뀌지 않은 경계 근거는 source 범위·A/V edge·인접 상태가 동일하다는 결정론적 diff가 있을 때만 승계한다. 수정 중 검수는 경계 변경은 해당 경계와 양쪽 인접 문맥, scene 변경은 해당 scene과 인접 전환, chapter 변경은 해당 chapter와 인접 전환, 사건 순서·스파인·전역 리듬 변경은 완성 sequence 전체로 확대한다. 이 영향 범위 검수는 중간 QA evidence이며 semantic status를 통과시키지 않는다. editorial mutation 뒤 stale 의미 pass는 통과할 수 없고, XML 생성·전달 전에는 최신 mutation 뒤의 한 번의 완성 sequence 전체 재생과 세 관점 record를 새 `editorial_fingerprint`에 결속한다. editorial fingerprint를 보존한 delivery-only 재생성은 의미 pass를 무효화하지 않는다. identity·profile·source·sequence·editorial evidence·revision의 결속은 `payload_fingerprint`, 그 content/revision identity와 approval·validation의 exact state 결속은 `task_payload_fingerprint`, task state와 생성 대상·profile·non-overwrite 계약의 결속은 `delivery_fingerprint`로 검증한다. 각 fingerprint 일치만으로 내부 approval·validation 조건을 통과했다고 간주하지 않고 해당 gate를 별도로 실행한다. contact sheet·경계 정지 frame·segment decode·SRT·RMS·audio assembly는 결함 후보와 기술 상태를 확인할 뿐 실제 A/V 검수를 대체하지 않는다.
- 예외: 해당 산출물에 적용되지 않는 검사는 `해당 없음`으로 남기며 통과로 계산하지 않는다.
- 검증: 두 gate가 모두 필요한 작업은 둘 다 통과하기 전 `편집 완료`나 `사용자 승인 후보`라고 보고하지 않는다. 최신 mutation 뒤 완성 sequence 전체 정상 속도 재생이 실행되지 않았으면 `semantic_status: not_run`이며 영향 범위 검수·내부 reviewer·자동 수치로 `passed`로 바꾸지 않는다. 세 관점 record가 같은 review run과 현재 fingerprint에 결속되고 각자 다른 관점의 결론·evidence를 갖는지 확인한다. fingerprint 파생 결과의 비결정성, persisted reference pointer 불일치, required calibration 미승인, exact baseline reference 불일치, 사건·microbeat·clip 결속 누락, 미완료 microbeat, 피드백 회귀, state owner 충돌, reviewer 불일치, 최신 전체 재생 근거 또는 세 관점 record 미통과 중 하나라도 있으면 XML 파일과 임시 파일이 생성되지 않는 결함 주입 회귀를 실행한다.

### R15 — 검증 단계별 주장 제한

- 조건: XML 생성, import, 재생, 사용자 검토 결과를 상태로 기록하거나 보고한다.
- 행동: `generated`, `parsed`, `structure-validated`, `tool-validated`, `semantic_gate: passed`, `media-validated`, `app-validated`, `user-approved` 중 증거가 있는 상태만 기록하고, 다음 단계가 자동으로 충족됐다고 추론하지 않는다. 기술 상태와 의미 상태는 독립적으로 보고한다. 사용자가 점수를 요청해도 서로 다른 검증 계층을 하나의 완성도 점수로 합치지 않으며, 정상 속도 순차 검수 전 편집 품질은 숫자 대신 `not_scored`로 둔다. 기술 준비도 점수를 제공할 때는 이름·대상 gate·미실행 gate를 함께 표시한다.
- 예외: 적용되지 않는 단계는 `not-applicable`로 기록할 수 있지만 더 높은 단계를 통과한 것으로 계산하지 않는다.
- 검증: 각 상태에 실행 시점, 대상 artifact, 검사 방법, 결과 owner가 있고 보고 문구가 최고 검증 단계보다 높지 않은지 확인한다. 단일 점수가 technical·semantic·app·user 상태를 합치지 않았으며, `semantic_gate: not_run`인 artifact의 편집 품질 숫자 점수는 0건인지 확인한다.

### R16 — validator 계층 분리

- 조건: 새 validator를 추가하거나 여러 검사를 하나의 합격 결과로 묶으려 한다.
- 행동: 검사를 `비보호 구조 / 선언 metadata / 보호 미디어 / 의미 검수`로 분류하고 각 결과를 독립적으로 반환한다. 선언 metadata gate는 `video-edit-timeline-v2.schema.json`과 runtime validator가 representable conditional state의 공통 accept/reject corpus를 소유한다. XML 전달 CLI는 v2 하나만 받고 네 fingerprint를 결정적으로 파생하며, persisted calibration/baseline pointer는 payload/task fingerprint와 비교하고, 전달 대상은 `delivery` 객체와 CLI의 exact output·profile·source byte hash·size를 직접 대조한다. package 공개 API는 guarded writer 하나다. direct calibration·baseline payload는 각각 `--calibration-timeline-json`, `--baseline-timeline-json`으로 받고, authoritative latest owner/resolver가 제공하는 transitive dependency와 state는 반복 가능한 `--reference-timeline-json` bundle로 함께 전달한다. registry는 payload·task fingerprint를 모두 색인하고 소비 pointer는 referenced task state로 resolve하며 calibration self-approval만 payload identity를 사용한다. reference 수는 bounded limit 안이어야 한다. validator 결과는 제공 bundle에 상대적이고 caller가 숨긴 후속 state는 탐지하지 못하므로 owner provenance·최신성·완전성이 없는 bundle은 승인 근거로 사용하지 않는다. `format_regeneration`은 exact `current` 또는 `approved` baseline의 editorial fingerprint를 보존하고 delivery만 바꿔야 하며, editorial 내용이 바뀌면 새 편집 revision으로 판정해 의미 검수와 해당 사용자 승인을 무효화한다. v1은 v2 `working_candidate`로 이관하는 입력에만 허용하고 사용자 전달 XML을 직접 만들 수 없다. v1 retained clip이 여러 event 경계를 가로지르면 migrator는 같은 source·timeline media 범위를 유지한 채 event boundary에서 결정적으로 clip을 분할하고, revision·calibration·boundary 상태는 pending, 의미 상태는 `not_run`으로 초기화한다. low-level XML adapter는 내부 legacy 구조 테스트용이며 전달 진입점으로 직접 사용하지 않는다.
- 예외: 하나의 명령이 여러 계층을 실행할 수 있지만 계층별 결과와 미실행 상태를 합치지 않는다.
- 검증: 보호 미디어 검사는 exact 승인 없이는 실행되지 않고, 구조 통과가 media·app·user 통과를 만들지 않는지 확인한다. schema/runtime 공통 corpus와 runtime cross-reference 결함별 error code 회귀를 실행한다. direct reference와 authoritative 반복 bundle에서 task-state resolve, transitive success, dangling, cycle, same-payload ambiguous state를 각각 재현하고, 빠진 후속 owner state는 validator가 탐지하지 못한다는 bundle-relative 한계를 보고한다. canonical `entire_revision`, calibration self payload pointer, 소비 calibration/baseline task pointer와 승인 chronology도 확인한다. v1 직접 전달, format regeneration의 editorial mutation, latest reject·superseded·동시각 승인 충돌, relative·non-canonical source path, mandatory source lock 실패, publish 직전 source drift, output/profile/input collision, concurrent writer race와 모든 gate 실패에서 기존 결과를 덮어쓰지 않고 XML·임시 파일 생성 수가 0개인지 확인한다.

### R17 — 일괄 편집 연산 뒤 회귀

- 조건: 무발화 제거·속도 조정·경계 자동 보정·구간 일괄 삭제처럼 여러 clip을 한 번에 바꾸는 연산을 적용한다.
- 행동: 연산 전에 필수 anchor·상태 전환·발화 경계 목록을 고정하고, 연산 뒤 완성 timeline 전체에서 같은 목록을 다시 대조한다. 연산이 제거하거나 바꾼 구간 목록을 남기고 누락·절단이 생긴 항목만 복원한다.
- 예외: 연산 범위가 한 scene 안에 한정되면 R12의 영향 범위 검수 단위를 따른다.
- 검증: 연산 전후로 필수 anchor 누락, 상태 전환 누락, 새로 잘린 발화가 각각 0개인지 확인한다.

### R18 — 검수 후보 전 에이전트 사전검수

- 조건: 사용자에게 검수용 후보를 넘긴다.
- 행동: 넘기기 전에 에이전트가 실행할 수 있는 검사를 모두 실행한다. 최소 범위는 최종 전사 순차 대조로 확인하는 발화 의존·상태 전환·필수 anchor(R06), 발화 끝과 인접 중복 발화(R08), 남긴 무발화 구간의 기능과 화면 근거(R09), 일괄 연산 회귀(R17)다. 발견한 결함은 고치고 다시 검사한 뒤 넘기며, 실행 방법·결과·남은 한계를 사전검수 요약으로 함께 보고한다. 정상 속도 시청처럼 사람만 할 수 있는 검수 범위는 요약에 따로 적는다. 사전검수 결과는 검수 후보 전달 절의 기록에 실제 method·evidence와 함께 남긴다.
- 예외: 도구나 입력이 없어 실행할 수 없는 검사는 이유와 대체 확인을 적고 `not_run`으로 남긴다.
- 검증: 요약의 각 검사에 실행 결과나 미실행 이유가 있고, 사전검수에서 찾은 결함이 미해결인 후보를 넘기지 않았는지 확인한다. 사전검수 결과를 의미 gate 통과나 사용자 승인으로 보고하지 않는다.

## 상태 증거

| 상태 | 최소 증거 |
|---|---|
| `generated` | exact 작업 계약에 따라 artifact가 생성되고 대상·시점·생성 owner가 기록됨 |
| `parsed` | 선택한 parser가 artifact를 읽고 필수 구조·metadata를 반환함 |
| `tool-validated` | 지정된 domain validator와 버전/계약 검사가 통과함. media·app·user 통과는 포함하지 않음 |
| `semantic_gate: passed` | 완성 timeline 순차 의미 검수와 reviewer |
| `structure-validated` | frame·gap·track·source lineage·XML 구조 검사 |
| `media-validated` | exact 승인 원본의 decode·프레임·오디오 확인 |
| `app-validated` | 대상 Premiere profile의 실제 import·offline media·재생 확인 |
| `user-approved` | exact artifact에 대한 사용자 결과 승인 |

## 재현 사례

| ID | 상황 | 기대 판정 |
|---|---|---|
| TC12 | XML 구조 검사는 통과했지만 인과 누락이 남음 | 기술 통과·의미 실패로 기록하고 완료 보고를 차단한다 |
| TC15 | 합성 XML 구조 테스트만 통과함 | `structure-validated`까지만 보고하고 Premiere 호환·사용자 승인을 주장하지 않는다 |
| TC16 | exact 원본 승인 없이 RMS·밝기 검사를 실행하려 함 | 보호 미디어 검사를 미실행으로 두고 구조 결과와 분리한다 |
| TC20 | 무발화 구간을 일괄 제거한 뒤 필수 장면과 말끝이 사라짐 | 연산 전 목록과 전체 대조해 누락·절단 항목을 복원한다 |
| TC26 | 검수용 후보를 사용자에게 넘기려 함 | 에이전트가 실행 가능한 사전검수를 먼저 실행하고 결과 요약과 함께 넘긴다 |
