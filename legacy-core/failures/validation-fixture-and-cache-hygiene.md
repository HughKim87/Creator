# 검증 fixture·패치·캐시 위생

- 상태: 해결
- 적용 범위: 테스트 fixture, Markdown patch, 검증 명령, Python cache와 작업공간 청결

## 증상

테스트 대상보다 fixture 구조가 먼저 실패하거나, patch 문법·검증 literal·기존 bytecode cache 때문에 실제 구현과 무관한 실패가 발생했다.

## 확인된 원인

현재 계약과 실행 환경을 읽지 않고 기억으로 fixture·명령·패치를 작성했으며 Git ignored 상태를 파일 부재로 해석했다.

## 실패·해결 이력

payload 필드 추측, Markdown 목록 patch 충돌, literal 문구 과적합, 기존 `.pyc` 잔존이 반복적으로 검증을 방해했다.

## 해결과 검증

- fixture는 계약과 검증된 builder를 사용하고 작은 patch 뒤 실제 diff를 확인한다.
- 전체 회귀와 실제 cache 탐색을 분리해 구현 실패와 환경 실패를 구분했다.

## 재사용 규칙

- fixture 생성 실패와 테스트 대상 기능 실패를 분리한다.
- 복합 fixture는 현재 schema·validator 또는 공용 builder에서 만든다.
- patch 실패 뒤 부분 적용 여부와 실제 문맥을 먼저 확인한다.
- Git ignored는 파일 부재가 아니므로 cache는 filesystem에서 별도 검사한다.
- 검증 명령은 literal 문장보다 의미·구조·exit kind를 단언한다.
