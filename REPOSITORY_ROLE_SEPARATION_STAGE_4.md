# 저장소 역할 분리 단계 4 설계

- 목적: Creator와 새 Maintainer의 Core 연결·역할 문서·의존 방향을 대조해 로컬 역할 분리를 마감한다.
- 읽는 시점: 저장소 역할 분리 단계 4를 실행·검토·재개할 때.
- 책임: 작업 에이전트가 양쪽 공개 계약과 관련 gate를 대조하고 실제 영상 사용은 사용자 운영에 남긴다.
- 상태: 활성 단계 설계.
- 관련 권위: `REPOSITORY_ROLE_SEPARATION_DESIGN.md`, `REPOSITORY_ROLE_SEPARATION_STAGE_2.md`, `REPOSITORY_ROLE_SEPARATION_STAGE_3.md`.
- 문서 분류: `phase-design`
- phase ID: `STAGE_4`
- lifecycle: `passed`
- optional evidence owner: 실제 영상 사용 결과는 사용자 운영이 소유하며 `startup-required 아님`.
- 첫 다음 행동: 단계 4 결과를 보고하고 단계 5의 정확한 폴더 source·target를 확정한다.
- 종료 조건: 역할·의존·Core 연결과 관련 gate가 모두 통과하고 두 저장소 최종 상태가 commit되면 완료한다.

## Entry gate

- Maintainer 단계 2 commit과 clean clone이 `pass`다.
- Creator 단계 3의 두 commit과 Host 관련 gate가 `pass`다.
- 양쪽 Core 작업 트리에 변경이 없다.

## 변경 범위

- 양쪽 Core gitlink·`.gitmodules`·역할 문서의 읽기 전용 대조
- Creator 분리 설계 route와 `SESSION_HANDOFF.md` 마감
- 필요할 때만 새 Maintainer `SESSION_HANDOFF.md`의 현재 상태 문구 교정

## 제외 범위

- Core·gitlink·`.gitmodules` 변경
- Creator 도메인 구현과 Maintainer 검증기 변경
- 실제 영상 사용 테스트와 추가 clean clone
- 보호 경로·폴더 이동·원격 작업

## 실행 절차

1. 양쪽 Core remote path와 gitlink를 대조한다.
2. 각 저장소의 소비 역할과 반대 역할 운영 import·route를 검색한다.
3. 역할별 README·정책·handoff의 실제 상태를 대조한다.
4. 변경 없는 Maintainer 단계 2 clean-clone 근거를 재사용한다.
5. Creator 최종 Host gate를 한 번 실행한다.
6. 최종 상태 문서에 결과를 반영하고 관련 local commit을 만든다.

## Slice gates

- Core 연결: 양쪽 `.gitmodules` path·URL과 gitlink가 일치한다.
- 역할: Maintainer는 `maintainer`, Creator는 `host` 계약 하나만 가진다.
- 의존: 두 부모 저장소가 서로의 경로·코드·상태를 import하지 않는다.
- 검증: Maintainer 단계 2 근거 유효, Creator 최종 Host gate `pass`.

## Exit gate

- Maintainer는 Core 유지보수만, Creator는 영상 작업만 소유한다.
- 두 저장소 작업 트리가 clean이다.
- 실제 영상 사용성은 `not_run`이며 사용자 운영 대상이다.
- 단계 5 폴더 이동 전에 정확한 source·target를 보고한다.

## 복구와 중단

- Core 연결이 다르면 수정하지 않고 어느 저장소가 틀렸는지 보고한다.
- 반대 역할 import가 발견되면 해당 owner에서만 제거하고 관련 gate를 다시 선택한다.
- 최종 gate 실패 시 폴더 이동을 시작하지 않는다.
