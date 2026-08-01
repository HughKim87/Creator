# 세션 핸드오프

- 갱신일: 2026-08-01
- 역할: ainotebook 이외 worktree의 현재 상태 단일 owner
- 현재 작업: 없음
- 상태: idle; Git 이력 정제·canonical 원격 게시·fresh clone 검증 완료
- branch: `main`
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; uncommitted ignored runtime은 이 workspace에만 존재한다.
- startup route: `PROJECT_RULES.md` → 이 문서 → 새 사용자 요청에 맞는 조건부 규칙

## 현재 검증 상태

- 원본 43개 논리 커밋은 43/43 대응되고 외부 bundle set·SHA mapping과 로컬 보존 branch로 복구 가능하다.
- canonical GitHub fresh clone에서 protected path와 100MiB 초과 blob은 0이며 전체 gate가 통과했다.
- 모든 `inputs` 경로는 분석·변경·stage 대상에서 제외한다.
- inputs 제외 현재 파일은 tracked 181개, ignored runtime 67개, untracked 0개다.
- `extension/outputs/`에는 현재 파일이 없고, Git 추적 input·output·cache도 없다.
- FFmpeg 45개와 whisper.cpp 22개는 `extension/.runtime/`에서 유지한다.

## 첫 다음 행동

1. 새 요청이 오면 idle 상태에서 가장 낮은 충분 작업 등급과 matching rule을 선택한다.

## 다음 session 시작 prompt

1. `PROJECT_RULES.md`와 `SESSION_HANDOFF.md`를 읽고 새 사용자 요청을 분류한다.
