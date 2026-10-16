# E1 시청자 관점 분석 개선 설계

- 목적: 승인된 E1을 원본 근거에 연결된 편집 방향 선택으로 구현한다.
- 읽는 시점: 이 작업의 실행·재개·정리 시.
- 책임: main 작업 에이전트가 실행·검증하고 사용자가 범위와 로컬 커밋을 승인한다.
- 상태: 작업 전용 임시 설계. 완료 후 제거하며 복구와 완료 근거는 Git이 소유한다.
- 관련 권위: PROJECT_RULES.md, Core 단계 작업·버전 관리·규칙 거버넌스, session-close.

## 전체 설계

- 분석 원본: 이 채팅에서 수행한 main 정리와 다른 워크트리 검사. 다른 세션은 수집하지 않는다. dokkaebi `fe86d7a`의 공통 편집 개선이 main에 없는 것을 직접 비교했다. 실제 영상 성과는 검증하지 않았다.
- 대상: `D:/AI Agent/GitHub/Creator`, `main`, Host. Extension은 영상 도메인 작업을 소유한다. Core는 읽기 전용이며 gitlink를 변경하지 않는다. 다른 워크트리에는 쓰지 않는다.
- 승인: 사용자가 main 선택 후 E1 설명을 받고 진행을 지시했다. 설계·구현·정리 각각 로컬 커밋, 아래 임시 설계 제거와 저장소 밖 보고를 포함한다. push·설치·외부 쓰기와 보호 데이터 접근은 제외한다.
- 진입: main HEAD `4160b64`, 부모·Core 미커밋 변경 없음을 확인. 기존 ignored runtime/data는 기존 자원으로 보존한다.
- 입력: main의 편집 계약, 입력·스토리 규칙, 기존 routing/workflow 검사와 source commit. 특정 영상의 자료·상태·스타일은 흡수하지 않는다.
- 소유권: 영상의 시청자 궁금증과 source anchor 연결은 Extension 도메인 책임이다. Core 일반화/규칙 의미 변경은 해당 없음. 기존 R03/R05/R06의 조건 안에서 보강하고 활성 route는 유지한다.
- 적용: 방향 미정의 new_full_edit에서 내용 지도 뒤 질문별 근거·공백을 정리하고 방향과 도입·결말에 연결한다. 자막 오인식·화자 불확실성을 사실로 승격하지 않는다.
- near-miss: 승인 방향 재사용, approved_delta, format_regeneration, 국소 calibration에 전체 신규 분석을 강제하지 않는다. 필요한 영향 범위만 확인한다. 무발화 원본에는 발화·화자 검증이 비해당이며 자막을 억지로 만들지 않는다.

| 요청 조건 | 변경 표면 | 필수 검증 |
|---|---|---|
| 내용 지도 → 궁금증 → 방향 선택 연결 | VIDEO_EDITING_WORKFLOW_CONTRACT.md, R03/R05 | 문맥 대조 + 기존 규칙/계약 회귀 |
| 질문마다 원본 근거 또는 공백, 없는 답 생성 금지 | R05, 재현 사례 TC41 | 답 있음/없음 시나리오 대조 |
| 자막·화자 불확실성 구분 | 계약, R05 | 불명 화자/무발화 시나리오 대조 |
| 질문에서 도입 선택·결말 회수 | R06 | 회수 가능/불가능 시나리오 대조 |
| 국소 수정에 전체 재분석 강제 금지 | 계약/R03/R05, TC42 | approved_delta/format_regeneration 대조 |
| 기존 승인·보호·fingerprint 유지 | 동일 파일의 scoped diff | 기존 회귀, diff 검사, Core 불변 |

## 단계와 성공 조건

0. 이 설계와 main의 활성 상태만 커밋. snapshot 경로·내용과 승인 범위를 대조한 후 구현 진입.
1. E1 구현 및 검증. 정확한 변경 경로는 위 계약·규칙 두 파일, `extension/tests/test_extension_rule_routing.py`, `extension/tests/test_video_editing_workflow.py`, `state/main.md`다. 재현 사례 ID는 TC41~TC42로 확장하고 기존 사례와 승인 경계를 보존한다. 필수 검사는 아래 명령·문맥 대조·diff 검사다. pass 후 해당 단계 변경만 커밋하고 snapshot과 작업 트리 일치를 확인한다.
2. 설계의 고유 결정은 구현 정본과 단계 커밋에 남기고 이 설계만 제거한다. 상태의 활성 링크를 해제하고 정리 커밋을 만든다. 부모와 Core clean 및 설계 잔존 참조 없음 확인 후 저장소 밖 보고를 작성한다.

## 현재 구현 단계 정의

- 진입: 0단계 커밋 snapshot 확인, main 동일성 및 무관 변경 없음.
- 작업: 승인된 E1 의미만 위 기존 owner에 반영. 원래 source commit 전체를 cherry-pick하지 않는다. 새 schema·runtime·성과 추정은 추가하지 않는다.
- 검사: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=extension/src`로 `python -m unittest extension.tests.test_extension_rule_routing extension.tests.test_video_editing_workflow extension.tests.test_worktree_state_files` 실행. Core 소비 runtime은 실행하지 않는다. `git diff --check`와 변경 문맥을 직접 대조한다.
- 의미 대조: 질문에 근거 있음, 답 없음, 화자 불명, 무발화, 방향 확정, approved_delta, format_regeneration, calibration 총 8개를 문맥 검토한다. 독립 Agent 재현·실제 제작·조회수 효과는 not_run이며 완료 주장에 포함하지 않는다. route·Core 의미는 바꾸지 않아 독립 route/Core 감사는 비해당이다.
- 판정: 위 필수 게이트 실제 통과면 pass. 미실행은 not_run, 실패는 fail로 두고 다음 단계로 전환하지 않는다. 실패 시 현재 단계에서 원인에 맞는 최소 수정 후 관련 검사 재실행. 범위 확대·새 무관 변경은 멈추고 필요한 결정을 받는다.
- 커밋: 정확한 경로만 stage, 검증과 이유를 메시지에 기록. 커밋 후 show 경로와 HEAD diff를 대조한다. 릴리스·패키징 주장이 없어 clean clone은 비해당이다.
- 복구: 설계 및 구현 commit이 복구 지점이며 승인 없는 reset·stash·사용자 자원 삭제는 하지 않는다.

## 정리와 보고

- 이번 생성 임시 자원: 이 설계 파일 하나. Git snapshot에서 복구 가능하며 최종 정리 단계에서 정확한 파일만 제거한다. 별도 scratch·설치·cache는 만들지 않는다. Python bytecode 생성을 비활성화한다.
- 최종 보고: `C:/Users/Hugh/.codex/visualizations/2026/10/11/01a12b91-7a7d-7651-8c68-5cff72b351ca/session-close-report.md`. 보고는 유지하고 repository에는 넣지 않는다.
- 최종 성공: 승인 E1만 구현, 필수 검증 pass, 설계·구현·정리 커밋 확인, 설계 및 활성 링크 없음, main/Core clean, 기존 자원 보존, 보고의 실제 근거/한계 일치.
