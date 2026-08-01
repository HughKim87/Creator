# W4 Git 이력 정제 게시

- 문서 분류: `phase-design`
- phase ID: `W4`
- lifecycle: `in_progress`
- 독자: 게시를 실행·재개하는 프로젝트 에이전트
- 권위: 최신 사용자 지시, `PROJECT_RULES.md`, 전체 설계
- optional evidence owner: [초기 상세 설계 근거](2026-08-01_GIT_HISTORY_SANITIZATION.md), startup-required 아님

## 결과

검증된 정제 이력과 사전 게시 증거를 최종보고서 초안으로 고정하고, 원격 `main`이 기준 SHA일 때 force 없이 fast-forward 게시한다.

## Entry gate

- W0~W3가 통과했고 정제 branch와 independent clean clone이 clean이다.
- 원본 보존 branch, verified bundle, 43행 SHA 대응표가 유지 중이다.
- reachable 100MiB 초과 blob과 protected tracked path는 0이다.
- 사용자가 `main` push를 포함한 설계 실행을 승인했다.

## 포함·제외

- 포함: 최종보고서 초안, 문서·객체 재검증, 원격 SHA 확인, fast-forward push, 원격 HEAD 확인.
- 제외: force push, 원격 archive branch, PR, LFS, 기존 파일·로컬 branch·scratch 삭제, 로컬 main 정렬.

## 실행 slices

1. `W4-S1`: 최종보고서 초안에 설계·복구·재적용·검증 수치와 미완료 원격 항목을 구분해 기록한다.
2. `W4-S2`: task-rule을 동결·처분하고 보고서·handoff·설계 라우팅을 검증해 커밋한다.
3. `W4-S3`: 원격 `main=44e3059...`와 fast-forward 조건을 다시 확인한다.
4. `W4-S4`: 정제 branch를 원격 `main`에 일반 push하고 원격 HEAD를 확인한다.

## Slice gates

- `W4-S1`: 직접 측정과 미검증 주장이 구분되고 bundle·mapping 해시와 테스트 수치가 일치한다.
- `W4-S2`: strict UTF-8, NUL 0, trailing whitespace 0, protected staged path 0, 전체 gate pass가 유지된다.
- `W4-S3`: live 원격 SHA가 기준과 같고 push가 fast-forward다.
- `W4-S4`: push exit 0, 원격 HEAD가 게시 commit과 일치하고 force option 사용 0이다.

## Exit gate

- 최종보고서 초안 commit이 정제 branch에 있고 원격 `main` 첫 게시가 성공한다.
- 원본·복구 자료·로컬 branch·scratch는 삭제되지 않는다.
- W5가 원격 fresh clone과 최종 보고서 증거 갱신을 인계받는다.

## 복구·중단

- 원격 SHA 변화 또는 non-fast-forward가 확인되면 push하지 않고 fetch 후 재설계를 요구한다.
- push 실패 시 원본과 정제 branch를 유지하고 인증·용량·정책 오류를 구분해 기록한다.
- 기존 파일·branch·복구 자료는 W5 완료 전 삭제하지 않는다.

## Task-rule disposition

| trigger | extracted rule | evidence | target owner | disposition |
|---|---|---|---|---|
| 게시 직전 동적 상태 | 원격 SHA를 live 재확인하고 일치할 때만 fast-forward push한다 | 현재 원격 기준 | 현재 phase | `reject`: 작업 전용 상태 |
| 보고서 정확성 | push 전 수치는 완료, 원격 fresh clone은 미완료로 구분한다 | 사용자 사실 기반 요구 | 현재 phase | `reject`: 현재 보고 경계 |

- 첫 다음 행동: live 원격 SHA와 fast-forward 조건을 확인한 뒤 정제 branch를 원격 `main`에 push한다.
