# Creator main 공통 개발 상태

- 목적: 단일 workspace의 공통 구현 유지보수와 현재 재개 지점을 소유한다.
- 읽는 시점: 시작 문서 뒤.
- 책임: main 유지보수 세션과 사용자.
- 상태: session-close E3 반영·정리 완료. 보고 commit과 최종 Git 상태 확인 뒤 새 공통 요청 대기.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md, extension/docs/WORKSPACE.md.

## 현재 단계

E3 후편집 피크 경계값 수정·검증·설계 정리를 완료했다. 활성 설계는 없다. 결과·복구·검증 한계는 `extension/docs/reports/SESSION_CLOSE_GAMEPLAY_2026-10-23.md`가 소유한다. E1은 기존 완료 상태, E2 실제 게임 평가는 기존 보류를 유지한다.

공통 게임 편집 스킬은 `.agents/skills/edit-gameplay-video/`, 영상별 상태는 `extension/jobs/<job-id>/`가 소유한다. E3는 normalize_audio의 내부 피크 계산만 수정하며 최종 verify_audio와 기존 지원 범위를 유지한다.

## 직전 게이트

`test_gameplay_postproduction` 15개와 `test_edit_gameplay_video_skill` 15개, 총 30개 pass. 내부 TP 경계값·기본 여유값·잘못된 프로필 거부, 실제 합성 AAC의 최종 음량/피크·길이·샘플 수, 기존 최종 피크 실패 시 미게시를 확인했다. Python 구문·UTF-8·diff 검사 pass. 합성 결과는 실제 게임 의미·청취 검수 통과가 아니다.

## 승인 상태

E3의 설계·최소 수정·회귀 검사·단계별 로컬 커밋·이번 한시 설계 삭제·기존 `extension/docs/reports/SESSION_CLOSE_GAMEPLAY_2026-10-23.md` 갱신 커밋이 승인됐다. E2 실제 게임 전편·일반화 평가는 기존 보류를 유지한다. Core·규칙·모델·실제 영상·설치·외부 전송·push는 제외한다.

## 차단

없음. 단계별 선택 게이트와 commit 확인 뒤에만 다음 단계로 전환한다.

## 알려진 위험

실제 게임 영상의 재미·연속 A/V·직접 청취·실모델 추론·앱 재생·job runner 전체 실행은 E3에서 not_run이다. 내부 피크를 유효 범위로 제한해도 모든 음원의 최종 목표 달성을 보장하지 않으며, 최종 목표를 벗어나면 기존처럼 게시하지 않는다. 기존 상위 승인 경계·단일 CFR/샘플 정렬/Windows 잠금 등 지원 제약은 그대로다.

기존 ignored runtime/jobs는 보존하며, clean Git 상태와 디스크 자료 정리는 별개다. 작업 상태·승인·원본은 다른 job에서 재사용하지 않는다.

## 첫 다음 행동

1. 새 공통 작업을 시작할 때 git status --short --ignore-submodules=all과 state/main.md를 대조한다. 다른 작업의 변경이나 job 자료를 자동 정리하지 않는다.
2. 다음 게임 편집 요청이면 `.agents/skills/edit-gameplay-video/SKILL.md`의 준비 단계부터 해당 job의 입력·프로필·가능한 A/V 검수 방법을 확인한다.
3. 보류한 E2 실제 전편 평가는 별도 요청이 있을 때 범위와 방법을 확정한다. 합성 통과를 실제 게임 의미·청취 검수 완료로 사용하지 않는다.
