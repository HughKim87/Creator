# Creator 현재 상태 안내

- 목적: main 공통 유지보수와 영상별 job의 상태 owner로 안내한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md 뒤.
- 책임: main 유지보수 세션과 해당 job 작업 세션.
- 상태: 안내판. 활성 전체 설계·단계 설계 없음.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md의 영상별 작업 공간과 상태.

## 현재 단계

공통 구현과 유지보수는 state/main.md가 소유한다. 영상 데이터와 현재 상태는 extension/jobs/<job-id>/가 소유한다. 공용 도구의 사용 경로는 extension/docs/WORKSPACE.md를 따른다.

| 브랜치 | 상태 파일 |
|---|---|
| main | state/main.md |

## 직전 게이트

공용 도구의 main 내 재배치와 경로·기본 실행 확인을 마쳤다. 운영 안내에서 종료된 자료의 백업·복구 경로를 제거했다.

## 승인 상태

운영 문서의 이전 백업·복구 안내 제거가 승인됐다. 외부 게시·push·영구 데이터 폐기·Core 변경은 이번 작업 범위가 아니다.

## 차단

없음.

## 알려진 위험

실제 모델 추론·Premiere 재생·로그인 검증은 이번 문서 정리에서 실행하지 않았다. 남아 있는 전용 기능 참조와 미커밋 변경은 state/main.md를 따른다.

## 첫 다음 행동

1. 공통 유지보수는 state/main.md를 읽는다.
2. 도구 경로는 scripts/creator_job.py runtime --component <component-id>로 조회한다. 진행 중 영상은 해당 job의 state.md를 읽는다.
3. 새 영상은 scripts/creator_job.py init --job <job-id>로 main 안에 만든다.

## 다음 세션 시작 prompt

시작 문서 뒤 state/main.md를 읽는다. 영상 작업은 명시된 job 폴더의 상태와 자료만 이어서 읽는다.
