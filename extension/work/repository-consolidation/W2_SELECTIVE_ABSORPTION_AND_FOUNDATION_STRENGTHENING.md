# W2 선택적 흡수·기반 강화

- 문서 분류: `phase-design`
- phase ID: `W2`
- lifecycle: `passed`
- 결과: W1의 K01~K04만 기존 owner 3개에 최소 병합하고 신규 owner·Core 변경·중복 규칙 없이 검증한다.
- 독자: W2 실행 agent와 W3 처분 manifest 작성자
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- optional evidence owner: `extension/work/repository-consolidation/W1_REUSABLE_KNOWLEDGE_MAP.md` — startup-required 아님
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; 이 문서는 Core·보호 데이터·삭제·이동·외부 효과를 승인하지 않는다.
- 첫 다음 행동: W2 task-owned 7경로만 stage해 checkpoint를 commit하고, commit 검증 뒤 W3 phase를 활성화한다.

## Entry gate

- W1-S1~S4와 exit/commit이 passed이고 checkpoint는 `f02c304`다.
- entry 작업트리는 clean이다.
- W1 exact path set은 `README.md`, `extension/README.md`, `extension/rules/video-editing-intake-and-instructions.md`다.
- 신규 file·rule ID·replay ID·schema·code·dependency 후보는 0이고 Core 후보도 0이다.

## 포함·제외 범위

포함:

1. `README.md`: K01 single verify 발견 가능성
2. `extension/README.md`: K02 구현 owner·상태 경계, K04 runtime 유지 조건
3. `extension/rules/video-editing-intake-and-instructions.md`: K03 지시 문법 오독 방지
4. W2 phase·overall·handoff·W1 transition metadata

제외:

- `core/**`, code·test·schema·dependency·runtime 내용 변경
- 보호 inputs/outputs의 추가 읽기·복제·stage
- 과거 report·plan·output의 삭제·이동
- synthetic test 결과를 production KPI·실제 앱 검증으로 승격

## Slice gate

각 slice는 exact owner·최소 delta·현재 구현 evidence·중복 여부를 기록하고 관련 검증을 통과한 뒤 다음 slice로 전환한다.

## W2-S1 — 루트 검증 경로

`README.md`는 전체 검증의 기본 명령을 `python -B scripts/verify.py` 하나로 안내한다. raw Core·Extension unittest는 특정 실패를 좁혀 재실행하는 보조 경로로 구분한다. single verify가 bootstrap·Node·Core·Extension·maintenance·clean clone을 합성한다는 현재 구현보다 높은 주장을 하지 않는다.

### W2-S1 gate

- 문서 기본 검증 진입점이 하나다.
- README 명령을 실제 실행해 현재 workspace와 clean clone에서 통과한다.
- browser user session의 `needs_user`를 deterministic 실패나 성공으로 오인하지 않는다.

## W2-S2 — Extension 구현·runtime owner

`extension/README.md`에 이미 구현된 세 기반 adapter의 owner와 경계를 짧게 연결한다.

- `video_workflow`: next-step·resume·boundary를 검증하는 deterministic engine; 실제 외부 작업은 skill owner
- `learning`: aggregate-only KPI·복잡성 후보; 실제 production 측정 전 효과 주장 금지
- Core export conformance: empty/youtube/game consumer의 동일 manifest 검증; 실제 게임 제품·별도 배포 주장 금지

`.runtime/`은 Git 제외 capability cache이며 active owner와 install/rebuild 경로가 있는 항목만 현재 필요 runtime으로 본다. output 보고서나 과거 tool 사용 사실만으로 unreferenced binary를 유지하지 않는다.

### W2-S2 gate

- 구현·test·skill owner가 서로의 책임을 대체하지 않는다.
- synthetic·production·external 경계가 명시된다.
- runtime 유지 조건은 상위 machine artifact 규칙을 복제하지 않고 Extension 배치만 설명한다.

## W2-S3 — 영상 지시 문법 오독 방지

R01의 기존 `증상 / 제안 방법 / 수치` 분리를 유지하면서 다음 문법 경계를 최소 보강한다.

- 시각 표기가 좌표인지 구간인지 원문 구조로 판정
- 권장·예시와 금지·필수를 서로 바꾸지 않음
- 예상 예산과 hard cap을 명시 없이 같은 합격 기준으로 만들지 않음
- source에 없는 coverage·비율을 자체 합격 지표로 만들지 않음

### W2-S3 gate

- 기존 R01 owner와 TC01 ID를 유지하고 새 rule·replay를 만들지 않는다.
- 좌표/범위, 권장/금지, 예산/hard cap 세 대조 사례에서 문법 역할을 보존한다.
- exact 보호 task 사실·수치·파일명은 rule에 0건이다.

## W2-S4 — 통합·복잡성 대조

W1 K01~K04가 최종 owner 하나씩에 존재하고, D01~D21·보호 output 원문을 runtime dependency로 참조하지 않는지 확인한다. 추가 줄 수와 startup·rule-surface 변화를 측정해 owner 보강보다 문서 복잡성이 더 커지지 않았는지 판정한다.

### W2-S4 gate

- K01~K04 owner coverage 4/4, 중복 active owner 0
- 신규 파일·rule ID·replay ID·schema·dependency 0
- W2 owner 3개 순증가 50줄 이하
- Core diff·보호 staged·삭제·이동 0

## Exit·commit·transition gate

- W2-S1~S4가 passed다.
- `python -B scripts/verify.py`와 clean clone, Core·Extension·maintenance·route가 통과한다.
- strict UTF-8·NUL·후행 공백·links·`git diff --check`가 통과한다.
- task-owned W2 phase·owner 3개·overall·handoff·W1 transition만 단계 commit한다.
- commit 검증 뒤 W3가 전역 allowlist·reference·rebuild·recovery·exact disposition manifest를 활성화한다.

## 복구·중단 조건

- Core 변경이 필요해지면 구현을 멈추고 exact 경로·이유·Extension 대안에 대한 현재 대화 승인을 확인한다.
- 보호 원문·task 사실이 owner에 들어가면 해당 delta를 제거하고 추상 의미만 재작성한다.
- 현재 code와 문서 주장이 다르면 code를 확대하지 않고 문서 주장을 실제 구현 수준으로 낮춘다.
- 신규 owner나 50줄 초과가 필요하면 기존 owner 압축안을 먼저 검토한다.

## Gate evidence·점수

- owner delta: 3파일, 순증가 20줄; 신규 file·rule·replay·schema·code·dependency 0
- K01~K04 owner coverage 4/4, Core diff·보호 diff·삭제·이동 0
- focused cross-check: 56 tests passed; Core export empty·YouTube·game conformance passed
- single verify: Core 139, Extension 132, Node ready, maintenance 96 documents·130 links
- clean clone: ASCII·한글+공백·공백 경로 3/3 passed; browser session은 `needs_user`
- 설계 예산: overall 90줄·4,957자, W2 phase 129줄·4,727자
- W2-S1 5/5: 실제 single gate와 README 기본 경로 일치
- W2-S2 5/5: 세 구현 owner와 synthetic/production/runtime 경계 연결
- W2-S3 4/5: 세 문법 대조는 통과했으나 자연어 절차라 executable parser 검증은 없음
- W2-S4 5/5: one-owner·복잡성·회귀·경계 통과
- W2 전체 4.75/5: 최소 owner 흡수와 재현성은 충족, 자연어 의미 gate는 수동 대조 유지

## Closeout record

- W2-S1: `passed`
- W2-S2: `passed`
- W2-S3: `passed`
- W2-S4: `passed`
- W2 exit: `passed`
- W3 transition: `passed` — W2 checkpoint `5ed6bb6`, clean status 확인 뒤 W3 활성화
