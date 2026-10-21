# Creator main 공통 개발 상태

- 목적: 단일 workspace와 공통 구현 유지보수의 현재 상태를 소유한다.
- 읽는 시점: 시작 문서 뒤.
- 책임: main 유지보수 세션과 사용자.
- 상태: 통합·이전·복구 검증 완료. 활성 단계 없음.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md, extension/docs/WORKSPACE.md.

## 현재 단계

영상별 job·공용 runtime 코드와 브랜치 개선 흡수, archive 보관 및 worktree 퇴역을 완료했다. main의 기존 job·설치 runtime·data·cache도 외부 cleanup snapshot으로 옮겨 비웠다. 설계·복구 절차는 extension/docs/WORKSPACE.md, 출처·실측 gate는 extension/reports/workspace-consolidation-20261021.md가 소유한다.

## 직전 게이트

cleanup 대상의 이동 전후 파일 identity·metadata 일치와 main의 ignored·미추적 항목 부재를 확인했다. 기존 원본 복구 검증 결과는 외부 archive에 유지한다.

## 승인 상태

이번 로컬 통합·정리·커밋은 위임됐다. archive·before 태그·원래 브랜치·bundle을 유지한다. 영구 데이터 폐기·push·외부 게시·Core 변경은 위임되지 않았다.

## 차단

없음. 기존에 누락된 Zeus 원본은 사용자 지시로 제외한 상태다.

## 알려진 위험

새 제작 전체 실행·실모델 추론·Premiere 재생·개인설정 복호화와 로그인은 not_run이다. 파일 복원 검증을 이들 기능의 성공으로 확대하지 않는다. archive는 별도 물리 디스크 백업이 아니다.

## 첫 다음 행동

1. 영상 재개는 extension/docs/WORKSPACE.md의 cleanup snapshot에서 필요한 job·도구 경로를 먼저 복원한 뒤 해당 job의 state.md와 work/migration.json을 읽는다.
2. 새 영상은 scripts/creator_job.py init --job <job-id>로 생성하고 job runner 안에서 실행한다.
3. 복구가 필요하면 extension/docs/WORKSPACE.md의 복구 절차로 새 빈 경로에 snapshot을 복원한다.
