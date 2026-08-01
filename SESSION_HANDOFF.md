# 세션 핸드오프

- 갱신일: 2026-08-01
- 역할: ainotebook 이외 worktree의 현재 상태 단일 owner
- 현재 작업: Git 이력 정제 및 GitHub 게시
- 상태: `GHP1-S1 ready`; 설계 문서 게이트 통과, 원본 복구 경계 준비 중
- branch: `main`
- 활성 전체 설계: 없음
- 활성 단계 설계: [Git 이력 정제 및 게시 설계](extension/work/2026-08-01_GIT_HISTORY_SANITIZATION.md)
- handoff mode: `same-workspace`; uncommitted ignored runtime은 이 workspace에만 존재한다.
- startup route: `PROJECT_RULES.md` → 이 문서 → 새 사용자 요청에 맞는 조건부 규칙

## 현재 검증 상태

- 모든 `inputs` 경로는 분석·변경·stage 대상에서 제외한다.
- inputs 제외 현재 파일은 tracked 180개, ignored runtime 67개, untracked 0개다.
- `extension/outputs/`에는 현재 파일이 없고, Git 추적 input·output·cache도 없다.
- FFmpeg 45개와 whisper.cpp 22개는 `extension/.runtime/`에서 유지한다.

## 첫 다음 행동

1. 활성 설계의 `GHP1-S1`에 따라 원본 보존 branch와 외부 bundle을 만들고 검증한다.

## 다음 session 시작 prompt

1. `PROJECT_RULES.md` → `SESSION_HANDOFF.md` → 활성 단계 설계를 읽는다.
2. `GHP1-S1`부터 재개하고, 완료 전 기존 파일·로컬 branch를 삭제하지 않는다.
