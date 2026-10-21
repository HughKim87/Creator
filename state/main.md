# Creator main 공통 개발 상태

- 목적: 공통 구현 유지보수와 단일 workspace 전환의 현재 상태를 소유한다.
- 읽는 시점: 시작 세 문서 뒤.
- 책임: main 유지보수 세션과 사용자.
- 상태: 단일 workspace 전환 진행.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md, extension/docs/WORKSPACE.md.

## 현재 단계

복구 지점 확보 완료 후보. 전체 설계와 단계별 게이트는 `extension/docs/WORKSPACE.md`가 소유한다. 다음 단계는 브랜치 개선 통합이다.

## 직전 게이트

로컬 before 태그와 브랜치별 복구 태그를 생성하고 원본 커밋과 대조했다. 기존 worktree의 부모 저장소 추적 변경은 없었다. ignored 데이터는 원래 위치에 유지하며 metadata 목록은 로컬 extension/data/consolidation/baseline.json에 있다.

## 승인 상태

위임: before 및 브랜치 복구 지점, 모든 브랜치의 개선사항 main 흡수, 영상별 폴더·공용 도구 구조 구현·검증·로컬 커밋. 합리적인 구현 선택은 권장안으로 진행한다.
미위임: 기존 자료 이동·삭제, worktree 제거. 정확한 대상과 보존·복구 방법을 제시해 먼저 확인받는다. push·외부 게시·Core 수정은 제외한다.

## 차단

구현 차단 없음. 최종 자료 처분은 대상별 승인 대기 전 단계다.

## 알려진 위험

Git 태그는 미추적·ignored 데이터와 설치 환경을 백업하지 않는다. 기존 자료를 유지하고 삭제 전 별도의 복구 가능성을 확보한다. 실제 앱·GPU와 새 구조의 전체 제작은 아직 검증하지 않았다.

## 첫 다음 행동

1. branch별 공통 조상 이후 변경을 main과 대조해 개선사항을 누락 없이 판정한다.
2. 고유 공통 구현을 main에 반영하고 관련 검사·앱 빌드를 실행한다.
3. 기존 자료 이동·삭제 없이 job 경로·공용 runtime과 제작 진입점을 구현한다.
