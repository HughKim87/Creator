# 세션 핸드오프

- 갱신일: 2026-07-31
- 역할: ainotebook 이외 worktree의 현재 work·blocker·검증 상태·첫 다음 행동 단일 owner
- 현재 작업: 프로젝트 전역 지식 선별·구조 통합·workspace 정리 W2
- 상태: W2-S1~S4와 전체 single gate가 passed했고, task-owned 7경로의 단계 checkpoint commit을 준비한다.
- 활성 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 활성 단계 설계: `extension/work/repository-consolidation/W2_SELECTIVE_ABSORPTION_AND_FOUNDATION_STRENGTHENING.md`
- 프로젝트 방향: `PROJECT_DIRECTION.md`
- 읽기 순서: `PROJECT_RULES.md` → 이 문서 → 활성 전체 설계 → W2 phase-design → W2 다음 행동에 matching된 규칙
- handoff mode: `same-workspace`; W2 phase activation이 uncommitted이므로 fresh clone은 W1 checkpoint까지만 재개 가능하다.

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
| `extension/work/rule-preservation/M4_EXACT_DISPOSITION_AND_FINAL_REPORT.md` | invalidated phase-design | 이전 22파일 후보의 historical evidence; 실행 금지 |
| `extension/reports/2026-07-31_규칙_무손실_통합_M0_작업_보고.md` | historical partial evidence | 규칙·문서 슬라이스 검증; 프로젝트 전역 최종보고 아님 |
| `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md` | optional prior evidence | 규칙 의미 78개 계보·owner |

## blocker·위험

- runtime 67파일은 exact tracked reference가 0이지만 설치 source·rebuild command가 없어 unresolved다.
- protected outputs 201파일은 Git 복구가 없고 current deliverable·재생성·외부 복구가 미확정이라 W1/W3 전 자동 처분하지 않는다.
- W1 first single-gate는 sandbox 상위 경로 EPERM과 optional evidence metadata 누락으로 실패했다. metadata를 복구했고 권한 있는 Node·clean-clone 및 전체 회귀가 통과해 환경·구현 실패를 분리했다.

## 실패 ledger

| objective | attempt | result / cause | count | next condition |
|---|---|---|---:|---|
| 프로젝트 전역 정리 설계 | 이전 M0~M4 | 문서·규칙 슬라이스를 전체 목표로 좁게 해석 | 1 | 사용자 직접 의도를 overall 상단에 고정하고 W0 전역 inventory로 재시작 |
| 전체 읽기 비용 비증가 | 이전 M2 | rule-surface +430 tokens(+4.41%) | 1 | W2에서 재사용 가치·중복 상쇄를 함께 검증, Core 변경은 exact 승인 |

## 첫 다음 행동

1. W2 task-owned 7경로만 stage하고 보호·Core·unrelated staged count 0을 확인한다.
2. W2 단계 commit을 만든 뒤 commit path와 Git 상태를 검증한다.
3. W3 phase-design을 활성화하고 전역 allowlist와 exact disposition manifest를 작성한다.

## 다음 session 시작 prompt

`PROJECT_RULES.md → SESSION_HANDOFF.md → overall-design → W2 phase-design → W1 evidence`를 읽고 W2 commit gate부터 실행한다. 보호 원문·exact 이름·secret·Core·삭제·이동·외부 상태는 해당 exact 승인 없이 변경하지 않는다.
