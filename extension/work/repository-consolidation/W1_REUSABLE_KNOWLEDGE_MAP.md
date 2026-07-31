# W1 재사용 지식·owner mapping

- 문서 분류: `reference-evidence`
- startup-required: 아니오
- owner: `extension/work/repository-consolidation/W1_REUSABLE_KNOWLEDGE_EXTRACTION_AND_OWNER_MAPPING.md`
- 독자: W2 실행 agent와 W3 처분 manifest 작성자
- 역할: W0 queue의 과거 문서·선행 evidence·보호 output 구조를 현재 정본과 대조하고, 재사용 의미와 미흡수 이유를 고정한다.
- 측정 기준: 2026-07-31, W1 baseline `16f87cc`
- evidence label: 별도 표기가 없으면 source는 `direct-read`, 현재 owner·구현·test는 `direct-remeasurement`
- 보호 경계: 보호 exact 파일명·본문·media path·사용자별 사실은 기록하지 않고 W0 opaque group과 구조 aggregate만 사용한다.

## 결론

W0가 넘긴 21개 과거 report·plan·foundation 문서와 선행 evidence 7개는 모두 읽고 현재 정본·코드·test와 대조했다. 과거 문서의 대부분은 이미 구현되었거나 M0~M2 규칙 통합에서 기존 owner에 반영됐다. 오래된 “미구현”·“다음 단계”·“승인 대기” 문구는 현재 상태로 승격하지 않는다.

보호 output 10그룹의 text·structured artifact도 opaque group 단위로 검토했다. 반복 workflow의 대부분은 현재 영상 편집 계약, R01~R16, `video-to-srt`, workflow engine과 검증 코드에 이미 존재한다. exact 장면·프레임·길이·수정 이력·사용자 판단은 task-specific으로 남겼다.

W2로 넘길 재사용 의미는 네 가지이며 신규 owner나 Core 변경은 필요하지 않다.

1. 루트 README가 이미 구현된 단일 검증 진입점을 기본 경로로 안내한다.
2. Extension README가 workflow engine·aggregate learning·Core export conformance의 실제 owner와 synthetic/production 경계를 연결한다.
3. 영상 지시 해석 owner가 시간 좌표와 범위, 권장과 금지, 예산과 hard cap을 문법 근거 없이 바꾸지 않도록 보강된다.
4. Extension의 ignored runtime은 active owner와 설치·재구축 경로가 있는 capability cache만 유지한다는 배치 경계를 명확히 한다.

## W1-S1 — 과거 문서 21/21

같은 계보의 plan과 final report는 독립 근거로 중복 계산하지 않았다. `complete`는 extraction 완료를 뜻하며 문서의 현재 유지 필요성을 뜻하지 않는다.

| ID | source | family | extraction | 판정 | 현재 owner·결과 |
|---|---|---|---|---|---|
| D01 | `extension/reports/2026-07-24_프로젝트_구조_및_목표_달성도_진단.md` | 초기 목표 진단 | complete | `already-canonical` + K02 | 사용자 결과·실제 KPI 우선은 `PROJECT_DIRECTION.md`; 당시 미구현 기능 다수는 현재 코드·skill로 구현 |
| D02 | `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md` | 규칙 손실 감사 | complete | `already-canonical` | L01~L10의 유효 공백은 M2의 기존 Core·Extension owner에 반영; 충돌·미확정 의미는 비복원 |
| D03 | `extension/reports/codex_2026-07-27_e4161fd_장점선별_현재버전_개선적용계획.md` | 영상 도구 이식 plan | complete | `already-canonical` | SRT·legacy CSV·Premiere profile 경계는 현재 영상 편집 계약·코드·test가 소유 |
| D04 | `extension/reports/codex_2026-07-27_e4161fd_장점선별_개선적용_최종보고.md` | 영상 도구 이식 final | complete | `already-canonical` + `domain-candidate` | 구조 검증은 구현됨; 실제 앱 import·재생은 현재 R15와 CAND08의 별도 gate |
| D05 | `extension/reports/codex_2026-07-27_전체세션자료_재분석_최종개선계획.md` | 영상 편집 근간 plan | complete | `already-canonical` | 의미/구조 분리, 단일 source lineage, 보류 승격 gate는 현재 workflow 계약·R01~R16·candidate owner에 있음 |
| D06 | `extension/reports/codex_2026-07-27_영상편집_프로젝트근간_개선_최종보고.md` | 영상 편집 근간 final | complete | `already-canonical` | 구현·회귀는 현재 code·schema·test로 직접 재현; 당시 단일 작업 수치는 승격하지 않음 |
| D07 | `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G0-G1_기준고정과_상태라우팅.md` | 문서 지시 plan | complete | `already-canonical` | startup route·현재 상태 owner는 `PROJECT_RULES.md`, handoff, route tests가 소유 |
| D08 | `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G2_ainotebook_상태이전.md` | worktree 상태 plan | complete | `task-specific` | 당시 worktree 이전 절차·경로이며 현재 상태나 일반 owner가 아님 |
| D09 | `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G3-G4_지시준수_규칙과_회귀검증.md` | 지시·회귀 plan | complete | `already-canonical` | exact Core 승인·행동 회귀·중복 owner 금지는 현재 정책·staged design·tests가 소유 |
| D10 | `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G5_통합검증과_최종보고.md` | 통합 closeout plan | complete | `already-canonical` | 전체 gate·최종보고·handoff 종료는 현재 단계 작업 규칙이 소유 |
| D11 | `extension/reports/codex_2026-07-28_문서기반_지시준수와_워크트리상태관리_개선안.md` | 문서 지시 master | complete | `already-canonical` | 지시 불변조건·단계 checkpoint는 현재 startup·phase contract에 흡수됨 |
| D12 | `extension/reports/codex_2026-07-28_문서기반_지시준수_개선_최종보고.md` | 문서 지시 final | complete | `historical-git` | 완료 사실은 Git으로 복구 가능하며 현재 행동을 바꾸는 고유 의미 없음 |
| D13 | `extension/reports/codex_2026-07-28_재현가능한_프로젝트_기반_방향분석과_개선계획.md` | foundation 분석 | complete | `already-canonical` + K01·K02·K04 | 장기 방향은 `PROJECT_DIRECTION.md`; 구현된 단일 gate·학습·conformance의 발견 가능성만 보강 필요 |
| D14 | `extension/work/PROJECT_FOUNDATION_DESIGN.md` | foundation overall | complete | `already-canonical` + K01·K02 | M0~M6 목표는 구현·test로 재현되며 현재 장기 방향과 active overall이 안정 의미를 소유 |
| D15 | `extension/work/project-foundation/M0_BASELINE_AND_SUCCESS_GATES.md` | foundation M0 | complete | `already-canonical` | runtime·Q0~Q5·외부 capability 경계는 manifests, bootstrap, verify에 구현 |
| D16 | `extension/work/project-foundation/M1_FRESH_CLONE_AND_CORE_PURITY.md` | foundation M1 | complete | `already-canonical` + K01·K04 | `pyproject.toml`, bootstrap, clone conformance, Core boundary가 구현됨 |
| D17 | `extension/work/project-foundation/M2_DESIGN_EXECUTION_CONTRACT.md` | foundation M2 | complete | `already-canonical` | phase invalidation·slice gate·handoff·commit 경계는 현재 staged-work design이 소유 |
| D18 | `extension/work/project-foundation/M3_SINGLE_QUALITY_GATE.md` | foundation M3 | complete | `already-canonical` + K01 | `scripts/verify.py`와 clone conformance가 구현됐으나 README 기본 진입점 연결이 약함 |
| D19 | `extension/work/project-foundation/M4_VIDEO_WORKFLOW_ENGINE.md` | foundation M4 | complete | `already-canonical` + K02 | `extension/src/video_workflow/`과 5개 synthetic engine test가 단계·resume·boundary를 구현 |
| D20 | `extension/work/project-foundation/M5_LEARNING_AND_COMPLEXITY_AUDIT.md` | foundation M5 | complete | `already-canonical` + K02 | aggregate-only KPI·복잡성 판정 code/test 구현; 실제 production KPI는 측정 근거가 생길 때만 주장 |
| D21 | `extension/work/project-foundation/M6_CORE_EXPORT_GAME_PILOT.md` | foundation M6 | complete | `already-canonical` + K02 | Core export manifest·empty domain·game pilot·dual-domain conformance가 code/test로 구현 |

Coverage:

- exact source: 21/21
- extraction complete: 21/21
- 현재 owner 또는 미흡수 이유: 21/21
- 과거 plan/final을 독립 효과 증거로 중복 계산: 0
- stale “미구현” 상태를 현재 사실로 승격: 0

## W1-S2 — 선행 evidence 7/7 delta

| source | 유효한 결과 | 현재 전역 목표와의 delta |
|---|---|---|
| `M0_RULE_CONSERVATION_MAP.md` | 78개 의미의 source·owner·disposition | 재사용 규칙 감사 evidence로 유지; 전역 file disposition은 W0로 대체 |
| `M0_RULE_LINEAGE_AND_LOSS_AUDIT.md` | 규칙 계보·손실 후보 | 완료된 phase; 새 후보 없음 |
| `M1_PRESERVATION_VALIDATION_AND_MINIMAL_CHANGE.md` | 기존 owner 우선·최소 delta | W2도 같은 원칙 적용 |
| `M2_RESTORE_INTEGRATE_AND_SINGLE_GATE.md` | Core 5·Extension 1 owner 의미 복원 | 재복원 금지; W2 후보와 중복 0 |
| `M3_STARTUP_ROUTE_REGRESSION_AND_DISPOSITION.md` | startup route·기존 22파일 후보 | 문서 슬라이스 evidence만 유효; disposition 목록은 전역 W3에서 다시 작성 |
| `M4_EXACT_DISPOSITION_AND_FINAL_REPORT.md` | exact 승인 전 처분 금지 | lifecycle `invalidated`; 실행 목록으로 사용 금지 |
| `2026-07-31_규칙_무손실_통합_M0_작업_보고.md` | M0~M3 commit·점수·rule-surface 증가 교정 | W5 전역 최종보고로 갱신 예정; 현재는 historical partial evidence |

선행 evidence에서 W2로 넘길 추가 규칙 의미는 0개다. 다만 이전 M2에서 active rule-surface가 430 tokens, 4.41% 증가한 사실은 W2 복잡성 gate로 유지한다. W2는 신규 파일·신규 rule ID 없이 기존 owner 3개만 보강해야 한다.

## W1-S3 — 보호 output 10그룹 구조 대조

### 구조 aggregate

| opaque group | 검토 구조 | 직접 결과 | 판정·현재 owner |
|---|---|---|---|
| `OUT-3537c733f2` | PNG 15 | text/structured artifact 없음 | media derivative; reusable extraction 없음 |
| `OUT-4f577374b7` | JSON 1, MD 1 | 전사 schema와 단일 분석 index | 전사 구조는 `video-to-srt`, 분석 사실은 task-specific |
| `OUT-52b4eba74b` | MD 1, TXT 1 | evidence index·대량 분석 text | index 원칙은 R04에 이미 존재; raw 분석은 task-specific |
| `OUT-736a78dfc7` | WAV 15 | text/structured artifact 없음 | regenerable media derivative |
| `OUT-74185d747c` | JSON 1, MD 1 | 전사 schema·검증 index | 현재 skill·R04·R15에 이미 존재 |
| `OUT-7cfbf66621` | JSON 2 | 전사 schema | 현재 `video-to-srt` raw JSON owner에 이미 존재 |
| `OUT-b1781b1e40` | JSON 4, MD 10, SRT 1, XML 18 | revision·pre/post audit·speech/structure 검증; SRT·XML 파싱 성공 | 대부분 R04·R06·R08·R10~R15에 존재; 지시 문법 오독 예방만 K03 |
| `OUT-b9616a9104` | PNG 30 | text/structured artifact 없음 | media derivative; reusable extraction 없음 |
| `OUT-ee118bab0c` | JSON 15, SRT 15, TXT 15 | batch 전사 구조; SRT cue 형식 정상 | 전사·SRT 계약에 이미 존재; raw TXT는 재생성 derivative |
| `OUT-f7969614e6` | MD 1 | 분석 evidence index·도구 검증 기록 | evidence index는 R04; 당시 도구명·작업 순서는 current runtime owner가 아님 |

구조 수치:

- MD 14개, 3,188 lines, 292 headings
- JSON 23개, parse failure 0
- SRT 16개, 1,249 cues, timestamp arrow format error 0
- XML 18개, parse failure 0, root `xmeml` 18, sequence 18, clip structure 7,452
- exact 보호 파일명·본문·media path·사용자 사실의 persistent 기록: 0

### 보호 source에서 승격하지 않은 의미

- exact 장면·프레임·러닝타임·revision별 수정·승인 결과: `task-specific`
- 단일 영상에서 관찰된 밝기·RMS·컷 길이·압축량: 기존 candidate owner 또는 task evidence
- 여러 전사 JSON/SRT/TXT의 존재: 현재 skill이 재생성·검증하므로 artifact 자체를 foundation evidence로 보존하지 않음
- XML revision 18개의 존재: 현재 timeline/XML code·test가 구조를 생성·검증하므로 output 복제본을 계약 owner로 만들지 않음
- 당시 사용한 unreferenced local tool 이름과 binary: current active owner·rebuild가 없으므로 `superseded-or-unsafe`; W3 runtime 판정으로 넘김

## W1-S4 — 재사용 의미와 W2 exact 입력

| ID | 재사용 의미 | evidence | 판정 | 기존 owner | W2 최소 delta |
|---|---|---|---|---|---|
| K01 | 구현된 단일 Q0~Q3·clone gate를 첫 검증 경로로 발견 가능하게 함 | D13·D14·D16·D18 + `scripts/verify.py`·`clone_conformance.py` | `strengthen-existing-owner` | `README.md` | raw test 나열보다 `python -B scripts/verify.py`를 기본으로 안내하고 targeted fallback을 구분 |
| K02 | workflow engine·aggregate learning·Core export conformance의 실제 상태와 synthetic/production 경계를 라우팅 | D01·D13·D14·D19~D21 + code/test | `strengthen-existing-owner` | `extension/README.md` | 구현 owner·검증 owner·금지된 성공 주장과 실제 KPI 미측정을 짧은 표로 연결 |
| K03 | 시간 좌표/범위, 권장/금지, 예산/hard cap을 원문 문법 없이 서로 바꾸지 않음 | `OUT-b1781b1e40`의 반복 오독 교정 + 현재 R01 대조 | `strengthen-existing-owner` | `extension/rules/video-editing-intake-and-instructions.md` R01 | 결과·방법·수치 분리에 문법 역할과 자체 coverage 지표 금지를 최소 추가 |
| K04 | ignored runtime은 증거 보관소가 아니라 active owner와 install/rebuild가 있는 capability cache | D13·D16 + W0 runtime 67파일 + current skill 대조 | `strengthen-existing-owner` | `extension/README.md` | `.runtime/` 유지 조건과 owner 없는 legacy tool을 current capability로 간주하지 않는 배치 경계 추가 |

신규 owner 후보: 0.

Core 변경 후보: 0. K01~K04는 모두 root/Extension 기존 owner에서 표현 가능하다. 따라서 W2는 별도 Core 승인 없이 진행할 수 있으며 `core/**` diff가 생기면 즉시 범위 위반이다.

W2 exact path set:

1. `README.md`
2. `extension/README.md`
3. `extension/rules/video-editing-intake-and-instructions.md`

예상 복잡성 delta:

- 신규 파일: 0
- 신규 rule·replay ID: 0
- 신규 schema·code·dependency: 0
- startup-required 파일 수: 변화 0
- 변경 owner: 3
- 목표 순증가: 50 lines 이하, 중복 설명은 기존 문구 교체·압축으로 상쇄

W2 검증:

- `python -B scripts/verify.py` 전체 single gate와 clean clone
- Core·Extension 전체 회귀와 maintenance
- Extension rule route one-owner test
- K03의 세 의미 대조 사례: 좌표/범위, 권장/금지, 예산/hard cap
- strict UTF-8, NUL 0, trailing whitespace 0, links, `git diff --check`
- Core diff 0, 보호 staged 0, 신규 active owner 0

## W1 점수

| slice | 목표 | 실제 결과 | 점수 | 이유 |
|---|---|---|---:|---|
| W1-S1 | 과거 21문서 의미 추출 | 21/21 exact source·family·판정·owner 연결 | 5/5 | stale 상태와 구현 사실을 code/test로 교차검증 |
| W1-S2 | 선행 7 evidence의 전역 delta | 7/7 유효 결과·무효 실행 범위 분리, 새 중복 후보 0 | 5/5 | M0~M2 의미를 재승격하지 않음 |
| W1-S3 | 보호 output 10그룹 최소 검토 | 10/10 구조 검토, parse error 0, 보호 exact persistent 기록 0 | 5/5 | binary 내용은 의도적으로 제외하고 text/schema/validator만 사용 |
| W1-S4 | owner matrix·W2 exact 입력 | K01~K04, 기존 owner 3개, 신규 owner·Core 후보 0 | 5/5 | 최소 변경·검증·복잡성 상한이 명확함 |
| W1 전체 | 선택적 재사용 지식만 W2로 전달 | 28개 source/evidence와 output 10그룹을 4개 최소 delta로 압축 | 5/5 | 모든 source coverage와 보호·owner 경계 충족 |

## W3로 넘기는 비흡수 queue

- 과거 report·plan·foundation 21개와 `docs.md`: 현재 owner·Git recovery·inbound reference를 W3 manifest에서 다시 확인
- prior evidence 7개: active dependency와 최종보고 흡수 여부에 따라 historical Git 후보로 판정
- Python cache·Obsidian local state: 재생성 가능 disposition 후보
- local runtime 67파일: active exact reference 0; 설치 source·license·rebuild·대체 capability를 W3에서 확인
- 보호 inputs 2파일: 사용자 원본 보존
- 보호 outputs 201파일: current deliverable·최종 패키지·재생성·외부 recovery를 opaque group에서 exact manifest로 전환할 때 별도 승인

W1은 삭제·이동·owner mutation을 수행하지 않았다.
