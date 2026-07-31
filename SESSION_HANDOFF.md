# 세션 핸드오프

- 갱신일: 2026-07-31
- 역할: ainotebook 이외 worktree의 현재 work·blocker·검증 상태·첫 다음 행동 단일 owner
- 현재 작업: 프로젝트 전역 지식 선별·구조 통합·workspace 정리 W3 exit
- 상태: W3 의존성 해제·exact disposition manifest와 전체 gate가 passed했고, W4 exact Core·처분 승인만 기다린다.
- 활성 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 활성 단계 설계: `extension/work/repository-consolidation/W3_DEPENDENCY_RELEASE_AND_EXACT_DISPOSITION_MANIFEST.md`
- 프로젝트 방향: `PROJECT_DIRECTION.md`
- 읽기 순서: `PROJECT_RULES.md` → 이 문서 → 활성 전체 설계 → W3 phase-design → W3 다음 행동에 matching된 규칙
- handoff mode: `same-workspace`; 보호 allowlist와 처분 후보는 Git 밖의 uncommitted filesystem state이므로 W3 exit commit과 현재 workspace를 함께 재개 checkpoint로 사용한다.

## 현재 사용자 의도

- 정리 범위는 ignored 파일만이 아니라 tracked·untracked·ignored, 백룸·개선 작업에서 생성된 모든 프로젝트 파일과 `outputs/`·`extension/data/`를 포함한다.
- 모든 내용을 무조건 흡수하지 않는다. 이후 반복 workflow에 재사용할 수 있는 지식·계약·검증·실패 예방만 선별한다.
- 재사용 내용은 기존 canonical owner에 우선 흡수·병합하고, 기존 owner가 서로 다른 책임을 섞을 때만 최소 owner를 신설한다.
- 최종 결과는 단계 gate와 commit을 거친 Git clean 상태이며, reviewed allowlist 밖의 untracked·ignored·임시·백룸·개선 산출물도 0인 설명 가능한 workspace다.
- 삭제·이동은 지식 추출·owner 반영·reference·rebuild/recovery 검증 후 새 exact 목록으로 승인받아 수행한다.

## 검증된 baseline

- branch `main`, HEAD `16f87cc961dd1a216697b218eb30cb84d705526b`, `origin/main` 대비 21 commits ahead이며 W1 entry status는 clean이었다.
- W0 commit은 11개 비보호 task-owned path만 포함했고 Core·보호 path count가 0이었다.
- 기존 M0~M3은 규칙·문서 슬라이스 evidence로 유효하다. M4는 exact delete 승인 전에 `invalidated`됐고 삭제·이동은 0이다.
- W0 direct inventory는 tracked 209·untracked 1·ignored 345·filesystem 555/555, 5,223,547,559 bytes이며 양방향 차이·중복·오류·reparse가 0이다.
- 보호 경로는 inputs 2파일·3,799,860,960 bytes, outputs 201파일·604,959,116 bytes다. content와 exact 이름은 evidence에 복제하지 않았다.
- W0 분류는 canonical-retain 181, historical-git 7, disposition-candidate 22, regenerable-disposable 75, protected-user-artifact 2, unresolved 268로 합계 555다.
- W0 gate는 Core 139·Extension 132, maintenance 93문서·122링크(errors/drift/duplicates 0), overall 90줄·5,017자, W0 140줄·6,358자, strict UTF-8·NUL·후행 공백·diff check·보호 staged 0으로 통과했다.
- W1은 과거 문서 21/21, 선행 evidence 7/7, 보호 opaque output 10/10을 대조해 K01~K04만 W2로 넘겼다. 신규 owner·Core 후보는 0이고 exact W2 owner는 `README.md`, `extension/README.md`, 영상 R01이다.
- W1 gate는 Core 139·Extension 132, Node v20.11.1, maintenance 95문서·122링크, ASCII·한글+공백·공백 경로 clean clone 3/3으로 통과했다.
- W1 commit `f02c304`는 task-owned 5경로만 포함했고 Core·보호 path count가 0이며 commit 뒤 status는 clean이었다.
- W2는 K01~K04를 기존 owner 3개에 순증가 20줄로 흡수했다. 신규 file·rule·replay·schema·code·dependency와 Core diff는 0이다.
- W2 gate는 focused 56 tests, Core 139·Extension 132, Node ready, maintenance 96문서·130링크, clean clone 3/3으로 통과했다.
- W2 commit `5ed6bb6`는 task-owned 7경로만 포함했고 Core·보호 path count가 0이며 commit 뒤 status는 clean이었다.
- W3 기준 inventory는 manifest 생성 전 tracked 214·untracked 1·ignored 345·Git union/filesystem 560/560이었고 양방향 차이·중복·reparse가 0이었다.
- W3은 최종 tracked allowlist 180개와 보호 입력 2개·보호 출력 4개를 고정했다. W4 처분 후보는 파일 367개·1,305,301,788 bytes와 빈 디렉터리 6개다.
- W3 dry-run은 exact tracked 28개, 비보호 ignored 142개, 보호 출력 197개의 존재·용량·집계 해시를 재계산했고 duplicate·보호 겹침·workspace 이탈이 0이었다.
- W3 gate는 Core 139·Extension 132, Node v20.11.1, maintenance 98문서·130링크, clean clone 3/3으로 passed다.

## 권한·보호 경계

- 현재 사용자 지시는 전 작업트리의 inventory·분류와 정리 설계를 승인한다.
- W0는 보호 path를 포함한 최소 metadata inventory만 수행한다. 보호 content·exact filename을 reusable evidence나 Git에 복제하지 않고 보호 path를 stage·commit하지 않는다.
- secret·credential·cookie·token·browser profile 내용은 읽지 않고 `sensitive-unread`로 분류한다.
- Core mutation은 exact 경로·이유·extension 대안을 제시한 뒤 현재 대화의 별도 승인이 필요하다.
- 삭제·이동·rename·overwrite는 W3의 새 exact manifest와 사용자 승인 전까지 금지한다.
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
| `extension/work/repository-consolidation/W3_DISPOSITION_MANIFEST.md` | current reference-evidence | exact tracked·ignored 처분, 보호 opaque allowlist, Core 승인 경계 |
| `extension/work/rule-preservation/M4_EXACT_DISPOSITION_AND_FINAL_REPORT.md` | invalidated phase-design | 이전 22파일 후보의 historical evidence; 실행 금지 |
| `extension/reports/2026-07-31_규칙_무손실_통합_M0_작업_보고.md` | historical partial evidence | 규칙·문서 슬라이스 검증; 프로젝트 전역 최종보고 아님 |
| `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md` | optional prior evidence | 규칙 의미 78개 계보·owner |

## blocker·위험

- `core/tests/test_rule_routing.py`가 처분 후보 역사 보고서를 직접 읽는다. W4에서 현재 canonical owner로 fixture를 전환하려면 exact Core 승인이 필요하다.
- 보호 출력 제거 후보 197개와 runtime 67개는 byte-identical Git 복구가 불가능하다. 보호 출력 4개와 입력 2개는 보존한다.
- W4 삭제·빈 디렉터리 제거는 exact 승인 전 금지다. 승인 뒤에도 집계 해시가 달라지면 실행하지 않고 재측정한다.

## 실패 ledger

| objective | attempt | result / cause | count | next condition |
|---|---|---|---:|---|
| 프로젝트 전역 정리 설계 | 이전 M0~M4 | 문서·규칙 슬라이스를 전체 목표로 좁게 해석 | 1 | 사용자 직접 의도를 overall 상단에 고정하고 W0 전역 inventory로 재시작 |
| 전체 읽기 비용 비증가 | 이전 M2 | rule-surface +430 tokens(+4.41%) | 1 | W2에서 재사용 가치·중복 상쇄를 함께 검증, Core 변경은 exact 승인 |
| W3 통합 dry-run | 구형 PowerShell 상대경로 API | `GetRelativePath` 미지원으로 첫 통합 집계가 무효 | 1 | 호환 substring 방식으로 재실행해 모든 수치·해시 일치 |
| W3 전체 gate | sandbox·실행시간 | Node 상위 경로 EPERM 뒤 권한 실행이 124초 제한 초과 | 2 | 승인된 환경에서 139.1초 재실행, 전체 exit 0 |
| W3 closeout 문서 gate | 증거 상세화 | active phase 162줄·same-workspace marker 누락 | 1 | phase 160줄로 압축·uncommitted 경계 복구, focused 6개와 전체 no-clone gate 통과 |

## 첫 다음 행동

1. 사용자에게 `core/tests/test_rule_routing.py`의 exact fixture routing 변경 승인을 받는다.
2. tracked 28개, 비보호 ignored 142개, 보호 출력 197개, 빈 디렉터리 6개의 exact 처분 승인을 받는다.
3. 두 승인이 모두 있으면 mutation 직전 해시·containment를 재검증하고 W4를 시작한다.

## 다음 session 시작 prompt

`PROJECT_RULES.md → SESSION_HANDOFF.md → overall-design → W3 phase-design → W3 disposition manifest`를 읽는다. 현재 대화의 exact Core 승인과 exact 처분 승인이 모두 있을 때만 W4를 설계·실행하고, 보호 보존 6개는 stage·commit·삭제하지 않는다.
