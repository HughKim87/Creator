# 저장소 역할 분리 단계 2 설계

- 목적: 새 Maintainer가 Core 최소 Python과 독립 commit snapshot에서 Creator 없이 재현되는지 확인한다.
- 읽는 시점: 저장소 역할 분리 단계 2를 실행·검토·재개할 때.
- 책임: 작업 에이전트가 최소 Runtime·독립성·snapshot 근거를 확인하고 단계 2 commit을 유지한다.
- 상태: 활성 단계 설계.
- 관련 권위: `REPOSITORY_ROLE_SEPARATION_DESIGN.md`, `REPOSITORY_ROLE_SEPARATION_STAGE_1.md`, 새 Maintainer `SESSION_HANDOFF.md`.
- 문서 분류: `phase-design`
- phase ID: `STAGE_2`
- lifecycle: `passed`
- optional evidence owner: 단계 1 clean clone 결과는 동일 구현의 선행 근거이며 `startup-required 아님`.
- 첫 다음 행동: 단계 2 결과를 보고하고 Creator Host 전환 범위를 적용한다.
- 종료 조건: 최소 Python gate, Creator 독립성, 단계 2 commit clean clone이 모두 통과하면 완료한다.

## Entry gate

- 단계 1 후보 commit `44d99d1`과 Core gitlink `e1c7c63`이 clean 상태다.
- 새 Maintainer 최종 임시 경로가 `D:\AI Agent\Sandbox\Agent-Core-Maintainer-New`다.
- 단계 1 consumer verify와 clean clone이 `pass`다.

## 변경 범위

- 새 Maintainer `SESSION_HANDOFF.md`의 단계 2 상태
- 단계 2 결과를 고정하는 새 Maintainer 로컬 commit
- 현재 분리 설계 route와 부모 `SESSION_HANDOFF.md`

## 제외 범위

- Core 코드·gitlink 변경
- Maintainer Runtime·dependency 설치
- Creator 구현·정책·보호 경로 접근
- 원격 생성·push와 실제 Host 사용 테스트

## 실행 절차

1. 설치된 Python 3.10 경로를 읽기 전용으로 찾는다.
2. Python 3.10에서 `scripts/verify.py`를 한 번 실행한다.
3. 새 Maintainer의 추적 파일에서 Creator 절대경로·Extension 운영 의존을 검색한다.
4. handoff를 실제 결과로 갱신하고 consumer verify를 먼저 통과시킨다.
5. 단계 2 상태 파일만 commit한다.
6. commit snapshot clean clone을 한 번 실행한다.

## Slice gates

- 최소 Runtime: Python 3.10 전체 Maintainer gate `pass`.
- 독립성: Creator 절대경로·`.agents/skills`·`extension/` 운영 의존 0.
- 상태 계약: handoff 갱신 뒤 consumer verify `pass`.
- Git: 단계 2 상태 경로만 commit되고 Core와 부모가 의도한 상태다.

## Exit gate

- 단계 2 commit의 clean clone에서 Core submodule과 Maintainer gate가 `pass`다.
- 새 Maintainer 작업 트리가 clean이다.
- 단계 3 착수 전에 Creator 변경 범위를 보고한다.

## 복구와 중단

- Python 3.10이 없으면 설치하지 않고 `blocked`로 보고한다.
- 최소 Runtime 실패 시 handoff commit과 clean clone을 실행하지 않는다.
- consumer verify 실패 시 commit을 만들지 않는다.
- clean clone 실패 시 단계 2 commit을 완료로 주장하지 않고 원인별 최소 검사로 돌아간다.
