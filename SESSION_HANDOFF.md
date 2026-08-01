# 세션 핸드오프

- 갱신일: 2026-08-01
- 역할: ainotebook 이외 worktree의 현재 상태 단일 owner
- 현재 작업: Git 이력 정제 및 GitHub 게시
- 상태: `GHP1-S3 in_progress`; 커밋별 이력 정제 게이트 통과, 통합 검증 중
- branch: `codex/history-sanitization-20260801`
- 활성 전체 설계: 없음
- 활성 단계 설계: [Git 이력 정제 및 게시 설계](extension/work/2026-08-01_GIT_HISTORY_SANITIZATION.md)
- handoff mode: `same-workspace`; uncommitted ignored runtime은 이 workspace에만 존재한다.
- startup route: `PROJECT_RULES.md` → 이 문서 → 새 사용자 요청에 맞는 조건부 규칙

## 현재 검증 상태

- `GHP1-S1` 통과: 보존 branch와 외부 bundle의 HEAD는 `997ab157418f3c9b9257cc9561f1a81f51d45435`로 일치한다.
- bundle은 383,824,883 bytes, SHA-256 `F13A2552E1690924A4E29F6DDBB8A6DCE14C0CB3120DFDDE927A74947CA7DD7B`, verify·복구 clone·213커밋 일치 검증을 통과했다.
- `GHP1-S2` 통과: 원본 43커밋을 충돌·merge 없이 재적용했고 메타데이터 순서가 43/43 일치한다.
- 새 이력은 output 경로 0, input 접근 0, 100MiB 초과 reachable blob 0이며 원본 최종 tree와의 차이는 원격 README 표현 3곳뿐이다.
- 모든 `inputs` 경로는 분석·변경·stage 대상에서 제외한다.
- inputs 제외 현재 파일은 tracked 180개, ignored runtime 67개, untracked 0개다.
- `extension/outputs/`에는 현재 파일이 없고, Git 추적 input·output·cache도 없다.
- FFmpeg 45개와 whisper.cpp 22개는 `extension/.runtime/`에서 유지한다.

## 첫 다음 행동

1. `python -B scripts/verify.py`와 별도 local clean clone gate를 실행한다.

## 다음 session 시작 prompt

1. `PROJECT_RULES.md` → `SESSION_HANDOFF.md` → 활성 단계 설계를 읽는다.
2. `GHP1-S3`부터 재개하고, 완료 전 기존 파일·로컬 branch를 삭제하지 않는다.
