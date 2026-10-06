# 영상 편집 workflow 계약

- 목적: 원본 영상에서 재현 가능한 실제 컷을 설계하고, 의미 검수와 구조 검수를 통과한 Premiere XML을 최소 산출물로 만든다.
- 읽는 시점: 게임플레이·YouTube 영상의 분석, 컷 설계, 사용자 수정본 반영, Premiere XML 생성 작업을 시작할 때.
- 책임: 에이전트는 승인 범위의 분석·편집 판단·검증·복구를 수행하고, 사용자는 창작 방향·보호 데이터 접근·결과 승인을 소유한다.
- 상태: 활성 영상 편집 운영 계약.
- 관련 권위: 루트 `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, `extension/README.md`.

## 사용자 검수 방식의 후보 전달

사용자가 실제 재생 검수를 맡는다고 명시한 경우, 검수용 후보 출력은 `rules/video-editing-validation-and-delivery.md`의 「사용자 검수 후보의 별도 전달 경로」를 따른다. 아래의 XML 생성 전 의미 gate·공개 writer 제한은 검수 완료 경로에 적용하며, 후보 경로에는 그 절의 별도 gate가 적용된다. 최종 완료·승인 기준은 유지한다. 후보는 `premiere-review-xml --timeline-json <v2.json> --preflight-json <review-preflight.json> --editorial-state-json <latest-editorial-state.json> --output <candidate.xml> --profile premiere-cs6-v4`로 생성한다. 사전 검사 기록은 내부 scratch에 두며 사용자 전달물은 XML 하나다.

## 1. 범위와 완료 정의

이 계약은 촬영이 끝난 원본 영상의 내용 분석부터 Premiere XML 전달까지를 다룬다. 촬영 전 근거 패키지는 `YOUTUBE_EVIDENCE_PACK_CONTRACT.md`가 별도로 소유한다. 컷 timeline 이후의 자막·효과·카드·오디오 마감은 `rules/video-post-production.md`(R19~R22)가 소유하며, 후편집 중 컷 내용이 바뀌면 이 계약의 컷 편집 gate로 돌아간다.

편집 완료는 다음 조건을 모두 만족한 상태다.

1. 선택한 방향과 스파인 기능이 완성 타임라인에서 이해된다.
2. 후보 범위 내부의 2차 편집이 끝났다.
3. 발화·인과·상태·공간·반복을 검수했다.
4. timeline 구조 검증이 통과했다.
5. XML이 원본 미디어만 참조한다.
6. 사용자가 요청한 산출물 외 미디어를 만들지 않았다.

기술적으로 열리는 XML, 목표 길이에 맞는 영상, 자막 cue를 보존한 영상만으로는 완료가 아니다.

## 2. 시작 계약과 보호 경계

보호 데이터에 접근하기 전 다음을 확정한다.

- exact 원본 영상과 선택 자막
- 이번 단계의 목적
- 허용된 산출물 종류와 exact 대상
- 원본은 읽기 전용이며 덮어쓰지 않는다는 조건
- 이번 단계의 종료 조건과 사용자 소유 승인 gate

편집을 시작할 때 `VIDEO_EDITING_PROFILES.md`에서 채널·장르 편집 프로필을 골라 작업 기록에 남긴다. 프로필은 규칙이 위임한 기본값만 정하고 규칙을 대체하지 않는다.

한 단계의 계획을 이미 승인받았으면 같은 범위에서 반복 확인하지 않는다. 실제 `inputs/`·`outputs/`의 새 항목, 외부 효과, 삭제·이동, 결과를 바꾸는 충돌이 생길 때만 다시 확인한다.

## 3. 네 작업 층

| 층 | 질문 | 주요 결과 | 종료 조건 |
|---|---|---|---|
| 1차 내용 분석 | 원본에 어떤 사건·반응·변화가 있는가 | 방향을 고정하지 않은 내용 지도 | 구성 가능한 근거와 공백을 설명 가능 |
| 2차 상세 분석 | 선택 방향에 무엇을 쓸 것인가 | 후보 범위·스파인 기능·예상 위험 | 각 후보의 유지·축소·제외 이유가 있음 |
| 1차 구성 편집 | 사건 블록을 어떤 순서로 놓을 것인가 | 블록 순서와 대략 범위 | 도입·전개·회수의 인과가 연결됨 |
| 2차 편집 | 후보 내부를 어디서 실제로 자를 것인가 | frame 단위 video/audio timeline | 모든 블록이 microbeat 검수 완료 |

XML은 2차 편집의 전달 형식이다. 후보 범위나 이야기 블록을 clip 하나로 배치한 것은 1차 구성 편집이며, 완성 편집으로 승인할 수 없다.

1차 내용 분석의 전체 source coverage는 원본 전체를 1배속으로 재생한다는 뜻이 아니다. 먼저 FFprobe, SRT, scene·motion·luma 변화, silence·RMS, 기존 locator처럼 로컬에서 재현 가능한 색인을 source 전체에 적용하고 가속 탐색으로 검토 우선순위를 만든다. 이 자동 근거는 위치 탐색과 위험 선별만 소유하며 사건의 의미나 유지·제외 결정을 단독으로 확정하지 않는다.

정상 속도 A/V 확인은 채택 후보와 양쪽 source handle, 원인·행동·결과 및 상태·공간 전환, 발화 시작·종료, 동일 공간 화면 jump 위험, 색인 신호가 충돌하거나 불확실한 구간에 필수다. 낮은 위험의 제외 후보는 가속 탐색과 표본 검수로 coverage할 수 있지만, 정상 속도로 확인하지 않은 구간을 긍정적 사건 근거나 의미 검수 완료로 보고하지 않는다.

## 4. 작업 프로필과 최소 workflow

작업은 다음 프로필 중 하나를 `video-edit-timeline-v2.workflow_profile`에 선언한다. 모든 작업에 전체 신규 편집 절차를 반복하지 않는다.

| profile | 사용할 때 | 필수 흐름 | 제외 |
|---|---|---|---|
| `new_full_edit` | 방향과 전체 구성이 아직 없는 새 편집 | 입력 계약 → 1차 내용 분석 → 필요한 방향 비교와 사용자 선택 → 2차 분석 → 구성·microbeat 편집 → 의미·구조 gate → XML | 방향이 이미 확정됐는데 세 안을 다시 만들지 않음 |
| `calibration` | 유효한 승인 편집 문법이 없거나 최신 교정이 기존 문법을 무효화함 | exact 교정 범위 → 사건 anchor·microbeat 설계 → 단일 sequence XML → 의미·구조 gate → 사용자 방향 확인 | 전체 영상 확장, calibration 사용자 승인 추정 |
| `approved_delta` | 사용자 승인본이나 수정본의 특정 결함만 수정 | exact protected baseline reference → defect·positive lock·untouched scope → 실제 diff와 영향 구간 편집 → 국소·전역 회귀 → 새 XML | 승인된 무관 범위 재설계, fingerprint 문자열만을 기준본으로 사용 |
| `format_regeneration` | 편집 내용은 그대로 두고 전달 profile만 재생성 | exact current/approved baseline 확인 → editorial fingerprint 보존 → delivery만 변경 → 구조 회귀 | 의미 결정·clip 범위·editorial evidence 변경 |

`new_full_edit`에서 창작 방향이 실제로 미정일 때만 촬영본이 뒷받침하는 방향을 최대 3개 비교한다. 근거가 부족하면 수를 채우지 않는다. 사용자가 자동 진행을 위임했더라도 사용자 소유 방향 승인과 결과 승인은 자동 통과시키지 않는다.

각 프로필은 하나의 v2 payload에서 source manifest, sequence, editorial evidence, revision, approval, validation, delivery를 유지한다. 채택 전 `working_candidate` payload와 임시 sidecar는 선언된 하나의 Git 제외 scratch root에 둔다. `current` 또는 `approved`가 후속 `approved_delta`의 기준이 되면 exact v2 artifact나 불변 snapshot을 보호 evidence owner로 승격하고 대체 revision이나 만료 조건이 충족될 때까지 보존한다. 사용자가 XML 하나만 요청하면 전달 폴더에는 XML 하나만 만든다.

`baseline_reference`와 `calibration_reference`는 최소 `evidence_owner / artifact_id / editorial_fingerprint / source_manifest_fingerprint / user_decision_evidence`를 실제 owner와 교차검증한다. direct payload와 authoritative latest owner/resolver가 제공한 반복 bundle은 payload fingerprint와 task payload fingerprint를 함께 색인한 registry 하나를 이룬다. `new_full_edit`·`approved_delta`의 calibration pointer와 baseline pointer는 referenced task state를 가리키고, calibration artifact 자체의 `approved_payload_fingerprint`만 자기 content/revision payload fingerprint를 가리킨다. 참조 payload가 다시 요구하는 baseline·calibration도 `premiere_xml` gate로 재귀 검증하며, 필요한 fingerprint 누락·cycle·같은 payload identity의 서로 다른 state object를 차단한다. validator는 bundle 밖에 숨겨진 후속 approval·rejection·supersession을 발견할 수 없으므로 caller가 owner provenance·최신성·완전성을 증명해야 하고 결과는 bundle-relative다. 임의 hash, self-reported `preserved`·`approved` 표지, 보고서의 과거 주장은 기준본이나 calibration 승인을 대신하지 않는다. `calibration.required=true`는 유효한 승인 문법이 없거나 최신 사용자 교정이 이를 무효화했을 때만 사용한다. false 또는 `not_required`는 `artifact_id / approved_payload_fingerprint / approved_by=user / approval_evidence / checked_at`가 모두 있고, actual calibration task state의 동일 source·approved revision·semantic pass·latest active `entire_revision` user approval과 일치할 때만 허용한다. binding `checked_at`은 그 latest approval time과 같고 소비 revision은 calibration approval보다 이전일 수 없다. `approved_delta`와 `format_regeneration` baseline은 `current` 또는 `approved` revision이어야 하며 latest active whole-revision approval을 갖고 소비 revision은 그 승인보다 이전일 수 없다.

## 5. 조건부 운영 규칙

루트 `PROJECT_RULES.md`가 유일한 소비 규칙 라우터다. `extension/README.md`와 아래 표는 책임 안내이며 규칙을 독립적으로 선택하지 않는다.

| 책임 | 단일 owner | 규칙 |
|---|---|---|
| 입력 범위와 지시 해석 | `rules/video-editing-intake-and-instructions.md` | R01~R03 |
| 원본 계보와 산출물 예산 | `rules/video-editing-artifact-lineage.md` | R04 |
| 스토리·구성·실제 컷 설계 | `rules/video-editing-story-and-cut-design.md` | R05~R07, R09 |
| 발화·화면·전환 경계 | `rules/video-editing-boundary-quality.md` | R08, R10 |
| current revision과 승인 범위 | `rules/video-editing-state-and-approval.md` | R11, R13~R14 |
| 검증 단계와 전달 주장 | `rules/video-editing-validation-and-delivery.md` | R12, R15~R18 |
| 후편집 연출과 마감 | `rules/video-post-production.md` | R19~R22 |

운영 규칙은 `조건 / 행동 / 예외 / 검증`을 가져야 한다. 작업 버전·프레임 번호·과거 발언·세션 원문·보고서 경로는 규칙에 넣지 않는다. 새 실패가 기존 조건과 겹치면 규칙을 추가하지 않고 기존 owner의 조건·예외·재현 사례를 보강한다.

## 6. 의미 gate와 구조 gate

XML 생성 전에 완성 타임라인 순서로 다음을 검수한다.

- 스파인 기능과 원인·시도·결과가 남아 있는가
- 상태·공간 이동과 행동의 최소 연결이 있는가
- 후보 내부 2차 편집과 긴 clip의 유지 근거가 있는가
- 모든 retained clip이 정확히 하나의 event와 microbeat에 소유되고, 제거 microbeat나 중복 owner가 없는가
- 말 조각·미완성 생각·진행 없는 반복이 남지 않았는가
- 화면 점프·밝기 전환·동작 불연속을 확인했는가

의미 gate는 AI 사전감사다. 사용자가 완성본의 첫 결함 탐지자가 되도록 넘기지 않는다.

최신 editorial mutation이 반영된 완성 sequence는 처음부터 끝까지 건너뛰지 않는 정상 속도 재생을 최소 한 번 거친다. `causal_space / tempo_repetition / av_boundary`는 서로 다른 판단 record이지만 각각 별도 전편 재생을 뜻하지 않으며, 하나의 review run을 공유할 때도 관점별 결론과 evidence를 따로 기록한다. 새로 만들거나 바꾼 cut boundary는 정상 속도 전후 문맥 A/B로 확인하고, 바뀌지 않은 경계의 기존 근거는 source 범위·A/V edge·인접 상태가 동일하다는 결정론적 diff가 있을 때만 승계한다.

수정 중 재검수는 경계 변경이면 해당 경계와 양쪽 인접 문맥, scene 변경이면 해당 scene과 인접 전환, chapter 변경이면 해당 chapter와 인접 전환, 사건 순서·스파인·전역 리듬 변경이면 완성 sequence 전체로 확대한다. 영향 범위 검수는 중간 QA이며 canonical 의미 pass를 통과시키지 않는다. XML 생성·전달 전에는 최신 mutation 뒤의 완성 sequence 전체 정상 속도 재생과 세 관점 record가 새 editorial fingerprint에 결속되어야 한다.

`video-edit-timeline-v2`는 sequence와 별도 계약이 서로 다른 의미 상태를 주장하지 못하게 하는 타임라인 상태 payload다. XML 전달은 별도의 최신 `editorial-state-v1`도 필수로 받아 원본 장면 설계·실제 생략·누적 피드백을 검사한다. 상태 소유자는 같은 작업의 최신 파일 하나를 handoff에 지정하며, 오래된 state를 골라 전달하는 것을 허용하지 않는다. 실제 source byte hash·size, 정규화된 시간 좌표, clip ID에 결속된 사건·microbeat·feedback, working candidate와 current·approved의 구분, exact baseline/calibration reference, 최신 mutation 뒤 전체 정상 속도 review run에 결속된 세 관점 결과, exact output path·profile을 함께 대조한다.

- `editorial_fingerprint`: timeline version, source manifest, 정규화된 time instruction, sequence, event·microbeat·clip ownership, editorial evidence를 결속하되 feedback의 baseline payload pointer는 중립화한다. workflow profile, timeline ID, revision state, approval, validation, delivery는 제외하며 사용자 승인과 의미 pass의 대상이다.
- `payload_fingerprint`: `timeline_version / timeline_id / workflow_profile / source_manifest / sequence / editorial_evidence / revision`의 content/revision identity를 결속하고 approval·validation·delivery는 제외한다.
- `task_payload_fingerprint`: payload fingerprint에 exact approval·validation state를 더해 reference가 소비할 state를 결속한다. fingerprint 일치만으로 그 state의 내부 승인·검수 조건이 유효하다고 추론하지 않는다.
- `delivery_fingerprint`: task payload fingerprint와 exact `delivery` 객체의 artifact·output path·profile·overwrite 조건을 결속해 한 번의 전달 인수를 검증한다. `format_regeneration`은 editorial fingerprint를 보존하되 새 revision·approval·validation·delivery 상태에 따라 payload·task·delivery fingerprint가 각 owner대로 달라질 수 있다.

editorial mutation은 기존 의미 pass와 영향 범위의 사용자 승인을 즉시 무효화한다. editorial fingerprint를 보존한 delivery-only 재생성은 의미 pass를 무효화하지 않지만 새 profile의 구조·앱 검증은 별도다.

revision decision의 `approved_scope`는 canonical literal `entire_revision`만 허용한다. authoritative owner bundle 안에서 current artifact ID·source manifest fingerprint·editorial fingerprint와 정확히 일치하는 결정만 후보로 삼고 가장 최신 `checked_at`의 결정을 적용한다. 최신 rejection은 `use_prohibited`, superseded 결정은 `historical` revision을 요구하며 둘 다 XML 전달을 막는다. 최신 시각에 서로 다른 decision·invalidation·approver·scope 상태가 충돌하면 `approval_decision_conflict`로 중단하고, 최신 approved 결정에 `invalidated_by`가 있으면 활성 승인으로 쓰지 않는다. 이 latest 판정은 제공 bundle에 상대적이며 누락된 후속 owner state까지 증명하지 않는다.

`video-edit-timeline-v1`과 `video-edit-contract-v1`은 이전 자료를 v2 `working_candidate`로 이관하기 위한 legacy 입력이다. v1 parser·adapter의 구조 회귀는 유지할 수 있지만 v1에서 사용자 전달 XML을 직접 생성하거나 v2 acceptance·의미 gate·사용자 승인을 승계할 수 없다.

구조 validator는 frame 범위, 길이 식, track 연속성, audio gap, A/V 총길이, 원본 범위, 명시적 시간 역전, source lineage만 판정한다. 스파인 적절성, 발화 자연스러움, 공간 연결, 리듬, 밝기·RMS 합격값은 자동 승인하지 않는다.

### 원본 장면 설계와 최신 피드백 입력

`editorial_state.py`가 `editorial-state-v1`의 runtime 계약을 소유한다. 구조 예시는 `extension/examples/editorial-state-v1.json`, 실행 검사는 `editorial-check --timeline-json ... --editorial-state-json ...`다. 이 명령은 원본 미디어를 읽지 않고 실패 시에도 계산한 생략 목록을 반환한다.

- `source_manifest_fingerprint / generation`: 같은 원본과 최신 상태 식별. `scenes`는 최종 컷에서 자동 생성하지 않고 원본 관찰로 작성한다. 각 scene은 검토한 `source_in/out`, 보여줄 사건(`show`), 시청자가 아는 정보(`viewer_learns`), 다음 행동 이유(`next_action_reason`), 선행 scene ID(`depends_on`), 필수 화면·음성 `anchors`를 갖는다. anchor는 ID·원본 범위·media_scope·관찰 내용을 가진다. source 범위는 반개구간 프레임이다.
- 장면 검토 범위 안 retained union의 여집합을 video/audio 각각 계산한다. 선두·꼬리 생략, J/L 음성 차이도 포함한다. 장면 바깥 미검토 원본 전체를 분석했다고 주장하지 않는다. 선택한 컷이 설계 범위를 벗어나면 차단한다.
- `reviews`의 현재 편집은 exact editorial fingerprint, 설계·feedback의 `state_basis_fingerprint`, generation에 결속한다. `omissions`는 계산된 각각의 scene/track/source 범위와 정확히 일치해야 하며 reason·observation·certainty=confirmed가 필요하다. 불확실하면 원본 유지 또는 추가 관찰로 해소한다. 미신고·중복·낡은 범위는 통과하지 못한다.
- 필수 anchor의 전체 범위를 순방향으로 연속 유지해야 한다. 이음새만 나눈 연속 clip은 허용하지만 부분 삭제·순서 역전은 차단한다. scene 의존 관계가 실제 편집 위치에서도 선행하는지 검사한다. observation은 사람이 작성한 근거이며 내용의 진위를 기계가 판별하는 것은 아니다.
- `record-feedback --timeline-json ... --editorial-state-json ... --feedback-id ... --symptom ... --reported-by user --output <새 절대 JSON 경로>`는 기존 설계·피드백을 보존한 새 state를 생성하며 generation을 증가시키고 이전 reviews를 비운다. 정확한 source 시각 미확정이면 빈 scenes의 초안 상태에서도 등록할 수 있지만 XML 전달은 차단된다. `--required-anchor-id`는 반복 지정 가능하다. 반환 경로를 최신 task owner로 handoff에 반영하고 과거 state는 snapshot으로 보존한다. 별도 사용자 전달물은 아니다.
- 피드백 대상 편집은 이름을 바꿔도 재출력할 수 없다. 새 편집에는 모든 누적 feedback ID의 `resolutions`와 보존된 anchor·근거가 필요하다. 전달 결과는 editorial state fingerprint를 포함하므로 옛 timeline의 pending/passed만 보고 현재 채택 가능하다고 해석하지 않는다. 기존 승인 payload를 직접 수정하지 않는다.
- `premiere-xml`과 `premiere-review-xml`의 공개 writer는 `editorial_state=` 인수를 요구한다. CLI는 `--editorial-state-json`이 없으면 출력 전에 차단한다. 기존 v2 schema·fingerprint는 유지되며, 이 추가 입력을 생략한 과거 호출은 새 전달에 사용할 수 없다. `rule-gate`는 v2 상태 검사이고 전체 전달 검사를 대신하지 않는다.
- `review-preflight-v2`는 `editorial_state_fingerprint`를 추가한다. source_mapping만 passed이며, 나머지 관찰은 recorded 또는 not_run이다. `agent_preflight_status=recorded`, `editorial_structure.status=structure_checked`는 지각 검수·사용자 승인이 아니다. v1의 다섯 passed를 그대로 재사용할 수 없다.

검사 한계: 제공한 state 밖에 숨겨진 후속 피드백, 실제 관찰 없이 작성한 설명, 최초 설계에서 누락한 중요한 장면은 자동 탐지하지 못한다. task owner의 최신성·완전성은 호출자가 보장하며, 불확실한 어두운 화면을 반복으로 단정하지 않는 편집 판단을 대신하지 않는다.

## 7. 도구와 XML 경계

- SRT 검증·정리는 strict UTF-8, cue 순서·겹침·미디어 범위를 확인하고 명시된 timestamp 보정·제외만 새 파일에 적용한다. 원본 hash와 cue 본문은 바꾸지 않는다.
- legacy CSV importer는 frame·gap·순서를 그대로 이관하고 의미 역할을 추론하지 않으며 결과는 `semantic_gate: not_run`이다. v1 migrator도 source media와 최종 timeline coverage를 보존하지만 retained clip이 여러 event 경계를 가로지르면 exact event ownership을 위해 그 경계에서 결정적으로 clip을 구조 분할한다. migration 결과는 `working_candidate`, calibration pending, approval 비어 있음, `validation.semantic_status: not_run`, boundary review pending이며 legacy 승인·검수를 승계하지 않으므로 별도 v2 의미 검수 전 XML을 만들 수 없다.
- timeline 오류는 가능한 범위에서 모두 수집하며, 각 issue는 `code / message / track / clip_id / index`를 가진다.
- 편집 계약 오류도 가능한 범위에서 모두 수집하며, 각 issue는 `code / message / path`를 가진다. `rule-gate`는 개별 실패를 합격 점수로 상쇄하지 않는다.
- XML adapter는 원본 source reference 하나, 결정론적 clip·link 구조, frame·gap·예외, 비덮어쓰기, XML 단일 산출물을 지킨다.
- `build_premiere_xml`·`write_premiere_xml`은 `video_editing.premiere_xml` 내부의 legacy 구조 테스트 adapter이며 package 공개 API가 아니다. 사용자 전달 XML은 v2 payload를 받는 `write_validated_premiere_xml` 또는 `python -m video_editing premiere-xml`만 생성한다.
- v2 전달은 source file byte hash·size와 payload 선언을 대조한다. 네 fingerprint는 현재 payload에서 결정적으로 파생하고 persisted calibration/baseline pointer만 해당 payload/task fingerprint와 비교한다. 전달 대상은 `delivery` 객체와 CLI 인수의 output·profile을 직접 대조한다. `source_manifest.path`는 XML이 참조할 absolute canonical path여야 한다. timeline·source·reference 입력과 같은 output, `.xml` 이외 경로, 기존 파일, `overwrite=true`는 거부한다.
- `validate`, `rule-gate`, `premiere-xml`은 direct calibration·baseline에 `--calibration-timeline-json`, `--baseline-timeline-json`을 사용하고, authoritative latest owner/resolver가 제공한 transitive dependency와 exact state에는 반복 가능한 `--reference-timeline-json`을 사용한다. payload·task fingerprint registry에서 bounded graph를 재귀 검증하며 dangling·cycle·same-payload ambiguous state·reference 수 초과를 fail closed한다. 이 저장소에는 canonical owner의 최신성을 자체 조회하는 resolver가 아직 없으므로 bundle provenance·최신성·완전성은 caller 계약이고 validator 결과는 bundle-relative다.
- delivery writer는 Windows mandatory handle로 source의 write/delete sharing을 거부한 채 최초 hash·size, XML 생성 뒤, atomic publish 직전의 hash·size를 같은 handle에서 대조한다. 이 immutable snapshot을 보장할 수 없거나 source drift가 있으면 전달하지 않는다.
- non-overwrite는 존재 여부 선검사 뒤 replace하지 않고 filesystem의 원자적 no-clobber 생성으로 보장한다. source/reference/gate/lock/drift/no-clobber 실패는 기존 결과를 보존하고 XML과 임시 파일을 남기지 않는다.

| profile | 용도 | 상태 경계 |
|---|---|---|
| `sequence-v5` | v1 legacy 경량 sequence XML | 내부 byte 호환 회귀만 유지; 사용자 전달 profile 아님 |
| `premiere-cs6-v4` | project·bin·masterclip을 포함한 CS6용 FCP XML v4 | v2의 유일한 전달 profile. 구조 검증이며 실제 Premiere import·재생 검수는 별도 |

## 8. 상태·승인·산출물 수명

- current artifact, exact baseline evidence와 source manifest fingerprint는 하나의 state owner가 소유한다.
- 사용자 승인은 결과와 exact 범위에 붙으며 source·사용자 수정·인접 경계 변경 시 해당 범위만 무효화한다.
- revision-level 결정 범위는 `entire_revision`이고, clip·결함 단위 보존 범위는 feedback owner가 별도로 유지한다.
- authoritative owner bundle 안 exact artifact·source·editorial fingerprint에 대한 최신 결정만 활성 상태를 정한다. rejection·superseded·invalidated approval·동시각 충돌은 각각 R11~R14의 fail-closed 상태 전이를 따르며 bundle 밖 후속 상태를 탐지한 것으로 확대하지 않는다.
- 후속 baseline은 latest active whole-revision approval을 가진 `current` 또는 `approved` state이고, 소비 revision은 baseline과 calibration의 latest approval time보다 이전일 수 없다.
- 기술 통과는 창작 방향 승인, 앱 import 검수, 사용자 재생 승인을 대체하지 않는다.

| 종류 | 기본 수명 | 원칙 |
|---|---|---|
| 운영 계약·rule·schema·검증 코드 | 유지 | 유일 owner와 회귀가 있어야 함 |
| 현재 작업 brief·handoff | 현재 상태 동안 유지 | 완료 이력과 원문을 복제하지 않음 |
| v2 `working_candidate` payload | 활성 작업 동안 Git 제외 scratch | 내부 재현·gate 입력이며 채택되지 않으면 closeout에서 제거; 사용자가 요청하지 않으면 전달 sidecar가 아님 |
| v2 `current`·`approved` baseline evidence | 후속 소비가 끝나거나 superseded·expiry가 충족될 때까지 보호 보존 | exact artifact와 editorial·payload·task·delivery fingerprint 중 소비에 필요한 값, source manifest, 소비자·검증·만료를 함께 유지 |
| timeline·XML·사용자 deliverable | 보호 파생물 | exact 항목·목적 승인, Git 제외 |
| 분석 cache·RMS 배열·임시 frame·재전사 | disposable runtime | 재생성 가능, 기본 비추적 |
| 세션 원문·버전별 중복 보고 | 운영 비의존 | 외부 백업 또는 Git 이력, 활성 owner에서 제외 |

규칙으로 승격하지 않은 수치·자동화·skill 후보는 `docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md`만 소유하며 일반 편집의 기본 읽기 대상이 아니다.

### 과거 영상 자료의 domain 지식 환류

과거 영상 spine·방향안·검수 문서·분석 파생물을 추출하거나 정리할 때 범용 절차는 상위 router가 선택한 foundation owner가 담당한다. 이 계약은 추출 결과 중 영상 편집 domain의 배치만 소유한다.

| 추출 내용 | 영상 domain owner |
|---|---|
| 독립 영상에서 반복되고 일반화된 편집 조건 | R01~R22의 가장 좁은 기존 rule owner |
| 한 영상에서만 확인된 판단·수치·자동화·skill 가능성 | `VIDEO_EDITING_RULE_CANDIDATES.md`의 기존 후보 또는 task evidence |
| exact frame·파일명·해시·길이·영상별 사용자 승인 | 원래 검수·보호 자료 또는 현재 영상 task owner |
| 현재 revision·승인 범위·source fingerprint | 상태·승인 rule이 선택한 current owner |
| 세션 원문·버전별 중복 보고·완료 명령 | active owner로 승격하지 않고 Git 이력 또는 사용자 요청 보고서 |

같은 영상 spine의 직접 연결 자료만 목적 범위에서 다루며 sibling 자료를 넓게 열거하지 않는다. 단일 영상 사실을 전역 규칙으로 승격하거나, 범용 파일 절차를 extension 규칙으로 복제하지 않는다.

## 9. 실행점

보호 데이터가 없는 v2 기본 구조·규칙 검증:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = ((Resolve-Path 'core/src').Path, (Resolve-Path 'extension/src').Path -join ';')
python -m video_editing validate `
  --timeline-json extension/examples/video-edit-timeline-v2.json
python -m video_editing rule-gate `
  --timeline-json extension/examples/video-edit-timeline-v2.json `
  --purpose premiere_xml
```

`approved_delta`처럼 dependency graph가 있는 payload는 authoritative latest owner/resolver에서 받은 direct reference를 명시하고, 그 reference가 다시 요구하는 dependency와 exact task state를 `--reference-timeline-json`으로 필요한 횟수만큼 반복한다. 임의로 일부 state만 고른 bundle은 latest 검증 근거가 아니다.

```powershell
python -m video_editing rule-gate `
  --timeline-json <승인된-v2-task-payload.json> `
  --calibration-timeline-json <직접-calibration-v2.json> `
  --baseline-timeline-json <직접-baseline-v2.json> `
  --reference-timeline-json <간접-reference-v2-1.json> `
  --reference-timeline-json <간접-reference-v2-2.json> `
  --purpose premiere_xml
```

자막 검증·정리, legacy CSV 이관, XML 생성:

```powershell
python -m video_editing subtitle-validate --source <승인된-source.srt>
python -m video_editing subtitle-clean `
  --source <승인된-source.srt> `
  --destination <승인된-cleaned.srt> `
  --media-end-ms <정수> `
  --start <cue=ms> `
  --end <cue=ms> `
  --exclude <cue>
python -m video_editing import-csv `
  --video-csv <승인된-video.csv> `
  --audio-csv <승인된-audio.csv> `
  --output <승인된-timeline.json> `
  <source와 sequence metadata>
python -m video_editing migrate-v1 `
  --timeline-json <명시된-legacy-timeline.json> `
  --edit-contract-json <명시된-legacy-contract.json> `
  --output <새-v2-task-payload.json> `
  --timeline-id <새-id> `
  --source-content-sha256 <sha256:...> `
  --source-byte-size <정수> `
  --delivery-output-path <새-output.xml> `
  --checked-at <검사시각>
python -m video_editing premiere-xml `
  --timeline-json <승인된-approved_delta-v2-task-payload.json> `
  --calibration-timeline-json <적용되는-직접-calibration-v2.json> `
  --baseline-timeline-json <적용되는-직접-baseline-v2.json> `
  --reference-timeline-json <필요한-간접-reference-v2.json> `
  --output <승인된-output.xml> `
  --profile premiere-cs6-v4
```

실제 `inputs/`·`outputs/`를 사용하는 명령은 사용자가 exact 항목과 목적을 승인한 작업에서만 실행한다.

`migrate-v1`은 legacy 승인과 의미 검수를 승계하지 않는다. 여러 event를 가로지르는 retained clip은 source·timeline media 범위를 보존하며 event boundary에서 결정적으로 구조 분할한다. 결과는 `working_candidate`, calibration `pending`, semantic `not_run`, 모든 boundary review `pending`이며 재검수 전 XML을 만들 수 없다.

## 10. Acceptance

1. 루트 `PROJECT_RULES.md`가 활성 영상 편집 규칙 6개를 각각 정확히 한 번 라우팅하고, `extension/README.md`와 이 계약의 책임표는 병렬 라우터로 동작하지 않는다.
2. 운영 규칙 R01~R22과 재현 사례 TC01~TC33은 각 rule owner에 정확히 한 번 존재한다.
3. 기존 TC01~TC12의 기대 판정이 이관 전과 동일하다.
4. TC13~TC16이 current revision 동결, 상태 충돌 중단, 검증 주장 제한, validator 계층 분리를 재현한다.
5. 정상 v2 timeline은 결정론적 editorial·payload·task payload·delivery fingerprint를 반환한다. payload는 content/revision identity, task payload는 payload+approval+validation state, delivery는 task payload+delivery 객체를 소유하며 각 내부 gate는 fingerprint 일치와 별도로 판정한다.
6. editorial mutation은 이전 canonical 의미 검수와 영향 범위 승인을 무효화한다. 수정 중 검수는 영향 범위에 맞게 수행하되 XML 전달 전 최신 mutation 뒤 완성 sequence 전체 정상 속도 재생과 세 관점 record를 새 fingerprint에 결속한다. delivery-only regeneration은 editorial fingerprint를 보존한다.
7. 정상 v2 timeline은 검증된 원본 reference 하나를 가진 CS6 XML 하나만 만든다.
8. XML의 clip 수·frame 범위·audio gap이 timeline과 일치한다.
9. SRT·CSV 원본 hash가 유지되고 실패 시 부분 출력이 없다.
10. legacy import·v1 migration은 의미 gate를 통과시키지 않고, 여러 event를 가로지르는 legacy clip은 media coverage를 보존한 결정적 boundary split 뒤 모든 승인·검수가 reset되며, v1은 사용자 전달 XML을 직접 만들지 못한다.
11. `sequence-v5` byte 회귀와 `premiere-cs6-v4` 구조 회귀가 함께 통과한다.
12. Core와 Extension 전체 회귀가 통과한다.
13. v2 XML 전달 CLI는 별도 self-attested 계약을 받지 않고 main payload와 authoritative owner/resolver reference bundle gate를 우회할 수 없으며, 결함 주입 시 XML과 임시 파일을 만들지 않는다.
14. schema와 runtime validator는 필드 집합뿐 아니라 representable conditional state의 공통 accept/reject corpus를 통과한다.
15. relative·non-canonical source path, mandatory source lock 실패, source drift, output/profile/input collision과 동시 writer race에서 기존 파일을 덮어쓰지 않고 XML·임시 파일을 남기지 않는다.
16. exact baseline·calibration reference는 evidence owner의 artifact·editorial fingerprint·source manifest·task state·사용자 결정과 교차검증되고, transitive dependency는 authoritative repeatable bundle에서 재귀 해소되며 dangling·cycle·same-payload ambiguous state는 거부된다. 검증 결과는 bundle-relative이고 숨겨진 후속 state까지 증명하지 않는다.
17. `calibration.required`가 true인 미승인 확장과, exact artifact·referenced task fingerprint·user evidence·latest whole-revision approval time 및 actual approved calibration state가 없는 `not_required`는 거부된다. calibration artifact 자신의 self-approval pointer는 자기 payload fingerprint와 일치한다.
18. retained clip은 정확히 하나의 event와 microbeat가 소유하고 미소유·중복 소유·제거 microbeat 소유가 거부된다.
19. `approved_scope`는 literal `entire_revision`이고, authoritative bundle 안 exact editorial payload에 대한 최신 rejection은 `use_prohibited`, superseded 결정은 `historical`을 요구하며 invalidated approval과 latest timestamp 충돌은 전달을 차단한다.
20. baseline은 latest active whole-revision approval을 가진 `current` 또는 `approved` state이고, 소비 revision의 checked_at은 referenced baseline과 calibration approval time보다 이전일 수 없다.
