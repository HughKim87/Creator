# W5 Git 이력 정제 종료

- 문서 분류: `phase-design`
- phase ID: `W5`
- lifecycle: `in_progress`
- 독자: 원격·보고서·로컬 종료를 실행·재개하는 프로젝트 에이전트
- 권위: 최신 사용자 지시, `PROJECT_RULES.md`, 전체 설계
- optional evidence owner: [최종보고서 초안](../reports/2026-08-01_GIT_HISTORY_SANITIZATION_FINAL_REPORT.md), startup-required 아님

## 결과

canonical 원격의 fresh clone을 검증하고 최종보고서를 실제 원격 결과로 갱신한 뒤, active 설계를 종료하고 로컬을 게시 상태와 일치시키며 clean 상태를 확정한다.

## Entry gate

- W0~W4가 통과했고 첫 원격 `main` push가 force 없이 성공했다.
- canonical 원격과 게시 HEAD `efe4165...`가 일치한다.
- 원본 branch·bundle set·mapping·scratch가 유지 중이다.
- 기존 파일·로컬 branch 삭제는 0이다.

## 포함·제외

- 포함: canonical remote fresh clone, 전체 gate, 보고서 갱신, active 설계 retirement, 최종 commit·push, 로컬 main 정렬, task scratch 정리.
- 제외: 원본 보존 branch·bundle·mapping 삭제, protected data, ignored runtime 변경, force push, 원격 보존 branch.

## 실행 slices

1. `W5-S1`: canonical 원격 `main`을 새 경로에 single-branch clone하고 HEAD·object·전체 gate를 검증한다.
2. `W5-S2`: 최종보고서에 원격 결과·W4/W5 점수·최종 SHA를 반영한다.
3. `W5-S3`: task-rule을 처분하고 handoff를 idle로 전환하며 현재 작업 설계 문서를 closeout commit에서 제거한다.
4. `W5-S4`: 최종 commit을 `main`에 fast-forward push하고 원격 HEAD·보고서 hash를 검증한다.
5. `W5-S5`: 로컬 원본 main을 보존명으로 남기고 게시 branch를 local main으로 정렬한 뒤 scratch만 제거한다.

## Slice gates

- `W5-S1`: remote/source HEAD 일치, full verify pass, status clean, 100MiB 초과 blob·protected tracked path 0.
- `W5-S2`: 보고서의 수치·SHA·성공/실패·미검증 상태가 실측과 일치한다.
- `W5-S3`: active overall·phase·task-rule 0, handoff idle, 삭제 대상은 현재 작업 설계 문서뿐이다.
- `W5-S4`: force 0, remote HEAD 일치, report SHA-256 일치.
- `W5-S5`: local/remote main 일치, 원본 보존 branch 존재, 기존 local branch 삭제 0, worktree clean, scratch 0.

## Exit gate

- W0~W5 목표와 slice gate가 모두 pass하고 최종보고서가 현재 tree의 단일 상세 owner다.
- 프로젝트 내부 active 설계·task-rule·scratch residue가 0이다.
- 원본 복구 branch·bundle set·mapping은 보존되고 프로젝트가 외부 백업에 의존하지 않는다.

## 복구·중단

- remote fresh clone 또는 전체 gate가 실패하면 설계 문서를 제거하지 않고 W5 blocker를 기록한다.
- 최종 push가 실패하면 로컬 commit·원본 branch·remote 첫 게시 상태를 유지하고 원인을 구분한다.
- local branch 정렬은 원격 최종 검증 후에만 실행하며 원본 branch를 삭제하지 않는다.

## Task rules (`active`)

| trigger | extracted rule | evidence | target owner | disposition |
|---|---|---|---|---|
| canonical remote 전환 | GitHub가 안내한 새 URL과 live HEAD를 확인해 clone·push 기준으로 사용한다 | 첫 push 응답·ls-remote | 현재 phase | `reject`: 현재 저장소 상태 |
| closeout 정리 | 원격 검증 후 현재 작업 설계와 scratch만 마지막 checkpoint에서 정리한다 | 사용자 삭제 금지·문서 lifecycle | 기존 document/file-cleanup rules | `reject`: 기존 계약 적용 |

- 첫 다음 행동: canonical 원격 `main` fresh clone에서 전체 gate를 실행한다.
