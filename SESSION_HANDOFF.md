# 세션 핸드오프

- 갱신일: 2026-07-23
- 역할: 채팅 기억 없이 현재 검증 상태와 첫 다음 행동을 재구성하는 단일 활성 상태 정본
- 현재 단계: Stage 10 에이전트 자율 운영·구조 최적화 97/100 완료
- 백업 정책: 별도 복제 없음. 활성 프로젝트는 Git 이력을 복구 근거로 사용한다.

## 1. 시작 순서와 권위

새 대화·세션에서는 다음 세 파일을 한 번만 끝까지 읽는다.

1. `AGENTS.md`
2. `PROJECT_RULES.md`
3. `SESSION_HANDOFF.md`

이후에는 `AGENTS.md`가 현재 행동에 연결한 `rules/*.md`와 정확한 단계·계약 owner만 읽는다. 권위 순서는 사용자의 최신 명시적 지시 → `PROJECT_RULES.md` → 이 핸드오프 → 현재 단계 owner다.

주요 owner:

- 최신 요구사항: `reports/2026-07-22_프로젝트_의도_통합_요구사항_기준서.md`
- 구축 순서: `docs/build/MASTER_BUILD_PLAN.md`
- Stage 10 진단·계획·실행·Claude 검증·점수: `docs/build/stage-10-agent-autonomy-structure-optimization.md`
- 실패 지식 탐색: `failures/README.md`

## 2. 현재 목적과 운영 경계

프로젝트의 최상위 목적은 사람에게 생산 작업을 떠넘기지 않고, 에이전트가 승인된 목표와 안전 경계 안에서 조사·설계·구현·검증·복구를 자율 수행해 생산성을 극대화하는 것이다. 데이터·문서·지식 기반은 그 목적을 위한 수단이다.

- 에이전트는 안전하고 가역적인 로컬 구현 세부와 실패 복구를 스스로 결정하고 중요한 선택·진행·실패·결과를 사람에게 보고한다.
- 목표가 여러 방향으로 갈리는 선택, 보호 데이터, 외부 쓰기, 설치·비용, 삭제·이동, 보안·권한, 되돌리기 어려운 결정, 실질적 범위 확대는 사전 확인한다.
- `backup/`은 읽기 전용 역사 경계이며 활성 규칙으로 사용하지 않는다.
- `inputs/`, `outputs/`는 사용자가 정확한 대상과 목적을 지정하기 전에는 열거·열람하지 않는다.
- 새 기능·단계는 자동 생성하지 않는다.

## 3. 활성 구조화 작업

- work ID: `bd180787-dc89-4204-81cb-1502b1226da7`
- 상태: `completed`
- snapshot: `data/records/bd180787-dc89-4204-81cb-1502b1226da7.json`
- snapshot hash: `sha256:3b0f819279c8ca290ed5a85348e7e68415a6ac028ebe9be33f4defe743c27434`
- event 정본: `data/events/work_events.jsonl`
- blocker: 없음

요청·승인·제외 범위와 세부 완료 근거는 위 snapshot이 소유한다.

## 4. Stage 10 완료 상태

| 항목 | 검증 결과 |
|---|---|
| 목적·권한 | 에이전트 자율 생산 목적과 사람 사전 확인 경계를 상위 규칙·요구사항·단계 절차에 연결 |
| 문서 구조 | initiative owner 1개, 수동 `DOCUMENT_MAP`은 router, 전체 경로는 자동 inventory가 소유 |
| 실패 지식 | `failures/*.md` 직접 검증·검색·package·maintenance, 새 사례별 projection/source/lifecycle 생성 중단 |
| legacy 호환 | 기존 `failure_knowledge`와 source/lifecycle은 삭제하지 않고 직접 ID 읽기만 유지, 기본 검색·drift에서 제외 |
| Claude 검증 | 실제 파일 read-only review와 challenge 수행, 결합 회귀 공백을 지적받아 생성·개정 흐름까지 보강 |
| 자동 검증 | 99개 unittest 성공, maintenance scan·verify drift 0·duplicates 0·errors 0·inventory 일치 |
| 실제 데이터 대조 | canonical 26, legacy 39, 기본 failure 후보 26, unique ref 26, legacy ID 후보 0 |
| 최종 판정 | 네 가지 확인 통과, 97/100, 차단 결함 0 |

Stage 00~09의 상세 결정·점수·커밋은 각 `docs/build/stage-*.md` owner와 Git 이력이 소유한다. 이 핸드오프에 완료 역사를 복사하지 않는다.

## 5. 현재 실패와 잔여 위험

현재 Stage 10 구현을 막는 미해결 실패는 없다.

- 기존 39개 legacy failure projection과 관련 source·lifecycle data는 감사 역사로 남아 있다. 기본 현재성 판단에는 쓰지 않으며 삭제·대량 이관은 별도 승인 범위다.
- legacy failure source hash drift는 의도적으로 scan·audit 차단 사유가 아니다. 현재 owner는 canonical Markdown이다.
- `delegate-to-claude` 래퍼는 큰 프로젝트 검토에서 구조화 결과 전 종료 코드 1을 간헐적으로 반환했다. 같은 Claude CLI의 읽기 전용 안전 호출로 실제 파일 검토를 완료했고, 래퍼 challenge도 한 차례 성공했다. 프로젝트 구현 결함은 아니지만 스킬을 다음에 고칠 때 재현해야 할 도구 위험이다.
- context·maintenance는 현재 규모에서 선형 순회한다. 실제 scan은 약 3초이며 5초 경고나 품질 저하가 관측되기 전에는 인덱스·DB·스케줄러를 선행 구현하지 않는다.

장기 재사용 지식은 `failures/README.md`와 각 canonical 사례가 소유한다. Stage 10의 새 구조 원인은 `failures/derived-failure-projection-fanout.md`에 보존했다.

## 6. 보존해야 할 기존 미커밋 변경

Stage 10 착수 전에 이미 존재한 다음 사용자 변경은 이번 단계 변경에 포함하거나 되돌리지 않는다.

- `failures/runtime-discovery-system-python.md`
- `data/records/89c687f4-6ea0-4bbb-aeab-68a575055870.json`
- `data/records/a71086a8-0cdc-4180-a82d-2d480ec44afc.json`
- `data/records/a170232b-a3e8-4851-a995-81169433b95d.json`
- `data/records/b46c3955-5432-4711-b51e-b4a31a36af04.json`
- `data/records/cfd6c1bc-1c98-4065-9456-cbcd0e9b65c9.json`
- `data/records/d62f0626-575c-44f6-b621-5cef5c00ad45.json`
- `data/events/lifecycle_events.jsonl`에서 Stage 10 착수 전 추가된 첫 네 event

## 7. 정확한 다음 행동

1. 새 기능·단계를 자동 시작하지 않고 사용자의 다음 목표를 기다린다.
2. 다음 요청이 오면 최신 목적·안전 경계와 Stage 10의 legacy 위험을 먼저 대조한다.
3. 새 실패 사례는 canonical Markdown 한 파일로 직접 검증·검색하며 per-case projection을 만들지 않는다.
4. 보호 데이터·외부 앱·삭제·이동·legacy 대량 이관은 새 승인 범위가 있을 때만 수행한다.

## 8. 다음 세션 시작 프롬프트

> `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`를 새 세션 시작 시 한 번 읽어라. Stage 10은 97/100으로 완료됐고 work `bd180787-dc89-4204-81cb-1502b1226da7`는 `completed`다. 실패 Markdown은 직접 검증·검색하며 새 per-case projection을 만들지 않는다. 기존 legacy data와 §6의 사용자 미커밋 변경을 보존하고 새 기능·단계를 자동 시작하지 말고 사용자의 다음 목표를 기다려라.
