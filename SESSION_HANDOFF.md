# 세션 핸드오프

- 갱신일: 2026-08-01
- 역할: ainotebook 이외 worktree의 현재 상태 단일 owner
- 현재 작업: Git 이력 정제 및 GitHub 게시
- 상태: `W4 ready`; 최종보고서 초안 작성, live 원격 SHA와 fast-forward 게시 확인 대기
- branch: `codex/history-sanitization-20260801`
- 활성 전체 설계: `extension/work/2026-08-01_GIT_HISTORY_SANITIZATION_OVERALL.md`
- 활성 단계 설계: `extension/work/2026-08-01_W4_GIT_HISTORY_SANITIZATION.md`
- handoff mode: `same-workspace`; uncommitted ignored runtime은 이 workspace에만 존재한다.
- startup route: `PROJECT_RULES.md` → 이 문서 → 새 사용자 요청에 맞는 조건부 규칙

## 현재 검증 상태

- `GHP1-S1` 통과: 보존 branch와 외부 bundle의 HEAD는 `997ab157418f3c9b9257cc9561f1a81f51d45435`로 일치한다.
- bundle은 383,824,883 bytes, SHA-256 `F13A2552E1690924A4E29F6DDBB8A6DCE14C0CB3120DFDDE927A74947CA7DD7B`, verify·복구 clone·213커밋 일치 검증을 통과했다.
- `GHP1-S2` 통과: 원본 43커밋을 충돌·merge 없이 재적용했고 메타데이터 순서가 43/43 일치한다.
- 새 이력은 output 경로 0, input 접근 0, 100MiB 초과 reachable blob 0이며 원본 최종 tree와의 차이는 원격 README 표현 3곳뿐이다.
- `W3` 통과: source와 independent no-local clean clone에서 Core 141·Extension 140·maintenance·Node·clone-conformance가 모두 성공했다.
- old→new SHA 대응표는 43행이며 외부 파일 SHA-256은 `240C0D5ED13B47AAB04D17DE754D219998D0939F8FC0694725D9AE6FB91BD1C8`이다.
- 모든 `inputs` 경로는 분석·변경·stage 대상에서 제외한다.
- inputs 제외 현재 파일은 tracked 180개, ignored runtime 67개, untracked 0개다.
- `extension/outputs/`에는 현재 파일이 없고, Git 추적 input·output·cache도 없다.
- FFmpeg 45개와 whisper.cpp 22개는 `extension/.runtime/`에서 유지한다.

## 첫 다음 행동

1. live 원격 SHA와 fast-forward 조건을 재확인하고 정제 branch를 원격 `main`에 push한다.

## 다음 session 시작 prompt

1. `PROJECT_RULES.md` → `SESSION_HANDOFF.md` → 활성 단계 설계를 읽는다.
2. `W4`부터 재개하고, 완료 전 기존 파일·로컬 branch를 삭제하지 않는다.
