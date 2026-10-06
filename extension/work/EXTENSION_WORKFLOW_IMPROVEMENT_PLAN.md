# Extension 영상 편집 워크플로우 개선계획

- 목적: 기존 영상 편집 규칙을 실제 생성·검수·전달 능력에 연결하여, 기술 통과와 편집 품질을 혼동하는 반복을 줄인다.
- 읽는 시점: Creator 영상 편집 workflow 개선을 승인하거나 백룸 단계 0을 재개하기 전.
- 책임: Creator 에이전트가 승인된 Extension 구현·검증을 수행하고, 사용자는 실제 창작 갈림길·보호 데이터·revision 채택을 결정한다.
- 상태: active 개선 설계. 사용자가 계획 재검토·정정과 Extension 개선 구현을 요청했다. 2026-09-23 사용자 지시에 따라 아래 활성 전환을 적용한다.
- 관련 권위: [Creator 정책](../../PROJECT_RULES.md), [Extension owner](../README.md), [영상 편집 계약](../docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md), [Core 개선계획](CORE_WORKFLOW_IMPROVEMENT_PLAN.md).
- 정보 유형·수명: 한시 개선 설계. 기존 백룸 전체 편집계획에 대한 구현 차이만 소유하며 현재 상태·편집 규칙을 대체하지 않는다. 반영 후 해당 기존 owner에 연결하고 역할을 종료한다. 물리적 삭제·이동은 별도 승인 범위다.

## 활성 변경 계약 — 장면 보존·삭제 검토·피드백 (2026-09-24)

최신 사용자가 승인한 범위는 기존 Extension의 세 가지 최소 기능 개선이다. 백룸 영상 편집은 중단 상태를 유지한다.

- 결과: 원본 장면 설계의 필수 범위 누락, 검토 없는 실제 삭제, 최신 피드백의 미해결·검증 재사용을 XML 전달 전에 차단한다.
- 구현: 백룸 worktree의 기존 writer/CLI/preflight에 필수 editorial-state 입력을 연결한다. 장면 설계는 타임라인 밖 원본 좌표로 유지하며 검토 범위·필수 anchor·정보·행동 이유를 소유한다. 실제 A/V 삭제는 검토 범위에서 retained union을 뺀 결과와 exact 대조한다. 불확실 삭제는 유지 또는 추가 확인으로 해소한다.
- 상태: 같은 source의 사용자 피드백은 revision과 독립된 ID로 유지하고, 등록 시 이전 검토를 무효화한다. 새 후보는 최신 state와 결속된 해결 근거를 요구한다. 제공된 state 밖의 숨겨진 최신 상태까지 탐지한다고 주장하지 않는다. 호출자는 handoff의 단일 최신 owner를 제공한다.
- 검증 수준: preflight v2는 기술 passed와 관찰 recorded/not_run을 구분한다. 원본 장면의 의미를 자동 판별하거나 정상 속도 시청을 강제 도구로 대체하지 않는다. 기존 v2 semantic 완료 경로와 source lock/hash/no-clobber는 유지한다.
- 입력·보호: 기존 Extension 코드·합성 fixture·검사와 승인된 백룸 내부 JSON을 사용한다. 원본/산출물 수정, 영상 재편집, Core 변경, 설치, 유료 API, 외부 전송, commit/push/삭제 제외. 추가 사용자 선택은 필요하지 않다.
- 필수 검사: 필수 anchor 일부/전체 삭제·순서 역전, 삭제 누락·중복·오디오 독립 삭제·불확실 관찰, stale state/preflight·새 revision 피드백 누락, writer/CLI no-output 차단과 정상 전달. 기존 v2/CS6/review-delivery/workflow/rule-gate 회귀와 inventory 등록 확인. 실패 시 이번 변경만 수정하며 다른 로컬 변경 보존.
- 적용 경계: 이 구현은 선언된 장면·관찰 근거의 누락과 불일치를 탐지한다. 잘못 해석한 화면이나 고의로 누락한 owner를 자동으로 진실 판정하지 않는다. 사용자에게 새 검수 앱을 요구하지 않는다.

## 활성 전환 (2026-09-23)

사용자는 추가 유료 API 없이 에이전트가 가능한 사전 검증을 모두 수행하고, 실제 재생 품질은 직접 확인하는 방식을 승인했다. 아래 A2의 에이전트 실제 A/V reviewer 확보와 그에 따른 원본 진입 금지는 이 작업에 더 이상 적용하지 않는다. 기존 A1/A2 절은 이전 설계의 근거다. 검수 완료를 가장하거나 기술 통과를 의미 통과로 올리지 않는 경계는 유지한다.

활성 실행·단계 설계는 `D:/AI Agent/GitHub/Creator-backroom/extension/docs/domain/youtube/BACKROOM_EDITING_EXECUTION_PLAN.md`의 「활성 실행 변경 계약 — 사용자 검수 방식」이 소유한다. 구현은 별도 guarded review-candidate XML 경로이며, 기술 gate 통과 후 기존 승인 원본 분석과 대표 구간 편집으로 진행한다. 실제 진행·재개 지점은 백룸 `SESSION_HANDOFF.md`가 소유한다. 대표 구간 방향 확인 후 전체로 확장하며 사용자 검수는 대표본과 전체본 두 번을 목표로 한다.

## 1. 대상과 경계

계획은 현재 Creator main의 `extension/work`에 작성한다. 영상 편집 구현과 실제 작업의 대상은 `codex/backroom-video` worktree이며, 두 범위가 자동 동기화된다고 가정하지 않는다.

백룸에는 `extension/docs/domain/youtube/BACKROOM_EDITING_EXECUTION_PLAN.md`라는 기존 전체 설계가 있다. 이 문서는 그 설계의 편집 원칙과 단계 전체를 복제하지 않고, 실행을 가능하게 할 개선사항만 다룬다. main과 백룸의 같은 상대경로도 내용이 같다고 가정하지 않는다. 아래 구현 경로는 별도 표기가 없으면 **백룸 worktree 기준**이다.

- 허용할 향후 변경 후보: Extension의 runtime 연결, proxy, 증거 결속, 검증/보고 경로, 관련 테스트와 기존 owner 문서의 필요한 차이.
- 제외: Core 직접 수정, 전체 원본 1배속 의무의 재도입, 고정 영상 길이·컷 수 목표, 반려 결과의 재사용, 원본·기존 결과 덮어쓰기, 임의 음악·효과·그래픽 추가.
- 보호: 경로 구간이 `inputs` 또는 `outputs`인 항목은 이 계획 작성에서 열거·읽지 않는다. 실제 구현 후 미디어 작업은 최신 지시와 exact 항목·목적을 다시 대조하고 필요한 권한만 요청한다.
- Git·환경: 새 branch/worktree 생성, merge·checkout·commit·push, 설치·권한 변경은 별도 승인 없이 실행하지 않는다. 기존 환경의 정확한 대상에 대한 sandbox 실행 승인은 작업 권한과 구분한다. 새 작업 생성·외부 전송은 포함하지 않는다.

## 2. 이미 있는 것과 실제 보완점

계획 수립일은 2026-09-07이다. 동적 상태는 실행 직전에 다시 확인하며 현재성·승인 정본은 이 문서가 소유하지 않는다.

| ID | 문제와 근거 | 이미 있는 owner | 개선할 차이 |
|---|---|---|---|
| E1 | main/백룸 대상·권한 혼동, 커밋한 변경을 미커밋으로 남긴 핸드오프. 문서·Git 대조로 확인 | 각 worktree의 소비 정책·상태, 공통 Core 계약 | 실제 작업 대상/승인 범위 확인과 핸드오프 사실 정정. 최신 Core 사용과 최신 Creator main 반영을 별도 확인 |
| E2 | FFmpeg 실행 가능 여부와 실제 A/V 검수 능력을 혼동. `local_runtime.py`에 FFmpeg·ffprobe·합성 audio probe가 있음을 직접 확인 | `extension/config/local-runtime-v1.json`, `extension/src/local_runtime.py` | 기존 도구를 재사용하는 v2-equivalent proxy와 실제 reviewer/Premiere operator 연결 증명 |
| E3 | 원인 장면 과삭제, 공간 순간이동, 반복 도주·갑작스러운 발화. 사용자 피드백 근거이며 이번에 미디어 재검수하지 않음 | 기존 스토리·컷/경계 규칙과 백룸 전체 설계 | 사건 anchor 보존→내부 microbeat 판단→실제 연결 A/B 검수의 실행 증거. 규칙 재작성보다 실제 사례 적용 |
| E4 | 원본 전체 1배속과 반복 전편 검수는 비용 과다. 비용 최적화 설계의 커밋 근거 확인 | 백룸 전체 설계, 검증·전달 규칙 | 이미 도입한 로컬 index·가속 discovery·위험 기반 1배속을 실행. 측정으로 비용/누락 균형 확인 |
| E5 | 의미 통과·점수를 실제 청취 없이 보고한 과거 사례. 현재 v2 validator는 method/reviewer/time/evidence 및 fingerprint를 검사함 | `extension/src/video_editing/timeline_v2.py`, `delivery.py`, `cli.py`, 관련 schema/tests | 선언 문자열 존재 검사를 실제 proxy·review run 증거에 연결. 기술·의미·앱·사용자 상태의 독립 보고 유지 |
| E6 | 준비·문서·테스트가 실제 산출물보다 먼저 커지고, 재개 기록은 뒤처짐 | 기존 전체 설계·상태·검증 경로 | 완료 조건마다 최소 실행 증명과 즉시 상태 대조. 새 timeline/보고서 묶음을 사용자 전달물에 추가하지 않음 |

현재 v2의 reference·approval·event/microbeat·guarded writer와 비용 최적화 규칙은 재구현 대상으로 세지 않는다. `missing_review_evidence`·`stale_semantic_review` 같은 기존 검사를 보존하고 실제 결속이 빠진 부분을 보완한다. 이번 소스 목록에서는 독립 proxy 구현을 확인하지 못했으므로 E2 시작 시 연결 경로 전체를 확인해 중복 구현을 피한다.

## 3. 단계 A — 실행 가능한 검수 경로 확보: E1·E2·E5

### 재검토 정정과 현재 변경 계약

- 단계 A는 **A1 기술 준비**와 **A2 실제 지각·앱 검수**라는 독립 판정을 갖는다. 이는 기존 단계 0의 다섯 능력을 낮추는 변경이 아니다. A1만 통과하면 부분 구현이며 단계 B 진입은 여전히 금지다.
- 이번 결과는 비보호 합성 source를 사용하는 proxy 구현·결속 검사·회귀와 정확한 재개 상태다. 최초 구현은 CFR·단일 원본·연속 video/audio·속도 1배·추가 효과 없는 v2 범위를 명시하며, 지원 밖 입력은 렌더 전에 거부한다. 범용 동등성이나 실제 영상 적합성을 주장하지 않는다.
- 기존 v2 검증을 재사용하되 `as_legacy_timeline`은 의미 통과를 요구하므로 검수 전 proxy 경로에 쓰지 않는다. 의미 상태를 위조해 adapter를 통과시키지 않는다. 기존 XML writer·v2 schema와 package 공개 export는 이번 A1에서 변경하지 않는다.
- `extension/src/video_editing/review_proxy.py`, `extension/tests/test_video_editing_review_proxy.py`, `scripts/run_test_inventory.py`, 기존 `extension/README.md`의 연결 설명 및 해당 상태 문서를 최소 변경 대상으로 한다. main의 이 계획은 정본으로 유지하고 백룸에는 복제하지 않는다. 미커밋 main 계획 참조는 같은 workspace 재개 의존이며 portable로 주장하지 않는다.
- 필수 검증은 백룸 root에서 `PYTHONPATH=extension/src`와 bytecode 금지 조건으로 `python -B -m unittest discover -s extension/tests -p test_video_editing_review_proxy.py -v`, 기존 v2 회귀 및 test inventory 등록 확인이다. 합성 시험은 실행 전용 임시 디렉터리에서 만들고 그 디렉터리의 이번 생성물만 정리한다. 기존 파일·보호 경로는 읽거나 지우지 않는다.
- 실패 시 해당 신규 구현·회귀의 원인만 고치고 기존 결과·사용자 변경을 보존한다. capability 부재를 코드 성공으로 덮지 않는다. 실제 A/V reviewer와 Premiere 경로가 확인되지 않으면 A2를 미실행으로 남겨 필요한 결정을 요청한다.

### 진입과 기준 정리

1. 시작 문서, 실제 root·branch·HEAD·기존 변경·쓰기 가능 경로를 확인한다. 최신 Creator main과의 관계, 부모 gitlink·Core checkout의 관계를 각각 대조한다. 단순히 Core가 최신이라고 main이 반영됐다고 말하지 않는다.
2. 사용자의 최신 main 기준 원칙과 백룸 고유 구현을 함께 보존한다. 차이가 있으면 필요한 main 변경·충돌·통합 방법을 먼저 정하고, 승인 없이 reset/checkout/merge하지 않는다.
3. 이미 커밋된 변경을 미커밋이라고 적은 백룸 상태와 현재 승인 범위의 모순을 실제 Git·최신 사용자 지시로 정정한다. 과거 문서의 `calibration 승인`을 전편 확장 승인으로 확대하거나, 전체 결과 요구를 조각 전달로 축소하지 않는다.
4. 기존 전체 설계의 단계 0 범위에서 가장 작은 비보호 실행 시험을 수행한다. 원본 분석과 편집 XML 생성은 아직 시작하지 않는다.

### 구현 범위

- **runtime:** 기존 manifest와 verifier를 재사용한다. FFmpeg·ffprobe·선택적 전사 backend·A/V reviewer를 개별 판정한다. optional whisper 부재만으로 FFmpeg 실패라고 보고하지 않는다. 설치가 필요하면 별도 승인한다.
- **proxy:** 기존 구현 유무를 먼저 확인하고 없을 때만 `extension/src/video_editing/review_proxy.py` 같은 최소 모듈을 추가한다. v2 source 범위, timebase, video/audio 독립 경계, source handle을 재현한다. 지원하지 않는 연출은 조용히 단순화하지 않고 생성 전에 차단한다.
- **기술 결속:** source 식별값, editorial fingerprint, render 설정·도구 버전, 실제 proxy hash와 실측 길이·프레임/A/V 특성을 묶는다. 원본 전체 길이를 짧은 proxy의 정답 길이로 사용하거나 선언 프레임 수로 실측값을 덮어쓰지 않는다. 누락 음성을 합성 무음으로 덮어 성공 처리하지 않는다.
- **실제 review:** 실제 보고 들을 수 있는 reviewer와 재생 수단, Premiere operator/profile을 확인한다. 플레이어 실행·프로세스 종료·ASR·정지 프레임을 지각 검수로 간주하지 않는다. 지원 도구나 담당자가 없으면 능력 부재와 필요한 선택을 보고한다.
- **검수 결속:** review run이 정확한 proxy bytes와 editorial fingerprint를 참조하고 기존 v2 세 관점 기록에 대응하게 한다. hash와 재생 로그는 파일 동일성/재생 범위의 근거이지 사람이 실제 이해했다는 증명은 아니다. reviewer의 구간별 관찰과 판정을 별도로 남긴다.

### 최소 시험과 전환 조건

- 합성 정상 A/V fixture와 원인 누락·발화 절단·동작 점프 결함 fixture를 사용한다. reviewer에는 정답 label을 먼저 주지 않고 관찰 위치·증상·근거를 받는다.
- renderer는 서로 다른 video/audio 범위, J/L handle, 짧은 sequence, 잘못된 source 범위, 지원하지 않는 연출을 검증한다. 각 도구 명령의 종료 코드·결과를 별도로 확인한다.
- 기술 결속은 proxy 교체·fingerprint 변경·중단된 재생·누락된 실제 검수에서 의미 pass가 만들어지지 않는지 확인한다.
- 기존 단계 0의 다섯 능력인 재생기·proxy·실제 reviewer·fingerprint 결속·Premiere operator/profile이 각각 입증돼야 한다. fixture상 Premiere 확인은 실제 백룸 XML의 앱 검수를 대신하지 않는다.
- **A1 성공:** 합성 source→독립 A/V proxy→실측/hash 결속의 기술 실행과 결함 주입 회귀가 통과한다. 실제 지각·앱 통과는 포함하지 않는다. **A2 성공:** 실제 reviewer의 정상 속도 관찰과 Premiere operator/profile 검증이 별도로 입증된다. 다섯 능력 중 하나라도 미확인이면 단계 B로 가지 않는다. 기술 시험용 조각은 사용자 편집 결과가 아니다.

## 4. 단계 B — 비용을 통제하며 편집 문법 증명: E3·E4

- 진입: 단계 A 통과, 정확한 실제 입력 접근과 이번 산출물/편집 범위를 확인한다. 기존 전체 설계에서 대응하는 원본 분석·구성·문법 증명 구간을 수행하며 별도 경쟁 계획을 만들지 않는다.
- 작업: 전편 로컬 index·가속 discovery로 시간 구간을 분류하고, 채택 후보·양쪽 handle·인과/공간 bridge·발화 경계·동일 공간 점프·불확실 구간을 실제 1배속 A/V로 확인한다. 저위험 제외 구간의 자동 분류를 의미 확인으로 승격하지 않는다.
- 보존: 사건의 발견·원인·행동·결과와 필요한 공간 연결을 먼저 확보한다. 그 안에서 의미 없는 혼잣말·반복·진행 없는 이동을 microbeat 단위로 유지/축소/제거/분할한다. 기능 있는 무음과 기존 자연스러움은 삭제량 목표보다 우선한다.
- 경계: 실제 source의 호흡·환경음·동작 연결을 사용한다. J/L cut은 화면/음성의 역할이 다를 때 선택하고, 화면 점프가 계속되면 음성 분리만으로 해결됐다고 하지 않는다.
- 시간: 원문과 source/timeline·단위·점/범위를 보존한다. 결과를 크게 바꾸는 모호성만 질문한다. 과거 revision의 시각을 새 revision에 그대로 적용하지 않는다.
- 비용: 입력 길이, indexing 시간, 실제 정상 속도 검수 시간, 불확실 구간과 수정 재검수 범위를 측정한다. 첫 실제 작업을 기준선으로 삼고 절감률을 미리 주장하지 않는다. 비용이 커지면 이유와 확대 범위를 보고하며 필수 검수를 몰래 줄이지 않는다.
- 증명: 필요한 경우 기존 승인 계약에 따라 가장 작은 대표 연속 장에서 문법을 검증한다. 이미 유효한 exact 문법 승인 근거가 있으면 규칙이 허용하는 범위에서 재사용하고 매번 calibration을 다시 만들지 않는다. calibration은 전체 결과가 아니다.
- **성공:** 원인 없는 반응·공간 단절·발화 절단·거친 화면 연결이 대표 위험 사례에서 해결되고, 필요한 방향 승인과 실제 검수 근거가 분리돼 있다. 허용된 확장 범위가 확인된 경우에만 단계 C로 간다.

## 5. 단계 C — 단일 결과와 근거 수준별 전달: E5·E6

- 진입: 단계 B의 실제 문법 증명과 필요한 전체 편집 위임이 확인됐다.
- 작업: 기존 전체 설계의 전체 편집·최종 QA 순서를 따른다. 수정 중에는 변경 경계/scene/chapter와 인접 문맥을 검수하고, 안정된 최신 fingerprint의 완성 sequence 전체를 1배속으로 한 번 보며 세 관점을 기록한다. 세 관점을 이유로 세 번 전편 재생하지 않는다.
- 무효화: editorial 변경 뒤 과거 의미 pass를 재사용하지 않는다. 영향 범위 검수는 중간 QA이며 최신 최종 전편 검수와 구분한다. editorial identity가 같은 delivery-only 재생성은 기존 계약에 따라 불필요한 의미 재검수를 피한다.
- 검증: 정확한 proxy→v2→XML의 source/clip/A/V mapping을 확인한다. 기존 guarded writer의 source lock·reference·approval·non-overwrite 보장을 우회하지 않는다. 실제 Premiere import·online media·track/link·전체 재생은 별도 앱 검수다.
- 전달: 요청된 범위의 단일 sequence XML 하나와 그 폴더 링크를 제공한다. 내부 timeline JSON·proxy·검토 자료를 추가 전달물로 떠넘기지 않는다. 내부 기술자료는 승인된 수명·보호 경계를 따르고 자동 삭제하지 않는다.
- 보고: `기술 / 의미 / Premiere / 사용자 승인`을 각각 근거·대상·미실행 상태와 함께 보고한다. 실제 정상 속도 의미 검수가 없으면 편집 품질은 `not_scored`다. 사용자 승인 전에는 승인본·최종 완료본으로 부르지 않는다.
- **성공:** 정확한 전체 revision의 선택된 기술·의미·앱 검사와 요청된 승인 수준을 충족한다. 도구 구현 완료, 검토용 XML 전달, 사용자 승인 전체 완료는 서로 다른 완료 수준이다.

## 6. 변경 대상과 회귀 계획

| 변경 표면 | 재사용/보완 대상 | 최소 확인 |
|---|---|---|
| runtime 선택 | `extension/src/local_runtime.py`, `extension/config/local-runtime-v1.json`, `extension/tests/test_local_runtime.py` | 필요한 component 준비와 optional absent를 구분; 설치·비밀 접근 없음 |
| proxy 및 review 결속 | `extension/src/video_editing/`의 확인된 기존 경로 또는 최소 신규 모듈, 해당 합성 tests | A/V 범위·실측 정합성·불일치 차단·실제 review 한계 |
| v2 validation·전달 | `timeline_v2.py`, `delivery.py`, `cli.py`, `extension/schemas/video-edit-timeline-v2.schema.json`, `extension/tests/test_video_editing_timeline_v2.py` | schema/runtime 동기화, stale evidence·reviewer 불일치·잘못된 reference·불완전 검수의 전달 차단 |
| 사용자 요구 회귀 | 기존 전체 설계의 교정 목록, `extension/tests/test_video_editing_rule_gate.py` | 단위 오해·원인 삭제·공간 이동·오프닝 절단·발화 lead·화면 점프. 자동 검사는 구조만, 의미는 실제 A/V |
| 상태·문서 | 해당 worktree의 `SESSION_HANDOFF.md`, 기존 전체 설계·workflow 계약 | 실제 Git·승인·차단에 맞는 재개 지점; 규칙과 완료 이력 복제 없음 |

구현 전에 각 단계의 실제 명령·실행 경로·필수 검사를 기존 CLI와 테스트 runner에서 확인한다. 공개 계약/CLI·schema·전달 경로에 영향이 있으면 관련 통합 검사를 추가하고, 전체 `scripts/verify.py`는 실제 영향 범위가 요구할 때 선택한다. Core 내부 helper를 Host 검사 지름길로 사용하지 않는다.

검사 실패는 상세 결과 확인→원인 분류→최소 수정→관련 검사→선택된 최종 통합 순서로 처리한다. 기술 fixture 통과를 실제 영상 품질 또는 실제 Premiere 검증으로 승격하지 않는다.

## 7. 재개·중단·승인과 종료

- 단계별 성공·차단·작업 전환 시 실제 파일과 Git을 확인해 현재 상태를 갱신한다. 뒤 단계가 끝날 때까지 기록을 미루지 않는다. 커밋이 위임되지 않았으면 same-workspace 의존을 정확히 남긴다.
- 사용자 변경과 기존 결과를 보존한다. 실패 후보를 current/approved로 승격하지 않으며, source/state owner 최신성이 미확인일 때 bundle 내부 검증만으로 전역 최신 승인이라고 말하지 않는다. canonical resolver 확대는 실제 필요와 별도 범위를 먼저 정한다.
- Core 변경 없이 가능한 E1–E6은 독립적으로 진행할 수 있다. 공통 Core 계약을 Extension 규칙에 복제하지 않는다.
- 실제 A/V 검수 불가, 잘못된 source mapping, 의미/앱 실패, 권한 부재는 해당 단계의 중단 조건이다. 기본 편집 결함은 에이전트가 해결하고, 실제 창작 손실의 선택·결과를 바꾸는 시간 모호성·새 보호/외부/환경 권한만 사용자에게 요청한다.
- 개선 효과는 false semantic pass 차단, 작은 실제 end-to-end 성공, 최신 revision에 결속된 검수, 사용자 교정 결함의 재발 여부, 검수 비용 실측으로 판정한다. 테스트 개수·문서 수·자기점수 상승은 성과 지표가 아니다.

이번 문서 작성 후의 첫 구현 후보는 **단계 A의 실제 worktree/상태 대조와 가장 작은 비보호 proxy·review 연결 증명**이다. 문서 작성 완료를 이 단계의 착수나 통과로 표현하지 않는다.
