# 세션 핸드오프

- 갱신일: 2026-07-31
- 역할: main workspace의 현재 상태 단일 owner
- 현재 작업: 없음
- 상태: idle; 활성 계획·task-rule·scratch·종료 보고서는 없다.
- branch: `main`
- startup route: `PROJECT_RULES.md` → 이 문서 → 새 사용자 요청에 맞는 조건부 규칙

## 현재 검증 상태

- 모든 `inputs` 경로는 분석·변경·stage 대상에서 제외한다.
- inputs 제외 현재 파일은 tracked 180개, ignored runtime 67개, untracked 0개다.
- `extension/outputs/`에는 현재 파일이 없고, Git 추적 input·output·cache도 없다.
- FFmpeg 45개와 whisper.cpp 22개는 `extension/.runtime/`에서 유지한다.
- 최신 전체 gate는 Core 141, Extension 140, maintenance 문서 59·링크 78·오류 0, Node·clean-clone 통과다.

## 첫 다음 행동

새 요청이 오면 현재 idle 상태에서 가장 낮은 충분 작업 등급과 matching rule을 선택한다.
