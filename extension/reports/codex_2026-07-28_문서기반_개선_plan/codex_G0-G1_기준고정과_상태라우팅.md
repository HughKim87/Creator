# G0-G1 — 기준 고정과 상태 라우팅

- 역할: master plan의 G0·G1 세부 실행 절차
- 읽는 시점: master 단계 표에서 G0~G1이 `진행 중`일 때만
- 상태 owner: 상위 [master plan](../codex_2026-07-28_문서기반_지시준수와_워크트리상태관리_개선안.md)
- 이 문서는 현재 진행 상태를 소유하지 않는다.
- 완료 조건: G1 커밋과 성공 게이트를 master에 기록
- 만료 조건: G1 완료 후 재실행하지 않고 검증 참고용으로만 유지

## G0 — 기준 상태 고정

### 목표

첫 변경 전에 사용자 의도, 제어 문서, 두 worktree의 Git 상태를 하나의 실행 기준으로 확정한다.

### 순서

1. main에서 `AGENTS.md`, `PROJECT_RULES.md`, 선택된 상태 문서를 EOF까지 읽는다.
2. `core/rules/document-work.md`, `core/rules/version-control.md`, `core/rules/rule-governance.md`, `core/rules/core-change-control.md`를 EOF까지 읽는다.
3. 관련 세션 대화와 첨부 대화에서 다음 문장을 다시 확인한다.
   - AGENTS는 PROJECT_RULES를 찾기 위한 플랫폼 진입점일 뿐 프로젝트 규칙 router가 아님
   - AGENTS의 startup·분류·worktree 조건·`core/rules/*` 직접 링크 금지
   - PROJECT_RULES가 상태 선택과 세분화 규칙 routing을 모두 소유
   - ainotebook SESSION 변경을 전용 상태로 이전
4. 핵심 문장을 `명시적 사용자 지시 / 프로젝트 규칙 / 에이전트 제안 / 추론`으로 분류한다.
5. 첨부 대화의 “AGENTS가 공통 router”와 “SESSION은 항상 unstaged” 문구는 에이전트 제안으로 표시하고 최신 사용자 지시로 덮어쓰지 않는다.
6. main과 ainotebook의 worktree, branch, HEAD, staged, unstaged, untracked를 측정한다.
7. 제거된 6개 파일 변경을 대화 기록에서 재구성한다.
8. 현재 stash는 2026-07-27 영상 편집 자료로 확인됐으므로 제거된 6개 파일의 recovery source로 사용하지 않는다.
9. 재구성한 변경을 곧바로 적용하지 말고 현재 파일과 항목별로 비교한다.
10. master 2절과 값이 다르면 master를 갱신하고 중단 조건을 판단한다.

### 기록 형식

master에 다음 표를 한 번만 추가한다.

| 문서 | EOF | 현재 적용 조항 | 최신 사용자 지시와 충돌 |
|---|---|---|---|
| 경로 | yes/no | 짧은 요약 | 없음 또는 충돌 내용 |

별도 권위 표에는 `화자 / 분류 / 현재 효력 / 반영 위치`만 남긴다. 원문을 복사하지 않는다.

### G0 성공 게이트

- 모든 제어 문서의 EOF 확인이 있다.
- 최신 사용자 지시 불변조건 8개가 유지된다.
- Git 상태가 재측정됐다.
- 제거된 변경의 복구 가능·불가능 범위가 구분됐다.
- 아직 restore·stage·commit이 없다.

### G0 기준 커밋

검증된 plan 문서 5개와 갱신된 `SESSION_HANDOFF.md`만 exact path로 검토한다. 현재 대화 또는 다음 세션에서 해당 commit에 대한 승인이 확인된 경우:

`docs(plan): 지시 준수 개선 계획과 인수인계 고정`

커밋 후 master의 G0 행에 hash를 기록한다. 이 commit이 없으면 G1을 시작하지 않는다.

## G1 — PROJECT_RULES 중심 상태 라우팅

### 사전 승인

이 단계는 `core/rules/rule-governance.md`와 core test 변경을 포함하므로 현재 대화의 exact core 변경 승인이 필요하다. 없으면 진행하지 않는다.

### 예상 변경 대상

- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_RULES.md`
- `core/rules/rule-governance.md`
- `core/tests/test_rule_routing.py`
- `extension/tests/test_claude_entrypoint.py`
- 필요할 때만 worktree 상태 선택 전용 테스트 1개

다른 파일이 필요해지면 master 범위를 먼저 갱신한다.

### 구현 요구

1. AGENTS는 Codex가 PROJECT_RULES를 찾기 위한 최소 정적 진입점만 제공한다.
2. CLAUDE는 Claude가 PROJECT_RULES를 불러오기 위한 최소 정적 진입점만 제공한다.
3. AGENTS와 CLAUDE에서 startup 순서, 작업 분류, worktree 조건, `core/rules/*`, extension owner 링크를 제거한다.
4. PROJECT_RULES가 항상 적용되는 최소 정책과 startup 순서를 소유한다.
5. PROJECT_RULES가 quick·standard·controlled 작업 분류를 소유한다.
6. PROJECT_RULES가 `git rev-parse --show-toplevel`에 해당하는 정규화된 repository root의 마지막 디렉터리명을 기준으로 상태 문서를 선택한다.
7. root 디렉터리명이 정확히 `ainotebook`이면 `extension/work/AINOTEBOOK_WORKTREE_STATE.md`만 읽는다.
8. 그 외에는 `SESSION_HANDOFF.md`만 읽는다.
9. 두 상태 문서를 동시에 읽지 않는다.
10. PROJECT_RULES가 작업 trigger에 따라 필요한 `core/rules/*`와 extension owner만 연결한다.
11. 모든 활성 세분화 규칙은 PROJECT_RULES에서 정확히 한 번만 라우팅한다.
12. rule-governance의 단일 router를 AGENTS가 아니라 PROJECT_RULES로 수정한다.

### 검증

- AGENTS·CLAUDE에 worktree 조건·작업 분류·`core/rules/*` 링크 0건
- AGENTS·CLAUDE의 프로젝트 문서 링크는 PROJECT_RULES 포인터만 존재
- PROJECT_RULES에 배타적 상태 선택 1개
- Windows separator·대소문자 정규화 뒤 root basename을 사용하며 branch 이름만으로 분기하지 않음
- PROJECT_RULES에서 모든 활성 `core/rules/*` route가 정확히 1개
- extension entry route도 PROJECT_RULES가 소유
- 선택 대상 두 파일 존재
- 진입점 순환 참조 0건
- strict UTF-8, NUL 0, trailing whitespace 0
- core rule routing test
- Claude entrypoint test
- 변경한 core에 필요한 통합 gate

### G1 성공 게이트

- main 시뮬레이션은 SESSION 하나를 선택한다.
- ainotebook 시뮬레이션은 전용 상태 하나를 선택한다.
- AGENTS·CLAUDE는 프로젝트 규칙이나 조건을 소유하지 않는다.
- PROJECT_RULES만 startup·분류·상태 선택·세분화 규칙 routing을 소유한다.
- exact staged 목록에 승인된 파일만 있다.

### 커밋

`docs(core): 워크트리 상태 선택을 PROJECT_RULES로 일원화`

커밋 후 object, 변경 경로, 보호 경로 0건, 두 worktree status를 확인하고 master의 G1 행을 완료로 갱신한다.
