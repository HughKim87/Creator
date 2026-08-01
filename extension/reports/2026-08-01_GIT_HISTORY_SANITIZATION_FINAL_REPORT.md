# Git 이력 정제 및 게시 최종 보고서

- 기준일: 2026-08-01 KST
- 상태: W4 사전 게시 증거 확정; 원격 게시·fresh clone 결과는 W5에서 갱신
- 대상: 로컬 `main`의 미게시 작업 이력과 GitHub `main`
- 목적: 작업별 커밋 추적성을 유지하면서 GitHub 제한을 넘는 작업 output 객체를 게시 이력에서 제거하고, 새 PC에서 검증 가능한 기반을 게시한다.

## 결론

원본 43개 커밋은 순서·작성자·이메일·작성 시각·제목을 43/43 보존해 최신 원격 위에 재적용됐다. 원본 이력은 외부 full+incremental bundle과 로컬 branch로 복구 가능하며, 새 이력에서 `outputs/**`, `inputs/**`, 100MiB 초과 reachable blob은 모두 0이다.

현재 기능·문서 tree와 새 tree의 유일한 차이는 원격에서 추가된 README 표현 3곳이다. Core·Extension·maintenance·Node·clone-conformance는 source와 독립 clean clone에서 모두 통과했다.

## 범위와 보존 경계

| 항목 | 실제 처리 |
|---|---|
| 정제 대상 | 기존 43개 커밋의 `outputs/**` patch |
| 제외 대상 | `inputs/**` 내용, ignored runtime, 새 기능 변경, LFS, squash, force push |
| 원본 로컬 tip | `da5c725025c2629404b12c44fde859e7935c31e7` |
| 원격 기준 | `44e3059be53eed7b190451d9bb9934add48f9213` |
| 정제된 원본 대응 tip | `ffdcfb7bad8fab460f10d5d64119466d5ef64a6d` |
| 복구 branch | `codex/archive-pre-sanitize-20260801`과 완료 시 보존할 원본 `main` branch |
| 작업 branch | `codex/history-sanitization-20260801` |

## 외부 복구 자료

| 자료 | 크기 | SHA-256 | 검증 |
|---|---:|---|---|
| full bundle `youtube_channel-pre-sanitize-20260801-997ab157.bundle` | 383,824,883 bytes | `F13A2552E1690924A4E29F6DDBB8A6DCE14C0CB3120DFDDE927A74947CA7DD7B` | verify, clone, HEAD·213커밋 일치 |
| incremental bundle `youtube_channel-pre-sanitize-increment-da5c725.bundle` | 1,427 bytes | `92E8C9B3B809E2B8142745BC98CBA7D5F3BAFD288F62ED31D835B3C5EE0817FC` | prerequisite 적용, tip `da5c725`, 214커밋 복구 |
| `commit-map-20260801.tsv` | 6,891 bytes·43행 | `240C0D5ED13B47AAB04D17DE754D219998D0939F8FC0694725D9AE6FB91BD1C8` | 각 행 작성 시 author date·subject 대응 확인 |

저장 위치는 프로젝트 외부 `Backups/김실버유튜브/2026-08-01/`이며 프로젝트 실행은 이 자료에 의존하지 않는다.

## 개선 수치

| 지표 | 전 | 후 | 효과 |
|---|---:|---:|---:|
| 논리 커밋 대응 | 43 | 43 | 100% 보존 |
| output 고유 경로 | 201 | 0 | 100% 제거 |
| input 경로 접근·이력 변화 | 0 | 0 | 보호 경계 유지 |
| 100MiB 초과 reachable blob | 3 | 0 | GitHub 차단 원인 100% 제거 |
| 최대 차단 blob | 124,943,092 bytes | 최대 reachable blob 35,915,880 bytes | 최대 크기 71.3% 감소 |
| merge commit | 0 | 0 | 선형 추적성 유지 |
| 재적용 충돌 | 해당 없음 | 0 | 자동 적용 성공 |
| 최종 tree 차이 | 기준 | README 1파일·표현 3곳 | 원격 최신 의도만 병합 |

서로 범위가 다른 전체 객체 byte 합계는 개선율로 사용하지 않았다.

## 단계별 결과와 점수

| 단계 | 목표 | 실제 결과 | 점수 | 이유 |
|---|---|---|---:|---|
| W0 | 승인·금지·게이트 설계 고정 | 설계·handoff 커밋 `997ab15` | 10/10 | 범위와 삭제 금지를 선행 고정 |
| W1 | 원본 복구 경계 | full+incremental bundle과 복구 clone 성공 | 10/10 | 원본 43개 tip까지 외부 복구 가능 |
| W2 | output 제외 커밋별 재적용 | 43/43, conflict 0, merge 0 | 10/10 | 커밋 메타데이터 완전 대응 |
| W3 | 통합·독립 검증 | source와 no-local clean clone 전체 gate pass | 9/10 | 최초 설계 route 오류를 발견·수정 후 재검증 |
| W4 | 보고서·fast-forward 게시 | 사전 게시 보고서·게이트 준비 완료 | 진행 중 | push 결과는 실행 후 확정 |
| W5 | 원격 fresh clone·로컬 종료 | 미실행 | 대기 | 원격 게시 후 측정 |

## Slice 교차 검증

| Slice | 증거 | 결과 | 점수 |
|---|---|---|---:|
| 커밋 대응 | old/new log 직접 비교·외부 mapping | 43/43 일치 | 10/10 |
| 보호 경로 | log path와 HEAD tree 별도 측정 | output 0, input 0 | 10/10 |
| 객체 크기 | 정제 HEAD reachable object 전수 검사 | 2,355 blobs, 100MiB 초과 0 | 10/10 |
| 최종 tree | 원본 main과 정제 branch 직접 diff | README 3개 표현만 차이 | 10/10 |
| 프로젝트 gate | `python -B scripts/verify.py` | Core 141, Extension 140, maintenance·Node·clone pass | 10/10 |
| 독립 재현 | `--no-local --single-branch` clean clone | HEAD 일치·전체 gate pass·status clean | 10/10 |
| 설계 라우팅 | targeted 6 tests와 전체 gate | 수정 후 전부 pass | 9/10 |

## 발견한 실패와 수정

1. 최초 전체 gate는 handoff의 활성 설계를 Markdown link로 기록하고 overall owner를 두지 않아 실패했다. 프로젝트 테스트가 요구하는 backtick route와 W0~W5 overall/phase 구조로 수정했고 targeted 6/6 및 전체 gate로 재검증했다.
2. 두 읽기 검증에서 축약 SHA를 임의 확장한 예상값을 사용해 명령이 mutation 전에 중단됐다. 이후 모든 SHA 비교를 `git rev-parse` 실측값으로 바꿨으며 branch·clone·bundle 손실은 0이다.
3. `git bundle verify`의 성공 문구가 stderr에 출력되어 PowerShell이 오류 레코드로 표시했지만 exit code는 0이었다. exit code와 실제 recovery clone으로 성공 여부를 교차 판정했다.

## 규칙 처분

| 작업 중 규칙 | 처분 | 이유 |
|---|---|---|
| 완료 전 기존 파일·branch 삭제 금지 | project rule 변경 없음 | 현재 작업 전용 사용자 경계 |
| bundle+새 커밋+SHA mapping 이중 추적 | project rule 변경 없음 | 현재 이력 이관의 구체적 복구 방식 |
| overall·W0~W5 route 준수 | 기존 규칙·테스트 재사용 | 새 규칙이 아니라 기존 staged-design 계약 |
| push 전 live 원격 SHA 확인 | 기존 version-control 절차 적용 | 현재 원격값은 task fact |

새 Core·Extension 규칙은 추가하거나 수정하지 않았다.

## 남은 W4·W5 게이트

- 원격 `main`이 여전히 `44e3059...`인지 live 확인한다.
- 정제 branch를 force 없이 `main`에 push한다.
- 원격 fresh clone에서 전체 gate를 실행한다.
- 실제 원격 SHA·검증 결과를 이 보고서에 반영해 최종 commit·push한다.
- 로컬 main을 게시 tip에 정렬하고 worktree clean·기존 파일 삭제 0·로컬 branch 삭제 0을 확인한다.
