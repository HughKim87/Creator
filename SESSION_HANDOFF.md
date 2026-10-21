# Creator 현재 상태 안내

- 목적: main 공통 유지보수와 영상별 job의 상태 owner로 안내한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md 뒤.
- 책임: main 유지보수 세션과 해당 job 작업 세션.
- 상태: 안내판. 활성 전체 설계·단계 설계 없음.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md의 영상별 작업 공간과 상태.

## 현재 단계

공통 구현과 유지보수는 state/main.md가 소유한다. 영상 데이터와 현재 상태는 extension/jobs/<job-id>/가 소유한다. 기존 브랜치별 상태는 archive와 before 태그에서 보존하는 역사 자료다.

| 브랜치 | 상태 파일 |
|---|---|
| main | state/main.md |

## 직전 게이트

자료 이전·복구 검증·기존 worktree 퇴역 후 main의 ignored·미추적 자료까지 외부 archive로 비웠다. 상세 근거와 한계는 extension/reports/workspace-consolidation-20261021.md가 소유한다.

## 승인 상태

현재 통합·정리의 로컬 구현·이전·복구 검증·커밋은 위임됐다. 새 외부 게시·push·영구 데이터 폐기·Core 변경은 위임되지 않았다.

## 차단

없음.

## 알려진 위험

실제 모델 추론·Premiere 재생·로그인 검증은 이번 파일 정리와 별개다. 복구 범위와 사용자 제외 원본은 보고서·WORKSPACE.md를 따른다.

## 첫 다음 행동

1. 공통 유지보수는 state/main.md를 읽는다.
2. 기존 영상·도구는 extension/docs/WORKSPACE.md의 cleanup snapshot 복구 절차로 필요한 경로를 먼저 복원하고 해당 job의 state.md를 읽는다.
3. 새 영상은 scripts/creator_job.py init --job <job-id>로 main 안에 만든다.

## 다음 세션 시작 prompt

시작 문서 뒤 state/main.md를 읽는다. 영상 작업은 명시된 job 폴더의 상태와 자료만 이어서 읽는다.
