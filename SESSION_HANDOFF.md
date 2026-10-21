# Creator 현재 상태 안내

- 목적: main 공통 유지보수와 영상별 job의 상태 owner로 안내한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md 뒤.
- 책임: main 유지보수 세션과 해당 job 작업 세션.
- 상태: 안내판. 공통 유지보수와 개별 job의 상태 owner를 분리한다.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md의 영상별 작업 공간과 상태.

## 현재 단계

공통 구현과 유지보수는 state/main.md가 소유한다. 영상 데이터와 현재 상태는 extension/jobs/<job-id>/가 소유한다. 공용 도구의 사용 경로는 extension/docs/WORKSPACE.md를 따른다.

| 브랜치 | 상태 파일 |
|---|---|
| main | state/main.md |

## 직전 게이트

공통 현재 상태 안내를 실제 작업 상태와 대조했다. 제작·모델 추론·앱 재생 검증과는 구분한다.

## 승인 상태

E1의 현재 상태 안내 정정·단계별 로컬 커밋·임시 설계 정리·저장소 밖 종료 보고가 승인됐다. 개별 영상 제작·자료 처분·설치·외부 게시·push·Core 변경은 별도 작업 범위다.

## 차단

확인된 공통 차단은 없다. 실제 Git 변경과 개별 job의 차단은 작업 시작 시 해당 owner에서 확인한다.

## 알려진 위험

실제 모델 추론·Premiere 재생·로그인 검증은 이번 상태 안내 정정에서 실행하지 않았다. 공통 runtime의 제약은 state/main.md를, 개별 자료와 제작 기록의 한계는 해당 job의 state.md를 따른다.

## 첫 다음 행동

1. 공통 유지보수는 state/main.md를 읽는다.
2. 도구 경로는 scripts/creator_job.py runtime --component <component-id>로 조회한다. 진행 중 영상은 해당 job의 state.md를 읽는다.
3. 새 작업은 기존 job 재사용 여부와 범위를 먼저 확인하고, 필요한 경우에만 scripts/creator_job.py init --job <job-id>로 main 안에 만든다.

## 다음 세션 시작 prompt

시작 문서 뒤 state/main.md를 읽는다. 영상 작업은 명시된 job 폴더의 상태와 자료만 이어서 읽는다.
