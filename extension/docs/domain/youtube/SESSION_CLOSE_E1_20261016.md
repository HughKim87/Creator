# E1 조회수 전망 근거 개선 설계

- 목적: 승인된 E1을 설계·개선·정리의 로컬 커밋으로 수행한다.
- 읽는 시점: 이 작업을 실행하거나 재개할 때.
- 책임: 에이전트가 승인 범위와 검증을 지키며 사용자에게 결과를 보고한다.
- 상태: 활성 한시 설계. 정리 단계에서 삭제하고 Git 이력으로 보존한다.
- 관련 권위: session-close 스킬, PROJECT_RULES.md, core/PROJECT_RULES.md.

## 전체 계약

- 분석 원본은 현재 대화뿐이다. 공개 유사 영상에 임의의 후발 계수를 곱해 작은 채널의 기대 조회수처럼 제시한 뒤 근거 부족을 정정한 사실을 사용한다. 계정 수치·영상명·대화 원문을 공통 스킬에 복제하지 않는다.
- 대상: D:/AI Agent/GitHub/Creator, main, 시작 HEAD de1ae612ff5f732a5db7d832ff38aeb43447df23. 관련 Core는 읽기 전용이며 부모 gitlink를 바꾸지 않는다.
- 승인: E1 진행, E2·E3 보류. 기존 game-trend-brief와 main 상태의 국소 수정, 설계/개선/정리 로컬 커밋, 이번 설계 삭제, 저장소 밖 보고서 작성.
- 결과: 비교 영상의 수요 관측과 사용자 채널의 조회수 예측을 분리한다. 수치 전망은 비교 조건·관측 기간·표본·산정 근거를 설명할 때만 제공하고 부족하면 예측 불가로 보고한다. 요청된 가정 계산은 시나리오로 구별한다.
- 소유권: YouTube 소재 선정이라는 기존 Extension skill의 책임이다. Core 규칙·route·실행 API를 바꿀 필요가 없다.
- near-miss: 경쟁 영상의 실측 조회수 인용은 계속 허용한다. 사용자가 특정 가정의 산술 계산을 요청하면 계산은 허용하되 예상 성과로 제시하지 않는다. 근거 있는 수치 전망을 일률 금지하지 않는다.
- 제외: E2 외부 코치 플러그인, E3 썸네일 계약, 브라우저 adapter, 다른 워크트리, 영상별 자료, inputs/outputs, 설치, push, 원격 쓰기.

## 단계와 검증

### 0단계: 설계 체크포인트

- 진입: main과 Core의 비보호 tracked/untracked 상태 clean, Core gitlink/HEAD 일치, E1 승인.
- 변경: 이 설계와 state/main.md의 활성 단계 참조.
- 게이트: 승인 범위·단계·정확한 임시 경로·보호 경계·필수 검사/한계의 수동 대조, git diff --check.
- 커밋: 정확한 두 경로만 stage. git show로 snapshot의 경로와 설계 bytes 일치를 확인한 뒤 1단계로 간다.

### 1단계: E1 구현과 검증

- 진입: 0단계 커밋 확인, 예상하지 않은 local change 없음.
- 변경: .agents/skills/game-trend-brief/SKILL.md의 설명·후발 진입성·출력·전달/게이트를 하나의 전망 판단 절로 일관되게 연결한다. state/main.md에는 현재 상태만 남긴다.
- 필수 게이트: UTF-8/frontmatter 이름·설명 확인, Markdown 코드 fence/변경 diff 점검, 아래 6개 합성 시나리오의 수동 문맥 대조, 기존 test_video_session_improvements·test_title_thumbnail_package·test_worktree_state_files 및 영상 스킬 번들 무결성 검사.
- 시나리오: 대형 채널만 관측 / 작은 채널의 다른 형식·기간 / 비교 가능한 자기 채널 과거 표본 / 사용자가 지정한 계수 계산 / 수요는 확인되나 예측 자료 부족 / 낮은 조회수 사례와 비교 한계 포함. 각각 과잉 예측을 막고 허용된 관측·조건부 추정·시나리오 계산을 유지하는지 확인한다.
- 공식 quick_validate는 현 runtime에 PyYAML이 없어 not_run으로 공개한다. 설치하지 않는다. 위 최소 구조 검사는 이를 대체한 공식 통과나 Agent 행동 검증이라고 주장하지 않는다.
- 성공/커밋: 필수 게이트 pass 후 skill과 state만 stage한다. git show의 경로·skill bytes를 검증한 뒤 2단계로 간다. 릴리스/독립 재현성/실제 성과는 주장하지 않으므로 clean clone과 실제 채널 실험은 선택하지 않는다.

### 2단계: 정리와 보고

- 진입: 1단계 커밋과 선택 필수 게이트 pass.
- 삭제 대상은 이 작업에서 새로 만든 extension/docs/domain/youtube/SESSION_CLOSE_E1_20261016.md 한 파일뿐이다. 설계 고유 내용은 0단계 commit으로 복원된다. 기존 사용자 파일·cache·다른 작업 자원은 보존한다.
- state/main.md에서 활성 설계 참조를 제거한다. 스킬의 현재 행동과 성과 미검증 한계를 짧게 보존한다. 참조가 남지 않았는지 확인하고 삭제/state 변경을 별도 정리 커밋한다.
- 최종 보고: C:/Users/Hugh/.codex/visualizations/2026/10/13/01a1341e-3945-7502-9366-f8b0f504e992/session-close-e1-20261016.md. 보존 보고서이며 삭제 대상이 아니다.
- 게이트: 설계 부재·활성 참조 없음, 최종 skill 내용 유지, diff 검사, main/Core 변경 없음과 gitlink 불변, 실제 commit별 경로 대조. 보고서 저장 뒤 Git 상태도 다시 확인한다.

## 실패·복구·완료 수준

- 필수 fail/not_run이면 해당 단계에 머물러 원인을 해결한다. 승인 밖 변경이나 무관한 local change는 멈추고 결정을 받는다. reset/stash/clean 또는 기존 사용자 파일 처분은 위임되지 않았다.
- 마지막 검증 commit이 복구 근거다. 되돌림이 필요하면 정확한 영향·범위를 확인하고 현재 승인으로 가능한 국소 수정만 수행한다.
- 수동 문맥 대조는 독립 Agent 재현이 아니다. 실제 게시 후 조회수·CTR 개선은 not_measured다. 최종 성공은 승인된 E1·정리·로컬 commit snapshot·보고서와 clean 상태까지다.
