# 김실버유튜브 프로젝트

이 저장소의 목적은 **사용자의 수동 생산 작업을 줄이고, 승인된 목표와 안전 경계 안에서 에이전트가 유튜브 작업을 자율 수행하도록 돕는 것**이다.

## 시작

| 확인 | 위치 |
|---|---|
| 현재 작업·blocker·첫 다음 행동 | [SESSION_HANDOFF.md](SESSION_HANDOFF.md) |
| 작업 등급과 조건부 규칙 | [AGENTS.md](AGENTS.md) |
| 상시 안전·권한 정책 | [PROJECT_RULES.md](PROJECT_RULES.md) |
| 현재 계약 | [docs](docs/) |
| 과거 핵심 결정 | [프로젝트 역사 요약](docs/PROJECT_HISTORY.md) |

완료 작업의 상세 과정과 삭제된 과거 문서는 Git 이력에서 필요할 때만 찾는다.

## 기본 작업 방식

1. 새 세션은 `AGENTS.md` → `PROJECT_RULES.md` → `SESSION_HANDOFF.md`를 읽는다.
2. 가장 낮은 충분 등급과 matching rule을 고른다.
3. 승인 범위의 작업을 자율 수행한다.
4. 논리적 완료 checkpoint에서 관련 검사와 diff를 검증한다.
5. 현재 상태가 바뀐 경우에만 handoff를 갱신한다.

## 구조

| 위치 | 역할 |
|---|---|
| 루트 | 시작 경로, 상시 정책, 현재 상태, 사용자 개요 |
| `rules/` | matching action에서만 읽는 절차 |
| `docs/` | 활성 계약과 짧은 역사 요약 |
| `docs/obsidian/` | Obsidian 보호 설정 계약 |
| `failures/` | material하고 재사용 가능한 해결 실패 지식 |
| `src/`, `schemas/`, `tests/`, `examples/` | 구현·파생 계약·회귀·예시 |
| `inputs/`, `outputs/` | 사용자가 exact 대상을 지정해야 접근하는 보호 데이터 |

## 검증

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m unittest discover -s tests -q
```

완료 이력과 복구는 Git을 사용하며 프로젝트 내부에 별도 백업 복제본을 만들지 않는다.
