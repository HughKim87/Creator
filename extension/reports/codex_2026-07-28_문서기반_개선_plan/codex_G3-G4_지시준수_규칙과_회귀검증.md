# G3-G4 — 지시 준수 규칙과 회귀 검증

- 역할: master plan의 G3·G4 세부 실행 절차
- 읽는 시점: G2 완료 후 master에서 G3~G4가 `진행 중`일 때만
- 상태 owner: 상위 [master plan](../codex_2026-07-28_문서기반_지시준수와_워크트리상태관리_개선안.md)
- 이 문서는 현재 진행 상태나 실패 횟수를 소유하지 않는다.
- 완료 조건: 최소 규칙 강화와 회귀 커밋 확인
- 만료 조건: G4 완료 후 검증 참고용으로만 유지

## G3 — 기존 규칙 owner 최소 강화

### 목표

새 장문 규칙이나 새 스킬을 만들지 않고, 기존 owner에 “읽었지만 무시한 실패”를 차단하는 실행 게이트를 추가한다.

### 사전 승인

core 규칙과 failure case 변경이므로 현재 대화의 exact core 변경 승인이 필요하다.

### 우선 검토 owner

- `core/rules/document-work.md`
- `core/rules/rule-governance.md`
- `core/rules/version-control.md`
- `core/failures/canonical-owner-and-document-drift.md`
- `core/failures/scope-and-authority-boundaries.md`

새 파일을 만들기 전에 위 owner로 해결 가능한지 확인한다.

### 필요한 불변조건

1. controlled 작업의 첫 mutation 전에 제어 문서 EOF와 적용 조항을 확인한다.
2. 최신 사용자 지시와 문서가 충돌하면 최신 사용자 지시를 기준으로 계획을 갱신한다.
3. 사용자가 의도 오해를 지적하면 현재 계획과 대기 중 mutation을 즉시 무효화한다.
4. 문서 대조와 새 성공 게이트가 끝나기 전에는 mutation을 재개하지 않는다.
5. 다른 세션의 미커밋 변경은 exact target, diff, 복구 수단, 승인 없이 restore하지 않는다.
6. 실행 checkpoint에는 목표·금지·owner·현재 단계만 기록하고 대화 원문을 복사하지 않는다.
7. 첨부 대화·보고서의 에이전트 답변은 사용자 지시와 화자를 분리하며 자동으로 정책 권위를 갖지 않는다.
8. 미완료 세션 종료 전 선택된 상태 owner에 현재 단계·blocker·첫 다음 행동을 갱신한다.

### 규칙 작성 경계

- 사용자 발언 원문과 감정 표현을 규칙에 복사하지 않는다.
- 이번 ainotebook 작업명이나 경로를 전역 불변조건에 넣지 않는다.
- 기존 조항을 단순 반복하지 않는다.
- 실패 원인·필수 행동·검증만 남긴다.
- 새 규칙 파일과 새 스킬은 만들지 않는다.

### G3 성공 게이트

- 기존 owner만 수정했다.
- 한 작업의 사실을 전역 규칙으로 승격하지 않았다.
- 중복 문장과 장문 사례가 없다.
- 사용자 교정 후 mutation 중단 조건이 명시됐다.
- 미커밋 변경 restore 보호 조건이 명시됐다.
- 사용자 발언과 에이전트 제안의 권위 분리 조건이 명시됐다.
- 미완료 세션의 handoff 갱신 조건이 명시됐다.

### 예정 커밋

`docs(core): 사용자 교정과 미커밋 변경 보존 게이트 강화`

## G4 — 자동 회귀

### 목표

규칙 문장이 존재하는지뿐 아니라 잘못된 구조가 다시 생기지 않는지 검증한다.

### 필수 시나리오

1. main root는 `SESSION_HANDOFF.md` 하나를 선택한다.
2. ainotebook root는 `AINOTEBOOK_WORKTREE_STATE.md` 하나를 선택한다.
3. 두 상태 문서를 동시에 선택하면 실패한다.
4. AGENTS·CLAUDE에 worktree 조건·작업 분류·규칙 route가 생기면 실패한다.
5. AGENTS·CLAUDE가 PROJECT_RULES 외 프로젝트 문서를 직접 연결하면 실패한다.
6. PROJECT_RULES에서 활성 `core/rules/*` route가 누락·중복되면 실패한다.
7. 선택 대상이 없으면 명시적으로 실패한다.
8. 상태 문서 두 개가 모두 single owner를 선언하면 실패한다.
9. controlled 계획에 사용자 교정 무효화 조건이 없으면 실패한다.
10. destructive Git 절차에 exact target·복구·승인 조건이 없으면 실패한다.
11. 외부 에이전트 제안을 사용자 지시로 취급하면 실패한다.
12. 미완료 단계인데 선택된 상태 owner에 checkpoint가 없으면 실패한다.

### 테스트 배치

- 기존 routing test에 자연스럽게 들어가면 그 파일을 확장한다.
- 별도 실행 입력이 필요할 때만 전용 테스트 파일 1개를 추가한다.
- 테스트를 맞추기 위해 운영 규칙을 중복하지 않는다.

### 검증

- 관련 단위 테스트
- Core 전체 테스트
- Extension 전체 테스트
- 통합 maintenance
- strict UTF-8
- NUL 0
- trailing whitespace 0
- Markdown 링크와 라우팅 owner 유일성
- Obsidian graph 기준 PROJECT_RULES→활성 core rule edge 완전성·유일성
- AGENTS→core rule 직접 edge 0건

### G4 성공 게이트

- 필수 시나리오가 모두 자동 검증된다.
- 미실행 검증은 통과로 기록되지 않는다.
- 테스트가 실제 파일 내용과 worktree 입력을 검사한다.

### 예정 커밋

`test(routing): 상태 owner와 지시 준수 회귀 추가`

각 커밋 후 exact path와 잔여 status를 확인하고 master의 G3~G4 행에 두 commit hash와 검증 결과를 기록한다.
