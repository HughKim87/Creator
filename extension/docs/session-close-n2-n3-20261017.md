# N2·N3 최소 개선 설계

- 목적: 자동 제작의 국소 보정과 일반 편집 승인 경계를 구분하고 기존 연속 실행을 검증한다.
- 읽는 시점: 이번 승인 개선의 구현·검증·정리 시.
- 책임: 에이전트가 main에서 승인 범위만 구현하고 사용자가 범위를 소유한다.
- 상태: active. 구현·검증 뒤 이 작업 전용 설계를 종료한다.
- 관련 권위: PROJECT_RULES.md, Core 작업 계약·규칙 거버넌스, session-close 스킬, 현재 사용자 N2·N3 실행 지시.

## 계약과 소유

대상은 D:/AI Agent/GitHub/Creator의 main, Creator Extension이다. 현재 세션의 확인 요청·지침 혼용과 기존 파일을 근거로 한다. 과거 성공 영상의 실제 재생이나 에이전트 독립 재현은 수행하지 않았다. Core는 읽기 전용이고 소비 경계·gitlink를 바꾸지 않는다.

- N2: coordinator의 내용 검수 절과 R03·R05 적용 경계만 보강한다. 승인 범위 안의 의미 보존 보정은 기존 검수 후 계속하며, 창작 변경·불확실한 의미·명시적 검수·외부 권한 경계는 유지한다.
- N3: 기존 workflow engine 및 검수 validator의 합성 회귀에 정상 자동 진행, 복구 후 진행, 실제 승인 대기와 중대 오류 차단을 대조한다. 테스트는 개발 검증이며 제작의 새 단계나 정책 정본이 아니다.
- 제외: N1 구조·필드 추가, 새 runtime API·schema·route·승인 단계, Core 변경, 보호 자료 접근, 다른 worktree 병합, 재제작, 설치·외부 쓰기·push.
- 최소 소유자: 기존 coordinator가 보정 판단을, R03·R05가 일반 편집 절차의 적용 범위를 소유한다. 별도 규칙 파일은 만들지 않는다.

## 단계와 성공 조건

0. 이 설계와 현재 상태의 참조만 로컬 커밋하고 snapshot 경로를 확인한다.
1. N2·N3를 하나의 논리적 구현 단계로 수행한다. 변경 표면은 coordinator SKILL.md, R03·R05 규칙, 기존 test_video_workflow_engine.py·test_video_session_improvements.py, 스킬 manifest와 state/main.md이다.
   - 진입: main·Core clean 확인, 설계 commit 확인.
   - goal: 정상·복구 경로에 확인을 추가하지 않고 필요한 승인·정확성 검사를 보존한다.
   - 필수 검사: 관련 workflow engine·job validation·session improvements·creative delegation unittest, 번들 무결성, diff --check, 수정 문구의 정상/국소 보정/의미 변경/음성 불확실/명시 검수/외부 권한 6개 문맥 대조.
   - 합성 검사는 기록·상태 전이 증거다. 실제 NotebookLM 전체 실행과 독립 Agent 행동 재현은 not_run으로 보고하며 그 실행을 이번 수정 완료의 필수 조건으로 추가하지 않는다.
   - 검토 뒤 기존 manifest만 갱신한다. 새 규칙·Core 의미·route는 추가하지 않는다.
   - goal·검사 pass 뒤 정확한 경로만 로컬 커밋하고 snapshot을 대조한다. fail이면 해당 원인만 수정하며 범위 확대는 하지 않는다.
2. 작업 전용 설계만 종료 제거하고 별도 정리 커밋한다. 고유 구현 근거는 규칙·테스트와 단계 commit이 보존한다. 기존 파일·cache는 정리하지 않는다.

## 정리와 보고

이번에 생성하는 유일한 임시 문서는 extension/docs/session-close-n2-n3-20261017.md이며 완료 후 정확히 이 파일만 제거한다. 설계·구현·정리 이력은 유지한다. 보고는 저장소 밖 C:/Users/Hugh/.codex/visualizations/2026/10/16/01a145f8-7cf9-7640-92a5-aae0fe8061b5/n2-n3-improvement-report.md에 보존한다. 이는 호출된 session-close의 작업 전용 설계·정리·보고 범위이며 추가 유지 정본이 아니다.

실패 시 마지막 검증 commit을 복구 기준으로 사용하되 무관한 파일을 reset하지 않는다. 완료는 관련 검사 pass, 정확한 commit·설계 정리, main과 Core 상태 대조, 보고 존재로 판단한다. main만 개선하며 다른 제작 worktree에 반영됐다고 주장하지 않는다.
