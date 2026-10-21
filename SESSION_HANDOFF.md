# Creator 현재 상태 안내

- 목적: main 유지보수 상태와 이전 대기 중인 legacy 브랜치 상태로 안내한다. 영상 상태는 job 폴더가 소유한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤.
- 책임: main 유지보수 세션이 안내판을 유지하고 영상 작업 세션은 해당 job 상태만 갱신한다. 사용자가 결과와 외부 효과를 소유한다.
- 상태: 안내판. 작업별 현재 상태는 아래 표의 상태 파일이 소유한다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`의 「영상별 작업 공간과 상태」.
- 활성 전체 설계: 없음.
- 활성 단계 설계: 없음.
- handoff mode: `same-workspace`.

## 현재 단계

main의 공통 개발 상태는 state/main.md가 소유한다. 아래 다른 브랜치는 제거 승인 전까지 보존 중인 legacy 상태다. 새 영상은 extension/jobs/<job-id>/를 사용하며 이 표에 추가하지 않는다.

| 브랜치 | 상태 파일 |
|---|---|
| `main` | `state/main.md` |
| `codex/wardogs` | `state/wardogs.md` |
| `codex/TRYALLGAME` | `state/TRYALLGAME.md` |
| `codex/ainotebook` | `state/ainotebook.md` |
| `claude/dokkaebi` | `state/dokkaebi.md` |
| `codex/24HReplier` | `state/24HReplier.md` |

## 직전 게이트

- main의 단일 workspace 코드와 관련 검사 통과. 현재 후보·실측 한계·다음 승인 대상은 state/main.md를 따른다.

## 승인 상태

- 위임: main에 모든 재사용 개선 흡수, job·공용 runtime 구현과 관련 검증·로컬 커밋.
- 미위임: 기존 자료 이동·삭제와 worktree 제거. 대상별 승인 후 진행한다.

## 차단

- 구현 차단 없음. 자료 처분은 별도 승인 단계다.

## 알려진 위험

- before 태그는 Git 제외 자료를 복원하지 않는다. 기존 자료는 원위치 보존 중이다.
- 보존 중인 legacy 상태 파일은 해당 브랜치에만 있을 수 있다.

## 첫 다음 행동

1. 공통 유지보수는 state/main.md의 활성 단계와 다음 행동을 읽는다.
2. 영상 제작·재개는 명시된 job ID로 scripts/creator_job.py inspect를 실행하고 해당 job의 state.md를 읽는다.
3. legacy 자료를 처분하려면 extension/reports/workspace-consolidation-20261021.md의 대상과 복구 조건을 먼저 대조한다.

## 다음 세션 시작 prompt

시작 3문서 뒤 state/main.md를 읽는다. 영상 작업은 명시된 job 폴더만 이어서 읽고 다른 job 상태를 승계하지 않는다.
