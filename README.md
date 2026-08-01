# 크리에이터 프로젝트

이 저장소의 목적은 **사용자의 수동 생산 작업을 줄이고, 승인된 목표와 안전 경계 안에서 에이전트가 영상 작업을 자율 수행하도록 돕는 것**이다.

## 시작

| 확인 | 위치 |
|---|---|
| 현재 작업·blocker·첫 다음 행동 | [SESSION_HANDOFF.md](SESSION_HANDOFF.md) |
| 작업 등급과 조건부 규칙 | [AGENTS.md](AGENTS.md) |
| 상시 안전·권한 정책 | [PROJECT_RULES.md](PROJECT_RULES.md) |
| 변경 불가 기본 골조 | [core](core/) |
| 앞으로 확장할 작업 영역 | [extension](extension/) |
| 현재 기반 계약 | [core/docs](core/docs/) |

완료 작업의 상세 과정과 삭제된 과거 문서는 Git 이력에서 필요할 때만 찾는다.

## 기본 작업 방식

1. 새 세션은 `AGENTS.md` → `PROJECT_RULES.md` → `SESSION_HANDOFF.md`를 읽는다.
2. 가장 낮은 충분 등급과 matching rule을 고른다.
3. 승인 범위의 작업을 자율 수행한다.
4. `core/` 변경이 필요하면 명시적 사용자 승인을 확인한다. 자동 작업은 변경하지 않고 실패로 기록한다.
5. 논리적 완료 checkpoint에서 관련 검사와 diff를 검증한다.
6. 현재 상태가 바뀐 경우에만 handoff를 갱신한다.

## 구조

| 위치 | 역할 |
|---|---|
| 루트 | 시작 경로, 상시 정책, 현재 상태, 사용자 개요 |
| `core/` | 사용자 승인 없이는 변경할 수 없는 Agent 기본 골조 |
| `core/rules/` | matching action에서만 읽는 기반 절차 |
| `core/docs/` | 현재 기반 계약과 유지 설명 |
| `core/failures/` | material하고 재사용 가능한 기반 실패 지식 |
| `core/src/`, `core/schemas/`, `core/tests/` | 기반 구현·파생 계약·회귀 |
| `extension/` | 영상·스킬·작업 상태·runtime·예시·보고서 |
| `inputs/`, `outputs/` | 사용자가 exact 대상을 지정해야 접근하는 보호 데이터 |

## 검증

전체 deterministic gate는 다음 한 명령으로 실행한다.

```powershell
python -B scripts/verify.py
```

이 명령은 bootstrap·Node·Core·Extension·maintenance와 ASCII·한글·공백 경로 clean clone을 함께 검사한다. 로그인 browser session 같은 외부 capability는 `needs_user`로 분리하며 품질 통과로 대신하지 않는다.

특정 Python 회귀 실패를 좁힐 때만 아래 명령을 직접 실행한다.

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = ((Resolve-Path 'core/src').Path, (Resolve-Path 'extension/src').Path, (Resolve-Path 'core/tests').Path -join ';')
python -B -m unittest discover -s core/tests -q
python -B -m unittest discover -s extension/tests -q
```

완료 이력과 복구는 Git을 사용하며 프로젝트 내부에 별도 백업 복제본을 만들지 않는다.
