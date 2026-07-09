# AI 에이전트 프로젝트 유지관리 기준

- 상태: 기준
- 목적: AI 에이전트가 세션 시작 시 최소 컨텍스트만 읽고, 필요할 때 필요한 문서만 열고, 구조를 망가뜨리지 않게 유지하는 기준.
- 적용 대상: `PROJECT_BOOTSTRAP.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_RULES.md`, `docs/INDEX.md`, `README.md`, `SESSION_HANDOFF.md`, `CURRENT_TASK.md`, `skills/`, `tools/`.

## 1. 표준 진입점

| 파일 | 대상 | 역할 | 운영 규칙 |
|---|---|---|---|
| `AGENTS.md` | Codex 계열 | 자동 인식 지침 파일 | `PROJECT_BOOTSTRAP.md`를 먼저 읽게 한다 |
| `CLAUDE.md` | Claude Code | 자동 인식 지침 파일 | `@PROJECT_BOOTSTRAP.md`로 시작 커널을 import한다 |
| `GEMINI.md` | Gemini CLI | 자동 인식 context 파일 | `@PROJECT_BOOTSTRAP.md`로 시작 커널을 import한다 |
| `PROJECT_BOOTSTRAP.md` | 모든 에이전트 | 최소 시작 로더와 안전 커널 | 짧게 유지하고 전체 규칙 로드 조건만 둔다 |
| `PROJECT_RULES.md` | 모든 에이전트 | 전체 규칙 원본 | 최상위 원문과 로컬 추가 규칙만 둔다 |
| `docs/INDEX.md` | 모든 에이전트 | 파일 맵과 읽는 조건 | 문서 라우터 역할만 한다 |

포인터 파일에는 프로젝트 규칙, 상태, 작업 절차, 도메인 지식을 넣지 않는다. 시작에 반드시 필요한 최소 지시만 `PROJECT_BOOTSTRAP.md`에 두고, 나머지는 `PROJECT_RULES.md`, `docs/INDEX.md`, 단계 문서, 스킬 문서 중 하나로 보낸다.

## 2. 읽기 경로

최소 시작 로드는 아래만 허용한다.

1. `PROJECT_BOOTSTRAP.md`
2. `docs/INDEX.md`

이어서 필요한 경우에만 `SESSION_HANDOFF.md`, `CURRENT_TASK.md`, `PROJECT_RULES.md`, 단계 문서, 스킬 문서, 도구 문서를 연다. 선택한 지시 문서는 끝까지 읽는다. 긴 리서치 보고서와 폐기 문서는 기본 로드하지 않는다.

`PROJECT_RULES.md` 전체는 규칙, 안전, 삭제/이동/덮어쓰기, 커밋, 외부쓰기, 권한, 반복 실패, 검증, 백업, 문서 구조 변경, 충돌 판단이 있을 때만 읽는다.

## 3. 문서 역할

| 문서 | 역할 | 금지 |
|---|---|---|
| `README.md` | 사람이 보는 프로젝트 입구와 현재 자산 요약 | 세부 절차 저장소로 확장 금지 |
| `PROJECT_BOOTSTRAP.md` | 최소 시작 로더와 안전 커널 | 긴 규칙 원문, 작업 로그, 리서치 저장 금지 |
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
2. 시작 로더를 확인한다: `PROJECT_BOOTSTRAP.md`.
3. 규칙 원본을 확인한다: `PROJECT_RULES.md`.
4. 라우터를 확인한다: `docs/INDEX.md`.
5. 상태 문서를 확인한다: `SESSION_HANDOFF.md`, `CURRENT_TASK.md`.
6. 바뀐 경로를 전체 검색으로 정리한다.
7. `tools\run_doccheck.bat`와 `git diff --check`를 실행한다.

중간에 같은 목표가 3번 연속 실패하면 최상위 Stop Rule에 따라 멈춘다.

## 6. 검증 기준

구조 변경이 끝났다고 말하려면 아래를 만족해야 한다.

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`가 `PROJECT_BOOTSTRAP.md` 포인터 또는 import 역할만 한다.
- `PROJECT_BOOTSTRAP.md`가 짧은 시작 로더 역할만 하고 전체 규칙을 복사하지 않는다.
- `PROJECT_RULES.md`에 최상위 Stop Rule 원문이 남아 있다.
- 비표준 한글 라우터 파일명이 남아 있지 않다.
- `docs/INDEX.md`가 모든 기준 문서의 읽는 조건을 가진다.
- `CURRENT_TASK.md`와 `SESSION_HANDOFF.md`가 서로 다른 현재 상태를 말하지 않는다.
- `tools\run_doccheck.bat`가 에러 없이 통과한다.

## 7. 구조적 문제

AI 에이전트는 아래 문제 때문에 프로젝트 규칙을 자주 손실한다.

| 문제 | 증상 | 이 프로젝트 대응 |
|---|---|---|
| 부분 로드 | 규칙 파일 일부만 읽고 진행 | `PROJECT_BOOTSTRAP.md`를 끝까지 읽고, 필요한 문서도 끝까지 읽는다 |
| 요약 손실 | 핸드오프나 압축 요약에서 제약 조건이 빠짐 | Stop Rule 핵심은 부트스트랩에 두고, 상세 규칙은 `PROJECT_RULES.md` 원문에 둔다 |
| 컨텍스트 과적재 | 문서를 많이 읽을수록 관련 없는 내용이 끼어듦 | 기본 로드는 2개 문서로 제한하고 `docs/INDEX.md`로 선택 로드한다 |
| 컨텍스트 충돌 | 과거 문서와 현재 문서가 서로 다른 기준을 말함 | 문서 상태를 `기준`, `현재작업`, `참고`, `폐기`로 나눈다 |
| 세션 장기화 | 대화가 길어지며 실패 이력과 사용자 제약이 흐려짐 | 3회 연속 실패 Stop Rule과 종료 전 자가 검증을 사용한다 |
| 도구 출력 팽창 | 긴 로그와 검색 결과가 작업 기준을 밀어냄 | 긴 리서치는 `reports/`에 두고 기본 로드하지 않는다 |
| 교차 에이전트 손실 | Codex, Claude, Gemini가 서로 다른 진입 파일을 봄 | 각 표준 진입점에서 같은 `PROJECT_RULES.md`를 참조하게 한다 |
| 약한 강제력 | 문서 지침만 있고 자동 검증이 없음 | `tools\run_doccheck.bat`가 진입점과 라우터 규칙을 검사한다 |

## 8. 방법별 점수

점수는 실행가능성, 최적화 효과, 유지보수성, 위험 감소, 조합성을 각 5점 만점으로 본다.

| 방법 | 실행 | 효과 | 유지 | 위험 | 조합 | 총점 | 판단 |
|---|---:|---:|---:|---:|---:|---:|---|
| 표준 진입점 부트스트랩 게이트 | 5 | 5 | 5 | 5 | 5 | 25 | 즉시 적용 |
| Claude/Gemini `@PROJECT_BOOTSTRAP.md` import | 5 | 5 | 5 | 4 | 5 | 24 | 즉시 적용 |
| Codex `PROJECT_BOOTSTRAP.md` 명시 읽기 | 5 | 4 | 5 | 4 | 5 | 23 | 즉시 적용 |
| `PROJECT_RULES.md` 조건부 전체 로드 | 5 | 4 | 5 | 5 | 5 | 24 | 즉시 적용 |
| `docs/INDEX.md` 선택 라우팅 | 5 | 5 | 5 | 4 | 5 | 24 | 즉시 적용 |
| 기본 로드 2개 문서 제한 | 5 | 5 | 5 | 4 | 5 | 24 | 즉시 적용 |
| `CURRENT_TASK.md`와 `SESSION_HANDOFF.md` 분리 | 5 | 4 | 4 | 4 | 5 | 22 | 유지 |
| 3회 실패 Stop Rule | 5 | 5 | 4 | 5 | 5 | 24 | 유지 및 검증 |
| `doccheck` 자동 검사 | 5 | 5 | 4 | 5 | 5 | 24 | 즉시 강화 |
| `.geminiignore` 대형/임시 파일 제외 | 5 | 3 | 5 | 3 | 5 | 21 | 즉시 적용 |
| 토큰 예산과 문서 줄 수 경고 | 4 | 4 | 4 | 4 | 5 | 21 | 유지 |
| 리서치/진단 보고서 기본 로드 금지 | 5 | 4 | 5 | 4 | 5 | 23 | 유지 |
| 장기 세션 압축 체크포인트 | 3 | 5 | 3 | 4 | 4 | 19 | 향후 도입 |
| Claude hooks 기반 하드 차단 | 2 | 5 | 3 | 5 | 4 | 19 | Claude 전용 후보 |
| 서브에이전트 격리 리서치 | 3 | 3 | 3 | 3 | 3 | 15 | 조사 전용 제한 |
| API prompt caching형 정적 prefix | 2 | 3 | 4 | 2 | 3 | 14 | API 자동화 때만 |
| MCP/검색 기반 문서 retrieval | 2 | 4 | 3 | 4 | 4 | 17 | 별도 설계 필요 |

## 9. 조합 전략

| 조합 | 구성 | 효과 | 현재 판단 |
|---|---|---|---|
| 기본 안전 조합 | 표준 진입점 + `PROJECT_BOOTSTRAP.md` + 조건부 `PROJECT_RULES.md` + `docs/INDEX.md` + `doccheck` | 규칙 손실과 문서 드리프트를 동시에 줄임 | 현재 적용 |
| 토큰 최적화 조합 | 기본 로드 2개 + 선택 라우팅 + `.geminiignore` + 줄 수 경고 | 불필요한 컨텍스트 투입을 줄임 | 현재 적용 |
| 장기 세션 조합 | `CURRENT_TASK.md` + `SESSION_HANDOFF.md` + Stop Rule + 종료 전 자가 검증 | 세션 압축과 상태 손실을 줄임 | 현재 적용 |
| 리서치 관리 조합 | 긴 근거는 `reports/`, 기준은 `docs/AGENT_MAINTENANCE.md`, 경로는 `docs/INDEX.md` | 근거는 보존하고 기본 로드는 줄임 | 현재 적용 |
| 강제 차단 조합 | `doccheck` + Claude hooks + Git hook | 규칙 위반을 실행 전에 막음 | hooks/Git hook은 향후 후보 |
| 병렬 조사 조합 | 단일 주 에이전트 + 조사 전용 서브에이전트 | 메인 컨텍스트 오염을 줄임 | 수정 작업에는 제한 |

## 10. 적용 결정

이번 프로젝트에는 아래 결정을 적용한다.

1. `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`는 모두 `Mandatory Bootstrap Load Gate`를 가진다.
2. `CLAUDE.md`와 `GEMINI.md`는 `@PROJECT_BOOTSTRAP.md`를 직접 import한다.
3. `AGENTS.md`는 Codex용 명시 지시만 둔다. Codex 공식 문서에서 `@file` import를 표준 기능으로 확인하지 못했으므로 import 문법을 넣지 않는다.
4. 시작 커널은 `PROJECT_BOOTSTRAP.md`에만 둔다.
5. 전체 규칙 본문은 `PROJECT_RULES.md`에만 둔다.
6. 문서 위치와 읽는 조건은 `docs/INDEX.md`에만 둔다.
7. 유지관리 기준과 리서치 근거는 이 문서에 둔다.
8. `tools\run_doccheck.bat`는 부트스트랩 게이트, Stop Rule 원문, 표준 라우터, Gemini 제외 목록을 검사한다.
9. Claude hooks, Git hook, MCP retrieval, API prompt caching은 지금 바로 섞지 않는다. 현재 환경 전체에 공통 적용되지 않거나 유지비가 높기 때문이다.

## 11. 리서치 근거

| 출처 | 핵심 근거 | 적용 |
|---|---|---|
| OpenAI Codex `AGENTS.md` | Codex는 작업 전 `AGENTS.md`를 읽고, 경로 계층과 크기 제한을 가진다 | `AGENTS.md`를 표준 진입점으로 유지 |
| Claude Code memory | Claude는 `CLAUDE.md`와 `@path` import를 지원한다 | `@PROJECT_BOOTSTRAP.md` 사용 |
| Gemini CLI context | Gemini는 `GEMINI.md`, `@file` import, ignore 파일을 사용한다 | `@PROJECT_BOOTSTRAP.md`와 `.geminiignore` 사용 |
| AGENTS.md open format | `AGENTS.md`는 에이전트용 README이며 nested 지침을 지원한다 | README와 에이전트 지침 분리 |
| LangChain context engineering | 주요 전략은 write, select, compress, isolate | 선택 로드와 긴 보고서 분리 |
| Drew Breunig long context | 과도한 컨텍스트는 poisoning, distraction, confusion, clash를 만든다 | 기본 로드 최소화 |
| OpenAI compaction | 긴 대화는 상태 보존형 압축으로 품질, 비용, 지연을 관리한다 | 핸드오프와 종료 전 검증 강화 |
| OpenAI token counting | 지시, 도구, 파일도 토큰 비용에 포함된다 | 기본 로드 문서 줄 수 경고 유지 |
| OpenAI prompt caching | 정적 지시는 앞에, 동적 정보는 뒤에 둘 때 캐시 효과가 난다 | 규칙/상태/작업 문서 분리 |
| Claude Code hooks | `PreToolUse`, `PostToolUseFailure`, `PreCompact` 등에서 차단과 검증이 가능하다 | 향후 하드 차단 후보 |
| Anthropic effective agents | 단순한 조합, 명확한 도구 문서, 체크포인트가 중요하다 | 문서 역할 분리와 검증 게이트 유지 |
| Cognition multi-agent 글 | 병렬 다중 에이전트는 전체 맥락과 암묵 결정을 공유하지 못하면 취약하다 | 서브에이전트는 조사용으로 제한 |
| arXiv AGENTS 효율 연구 | `AGENTS.md`가 median runtime 28.64%, output token 16.58% 감소와 연관됨 | 표준 진입점 유지 |
| arXiv AGENTS 효과 평가 | 불필요한 context 파일은 비용을 20% 이상 늘리고 성공률을 낮출 수 있음 | 최소 필수 규칙만 유지 |
| arXiv configuration smells | Lint Leakage 62%, Context Bloat 42%, Skill Leakage 35%가 관찰됨 | `doccheck`와 문서 역할 분리 강화 |
| arXiv agentic manifests | manifest는 운영 명령, 기술 메모, 아키텍처가 섞이기 쉽다 | 규칙, 라우터, 상태, 보고서 분리 |

근거 링크:

- <https://developers.openai.com/codex/guides/agents-md>
- <https://docs.anthropic.com/en/docs/claude-code/memory>
- <https://geminicli.com/docs/cli/gemini-md/>
- <https://agents.md/>
- <https://www.langchain.com/blog/context-engineering-for-agents>
- <https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html>
- <https://developers.openai.com/api/docs/guides/compaction>
- <https://developers.openai.com/api/docs/guides/token-counting>
- <https://developers.openai.com/api/docs/guides/prompt-caching>
- <https://docs.anthropic.com/en/docs/claude-code/hooks>
- <https://www.anthropic.com/engineering/building-effective-agents>
- <https://cognition.com/blog/dont-build-multi-agents>
- <https://arxiv.org/abs/2601.20404>
- <https://arxiv.org/abs/2602.11988>
- <https://arxiv.org/abs/2606.15828>
- <https://arxiv.org/abs/2509.14744>
