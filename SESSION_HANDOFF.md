# 세션 핸드오프

- 갱신일: 2026-07-31
- 역할: ainotebook 이외 worktree의 현재 work·blocker·검증 상태·첫 다음 행동 단일 owner
- 현재 작업: 프로젝트 전역 지식 선별·구조 통합·workspace 정리 W0
- 상태: W0-S1~S4와 exit gate가 passed다. 전 작업트리 555파일의 Git/filesystem inventory와 1차 분류를 완료했고 W0 phase commit 뒤 W1로 전환한다.
- 활성 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 활성 단계 설계: `extension/work/repository-consolidation/W0_REPOSITORY_WIDE_INVENTORY_AND_CLASSIFICATION.md`
- 프로젝트 방향: `PROJECT_DIRECTION.md`
- 읽기 순서: `PROJECT_RULES.md` → 이 문서 → 활성 전체 설계 → W0 phase-design → W0 다음 행동에 matching된 규칙
- handoff mode: `same-workspace`; 현재 설계·감사 변경이 uncommitted이므로 fresh clone에서 재개 가능하다고 주장하지 않는다.

## 현재 사용자 의도

- 정리 범위는 ignored 파일만이 아니라 tracked·untracked·ignored, 백룸·개선 작업에서 생성된 모든 프로젝트 파일과 `outputs/`·`extension/data/`를 포함한다.
- 모든 내용을 무조건 흡수하지 않는다. 이후 반복 workflow에 재사용할 수 있는 지식·계약·검증·실패 예방만 선별한다.
- 재사용 내용은 기존 canonical owner에 우선 흡수·병합하고, 기존 owner가 서로 다른 책임을 섞을 때만 최소 owner를 신설한다.
- 최종 결과는 단계 gate와 commit을 거친 Git clean 상태이며, reviewed allowlist 밖의 untracked·ignored·임시·백룸·개선 산출물도 0인 설명 가능한 workspace다.
- 삭제·이동은 지식 추출·owner 반영·reference·rebuild/recovery 검증 후 새 exact 목록으로 승인받아 수행한다.

## 검증된 baseline

- branch `main`, HEAD `11a6031d93e9ea86b11a477450b37d459c847943`, `origin/main` 대비 20 commits ahead다.
- 사용자 범위 교정 전 entry dirty baseline은 이전 감사의 task-owned 6문서다: `SESSION_HANDOFF.md`, 기존 최종 보고서, M1·M2·M3·M4 phase-design. restore·discard하지 않는다.
- 현재 설계·W0 실행 변경은 `PROJECT_DIRECTION.md`, overall, W0 phase/evidence, handoff, M4 invalidation, 이전 보고 scope label, route test를 포함하며 모두 task-owned·uncommitted다.
- 기존 M0~M3은 규칙·문서 슬라이스 evidence로 유효하다. M4는 exact delete 승인 전에 `invalidated`됐고 삭제·이동은 0이다.
- W0 direct inventory는 tracked 209·untracked 1·ignored 345·filesystem 555/555, 5,223,547,559 bytes이며 양방향 차이·중복·오류·reparse가 0이다.
- 보호 경로는 inputs 2파일·3,799,860,960 bytes, outputs 201파일·604,959,116 bytes다. content와 exact 이름은 evidence에 복제하지 않았다.
- W0 분류는 canonical-retain 181, historical-git 7, disposition-candidate 22, regenerable-disposable 75, protected-user-artifact 2, unresolved 268로 합계 555다.
- W0 gate는 Core 139·Extension 132, maintenance 93문서·122링크(errors/drift/duplicates 0), overall 90줄·5,017자, W0 140줄·6,358자, strict UTF-8·NUL·후행 공백·diff check·보호 staged 0으로 통과했다.

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
| `extension/work/rule-preservation/M4_EXACT_DISPOSITION_AND_FINAL_REPORT.md` | invalidated phase-design | 이전 22파일 후보의 historical evidence; 실행 금지 |
| `extension/reports/2026-07-31_규칙_무손실_통합_M0_작업_보고.md` | historical partial evidence | 규칙·문서 슬라이스 검증; 프로젝트 전역 최종보고 아님 |
| `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md` | optional prior evidence | 규칙 의미 78개 계보·owner |

## blocker·위험

- runtime 67파일은 exact tracked reference가 0이지만 설치 source·rebuild command가 없어 unresolved다.
- protected outputs 201파일은 Git 복구가 없고 current deliverable·재생성·외부 복구가 미확정이라 W1/W3 전 자동 처분하지 않는다.
- entry dirty 6문서와 W0 task delta는 evidence의 exact path·composite hash로 구분했다.

## 실패 ledger

| objective | attempt | result / cause | count | next condition |
|---|---|---|---:|---|
| 프로젝트 전역 정리 설계 | 이전 M0~M4 | 문서·규칙 슬라이스를 전체 목표로 좁게 해석 | 1 | 사용자 직접 의도를 overall 상단에 고정하고 W0 전역 inventory로 재시작 |
| 전체 읽기 비용 비증가 | 이전 M2 | rule-surface +430 tokens(+4.41%) | 1 | W2에서 재사용 가치·중복 상쇄를 함께 검증, Core 변경은 exact 승인 |

## 첫 다음 행동

1. task-owned maintained path만 W0 phase commit한다.
2. commit object·포함 path·보호 staged 0·status를 검증한다.
3. W1 재사용 지식 추출·owner mapping phase를 활성화한다.

## 다음 session 시작 prompt

`PROJECT_RULES.md → SESSION_HANDOFF.md → overall-design → W0 phase-design → W0 evidence`를 읽고 W0 phase commit을 만든 뒤 W1로 전환한다. 보호 content·secret·Core·삭제·이동·외부 상태는 해당 exact 승인 없이 변경하지 않는다.
