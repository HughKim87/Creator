# AI 에이전트 프로젝트 유지관리 기준

- 상태: 기준
- 목적: AI 에이전트가 이 프로젝트를 누락 없이 읽고, 필요할 때 필요한 문서만 열고, 구조를 망가뜨리지 않게 유지하는 기준.
- 적용 대상: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_RULES.md`, `docs/INDEX.md`, `README.md`, `SESSION_HANDOFF.md`, `CURRENT_TASK.md`, `skills/`, `tools/`.

## 1. 표준 진입점

| 파일 | 대상 | 역할 | 운영 규칙 |
|---|---|---|---|
| `AGENTS.md` | Codex 계열 | 자동 인식 지침 파일 | 포인터만 둔다. 규칙 본문을 쓰지 않는다 |
| `CLAUDE.md` | Claude Code | 자동 인식 지침 파일 | `@PROJECT_RULES.md`로 원본 규칙을 import한다 |
| `GEMINI.md` | Gemini CLI | 자동 인식 context 파일 | `@PROJECT_RULES.md`로 원본 규칙을 import한다 |
| `PROJECT_RULES.md` | 모든 에이전트 | 단일 규칙 원본 | 최상위 원문과 로컬 추가 규칙만 둔다 |
| `docs/INDEX.md` | 모든 에이전트 | 파일 맵과 읽는 조건 | 문서 라우터 역할만 한다 |

포인터 파일에는 프로젝트 규칙, 상태, 작업 절차, 도메인 지식을 넣지 않는다. 그런 내용은 `PROJECT_RULES.md`, `docs/INDEX.md`, 단계 문서, 스킬 문서 중 하나로 보내야 한다.

## 2. 읽기 경로

기본 로드는 아래만 허용한다.

1. `PROJECT_RULES.md`
2. `SESSION_HANDOFF.md`
3. `docs/INDEX.md`

이어서 필요한 경우에만 `CURRENT_TASK.md`, 단계 문서, 스킬 문서, 도구 문서를 연다. 선택한 지시 문서는 끝까지 읽는다. 긴 리서치 보고서와 폐기 문서는 기본 로드하지 않는다.

## 3. 문서 역할

| 문서 | 역할 | 금지 |
|---|---|---|
| `README.md` | 사람이 보는 프로젝트 입구와 현재 자산 요약 | 세부 절차 저장소로 확장 금지 |
| `PROJECT_RULES.md` | 영구 규칙 | 작업 로그, 커밋 상태, 긴 리서치 저장 금지 |
| `docs/INDEX.md` | 문서 위치와 읽는 조건 | 규칙 본문 중복 금지 |
| `SESSION_HANDOFF.md` | 다음 세션 인계 상태 | 장기 지식 저장소화 금지 |
| `CURRENT_TASK.md` | 현재 작업 카드 | 완료된 작업 히스토리 누적 금지 |
| `skills/*/SKILL.md` | 단계별 실행 절차 | 전체 워크플로우 반복 금지 |
| `reports/` | 긴 리서치와 진단 | 기본 로드 문서로 승격 금지 |

## 4. 새 문서 판단

새 문서는 아래 조건을 모두 만족할 때만 만든다.

1. 기존 기준 문서에 넣으면 역할이 섞인다.
2. 다음 세션에서 다시 찾아야 할 만큼 중요한 기준이나 근거다.
3. `docs/INDEX.md`에 상태와 읽는 조건을 즉시 등록할 수 있다.
4. 기존 문서를 대체한다면 대체 관계가 명확하다.

단순 작업 기록, 임시 판단, 한 번 쓰고 버릴 분석은 새 기준 문서로 만들지 않는다.

## 5. 유지관리 작업 순서

문서 구조를 바꿀 때는 아래 순서를 따른다.

1. 표준 진입점 파일을 확인한다: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`.
2. 규칙 원본을 확인한다: `PROJECT_RULES.md`.
3. 라우터를 확인한다: `docs/INDEX.md`.
4. 상태 문서를 확인한다: `SESSION_HANDOFF.md`, `CURRENT_TASK.md`.
5. 바뀐 경로를 전체 검색으로 정리한다.
6. `tools\run_doccheck.bat`와 `git diff --check`를 실행한다.

중간에 같은 목표가 3번 연속 실패하면 최상위 Stop Rule에 따라 멈춘다.

## 6. 검증 기준

구조 변경이 끝났다고 말하려면 아래를 만족해야 한다.

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`가 포인터 또는 import 역할만 한다.
- `PROJECT_RULES.md`에 최상위 Stop Rule 원문이 남아 있다.
- 비표준 한글 라우터 파일명이 남아 있지 않다.
- `docs/INDEX.md`가 모든 기준 문서의 읽는 조건을 가진다.
- `CURRENT_TASK.md`와 `SESSION_HANDOFF.md`가 서로 다른 현재 상태를 말하지 않는다.
- `tools\run_doccheck.bat`가 에러 없이 통과한다.

## 7. 리서치 근거

- OpenAI Codex는 `AGENTS.md`를 프로젝트 지침 파일로 사용하고, fallback 파일명은 별도 설정하지 않으면 무시한다. 근거: <https://developers.openai.com/codex/guides/agents-md>
- Claude Code는 `CLAUDE.md`를 읽으며, `@path` import로 다른 파일을 불러올 수 있다. 근거: <https://docs.anthropic.com/en/docs/claude-code/memory>
- Gemini CLI는 기본 context 파일명으로 `GEMINI.md`를 사용하고, `@file.md` import를 지원한다. 근거: <https://geminicli.com/docs/cli/gemini-md/>
- `llms.txt`는 웹 문서 탐색용 제안 규격에 가깝고, 이 로컬 프로젝트의 필수 에이전트 진입점은 아니다. 근거: <https://llmstxt.org/>
