# Creator main 공통 개발 상태

- 목적: 공통 구현 유지보수의 현재 재개 지점과 검증 경계를 소유한다.
- 읽는 시점: 시작 문서 뒤.
- 책임: main 유지보수 세션과 사용자.
- 상태: Core 소비 갱신·adapter·규칙 정렬 완료. 후속 요청 대기.
- handoff mode: same-workspace. 실제 job 자료와 도구 설치는 로컬이며 전달·재설치는 별도다.
- 관련 권위: PROJECT_RULES.md, extension/docs/WORKSPACE.md.

## 현재 단계

활성 공통 구현 단계는 없다. Core 공개 호출 adapter는 Consumer cwd와 격리 bootstrap을 사용하고 Core 내부 cwd를 거부한다. 규칙은 기술 명세 owner 참조, source timebase, 영향에 맞는 사전검수, 위임/사용자 샘플 검수 주체를 정렬했다.

영상별 현재 상태·승인·미디어는 각 `extension/jobs/<job-id>/`가 소유한다. 공통 변경의 raw 근거는 `maintenance/agent-core-update-20261023/verification.json`에 있다. 기존 E3 오디오 피크 결과는 [이전 종료 보고](../extension/docs/reports/SESSION_CLOSE_GAMEPLAY_2026-10-23.md)의 역사 근거이며 이번 Core 검증과 혼합하지 않는다.

## 직전 게이트

`pass` — Core 고정 후보와 실제 Host gate, 실제 adapter verify/info의 contract 2·shared_data 1 조회, 관련 회귀와 규칙 행동 사례를 확인했다. 실제 영상 의미·청취·앱 승인의 통과는 아니다.

## 승인 상태

이번 Core 소비 연결·adapter/규칙·상태 정렬과 관련 로컬 commit이 승인됐다. Core 본문 개발·개인 스킬/모델 설치·실제 미디어 처리·외부 전송·게시·push는 제외한다. E2 실제 게임 전편·일반화 평가는 기존 보류를 유지한다.

## 차단

현재 공통 유지보수의 차단은 없다. 새 영상 작업은 exact job 입력·목적·승인과 필요한 도구 준비를 적용한다.

## 알려진 위험

이번에 실제 게임 영상 재미·연속 A/V·직접 청취·실모델 추론·Premiere 재생·job runner 전체를 검증하지 않았다. shared_data 쓰기 invoke나 원격 push 권한은 검증하지 않았다. 이전 E3의 피크 제한은 모든 음원의 목표 달성을 보장하지 않으며 기존 최종 피크 거부는 유지한다. ignored jobs/runtime과 사용자 자료는 보존하고 다른 job의 상태·승인을 승계하지 않는다.

## 첫 다음 행동

1. 새 공통 요청의 범위를 `PROJECT_RULES.md`와 현재 Git 변경에 대조한다.
2. 게임 편집 요청이면 `.agents/skills/edit-gameplay-video/SKILL.md`의 준비 단계와 명시된 job 상태·입력·가능한 A/V 검수 방법을 확인한다.
3. 보류한 E2 실제 전편 평가를 요청받으면 해당 범위·방법을 확정하고 합성 검증과 실제 사용 검증을 분리한다.
