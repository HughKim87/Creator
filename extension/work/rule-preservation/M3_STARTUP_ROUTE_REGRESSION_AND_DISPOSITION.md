# M3 시작 경로·회귀·종료

- 문서 분류: `phase-design`
- phase ID: `M3`
- lifecycle: `passed`
- 결과: M2 이후 startup-required 경로가 현재 작업만 가리키는지, 이전 이니셔티브 문서의 inbound reference와 지식 보존이 충분한지, Core·Extension·maintenance·음성 대조가 통과하는지 확인하고 M4 exact 처분 후보를 고정한다.
- 독자: M3 실행 agent와 M4 처분 승인자
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- evidence owner: `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md`
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; 이 문서는 삭제·이동 승인 자체가 아니다.
- 첫 다음 행동: M3-S1에서 `README → PROJECT_RULES → SESSION_HANDOFF → overall-design → M3 phase-design`의 active route와 음성 대조를 실행한다.

## Entry gate

- M0·M1·M2가 passed이고 M2 checkpoint는 `90d09cd0f88a09829e4080b2854d1bdcb863da04`다.
- M2의 exact Core/Extension 변경과 통합 gate가 커밋됐고 entry 작업트리가 clean이다.
- M3에서는 삭제·이동·이름 변경·보호 데이터 접근·Core mutation·외부 효과·dependency 설치·push를 하지 않는다.
- M4 처분은 지식·참조·복구 검증이 끝난 exact 목록만 대상으로 하며, 이 문서의 후보 목록은 승인 전 기록이다.

## M3-S1 — startup route와 음성 대조

정상 시작 route는 다음 하나다.

`README.md → PROJECT_RULES.md → SESSION_HANDOFF.md → RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md → M3 phase-design`

`extension/README.md`는 실제 extension 작업을 선택할 때만 `PROJECT_RULES.md`의 상위 route로 읽는다. 완료된 M0·M1·M2 phase, M0 evidence, old foundation design, 과거 report, raw command record는 startup-required route에 포함되지 않는다. active phase 외의 경로를 요구하는 link·문구·테스트는 음성 대조에서 실패로 본다.

## M3-S2 — 이전 문서 참조·지식 보존

M0의 그룹 수치를 현재 exact path로 재측정한다. 현재 후보 inventory는 23개 파일, 빈 child 디렉터리 1개와 그 child만 보유한 parent 디렉터리 1개다.

### 이전 foundation 이니셔티브 8개

- `extension/work/PROJECT_FOUNDATION_DESIGN.md`
- `extension/work/project-foundation/M0_BASELINE_AND_SUCCESS_GATES.md`
- `extension/work/project-foundation/M1_FRESH_CLONE_AND_CORE_PURITY.md`
- `extension/work/project-foundation/M2_DESIGN_EXECUTION_CONTRACT.md`
- `extension/work/project-foundation/M3_SINGLE_QUALITY_GATE.md`
- `extension/work/project-foundation/M4_VIDEO_WORKFLOW_ENGINE.md`
- `extension/work/project-foundation/M5_LEARNING_AND_COMPLEXITY_AUDIT.md`
- `extension/work/project-foundation/M6_CORE_EXPORT_GAME_PILOT.md`

### 과거 report 10개와 별도 plan 4개

`extension/reports/`의 10개 top-level report는 다음 중 현재 최종 보고서가 아닌 9개를 M4 후보로 판정한다. `2026-07-31_규칙_무손실_통합_M0_작업_보고.md`는 모든 단계의 최종 보고서 owner로 갱신·보존한다.

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

### 0-byte·빈 디렉터리 후보

- `docs.md` — 0 bytes
- `extension/work/2026-06-30-00-23-03/xml_build/` — empty
- `extension/work/2026-06-30-00-23-03/` — child `xml_build`만 보유한 empty parent candidate

Inbound scan 결과, 현재 startup-required chain이 직접 읽도록 요구하는 후보는 0개다. 다만 2026-07-31 사후 감사에서 M4 exact-list 문서를 제외한 retained 5문서에 후보 경로의 비링크 역사·처분 표기 40건과 overall의 실행 가능한 Markdown evidence link 1건을 확인했다. M4-S2에서 실행 가능한 link는 0으로 만들고, 비링크 path 표기는 Git 복구·처분 기록인지 active dependency인지 분류한다. historical report는 M0 map·handoff의 source evidence로만 남아 있으며, 이전 foundation report가 old foundation overall과 M0 phase를 참조한다. M4 전 최종 보고서에 지식·source anchor·복구 경로를 보존하고, 그 report와 predecessor를 함께 처분하는 bundle을 별도로 승인받는다.

## Slice gate

M3-S1~M3-S4의 각 slice는 startup route·후보 inventory·실제 gate 결과를 기록한 뒤 다음 slice로 전환한다.

## M3-S3 — 회귀·문서 무결성 gate

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH=((Resolve-Path 'core/src').Path, (Resolve-Path 'extension/src').Path, (Resolve-Path 'core/tests').Path -join ';')
python -m unittest discover -s core/tests -q
python -m unittest discover -s extension/tests -q
python -m file_data --root . maintenance-verify
```

M2 이후 Core diff가 없음을 확인하고 기본 maintenance를 사용한다. 추가로 startup route 링크, active phase 단일성, old candidate의 inbound reference, strict UTF-8·NUL 0·후행 공백·`git diff --check`를 직접 검사한다. 음성 대조는 “현재 startup이 old foundation/report를 읽도록 요구하지 않는가”를 확인한다.

## Exit gate

M3-S4의 결과가 아래 조건을 모두 충족해야 M3를 `passed`로 전환한다.

## M3-S4 — M4 transition gate

- startup route가 위 1개 active phase만 가리키고 active phase·current-state owner가 각각 하나다.
- Core 139개·Extension 132개와 기본 maintenance가 통과한다.
- M0 map의 과거 후보 수치가 현재 exact inventory로 교정되고, 후보 23개 파일·2개 child-first 디렉터리 후보의 path·size·inbound·보존/처분 이유가 있다.
- 최종 보고서 owner는 1개이고, 삭제하지 않을 최종 보고서·M0 evidence·handoff·overall의 역할이 분리된다.
- M4 처분 후보의 exact list, bundle dependency, unique evidence/recovery 확인 결과가 사용자 승인 질문으로 정리된다.
- M3 동안 삭제·이동은 0건이며 보호 staged count도 0이다.

통과 뒤 lifecycle을 `passed`로 바꾸고, M4 phase-design에 exact disposition approval boundary를 넘긴다. M4 승인 전에는 어떤 후보도 제거하지 않는다.

## 복구·전환 gate

라우팅·수치·참조 검증이 실패하면 후보를 처분하지 않고 M3 문서와 handoff에 원인·경로·다음 조사 방법을 기록한다. 문서 손상은 마지막 정상 Git 버전과 strict UTF-8/NUL/scoped diff를 대조해 복구한다. 동일 목적이 세 번 실패하면 blocker를 보존하고 새 권한 없는 조회 방법으로 전환한다.

## Closeout record

- M3-S1: `passed` — active link 1개, startup old-foundation reference 0개
- M3-S2: `passed` — exact inventory 23개 파일·2개 child-first 디렉터리 후보, M4 후보는 최종 보고서 제외 22개 파일
- M3-S3: `passed` — Core 139·Extension 132·기본 maintenance pass·문서 무결성 통과
- M3-S4: `passed` — Core diff 0, 삭제·이동 0, 보호 staged count 0, M4 exact 목록 준비
- M3 exit: `passed`
- M4 transition: `passed` — M4 준비 checkpoint `11a6031`에서 exact approval boundary 활성화
