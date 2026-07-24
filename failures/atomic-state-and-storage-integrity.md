# 원자 쓰기·기록·상태 무결성

- 상태: 해결
- 적용 범위: 파일 record, event stream, snapshot, lifecycle, 동시 쓰기와 저장 유형 검증

## 증상

쓰기 뒤 검증 사이에 경쟁 구간이 생기거나, event 시각이 역행하고, 저장 주소·ID·유형·완료 상태가 서로 충돌했다.

## 확인된 원인

입력 경계만 검증하고 저장된 데이터와 사후 검증을 신뢰했으며, 원장 append와 projection 성공 조건을 하나의 불변식으로 설계하지 않았다.

## 실패·해결 이력

잠금 해제 뒤 재읽기, 자유 경로 ID 중복, 미승인 저장 유형, terminal work의 next action, event 시간 역행이 각각 회귀로 확인됐다.

## 해결과 검증

- 원자 교체와 성공 판정 재읽기를 같은 잠금 경계에 두고 ID에서 저장 주소를 결정한다.
- 저장 유형·event 시간·상태 전이·expected hash의 정상·실패 회귀를 통과했다.

## 재사용 규칙

- 성공 판정에 쓰는 hash·count·version은 잠금 내부 snapshot에서 계산한다.
- 중앙 인덱스가 없으면 ID와 저장 주소를 결정적으로 대응시킨다.
- 입력 허용 목록과 저장된 record 유형을 모두 fail-closed 검증한다.
- 원장 append 전에 event 시간과 전이 불변식을 검사한다.
- terminal work에는 다음 행동을 남기지 않고 새 work나 handoff가 후속 행동을 소유한다.
