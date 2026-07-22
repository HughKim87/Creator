# 기존 Python bytecode 캐시와 청결 게이트 불일치

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 08 통합 게이트
- 마지막 검증: 2026-07-23
- 적용 범위: Python 실행, `PYTHONDONTWRITEBYTECODE`, 단계 경계 청결 검사

## 증상

기능·구조·전체 테스트는 모두 성공했지만 통합 게이트의 마지막 검사에서 `src/file_data/__pycache__` 디렉터리 1개가 발견되어 단계 완료가 중단됐다.

## 확인된 원인

- `PYTHONDONTWRITEBYTECODE=1`은 이후 Python 실행의 새 `.pyc` 생성을 막지만 이미 존재하는 cache를 제거하지 않는다.
- 발견된 cache는 통합 게이트보다 이전 시각에 생성됐고 `.gitignore` 대상이라 Git 상태만으로는 보이지 않았다.
- 게이트가 실행 환경 변수 설정과 작업 시작 시점의 cache 부재를 같은 조건으로 간주했다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 08 통합 게이트 1차 | scan·verify·87개 테스트는 성공했으나 마지막 cache 검사에서 `__pycache__` 1개를 발견해 전체 실패 | 1 | 작업공간 내부의 정확한 cache 경계를 확인해 기존 bytecode만 정리하고 같은 환경의 실제 `maintenance-scan`을 재실행한 뒤 cache 0개 확인 |

## 해결과 검증

- cache 경로가 프로젝트 루트 아래의 정확한 `src/file_data/__pycache__`인지 확인한 뒤 내부 bytecode와 빈 디렉터리만 정리했다.
- `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUTF8=1`, `PYTHONPATH=src`를 적용한 실제 CLI 재실행이 성공했다.
- 재실행 직후 `src`, `tests` 아래 `__pycache__`가 0개임을 확인했다.
- 보정 뒤 Stage 08 통합 게이트 전체를 처음부터 다시 실행한다.

## 재사용 규칙

- Python 검증 전에 bytecode 쓰기 방지 환경을 설정하고, 단계 경계에서는 기존 cache 존재 여부를 별도 검사한다.
- Git ignored 상태는 파일 부재를 뜻하지 않으므로 청결 게이트에서 Git 상태와 실제 cache 탐색을 분리한다.
- cache를 정리할 때는 resolve된 절대 경로가 작업공간 내부의 예상 경로와 정확히 일치하는지 먼저 확인한다.
- 한 번 실패한 통합 게이트는 마지막 검사만 통과시켜 닫지 않고 전체를 처음부터 다시 실행한다.

## 근거

- [세션 핸드오프](../SESSION_HANDOFF.md)
- [Stage 08 계획](../docs/build/stage-08-maintenance-automation.md)
