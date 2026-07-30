# M0 규칙 보존 지도

- 문서 분류: `reference-evidence`
- 상태: `active-for-M0`
- startup-required: 아니오. M0 phase가 exact 행을 지목할 때만 읽는다.
- owner: `M0_RULE_LINEAGE_AND_LOSS_AUDIT.md`
- 독자: M0 판정·M1 변경안·M2 의미 보존 검증을 수행하는 agent와 승인자.
- 역할: baseline, 의미 단위, Git lineage, 교차검증 판정을 한 행 단위로 소유한다.
- 보존: M0~M2 동안 유지하고 M3 종료 때 historical로 전환해 active route에서 제거한다.
- 권위: 증거 기록이며 정책·현재 상태·Core 승인·다음 행동 owner가 아니다.
- 현재 reviewer: 이 저장소에서 재측정을 수행하는 현재 세션 agent. source 저자(Claude 보고서 작성자)와 분리하며, 행마다 판정 주체를 source·current reviewer로 구분해 적는다.

## 기록 규칙

- 한 행은 `trigger / protected outcome / action / exception / verification / canonical owner / source anchor / evidence label / disposition`을 갖는다.
- 문장 일치가 아니라 보호 의미의 생존 여부를 판정한다. 같은 의미가 여러 owner에 있으면 중복으로, owner가 없으면 공백으로 기록한다.
- evidence label은 `direct-remeasurement / repository-source / git-lineage / shared-source-agreement / report-only / unresolved` 중 하나다.
- disposition은 `preserved / migrated / superseded / task-specific / unsafe-outdated / candidate-loss` 중 하나다.
- 보고서나 과거 규칙은 evidence이며 현재 권위가 아니다. 원문·명령 로그·전체 commit narrative는 복제하지 않고 exact path·commit만 가리킨다.
- 행 입도는 phase-design `D3`을, 이 문서의 상한은 `D4`를 따른다. `M0-S1` 실측으로 두 수치를 **확정**했다: 파일당 최대 11행이 관측되어 `D3`의 12행 상한이 유효하고, 전체 78행 기록 뒤에도 `D4`의 400줄·30,000자에 여유가 있다(199줄·18,023자). 상한에 닿으면 행을 늘리지 말고 입도를 상향한다.

## corpus 정의

측정: 2026-07-30, 작업트리 기준(미커밋 포함), 현재 reviewer 직접 재측정. 재현 명령과 정렬된 파일 목록이 없는 수치는 후속 성공 기준의 근거가 될 수 없다.

| corpus | exact glob | 용도 | 파일 수 | 토큰 수 | 문자 수 |
|---|---|---|---:|---:|---:|
| `rule-surface` | `PROJECT_RULES.md`, `core/rules/*.md`, `extension/rules/*.md`, `extension/README.md` | 의미 인벤토리 대상 | 19 | 9,650 | 58,813 |
| `normative-corpus` | `rule-surface` + `core/failures/*.md` + `core/docs/**/*.md` + `extension/docs/**/*.md` − candidate | 읽기 비용 기준 | 37 | 18,433 | — |
| `candidate/reference` | `extension/docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md` | 판정 제외 | 1 | 675 | 2,772 |

재현 명령: UTF-8 디코드 후 공백 분리 토큰 수와 `len(text)` 문자 수를 파일별로 출력하고 정렬된 경로 목록을 함께 남긴다. 같은 glob을 `git show HEAD:<path>`로 측정하면 `normative-corpus`는 37파일·18,010토큰이다.

기존 수치 판정(`direct-remeasurement`): `37파일·18,844단어`와 보고서의 `19,519단어` 모두 **재현되지 않았다.** 파일 수 37은 일치하나 토큰 수는 작업트리 18,433, HEAD 18,010으로 어느 쪽과도 맞지 않는다. 두 수치 모두 산출 glob과 명령이 기록되지 않아 재구성할 수 없으므로 `unresolved`로 두고, 후속 성공 기준은 위 표의 값만 사용한다. 이전 세션의 `18,844 + 675 = 19,519` 계산은 candidate가 이미 제외된 값에서 candidate를 다시 빼는 이중 차감으로 보이나 원본 정의가 없어 확정하지 않는다.

제거 후보 인벤토리(기록 전용). 사용자 지시에 따라 이 이니셔티브의 어떤 단계에서도 삭제·이동하지 않으며, 전체 완료 뒤 exact 목록으로 승인을 받아 처분한다.

| 후보 | 수 | startup route 연결 | 상태 |
|---|---:|---|---|
| `extension/work/project-foundation/M0~M6` | 7 | 없음 | 완료된 이전 이니셔티브 phase-design |
| `extension/work/PROJECT_FOUNDATION_DESIGN.md` | 1 | 없음 | 위 이니셔티브의 overall-design, 완료 |
| `extension/reports/*` | 12 | 없음(1건은 설계가 참조) | 시점 보고서, 약 212KB |
| `docs.md`, `codex_2026-07-28_문서기반_개선_plan` | 2 | 없음 | 0-byte |
| `extension/work/2026-06-30-00-23-03/` | 1 | 없음 | 빈 디렉토리 |

## handoff baseline

기준: branch `main`, 준비 checkpoint의 부모 HEAD `3810abc`. 표의 status는 commit 전 상태이고 SHA-256은 commit할 byte anchor다. 사용자 지시에 따라 기존 작업 내용을 되돌리지 않고 방향·overall·phase·handoff·M4 route·Core 4경로를 같은 checkpoint에 보존해 handoff mode를 `portable`로 전환한다.

| path | status | ownership | SHA-256 / anchor |
|---|---|---|---|
| `PROJECT_RULES.md` | `M` | entry 이전 변경을 보존하고 이번 방향 reference route만 추가; M0 실행 변경 금지 | `725beca47d5a8d53ce35817e7193459ea11f6002640a5c1858761845951794cd` |
| `PROJECT_DIRECTION.md` | `??` | Codex 직접 사용자 발언 3개 작업과 현재 교정으로 재구성한 장기 방향 reference | `0c0f4264176915231d40d2bbdc30fa258eb1429c2258e5116b95d90c4a5bbc7d` |
| `README.md` | `M` | 방향 reference 사용자 탐색 link | `1e7c8a1d49dd502d26668043189e0c14e72e39bf10718600bd69ae5d8a2ac619` |
| `core/rules/document-work.md` | `M` | entry 이전 Core 변경; M0 비소유 | `c29ba6d3796db5b08bf84f55e83fdd61796bb4d0f663dca468c774fac1f30a9b` |
| `core/rules/rule-governance.md` | `M` | 중단된 외부 세션 변경이지만 사용자 지시에 따라 되돌리지 않고 checkpoint에 보존 | `b5b68e8268da424b72a9c7b61539efd4583fc93b679d70da44f9f64b8334f63e` |
| `core/tests/test_rule_routing.py` | `M` | entry 이전 Core 변경; M0 비소유 | `1d618aa1ed5a71c5669a15eb5345867dc83b475ec6a96b5c7e9c75eb18b764c1` |
| `core/rules/staged-work-design.md` | `??` | 이번 설계에서 exact 승인된 Core owner; M0 실행 변경 금지 | `83d8dbe22e0e45c9910f346d2843130a7269c8b4cd5a94ae758df4cc17c453bb` |
| `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md` | `??` | 사용자 제공 reference; 읽기 전용 | `9e3d2901df618c2e5dce0d4ab23329c55c9af97d933c209860495b14e09a0d4e` |
| `SESSION_HANDOFF.md` | `M` | current-state owner; portable checkpoint·M0-S2·M4 경계 교정 | `c1fa8ac1b9444f597380fdaf83a1f7ebb5e2a21b70b5a5618c0b8a3c3d52193a` |
| `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md` | `??` | 문서 제거 1차 목표와 완료 후 M4 처분을 소유하는 overall-design | `f2237390752a113dcd93ca5ff77a950734497b03f126ba00df0abe3d462d8b92` |
| `extension/work/rule-preservation/M0_RULE_LINEAGE_AND_LOSS_AUDIT.md` | `??` | `M0-S1` passed·`M0-S2` unstarted phase-design | `8656026972f8aa495996232c947b2ffbc9f8c999658c9a9bfb5e1498264fe23a` |
| `extension/tests/test_staged_design_routing.py` | `M` | M0~M4 단계·위임·portable route 구조 회귀 검증 | `69973c2facb1d045a1849020ea1d4071b4b9824dc2803f5adeac3de5efe755b9` |
| 이 파일 | `??` | M0 evidence owner; M0-S1~S4에서 변경 허용 | self; slice 시작·종료 SHA-256 대조 |

준비 checkpoint 전 `D5`에 따라 untracked 5건(`PROJECT_DIRECTION.md`, `core/rules/staged-work-design.md`, Claude 보고서, overall-design, phase-design)과 이 파일은 `git diff` 대상이 아니었다. 이들은 위 앵커의 SHA-256 대조로 검증한 뒤 같은 checkpoint에 포함한다.

준비 checkpoint 전 기본 `maintenance-verify`는 Core 4경로 때문에 `core_change_required`를 반환했다. 사용자가 기존 작업 보존과 commit을 지시한 뒤 Core 139개·Extension 132개와 `maintenance-verify --allow-core-changes`가 통과했다. commit 뒤 M0는 기본 maintenance를 사용하며 새 Core diff가 추가되지 않았는지 확인한다.

## 의미 보존 schema

행이 넓어져 두 표로 나눈다. 같은 `ID`로 결합하며 한 의미는 여전히 한 행이다. 아래 표는 `M0-S1`이 채우고, source anchor·evidence·disposition·M1 decision은 `M0-S2`·`M0-S3`이 채운다.

### S1 인벤토리 — rule-surface 19파일 / 78개 의미

| ID | trigger | protected outcome | action·exception | verification | current owner |
|---|---|---|---|---|---|
| F01-1 | 새 세션 시작 | 시작 문맥이 작고 현재 상태를 정확히 고른다 | 정책 1회 통독, git root_name으로 상태 문서 분기 | branch명에 의존하지 않음 | `PROJECT_RULES` 시작·라우팅 |
| F01-2 | 작업 착수 | 과잉 절차로 비용이 늘지 않는다 | 최저 충분 등급 선택; quick·standard에 번호계획·점수·보고서·commit 금지 | 등급과 실제 절차 일치 | 동 |
| F01-3 | 행동이 규칙 트리거에 해당 | 필요한 규칙만 읽어 문맥 비용 억제 | 매칭 표의 규칙만 논리작업당 1회 통독 | 미매칭 규칙 본문 미열람 | 동 |
| F01-4 | 목표·우선순위 판단 | 프로젝트가 수동작업 절감 결과에 정렬 | 권위 순서 = 최신 지시 > 정책 > 활성 owner | 충돌을 순서대로 해소 | `PROJECT_RULES` Outcome |
| F01-5 | 요청 범위 밖 개선 유혹 | 승인되지 않은 확대 방지 | 요청 결과만 수행 | scoped diff | 동 |
| F01-6 | 질문할지 판단 | 불필요한 확인으로 자율성 저하 방지 | 승인 결과 변경·경계 통과·비가역 위험일 때만 질문 | 질문 사유가 셋 중 하나 | 동 |
| F01-7 | 삭제·이동·push·설치·외부쓰기 | 비가역·외부 효과의 사용자 통제 | 사전 승인 필수; 무관한 변경 보존 | 승인 기록 존재 | `PROJECT_RULES` Approval |
| F01-8 | `core/**` 변경 시도 | 기반 불변성 | 현재 대화 exact 승인 필요; 자동작업은 `core_change_required`로 실패 기록 | 실패 기록과 비성공 종료 | `PROJECT_RULES` Core |
| F01-9 | `inputs`·`outputs` 접근 | 사용자 원본 보호 | exact 대상·목적 없이 접근 금지; stage·commit 금지 | 보호 경로 미포함 | `PROJECT_RULES` Protected |
| F01-10 | 정보 기록 위치 판단 | 중복 권위와 탐색 비용 방지 | 재개·운영·감사에 필요한 사실만; owner 하나, 나머지는 링크 | 중복 owner 0 | `PROJECT_RULES` Ownership |
| F01-11 | 변경 완료 시점 | 미검증을 통과로 세지 않음 | 위험 비례 검증; 3연속 실패 시 방법 변경 | 검사 실행 증거 | `PROJECT_RULES` Verification |
| F02-1 | foundation·domain 문서를 함께 읽음 | 두 영역이 독립적으로 탐색 가능 | 상위 router 경유; 상호 직접 라우팅 금지 | 직접 link·route 0 | `boundary-routing` BND01 |
| F02-2 | 경계 참조 필요 | 참조 성격을 숨기지 않음 | 6종 분류; navigation·routing은 상위 router로 이동 | 이유·owner·방향 기록 | BND02 |
| F02-3 | 기존 owner로 표현 안 되는 경계 참조 | 무근거 경계 확장 방지 | 기존 interface 검색, trigger·owner·수명·대체경로 확정; 단일 작업 사실은 승격 금지 | router·회귀 반영 | BND03 |
| F02-4 | 경계 변경 구현·완료 판정 | 한쪽만 보고 완료 선언하지 않음 | 정해진 5단계 읽기 순서, 각 1회 | 양쪽 scan + 회귀 | BND04 |
| F03-1 | `core/**` 변경 필요 판단 | 승인 없는 기반 변경 차단 | 경로 확정 → extension-only 불가 이유 → 현재 대화 승인 확인 → 최소 범위만 | 승인 범위와 diff 일치 | `core-change-control` Decision |
| F03-2 | 무인·자동 작업이 core 변경 필요 | 자동 작업이 승인을 추정·대기하지 않음 | core 미변경, 실패 기록 append, 비성공 반환, 목표 중단 | `core_change_required` 코드 | 동 Automatic failure record |
| F03-3 | 승인된 core 변경 완료 | 부분 검증으로 통과 선언 방지 | Core·Extension 회귀 + `maintenance-verify --allow-core-changes` | 3개 명령 전부 통과 | 동 Approved gate |
| F04-1 | 보고서·에이전트 결론 대조 | 증거 강도를 과장하지 않음 | 4종 라벨 분류; shared-source를 독립 확증으로 세지 않음 | 결론마다 라벨 | `cross-validation` labels |
| F04-2 | 교차검증 수행 | 출처와 현재 검토자 혼동 방지 | 현재 세션에서 reviewer 식별; 1차 자료 우선; 모순·미검증 명시 | 저자·reviewer·방법 분리 | 동 Rules |
| F04-3 | 결론 확정 직전 | 낡은 동적 수치로 판정하지 않음 | identity·date·revision·수치 재확인 | 재확인 기록 | 동 Verification |
| F05-1 | 유지 문서 작성 전 | 문서가 작업 산출물이 되지 않음 | owner·경로·목적·독자·개수를 먼저 고정 | artifact budget 일치 | `document-work` General |
| F05-2 | controlled work 첫 mutation 전 | 규칙 미적용 상태의 변경 방지 | controlling 문서 EOF 통독 후 적용 조항·충돌을 활성 계획에 기록 | 기록 존재 | 동 |
| F05-3 | 보고만 요청받음 | 요청 범위 초과 방지 | 그 보고서만 authorize; 구현·규칙변경·sidecar 금지 | 산출물 수 일치 | 동 |
| F05-4 | 새 문서 생성 유혹 | 중복 owner 방지 | 정본 owner 확인 후 갱신 우선; 고유 목적·독자가 있을 때만 신설 | 단일 owner | 동 |
| F05-5 | 현재 상태 변경 | 완료 상세가 시작 경로에 쌓이지 않음 | 선택된 상태 문서만 갱신; 완료 상세 제거 | 시작 경로 크기 | 동 |
| F05-6 | 논리 배치 완료 | 무결성 결함 잔존 방지 | UTF-8·NUL·구조·링크·후행공백·scoped diff 검사; 완료 전 무의미 텍스트 압축 | 검사 통과 | 동 |
| F05-7 | 설계 문서 작성 | 세 역할 혼합 방지 | `overall-design`·`phase-design`·`reference-evidence` 중 하나로 분류하고 역할 경계 준수 | 분류와 내용 일치 | 동 Design rules |
| F05-8 | 필독 설계 라우팅 전 | 읽기 비용 폭증 방지 | overall 120줄·8,000자, phase 160줄·12,000자; 초과 시 요약+미독 본문 금지 | 줄·문자 계수 | 동 |
| F06-1 | 실패 기록 여부 판단 | 일회성 실수로 규칙이 늘지 않음 | 원인·해결 검증 + 재발·안전영향·비자명 재사용성·실질 차단 중 하나 충족 시에만 | 임계 충족 근거 | `failure-records` Threshold |
| F06-2 | 현재 차단 중인 실패 | 활성 blocker와 영구 지식 분리 | blocker·연속 횟수·재시작 조건은 상태 문서에, 해소되면 제거 | 상태 문서 기록 | 동 Rules |
| F06-3 | 새 실패 케이스 생성 | 같은 원인의 분산 방지 | README 검색 후 같은 root-cause owner에 병합 | 케이스 중복 0 | 동 |
| F06-4 | controlled 작업 완료 전 | 미해결을 해결로 보고하지 않음 | 미해결 blocker·임계 충족 실패 누락 확인 | 완료 전 점검 | 동 |
| F07-1 | 파일을 정리·삭제 후보로 분류 | 추출 전 삭제 방지 | 대상·변화·권한·복구·목적 고정 → 추출 규칙 먼저 → 4분류 → 승인 후에만 mutation | 판정마다 owner·복구·승인 | `file-cleanup` FCL01 |
| F07-2 | 계획·보고서·handoff를 삭제 후보로 확정 | 문서 소멸로 지식이 함께 사라지지 않음 | 성공 지식은 `조건/행동/예외/검증`으로 압축해 최협 owner에, 실패 지식은 6요소 갖출 때만 failure owner에; 유일 증거는 삭제 금지 | 후보마다 추출·owner·참조·복구·승인 | FCL02 |
| F07-3 | 정리 근거를 남기고 싶음 | 정리하며 문서가 늘지 않음 | sidecar 추출 보고서 신설 금지; 지식은 owner에, 상세는 Git에 | 신규 보고서 0 | FCL02 예외 |
| F08-1 | 파일에서 재사용 내용 추출 | 보호 경로·범위 확대 방지 | 대상·목적·읽기쓰기 범위·독자 먼저 고정; 지정 파일과 직접 연결 자료만 | 열람 범위 일치 | `file-extraction` FEX01.1-2 |
| F08-2 | 추출 내용 분류 | 일회성 사실의 규칙 승격 방지 | 8종 분류; 재사용 판단만 작업명·수치 제거 후 최협 owner에; 해시·경로·개별 선호는 evidence에 | 항목마다 라벨·owner·보류 이유 | FEX01.3-6 |
| F09-1 | 조건부 행동을 어디 둘지 판단 | 시작 문맥 팽창 방지 | 상시 경계만 정책에, 조건부는 최협 기존 owner에; 도메인 절차는 extension owner에 | 계층 판정 근거 | `rule-governance` Placement |
| F09-2 | 새 규칙 생성 검토 | 중복 규칙 증가 방지 | trigger·독자·책임·검증이 모두 구별될 때만 신설; 기존 owner 강화 우선 | 신설 사유 기록 | 동 Lifecycle·Creation |
| F09-3 | 규칙 파일 작성 | 역사 문서가 규칙으로 오인되지 않음 | `Purpose`·`Read when`·`Authority` + `조건/행동/예외/검증` 분리 | 필수 절 존재 | 동 Creation |
| F09-4 | 규칙 라우팅 | 고아·중복 route 방지 | 활성 규칙마다 route 정확히 하나; core·extension 상호 라우팅 금지; rename 시 같은 checkpoint에서 전부 갱신 | route 유일·링크 유효 | 동 Routing |
| F09-5 | 규칙 읽기 | 전체 규칙 preload 방지 | 매칭된 것만 EOF까지 1회; 참조는 확장 허가가 아님 | 미매칭 미열람 | 동 Reading |
| F09-6 | 사용자가 작업을 교정 | 낡은 규칙 선택으로 계속 진행 방지 | 예약 mutation 중단, 이전 선택 폐기, route 재계산 | 재계산 기록 | 동 Reading |
| F09-7 | controlled 작업 완료 전 | 경험이 규칙 개선으로 환류 | 매칭 규칙을 4분류로 감사; 별도 closeout 보고서 금지 | 4분류 판정 존재 | 동 Closeout |
| F10-1 | 다단계 작업 설계 | 활성 계획이 역사로 비대해지지 않음 | overall 1 + active phase 최대 1 + 상태 문서; 긴 분석은 선택적 evidence | 라우팅된 문서 수 | `staged-work-design` Topology |
| F10-2 | overall-design 작성 | 진행 상태·명령 로그 혼입 방지 | 결과·불변식·금지 확대·단계 순서·한 줄 결과만 | 역할 경계 준수 | 동 Overall |
| F10-3 | phase-design 작성 | 미래 단계 상세 선작성 방지 | 현재 또는 즉시 활성화 후보 단계만; lifecycle 7종 명시 | 활성 phase 0 또는 1 | 동 Phase |
| F10-4 | 단계 진행·전환 | 실행 종료를 통과로 오인하지 않음 | entry·slice·exit·transition 4 gate; exit 통과·상태 갱신 후에만 다음 단계 | 4 gate 존재 | 동 Gate |
| F10-5 | 사용자 교정으로 결과·범위·gate 변경 | 무효 설계로 계속 실행 방지 | mutation 중단, `invalidated` 표시, 설계 개정, 신규 승인 획득 | 무효화 기록 | 동 Gate |
| F10-6 | 다른 agent·세션에 위임 | 대화 원문 없이 재개 가능 | 목표·의도·범위·승인·gate·정지조건·기각 대안 보존; handoff mode 정직 선언; baseline 동결; 예상 실패 라벨 | 위임 gate 통과 | 동 Delegation |
| F10-7 | 다른 대화의 승인 재사용 유혹 | 승인 전이 방지 | 요약·암시로 전이 금지; 현재 대화에서 재획득 | 승인 출처 기록 | 동 Delegation |
| F11-1 | 보호 항목 접근 승인 후 | 원본 훼손·범위 확대 방지 | exact 항목·결과·읽기쓰기·목적지 확인; sibling 열거 금지; 원본 덮어쓰기·이동·삭제 금지 | 접근 항목이 승인 부분집합 | `user-data-work` |
| F11-2 | 보호 작업 결과 보고 | 보호 내용의 재사용물 유출 방지 | 원본은 `inputs`, 결과는 `outputs`; 규칙·보고서·캐시에 복제 금지 | staged diff에 보호 경로 0 | 동 |
| F12-1 | stage·commit·branch·push | 승인 없는 Git 쓰기 방지 | 추적 가능한 승인 또는 범위 명시된 상시 절차; 승인 경로만 stage | 승인·diff 일치 | `version-control` Rules |
| F12-2 | 다른 세션의 미커밋 변경에 접촉 | 타 작업 소실 방지 | 대상 확정·diff 확인·복구본 확인·현재 승인 확인; 하나라도 없으면 미접촉 | 조건 4개 확인 | 동 |
| F12-3 | 백업 요청 | 저장소 내부 복제본 누적 방지 | 복사·이동·복구 스냅샷 구분; 저장소 밖에 배치; 개수·해시 검증 | 유지 파일이 백업에 의존 안 함 | 동 Backup |
| F13-1 | 실제 작업 기능·데이터 생성 | core 오염 방지 | extension 영역에 추가; extension 작업을 이유로 core 자동 변경 금지 | core diff 0 | `extension/README` 배치 |
| F13-2 | 영상 작업 시작 | 두 계약 범위 혼합 방지 | evidence pack 계약과 영상 편집 workflow 계약을 분리 사용 | 계약 경계 준수 | 동 활성 영상 owner |
| F13-3 | 영상 편집 행동 선택 | 도메인 규칙 과잉 로딩 방지 | 계약 통독 후 행동에 일치하는 규칙만 1회 | 미매칭 미열람 | 동 조건부 라우팅 |
| F13-4 | extension이 foundation 필요 | 역방향 의존 방지 | 승인된 foundation interface만 사용; foundation은 extension을 import·소유하지 않음 | 의존 방향 검사 | 동 Core 의존 경계 |
| F14-1 | 영구 증거·timeline·XML·검토본 생성 | 요청 안 한 파생 파일 증가 방지 | exact 원본에서 직접 유도; 약속한 산출물만; 기존 출력 기본 미덮어쓰기 | 원본 외 source 0, 미요청 미디어 0 | `artifact-lineage` R04 |
| F14-2 | 분석 자료 보존 판단 | 세션 원문이 운영 의존이 되지 않음 | 보호 파생물은 Git 제외; cache·RMS·임시 frame은 재생성 가능 runtime; 단일 영상 수치는 일반 규칙에 복사 금지 | 자료 분류·명명 규칙 | 동 수명 |
| F15-1 | 발화 근처·자막 cue 내부 절단 | 청취 확인 없는 기계적 절단 방지 | 호흡·완결 절·정보 단위에서 자르고 실제 오디오 청취; SRT·ASR은 탐색 보조 | 파편 잔존 여부를 정상 속도로 확인 | `boundary-quality` R08 |
| F15-2 | `튄다`·`부자연스럽다` 피드백 | 수치로 원인을 추정하지 않음 | 원본 화면·동작·밝기·오디오로 원인 확정; frame sample·RMS는 후보 탐색 보조 | 같은 감각 채널에서 해소 확인 | 동 R10 |
| F16-1 | 사용자가 증상과 방법·수치를 함께 말함 | 방법이 결과 계약을 대체하지 않음 | `증상`·`제안 방법`·`수치`로 분리, 증상을 계약으로; 수치는 3종 라벨 | 다른 방법으로도 증상 해결 가능한지 설명 | `intake` R01 |
| F16-2 | 새 지시가 이전 계획과 다름 | 낡은 계획 고수 방지 | 결과가 명확한 최신 지시 우선; 보호·비가역 충돌 시 `충돌/잃는 것/최소 선택지` 보고 | 적용·보류를 한 문장으로 구분 | 동 R02 |
| F16-3 | 원본·파생 결과를 새로 열거나 다음 단계 진입 | 방향 미확정 상태의 보호 데이터 확대 방지 | 항목·목적·산출물·종료조건 확정 후 지정 범위만; 방향 미정이면 1차 분석 후 최대 3개 방향 비교; 에이전트 추천은 승인이 아님 | 접근·생성이 승인 목록의 부분집합 | 동 R03 |
| F17-1 | 사용자 수정본 제공·승인 범위 재편집 | 사용자 수정의 자동 복원 방지 | 수정 범위 우선 보존, 그 범위와 인접 경계의 이전 승인 무효화 | 5개 필드로 승인 추적 | `state-and-approval` R11 |
| F17-2 | 새 revision 채택·중단 작업 재개 | 여러 revision 동시 편집 방지 | 한 owner에서 current 갱신, 그 revision만 후속 입력; 이전은 읽기 전용 동결 | 이전 revision 해시 불변 | 동 R13 |
| F17-3 | 문서들이 서로 다른 current를 가리킴 | 충돌 상태의 산출물 생성 방지 | `state_owner_conflict`로 편집·승인·XML 중단 후 owner 복구 | 활성 참조 충돌 0 | 동 R14 |
| F18-1 | 사건 후보 범위 확정 | 후보를 완성 컷으로 오인하지 않음 | 1차 내용 지도와 2차 상세 분석 분리; 후보마다 anchor·기능·유지 이유·위험 | 후보마다 검수 상태 명시 | `story-and-cut` R05 |
| F18-2 | 압축·삭제가 인과·상태·공간을 건드림 | 시청자 이해의 최소 연결 보존 | 스파인 고정 후 원인·시도·결과 순서 보존; 원본에 없는 감정·효과 추가 금지 | 순차 재생으로 `왜/어디서/무엇이` 답변 가능 | 동 R06 |
| F18-3 | 긴 후보에 설명·UI·반복 포함 | 고정 길이 기준의 전역화 방지 | 새 정보·행동 박자·반응·화면 변화·발화 절에서 분할; 최종 인아웃은 실제 재생으로 | 분할·유지 이유가 실제 변화와 대응 | 동 R07 |
| F18-4 | 같은 감정·행동 반복 | 수치만으로 저가치 판정 방지 | 전달된 반응·진행 없는 반복부터 축소; 새 상황 첫 반응은 유지 | 삭제 전후 새 정보·감정 변화 비교 | 동 R09 |
| F19-1 | timeline·XML·검토본을 성공으로 보고 | 기술 통과를 의미 통과로 오인하지 않음 | 구조·디코딩·길이·링크 검증과 의미 검수를 별도 결과로; 미적용은 `해당 없음` | 둘 다 통과 전 완료 보고 금지 | `validation-delivery` R12 |
| F19-2 | 검증 결과를 상태로 기록 | 상위 단계 자동 추론 방지 | `semantic → structure → media → app → user` 중 증거 있는 단계만 기록 | 보고 문구가 최고 검증 단계 이하 | 동 R15 |
| F19-3 | 새 validator 추가·검사 묶음 | 계층 혼합 합격 방지 | `비보호 구조/선언 metadata/보호 미디어/의미 검수`로 분류해 독립 반환 | 보호 미디어 검사는 승인 없이 미실행 | 동 R16 |

## M0-S2 직접 계보 결과

- checked-at: `2026-07-31 Asia/Seoul`; reviewer는 이 세션의 Codex agent이며 Claude 보고서 저자와 분리한다.
- 현재 19파일을 `git log --follow`로 조회해 78개 source anchor와 successor를 기록했다. 전환·삭제 4건은 아래 predecessor 표로 보완했고 `backup/**` bulk read는 0건이다.

### S2·S3 판정

| ID | source anchor | evidence | disposition | M1 decision |
|---|---|---|---|---|
| F01-1 | `e6c6328:PROJECT_RULES.md#L7` | git-lineage | preserved | retain |
| F01-2 | `e6c6328:PROJECT_RULES.md#L18` | git-lineage | preserved | retain |
| F01-3 | `e6c6328:PROJECT_RULES.md#L20` | git-lineage | preserved | retain |
| F01-4 | `3db88dd:PROJECT_RULES.md#L43` | git-lineage | preserved | retain |
| F01-5 | `3db88dd:PROJECT_RULES.md#L47` | git-lineage | preserved | retain |
| F01-6 | `c5c078a:PROJECT_RULES.md#L51` | git-lineage | preserved | retain |
| F01-7 | `c5c078a:PROJECT_RULES.md#L53` | git-lineage | preserved | retain |
| F01-8 | `f9b244c:PROJECT_RULES.md#L59` | git-lineage | preserved | retain |
| F01-9 | `8dc034e:PROJECT_RULES.md#L68` | git-lineage | preserved | retain |
| F01-10 | `3db88dd:PROJECT_RULES.md#L74` | git-lineage | preserved | retain |
| F01-11 | `153758f:PROJECT_RULES.md#L87` | git-lineage | preserved | retain |
| F02-1 | `8ae37b5:core/rules/boundary-routing-and-dependency.md#L7` | git-lineage | preserved | retain |
| F02-2 | `8ae37b5:core/rules/boundary-routing-and-dependency.md#L14` | git-lineage | preserved | retain |
| F02-3 | `8ae37b5:core/rules/boundary-routing-and-dependency.md#L21` | git-lineage | preserved | retain |
| F02-4 | `8ae37b5:core/rules/boundary-routing-and-dependency.md#L28` | git-lineage | preserved | retain |
| F03-1 | `f9b244c:core/rules/core-change-control.md#L7` | git-lineage | preserved | retain |
| F03-2 | `f9b244c:core/rules/core-change-control.md#L17` | git-lineage | preserved | retain |
| F03-3 | `f9b244c:core/rules/core-change-control.md#L33` | git-lineage | preserved | retain |
| F04-1 | `25237fe:core/rules/cross-validation.md#L7` | git-lineage | preserved | retain |
| F04-2 | `25237fe:core/rules/cross-validation.md#L18` | git-lineage | preserved | retain |
| F04-3 | `25237fe:core/rules/cross-validation.md#L29` | git-lineage | preserved | retain |
| F05-1 | `f6e180d:core/rules/document-work.md#L7` | git-lineage | preserved | retain |
| F05-2 | `06a2adc:core/rules/document-work.md#L10` | git-lineage | preserved | retain |
| F05-3 | `12f7bc6:core/rules/document-work.md#L11` | git-lineage | preserved | retain |
| F05-4 | `3db88dd:core/rules/document-work.md#L12` | git-lineage | preserved | retain |
| F05-5 | `06a2adc:core/rules/document-work.md#L15` | git-lineage | preserved | retain |
| F05-6 | `153758f:core/rules/document-work.md#L20` | git-lineage | preserved | retain |
| F05-7 | `f6e180d:core/rules/document-work.md#L24` | git-lineage | preserved | retain |
| F05-8 | `f6e180d:core/rules/document-work.md#L32` | git-lineage | preserved | retain |
| F06-1 | `153758f:core/rules/failure-records.md#L7` | git-lineage | preserved | retain |
| F06-2 | `8dc034e:core/rules/failure-records.md#L18` | git-lineage | preserved | retain |
| F06-3 | `8dc034e:core/rules/failure-records.md#L18` | git-lineage | preserved | retain |
| F06-4 | `8dc034e:core/rules/failure-records.md#L18` | git-lineage | preserved | retain |
| F07-1 | `8ae37b5:core/rules/file-cleanup.md#L7` | git-lineage | migrated | retain current core owner |
| F07-2 | `3633551:core/rules/file-cleanup.md#L27` | git-lineage | migrated | retain current core owner |
| F07-3 | `8ae37b5:core/rules/file-cleanup.md#L48` | git-lineage | migrated | retain current core owner |
| F08-1 | `07a26a3:extension/rules/file-extraction.md→core/rules/file-extraction.md#L7` | git-lineage | migrated | retain current core owner |
| F08-2 | `07a26a3:extension/rules/file-extraction.md→core/rules/file-extraction.md#L28` | git-lineage | migrated | retain current core owner |
| F09-1 | `25237fe:core/rules/rule-governance.md#L7` | git-lineage | preserved | retain |
| F09-2 | `8ae37b5:core/rules/rule-governance.md#L20` | git-lineage | preserved | retain |
| F09-3 | `8ae37b5:core/rules/rule-governance.md#L32` | git-lineage | preserved | retain |
| F09-4 | `8ae37b5:core/rules/rule-governance.md#L42` | git-lineage | preserved | retain |
| F09-5 | `8ae37b5:core/rules/rule-governance.md#L51` | git-lineage | preserved | retain |
| F09-6 | `06a2adc:core/rules/rule-governance.md#L51` | git-lineage | preserved | retain |
| F09-7 | `25237fe:core/rules/rule-governance.md#L77` | git-lineage | preserved | retain |
| F10-1 | `f6e180d:core/rules/staged-work-design.md#L7` | git-lineage | preserved | retain |
| F10-2 | `f6e180d:core/rules/staged-work-design.md#L14` | git-lineage | preserved | retain |
| F10-3 | `f6e180d:core/rules/staged-work-design.md#L21` | git-lineage | preserved | retain |
| F10-4 | `f6e180d:core/rules/staged-work-design.md#L29` | git-lineage | preserved | retain |
| F10-5 | `f6e180d:core/rules/staged-work-design.md#L29` | git-lineage | preserved | retain |
| F10-6 | `f6e180d:core/rules/staged-work-design.md#L43` | git-lineage | preserved | retain |
| F10-7 | `f6e180d:core/rules/staged-work-design.md#L43` | git-lineage | preserved | retain |
| F11-1 | `8dc034e:core/rules/user-data-work.md#L8` | git-lineage | preserved | retain |
| F11-2 | `8dc034e:core/rules/user-data-work.md#L8` | git-lineage | preserved | retain |
| F12-1 | `8dc034e:core/rules/version-control.md#L7` | git-lineage | preserved | retain |
| F12-2 | `8dc034e:core/rules/version-control.md#L7` | git-lineage | preserved | retain |
| F12-3 | `12f7bc6:core/rules/version-control.md#L20` | git-lineage | preserved | retain |
| F13-1 | `f9b244c:extension/README.md#L9` | git-lineage | preserved | retain |
| F13-2 | `532b41e:extension/README.md#L29` | git-lineage | preserved | retain |
| F13-3 | `a89a1dd:extension/README.md#L42` | git-lineage | preserved | retain |
| F13-4 | `8ae37b5:extension/README.md#L56` | git-lineage | preserved | retain |
| F14-1 | `a89a1dd:extension/rules/video-editing-artifact-lineage.md#L7` | git-lineage | preserved | retain |
| F14-2 | `a89a1dd:extension/rules/video-editing-artifact-lineage.md#L14` | git-lineage | preserved | retain |
| F15-1 | `a89a1dd:extension/rules/video-editing-boundary-quality.md#L7` | git-lineage | preserved | retain |
| F15-2 | `a89a1dd:extension/rules/video-editing-boundary-quality.md#L14` | git-lineage | preserved | retain |
| F16-1 | `a89a1dd:extension/rules/video-editing-intake-and-instructions.md#L7` | git-lineage | preserved | retain |
| F16-2 | `a89a1dd:extension/rules/video-editing-intake-and-instructions.md#L14` | git-lineage | preserved | retain |
| F16-3 | `a89a1dd:extension/rules/video-editing-intake-and-instructions.md#L21` | git-lineage | preserved | retain |
| F17-1 | `a89a1dd:extension/rules/video-editing-state-and-approval.md#L7` | git-lineage | preserved | retain |
| F17-2 | `a89a1dd:extension/rules/video-editing-state-and-approval.md#L14` | git-lineage | preserved | retain |
| F17-3 | `a89a1dd:extension/rules/video-editing-state-and-approval.md#L21` | git-lineage | preserved | retain |
| F18-1 | `a89a1dd:extension/rules/video-editing-story-and-cut-design.md#L7` | git-lineage | preserved | retain |
| F18-2 | `a89a1dd:extension/rules/video-editing-story-and-cut-design.md#L14` | git-lineage | preserved | retain |
| F18-3 | `a89a1dd:extension/rules/video-editing-story-and-cut-design.md#L21` | git-lineage | preserved | retain |
| F18-4 | `a89a1dd:extension/rules/video-editing-story-and-cut-design.md#L28` | git-lineage | preserved | retain |
| F19-1 | `a89a1dd:extension/rules/video-editing-validation-and-delivery.md#L7` | git-lineage | preserved | retain |
| F19-2 | `a89a1dd:extension/rules/video-editing-validation-and-delivery.md#L14` | git-lineage | preserved | retain |
| F19-3 | `a89a1dd:extension/rules/video-editing-validation-and-delivery.md#L21` | git-lineage | preserved | retain |

### 삭제·rename predecessor 보완

| predecessor | source anchor | successor / gap | 판정 |
|---|---|---|---|
| `rules/history-review.md` | `c5c078a^:rules/history-review.md` | `core/rules/file-extraction.md`와 `PROJECT_RULES.md`에 부분 승계; exact historical-read 절차는 공백 | candidate-loss 일부 |
| `rules/stage-work.md` | `c5c078a^:rules/stage-work.md` | `core/rules/staged-work-design.md`로 단계 topology·gate 승계 | superseded |
| `extension/rules/file-extraction.md` | `07a26a3^:extension/rules/file-extraction.md` | `core/rules/file-extraction.md`로 이동·승계 | migrated |
| `extension/rules/file-cleanup.md` | `07a26a3^:extension/rules/file-cleanup.md` | `core/rules/file-cleanup.md`로 R081 rename | migrated |

### 과거 후보 L01~L12 판정

| ID | source anchor | evidence | current owner | disposition | M1 decision |
|---|---|---|---|---|---|
| L01 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L87` | direct-remeasurement | 없음 | candidate-loss | 후보 owner·extension-only 대안 검토 |
| L02 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L88` | direct-remeasurement | 부분: `PROJECT_RULES.md` Approval/Protected | candidate-loss | exact delta 검토; 자동 Core 복원 금지 |
| L03 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L89` | direct-remeasurement | 없음 | candidate-loss | `core/rules/boundary-routing-and-dependency.md` 배치 검토 |
| L04 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L90` | direct-remeasurement | `core/rules/cross-validation.md` 부분 | migrated | 약한 출처·버전 주장 delta 검토 |
| L05 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L91` | direct-remeasurement | 없음 | candidate-loss | 조건부 `document-work` 배치 검토 |
| L06 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L92` | unresolved | `PROJECT_RULES.md` Verification과 충돌 | superseded | D7에서 사용자 의도 확인 |
| L07 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L93`; successor `core/rules/document-work.md#L22` | direct-remeasurement | `core/rules/document-work.md`, 영상 validation owner | preserved | 복원하지 않음 |
| L08 | `c5c078a^:rules/history-review.md`; successor `core/rules/file-extraction.md` | direct-remeasurement | `core/rules/file-extraction.md` 부분 | migrated | historical-read exact delta 검토 |
| L09 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L115`; successor `extension/rules/video-editing-validation-and-delivery.md#L7` | direct-remeasurement | domain owner 부분; Core 정의 없음 | migrated | domain 보존·foundation 필요성 비교 |
| L10 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L134`; successor `core/rules/document-work.md#L20` | direct-remeasurement | `core/rules/document-work.md` 부분 | migrated | write-success·복구 delta 검토 |
| L11 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L155`; successor `PROJECT_RULES.md#L87` | unresolved | `PROJECT_RULES.md` | superseded | D7에서 사용자 의도 확인 |
| L12 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md#L168` | report-only | `core/failures/` | task-specific | M1 변경 대상 아님; 표본 범위는 미검증 |

### M0-S2·S3 결과 요약

- 현재 의미: 78/78 source anchor·owner 연결, 고아 0. predecessor 4건도 successor 또는 공백을 기록했다.
- 과거 후보: candidate-loss 4건(L01·L02·L03·L05)+history-review delta; migrated 4건; superseded 2건; preserved 1건; task-specific 1건.
- L01~L05·L08~L10은 현재 owner와 직접 비교했고, L06·L11은 사용자 의도 미확정으로 복원하지 않는다.

### M0-S4 M1 입력 고정

- 권장 M1 순서: candidate-loss와 migrated delta만 검증한다. Core 후보는 `PROJECT_RULES.md`, `core/rules/boundary-routing-and-dependency.md`, `core/rules/cross-validation.md`, `core/rules/document-work.md`, `core/rules/file-extraction.md`의 기존 owner 강화로 한정한다.
- extension-only 대안은 L09(영상 validation)에는 가능하지만 L01~L05·L08·L10은 foundation 범용 경계라 대체하지 못한다. L06·L11은 사용자 결정 전 보류한다.
- 예상 효과(미검증): candidate-loss 0, 중복 owner 0, 신규 active rule 0. 실제 효과는 M1/M2 gate에서 직접 재측정한다.
- 현재 Core diff 0. 후속 승인 시 검증은 Core·Extension 회귀, maintenance gate, UTF-8/NUL/links/diff와 의미 대조이며 literal-only 테스트는 제외한다.

파일별 의미 수: `PROJECT_RULES` 11, `document-work` 8, `rule-governance` 7, `staged-work-design` 7, `boundary-routing` 4, `failure-records` 4, `extension/README` 4, `story-and-cut-design` 4, `core-change-control` 3, `cross-validation` 3, `file-cleanup` 3, `version-control` 3, `intake-and-instructions` 3, `state-and-approval` 3, `validation-and-delivery` 3, `file-extraction` 2, `user-data-work` 2, `artifact-lineage` 2, `boundary-quality` 2. 합계 78, 최대 11(`PROJECT_RULES`).

## 초기 판정 queue

L01~L12는 Claude 보고서 유래 후보다. L13부터는 `M0-S3`의 세 발견 경로(보고서 유래, S1 인벤토리의 owner 공백, S2에서 successor 미확인 삭제 의미)로만 추가한다. 이 큐가 감사 범위의 상한이 아니다.

| ID | 과거 의미 | 현재 가설 | M0 exact 확인 |
|---|---|---|---|
| L01 | 외부 페이지·문서·tool 지시를 검증 전 불신 | candidate-loss | 보안 always-on owner 적합성 |
| L02 | 외부 agent·CLI 최소 권한 | candidate-loss | 기존 승인·secret 경계와 중복 여부 |
| L03 | 신규 tool/interface 최소 성공 호출 | candidate-loss | boundary owner와 외부 tooling 범위 |
| L04 | 공식·1차 출처 우선과 약한 출처 label | candidate-loss | cross-validation evidence 체계 통합 가능성 |
| L05 | 결정·위험 보고의 red-team 절 | candidate-loss 가능 | 반복 근거·독자 비용·조건부 필요성 |
| L06 | 같은 방향 두 번 거부 시 중단·의도 재진술 | unresolved | 최신 사용자 교정·자율성 규칙과 조정 |
| L07 | tool success는 콘텐츠 승인이 아님 | preserved | document·domain owner의 중복 복원 금지 |
| L08 | 역사 자료를 현재 지시로 재활성화하지 않음 | migrated 일부 | file-extraction에 없는 exact delta |
| L09 | Generated→App-validated 검증 사다리 | domain-preserved / foundation-gap | 범용 owner의 실제 필요성 |
| L10 | write success와 byte/content 검증 분리 | migrated 일부 | 안전 의미만 보존하고 자동 Git overwrite 폐기 |
| L11 | 3연속 실패 뒤 무조건 사용자 대기 | superseded 가능 | 범위 내 복구와 양립하는 stop 조건 |
| L12 | 과거 failures 24사례의 7 owner 통합 | report-only / unverified | case count 정의와 exact owner 표본 |

## Claude 보고서 교차검증 ledger

| claim | current result | evidence | downstream effect |
|---|---|---|---|
| 규칙 팽창·0단어 재구축 6사이클 | 일치 | direct-remeasurement | 의미 보존 gate 필수 |
| 현재 19,519단어 | 재현 실패 | direct-remeasurement | 같은 의도의 corpus를 재측정하면 37파일·18,433토큰(HEAD 18,010)이다. 보고서 수치도 이전 세션의 18,844도 재현되지 않아 둘 다 `unresolved`. 후속 기준은 재측정 값만 사용한다 |
| 핵심 규칙 4종 소실 | 판정 대기 | repository-source + git-lineage | L01~L04 owner·적용성 확인 |
| tool success와 콘텐츠 승인 분리 소실 | 반박 | repository-source | L07 중복 복원 금지 |
| 1,000단어 상한·literal inventory·자동 Git 복구 | 채택하지 않음 | 현재 사용자 의도·안전성 검토 | 후속 gate에서 제외 |

## 완료 조건

- corpus 정의 표의 세 corpus가 exact glob·파일 목록·재현 명령과 함께 측정되고, 기존 수치와의 일치 여부가 판정된다.
- active 의미 전부가 정확히 한 canonical owner 또는 candidate-loss로 연결된다.
- 유지하지 않는 의미마다 근거와 source anchor가 있다.
- L01~L12 및 추가 항목의 Claude 일치·반박·부분 일치가 분리된다.
- M1에 넘길 exact 변경 후보, extension-only 대안, 검증 방식, 미해결 사용자 결정을 별도 열로 확정한다.
