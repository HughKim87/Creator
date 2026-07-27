# 세션 핸드오프

- 갱신일: 2026-07-27
- 역할: 현재 work·blocker·검증 상태·첫 다음 행동의 단일 owner
- 현재 작업: 없음
- 상태: 이전 구현의 장점을 현재 근간에 선별 적용한 G0~G5 완료 후 대기
- blocker·사용자 결정 대기: 실제 Premiere CS6 import·재생 검수는 exact 보호 원본·출력·목적 승인이 필요한 별도 사용자 gate
- 검증된 현재 상태: 운영 규칙 R01~R12를 늘리지 않고 Claude 진입점, 원본 불변 SRT 정리, legacy CSV 이관·다중 진단, 기존 `sequence-v5` byte 호환, 명시적 `premiere-cs6-v4` 구조 profile을 추가했다. 합성 수직 acceptance와 Core 110개·Extension 107개, 총 217개 회귀가 통과했다. 실제 보호 데이터와 `core/`는 변경하지 않았고 push도 하지 않았다.
- 첫 다음 행동: 사용자가 exact 보호 원본·출력과 목적을 지정하면 운영 계약에 따라 실제 SRT·timeline·CS6 XML을 만들고 Premiere import·재생 gate를 확인한다.
