# Windows 텍스트 줄바꿈 변환과 실제 크기 측정 불일치

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 07 전체 읽기 기준선 테스트
- 마지막 검증: 2026-07-23
- 적용 범위: Windows text I/O, CRLF, Unicode 문자 수, UTF-8 byte 기준선

## 증상

한 문서의 선택 읽기 기준선을 실제 bytes에서 측정한 서비스 결과가 테스트의 `read_text()` 기대값보다 문자와 byte 각각 3만큼 컸다.

## 확인된 원인

- Windows text mode로 fixture를 쓸 때 세 개의 LF가 디스크에서 CRLF로 기록됐다.
- `Path.read_text()`는 universal newline 변환으로 CRLF를 다시 LF로 읽어 실제 디스크 문자 수와 다른 기대값을 만들었다.
- 서비스는 원본 bytes를 strict UTF-8로 decode해 CR과 LF를 각각 세므로 승인된 실제 저장 크기 계약을 정확히 따르고 있었다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 07 기준선 단위 테스트 | 서비스 25자·51 bytes, 테스트 기대 22자·48 bytes로 11개 중 1개 실패 | 1 | 테스트도 `read_bytes()` 후 strict UTF-8 decode로 실제 저장 내용을 세도록 변경하고 11개 컨텍스트 테스트 전체 성공 |

## 해결과 검증

- 저장 비용·무결성 기준선은 text mode로 정규화된 문자열이 아니라 실제 file bytes에서 계산한다.
- 테스트 기대값을 `read_bytes()`의 길이와 그 bytes를 strict UTF-8로 decode한 문자 길이로 바꿨다.
- CRLF fixture의 문자 수와 UTF-8 byte 수가 서비스 결과와 일치하고 전체 컨텍스트 테스트가 성공했다.

## 재사용 규칙

- 줄바꿈 자체가 측정 대상이면 `read_text()`의 universal newline 변환을 기준선으로 사용하지 않는다.
- 논리 문장 길이와 실제 저장 문자·byte 크기를 구분하고 측정 계약에 맞는 한쪽만 단언한다.
- Windows·Linux 간 결과를 비교할 때 newline 정규화 여부를 명시한다.
- 무결성 hash와 저장 비용은 원본 bytes, 사용자 표시용 논리 텍스트는 필요한 경우 별도 정규화한다.

## 근거

- [선택적 읽기·컨텍스트 계약](../docs/CONTEXT_PACKAGE_CONTRACT.md)
- [Stage 07 계획](../docs/build/stage-07-context-retrieval.md)
- [컨텍스트 테스트](../tests/test_context.py)
