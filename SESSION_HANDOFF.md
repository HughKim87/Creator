# SESSION_HANDOFF.md — Video Workflow

- 갱신: 2026-07-11
- 역할: 프로젝트 작업 상태의 단일 원본. 세션 인계와 활성 작업 카드를 모두
  이 파일에서 관리한다. 규칙이나 장기 로그가 아니다.
- 먼저 읽기: `PROJECT_BOOTSTRAP.md` → `docs/INDEX.md`.

## 현재 상태

- 편집 재개 아님. 현재 편집 산출물 없음. 새 원본 대기.
- `inputs/`에 구 원본 mp4 1개 존재(2026-06-30, gitignore 대상). 현재 작업
  입력이 아니며, 사용 여부는 사용자 결정 대기.
- 프레임워크/워크플로우 개선 1차 반영 완료.
- 규칙 문서 기본 다듬기 반영 완료(아래 완료된 정리 참조).
- 작업트리와 커밋 상태는 Git 명령으로 확인한다.

## 활성 작업 카드

- 없음. 새 원본 대기.

새 원본이 들어오면 아래를 확정해 이 섹션에 기록한다.

1. 소스: 원본 파일 경로, 자막 유무.
2. 시작 단계: 촬영 전 콘텐츠는 1단계, 촬영 완료본은 5단계.
3. 목표 산출물과 통과해야 할 게이트.
4. 승인 상태값과 사용자 결정 대기 항목.

## 완료된 정리 (이번 세션)

- 상태 정보를 이 파일로 단일화. `docs/INDEX.md`·`README.md`에서 상태 제거.
- `PROJECT_RULES.md` 로드 조건과 Finish Check를 `PROJECT_BOOTSTRAP.md`
  단일 원본으로 통일.
- 언어 정책 이원화 적용(원본: `PROJECT_RULES.md` Output). 프레임워크 문서
  영어 전환: `docs/INDEX.md`, `docs/AGENT_MAINTENANCE.md`,
  `skills/SKILL_CONTRACT.md`.
- 파일/폴더명 영어 전환: `01_youtube_production_workflow.md`,
  `planning_research/` 및 내부 문서 2개. 영어 파일명 규칙을 File Rules에 추가.
- 구 CURRENT_TASK 문서를 이 파일로 통합하고 삭제. doccheck 기준과 참조 갱신.
- 결정적 가드레일 추가: `.claude/settings.json` + `tools/guard/agent_guard.py`
  (PreToolUse 차단 + Stop 시 doccheck 강제). 차단/허용/루프방지 분기
  단위 테스트 완료. 상세는 `tools/README.md`의 guard 절.
- git 계층 강제 추가: `.githooks/pre-commit`(doccheck), `.gitattributes`,
  `--no-verify` 우회 차단. 이 사본에는 `core.hooksPath` 설정 완료.
- `CLAUDE.md`에 Cowork용 평문 로드 지시 추가(@ import 미확장 보완 완결).
- 새 원본 백업 확인 규칙을 File Rules에 추가. Codex/Gemini 사용자 설정
  템플릿을 `tools/guard/`에 배치(저장소 강제 불가, 사용자 1회 적용).

## 다음 작업

- 새 원본이 들어오면 활성 작업 카드부터 작성한다.
- 새 소스가 없으면 편집 산출물을 만들지 않는다.
- 구조 변경을 더 할 때만 `PROJECT_RULES.md`, `docs/AGENT_MAINTENANCE.md`를 읽는다.
- 보류(사용자 결정으로 연기): 동시 세션 커밋 조율 규칙화(우선 습관으로
  운용: 편집 전 git status 확인), 스킬의 네이티브 `.claude/skills/` 이전
  (실제 영상 작업에서 수동 라우팅이 불편할 때 재검토).
- 가드레일 실사용 검증 대기: Claude Code 실세션에서 `/hooks`로 등록 확인 후
  차단 1건을 실제로 유발해 본다. `py -3` 런처가 없으면
  `.claude/settings.json`의 명령을 사용 가능한 Python으로 바꾼다.

## 주의

- 파일 쓰기 후 NUL 바이트와 핵심 내용을 확인한다.
- 샌드박스(Linux 마운트)에서 축소 저장된 파일 꼬리가 NUL로 보일 수 있다.
  검증은 에이전트가 직접 한다: 꼬리 NUL을 제거한 사본을 만들어 중간 NUL이
  없음을 확인(실손상 판별)한 뒤, 그 사본으로 doccheck를 실행한다.
- 같은 목표가 3회 실패하면 Stop Rule에 따라 멈춘다.
- 삭제된 일회성 보고서 원문은 Git 이력 복구를 전제로 하지 않는다.

## 중단 조건

- 활성 작업 카드 없이 편집 산출물(컷리스트, XML, EDL, 러프컷)을 만들려는 경우.
- 같은 정합성 문제가 세 번 반복되는 경우.
- 파일 손상이 반복되는데 검증 없이 계속 쓰려는 경우.
