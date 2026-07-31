# W0 프로젝트 전역 inventory·분류

- 문서 분류: `phase-design`
- phase ID: `W0`
- lifecycle: `passed`
- 결과: 저장소 작업트리의 모든 항목을 Git 상태와 무관하게 안전하게 inventory하고, provenance·role·owner·reference·rebuild/recovery·재사용 가능성에 따라 1차 분류한다.
- 독자: W0 실행 agent와 프로젝트 전역 정리를 검토하는 사용자
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- optional evidence owner: `extension/work/repository-consolidation/W0_FILE_CLASSIFICATION.md` — 생성 완료, startup-required 아님, 보호 exact 이름·내용과 secrets 금지, W4 뒤 Git history로 회수하고 W5 정리 후보
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; 이 단계는 삭제·이동·Core mutation·보호 데이터 stage·commit을 승인하지 않는다.
- 첫 다음 행동: W0-S1에서 entry dirty baseline을 exact path로 고정한 뒤 Git inventory와 filesystem metadata inventory의 수집 명령·포함/제외 규칙을 dry run한다.

## Entry gate

- 사용자는 정리 범위를 ignored 파일로 한정하지 않고 tracked·untracked·ignored, 백룸·개선 산출물, `outputs/`, `extension/data/`를 포함한 작업트리 전체로 교정했다.
- 기존 M4는 문서 22개 중심의 좁은 범위이므로 `invalidated`이며 삭제 승인으로 사용하지 않는다.
- 기준 branch는 `main`, 기준 HEAD는 `11a6031`, `origin/main` 대비 20 commits ahead다.
- entry dirty baseline은 이전 감사의 task-owned 6문서다: `SESSION_HANDOFF.md`, 기존 최종 보고서, M1·M2·M3·M4 phase 문서. 이 변경은 restore하지 않고 새 설계 변경과 구분해 보존한다.
- W0 시작 시 overall·handoff·이 phase가 같은 목표·활성 단계·첫 행동을 가리켜야 한다.

## 포함 범위

- Git tracked·modified·deleted·untracked·ignored 항목
- filesystem에는 있으나 Git inventory에 나타나지 않는 file·directory
- 문서·보고·계획·코드·테스트·schema·example·runtime·cache·temp·render·data·입출력 파생물
- 백룸 조사·실험과 과거 개선 단계가 생성한 항목
- root 아래 모든 `inputs/outputs` path segment와 `extension/data/`의 최소 metadata

## 제외·보호 범위

- `.git/**` object 내부와 저장소 밖 경로
- secret·credential·cookie·token·browser profile 내용
- W0에서의 삭제·이동·rename·overwrite·dependency 설치·외부 write
- W0에서의 지식 흡수·규칙 변경·Core mutation
- 보호 파일의 content·exact filename을 reusable report·classification evidence·Git에 복제하는 행위

보호 path는 현재 사용자 지정 전역 정리 목적에 필요한 path-level inventory 범위에서만 다룬다. persistent evidence에는 aggregate count·bytes·opaque item ID·분류만 기록하고, exact content 검토와 처분은 후속 단계에서 다시 exact 목적·승인을 확인한다.

## 분류 체계

각 항목은 다음 필드를 갖는다.

| field | 값 |
|---|---|
| Git state | `tracked-clean / tracked-modified / tracked-deleted / untracked / ignored / non-git` |
| provenance | `canonical / user-source / user-deliverable / backroom / improvement / runtime / generated / unknown` |
| role | `policy / contract / workflow / code / test / schema / evidence / state / data / derivative / cache / tool / unknown` |
| reuse | `canonical-retain / reusable-existing-owner / reusable-new-owner-review / protected-user-artifact / regenerable-disposable / historical-git / disposition-candidate / unresolved` |
| safety | `normal / protected-metadata / sensitive-unread / external-recovery-required` |

`reusable`은 “내용이 있음”이 아니라 이후 반복 workflow의 조건·행동·예외·검증, 재현 가능한 contract/schema/test, 또는 검증된 실패 예방을 강화할 때만 부여한다.

## Slice gate

W0-S1~S4는 각 slice의 직접 측정·미해결 항목·금지 경계·gate 결과를 W0 evidence에 기록한 뒤에만 다음 slice로 전환한다.

## W0-S1 — baseline·safe census

다음 세 inventory를 독립 수집한다.

1. Git tracked와 현재 diff 상태
2. Git untracked·ignored 상태
3. root filesystem metadata(path class, file/dir, bytes, modified time)에서 `.git/**`만 제외한 집계

protected·sensitive 후보는 content를 열지 않는다. 경로 출력이 사용자 자료를 노출할 수 있으면 persistent evidence에는 opaque ID와 aggregate만 남긴다.

### W0-S1 gate

- 세 inventory의 포함·제외 규칙과 재현 명령이 기록된다.
- total file/dir·bytes가 Git state와 top-level owner별로 대조된다.
- entry dirty 6문서가 사용자/task-owned baseline으로 분리된다.
- 접근 실패·긴 경로·junction·symlink·permission·secret 후보는 숨기지 않고 `unresolved`로 기록된다.

## W0-S2 — provenance·role grouping

경로·Git history·router·build/test/config 참조를 먼저 사용해 provenance와 role을 분류한다. 내용 읽기가 필요한 경우 exact 질문과 최소 파일을 W0 evidence에 기록하되 W1 전에는 재사용 지식을 흡수하지 않는다.

### W0-S2 gate

- 모든 inventory 항목에 Git state·provenance·role·safety가 있다.
- `unknown`은 확인 질문·필요 evidence·다음 단계가 있다.
- ignored라는 이유만으로 disposable, tracked라는 이유만으로 retain 판정을 하지 않는다.

## W0-S3 — owner·reference·rebuild/recovery

각 그룹에 현재 owner, inbound reference, runtime 필요성, rebuild command 또는 복구 경계를 연결한다. tracked 항목은 Git recovery commit을, untracked·보호 항목은 유지 또는 사용자 지정 외부 복구 필요성을 기록한다.

### W0-S3 gate

- 각 그룹에 owner 또는 `owner-missing` 사유가 있다.
- 재생성 가능 판정은 실제 rebuild route·input·verification이 있을 때만 사용한다.
- 유일한 승인·상태·source lineage·사용자 원본은 disposition 후보가 아니다.
- reference scan은 실행 가능한 link/import/config와 역사 code-span을 구분한다.

## W0-S4 — 1차 reuse·disposition 분류

분류 체계의 reuse 값 하나를 모든 항목에 부여한다. protected exact item은 persistent evidence에서 식별 정보를 최소화하고 aggregate 분류를 사용한다. W1에는 재사용 후보만, W3에는 처분 후보만 넘긴다.

### W0-S4 gate

- inventory coverage 100%이며 중복 행과 누락이 0이다.
- `unresolved`는 blocker·위험·다음 확인 조건이 있어 자동 처분되지 않는다.
- 재사용 후보에는 evidence source와 예상 canonical owner가 있다.
- 처분 후보에는 추출 선행 조건·reference·rebuild/recovery·필요 승인 종류가 있다.
- 실제 삭제·이동·흡수·Core 변경·보호 stage는 0이다.

## Evidence artifact gate

전체 결과가 phase read budget에 맞지 않을 때만 `W0_FILE_CLASSIFICATION.md`를 만든다.

- owner/reader: W0 phase / W1~W4 실행 agent
- 내용: 비보호 exact path와 위 분류 필드, 보호 항목 aggregate·opaque ID
- 금지: 파일 content 복제, secret, 보호 exact filename, raw 로그
- retention: W4 disposition 검증까지, W5에서 Git history 복구를 확인한 뒤 정리 후보
- verification: inventory total reconciliation, duplicate path 0, strict UTF-8, NUL 0, links, scoped diff

## Exit·commit·transition gate

- W0-S1~S4가 모두 통과하고 W1 입력인 재사용 후보 queue가 owner별로 고정된다.
- 별도 evidence를 만들었다면 startup route에 포함하지 않고 expiry가 기록된다.
- Core·Extension 회귀, maintenance, active design budget, protected staged count 0, `git diff --check`가 통과한다.
- phase exit 뒤 현재 대화에서 요청된 단계 commit 원칙에 따라 task-owned maintained paths만 commit한다. 보호 path·runtime·inventory raw output·unrelated baseline은 stage하지 않고 push하지 않는다.
- transition review에서 문서 수 증가·중복 owner·미해결 위험을 감사한 뒤에만 W1 phase-design을 만들고 활성화한다.

## 복구·중단 조건

- inventory 방법 사이의 total이 맞지 않으면 분류를 진행하지 않고 차이 집합과 원인을 먼저 해결한다.
- junction·symlink가 root 밖으로 나가면 따라가지 않는다.
- secret 또는 보호 내용이 출력·persistent evidence에 들어가면 성공으로 보고하지 않고 해당 산출물을 폐기 가능한 방식으로 격리한 뒤 사용자에게 보고한다.
- exact 삭제·이동, 보호 원본 mutation, Core 변경이 필요해지면 W0를 멈추고 해당 권한을 별도로 확인한다.

## Closeout record

- W0-S1: `passed` — tracked 209·untracked 1·ignored 345와 filesystem 555/555 일치, 오류·reparse·중복 0
- W0-S2: `passed` — 18개 상호 배타 그룹으로 provenance·role·safety 100% 분류
- W0-S3: `passed` — owner·reference·rebuild/recovery 연결, runtime 67·protected outputs 201은 다음 조건과 함께 unresolved
- W0-S4: `passed` — reuse/disposition 합계 555, W1·W3 queue 분리
- W0 exit: `passed`
- W1 transition: `pending_phase_commit`
