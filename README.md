# 김실버유튜브 프로젝트

이 저장소의 최상위 목적은 **사람의 수동 생산 작업 없이 승인 범위의 조사·설계·구현·검증·복구를 에이전트가 자율 수행하도록 해 생산성을 극대화하는 것**이다. 데이터 기반 지식 운영 기반은 에이전트가 채팅 기억이나 사람의 수동 안내 없이 목적·근거·상태·실패를 정확히 재구성하기 위한 수단이다. 영상 제작 기능은 이 기반을 별도 승인 아래 사용하는 후속 영역이다.

사람은 목표·금지·보호 데이터·외부 영향·되돌리기 어려운 결정과 결과 확인을 맡는다. 에이전트는 그 경계 안의 안전한 기본값, 가역적 로컬 작업, 테스트와 실패 복구를 수행하고 중요한 선택·진행·실패·게이트 결과를 보고한다.

## 한눈에 보기

| 확인할 것 | 위치 |
|---|---|
| 프로젝트 최상위 목적 | 사람의 수동 실행을 에이전트 자율 작업으로 대체 |
| 현재 운영 기반 | 데이터 기반 지식·작업·실패 재사용 |
| 현재 단계·검증 상태 | [SESSION_HANDOFF.md](SESSION_HANDOFF.md) |
| 첫 다음 행동·차단 요소 | [SESSION_HANDOFF.md](SESSION_HANDOFF.md) |
| 전체 구축 순서 | [docs/build/MASTER_BUILD_PLAN.md](docs/build/MASTER_BUILD_PLAN.md) |
| 정보·문서 책임 구조 | [docs/INFORMATION_ARCHITECTURE.md](docs/INFORMATION_ARCHITECTURE.md) |
| 파일 데이터 저장 계약 | [docs/FILE_DATA_CONTRACT.md](docs/FILE_DATA_CONTRACT.md) |
| 공통 기록 I/O·사용법 | [docs/RECORD_IO_CONTRACT.md](docs/RECORD_IO_CONTRACT.md) |
| 작업 기록·현재 상태 계약 | [docs/WORK_STATE_CONTRACT.md](docs/WORK_STATE_CONTRACT.md) |
| 지식 유형 계약·사용법 | [docs/KNOWLEDGE_TYPES_CONTRACT.md](docs/KNOWLEDGE_TYPES_CONTRACT.md) |
| 지식 수명주기 계약·사용법 | [docs/KNOWLEDGE_LIFECYCLE_CONTRACT.md](docs/KNOWLEDGE_LIFECYCLE_CONTRACT.md) |
| 선택적 읽기·컨텍스트 계약 | [docs/CONTEXT_PACKAGE_CONTRACT.md](docs/CONTEXT_PACKAGE_CONTRACT.md) |
| 유지보수·검증 자동화 계약 | [docs/MAINTENANCE_AUTOMATION_CONTRACT.md](docs/MAINTENANCE_AUTOMATION_CONTRACT.md) |
| 첫 유튜브 도메인 계약 | [docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md](docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md) |
| Obsidian 검토 시작 | [docs/obsidian/START_HERE.md](docs/obsidian/START_HERE.md) |
| 현재 요구사항 | [통합 요구사항 기준서](reports/2026-07-22_프로젝트_의도_통합_요구사항_기준서.md) |
| Stage 00~09 최종 복기 | [최종 복기 보고서](reports/2026-07-23_codex_stage00-09_프로젝트_구축_최종_복기_보고서.md) |
| Stage 10 자율 운영·구조 최적화 | [Stage 10 계획·근거](docs/build/stage-10-agent-autonomy-structure-optimization.md) |
| 해결된 실패와 재발 방지 지식 | [failures/README.md](failures/README.md) |

사용자는 이 표에서 목적, 현재 상태, 다음 결정을 한 화면 안에서 확인한다. 현재 단계와 다음 행동은 중복을 막기 위해 `SESSION_HANDOFF.md` 한 곳에서만 관리한다.

## 기본 구조

| 위치 | 역할과 경계 |
|---|---|
| 프로젝트 루트 | `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, `README.md` 같은 시작 문서와 저장소 설정 |
| `rules/` | 특정 작업을 시작할 때만 선택해서 읽는 작업 규칙 |
| `failures/` | 단계에 종속되지 않는 해결된 실패의 원인·해결·검증·재발 방지 정본. 실행 시 직접 파싱하며 사례별 projection 파일을 만들지 않음 |
| `docs/` | 활성 정보·문서 계약과 유지 설명 |
| `docs/build/` | 승인된 구축 순서와 단계별 계획 |
| `docs/domain/` | 공통 기반과 분리된 승인 도메인의 계약·사용 경계 |
| `docs/obsidian/` | 정본을 복제하지 않는 Obsidian 시작 화면·owner router·자동 전체 inventory. Stage 00~09 단계별 보기는 완료 시점 파생물 |
| `schemas/` | 공통 기록과 승인된 작업·지식 유형의 기계 판독 payload 계약 |
| `src/file_data/` | 도메인 중립 기록 검증·안전 I/O·작업 상태·지식 유형·수명주기·선택 컨텍스트·유지보수 구현 |
| `src/youtube_domain/` | 공통 기반을 소비하는 첫 유튜브 촬영 전 근거 패키지 adapter |
| `examples/` | 보호 사용자 원본이 아닌 명시적·추적 가능한 실행 요청 예시 |
| `tests/` | 유효·무효 fixture와 정상·실패 흐름 회귀 검증 |
| `data/` | 승인된 공통 기록과 event의 프레임워크 데이터 루트. CLI·서비스만 읽고 쓰며 현재 단계별 work 기록을 보존 |
| `reports/` | 특정 시점의 분석·검증 근거. 현재 실행 지시는 아님 |
| `backup/` | 수정하거나 실행에 의존하지 않는 읽기 전용 역사 증거 |
| `inputs/` | 사용자가 지정한 원본 자료. 정확한 대상과 목적 없이는 열람하지 않으며 Git에 저장하지 않음 |
| `outputs/` | 사용자 작업의 파생 결과. 정확한 작업 범위 없이는 열람하지 않으며 Git에 저장하지 않음 |

코드·스키마·도구·자동화 폴더는 해당 단계에서 필요성과 위치가 승인되기 전에는 미리 만들지 않는다.

## 시작 방법

- 사용자: 이 `README.md`에서 전체 목적을 확인한 뒤 `SESSION_HANDOFF.md`에서 현재 상태와 다음 결정을 확인한다.
- 새 에이전트 세션: `AGENTS.md` → `PROJECT_RULES.md` → `SESSION_HANDOFF.md`를 세션 시작 시 한 번 읽는다.
- 특정 작업 시작: `AGENTS.md`의 작업 규칙 표에서 현재 행동과 일치하는 `rules/*.md`만 골라 읽은 뒤 단계 계획이나 작업 자료를 읽는다.
- 같은 세션의 매 메시지마다 시작 문서를 다시 읽지 않는다. 규칙이나 현재 상태가 바뀌었다는 알림이 있을 때만 다시 확인한다.

## 안전 경계

- 활성 프로젝트는 `backup/` 없이 시작하고 재개할 수 있어야 한다.
- `inputs/`와 `outputs/`는 사용자가 정확한 대상과 목적을 지정하기 전에는 열거하거나 읽지 않는다.
- 삭제·이동·푸시·설치·외부 변경과 승인되지 않은 커밋은 사용자 승인 없이 수행하지 않는다.
- 승인 목적 안의 안전하고 가역적인 구현 세부는 에이전트가 선택·실행하고 근거와 결과를 보고한다.
- 문서 생성이나 테스트 통과만으로 실제 기능 또는 사용자 승인이 완료됐다고 판단하지 않는다.
