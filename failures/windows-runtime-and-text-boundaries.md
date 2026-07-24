# Windows 런타임·명령·텍스트 경계

- 상태: 해결
- 적용 범위: Windows PowerShell, Python 실행, JSON 인수, UTF-8, 줄바꿈과 정규식

## 증상

한글이 깨지거나 JSON 따옴표가 손실됐고, 시스템 Python·명령 옵션·줄바꿈·정규식 동작을 잘못 가정해 검증이 실패했다.

## 확인된 원인

파일, PowerShell, native process, Python 표준 입출력의 인코딩·인수 변환·newline 정규화 경계를 각각 검증하지 않았다.

## 실패·해결 이력

CP949 출력, BOM 없는 UTF-8 읽기, JSON argv 손실, 시스템 Python 접근 거부, CRLF 크기 차이, 후행 공백 정규식 오탐이 반복됐다.

## 해결과 검증

- UTF-8 파일 읽기와 구조화 payload stdin을 명시하고 실제 실행 가능한 Python을 먼저 확인한다.
- Unicode subprocess 회귀, 원본 byte 기준 hash·크기 검증, PowerShell 실제 명령 검증을 통과했다.

## 재사용 규칙

- PowerShell의 `Get-Content`에는 `-Encoding utf8`을 명시한다.
- 복합 JSON은 native argv보다 UTF-8 stdin을 우선한다.
- 런타임은 설치 전에 작업공간 제공 경로와 실제 `python --version`을 확인한다.
- 저장 byte와 universal-newline 변환된 논리 텍스트를 구분한다.
- 정규식 escape와 CLI 옵션은 작은 실제 입력으로 확인한다.
