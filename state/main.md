# Creator main 공통 개발 상태

- 목적: 단일 workspace와 공통 구현 유지보수의 현재 상태를 소유한다.
- 읽는 시점: 시작 3문서 뒤.
- 책임: main 유지보수 세션과 사용자.
- 상태: 코드 구현 완료, 기존 자료 정리 승인 대기.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md, extension/docs/WORKSPACE.md.

## 현재 단계

브랜치 개선 통합과 단일 workspace 구현을 마쳤다. 현재 단계는 기존 자료·output·worktree의 정확한 처분 확인이다. 전체 설계는 extension/docs/WORKSPACE.md, 출처·검증·정리 제안은 extension/reports/workspace-consolidation-20261021.md가 소유한다.

## 직전 게이트

job 격리·프로세스 잠금·실패/취소/재개·provenance·경로 이탈 및 관련 workflow 검사 통과. 기존 환경의 음성 단위 검사와 Replier 합성 검사 통과. before Git bundle 독립 복원 통과. 실제 전체 제작과 새 경로로 이전한 실데이터 검증은 not_run이다.

## 승인 상태

위임: 모든 브랜치의 재사용 개선 main 흡수, 영상별 폴더·공용 도구 구조와 관련 검증·로컬 커밋. 구현 선택은 권장안으로 진행한다.
미위임: 기존 파일 이동·삭제와 worktree 제거. 보고서의 정확한 대상·보존·복구 조건을 사용자에게 먼저 확인받는다. push·외부 게시·Core 수정은 제외한다.

## 차단

기존 자료 이전·정리와 worktree 제거는 사용자 대상 확인 대기다. 코드 구현 차단은 없다.

## 알려진 위험

Git 태그·bundle에는 Git 제외 미디어·설치 환경·비밀 설정이 들어 있지 않다. 기존 데이터는 원위치에 있다. XML은 외부 자산을 참조하므로 XML만 보존하면 편집 프로젝트를 복구할 수 없다. 기존 입력·private 설정은 정리 목록에서 제외했다.

## 첫 다음 행동

1. 사용자에게 extension/reports/workspace-consolidation-20261021.md의 보존·archive·worktree 대상에 대한 승인을 받는다.
2. 승인 후 로컬 cleanup-plan.json의 각 원본을 재확인하고 내용 hash·종속 자산·복구 owner와 이동 journal을 확보한다.
3. 작업별 최종 결과와 공용 도구를 이전·검증한 뒤에만 승인된 기존 경로를 처분한다. before 태그와 recovery bundle은 유지한다.
