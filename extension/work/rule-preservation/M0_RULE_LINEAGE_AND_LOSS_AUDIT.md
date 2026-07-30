# M0 규칙 계보·손실 감사

- 문서 분류: `phase-design`
- phase ID: `M0`
- lifecycle: `in_progress`
- 진행 상태: `M0-S1` passed, `M0-S2` unstarted
- 결과: 현재 규칙과 직접 역사 계보의 의미를 대조해 복원·통합 전에 사용할 보존 지도를 확정한다.
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`가 상위 권위이며 이 단계는 Core 변경을 승인하지 않는다.
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- evidence owner: [M0 규칙 보존 지도](M0_RULE_CONSERVATION_MAP.md); 저장소 원본·Git은 해당 행의 source anchor이고 Claude 보고서는 교차검증 reference다.
- 개정: 2026-07-29 설계 점검으로 측정 기준·의미 입도·계보 대체 수단·전환 gate를 보강했다. slice 실행 전 개정이므로 무효화할 mutation은 없다.

## 현재 단계에 적용한 규칙

`PROJECT_RULES.md`에서 `M0-S1`의 다음 행동으로 재선택한 결과다. 별도 router가 아니며 매칭되지 않은 규칙은 본문을 열지 않는다.

| 규칙 | S1에 적용한 조항 |
|---|---|
| `document-work.md` | 첫 mutation 전에 적용 조항과 충돌을 이 표에 기록한다. 검증은 최소 직접 검사(UTF-8·NUL·trailing whitespace·scoped diff)를 쓰고 full maintenance를 돌리지 않는다 |
| `staged-work-design.md` | slice gate를 하나씩 검증한 뒤 다음으로 넘어가고 미실행 검사를 통과로 세지 않는다. entry baseline이 dirty이므로 gate가 clean tree를 요구하지 않는다 |
| `file-extraction.md` | FEX01.1로 대상·목적·읽기쓰기 범위·독자를 먼저 고정하고, FEX01.3의 8종으로 분류하며, FEX01.6에 따라 해시·경로·일회성 수치를 규칙으로 승격하지 않고 evidence에 둔다. FEX01.7로 삭제·이동을 예약하지 않는다 |
| `cross-validation.md` | 현재 reviewer를 현재 세션에서 식별해 source 저자와 분리하고, material claim마다 evidence label을 붙이며, 마감 직전 identity·revision·동적 수치를 재확인한다 |
| `rule-governance.md` | 기존 owner와 정확한 route를 새 owner보다 우선하고, agent 제안과 사용자 승인을 분리 표기하며, 종료 전 매칭 규칙을 4분류로 감사한다 |

- 미매칭과 사유: `core-change-control`(S1에 Core mutation 없음), `file-cleanup`(처분은 M4), `boundary-routing-and-dependency`(owner 계층 판정은 S3), `version-control`(stage·commit 없음), `user-data-work`·`failure-records`(트리거 미발생). 매칭 판정은 router 트리거로만 하고 본문을 예비 열람하지 않는다.
- 충돌: 없음. `file-extraction` FEX01.6과 `D5` 해시 검증은 둘 다 수치를 evidence에 두므로 양립한다.
- 향후 `core/**` mutation은 `core/rules/core-change-control.md`의 exact 승인과 통합 gate 전에는 금지한다.
- 상시 제약(사용자 지시): M0~M3 선행 개선 단계에서는 파일을 삭제·이동하지 않는다. 제거 후보는 목록으로만 기록하고 M3 통과 뒤 exact 목록을 승인받아 M4에서 처분한다.

## entry gate

- `M0-E1` 통과: S1 진입 당시 branch `main`, HEAD `3810abc`, 기존 미커밋 rule-surface 4건(`core/**` 3건)과 Claude reference-evidence 1건을 확인했다. 이후 중단된 초안 변경이 추가된 현재 기준선은 `M0_RULE_CONSERVATION_MAP.md`와 `SESSION_HANDOFF.md`를 따른다.
- `M0-E2` 통과: 사용자 지정 보고서와 현재 단계에 매칭된 규칙을 EOF까지 읽었다.
- `M0-E3` 통과: 보호 데이터·backup bulk read·외부 상태 변경 없이 저장소 원본과 Git만 재측정했다.
- `M0-E4` 통과: overall-design·이 active phase·M0 reference-evidence 1건만 소유한다. 보존 지도는 startup-required가 아니며 새 보고서·미래 phase 문서를 만들지 않는다.
- `M0-E5` 통과: 보존 지도 baseline 앵커 10건을 재측정해 전부 일치했다(2026-07-29, direct-remeasurement). 이번 개정으로 변경된 문서의 앵커는 개정 직후 지도에서 갱신한다.

## 확정 결정

측정값·corpus 목록·앵커는 보존 지도가 소유한다. 이 절은 판정 기준만 고정한다.

승인 상태를 분리한다. `D3`·`D4`의 수치는 사용자 확인에 따라 `provisional`이며 `M0-S1` 실측 뒤 확정한다. 나머지는 authorized scope 안의 agent 기본값이고, 사용자 판단이 필요한 항목은 `D7`이 모은다. agent 제안을 승인된 정책으로 표기하지 않는다.

- `D1` corpus 삼분: `rule-surface`(의미 인벤토리 대상), `normative-corpus`(읽기 비용 기준), `candidate/reference`(판정 제외). 각 corpus의 exact glob과 파일 목록은 보존 지도의 corpus 정의가 소유한다.
- `D2` 계수 방법: UTF-8 디코드 후 공백 분리 토큰 수와 문자 수를 함께 기록하고, 정렬된 exact 경로 목록을 남겨 재현 가능하게 한다. 재측정과 어긋나는 기존 수치는 채택하지 않고 `unresolved`로 표시한 뒤 정정한다. 재현 명령 없는 수치는 후속 성공 기준의 근거가 될 수 없다.
- `D3` 의미 단위 입도(`provisional`): `trigger`와 `protected outcome`을 함께 갖는 최소 단위(최상위 절 또는 단일 bullet)를 1행으로 한다. 잠정 상한은 파일당 12행이며, 넘기면 상위 절 단위로 병합한다. 실측 분포를 근거로 `M0-S1` 종료 때 확정하거나 조정한다.
- `D4` 보존 지도 예산(`provisional`): 잠정 400줄·30,000자. 초과하면 행을 늘리지 말고 `D3` 입도를 상향한다. evidence 전용 상한이며 startup 경로 예산이 아니다. `D3` 확정과 같은 시점에 실측 행 수를 근거로 확정한다.
- `D5` 미추적 산출물 검증: untracked 파일은 `git diff` 대상이 아니므로 slice 시작·종료 SHA-256 대조로 검증한다. scoped diff는 tracked 변경에만 적용한다.
- `D6` 계보 추적 수단: `git log --follow`는 단일 경로 전용이고 0단어 재구축 구간에서 rename 검출이 끊긴다. 끊기면 `git log --diff-filter=D --name-only`로 삭제 경로를 모아 역방향으로 매칭한다. 이 전환은 예상 실패이며 3연속 실패 규칙의 소진 대상이 아니다.
- `D7` 사용자 결정: 현행 정책·자율성과 충돌해 agent가 판정할 수 없는 항목은 `unresolved`로 두고 `M0-S3` 종료 시 exact 질문 목록으로 한 번에 제기한다. 항목마다 실행을 멈추지 않는다.

## 포함 범위

- 현재 `PROJECT_RULES.md`, `core/rules/**`, `extension/README.md`, `extension/rules/**`의 의미 단위.
- 읽기 비용 기준 산정에 한해 `core/failures/**`, `core/docs/**`, `extension/docs/**`.
- 위 활성 규칙 표면을 변경한 67개 commit과 직접 rename·delete predecessor.
- 확인된 16개 deleted historical rule path 중 backup·report를 제외한 active predecessor 후보.
- `core/failures/**`와 domain candidate는 특정 의미 공백이나 승계 판정에 필요한 exact 파일만.
- 이번 checkpoint 전 미커밋이었던 `PROJECT_RULES.md`, `document-work.md`, `rule-governance.md`, `test_rule_routing.py`, `staged-work-design.md`의 별도 lineage. 후속 M0는 이 commit을 기준선으로 사용한다.
- 완료 이니셔티브 잔여 문서(`extension/work/PROJECT_FOUNDATION_DESIGN.md`와 `extension/work/project-foundation/` 7건)의 startup route 연결 여부 기록.

## 제외 범위

- 전체 189개 commit의 동일 깊이 분석, 107개 handoff·work commit의 일괄 재독.
- `backup/**`, 과거 보고서, superseded phase의 bulk read. exact lineage gap이 확인된 파일만 예외 검토한다.
- 보호 `inputs/`·`outputs/`, secrets, 외부 시스템, dependency 설치.
- Core·Extension 규칙 수정, 삭제, 이동, stage, commit, push.
- 완료 이니셔티브 잔여 문서의 정리·이동·삭제. M0는 후보와 근거만 기록하고 실제 처분은 M3 통과 뒤 M4가 소유한다.
- 과거 문장의 그대로 복원, hard word cap 충족을 위한 삭제, 정규식 문구 존재 테스트 추가.

## 실행 slice와 gate

1. `M0-S1 현재 의미 인벤토리`
   - FEX01.1에 따라 읽기 범위를 먼저 고정한다. 의미 인벤토리 대상은 `rule-surface` 전문이고, `normative-corpus`는 토큰·문자 계수만 하며 의미를 추출하지 않는다.
   - 보존 지도에 현재 reviewer(현재 세션)를 source 저자와 분리해 기록한다.
   - 보존 지도에 `D1` corpus 정의와 `D2` 재측정 값을 고정하고, 기존 `37파일·18,844단어`와의 일치 여부를 evidence label과 함께 판정한다.
   - dirty baseline의 exact path·status·ownership·SHA-256 anchor를 갱신한다.
   - `rule-surface`의 각 의미를 `D3` 입도로 `trigger / outcome / action / exception / verification / owner`로 정규화한다.
   - 완료 이니셔티브 잔여 문서 8건을 startup route 미연결 상태로 인벤토리에만 기록한다.
   - 마감 직전 branch·HEAD·동적 수치를 재확인한 뒤 정지하고 결과를 보고한다. `M0-S2`는 사용자 확인 뒤에 시작한다.
   - `M0-S1-G`: (a) corpus 3종의 파일 목록·수치·재현 명령이 지도에 있고 기존 수치와의 일치·불일치가 판정됨; (b) `rule-surface` 전 파일이 최소 1행에 매핑되고 미매핑 0; (c) candidate/reference와 미커밋 제안이 별도 표시됨; (d) 지도가 `D4` 예산 이내; (e) 비작업 baseline 앵커가 유지됨; (f) 실측 행 분포를 근거로 `D3`·`D4`가 확정 또는 조정되고 `provisional` 표기가 해제됨.
2. `M0-S2 직접 계보 추적`
   - `D6` 순서로 현재 owner를 역추적하고 삭제·rename 지점만 확장해 보존 지도의 source anchor에 기록한다.
   - `M0-S2-G`: 제거된 의미마다 source commit과 successor 또는 공백이 있고, `--follow` 단절 구간은 대체 수단 결과나 `unresolved`로 명시되며, backup bulk read가 0이다.
3. `M0-S3 손실·승계 판정`
   - `preserved / migrated / superseded / task-specific / unsafe-outdated / candidate-loss`로 분류한다.
   - 추가 후보 발견은 세 경로만 사용한다: 보고서 유래 L01~L12, `M0-S1` 인벤토리의 owner 공백, `M0-S2`에서 successor가 확인되지 않은 삭제 의미. 추가 항목은 L13부터 번호를 잇는다.
   - `M0-S3-G`: 모든 항목에 evidence label·현재 owner·복원 여부가 있고, `extension/rules/**`와 `core/failures/**`가 발견 경로를 최소 1회 통과한 기록이 있으며, `D7` 질문 목록이 확정된다.
4. `M0-S4 M1 입력 고정`
   - 문구 고정이 아닌 보존 검증 대안과 최소 Core target을 비교한다.
   - `M0-S4-G`: extension-only로 불가능한 이유, exact Core 경로, 예상 감소·복구·검증이 사용자 승인 요청 전 준비된다.

## exit gate

- `M0-X1`: 보존하기로 한 모든 의미가 현재 owner 또는 candidate-loss에 정확히 한 번 매핑된다.
- `M0-X2`: 보존 지도에 Claude 보고서와의 일치·반박·부분 일치를 evidence label과 함께 기록한다.
- `M0-X3`: 1,000단어 hard cap, literal regex inventory, 자동 Git overwrite를 후속 성공 기준에서 제외한다.
- `M0-X4`: 미해결 사용자 결정과 exact Core 변경 후보가 분리되고, M0 실행 소유 Core diff는 0이며 checkpoint baseline의 Core 경로가 유지된다.
- `M0-X5`: overall-design 120줄·8,000자, phase-design 160줄·12,000자, 보존 지도 `D4` 예산과 문서 무결성 검사를 통과한다.
- `M0-X6`: 후속 성공 기준이 참조하는 모든 수치가 `D2` 재현 명령과 파일 목록을 가지며, 재현되지 않은 기존 수치는 근거에서 제외된다.

## 전환 gate와 정지·복구

- `M0-T1` 전환 자기점검: (a) 포함 범위가 증가하지 않았다; (b) artifact가 overall 1·phase 1·evidence 1·state 1을 유지한다; (c) 읽기 예산이 통과한다; (d) 잔여 위험과 미해결 질문이 상태 문서에 있다; (e) M1·M2가 여전히 필요한지 재확인한다. candidate-loss가 0이면 M1·M2를 건너뛰고 M3로 전환하되, 완료 후 처분 M4는 유지한다.
- `M0-T2` 규칙 감사: `rule-governance`의 controlled closeout에 따라 이 단계에 매칭된 규칙을 `무결점 적용 / 기존 owner 보강 필요 / 기존 failure 케이스 / 새 owner 필요` 4분류로 판정한다. 근거는 현재 작업이나 검증된 역사에서만 가져오고, 별도 closeout 보고서를 만들지 않으며, Core 변경 제안은 `M0-S4` 결과로만 넘긴다.
- `M0-T3` 커밋: 사용자 지시로 M0-S2 전에 방향·설계·evidence와 기존 작업 변경을 하나의 준비 checkpoint로 커밋해 handoff mode를 `portable`로 전환한다. M0 exit gate 뒤 새 persistent 결과가 있으면 `version-control` route를 다시 선택해 그 결과만 다음 checkpoint로 커밋하며 보호 데이터는 제외한다.
- 계보 공백이 발견되면 exact 질문·commit·path를 기록한 뒤 그 자료만 확장한다. 과거 snapshot 전체를 읽지 않는다.
- 같은 조회 목적이 세 번 실패하면 확인된 blocker를 보존하고 authorized scope 안에서 조회 방법을 바꾼다. `D6` 전환은 이 계수에 포함하지 않는다. 새 권한·보호 자료·외부 상태가 필요하면 `blocked`로 전환한다.
- 준비 checkpoint 전 Core dirty 때문에 기본 maintenance가 `core_change_required`로 끝난 것은 예상 실패였다. 승인된 checkpoint 검증은 `--allow-core-changes`로 통과했으며, 커밋 뒤 M0에서는 기본 maintenance를 사용하고 새 Core diff가 생기면 중단한다.
- M0가 passed이고 `M0-T1`이 M1을 필요하다고 판정한 뒤에만 M1 phase-design을 만든다. 후속 Core mutation 승인은 해당 agent의 현재 대화에서 다시 확인한다.
- 첫 다음 행동: `M0-S2`에서 `D6` 순서로 현재 78개 의미의 직접 계보를 역추적하고 source anchor를 보존 지도에 기록한다.
