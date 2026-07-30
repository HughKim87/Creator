# 세션 핸드오프

- 갱신일: 2026-07-31
- 역할: ainotebook 이외 worktree의 현재 work·blocker·검증 상태·첫 다음 행동 단일 owner
- 현재 작업: 규칙 무손실 통합 개선 M0 규칙 계보·손실 감사
- 상태: `M0-S1` passed, `M0-S2` unstarted. 이번 세션은 Codex 작업의 직접 사용자 발언으로 프로젝트 방향과 설계·인계를 교정했으며 M0 계보 실행은 시작하지 않았다.
- 활성 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 활성 단계 설계: `extension/work/rule-preservation/M0_RULE_LINEAGE_AND_LOSS_AUDIT.md`
- M0 evidence: `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md`
- 선택 근거: `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md`
- 프로젝트 방향: `PROJECT_DIRECTION.md`
- 읽기 순서: `PROJECT_RULES.md` → 이 문서 → 활성 전체 설계 → 활성 단계 설계 → 다음 행동에 matching된 규칙
- handoff mode: `portable`; 필수 방향·설계·evidence와 승인된 규칙 변경을 이번 Git checkpoint에서 함께 보존한다.

## 직접 사용자 근거로 교정한 방향

관련 Codex 작업 3개와 현재 작업에서 에이전트 요약이 아닌 직접 사용자 발언을 대조했다.

| Codex task | 확인된 사용자 방향 |
|---|---|
| `019fa4d3-728d-7c03-91ef-67cb0628148e` | 반복 영상 작업, 지식 추출 뒤 문서 정리, clean clone 품질, 자동화, 설계→실행, 성공·실패 환류, 복잡성 감사, Core 이식 |
| `019fa9f6-3956-7ac3-8a87-a9461be04da3` | 단계별 자동 실행·gate·커밋, 불필요한 규칙 증가 감사, 위임 시 목표·의도 보존 |
| `019faf75-037f-7e92-ac69-420f40b82324` | 데이터 근거의 출처 분리, 문서 제거가 현재 정리 이니셔티브의 1차 목표, 제거는 선행 개선 종료 뒤 exact 승인 단계 |

- 기존 `PROJECT_DIRECTION.md`가 실제 유튜브 산출물을 단독 최상위 결과로 두고 Core 이식·재현 가능한 운영 기반을 후순위 수단으로 낮춘 해석은 사용자 직접 발언과 맞지 않아 교정했다.
- 현재 이니셔티브의 1차 목표는 역할이 끝난 문서 제거다. 의미 보존·규칙 통합·참조 해제·검증은 제거 전 선행 조건이다.
- M0~M3에서는 삭제·이동하지 않는다. M3 통과 뒤 exact 처분 목록을 사용자에게 승인받고 M4에서 한 번에 처분한다.

## 검증된 현재 상태

- branch `main`, 이번 checkpoint의 부모 HEAD는 `3810abc`이고 `origin/main`보다 11 commit ahead였다.
- 이번 checkpoint 범위는 tracked modified 7건·untracked 6건, 합계 13파일이다. 최종 방향·설계·규칙·회귀를 함께 커밋하며, 서로만 참조하던 대체 완료 임시 초안 2건은 작업 파일을 건드리지 않고 휴지통으로 제거했다.
- `M0-S1` corpus: `rule-surface` 19파일·9,650토큰, `normative-corpus` 37파일·18,433토큰(HEAD 18,010), candidate 1파일·675토큰.
- `rule-surface` 의미 78개, 19파일 전부 매핑, 미매핑 0. 파일당 최대 11개로 `D3` 12행 상한과 `D4` 400줄·30,000자 예산을 확정했다.
- 기존 `37파일·18,844단어`와 `19,519단어`는 재현되지 않아 후속 성공 기준에서 제외한다.
- 방향·설계 교정 뒤 Core 139개·Extension 132개 회귀, design budget, UTF-8·NUL·후행 공백·`git diff --check`가 통과했다.
- 사용자 지시에 따라 기존 작업 내용을 되돌리지 않고 Core 4경로를 이번 checkpoint에 포함했다. Core 139개·Extension 132개와 `maintenance-verify --allow-core-changes`가 통과했다.

## 이번 checkpoint와 후속 승인 경계

아래 rule-surface 5경로는 이번 checkpoint에 보존한다. 그중 `core/**`는 4경로이며, 이번 정리에서는 기존 작업 내용을 되돌리거나 재작성하지 않았다.

| 경로 | 상태 | SHA-256 / 판정 |
|---|---|---|
| `PROJECT_RULES.md` | checkpoint | `725beca47d5a8d53ce35817e7193459ea11f6002640a5c1858761845951794cd` |
| `core/rules/document-work.md` | checkpoint | `c29ba6d3796db5b08bf84f55e83fdd61796bb4d0f663dca468c774fac1f30a9b` |
| `core/rules/rule-governance.md` | checkpoint | `b5b68e8268da424b72a9c7b61539efd4583fc93b679d70da44f9f64b8334f63e` |
| `core/tests/test_rule_routing.py` | checkpoint | `1d618aa1ed5a71c5669a15eb5345867dc83b475ec6a96b5c7e9c75eb18b764c1` |
| `core/rules/staged-work-design.md` | checkpoint | `83d8dbe22e0e45c9910f346d2843130a7269c8b4cd5a94ae758df4cc17c453bb` |

- `rule-governance.md`의 숫자 상한 문장은 중단된 외부 에이전트 세션에서 추가됐지만, 이번 사용자가 작업 내용을 되돌리지 말고 현재 변경을 커밋하라고 지시해 checkpoint 범위에 포함했다.
- 이전 대화의 Core 승인은 현재 대화로 자동 승계되지 않는다. 후속 Core mutation은 exact 경로·이유·대안이 확정된 뒤 현재 대화에서 다시 승인받는다.
- 삭제·이동, dependency 설치, 외부 상태 변경, stage·commit·push는 별도 승인 전 수행하지 않는다.

## 중요 문서

| 경로 | 상태 | 역할 |
|---|---|---|
| `PROJECT_DIRECTION.md` | active reference-evidence | 직접 사용자 발언으로 교정한 장기 결과·판단 기준 |
| `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md` | active overall-design | 문서 제거 1차 목표, M0~M4 단계와 전체 gate |
| `extension/work/rule-preservation/M0_RULE_LINEAGE_AND_LOSS_AUDIT.md` | in-progress phase-design | M0 exact 범위·slice·gate |
| `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md` | optional reference-evidence | corpus·의미 단위·lineage·교차검증 판정 owner |
| `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md` | reported / unverified reference | 교차검증 대상 에이전트 보고서 |
| `extension/work/CORE_CHANGE_FAILURES.md` | active failure owner | 자동 Core 변경 차단 기록 |

## 실패 ledger

| objective | attempt | result / cause | count | next condition |
|---|---|---|---:|---|
| 프로젝트 방향 정본화 | 2026-07-30 기존 초안 | 에이전트가 일부 결과를 우선순위로 재해석해 사용자가 반박 | 1 | 직접 사용자 발언 source map으로 교정 완료 |
| 규칙·설계·핸드오프 정비 | 첨부 외부 세션 | `rule-governance.md` 일부 변경 뒤 API 529로 중단 | 1 | Core draft는 보류하고 비-Core 문서 교정·검증 |
| M0-S2 계보 조회 | 이전 에이전트 시도 | Git 조회 명령 승인 거부, mutation 없음 | 1 | 다음 실행에서 read-only Git으로 재시작 |

## 첫 다음 행동

1. 후속 실행 요청이 이어지면 `M0-S2`에서 `D6` 순서로 78개 의미의 직접 계보를 read-only Git으로 역추적한다.
2. M0-S2에서는 Core·규칙·보호 데이터·외부 상태를 변경하지 않고 보존 지도의 source anchor만 갱신한다.
3. 문서 처분은 M0~M3 동안 후보 목록만 누적하고, M3 통과 뒤 M4 exact 승인 gate까지 실행하지 않는다.

## 다음 session 시작 prompt

`PROJECT_RULES.md → SESSION_HANDOFF.md → overall-design → M0 phase-design`을 읽고 `M0-S2`부터 재개한다. 현재 checkpoint를 기준선으로 보존하고 Core mutation·삭제·stage·commit·push 없이 read-only 계보와 보존 지도만 갱신한다.
