# 저장소 역할 분리 단계 1 설계

- 목적: 영상 도메인에 의존하지 않는 독립 Agent Core Maintainer 로컬 후보를 구성한다.
- 읽는 시점: 저장소 역할 분리 단계 1을 실행·검토·재개할 때.
- 책임: 작업 에이전트가 단계 0 분리표에 따라 최소 후보를 만들고 사용자가 구조 변경과 다음 단계 전환을 확인한다.
- 상태: 활성 단계 설계.
- 관련 권위: `REPOSITORY_ROLE_SEPARATION_DESIGN.md`, `REPOSITORY_ROLE_SEPARATION_STAGE_0.md`, `core/docs/CONSUMER_GUIDE.md`, `SESSION_HANDOFF.md`.
- 문서 분류: `phase-design`
- phase ID: `STAGE_1`
- lifecycle: `passed`
- optional evidence owner: 없음. 이 단계의 구조·검사 결과 외 자료는 `startup-required 아님`.
- 첫 다음 행동: 단계 1 결과를 보고하고 단계 2 전용 설계를 활성화한다.
- 종료 조건: 후보가 독립 Git commit에서 Maintainer 소비 계약·관련 gate·도메인 누출 0·clean 상태를 만족하고 최종 임시 경로로 이동하면 완료한다.

## Entry gate

- 단계 0 분리표와 사용자 확인이 `pass`다.
- 전체 설계 fingerprint와 활성 단계 route가 일치한다.
- 정확한 staging 경로와 최종 임시 경로가 모두 존재하지 않는다.
- Core 기준 후보는 기존 gitlink `e1c7c63`이며 Core 코드는 변경하지 않는다.

## 변경 범위

- staging: `D:\AI Agent\Sandbox\Agent-Core-Maintainer\.stage1-maintainer-new`
- 최종 임시 경로: `D:\AI Agent\Sandbox\Agent-Core-Maintainer-New`
- 새 저장소 기본 파일, Maintainer 소비 계약, Core submodule, 최소 Runtime·검증기·tests
- 현재 Creator에서는 전체·단계 설계와 `SESSION_HANDOFF.md`만 갱신

## 제외 범위

- Creator의 기존 구현·정책·도메인 파일 변경·삭제
- Core 코드와 Core commit 변경
- `.agents/skills`, `.obsidian`, `extension/`, Node·영상·YouTube·게임 의존 복제
- 보호 경로 접근
- 원격 생성·push·main·태그·릴리스

## 구현 절차

1. staging에 독립 Git 저장소와 최소 파일을 만든다.
2. 기존 Core checkout에서 로컬 clone한 submodule을 연결하고 `.gitmodules`는 공식 Core 원격을 기록한다.
3. `consumer_role: maintainer`, 빈 도메인 route, 빈 보호 경로 계약을 작성한다.
4. Core 공개 CLI만 호출하는 preflight·inventory·verify·clean-clone 실행기를 작성한다.
5. 진입 route와 Maintainer pipeline 대응 tests를 작성한다.
6. 관련 검사 통과 뒤 정확한 파일만 stage하고 단계 1 로컬 commit을 만든다.
7. commit snapshot을 확인한 뒤 staging 전체를 최종 임시 경로로 이동한다.

## Slice gates

- 구조: 필요한 Consumer 파일과 Core gitlink가 있고 빈 미래 디렉터리가 없다.
- 경계: Host 도메인 경로·import·route와 Node Runtime 의존이 0이다. 제외 범위를 설명하는 문구는 운영 의존으로 세지 않는다.
- 계약: Core consumer gate와 진입·pipeline tests가 통과한다.
- Git: 단계 1 경로만 commit되고 Core submodule과 부모 작업 트리가 clean이다.
- 이동: source·target가 승인된 정확한 경로이며 target 충돌이 없다.

## Exit gate

- 새 후보가 `D:\AI Agent\Sandbox\Agent-Core-Maintainer-New`에서 독립 Git 저장소로 열린다.
- 단계 1 commit snapshot의 경로와 선택 검사가 현재 결과와 일치한다.
- Creator 기존 구현과 보호 경로에 변화가 없다.
- 단계 2 전환 전 결과를 사용자에게 보고한다.

## 복구와 중단

- commit 전 실패: 현재 작업이 만든 staging만 제거하고 Creator는 설계·상태 외 변경하지 않는다.
- commit 후 이동 전 실패: staging의 독립 Git commit을 유지하고 원인을 보고한다.
- 이동 실패: source와 target의 실제 위치를 다시 확인하고 둘 중 하나만 존재할 때 해당 저장소를 유지한다.
- Core·Creator·보호 경계를 넘어야 하면 즉시 중단하고 범위 확대를 보고한다.

## 차단 해소와 결과

- 이전 차단의 재시작 조건을 충족해 사용자 지시로 재개했다.
- 교정된 첫 행동은 명령과 종료 코드 조건, 성공 시 갱신할 상태 절을 각각 분리한다.
- consumer verify 통과 뒤에만 후보 commit을 갱신했고 clean clone을 한 번 실행해 통과했다.
- 후보 commit: `44d99d1`; Core gitlink: `e1c7c63`.
- 최종 임시 경로: `D:\AI Agent\Sandbox\Agent-Core-Maintainer-New`; 이동 후 clean·진입 파일·Runtime preflight를 확인했다.
