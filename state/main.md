# Creator main 공통 개발 상태

- 목적: 단일 workspace와 공통 구현 유지보수의 현재 상태를 소유한다.
- 읽는 시점: 시작 문서 뒤.
- 책임: main 유지보수 세션과 사용자.
- 상태: 통합·이전·복구 검증 완료. 활성 단계 없음.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md, extension/docs/WORKSPACE.md.

## 현재 단계

main의 영상별 job·공용 runtime 구조와 브랜치 개선 흡수, 기존 자료의 archive 보관 및 worktree 퇴역을 완료했다. 설계·복구 절차는 extension/docs/WORKSPACE.md, 출처·실측 gate는 extension/reports/workspace-consolidation-20261021.md가 소유한다.

## 직전 게이트

원본별 archive 복구 기록·내용 해시·비공개 개인설정 복원, 이전 경로의 실행·import·모델 manifest, XML 참조와 기존 worktree 퇴역 gate를 통과했다.

## 승인 상태

이번 로컬 통합·정리·커밋은 위임됐다. archive·before 태그·원래 브랜치·bundle을 유지한다. 영구 데이터 폐기·push·외부 게시·Core 변경은 위임되지 않았다.

## 차단

없음. 기존에 누락된 Zeus 원본은 사용자 지시로 제외한 상태다.

## 알려진 위험

새 제작 전체 실행·실모델 추론·Premiere 재생·개인설정 복호화와 로그인은 not_run이다. 파일 복원 검증을 이들 기능의 성공으로 확대하지 않는다. archive는 별도 물리 디스크 백업이 아니다.

## 첫 다음 행동

1. 영상 재개는 해당 job의 state.md와 work/migration.json을 읽는다.
2. 새 영상은 scripts/creator_job.py init --job <job-id>로 생성하고 job runner 안에서 실행한다.
3. 복구가 필요하면 extension/docs/WORKSPACE.md의 복구 절차로 새 빈 경로에 snapshot을 복원한다.
