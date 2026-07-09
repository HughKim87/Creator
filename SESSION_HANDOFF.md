# SESSION_HANDOFF.md — 김실버유튜브

- 최종 갱신: 2026-07-09
- 성격: 다음 세션 인계 상태. 규칙 원본이 아니다.
- 먼저 읽기: `PROJECT_BOOTSTRAP.md` → `docs/INDEX.md`. 규칙 트리거면 `PROJECT_RULES.md`.
- Git 이력은 `git log --oneline`으로 확인한다. 커밋 SHA는 이 문서에 고정하지 않는다.

## 1. 현재 상태

- 편집 재개 아님. 원본 영상·자막·현재 산출물 없음.
- 모든 문서 NUL 바이트 없음, doccheck 통과(errors=0).
- 미커밋 변경 2건: `PROJECT_BOOTSTRAP.md`, `PROJECT_RULES.md` (아래 File Write Safety 규칙 추가분).
- 나머지 거버넌스 문서는 커밋 기준선 상태.

## 2. 이번 세션 완료 (커밋됨)

- `PROJECT_RULES.md`가 가리키던, 존재하지 않는 `docs/` 규칙 문서 6개 참조를 제거하고 핵심 규칙을 본문에 인라인화했다.
- `tools/doccheck/check_docs.py`에 "참조 문서 존재 검증"을 추가했다.
- `01_유튜브_제작_워크플로우.md`의 검증 라벨 불일치를 정돈하고, 백업 규칙을 Git 기반으로 바로잡았다.
- 문서 간결화 통합 실행안을 작성했다: `docs/claude_간결화_실행안.md` (claude·codex 두 제안 통합). 원본 제안 2파일은 삭제했다.

## 3. 이번 세션 완료 (미커밋)

- File Write Safety 규칙 신설: `PROJECT_RULES.md`에 새 섹션, `PROJECT_BOOTSTRAP.md` 하드룰에 한 줄. 커밋할지는 사용자 판단.

## 4. 다음 작업

- 문서 본체 압축(BOOTSTRAP·RULES·INDEX·HANDOFF 등 줄이기)은 중단 상태다. 명세는 `docs/claude_간결화_실행안.md`.
- 재개하면 한 파일씩 쓰고 매 파일마다 검증한다(§5 주의).
- 미커밋 2건은 검토 후 사용자 승인 시 커밋한다.

## 5. 반드시 주의 — 환경 함정

- 이 폴더로의 파일 쓰기가 간헐적으로 NUL 바이트를 섞어 파일을 손상시킨다. 편집기(Write) 일괄 쓰기와 대량·한글(CJK) 쓰기에서 특히 잦다.
- 대응은 `PROJECT_RULES.md`의 File Write Safety 규칙을 따른다: 쓴 직후 NUL·내용 검증, 손상 시 `git show HEAD:<경로> > <경로>`로 되돌린 뒤 재시도.
- 안전 확인된 통로는 셸 바이트-스트림 쓰기(임시본 → 검증 → 복사)다. 여러 파일을 한 번에 쓰지 않는다.

## 6. 중단 조건

- 새 영상 편집·XML·러프컷으로 넘어가려는 경우.
- 현재 기준 파일 없이 산출물을 만들려는 경우.
- 같은 방향 결과가 두 번 이상 거절된 경우.
- 파일 손상이 반복되는데 검증 없이 계속 쓰는 경우.

## 7. 다음 세션 시작 프롬프트

```
PROJECT_BOOTSTRAP.md와 docs/INDEX.md를 읽고 이어서 진행.
현재 원본 영상 없음, 편집 재개 아님.
미커밋 변경(File Write Safety) PROJECT_BOOTSTRAP.md, PROJECT_RULES.md 를 먼저 검토.
문서 압축은 docs/claude_간결화_실행안.md 명세대로, 파일당 쓰기 + 검증으로만 진행.
파일 쓰기는 File Write Safety 규칙 준수: 쓴 뒤 NUL 과 내용 검증, 손상 시 git show 로 복구.
```
