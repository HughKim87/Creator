# claude_간결화_실행안 — 통합 실행안

- 성격: 1회성 실행안. claude·codex 두 제안의 통합본. 실제 감량이 끝나면 이 파일도 지운다.
- 작성: 2026-07-09
- 뼈대: Codex의 2단 구조 + 수치 목표·"균일 무시" 근거·red-team 안전선(claude)

## 1. 진단

문제는 규칙 부족이 아니라 방어적 문서 누적이다. 거버넌스 문서 12개 1,175줄 중 약 82%(960줄)가
영상 제작이 아니라 문서 관리에 대한 메타 규칙이고, 세션 시작 시 항상 로드되는 양만 258줄이다.

왜 이게 역효과인가: 프런티어 모델이 안정적으로 따르는 지시는 약 150~200개, Claude 하네스가 이미
~50개를 쓴다. 지시가 이 한도를 넘으면 넘친 것만이 아니라 **전체 지시를 균일하게 무시**한다.
규칙을 더할수록 지켜야 할 안전 규칙까지 함께 약해진다. 그래서 다음 작업은 추가가 아니라 감량이다.

## 2. 설계 원칙

뼈대(2단 구조 유지):

- 항상 로드: 최소 커널 `PROJECT_BOOTSTRAP.md` + 라우터 `docs/INDEX.md`만.
- 조건부 로드: 전체 규칙 `PROJECT_RULES.md`와 단계 문서·스킬은 필요할 때만.
- 이 2단 구조는 연구가 지지하는 패턴이라 바꾸지 않고, 각 파일을 줄인다.

운영 원칙:

- 기본은 자율. 되돌릴 수 없는 행동만 멈춘다.
- 강제는 문장이 아니라 도구로. `doccheck`는 구조·크기·위험참조만 검사한다.
- 단순화 규칙: ① 한 규칙이 두 문서 이상에 반복되면 하나만 남긴다. ② "하지 마라"가 3개 이상이면
  상위 원칙 하나로 합친다. ③ 예외가 길어지면 목록 대신 판단 기준으로 바꾼다. ④ 리서치 근거는
  운영 규칙 파일에 넣지 않는다. ⑤ 항상 로드 문서에 역사·점수표·긴 설명을 넣지 않는다.

## 3. 목표 구조와 수치

| 파일 | 역할 | 현재 | 목표 |
|---|---|---:|---|
| `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` | 진입 포인터 | 48 | 각 5~12줄 |
| `PROJECT_BOOTSTRAP.md` | 항상 로드 커널 | 84 | ≤60줄 |
| `docs/INDEX.md` | 라우터(표만) | 174 | ≤60줄 |
| `PROJECT_RULES.md` | 조건부 전체 규칙 | 248 | ≤160줄 |
| `docs/AGENT_MAINTENANCE.md` | 유지관리 | 183 | `reports/`로 이동 또는 ≤50줄 체크리스트 |
| `SESSION_HANDOFF.md` | 현재 상태 인계 | 117 | ≤60줄 |
| `CURRENT_TASK.md` | 현재 작업 카드 | 59 | ≤40줄 |
| `00_공통_작업원칙.md` | 공통 원칙 | 51 | `PROJECT_RULES.md`로 흡수 후 삭제 |
| `01_유튜브_제작_워크플로우.md` | 도메인(단계) | 116 | ~90줄 (유지·경량) |

총량 목표: 거버넌스 1,175 → 약 500줄(≈ −60%), 항상 로드 258 → 약 110~120줄(≈ −55%).
참고: 더 공격적인 병합(코어 1개)이면 ~300줄까지 가능하나, 안전한 2단 구조를 택했으므로
목표는 위처럼 보수적으로 잡는다.

## 4. 자율성 기준

자율로 진행(승인 불필요):

- 요청 수행에 필요한 파일 읽기, `docs/INDEX.md` 기준 문서 선택
- 코드·문서 수정 방식 결정, 검증 명령 선택·실행
- 단순 오류 수정 후 재검증, 결과 보고 정리

사용자 확인 필요(되돌릴 수 없거나 위험):

- 삭제·대량 이동·덮어쓰기
- 커밋·푸시·업로드·외부 게시
- 새 도구 설치·네트워크 인증·권한 변경
- 같은 목표 3회 실패 후 계속 진행
- 사용자 의도와 다른 방향으로 목표 변경
- 영구 규칙 파일에 새 규칙 추가

핵심: 모든 행동을 막지 않는다. 되돌릴 수 없는 것만 멈춘다.

## 5. 실행 순서

1. `docs/AGENT_MAINTENANCE.md`의 리서치·16행 점수표를 `reports/`로 격리(또는 체크리스트로 축소).
2. `PROJECT_BOOTSTRAP.md`를 ≤60줄로 압축(중복 로드 설명 제거).
3. `PROJECT_RULES.md`에서 중복 설명·예시 제거, `00_공통_작업원칙.md` 흡수 → ≤160줄.
4. `docs/INDEX.md`에서 상태 체계·동기화표·로드맵을 빼고 라우터 표만 → ≤60줄.
5. `SESSION_HANDOFF.md` ≤60줄, `CURRENT_TASK.md` ≤40줄(현재 상태·다음 행동·차단 조건만).
6. `doccheck`의 하드코딩 문구 매칭 제거 → 크기·역할·깨진 참조·비밀·원본 덮어쓰기만 검사.
7. 각 단계 후 `doccheck`와 `git diff --check`로 검증.

## 6. Red-team — 남길 것

감량하되 아래는 유지한다(설명이 아니라 실제 안전선):

- 비밀 노출 금지, 되돌릴 수 없는 외부 행동 승인, 원본 파일 보호, 3회 실패 Stop Rule.
- 5단계 대사 추적성 규격(채널 품질의 핵심 도메인 규칙).
- `doccheck` 자체(단, 축소된 구조 검사 형태로).

과소 문서화도 위험하다(에이전트 README 연구: 2,303개 중 14.5%만 보안 언급). "다 지우기"가 아니라
안전 소수만 강하게 남기고 나머지는 자율이다.

검증 표시: Codex 제안이 인용한 arXiv:2601.07190의 "22.7% / 최대 57% 절감" 수치는 미확인이므로
이 실행안의 근거로 쓰지 않는다.

## 7. 완료 정의 (측정 가능)

- 거버넌스 총량 ≤ 500줄, 항상 로드 ≤ 120줄.
- 한 규칙이 두 문서 이상에 중복되지 않는다.
- `doccheck`가 문구가 아니라 구조·크기·깨진 참조를 검사한다.
- 에이전트가 되돌릴 수 있는 작업을 승인 없이 진행할 수 있다.

## Sources

- HumanLayer, "Writing a good CLAUDE.md" — <https://www.humanlayer.dev/blog/writing-a-good-claude-md>
- 지시 수 한계 연구 — <https://arxiv.org/pdf/2507.11538>
- Gloaguen et al., "Evaluating AGENTS.md" (arXiv:2602.11988) — <https://arxiv.org/abs/2602.11988>
- Iwo Szapar, 20+ 논문 종합 — <https://www.iwoszapar.com/p/agents-md-do-context-files-help>
- Anthropic, "Building Effective Agents" — <https://www.anthropic.com/engineering/building-effective-agents>
- LangChain, context engineering — <https://www.langchain.com/blog/context-engineering-for-agents>
- Drew Breunig, how contexts fail — <https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html>
- Cognition, don't build multi-agents — <https://cognition.com/blog/dont-build-multi-agents>
- 12-Factor Agents — <https://github.com/humanlayer/12-factor-agents>
