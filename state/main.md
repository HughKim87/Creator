# Creator main 공통 개발 상태

- 목적: 단일 workspace와 공통 구현 유지보수의 현재 상태를 소유한다.
- 읽는 시점: 시작 문서 뒤.
- 책임: main 유지보수 세션과 사용자.
- 상태: 공용 도구 재배치 완료. 문서의 이전 백업·복구 안내 정리.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md, extension/docs/WORKSPACE.md.

## 현재 단계

영상별 job·공용 runtime 구조는 유지한다. 공용 도구는 extension/.runtime에서 재사용하며 운영 안내는 extension/docs/WORKSPACE.md가 소유한다. 종료된 전용 파일의 이동에 따른 미커밋 삭제가 남아 있고, 전용 앱의 실행·설정 참조 정리는 별도 후속 범위다.

## 직전 게이트

공용 도구 재배치 후 파일 동일성·catalog 경로·기본 실행을 확인했다. 운영 안내에서 이전 자료의 백업·복구 절차와 해당 절차로 향하던 상태 안내를 제거했다.

## 승인 상태

현재 위임은 문서의 이전 백업·복구 안내 제거다. 브랜치·태그와 Git 이력은 변경하지 않았다. 영구 데이터 폐기·push·외부 게시·Core 변경은 이번 작업에 포함하지 않는다.

## 차단

문서 수정의 차단은 없다. 새 job 실행 전에는 미커밋 공통 코드 변경을 정리해야 한다.

## 알려진 위험

새 제작 전체 실행·실모델 추론·Premiere 재생·로그인은 not_run이다. 두 TTS 가상환경의 기반 Python은 Creator 밖의 Codex 기본 runtime을 사용한다. 전용 파일 이동에 따른 삭제 상태와 남은 참조를 정리하지 않은 채 새 제작을 시작하지 않는다.

## 첫 다음 행동

1. git status --short --ignore-submodules=all로 기존 미커밋 삭제와 이번 문서 변경을 대조하고, 추가 정리는 사용자 요청 범위를 확인한다.
2. 도구는 scripts/creator_job.py runtime --component <component-id>로 현재 경로를 조회한다.
3. 새 제작을 요청받으면 미커밋 코드 상태를 먼저 정리한 뒤 scripts/creator_job.py init --job <job-id>로 job을 생성하고 job runner 안에서 실행한다.
