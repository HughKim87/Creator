# 세션 핸드오프

- 갱신일: 2026-07-31
- 역할: ainotebook 이외 worktree의 현재 work·blocker·검증 상태·첫 다음 행동 단일 owner
- 현재 작업: 프로젝트 전역 지식 선별·구조 통합·workspace 정리 W4-S1 준비
- 상태: inputs 제외·runtime 67개 보존·outputs 중심 W4 phase-design과 전체 gate가 passed했고 W4-S1 runtime 관리화 구현이 ready다.
- 활성 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 활성 단계 설계: `extension/work/repository-consolidation/W4_RUNTIME_OUTPUT_CONSOLIDATION_AND_CLEANUP.md`
- 프로젝트 방향: `PROJECT_DIRECTION.md`
- 읽기 순서: `PROJECT_RULES.md` → 이 문서 → 활성 전체 설계 → W4 phase-design → W4 첫 다음 행동에 matching된 규칙
- handoff mode: `same-workspace`; ignored runtime·보호 output과 W4 uncommitted design 때문에 현재 workspace를 재개 checkpoint로 사용한다.

## 현재 사용자 의도

- 분석·정리 범위는 `inputs/**`를 제외한 tracked·untracked·ignored, 백룸·개선 파일과 `outputs/`·`extension/data/`를 포함한다.
- 모든 내용을 무조건 흡수하지 않는다. 이후 반복 workflow에 재사용할 수 있는 지식·계약·검증·실패 예방만 선별한다.
- 재사용 내용은 기존 canonical owner에 우선 흡수·병합하고, 기존 owner가 서로 다른 책임을 섞을 때만 최소 owner를 신설한다.
- 최종 결과는 단계 gate와 commit을 거친 Git clean 상태이며, reviewed allowlist 밖의 untracked·ignored·임시·백룸·개선 산출물도 0인 설명 가능한 workspace다.
- 삭제·이동은 지식 추출·owner 반영·reference·rebuild/recovery 검증 후 새 exact 목록으로 승인받아 수행한다.
- FFmpeg·whisper.cpp·모델 67개는 삭제하지 않고 검증 가능한 ignored local capability로 유지한다.

## 검증된 baseline

- branch `main`, W3 HEAD `73d66e4`, `origin/main` 대비 24 commits ahead이며 W4 entry status는 clean이었다.
- W0 commit은 11개 비보호 task-owned path만 포함했고 Core·보호 path count가 0이었다.
- 기존 M0~M3은 규칙·문서 슬라이스 evidence로 유효하다. M4는 exact delete 승인 전에 `invalidated`됐고 삭제·이동은 0이다.
- W0 direct inventory는 tracked 209·untracked 1·ignored 345·filesystem 555/555, 5,223,547,559 bytes이며 양방향 차이·중복·오류·reparse가 0이다.
- outputs 기준 inventory는 201파일·604,959,116 bytes다. inputs는 최신 지시에 따라 분석 수치에서 제외하고 보호 경계로만 유지한다.
- W0 분류는 canonical-retain 181, historical-git 7, disposition-candidate 22, regenerable-disposable 75, protected-user-artifact 2, unresolved 268로 합계 555다.
- W0 gate는 Core 139·Extension 132, maintenance 93문서·122링크(errors/drift/duplicates 0), overall 90줄·5,017자, W0 140줄·6,358자, strict UTF-8·NUL·후행 공백·diff check·보호 staged 0으로 통과했다.
- W1은 과거 문서 21/21, 선행 evidence 7/7, 보호 opaque output 10/10을 대조해 K01~K04만 W2로 넘겼다. 신규 owner·Core 후보는 0이고 exact W2 owner는 `README.md`, `extension/README.md`, 영상 R01이다.
- W1 gate는 Core 139·Extension 132, Node v20.11.1, maintenance 95문서·122링크, ASCII·한글+공백·공백 경로 clean clone 3/3으로 통과했다.
- W1 commit `f02c304`는 task-owned 5경로만 포함했고 Core·보호 path count가 0이며 commit 뒤 status는 clean이었다.
- W2는 K01~K04를 기존 owner 3개에 순증가 20줄로 흡수했다. 신규 file·rule·replay·schema·code·dependency와 Core diff는 0이다.
- W2 gate는 focused 56 tests, Core 139·Extension 132, Node ready, maintenance 96문서·130링크, clean clone 3/3으로 통과했다.
- W2 commit `5ed6bb6`는 task-owned 7경로만 포함했고 Core·보호 path count가 0이며 commit 뒤 status는 clean이었다.
- W3 기준 inventory는 manifest 생성 전 tracked 214·untracked 1·ignored 345·Git union/filesystem 560/560이었고 양방향 차이·중복·reparse가 0이었다.
- W3의 runtime 삭제와 input 분석 판정은 최신 사용자 정정으로 superseded다. current output keep 4개는 유지한다.
- W3 dry-run은 exact tracked 28개, 비보호 ignored 142개, 보호 출력 197개의 존재·용량·집계 해시를 재계산했고 duplicate·보호 겹침·workspace 이탈이 0이었다.
- W3 gate는 Core 139·Extension 132, Node v20.11.1, maintenance 98문서·130링크, clean clone 3/3으로 passed다.
- input 제외 분석 범위는 559개·1.326 GiB이며 runtime 67개·778.52 MiB, outputs 201개·576.93 MiB, 기타 291개·2.35 MiB다.
- outputs 처분 후보 197개는 media 113개·475,943,400 bytes와 structure/text 84개·11,793,473 bytes다.
- runtime 보존으로 수정된 처분 예상은 tracked 28개, cache/local 75개, outputs 197개로 합계 300개·488,962,975 bytes다.
- `.git`은 6.428 GiB이며 현재 refs에 없는 pack 약 3.284 GiB와 temporary garbage 약 2.895 GiB를 별도 위생 대상으로 확인했다. stash 2개는 보존해야 한다.
- W4 design gate는 focused 27개, Core 139·Extension 132, maintenance 99문서·130링크, clean clone 3/3으로 passed다. 설계 점수는 4.5/5다.

## 권한·보호 경계

- 현재 사용자 지시는 inputs 제외 범위의 inventory·정리 설계와 runtime 보존 방향을 승인한다.
- W0는 보호 path를 포함한 최소 metadata inventory만 수행한다. 보호 content·exact filename을 reusable evidence나 Git에 복제하지 않고 보호 path를 stage·commit하지 않는다.
- secret·credential·cookie·token·browser profile 내용은 읽지 않고 `sensitive-unread`로 분류한다.
- Core mutation은 exact 경로·이유·extension 대안을 제시한 뒤 현재 대화의 별도 승인이 필요하다.
- 보호 output 내용 열람, 삭제·이동·rename·overwrite, Git object prune는 W4의 분리된 exact 승인 전까지 금지한다.
- 단계 exit commit은 사용자가 요청한 단계 규칙을 따르되 task-owned maintained path만 포함하고 push하지 않는다.

## 중요 artifact

| 경로 | 상태 | 역할 |
|---|---|---|
| `PROJECT_DIRECTION.md` | active reference-evidence | 프로젝트 전역 clean·선별 흡수 방향 |
| `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md` | active overall-design | W0~W5 단계·불변 경계·전체 성공 기준 |
| `extension/work/repository-consolidation/W0_REPOSITORY_WIDE_INVENTORY_AND_CLASSIFICATION.md` | passed phase-design | 전 파일 inventory·provenance·owner·reuse 분류 |
| `extension/work/repository-consolidation/W0_FILE_CLASSIFICATION.md` | optional reference-evidence | 555파일 그룹 분류·보호 aggregate·W1/W3 queue |
| `extension/work/repository-consolidation/W1_REUSABLE_KNOWLEDGE_EXTRACTION_AND_OWNER_MAPPING.md` | passed phase-design | report·plan·보호 text/structure의 재사용 지식·owner mapping |
| `extension/work/repository-consolidation/W1_REUSABLE_KNOWLEDGE_MAP.md` | optional reference-evidence | 21+7 source와 보호 output 10그룹의 owner·판정·W2 exact 입력 |
| `extension/work/repository-consolidation/W2_SELECTIVE_ABSORPTION_AND_FOUNDATION_STRENGTHENING.md` | passed phase-design | K01~K04를 기존 owner 3개에 최소 병합 |
| `extension/work/repository-consolidation/W3_DEPENDENCY_RELEASE_AND_EXACT_DISPOSITION_MANIFEST.md` | passed phase-design | 유지 allowlist·reference·rebuild/recovery·W4 exact 처분 후보 |
| `extension/work/repository-consolidation/W3_DISPOSITION_MANIFEST.md` | partially superseded evidence | runtime 삭제·input 분석 제외 전 수치의 역사 근거 |
| `extension/work/repository-consolidation/W4_RUNTIME_OUTPUT_CONSOLIDATION_AND_CLEANUP.md` | ready phase-design | runtime owner·outputs 선별·승인 처분·Git 위생 실행 계약 |
| `extension/work/rule-preservation/M4_EXACT_DISPOSITION_AND_FINAL_REPORT.md` | invalidated phase-design | 이전 22파일 후보의 historical evidence; 실행 금지 |
| `extension/reports/2026-07-31_규칙_무손실_통합_M0_작업_보고.md` | historical partial evidence | 규칙·문서 슬라이스 검증; 프로젝트 전역 최종보고 아님 |
| `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md` | optional prior evidence | 규칙 의미 78개 계보·owner |

## blocker·위험

- `core/tests/test_rule_routing.py`가 처분 후보 역사 보고서를 직접 읽는다. W4에서 현재 canonical owner로 fixture를 전환하려면 exact Core 승인이 필요하다.
- runtime은 현재 faster-whisper primary 계약과 다른 도구이므로 FFmpeg shared tool·whisper.cpp optional backend로 구분하고 source·license·hash·smoke test owner를 만들어야 한다.
- structure/text output 84개의 보호 열람 승인과 300개 처분 승인, Core 승인, Git object maintenance 승인은 서로 대체하지 않는다.
- `.git` 정리 전 branch·tag·stash 2개·reflog와 모든 reachable commit의 recovery를 검증해야 한다.

## 실패 ledger

| objective | attempt | result / cause | count | next condition |
|---|---|---|---:|---|
| 프로젝트 전역 정리 설계 | 이전 M0~M4 | 문서·규칙 슬라이스를 전체 목표로 좁게 해석 | 1 | 사용자 직접 의도를 overall 상단에 고정하고 W0 전역 inventory로 재시작 |
| 전체 읽기 비용 비증가 | 이전 M2 | rule-surface +430 tokens(+4.41%) | 1 | W2에서 재사용 가치·중복 상쇄를 함께 검증, Core 변경은 exact 승인 |
| W3 통합 dry-run | 구형 PowerShell 상대경로 API | `GetRelativePath` 미지원으로 첫 통합 집계가 무효 | 1 | 호환 substring 방식으로 재실행해 모든 수치·해시 일치 |
| W3 전체 gate | sandbox·실행시간 | Node 상위 경로 EPERM 뒤 권한 실행이 124초 제한 초과 | 2 | 승인된 환경에서 139.1초 재실행, 전체 exit 0 |
| W3 closeout 문서 gate | 증거 상세화 | active phase 162줄·same-workspace marker 누락 | 1 | phase 160줄로 압축·uncommitted 경계 복구, focused 6개와 전체 no-clone gate 통과 |

## 첫 다음 행동

1. runtime 67개를 변경 없이 tree hash·version·entrypoint·license·source 기준으로 재측정한다.
2. local runtime manifest·schema·read-only verifier·synthetic test의 최소 구현 delta를 확정한다.
3. runtime owner commit 뒤 structure/text outputs 84개의 exact 보호 열람 승인을 요청한다.

## 다음 session 시작 prompt

`PROJECT_RULES.md → SESSION_HANDOFF.md → overall-design → W4 phase-design`을 읽고 W4-S1부터 실행한다. inputs는 분석하지 않고 runtime은 stage·삭제하지 않으며, output 열람·Core·삭제·Git prune는 각각 exact 승인 뒤 수행한다.
