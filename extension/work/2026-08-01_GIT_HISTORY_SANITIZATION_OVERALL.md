# Git 이력 정제 및 게시 전체 설계

- 문서 분류: `overall-design`
- 결과: 작업별 커밋 경계를 보존하면서 GitHub 제한을 넘는 output 객체를 게시 이력에서 제외하고, 검증된 `main`을 fast-forward 게시한다.
- 독자: 현재 작업을 실행·재개하는 프로젝트 에이전트와 사용자
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`
- 활성 단계: [W3 통합 검증](2026-08-01_W3_GIT_HISTORY_SANITIZATION.md)

## 불변 조건

- 완료 게이트 전에는 기존 파일·로컬 branch·원본 객체를 삭제하거나 이동하지 않는다.
- `inputs/**`는 접근·분석·stage하지 않고 `outputs/**` 이력만 정제한다.
- 원본은 로컬 보존 branch와 verified 외부 bundle로 복구 가능해야 한다.
- 원본 커밋의 순서·작성자·이메일·작성 시각·제목을 보존하고 old→new SHA를 대응시킨다.
- force push, LFS 전환, squash, 원격 archive branch 게시를 금지한다.

## 단계 지도

| 단계 | 한 줄 결과 |
|---|---|
| W0 설계 고정 | 승인·산출물·금지·게이트를 설계 커밋으로 고정한다. |
| W1 원본 보존 | 보존 branch와 bundle verify·복구 clone을 통과한다. |
| W2 이력 정제 | 최신 원격 위에 output을 제외한 원본 커밋을 순서대로 재적용한다. |
| W3 통합 검증 | 커밋 대응·blob·보호 경로·전체·clean clone gate를 통과한다. |
| W4 게시 | 최종보고서를 준비하고 정제 이력을 `main`에 fast-forward 게시한다. |
| W5 종료 | 원격 fresh clone과 로컬 정렬·clean·보존 경계를 확정한다. |

## 범위 경계

- 포함: 설계·handoff, 외부 bundle·SHA 대응표, 정제 branch, 전체 검증, fast-forward push, fresh clone, 최종보고서.
- 제외: 새로운 Core 의미 변경, protected data 내용, ignored runtime 변경, 기존 파일·branch 삭제.

## 완료 조건

W0~W5 게이트가 모두 통과하고 로컬·원격 `main`이 일치하며 worktree가 clean이고, 외부 복구 자료와 최종보고서가 실제 결과를 설명해야 한다.
