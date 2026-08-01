# Git 이력 정제 및 게시 설계

- 분류: `phase-design`
- Phase ID: `GHP1`
- 상태: `in_progress`
- 독자: 현재 작업을 실행·재개·검증하는 프로젝트 에이전트와 사용자
- 권위: 최신 사용자 지시, `PROJECT_RULES.md`, `core/rules/version-control.md`

## 결과

현재 로컬의 작업별 커밋 경계를 유지하면서 GitHub 제한을 넘는 `outputs/**` 객체만 게시 이력에서 제외하고, 최신 원격 `main` 위에 fast-forward 가능한 이력을 만든다. 원본 이력은 검증된 외부 Git bundle과 로컬 보존 브랜치로 복구 가능하게 남기며, 완료된 프로젝트는 clean 상태여야 한다.

## 기준선과 승인

- 기준선: 로컬 `main=6a7b271f25567d5c6caba5320bb66a43aff96814`, `origin/main=44e3059be53eed7b190451d9bb9934add48f9213`, ahead 41 / behind 1, tracked 변경 0.
- 직접 측정: 미푸시 이력은 선형 41커밋·merge 0·`outputs/**` 고유 경로 201개·`inputs/**` 경로 0개다.
- 승인: 사용자는 설계 작성, 순차 실행, 필요한 권한, 단계 게이트, 커밋, 최종보고서, 승인된 `main` push를 요청했다.
- Core 승인: 사용자는 2026-08-01 현재 이력의 `core/**` 34개 경로를 최종 내용 그대로 새 SHA에 재적용하는 것을 명시 승인했다.
- 외부 효과: 원격 SHA가 기준선과 같을 때만 `main` fast-forward push를 허용한다. force push와 원격 보존 브랜치 게시를 금지한다.

## 산출물 예산

| 산출물 | 위치 | 역할 | 종료 처분 |
|---|---|---|---|
| 활성 설계·task-rule | 이 파일 | 실행·게이트 단일 owner | 기술 게이트 후 최종보고서로 전환 |
| 현재 상태 | `SESSION_HANDOFF.md` | 현재 slice·blocker·첫 다음 행동 | 완료 시 idle로 축약 |
| 최종보고서 | `extension/reports/2026-08-01_GIT_HISTORY_SANITIZATION_FINAL_REPORT.md` | 사용자 요청 최종 증거 | 유지 |
| 원본 bundle | 저장소 외부 `Backups/김실버유튜브/2026-08-01/` | 원래 SHA·객체 복구 | 유지, 프로젝트가 의존하지 않음 |
| SHA 대응표 | bundle과 같은 외부 디렉터리 | 원본→게시 커밋 추적 | 유지 |
| scratch | `C:/Users/Hugh/AppData/Local/Temp/youtube-history-sanitize-20260801` | 패치·임시 clone | 종료 게이트 후에만 정리 |

프로젝트 내부에는 별도 분석 파일·백업·단계별 보고서를 만들지 않는다.

## 포함·제외 범위

- 포함: 설계·handoff, 보존 branch·bundle, 42개 이상 커밋의 순서별 재적용, 메타데이터 대응, 객체·경로·전체 검증, fast-forward push, fresh clone 검증, 최종보고서.
- 정제 경로: 커밋 patch에서 `outputs/**`만 제외한다.
- 제외: `inputs/**` 내용 접근·변경, 현재 ignored runtime 삭제·변경, Core 변경, LFS 도입, 과거 커밋 squash, force push, 원격 archive branch 생성, 기존 파일·로컬 branch 삭제.

## 불변 조건

1. 전체 작업이 검증되기 전에는 기존 파일·원본 객체·로컬 branch를 삭제하거나 이동하지 않는다.
2. 원본 `main` tip을 보존 branch가 가리키고 verified bundle clone이 성공하기 전에는 이력 재적용을 시작하지 않는다.
3. 보호 자료 내용은 읽지 않고 Git path·object metadata만 사용한다. `inputs/**`는 열거 대상에서도 제외한다.
4. 새 이력은 커밋 수·순서·작성자·이메일·작성 시각·제목을 보존한다. SHA 변경은 old→new 대응표로 추적한다.
5. 원격이 변경되거나 push가 fast-forward가 아니면 중단하고 원본과 작업 branch를 그대로 둔다.

## 순차 실행과 게이트

### S0 — 설계 고정

- 실행: 이 설계와 current-state owner를 연결하고 문서 무결성·예산을 검증한 뒤 설계 커밋을 만든다.
- 게이트 `GHP1-S0`: UTF-8·NUL 0·trailing whitespace 0, 설계 160줄/12,000자 이내, active owner 1개, protected staged path 0.

### S1 — 원본 복구 경계

- 실행: `codex/archive-pre-sanitize-20260801`을 원본 tip에 만들고 외부 bundle을 생성한다.
- 게이트 `GHP1-S1`: bundle verify, bundle clone, 원본 HEAD와 커밋 수 일치, bundle SHA-256 기록. 실패 시 정제 금지.

### S2 — 커밋별 이력 정제

- 실행: `codex/history-sanitization-20260801`을 최신 `origin/main`에서 만들고, 원본 범위를 `outputs/**` 제외 patch로 순서대로 적용한다.
- 게이트 `GHP1-S2`: 모든 patch 적용, conflict 0 또는 명시 해결, 원본과 새 커밋 수 일치, merge 0, 메타데이터 순서 일치, 새 이력의 output path 0.

### S3 — 통합 검증

- 실행: blob 크기, 최종 tree, 문서, 전체 프로젝트 gate와 local clean clone gate를 검사한다.
- 게이트 `GHP1-S3`: 100MiB 초과 reachable blob 0, protected tracked path 0, 허용된 최종 tree 차이만 존재, `python -B scripts/verify.py` 성공, source worktree clean.

### S4 — 게시 및 원격 검증

- 실행: task-rule을 동결·처분하고 이 파일을 최종보고서 owner로 전환한다. 원격 SHA를 재확인한 뒤 정제 branch를 `main`에 fast-forward push하고 fresh clone을 검증한다.
- 게이트 `GHP1-S4`: force push 0, 원격 HEAD 일치, fresh clone 전체 gate 성공, 보고서 증거 갱신·커밋·최종 fast-forward push 성공.

### S5 — 종료

- 실행: 로컬 `main`을 검증된 게시 tip에 정렬하고 handoff를 idle로 축약한다. 원본 보존 branch와 bundle은 유지한다.
- 게이트 `GHP1-S5`: 로컬/원격 main 일치, worktree clean, 기존 파일 삭제 0, 로컬 branch 삭제 0, scratch만 정확히 제거, active task-rule 0.

## 중단·복구 조건

- bundle 검증 실패, 원격 SHA 변화, commit 대응 누락, 100MiB 초과 객체 잔존, protected path stage, 전체 gate 실패, 비-fast-forward push 요구가 발생하면 즉시 중단한다.
- 중단 시 원본 `main`, 보존 branch, bundle, 작업 branch, scratch를 유지하고 `SESSION_HANDOFF.md`에 정확한 blocker와 첫 재개 행동을 기록한다.

## Task rules (`active`)

| trigger | extracted rule | evidence | target owner | disposition |
|---|---|---|---|---|
| 이력 정제 실행 | 완료 전 기존 파일·로컬 branch를 삭제하지 않는다 | 현재 사용자 지시 | 현재 설계 | `reject`: 이 작업 전용 보존 경계 |
| 커밋 추적성 우려 | 원본 SHA는 bundle, 논리 커밋은 새 이력, 대응은 mapping으로 검증한다 | 41커밋 임시 재적용 실험 | 현재 설계 | `reject`: 현재 저장소 이관 사실 |
| push 제한 해결 | 삭제 대상 output을 LFS로 재보존하지 않고 output patch만 제외한다 | 3개 100MiB 초과 blob 측정 | 현재 설계 | `reject`: 현재 이력 정제 선택 |

## 첫 다음 행동

`GHP1-S2` 작업 worktree를 만들고 `outputs/**`를 제외한 원본 커밋을 최신 `origin/main` 위에 순서대로 재적용한다.
