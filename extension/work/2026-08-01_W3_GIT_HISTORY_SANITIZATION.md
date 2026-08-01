# W3 Git 이력 정제 통합 검증

- 문서 분류: `phase-design`
- phase ID: `W3`
- lifecycle: `in_progress`
- 독자: 현재 검증을 실행·재개하는 프로젝트 에이전트
- 권위: 최신 사용자 지시, `PROJECT_RULES.md`, 전체 설계
- optional evidence owner: [초기 상세 설계 근거](2026-08-01_GIT_HISTORY_SANITIZATION.md), startup-required 아님

## 결과

정제 branch가 원본의 논리 커밋과 현재 최종 tree를 의도대로 보존하고 GitHub·프로젝트·clean clone 게이트를 모두 통과함을 직접 측정한다.

## Entry gate

- W0 설계 커밋과 W1 bundle 복구 gate가 통과했다.
- W2는 원본 43커밋을 충돌·merge 없이 재적용했고 메타데이터 순서가 43/43 일치했다.
- 사용자가 기존 `core/**` 34개 경로의 최종 상태 재적용을 명시 승인했다.
- 원본 workspace, 보존 branch, bundle, recovery clone은 유지 중이다.

## 포함·제외

- 포함: reachable blob 크기, commit/path/tree 대응, 문서 라우팅, 전체 verify, local clean clone.
- 제외: protected data 내용 접근, 새 기능·규칙 변경, 기존 파일·branch·복구 자료 삭제, push.

## 실행 slices

1. `W3-S1`: commit metadata·output/input path·final tree·reachable blob을 재측정한다.
2. `W3-S2`: staged-design 라우팅과 문서 예산을 검증한다.
3. `W3-S3`: `python -B scripts/verify.py`를 정제 worktree에서 실행한다.
4. `W3-S4`: 별도 local clean clone에서 같은 전체 gate를 실행한다.

## Slice gates

- `W3-S1`: 43/43 대응, output path 0, input 접근 0, 100MiB 초과 blob 0, 허용된 README 차이만 존재.
- `W3-S2`: handoff가 distinct overall·W3 phase를 backtick 경로로 route하고 설계 예산·task-rule owner 수를 지킨다.
- `W3-S3`: core·extension·maintenance·Node·clone-conformance가 성공한다.
- `W3-S4`: clean clone HEAD·검증 결과가 source와 일치한다.

## Exit gate

- 모든 slice gate가 pass이고 source·작업 worktree가 clean이다.
- unverified claim, protected staged path, 100MiB 초과 reachable blob, active blocker가 0이다.
- W4 전환 전에 task-rule을 동결하고 검증 증거를 현재 owner에 압축한다.

## 복구·중단

- 라우팅 또는 전체 gate 실패 시 실패 원인과 첫 재개 행동을 handoff에 남기고 push하지 않는다.
- 원격 SHA가 바뀌거나 비-fast-forward가 필요하면 원본·작업 branch·bundle을 그대로 두고 중단한다.
- 기존 파일·branch·복구 자료는 W5 완료 전 삭제하지 않는다.

## Task rules (`active`)

| trigger | extracted rule | evidence | target owner | disposition |
|---|---|---|---|---|
| 완료 전 정리 | 기존 파일·로컬 branch를 삭제하지 않는다 | 사용자 지시 | 현재 phase | `reject`: 작업 전용 경계 |
| 이력 추적성 | 원본 SHA는 bundle, 논리 커밋은 새 이력, 대응은 mapping으로 검증한다 | 43/43 재적용 | 현재 phase | `reject`: 현재 이관 사실 |
| 활성 설계 route | overall과 W0~W5 phase route 형식을 유지한다 | staged routing test | 기존 document/staged rules | `reject`: 기존 계약 중복 |

- 첫 다음 행동: staged-design 라우팅 단위 테스트를 다시 실행한 뒤 전체 gate를 재실행한다.
