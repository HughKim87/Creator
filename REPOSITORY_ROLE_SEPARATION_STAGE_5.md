# 저장소 역할 분리 단계 5 설계

- 목적: 검증된 Creator와 Maintainer 후보를 최종 로컬 폴더 이름으로 전환한다.
- 읽는 시점: 저장소 역할 분리 단계 5를 실행·검토·복구할 때.
- 책임: 작업 에이전트가 정확한 source·target·clean 상태를 확인하고 승인된 두 폴더만 이동한다.
- 상태: 활성 단계 설계.
- 관련 권위: `REPOSITORY_ROLE_SEPARATION_DESIGN.md`, `REPOSITORY_ROLE_SEPARATION_STAGE_4.md`, `SESSION_HANDOFF.md`.
- 문서 분류: `phase-design`
- phase ID: `STAGE_5`
- lifecycle: `in_progress`
- optional evidence owner: 이동 전후 경로 조회 결과는 실행 증거이며 `startup-required 아님`.
- 첫 다음 행동: 두 저장소의 clean 상태와 source·target 충돌을 대조한다.
- 종료 조건: 두 폴더가 최종 경로에서 동일 commit·Core gitlink·진입 파일을 유지하면 완료한다.

## Entry gate

- Creator 단계 4 commit과 새 Maintainer 단계 2 commit이 clean이다.
- 두 source가 `D:\AI Agent\Sandbox` 바로 아래에 존재한다.
- `Creator` target는 없고 최종 Maintainer target는 첫 이동으로 비워진다.

## 정확한 이동

| 순서 | source | target |
|---:|---|---|
| 1 | `D:\AI Agent\Sandbox\Agent-Core-Maintainer` | `D:\AI Agent\Sandbox\Creator` |
| 2 | `D:\AI Agent\Sandbox\Agent-Core-Maintainer-New` | `D:\AI Agent\Sandbox\Agent-Core-Maintainer` |

## 제외 범위

- 저장소 내부 파일별 이동·복사·삭제
- 보호 경로 열거·읽기
- Core·Git 이력·원격 변경
- 다른 `D:\AI Agent\Sandbox` 항목 이동

## 실행 절차

1. resolved source·target가 위 표와 정확히 일치하는지 대조한다.
2. 두 저장소 status clean, Core status clean, `.git/index.lock` 부재를 확인한다.
3. 부모 경로에서 첫 source를 `Creator`로 이동한다.
4. 같은 명령 안에서 두 번째 source를 비워진 Maintainer target로 이동한다.
5. 새 경로에서 각 root·HEAD·Core gitlink·진입 파일을 대조한다.

## Slice gates

- 경로: source·target 네 절대경로가 표와 일치한다.
- Git: 이동 전 두 저장소와 Core가 clean이다.
- 충돌: `Creator` target가 없고 두 번째 target는 첫 이동 source와 같다.
- 이동: source는 사라지고 target 두 곳만 존재한다.

## Exit gate

- `Creator`가 Host 계약과 Creator commit을 유지한다.
- 최종 `Agent-Core-Maintainer`가 Maintainer 계약과 Maintainer commit을 유지한다.
- 두 Core gitlink와 진입 파일이 새 경로에서 해석된다.
- 단계 6 원격 반영은 별도 승인 전 `not_run`이다.

## 복구와 중단

- 첫 이동만 성공하면 `Creator`를 원래 source로 되돌리고 두 번째 이동을 하지 않는다.
- 두 번째 이동 실패 시 두 source의 실제 위치를 보고하고 이름 충돌을 추측으로 해결하지 않는다.
- 이동 후 Git 상태가 달라지면 원래 이름으로 복구하고 단계 5를 완료로 주장하지 않는다.
