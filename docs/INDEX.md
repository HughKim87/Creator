# 문서 인덱스 — Video Workflow

- 갱신: 2026-07-09
- 역할: 필요한 문서만 고르는 라우터.

## 기본 로드

1. `PROJECT_BOOTSTRAP.md`
2. `docs/INDEX.md`

이어지는 작업이면 `SESSION_HANDOFF.md`와 `CURRENT_TASK.md`를 읽는다.
규칙, 안전, 삭제/이동/덮어쓰기, 커밋, 권한, 반복 실패, 검증, 문서 구조 변경,
충돌 판단이면 `PROJECT_RULES.md`를 읽는다.

## 현재 상태

- 원본 영상, 원본 자막, 현재 편집 산출물 없음.
- 새 영상 작업은 새 원본 제공 후 시작 단계와 기준 문서를 정한 뒤 진행.
- 과거 삭제된 `workspace/`, `temp/archive/`, 재설계 진단 보고서는 현재 입력이 아니다.

## 문서 라우터

| 상황 | 읽을 문서 |
|---|---|
| 프로젝트 입구 확인 | `README.md` |
| 이어서 작업 | `SESSION_HANDOFF.md`, `CURRENT_TASK.md` |
| 규칙/안전/구조 변경 | `PROJECT_RULES.md`, `docs/AGENT_MAINTENANCE.md` |
| 전체 제작 단계 판단 | `01_유튜브_제작_워크플로우.md` |
| 작업 원칙 확인 | `PROJECT_RULES.md` |
| 5단계 기획 | `기획_리서치/기획단계_규격_2026-07-06.md` |
| 스킬 작업 | `skills/README.md`, `skills/SKILL_CONTRACT.md`, 필요한 `skills/*/SKILL.md` |
| 도구 작업 | `tools/README.md`, 필요한 도구 도움말 |
| 과거 운영 진단 배경 | `기획_리서치/프로젝트_운영문제_진단_및_개선안_2026-07-07.md` |

## 기준 문서

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`: 플랫폼별 진입 포인터
- `PROJECT_BOOTSTRAP.md`: 항상 로드되는 최소 커널
- `PROJECT_RULES.md`: 조건부 전체 규칙 원본
- `docs/AGENT_MAINTENANCE.md`: 문서 구조 유지관리 체크리스트
- `skills/SKILL_CONTRACT.md`: 스킬 문서 공통 작성 기준
- `.geminiignore`: Gemini 컨텍스트 제외 목록

## 로드 원칙

- 선택한 지시 문서는 끝까지 읽는다.
- 긴 보고서와 폐기 문서는 기본 로드하지 않는다.
- 문서 안에 다른 문서의 절차를 복사하지 않는다.
- Git으로 확인 가능한 커밋 SHA와 작업트리 상태는 문서에 고정하지 않는다.
