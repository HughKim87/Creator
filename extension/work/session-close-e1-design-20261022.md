# E1 현재 상태 안내 정정 설계

- 목적: 실제 정리된 main과 오래된 상태 안내의 불일치를 없앤다.
- 읽는 시점: 승인된 E1 구현·검증·임시 설계 정리 시.
- 책임: Creator main 유지보수 세션.
- 상태: 사용자 승인 범위의 임시 설계. 검증 후 삭제하고 Git 이력에 보존한다.
- 관련 권위: session-close 스킬, PROJECT_RULES.md, Core의 단계 작업·버전 관리·현재 상태 규칙.

## 계약과 소유권

- 대상: D:/AI Agent/GitHub/Creator, main, Creator Host/Extension 상태 안내.
- 입력: 이번 대화에서 직접 확인한 작업과 교정, 현재 Git 상태, SESSION_HANDOFF.md, state/main.md.
- E1 분류: project_requirement. 공통 규칙 결함이 아닌 프로젝트 상태 기록의 지연이다.
- 관측: 두 상태 문서가 미커밋 삭제와 문서 수정이 남아 있다고 안내하지만 현재 main·Core·gitlink에는 변경이 없다.
- 변경 표면: SESSION_HANDOFF.md와 state/main.md의 현재 단계·직전 게이트·승인·차단·위험·첫 행동만 정정한다.
- 요청 대응: 오래된 미커밋 변경 안내 제거 → 두 상태 문서 → 실제 Git 상태와 문맥·snapshot 대조.
- 적용 조건: 현재 정리 상태를 안내할 때. 이후 생기는 변경을 clean으로 간주하거나 동적 Git 수치를 상시 정본으로 고정하지 않는다.
- Core 변경 후보는 보고만 한다. 이번에는 새 Core 개선을 제안할 근거가 없다.
- AInotebook의 완료 영상 복원은 execution_gap이었고 수정됐다. 중복 규칙을 만들지 않는다.
- 보호 경계: Core, job 입력·출력, 공용 runtime, 외부 원본·보관본을 변경하거나 새로 열거하지 않는다.
- 제외: 제작, 설치, 게시, 원격 Git 조작, 브랜치 전환, 데이터 처분, 실행·설정 참조의 별도 정리.
- 완료 수준: 같은 workspace의 검증된 문서 정정과 로컬 단계 커밋. 실제 영상 제작·모델 추론·로그인 검증은 not_run이다.

## 단계

### 0 — 설계 고정

- 진입: main과 Core가 clean이며 사용자가 E1과 외부 보고 위치를 승인했다.
- 작업: 이 파일만 커밋한다.
- 검증: 실제 root·branch 확인, 정확한 staged 경로, commit snapshot과 작업 트리 bytes 일치.
- 전환: 설계 내용·범위가 snapshot과 일치한 뒤에만 E1 구현을 시작한다.

### 1 — 현재 상태 안내 정정

- 진입: 0단계 snapshot 확인 완료, 무관한 변경 없음.
- 작업: 두 상태 문서에서 이미 해결된 미커밋 삭제·문서 작업 안내를 제거한다. 상태 문서의 필수 절과 미검증 위험은 유지한다.
- 검증: git diff --check, 두 문서의 필수 절·로컬 링크 존재 검사, 오래된 차단 제거 및 다음 행동 문맥 검토, 정확한 staged 경로와 commit snapshot bytes 대조.
- 성공: 새 세션이 현재 공통 도구·job 운영 안내로 진입하며 이미 끝난 정리를 다시 시작하도록 안내하지 않는다.
- 커밋: 두 상태 문서만 포함한다. Core·gitlink 불변을 확인한다.
- 전환: 문서 검사와 snapshot 대조가 모두 pass일 때만 정리한다.

### 2 — 임시 설계 정리와 종료 보고

- 진입: 1단계 성공·커밋 확인.
- 작업: 이번에 만든 이 설계 파일만 삭제하고 별도 정리 커밋을 만든다. 앞선 이력은 유지한다.
- 정확한 임시 경로: D:/AI Agent/GitHub/Creator/extension/work/session-close-e1-design-20261022.md.
- 보고 위치: D:/AI Agent/Creator-session-close-report-20261022.md. 사용자 승인된 저장소 밖 보존 보고이며 임시 자원이 아니다.
- 검증: 설계 부재, 최종 두 상태 문서만 순변경, main·Core·gitlink clean, 보고 내용과 실제 커밋·검사 대조, 보고 후 최종 상태 재확인.

## 실패와 복구

- 무관한 변경이나 대상 변경은 중단하고 처리 결정을 받는다.
- 검사 fail/not_run이면 다음 단계로 전환하지 않고 현재 단계의 원인만 해결한다.
- 복구 기준은 직전 검증 commit이며 임의 reset·stash·사용자 파일 처분은 하지 않는다.
- 범위·성공 조건·Core 변경이 필요하면 기존 승인으로 확대하지 않는다.
- 적용 불필요한 게이트: 코드·규칙·route 변경, 제작·설치·배포가 없으므로 전체 회귀·독립 Agent 의미 감사·clean clone은 not_applicable이다.
