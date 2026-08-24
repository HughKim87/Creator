# 저장소 역할 분리 단계 3 설계

- 목적: 현재 Creator 저장소에서 Core 유지보수 책임을 제거하고 영상 제작 Host 소비 저장소로 전환한다.
- 읽는 시점: 저장소 역할 분리 단계 3을 실행·검토·재개할 때.
- 책임: 작업 에이전트가 Host 계약·도메인 route·Creator gate를 유지하고 사용자가 실제 영상 사용을 확인한다.
- 상태: 활성 단계 설계.
- 관련 권위: `REPOSITORY_ROLE_SEPARATION_DESIGN.md`, `REPOSITORY_ROLE_SEPARATION_STAGE_0.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`.
- 문서 분류: `phase-design`
- phase ID: `STAGE_3`
- lifecycle: `in_progress`
- optional evidence owner: 실제 영상 사용 결과는 사용자 운영이 소유하며 `startup-required 아님`.
- 첫 다음 행동: `PROJECT_RULES.md`의 소비 역할과 경계를 영상 Host로 재작성한다.
- 종료 조건: Host 계약·Creator gate·도메인 route가 통과하고 Maintainer 책임 경로가 제거된 두 Creator commit이 clean이면 완료한다.

## Entry gate

- 새 Maintainer 단계 2 commit `9165b3c`과 clean clone이 `pass`다.
- `scripts/clone_conformance.py`의 owner와 복구 commit이 단계 0 분리표에 있다.
- 보호 경로는 모든 수정·검색·Git 명령에서 제외한다.

## 변경 범위

- Host 계약과 개요: `PROJECT_RULES.md`, `README.md`, `SESSION_HANDOFF.md`, `pyproject.toml`
- Creator gate: `scripts/bootstrap.py`, `scripts/run_test_inventory.py`, `scripts/verify.py`
- pipeline 회귀: `extension/tests/test_verification_pipeline.py`
- 제거: `scripts/clone_conformance.py`
- 분리 설계와 단계 상태

## 제외 범위

- `.agents/skills/**`와 그 기능 재설계
- `extension/`의 pipeline test 외 도메인 코드·문서·규칙 변경
- Core 코드·gitlink·`.gitmodules` 변경
- 보호 경로 접근과 실제 영상 사용 테스트
- 원격·폴더 이동

## 구현 절차

1. 소비 계약을 `host`로 바꾸고 Core 변경·push 책임을 제거한다.
2. README와 handoff를 영상 제작 Host 목적·상태로 갱신한다.
3. bootstrap과 dependency 선언을 Creator Runtime 기준으로 축소한다.
4. verify와 inventory에서 Core 유지보수·clean clone 책임을 제거한다.
5. pipeline test를 Host gate 계약으로 재작성한다.
6. Host 계약·route 관련 검사 뒤 첫 Creator commit을 만든다.
7. 검증된 Maintainer 전용 `scripts/clone_conformance.py`를 제거하고 관련 참조 0을 확인해 두 번째 commit을 만든다.

## Slice gates

- 계약: `consumer_role: host`, 보호 경로와 `shared_data v1` 요구 유지.
- 경계: Creator 활성 정책·상태·실행기에서 Core 수정·push·Maintainer Runtime 책임 0.
- 기능: Extension·Skills·Node·thumbnail 경로 유지.
- 검증: Host consumer gate와 Creator inventory·artifact gate `pass`.
- 정리: `clone_conformance.py`와 inbound reference 0, 복구 commit `69257b3`.

## Exit gate

- 두 Creator commit의 경로가 단계 3의 두 논리적 경계와 일치한다.
- Creator와 Core 작업 트리가 clean이다.
- 실제 영상 사용성은 자동 통과로 주장하지 않는다.
- 단계 4 전에 두 저장소 통합 마감 범위를 보고한다.

## 복구와 중단

- Host gate 실패 시 첫 Creator commit을 완료로 주장하지 않고 실패한 계약 표면만 교정한다.
- 제거 뒤 참조가 남으면 두 번째 commit을 만들지 않고 파일을 유지한다.
- 보호 경로나 Core 변경이 필요해지면 즉시 중단한다.
