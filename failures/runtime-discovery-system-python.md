# 시스템 Python 실행 경로 가정

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 02 실행 환경 확인
- 마지막 검증: 2026-07-23 Codex 재시작 후 샌드박스 초기화
- 적용 범위: 로컬 Python 실행, 설치 없는 테스트, Codex 번들 런타임, Windows 샌드박스 PATH

## 증상

Stage 02 구현 언어를 확인하려고 `python --version`과 `py -3 --version`을 실행했지만 시스템 PATH와 Windows Python Launcher에 설치된 Python 3가 없어 진단 명령이 실패했다.

2026-07-23 재발에서는 사용자 PATH에 기존 Python 3.10 경로가 있었지만 Codex 샌드박스가 해당 `python.exe` 실행을 `액세스가 거부되었습니다`로 차단했고, `Get-Command python`과 `where.exe python`은 실행 가능한 명령을 찾지 못했다. 초기화 도구가 bare `python` 명령을 요구해 첫 실행이 중단됐다.

## 확인된 원인

프로젝트가 시스템 전역 Python을 제공한다고 가정했고, Codex 데스크톱 작업에 제공되는 번들 런타임 경로를 먼저 조회하지 않았다.

재발 시에는 PATH 문자열에 Python 경로가 있다는 사실과 샌드박스에서 그 실행 파일을 실제 실행할 수 있다는 사실을 구분하지 않았다. 접근이 거부된 기존 Python 3.10 경로를 보고도 이를 단순한 “PATH 부재”로 잘못 설명했고, 샌드박스에서 실행 가능한 Codex 번들 Python 디렉터리를 PATH에 넣기 전에 bare `python`을 호출했다. 사용자 PATH 변경 뒤에도 실행 중인 Codex 프로세스는 시작 시점의 이전 PATH를 유지하므로 재시작 전에는 변경이 샌드박스에 반영되지 않는다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 02 런타임 확인 | `python`, `py -3` 모두 실행 불가 | 1 | 작업공간 번들 의존성 정보를 조회하고 Python 3.12.13 실행 경로로 표준 라이브러리 테스트 성공 |
| 2026-07-23 Codex 샌드박스 초기화 | 기존 Python 3.10 경로는 PATH에 있었지만 실행이 거부됐고, 이를 “PATH 부재”로 오진한 뒤 초기화의 bare `python` 호출이 중단됨 | 1 | 번들 Python 디렉터리를 사용자 PATH 맨 앞에 추가하고 Codex를 재시작한 뒤 bare `python`과 실제 초기화를 첫 시도에 검증 |

## 해결과 검증

- Codex 번들 Python 디렉터리를 사용자 PATH 맨 앞에 추가하고 Codex를 재시작해 새 샌드박스 프로세스가 해당 PATH를 상속하게 했다.
- 재시작한 샌드박스에서 `Get-Command python`이 `C:\Users\Hugh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`를 반환했고 `python --version`은 Python 3.12.13, 종료 상태 0을 반환했다.
- 임시 프로젝트 루트에서 `python -m file_data --root <temp> init`을 우회 없는 bare `python`으로 실행해 종료 상태 0과 `data/records`, `data/events` 생성을 확인했다.
- 검증용 임시 루트를 제거한 뒤 Git 작업 트리가 깨끗함을 확인했다.

## 재사용 규칙

- 로컬 프로젝트에서 런타임이 필요하면 설치를 시도하기 전에 제공된 작업공간 런타임을 조회한다.
- PATH에 문자열이 존재하는지만 보지 말고 샌드박스 안에서 `Get-Command python`과 실제 `python --version`이 모두 성공하는지 첫 의존 명령 전에 확인한다.
- 초기화 도구가 bare `python`을 요구하면 샌드박스에서 실행 가능한 번들 Python 디렉터리를 PATH에 먼저 넣고, 실행 중인 Codex가 이전 환경을 보유한 경우 재시작한 뒤 초기화를 실행한다.
- 번들 절대 경로는 버전에 따라 달라질 수 있으므로 프로젝트 계약에 고정하지 않고 작업공간 의존성 조회 결과와 실제 명령 해석 결과를 대조한다.
- 프로젝트 코드는 명시한 표준 라이브러리 범위를 유지하고 숨은 전역 패키지에 의존하지 않는다.

## 근거

- [파일 데이터 저장 계약](../docs/FILE_DATA_CONTRACT.md)
- [Stage 02 계획](../docs/build/stage-02-file-data-foundation.md)
