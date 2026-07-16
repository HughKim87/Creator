# 프로젝트 재구축 핸드오프

- 역할: 채팅 기억 없이 다음 세션이 검증된 체크포인트에서 재개하는 단일 상태 문서.
- 기준: 이 문서를 포함한 `origin/feature/refactoring` 최신 커밋.
- 읽기 순서: `AGENTS.md` -> `PROJECT_RULES.md` -> 이 문서 ->
  `docs/rebuild/AGENT_EXECUTION_PLAN.md` -> 승인된 현재 단계 문서.

## 현재 상태

- Stage 00: 완료·독립 검증 PASS. 기준선은 `docs/rebuild/stage-00/STAGE_REPORT.md`.
- Stage 01: 2026-07-17 사용자 승인 로컬 QA 기준 완료. 보고서는
  `docs/rebuild/stage-01/STAGE_REPORT.md`.
- 검증: 실제 Windows pre-commit `0`, doctor/full `0`, 전체 45개, fast 42개,
  필수 부정 시나리오 18개·21개 PASS, 독립 QA와 최종 문서 재감사 PASS.
- 보호 상태: staged 금지 경로 0, `backup/` worktree/index 변경 0, 사용자 데이터 접근·저장 0.
- 실제 구현은 루트 `pyproject.toml`, `uv.lock`, `src/`, `tests/`, 훅, CI에 누적한다.
  구축 설계·분석·단계 기록은 `docs/rebuild/`에만 둔다.

## 사용자 결정과 후속 게이트

- clean-clone과 원격 CI 실행 이력은 초기 Stage 01 완료 조건에서 제외했다.
- 첫 수직 기능 이식 전 또는 기본 브랜치 통합 전 중 먼저 도래하는 시점에 실행한다.
- Stage 02는 미착수다. 사용자 승인 전에는 시작하지 않는다.

## 해결된 실패 원장

| objective | attempts | confirmed result/cause | count | next condition |
|---|---:|---|---:|---|
| Windows 실제 훅 | 127, 127, 127, 0 | MSYS 확장자 제거를 suffix 보정 후 `cygpath` 변환해 해결 | 0 | 회귀 테스트 유지 |
| 중첩 훅 테스트 격리 | 9, 9, 0 | 격리 PATH에서 빠진 `cygpath`를 결정적 fixture로 제공해 해결 | 0 | 부모 셸과 무관한 fixture 유지 |
| Stage 01 부정 QA | 누락, 21 PASS | 18개 번호 매트릭스와 완전성 가드로 해결 | 0 | 새 필수 검사와 테스트를 함께 변경 |

## 다음 행동

1. 사용자가 Stage 02 착수를 승인할 때만
   `docs/rebuild/stage-02/AGENT_STAGE_02_DOMAIN_CONTRACTS.md`를 읽는다.
2. 착수 전 `workflow doctor --json`과 `workflow check --scope full --json`을 재실행한다.
3. 후속 통합 게이트 시 이 체크포인트에서 clean-clone과 원격 CI 결과를 기록한다.

다음 세션 시작 문구: `PROJECT_RULES.md와 SESSION_HANDOFF.md를 읽고 현재 승인된 단계만 진행해.`
