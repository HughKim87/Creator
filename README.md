# 영상 제작 워크플로우

AI 에이전트가 반복 영상 제작 작업을 안정적으로 처리하기 위한 독립 작업 폴더다.

- 현재 상태: 원본 영상, 자막, 편집 산출물 없음. 새 원본 대기.

## 핵심 방향

> 개별 영상 작업 정보는 규칙 문서가 아니라 작업 입력과 산출물 문서에서 관리한다.

수치나 사례는 최신 데이터로 다시 확인한다.

## 주요 파일

| 위치 | 역할 |
|---|---|
| `PROJECT_BOOTSTRAP.md` | 세션 시작 최소 커널 |
| `PROJECT_RULES.md` | 조건부 전체 규칙 |
| `docs/INDEX.md` | 문서 라우터 |
| `SESSION_HANDOFF.md` | 다음 세션 상태 |
| `CURRENT_TASK.md` | 현재 작업 카드 |
| `01_유튜브_제작_워크플로우.md` | 1~8단계 게이트 |
| `skills/` | 단계별 실행 스킬 |
| `tools/` | FFmpeg, synccheck, doccheck, remux |
| `기획_리서치/` | 5단계 기획 규격과 운영 진단 |

## 에이전트 사용 방식

1. `PROJECT_BOOTSTRAP.md`와 `docs/INDEX.md`만 먼저 읽는다.
2. 필요한 문서만 라우터에서 골라 끝까지 읽는다.
3. 규칙, 안전, 삭제/이동/덮어쓰기, 커밋, 권한, 반복 실패, 검증, 문서 구조 변경이면 `PROJECT_RULES.md`를 읽는다.
4. 되돌릴 수 있는 로컬 작업은 자율 진행하고, 되돌릴 수 없는 작업은 승인받는다.
5. 문서·스킬·도구 변경 후 `tools\run_doccheck.bat`와 `git diff --check`를 실행한다.

## 다시 시작

- 새 원본이 들어오면 `workspace/inputs/`, `workspace/active/`, `workspace/outputs/`를 만든다.
- 촬영 전 콘텐츠는 1단계부터, 촬영 완료본은 5단계부터 시작한다.
- 컷리스트, XML, 러프컷은 선행 게이트 통과 후에만 만든다.
