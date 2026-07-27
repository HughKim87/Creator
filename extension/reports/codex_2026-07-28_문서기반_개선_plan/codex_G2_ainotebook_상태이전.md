# G2 — ainotebook 상태 이전

- 역할: master plan의 G2 세부 실행 절차
- 읽는 시점: G0~G1 완료 후 master에서 G2가 `진행 중`일 때만
- 상태 owner: 상위 [master plan](../codex_2026-07-28_문서기반_지시준수와_워크트리상태관리_개선안.md)
- 이 문서는 ainotebook의 현재 영상 상태를 소유하지 않는다.
- 완료 조건: 외부 recovery 검증, 전용 상태 문서 커밋, SESSION local diff 제거, 승인된 main 병합
- 만료 조건: G2 완료 후 검증 참고용으로만 유지

## 목표

ainotebook의 로컬 `SESSION_HANDOFF.md` 변경을 `extension/work/AINOTEBOOK_WORKTREE_STATE.md`로 의미 손실 없이 이전하고 현재 상태 owner를 하나로 만든다.

## 사전 조건

- main에서 G0·G1 커밋 성공
- ainotebook worktree와 `codex/ainotebook` branch 확인
- staged 변경 0건
- `SESSION_HANDOFF.md`와 전용 상태 문서를 EOF까지 읽음
- 보호 `inputs/`·`outputs/`에 접근하지 않음
- main에만 존재하는 commit 목록을 다시 출력하고 병합 범위가 사용자 목표와 일치함

## 외부 recovery copy

ainotebook 파일을 수정·restore·stage·merge하기 전에 다음 두 파일을 저장소 밖 한 디렉터리에 복사한다.

- `SESSION_HANDOFF.md`
- `extension/work/AINOTEBOOK_WORKTREE_STATE.md`

권장 destination은 `C:\Users\Hugh\Documents\ainotebook-backups\<timestamp>-document-routing`이다. 경로 생성이나 쓰기에 별도 권한이 필요하면 mutation 전에 요청한다.

요구 사항:

- source와 destination 파일 수 일치
- 각 파일 SHA-256 일치
- backup 경로는 project 문서·규칙·runtime에서 링크하거나 참조하지 않음
- backup이 없어도 개선된 프로젝트가 정상 작동
- 이 recovery copy는 merge 실패 복구용이며 active owner가 아님

## 이전 순서

1. branch 기준 `SESSION_HANDOFF.md` diff를 읽는다.
2. diff를 다음 의미 단위로 분해한다.
   - 갱신일
   - 현재 작업
   - 상태
   - blocker·사용자 결정
   - 검증된 현재 상태
   - 실패 기록
   - 첫 다음 행동
   - 채널 적용 범위·URL·ID·목적·혼용 금지·패키지 경계
   - 첨부 대화의 에이전트가 추가한 Git 경계 문구
3. 각 의미 단위가 전용 상태 문서의 한 위치에만 존재하는지 대조한다.
4. 누락된 의미를 전용 상태 문서에 추가한다.
5. `SESSION_HANDOFF.md는 항상 unstaged` 문구는 사용자 지시가 아니라 첨부 대화의 에이전트 제안으로 분류한다.
6. 권장안은 이 문구를 상태 owner의 활성 정책으로 이전하지 않는 것이다. 누락으로 숨기지 말고 master의 G2 실행 기록에 `assistant proposal / not adopted / version-control owner 사용`으로 처분을 남긴다.
7. 산출물 경로가 현재 존재하지 않는다는 이유로 상태 문구를 삭제·수정하지 않는다.
8. 상태 검증 수준을 다음 단계로 구분한다.
   - reported
   - generated
   - structure-validated
   - tool-validated
   - app-validated
   - user-approved
9. 내용 parity와 Git 문구 처분이 확인된 뒤에만 `SESSION_HANDOFF.md`를 branch 기준 상태로 되돌린다.
10. 전용 상태 문서만 exact path로 stage한다.

## 검증

| 검사 | 통과 조건 |
|---|---|
| 의미 단위 parity | SESSION local diff의 모든 단위가 전용 상태에 한 번씩 존재 |
| 단일 owner | 전용 상태만 ainotebook 현재 상태 owner를 선언 |
| SESSION status | branch 기준 local diff 없음 |
| protected data | 접근·stage·commit 0건 |
| 문서 품질 | UTF-8, NUL 0, trailing whitespace 0, 링크 유효 |
| recovery | 외부 source·destination count와 SHA-256 일치 |
| 정책 처분 | assistant 제안 Git 문구가 활성 정책으로 승격되지 않음 |

## 성공 게이트

- `git status`에서 `SESSION_HANDOFF.md`가 사라진다.
- `AINOTEBOOK_WORKTREE_STATE.md`만 승인된 신규 파일로 stage된다.
- 사용자 지시·실패·blocker·다음 행동 의미 손실이 0건이다.
- 상태 문서 내용은 산출물 실재 검증으로 임의 재해석되지 않았다.
- 외부 recovery copy는 검증됐으며 프로젝트가 이를 참조하지 않는다.

## 커밋

ainotebook worktree에서:

`docs(worktree): ainotebook 현재 상태를 전용 owner로 이전`

커밋 후 main에는 변경이 없고 ainotebook의 의도하지 않은 local changes가 0인지 확인한다.

## main 병합

1. `git log --oneline codex/ainotebook..main`으로 병합 범위를 다시 출력한다.
2. G0·G1뿐 아니라 기존 main-only commit도 포함되므로 사용자 목표와 맞는지 확인한다.
3. 범위가 승인되지 않았거나 관련 없는 commit이 있으면 merge하지 않고 보고한다.
4. 승인 범위가 확인되면 ainotebook에서 main을 merge한다.
5. conflict가 나면 자동으로 restore하지 않는다. 외부 recovery copy를 보존하고 실패 objective·원인·재개 조건을 master에 기록한다.
6. merge 후 ainotebook에서 G1 commit ancestry, 전용 상태 선택, SESSION 비선택을 검증한다.

G2는 전용 상태 commit과 main merge 결과가 모두 검증된 뒤에만 완료로 바꾼다.
