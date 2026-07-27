# G5 — 통합 검증과 최종 보고

- 역할: master plan의 G5 세부 실행 절차
- 읽는 시점: G0~G4 완료 후 master에서 G5가 `진행 중`일 때만
- 상태 owner: 상위 [master plan](../codex_2026-07-28_문서기반_지시준수와_워크트리상태관리_개선안.md)
- 이 문서는 이전 단계의 현재 상태를 복제하지 않는다.
- 완료 조건: 전체 성공 게이트·단계별 커밋·최종 보고 확인
- 만료 조건: 최종 보고 후 historical execution guide로 전환

## 목표

두 worktree의 실제 동작과 Git 상태를 재검증하고, 다음 세션이 채팅 기억 없이도 하나의 상태 owner에서 작업을 이어받게 한다.

## 검증 순서

1. main의 branch, HEAD, staged, unstaged, untracked를 확인한다.
2. ainotebook의 branch, HEAD, staged, unstaged, untracked를 확인한다.
3. 단계별 commit hash와 실제 변경 경로를 대조한다.
4. 보호 `inputs/`·`outputs/`의 stage·commit 건수가 0인지 확인한다.
5. AGENTS·CLAUDE에 PROJECT_RULES 포인터 외 규칙·분류·라우팅이 없는지 확인한다.
6. PROJECT_RULES가 모든 활성 세분화 규칙을 정확히 한 번씩 연결하는지 확인한다.
7. Obsidian graph 기준 PROJECT_RULES→활성 core rule edge가 완전·유일하고 AGENTS 직접 edge가 0인지 확인한다.
8. PROJECT_RULES의 main·ainotebook 상태 선택을 각각 시뮬레이션한다.
9. 각 worktree에서 현재 상태 owner가 하나인지 확인한다.
10. ainotebook SESSION local diff가 없는지 확인한다.
11. ainotebook branch ancestry에 승인된 main merge와 G1 commit이 존재하는지 확인한다.
12. 외부 recovery copy가 project 파일에서 참조되지 않는지 확인한다.
13. Core 전체 테스트를 실행한다.
14. Extension 전체 테스트를 실행한다.
15. 통합 maintenance를 실행한다.
16. 문서 UTF-8, NUL, trailing whitespace, 링크를 확인한다.
17. push 이력이 없는지 확인한다.

## 최종 성공 게이트

| 영역 | 통과 조건 |
|---|---|
| 지시 준수 | 최신 사용자 지시 불변조건이 master와 실제 구조에 일치 |
| 진입점 | AGENTS·CLAUDE는 PROJECT_RULES만 가리키는 플랫폼 포인터 |
| 규칙 라우팅 | PROJECT_RULES만 작업 분류와 세분화 규칙 route 소유 |
| Obsidian graph | PROJECT_RULES→활성 core rule edge 완전·유일, AGENTS 직접 edge 0 |
| 상태 라우팅 | PROJECT_RULES가 worktree별 owner 하나 선택 |
| 상태 이전 | ainotebook SESSION diff 0, 전용 상태 의미 누락 0 |
| recovery | 외부 copy 해시 검증, project 의존·링크 0 |
| branch 정합 | 전용 상태 commit 후 승인된 main merge와 G1 ancestry 확인 |
| Git 안전 | 관련 없는 변경·보호 경로·무승인 restore 0 |
| 회귀 | Core·Extension·통합 gate 모두 실제 통과 |
| 커밋 | 단계별 로컬 커밋 확인 |
| 외부 효과 | push·publish·외부 변경 0 |

하나라도 실패하면 완료로 보고하지 않는다. 실패한 objective, attempt, 원인, 연속 횟수, 재개 조건을 master에 기록한다.

## 최종 보고 문서

사용자가 요청한 `codex_` 접두어를 사용해 `extension/reports/`에 최종 보고 1개를 만든다.

최종 보고에는 다음만 남긴다.

1. 최초 목적과 최종 판정
2. 단계별 변경과 commit hash
3. 중요도·필요도별 개선 항목의 완료 여부
4. 실행한 검증과 결과
5. 미실행 검증과 남은 사용자 gate
6. 복구하지 못한 정보
7. 프로젝트 목적·구조 적합성 평가
8. 사용자 지시와 기존 규칙을 무시했던 원인에 대한 자체 복기
9. 다음 세션의 첫 행동

대화 원문, 파일별 diff 전문, 테스트 로그 전문은 복사하지 않는다.

## 상태 문서 마감

- main의 현재 작업이 끝났다면 `SESSION_HANDOFF.md`에는 완료 상태와 첫 다음 행동만 남긴다.
- ainotebook에는 `AINOTEBOOK_WORKTREE_STATE.md`만 현재 상태를 소유하게 한다.
- 단계 문서의 진행 상태를 복사하지 않는다.
- completed detail은 Git과 최종 보고에 맡긴다.
- 다음 세션이 채팅 없이 시작할 수 있도록 선택된 상태 owner에 master 경로와 첫 다음 행동을 남긴다.

## 예정 커밋

최종 보고와 필요한 상태 owner 갱신을 exact path로 검토한 뒤:

`docs: 문서 기반 지시 준수 개선 최종 보고`

커밋 후 두 worktree 상태와 push 0건을 다시 확인하고 master의 G5 행을 완료로 바꾼다.
