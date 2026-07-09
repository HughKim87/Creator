# SESSION_HANDOFF.md — Video Workflow

- 갱신: 2026-07-09
- 성격: 다음 세션 인계 상태. 규칙 원본이 아니다.
- 먼저 읽기: `PROJECT_BOOTSTRAP.md` → `docs/INDEX.md`; 규칙 트리거면 `PROJECT_RULES.md`.

## 현재 상태

- 편집 재개 아님. 원본 영상, 자막, 현재 산출물 없음.
- 문서 감량 본작업 진행 중.
- 작업트리와 커밋 상태는 Git 명령으로 확인한다.

## 완료된 정리

- `PROJECT_BOOTSTRAP.md`, `PROJECT_RULES.md`, `docs/INDEX.md`, `README.md`, `CURRENT_TASK.md` 압축.
- `docs/AGENT_MAINTENANCE.md`를 체크리스트로 축소.
- `tools/doccheck/check_docs.py`를 구조 검사 중심으로 축소.
- 공통 작업 원칙은 `PROJECT_RULES.md`에 흡수하고 파일을 삭제.
- 일회성 간결화 제안/실행안 문서는 삭제.

## 다음 작업

- 워크플로우 문서가 목표 크기와 현재 구조에 맞는지 확인한다.
- 전체 NUL, 깨진 참조, `doccheck`, `git diff --check`를 실행한다.
- 통과하면 수치로 감량 결과를 보고한다.

## 주의

- 파일 쓰기 후 NUL 바이트와 핵심 내용을 확인한다.
- 손상 파일은 Git에서 복구하고 다시 시도한다.
- 같은 목표가 3회 실패하면 Stop Rule에 따라 멈춘다.

## 중단 조건

- 새 영상 편집, XML, 러프컷으로 넘어가려는 경우.
- 현재 기준 파일 없이 산출물을 만들려는 경우.
- 파일 손상이 반복되는데 검증 없이 계속 쓰려는 경우.
