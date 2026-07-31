# 프로젝트 전역 지식 선별·구조 통합·정리 전체 설계

- 문서 분류: `overall-design`
- 상태: `active`
- 최종 결과: 프로젝트 작업트리의 모든 파일을 Git 상태와 관계없이 감사하고, 이후 workflow에 재사용할 가치가 검증된 내용만 canonical owner에 흡수·병합한 뒤 불필요한 파일을 승인된 범위에서 정리해 기반 구조와 workspace cleanliness를 함께 달성한다.
- 독자: 프로젝트 전역 개선을 실행·승인하거나 다음 세션에서 재개하는 agent와 사용자
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; 이 문서는 Core 변경, 보호 데이터 mutation, 삭제·이동, commit·push의 독립 승인이 아니다.
- 프로젝트 방향: [장기 사용자 결과와 선택 기준](../../PROJECT_DIRECTION.md)
- 현재 상태 owner: `SESSION_HANDOFF.md`
- 활성 단계: [W4 runtime 보존·output 지식 통합·승인 정리](repository-consolidation/W4_RUNTIME_OUTPUT_CONSOLIDATION_AND_CLEANUP.md)
- 이전 규칙·문서 슬라이스 evidence: [M0 보존 지도](rule-preservation/M0_RULE_CONSERVATION_MAP.md), [M0~M4 검증 보고](../reports/2026-07-31_규칙_무손실_통합_M0_작업_보고.md) — optional, startup-required 아님

## 이번 세션에서 확정한 사용자 의도

- 범위는 ignored 파일을 추적하는 작업이 아니다. `inputs/**`를 제외한 tracked·untracked·ignored 파일, 백룸·개선 문서·코드·데이터·중간물·파생물, `outputs/`와 `extension/data/`가 대상이다.
- 모든 내용을 무조건 흡수하지 않는다. 이후 반복 작업의 workflow·규칙·계약·검증·재현성·실패 예방에 실제로 재사용할 수 있는 내용만 선별한다.
- 재사용 항목은 가장 좁은 기존 canonical owner에 우선 흡수·병합한다. 기존 owner로 서로 다른 책임이 섞일 때만 최소한의 새 owner를 만든다.
- 정리의 목적은 파일 수 감소 자체가 아니라, 일회성·중복·재생성 가능·역할 종료 항목을 걷어내면서 프로젝트 기반을 더 단단하고 재현 가능하게 만드는 것이다.
- 최종 결과는 `git status`만 깨끗한 상태가 아니다. 남아 있는 tracked·untracked·ignored·보호·runtime 항목이 모두 필요성과 owner·보존 또는 재생성 근거로 설명되고, 예상 밖 파일이 0인 clean workspace다.

## 범위와 경계

포함 범위:

- 저장소 root 아래의 tracked·modified·untracked·ignored 파일과 디렉터리
- 백룸 조사·실험·렌더·변환·임시·cache·runtime·개선 단계에서 생성된 항목
- 규칙·문서·보고서·코드·테스트·schema·example·data·입출력 파생물
- 삭제·rename된 선행 owner와 Git history는 현재 파일의 계보·복구 질문에 필요한 exact 범위

제외·제한 범위:

- `.git/**`는 artifact 지식 선별 대상이 아니지만 W4-S5에서 refs·stash·recovery를 보존하는 별도 object 위생 대상으로 감사한다.
- secret·credential 내용은 읽거나 inventory에 복제하지 않고 `sensitive-unread`로 분류한다.
- 보호 `inputs/**`는 분석·처분 범위에서 제외한다. `outputs/**`만 단계별 최소 metadata와 승인된 exact 후보를 분석하되 stage·commit하지 않는다.
- Core mutation은 exact 경로·이유·extension 대안을 제시해 현재 대화에서 별도 승인받기 전까지 금지한다.
- 삭제·이동·원본 덮어쓰기는 W4 exact 처분 목록 승인 전까지 실행하지 않는다.

## 선별·소유 원칙

모든 항목은 `canonical-retain / reusable-existing-owner / reusable-new-owner-review / protected-user-artifact / regenerable-disposable / historical-git / disposition-candidate / unresolved` 중 하나로 분류한다.

- 재사용 판정은 반복 가능한 `조건 / 행동 / 예외 / 검증` 또는 재현 가능한 workflow·contract·schema·test를 강화하는가로 결정한다.
- 단일 작업 수치·원문 대화·중복 설명·미검증 추측·재생성 가능한 파생물은 active foundation으로 승격하지 않는다.
- 재사용 가치가 없다는 판정도 owner·reference·rebuild/recovery·승인 근거가 있어야 한다.
- 새 문서·규칙·도구는 cleanup 과정에서 자동 증가시키지 않는다. 신설은 기존 owner가 책임을 표현할 수 없고 독자·trigger·verification이 구분될 때만 허용한다.
- 이전 M0~M3 결과는 규칙·문서 슬라이스의 유효한 선행 evidence다. 기존 M4 exact 목록은 프로젝트 전역 inventory보다 좁아 현재 실행 단계로는 무효다.

## 산출물·상태 계약

| artifact | owner·역할 | 유지 조건 |
|---|---|---|
| overall-design 1 | 이 문서; 안정된 의도·단계 지도 | initiative 종료까지 active |
| active phase-design 1 | 현재 W4 문서; runtime·output·처분·Git 위생 gate | W4 commit 뒤 active route에서 교체 |
| optional phase evidence 최대 1 | W3 disposition manifest; 선행 수치·digest | startup 제외, W4 최신 판정이 우선 |
| current-state 1 | `SESSION_HANDOFF.md`; 상태·blocker·첫 행동 | 현재 사실만 유지 |
| final report 1 | 기존 M0~M4 보고 경로를 W5에서 전역 보고로 갱신 | 중간 단계에서 별도 보고서 신설 금지 |

현재 handoff mode는 ignored runtime·보호 output 때문에 `same-workspace`다. 각 phase exit gate 뒤 task-owned maintained files만 commit하며, push와 보호 경로 stage는 하지 않는다.

## 단계 지도

| 단계 | 의존성 | 한 줄 결과 |
|---|---|---|
| W0 전역 inventory·분류 | 현재 사용자 범위 교정 | 모든 작업트리 항목의 Git 상태·provenance·role·owner·재생성/복구·1차 분류가 빠짐없이 고정됨 |
| W1 재사용 지식 추출·owner mapping | W0 passed | 재사용 후보만 exact source·evidence·기존 owner·미흡수 이유와 연결됨 |
| W2 선택적 흡수·기반 강화 | W1 passed, 필요한 Core exact 승인 | 승인된 지식·계약·검증만 기존 owner 중심으로 병합되고 중복·무효 증가가 0임 |
| W3 의존성 해제·처분 manifest | W2 passed | 유지 allowlist와 tracked·untracked·ignored·보호 exact 처분 후보가 reference·rebuild·recovery와 함께 확정됨 |
| W4 runtime·output 통합·승인 처분 | W3 passed, latest scope correction | runtime 67개가 관리되는 local capability가 되고 output 재사용 지식만 흡수된 뒤 승인 항목과 Git garbage만 정리됨 |
| W5 전역 회귀·clean closeout | W4 passed | 전체 회귀·재현성·링크·물리 inventory·Git clean이 통과하고 단일 최종 보고와 commit이 남음 |

## 전체 성공 기준

- W0 기준 작업트리 항목 100%가 분류되고 `unresolved`는 blocker·다음 확인 조건을 가진다.
- 재사용 가능 항목은 기존 canonical owner 우선으로 반영되며, 미흡수·폐기 항목은 근거가 있다.
- 보호 원본·파생물과 secrets는 reusable 문서·cache·Git에 복제되거나 stage되지 않는다.
- 유지 항목마다 현재 owner·runtime 필요성·검증·재설치 또는 보존 근거가 있고, 삭제 항목은 exact 승인·복구 경계와 일치한다.
- Core·Extension·workflow·문서·schema·link gate가 통과하고 startup-required 읽기 비용과 활성 규칙 복잡성이 근거 없이 증가하지 않는다.
- 최종 commit 뒤 `git status --porcelain`이 비고, reviewed allowlist 밖의 untracked·ignored·임시·백룸·개선 산출물이 0이다.
- “Git에서 보이지 않음”을 clean 근거로 사용하지 않고 filesystem inventory와 Git inventory가 서로 일치한다.

## 중단·복구·승인

- exact owner·재사용 가치·복구 경계를 확정할 수 없으면 `unresolved`로 남기고 처분하지 않는다.
- 보호 데이터 내용, secret, Core, 외부 상태, 삭제·이동이 새로 필요하면 해당 경계에서 중단하고 필요한 exact 승인을 확인한다.
- tracked 파일은 Git commit, untracked·보호 파일은 사용자 승인 외부 경계 또는 유지 판정이 없으면 삭제 후보로 확정하지 않는다.
- 이전 M4는 `invalidated`이며 새 전역 inventory가 끝나기 전 해당 22개 파일을 독립 처분하지 않는다.

## 다음 실행

[W4 runtime 보존·output 지식 통합·승인 정리](repository-consolidation/W4_RUNTIME_OUTPUT_CONSOLIDATION_AND_CLEANUP.md)에서 runtime owner를 먼저 만들고 outputs 201개를 교차검증한 뒤, 300개 파일·빈 디렉터리 6개와 Git garbage의 승인을 분리해 실행한다.
