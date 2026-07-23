# 김실버유튜브 프로젝트

이 저장소의 목적은 **사람의 수동 생산 작업을 줄이고, 승인된 목표와 안전 경계 안에서 에이전트가 조사·설계·구현·검증·복구를 자율 수행하게 하는 것**이다. 문서와 도구는 이 목적을 돕는 수단이며 작업보다 커져서는 안 된다.

## 지금 확인할 것

| 확인 | 위치 |
|---|---|
| 현재 작업·blocker·첫 다음 행동 | [SESSION_HANDOFF.md](SESSION_HANDOFF.md) |
| 현재 initiative 계획·실행·보고 | [Stage 11 운영 마찰·인지 복잡성 축소](docs/build/stage-11-operating-friction-reduction.md) |
| 작업 등급과 rule 선택 | [AGENTS.md](AGENTS.md) |
| 상시 안전·권한 정책 | [PROJECT_RULES.md](PROJECT_RULES.md) |
| 사용자용 문서 진입 지도 | [Obsidian 시작 화면](docs/obsidian/START_HERE.md) |

현재 작업은 위 다섯 진입점으로 충분하다. 완료 stage, 계약, 보고서, 실패 사례의 전체 목록은 [문서 지도](docs/obsidian/DOCUMENT_MAP.md)와 [자동 전체 inventory](docs/obsidian/GENERATED_DOCUMENT_INVENTORY.md)에서 필요할 때만 찾는다.

## 기본 작업 방식

1. 새 세션은 `AGENTS.md` → `PROJECT_RULES.md` → `SESSION_HANDOFF.md`를 한 번 읽는다.
2. `AGENTS.md`에서 가장 낮은 충분 등급(`quick / standard / controlled`)과 matching rule을 고른다.
3. exact task owner만 읽고 승인 범위의 작업을 자율 수행한다.
4. 논리적 완료 checkpoint에서 관련 검사와 diff를 검증한다.
5. 현재 상태가 실제로 바뀐 경우에만 handoff를 갱신한다.

일반 `quick`·`standard` 작업에는 번호 Stage, master, 점수, subagent, 별도 보고서, commit을 자동으로 붙이지 않는다.

## 구조

| 위치 | 역할 |
|---|---|
| 루트 | startup router, 상시 정책, 현재 상태, 사용자 개요 |
| `rules/` | matching action에서만 읽는 task 절차 |
| `docs/build/` | 번호 controlled stage의 계획·결과와 master |
| `docs/` | 정보·파일·작업·지식·컨텍스트·유지보수 계약 |
| `docs/obsidian/` | 현재 진입 router와 전체 추적 문서 inventory |
| `failures/` | material하고 재사용 가능한 해결 실패 지식 |
| `reports/` | 현재 지시가 아닌 시점 분석·검증 근거 |
| `src/`, `schemas/`, `tests/`, `examples/` | 구현·파생 계약·회귀·예시 |
| `data/` | read-only legacy record·event와 승인된 파생 데이터 |
| `backup/` | 활성화하지 않는 읽기 전용 역사 증거 |
| `inputs/`, `outputs/` | 사용자가 exact 대상을 지정해야 접근하는 보호 데이터 |

## 안전 경계

- `inputs/`, `outputs/`는 exact 대상과 목적 없이 열거하거나 읽지 않는다.
- `backup/`은 역사 증거이며 활성 지시나 runtime source가 아니다.
- 보호 데이터, 외부 쓰기, 설치·비용, 권한, 미승인 삭제·이동·commit·push는 사전 권한을 확인한다.
- 안전하고 가역적인 로컬 세부는 에이전트가 결정하고 결과와 material risk를 보고한다.
- 문서 수, 테스트 수, 점수만으로 사용자 결과를 완료라고 하지 않는다.
