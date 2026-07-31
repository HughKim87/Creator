# W5 전역 회귀·규칙 계보 보고·clean closeout

- 문서 분류: `phase-design`
- phase ID: `W5`
- lifecycle: `in_progress`
- 결과: 삭제 자료의 모든 재사용 규칙·지식을 원문에서 현재 owner까지 추적해 최종 보고하고, initiative 문서를 제거한 뒤 Git과 물리 workspace를 설명 가능한 clean 상태로 닫는다.
- 독자: 최종 결과를 검수하는 사용자와 다음 작업 agent
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- 최종 보고 owner: `extension/reports/2026-07-31_규칙_무손실_통합_M0_작업_보고.md`
- optional evidence owner: `extension/work/repository-consolidation/W1_REUSABLE_KNOWLEDGE_MAP.md` — startup-required 아님, W5 source coverage 대조 뒤 self-clean
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; inputs 내용·push·publish·history rewrite는 범위 밖이다.
- 첫 다음 행동: 삭제 source를 reachable Git commit에서 읽고 규칙별 lineage matrix를 현재 owner·commit·test와 교차검증한다.

## Entry gate

- W4-S1~S5 `passed`; 처분 commit `53607e9`; status clean.
- refs 11·stash 2·reflog 393·reachable object 4,640·graph 224와 `e705f71` tree가 GC 전후 동일하다.
- inputs 제외 inventory는 tracked 193, ignored 71(runtime 67 + current output 4), untracked 0, filesystem 264다.
- 기존 최종 보고서는 historical partial evidence이며 W5에서 전면 재작성한다.

## 불변 경계

- `extension/inputs/**`는 열람·해시·분류·변경·stage하지 않는다.
- current output 4와 runtime 67은 이름·크기·상태만 재검증하고 내용은 변경하지 않는다.
- 삭제 source는 `e705f71`, M0~W4 checkpoint와 현재 canonical owner에서 read-only로 교차검증한다.
- 같은 의미를 문서 수만큼 중복 규칙으로 세지 않고, distinct rule마다 모든 source를 연결한다.
- 신규 owner는 기존 owner가 의미를 표현할 수 없을 때만 허용하며, 그 경우 이유·경로·검증을 보고한다.

## Slice gate

각 slice는 source coverage·owner·실제 변경·정량 검증을 기록하고 통과한 뒤 다음 slice로 전환한다.

## W5-S1 — 삭제 자료 규칙·지식 lineage 재구성

다음 corpus를 빠짐없이 대조한다.

1. 삭제된 과거 report·plan·foundation 28개와 M0 rule-conservation evidence
2. output structure/text 84개 중 규칙을 담은 Markdown 14개와 schema·validator 근거
3. W1 K01~K04, M0~M4에서 복원·보류·폐기한 의미, 현재 rule·contract·README·code·test

최종 보고의 규칙 표는 distinct rule마다 다음 열을 가진다.

| 열 | 필수 내용 |
|---|---|
| 규칙 ID·주제 | 보고서 안에서 안정적으로 참조할 ID와 한 문장 이름 |
| 원문 내용 | 삭제 source 경로·anchor·원래 요구의 충실한 요약; 중복 source는 함께 열거 |
| 추출 규칙 | 조건·행동·예외·검증이 드러나는 재사용 문장 |
| 처분 | `absorbed-existing / created-owner / already-canonical / not-restored` |
| 현재 위치 | 실제 canonical 파일·section 또는 code/schema/test owner |
| 수행 작업 | 어느 commit에서 병합·보강·신설·비복원했는지 |
| 교차검증 | 현재 본문·동작 test·route·single gate 증거 |

규칙이 아닌 task-specific 지식, media derivative, revision history, cache/local state도 별도 표로 무엇이 있었고 왜 흡수하지 않았는지 기록한다.

### W5-S1 gate

- distinct rule 100%가 source→extraction→owner/disposition으로 연결되고 미매핑 0이다.
- 삭제 source가 주장한 현재 상태는 code·test·현재 문서로 재측정하며 stale 문구를 승격하지 않는다.
- 원문 복제와 의미 요약을 구분하고 신규·기존 owner 여부를 각각 명시한다.

## W5-S2 — 최종 보고서 전면 갱신

최종 보고서는 의도·범위, W0~W5와 이전 M0~M4의 설계/실제 커밋 대조, 삭제·보존 inventory, 규칙별 lineage, 비흡수 지식, 실패·교정, 정량 효과, 단계·슬라이스 점수, 복구 경계를 포함한다.

### W5-S2 gate

- commit hash·path count·bytes·test count·Git GC 수치가 실제 명령 결과와 일치한다.
- 각 단계 목표와 실제 결과가 분리되고 모든 단계·slice에 5점 만점 점수와 이유가 있다.
- 근거 없는 시간 절감·품질 향상은 주장하지 않고 입증 가능한 수치만 효과로 제시한다.
- 보고서는 삭제되는 initiative 문서를 active link로 요구하지 않고 Git commit을 복구 근거로 안내한다.

## W5-S3 — initiative self-clean·idle handoff

최종 보고에 의미를 흡수한 뒤 다음 10개 initiative 문서를 제거한다.

1. `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
2. `extension/work/repository-consolidation/W0_REPOSITORY_WIDE_INVENTORY_AND_CLASSIFICATION.md`
3. `extension/work/repository-consolidation/W0_FILE_CLASSIFICATION.md`
4. `extension/work/repository-consolidation/W1_REUSABLE_KNOWLEDGE_EXTRACTION_AND_OWNER_MAPPING.md`
5. `extension/work/repository-consolidation/W1_REUSABLE_KNOWLEDGE_MAP.md`
6. `extension/work/repository-consolidation/W2_SELECTIVE_ABSORPTION_AND_FOUNDATION_STRENGTHENING.md`
7. `extension/work/repository-consolidation/W3_DEPENDENCY_RELEASE_AND_EXACT_DISPOSITION_MANIFEST.md`
8. `extension/work/repository-consolidation/W3_DISPOSITION_MANIFEST.md`
9. `extension/work/repository-consolidation/W4_RUNTIME_OUTPUT_CONSOLIDATION_AND_CLEANUP.md`
10. `extension/work/repository-consolidation/W5_GLOBAL_REGRESSION_RULE_LINEAGE_AND_CLEAN_CLOSEOUT.md`

`SESSION_HANDOFF.md`는 active initiative가 없는 idle truth, clean 상태, 보존 allowlist와 다음 일반 작업 시작점만 남긴다.

### W5-S3 gate

- 10개 삭제와 final report·handoff 변경만 W5 diff에 존재한다.
- 삭제 문서 inbound active link 0, 빈 initiative directory 0, historical 복구는 Git commit으로 가능하다.

## W5-S4 — 전역 회귀·final commit

- Core·Extension 전체 test, maintenance, Node/bootstrap, runtime actual probe, clean-clone ASCII·한글·공백 3종을 통과한다.
- strict UTF-8·NUL·후행 공백·link·`git diff --check`를 통과한다.
- inputs 제외 최종 예상은 tracked 184, ignored 71, untracked 0, filesystem 255이며 tracked input·output·cache 0이다.
- final commit 후 `git status --porcelain`이 비고, ignored 71은 runtime 67 + current output 4로 정확히 설명된다.

## Exit·commit gate

- W5-S1~S4가 모두 passed이고 final report·idle handoff·Git clean 상태가 같은 commit에서 확정된다.
- final commit의 실제 hash와 status는 commit 뒤 read-only 검증으로 보고한다.

## 완료·중단 조건

- source와 owner가 불일치하면 보고서에 unresolved로 남기고 해당 owner를 사실처럼 주장하지 않는다.
- 보호 allowlist가 달라지거나 예상 외 파일이 생기면 self-clean과 commit을 중단하고 inventory를 갱신한다.
- 전체 gate 하나라도 실패하면 final commit 전 원인을 교정하고 같은 gate를 재실행한다.
