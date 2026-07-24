# Extension

- 목적: 앞으로 추가되는 YouTube·영상·제작 workflow·스킬·개별 작업과 runtime 데이터를 core와 분리해 소유한다.
- 읽는 시점: 기반 변경이 아닌 실제 작업 기능이나 작업 데이터를 만들거나 수정할 때.
- 책임: 프로젝트 에이전트가 승인 범위 안에서 유지하고, 사용자가 목표·보호 데이터·외부 효과를 승인한다.
- 상태: 활성 확장 영역.
- 관련 권위: 루트 `PROJECT_RULES.md`, `AGENTS.md`, `SESSION_HANDOFF.md`.

## 배치

| 위치 | 책임 |
|---|---|
| `docs/` | YouTube·영상·workflow 계약과 사용자 가이드 |
| `src/` | 도메인·workflow 구현 |
| `schemas/` | extension payload 구조 |
| `tests/` | extension 회귀와 수직 acceptance test |
| `examples/` | 보호 데이터가 아닌 실행 예시 |
| `reports/` | 사용자가 명시적으로 요청한 시점 보고서 |
| `work/` | 활성 작업과 core 변경 차단 실패 |
| `data/` | 실행 시 생성되는 disposable record·event |
| `inputs/` | 영상별 보호 원본; Git 제외 |
| `outputs/` | 영상·SRT·썸네일·업로드 패키지 같은 보호 파생물; Git 제외 |
| `.runtime/` | 프로젝트 로컬 도구·모델·의존성; Git 제외 |
| `../.agents/skills/` | 저장소 전체에서 자동 발견되는 Codex skill source |

새 작업은 이 영역에 추가한다. extension 작업을 이유로 core 구현·계약·규칙을 자동 변경하지 않는다.

## Core 의존 경계

- extension은 승인된 `file_data` 인터페이스를 사용할 수 있다.
- core는 extension을 import하거나 extension 도메인 개념을 소유하지 않는다.
- 필요한 core 기능이 없으면 임시 우회 구현을 조용히 추가하지 않는다.
- interactive 작업은 core 변경 필요성을 사용자에게 설명한다.
- 자동 작업은 `core_change_required`로 실패하고 `work/CORE_CHANGE_FAILURES.md`에 기록한다.
