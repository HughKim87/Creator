# Windows 문서 검증 명령의 환경·문구 가정

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 00
- 마지막 검증: 2026-07-24 Stage 11
- 적용 범위: Windows PowerShell, Git, `rg`, Python module CLI, 문서 검증 script

## 증상

프로젝트 산출물은 정상인데 검증 명령이 shell quoting, 경로, runtime, 공개 CLI 형태를 추측해 중단되거나 거짓 실패를 만들었다.

## 확인된 원인

- 공백이 있는 Git `safe.directory` 값, PowerShell quote·escape, native stderr 동작을 현재 shell에서 확인하지 않고 추측했다.
- Windows에서 wildcard, relative path, pipeline, .NET API가 다른 shell·runtime처럼 동작한다고 가정했다.
- CLI `--help`와 실제 무변경 응답을 먼저 보지 않고 option명·응답 구조·module path를 내부 개념에서 추정했다.
- literal 문구·file shape·test import 순서를 실제 의미·공개 계약보다 강하게 단언했다.
- 신규·미추적 파일과 보호 필터를 포함한 검증 범위를 명시하지 않았다.

## 실패·해결 이력

- 초기 구축에서는 같은 completion gate가 문구·PowerShell 문법·경로 가정으로 최고 3회 연속 실패했다.
- Stage 05~10에서 `safe.directory`, CLI option, `PYTHONPATH=src`, 응답 구조, 정규식·quote 가정이 재발해 각 공개 계약을 먼저 관찰하는 방식으로 보정했다.
- Stage 11 계획에서는 Git 조회의 `safe.directory` 누락과 stage 호출의 공백 경로 인용 누락이 각각 1회 재발했다. 호출별 `-c "safe.directory=<absolute path>"`를 사용해 조회·stage·commit을 성공시켰다.
- 상세 occurrence와 당시 command는 각 stage owner와 Git 이력이 소유한다. 이 문서는 공통 원인·예방만 소유한다.

## 해결과 검증

- 처음 사용하는 명령은 완료된 `--help`와 실제 무변경 응답 한 건을 순서대로 확인한다.
- 이 source-layout 프로젝트의 module CLI는 `PYTHONPATH=src`를 명시한다.
- sandbox Git 호출은 검증된 절대 경로를 큰따옴표로 감싼 호출별 `safe.directory`를 사용한다.
- 추적·미추적·보호 경로 검사를 분리하고, stage 뒤 `git diff --cached --check`와 포함 경로를 확인한다.
- trailing whitespace, strict UTF-8, NUL, link, native exit code는 목적별 검증 수단으로 나눈다.
- 보정 후 영향받은 consolidated checkpoint를 다시 실행해 성공했다.

## 재사용 규칙

- 검사기 실패와 산출물 실패를 구분한다.
- shell·runtime·CLI 계약을 추측하지 말고 가장 작은 read-only 관찰로 확인한다.
- 긴 one-liner보다 현재 PowerShell에서 읽히는 여러 문장을 사용한다.
- literal 문장 전체보다 필요한 의미·구조·exit kind를 단언한다.
- 같은 root cause의 단발 recurrence는 새 세부 행을 계속 쌓지 않고 예방 규칙이 달라질 때만 이 정본을 갱신한다.

## 근거

- [세션 핸드오프](../SESSION_HANDOFF.md)
- [Stage 11 운영 마찰·인지 복잡성 축소](../docs/build/stage-11-operating-friction-reduction.md)
- Git history
