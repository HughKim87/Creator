# M4 완료 후 문서 처분·최종 보고

- 문서 분류: `phase-design`
- phase ID: `M4`
- lifecycle: `invalidated`
- 결과: M3에서 검증한 role-ended 문서 중 사용자 승인 exact 목록만 처분하고, 지식·참조·복구 검증과 전체 최종 보고서·단계 점수를 남긴다.
- 독자: 처분을 승인하는 사용자와 종료 후 재개하는 agent
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- evidence owner: `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md`
- 최종 보고서 owner: `extension/reports/2026-07-31_규칙_무손실_통합_M0_작업_보고.md` — M0 보고서를 전체 M0~M4 consolidated report로 갱신하고 이 파일은 유지한다.
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; 아래 목록은 historical candidate evidence이며 현재 삭제 승인이나 실행 단계가 아니다.
- 무효화 이유: 사용자가 범위를 문서 22개가 아니라 tracked·untracked·ignored·백룸·개선 산출물·`outputs/`·`extension/data/`를 포함한 작업트리 전체로 교정했다. 전역 inventory·지식 선별 전 이 목록만 독립 처분하면 최종 목표와 gate를 충족하지 못한다.
- 첫 다음 행동: 이 문서를 실행하지 않고 `extension/work/repository-consolidation/W0_REPOSITORY_WIDE_INVENTORY_AND_CLASSIFICATION.md`로 전환한다.

## Invalidation record

- 현재 대화에서 아래 exact 목록의 delete 승인은 없었다.
- M4-S3 삭제·이동은 0이며 기존 목록은 W0 inventory의 historical candidate input으로만 사용한다.
- 전역 W3가 reference·rebuild·recovery를 다시 검증해 exact manifest를 만들기 전에는 이 목록을 승인 질문으로 재사용하지 않는다.

## Entry gate

- M0·M1·M2·M3가 passed이고 M3 checkpoint는 `bbe7912`, M4 준비 checkpoint는 `11a6031`이다.
- startup route는 현재 작업만 가리키며 M3가 처분 후보·inbound·복구 검사를 완료했다.
- 보호 `inputs/outputs`, Core, 외부 상태, push는 M4 대상이 아니다.
- 기본 처분은 `delete`뿐이며 `move`는 사용하지 않는다. 승인 목록이 바뀌면 M4 entry를 다시 검증한다.

## 권장 exact 처분 목록

아래 22개 파일, 빈 child 디렉터리 1개와 그 child만 보유한 parent 디렉터리 1개를 함께 처분하는 것이 권장안이다. 현재 최종 보고서·handoff·overall·M0 evidence·현재 M0~M3 phase-design은 유지한다.

### 이전 foundation 이니셔티브 8개

- `extension/work/PROJECT_FOUNDATION_DESIGN.md`
- `extension/work/project-foundation/M0_BASELINE_AND_SUCCESS_GATES.md`
- `extension/work/project-foundation/M1_FRESH_CLONE_AND_CORE_PURITY.md`
- `extension/work/project-foundation/M2_DESIGN_EXECUTION_CONTRACT.md`
- `extension/work/project-foundation/M3_SINGLE_QUALITY_GATE.md`
- `extension/work/project-foundation/M4_VIDEO_WORKFLOW_ENGINE.md`
- `extension/work/project-foundation/M5_LEARNING_AND_COMPLEXITY_AUDIT.md`
- `extension/work/project-foundation/M6_CORE_EXPORT_GAME_PILOT.md`

### 이전 report·plan 13개

- `extension/reports/2026-07-24_프로젝트_구조_및_목표_달성도_진단.md`
- `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md`
- `extension/reports/codex_2026-07-27_e4161fd_장점선별_개선적용_최종보고.md`
- `extension/reports/codex_2026-07-27_e4161fd_장점선별_현재버전_개선적용계획.md`
- `extension/reports/codex_2026-07-27_영상편집_프로젝트근간_개선_최종보고.md`
- `extension/reports/codex_2026-07-27_전체세션자료_재분석_최종개선계획.md`
- `extension/reports/codex_2026-07-28_문서기반_지시준수_개선_최종보고.md`
- `extension/reports/codex_2026-07-28_문서기반_지시준수와_워크트리상태관리_개선안.md`
- `extension/reports/codex_2026-07-28_재현가능한_프로젝트_기반_방향분석과_개선계획.md`
- `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G0-G1_기준고정과_상태라우팅.md`
- `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G2_ainotebook_상태이전.md`
- `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G3-G4_지시준수_규칙과_회귀검증.md`
- `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G5_통합검증과_최종보고.md`

### 0-byte·empty directory 3개

- `docs.md`
- `extension/work/2026-06-30-00-23-03/xml_build/`
- `extension/work/2026-06-30-00-23-03/`

위 목록의 두 디렉터리는 child-first로 확인하고, 파일 삭제 후 비어 있을 때만 parent를 처분한다. 현재 기록한 `codex_G2_ainotebook_상태이전.md` 경로는 파일시스템의 실제 대소문자·철자와 일치한다.

## 보존·복구 계약

- 현재 최종 보고서는 M0~M4 목표·실제 결과·성공게이트·slice 점수·효과 수치·미검증 항목·처분 목록·커밋을 보존한다.
- M0 map은 처분 전 78개 의미, L01~L12 판정, source anchor, current owner, M4 disposition을 최종 보고서에 교차 대조한다.
- 실행 가능한 Markdown/file link와 startup/current-state dependency는 삭제 전 0으로 만든다. 승인된 처분 목록·Git 복구·계보를 보존하는 비링크 code-span path는 historical evidence로 분류해 남길 수 있으며 고아 링크로 세지 않는다. `SESSION_HANDOFF.md`, overall, M0 map, 최종 보고서의 후보 표기를 이 기준으로 직접 분류한다.
- Git history가 삭제 파일의 복구 경로이며, 별도 backup snapshot은 만들지 않는다.
- 삭제 대상이 실제 path·size·SHA-256·승인 목록과 다르면 해당 파일을 처분하지 않는다.

## Slice gate

M4-S1~M4-S4의 각 slice는 승인 범위·실제 처분·최종 검증 결과를 기록한 뒤 다음 slice로 전환한다.

## Slices와 성공게이트

### M4-S1 — exact approval

권장 목록을 사용자에게 제시하고 “위 22개 파일, 빈 `xml_build/`와 그 child만 보유한 parent 디렉터리의 child-first delete를 승인한다”는 exact 승인을 받는다. 승인 없이는 M4를 `in_progress`로 전환하지 않는다.

### M4-S2 — final report·reference release

최종 보고서를 갱신하고 후보별 지식·inbound·복구 확인을 기록한다. 삭제 후보를 참조하는 active route·handoff·overall·evidence link를 제거하거나 최종 report link로 대체하고, historical code-span path는 복구·처분 증거 label을 붙인 뒤 직접 재검색한다.

### M4-S3 — exact disposition

승인된 exact path만 child-first로 삭제한다. move·rename·protected path 접근은 하지 않는다. 삭제 뒤 `git status`, staged path, Git diff, orphan link, exact remaining inventory를 확인한다.

### M4-S4 — final gate

Core·Extension 회귀, 기본 maintenance, strict UTF-8·NUL 0·후행 공백·links·scoped diff를 실행한다. 최종 보고서에는 직접 재측정과 보고-only 수치를 구분하고, M0~M4와 slice별 0~5점 및 이유를 남긴다.

## Exit gate

- 승인 목록과 실제 삭제 목록이 byte-level path로 일치한다.
- unique evidence·승인·계보 손실 0, orphan link 0, 보호 staged count 0이다.
- 최종 보고서가 단일 보고 owner이고 startup route에는 완료 phase·raw report·삭제 후보가 남지 않는다.
- 실패 시 삭제를 성공으로 보고하지 않고 Git에서 복구 가능한 상태를 보존한다. exact 목록 불일치·참조 잔존·검증 실패가 있으면 M4를 통과시키지 않는다.

## 복구·전환 gate

승인 목록과 실제 path가 달라지거나 검증이 실패하면 처분을 중단하고, 마지막 정상 Git 버전·inbound scan·final report를 대조한다. 사용자 승인 없이 목록을 넓히지 않는다.

## Closeout record

- M4-S1: `invalidated_before_approval`
- M4-S2: `audit_only_completed` — 최종 보고서 실제 결과 교정 완료; active reference release는 exact 승인 뒤 처분 직전에 수행
- M4-S3: `not_run`
- M4-S4: `not_run`
- M4 exit: `invalidated`
