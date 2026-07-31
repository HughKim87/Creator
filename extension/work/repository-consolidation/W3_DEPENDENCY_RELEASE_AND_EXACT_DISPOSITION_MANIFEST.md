# W3 의존성 해제·exact disposition manifest

- 문서 분류: `phase-design`
- phase ID: `W3`
- lifecycle: `passed`
- 결과: W2 이후 전 작업트리의 유지 allowlist와 tracked·ignored·runtime·보호 output 처분 후보를 reference·rebuild·recovery·승인 조건과 함께 확정한다.
- 독자: W3 실행 agent, W4 처분 승인자와 실행 agent
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- optional evidence owner: `extension/work/repository-consolidation/W3_DISPOSITION_MANIFEST.md` — startup-required 아님, 보호 exact 이름·원문 금지
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; W3는 manifest·dry-run만 수행하며 삭제·이동·overwrite를 승인하지 않는다.
- 첫 다음 행동: W3 commit 뒤 사용자에게 Core fixture 전환과 exact 처분 대상을 함께 제시하고 W4 승인을 받는다.

## Entry gate

- W2-S1~S4와 exit/commit이 passed이고 checkpoint는 `5ed6bb6`다.
- entry 작업트리는 clean이다.
- W1 reusable source 28개와 보호 output 10그룹의 owner mapping이 완료됐고 W2 K01~K04가 기존 owner에 반영됐다.
- Core·보호 source mutation과 delete/move는 W3 범위가 아니다.

## 포함·제외 범위

포함:

- tracked role-ended report·plan·phase·empty file
- ignored Python cache·Obsidian local state·local runtime
- 보호 output opaque group과 inputs 보존 allowlist
- 빈 backroom 디렉터리
- retained file의 inbound reference와 W4 reference release delta
- W5에서 역할이 끝나는 current initiative 문서의 self-clean queue

제외:

- protected media 내용 재생·전사·이미지 분석
- secret·credential·browser profile 내용
- W3에서의 실제 삭제·이동·rename·overwrite
- Git history rewrite·push·외부 backup 생성

## Slice gate

각 slice는 대상 aggregate 또는 exact 비보호 path, 현재 owner·reference, rebuild/recovery, 권장 처분, 승인 경계를 manifest에 기록하고 합계가 현재 inventory와 일치한 뒤 다음 slice로 전환한다.

## W3-S1 — 유지 allowlist

현재 tracked canonical owner와 사용자가 보존해야 할 보호 source를 먼저 고정한다. 유지 이유는 “Git에 있음”이 아니라 startup·rule·contract·code·test·schema·skill·사용자 source·현재 initiative 중 하나여야 한다.

### W3-S1 gate

- 현재 filesystem과 Git union의 양방향 차이·중복·enumeration error 0
- 모든 file이 유지·W4 처분·W5 self-clean·unresolved 중 하나에 정확히 한 번 포함
- protected inputs는 content 없이 opaque 보존 group으로만 기록

## W3-S2 — reference·rebuild·recovery

비보호 후보는 exact path로, 보호 output은 W0 opaque group으로 다음을 판정한다.

- active startup·runtime·code·test·Markdown inbound reference
- 동일 결과 재생성 가능 여부와 install/rebuild owner
- Git 또는 사용자 source로 복구 가능한지
- 유일한 canonical evidence인지

### W3-S2 gate

- tracked 처분 후보는 Git recovery 가능하고 active canonical owner가 아님
- cache·local state는 재생성 가능
- runtime은 active exact reference와 install/rebuild evidence를 분리
- 보호 output은 inputs 보존·W1 지식 흡수·current deliverable 여부를 구분

## W3-S3 — exact manifest·reference release

W4용 manifest는 다음 세 묶음으로 만든다.

1. exact tracked file·empty directory 처분
2. exact nonprotected ignored cache·local-state·runtime 처분
3. protected output opaque group 처분

보호 exact path는 Git 문서에 쓰지 않고 사용자 승인 요청에서만 opaque ID와 exact directory를 대응해 제시한다. W4 mutation 전 retained Markdown link와 startup/current-state dependency를 0으로 만드는 exact delta도 함께 기록한다.

### W3-S3 gate

- 비보호 exact path와 보호 opaque group 합계가 inventory와 일치
- W4 승인 요청이 대상·목적·복구·비용을 한 번에 판단 가능
- reference release가 history evidence를 active authority로 승격하지 않음
- 승인 전 실제 mutation 0

## W3-S4 — dry-run·전환

처분 전후 예상 inventory를 계산하고 삭제 명령 없이 target existence·경계·symlink/reparse·path containment·Git tracking을 검증한다. W5 self-clean queue는 W4에서 삭제하지 않고 현재 initiative 종료 시점까지 유지한다.

### W3-S4 gate

- target existence·분류·recovery·containment 100%
- duplicate·overlap·parent-before-child 0
- 예상 W4 제거 file·bytes와 잔여 allowlist 수치가 재계산 가능
- Core diff·보호 stage·삭제·이동 0

## Exit·commit·transition gate

- W3-S1~S4가 passed이고 manifest 합계·reference release·승인 view가 완결된다.
- Core·Extension·maintenance·route·strict UTF-8·NUL·후행 공백·links·`git diff --check`가 통과한다.
- task-owned W3 phase/manifest·overall·handoff·W2 transition만 단계 commit한다.
- commit 검증 뒤 W4 exact delete/move 승인을 사용자에게 요청하며 승인 전에는 mutation하지 않는다.

## 복구·중단 조건

- active owner·유일 evidence·복구 경계가 불명확하면 `unresolved`로 남기고 W4에서 제외한다.
- protected exact 이름이나 task fact가 tracked manifest에 들어가면 제거·재작성한다.
- target path가 workspace 밖, symlink/reparse, parent/child 중복이면 manifest를 실패로 되돌린다.
- W4 승인 대상이 commit 뒤 달라지면 해당 target을 실행하지 않고 inventory를 다시 측정한다.

## 실행 결과와 교차검증

### W3-S1 결과
- 매니페스트 생성 전 기준 inventory는 tracked 214, untracked 1, ignored 345, Git union 560, filesystem 560이며 양방향 차이·중복·enumeration error가 0이었다.
- W3 evidence 생성 뒤 재측정한 현재 inventory는 tracked 214, untracked 2, ignored 345, Git union 561, filesystem 561이며 양방향 차이가 0이다.
- W5 완료 tracked allowlist는 180개이고 path-list SHA-256 `9dfb565db0f84176b6dbee6cf7e6e8c9dcf6df05f24e6eb5242c1ec900d71f4f`로 재계산됐다.
- 보호 allowlist는 입력 2개와 출력 4개다. 보호 자식 이름·내용은 tracked evidence에 기록하지 않았다.

### W3-S2 결과
- tracked 처분 후보 28개는 모두 Git 복구 가능하고 canonical/current owner가 아니다.
- Python cache 71개와 Obsidian local state 4개는 재생성·로컬 상태 경계가 명확하다.
- inactive runtime 67개는 active exact reference가 0이지만 byte-identical 복구와 현재 install owner는 없다. 재사용 기반으로 승격하지 않고 향후 active owner 기준 재설치를 복구 경계로 삼았다.
- 보호 출력 201개를 일괄 삭제하지 않았다. 현재 derivative·interchange·사용자 승인 review media·manifest 4개는 보존하고 나머지 197개만 승인 후보로 분리했다.
- Core 회귀 테스트 1개가 역사 보고서를 직접 읽는 dependency를 발견해 exact Core 승인 대상으로 격리했다.

### W3-S3 결과

- exact tracked 후보: 28개, 319,521 bytes, 집계 SHA-256 `fb881b3bcf05b290338116a0d0488dca673522ad4296e456911a0ab6ee8a8ea1`
- 비보호 ignored 후보: 142개, 817,245,394 bytes, 집계 SHA-256 `ee3a0dc1acc0c85e02ca6e1b60c793b6a66cd627282bce045e4727cd54fbd5cb`
- 보호 출력 후보: 197개, 487,736,873 bytes, 집계 SHA-256 `8f2790624d2964a234b9ed0dd4b5dc308934b2c61f93f9aeb3d1aba710d37573`
- 빈 디렉터리 후보: 6개, path-list SHA-256 `e73435f72cfe130afd6e02f6dda6fc4b6c4505da78d5092520ab000ed168f116`
- W4 예상 제거 합계: 367개, 1,305,301,788 bytes. duplicate·보호 겹침·workspace 이탈·reparse point는 모두 0이다.

### W3-S4 결과

- dry-run에서 모든 exact 대상의 존재·tracking·ignored 상태·용량·집계 해시가 매니페스트와 일치했다.
- 빈 디렉터리 5개는 현재 비어 있고 parent 1개는 유일한 empty child 제거 뒤 비는 구조다.
- 권한 있는 전체 gate에서 Core 139개와 Extension 132개 테스트, Node v20.11.1, maintenance 98문서·130링크, ASCII·한국어+공백·공백 경로 clean clone 3종이 모두 통과했다.
- browser-user-session은 clone bootstrap 외부의 의도된 `needs_user`이고 실패가 아니다.
- 첫 sandbox 실행의 Node 상위 경로 EPERM과 124초 timeout은 권한 있는 139.1초 재실행으로 환경 실패임을 분리했고 최종 exit code는 0이다.
- 삭제·이동·Core diff·보호 stage는 0이다.

## 단계·슬라이스 점수

| 슬라이스 | 점수 | 이유 |
|---|---:|---|
| W3-S1 | 5/5 | Git union과 filesystem 561개를 양방향 대조했고 최종 180개 tracked allowlist를 재현 가능한 해시로 고정했다. |
| W3-S2 | 4/5 | 모든 dependency와 복구 경계를 판정했지만 보호 출력 197개와 runtime은 byte-identical 복구가 불가능하므로 승인 전 잔여 위험이 있다. |
| W3-S3 | 5/5 | exact·opaque 경계를 지키면서 367개 파일, 6개 디렉터리, Core 1개 파일 변경을 한 번에 판단 가능한 manifest로 만들었다. |
| W3-S4 | 5/5 | 집계 해시·containment·overlap과 전체 회귀·clean-clone을 독립 재검증했다. |
| W3 전체 | 4.75/5 | 설계·증거·게이트는 완결됐고 감점은 승인 없이는 없앨 수 없는 비가역 복구 위험에 한정된다. |

## Closeout record

- W3-S1: `passed`
- W3-S2: `passed_with_irreversible-recovery-risk`
- W3-S3: `passed`
- W3-S4: `passed`
- W3 exit: `passed`
- W4 transition: `awaiting_exact_core_and_disposition_approval`
