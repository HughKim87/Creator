# Gameplay session-close E1 설계

- 목적: MP4 후보 출력 뒤 선택적 전사 입력 오류가 발생하는 순서를 수정한다.
- 읽는 시점: 승인된 E1 구현·검증·단계 전환 시.
- 책임: Creator main 유지보수 에이전트. 사용자 승인: 2026-10-23 “E1만 진행”.
- 상태: 승인된 한시 설계. 완료 후 정확한 이 파일만 제거하고 Git 이력으로 복구한다.
- 관련 권위: PROJECT_RULES.md, session-close 스킬, Core 작업 계약·단계 설계·버전 관리·문서·정리 규칙.

## 범위와 소유

- 대상: `D:/AI Agent/GitHub/Creator`, `main`, Extension의 게임플레이 후보 CLI.
- 진입: tracked/untracked/conflict/gitlink 변경 없음. Core submodule도 clean. 기존 ignored runtime/jobs는 보존한다.
- 분석 원본: 이번 대화의 후보 출력 도구 작성·검증과 현재 동일 도구. 다른 세션 원문과 실제 게임 미디어는 수집하지 않는다.
- 관측: 메모리 모형에서 `main()`에 잘못된 `--raw-json`을 주면 `render` 호출 뒤 ValueError가 발생했다. 실제 영상을 생성한 재현이 아니라 호출 순서의 재현이다.
- 분류: E1 `execution_gap` / 구현 결함. 기존 입력·출력 판정 원칙은 충분하며 새 규칙이나 Core 수정이 필요하지 않다.
- 적용: `--raw-json`이 있을 때 파일 읽기와 단어 경계 힌트 계산이 MP4 출력보다 앞서야 한다.
- near-miss: 전사 옵션이 없는 기존 호출과 정상 전사 호출은 유지한다. ASR 힌트는 의미·발화 품질 pass가 아니다.
- E2: 실제 게임 전편·다른 게임 일반화 평가를 사용자 지시로 보류한다. 검수 한계로 보고하며 필수 게이트에 포함하지 않는다.

## 계약 대응

| 요청 조건 | 변경 표면 | 필수 검증 |
|---|---|---|
| 전사 오류 전에 렌더가 시작되지 않음 | `.agents/skills/edit-gameplay-video/scripts/render_candidate.py`의 main 입력 순서 | 잘못된 JSON·단어 시각·파일 부재에서 render 미호출 |
| 정상·무전사 경로 유지 | 동일 main의 findings 결과 연결 | 정상 힌트 반환과 옵션 없는 호출 회귀 |
| 원본/출력 보호와 A/V 연결 유지 | 구현은 기존 render를 바꾸지 않음 | 기존 합성 MP4·J/L 오디오·원본 hash·비덮어쓰기 검사 |
| 결과 근거·재개 상태 보존 | 기존 테스트 파일, state/main.md, 승인된 최종 보고 | 검사 실제 실행, snapshot 경로/내용, clean/Core 불변 |

설치·외부 전송·push·모델·실제 미디어·정책·스킬 문법·후편집 도구는 제외한다. 단어 시각의 진실이나 재미를 자동 승인하는 기능을 추가하지 않는다. 직접 재생·청취·실제 job 전편 실행은 not_run이다.

## 단계

### 0 — 설계 고정

- 진입: 사용자 E1·단계별 로컬 커밋·설계 제거·내부 보고 승인과 clean 대상.
- 작업: 이 한시 설계 작성. 구현은 아직 변경하지 않는다.
- 게이트: 승인 범위와 경로·성공 조건 대조, UTF-8·diff 확인.
- 커밋: 이 파일 하나. `git show`와 blob 동일성으로 실제 snapshot을 확인한다.
- 전환: 설계 내용이 commit에 존재하고 작업 트리와 같을 때만 1단계.

### 1 — E1 수정·검증

- 진입: 0단계 게이트와 커밋 확인, 새 무관 변경 없음.
- 작업: raw 읽기·speech_findings를 render 전에 실행하고 결과를 재사용한다. 기존 테스트 파일에 오류/정상/옵션 없음의 CLI 호출 순서 회귀를 추가한다. 필요한 오류 정규화는 이 입력에만 한정한다.
- 필수 게이트: `PYTHONPATH=extension/src;extension/tests`, bytecode 금지로 `python -B -m unittest test_edit_gameplay_video_skill -v`. 신규 CLI 오류에서 render 호출 0, 정상 경로 유지, 기존 합성 미디어 검사 pass. 실제 게임·모델·의미 평가는 해당 없음이다.
- 근거 수준: CLI 모형은 호출 순서, 기존 합성 FFmpeg는 A/V 기술 연결을 증명한다. 의미 검수는 증명하지 않는다.
- 커밋: script, `extension/tests/test_edit_gameplay_video_skill.py`, `state/main.md`만. 상태는 현재 단계·첫 다음 행동을 기록한다.
- 전환: 테스트 전부 pass, diff/snapshot 범위와 blob 일치, commit 확인 후에만 정리한다.

### 2 — 한시 설계 정리

- 진입: 1단계 성공·커밋·snapshot 확인. 고유 설계는 0단계 Git에서 복구 가능하다.
- 작업: 이번에 만든 이 파일만 제거하고 state/main.md의 활성 설계 링크를 해제한다. 기존 runtime/jobs/다른 문서는 처분하지 않는다.
- 게이트: root 내부 실제 경로·비링크·파일 동일성 확인, 남은 활성 참조 0, 삭제 뒤 파일 부재·개선 파일 유지·diff 검사.
- 커밋: 설계 삭제와 상태 전환만 별도 정리 commit. history를 squash/reset하지 않는다.
- 전환: 삭제 snapshot·보존 파일 확인 후 보고한다.

### 3 — 보고와 종료

- 작업: `extension/docs/reports/SESSION_CLOSE_GAMEPLAY_2026-10-23.md`에 목적·승인·전후 동작·E1/E2 처분·소유 판단·단계 commit·검사/한계·정리와 최종 Git 상태를 기록한다. 이 보고는 보존 산출물이며 임시 정리 대상이 아니다.
- 게이트: 실제 앞 단계 commit과 내용 대조, 내부 경로·링크·인코딩·diff 확인. 보고 전 예상 상태를 확인하고 보고 commit 뒤 main/Core가 clean인지 재검사한다.
- 커밋: 보고와 필요한 state/main.md의 현재 상태만. 보고 자체 commit ID는 자기 본문에 쓰지 않고 최종 응답에서 식별한다.
- 종료: 모든 승인 단계·필수 게이트·commit 확인·미결 0일 때만 스킬의 종료 표시를 쓴다.

## 임시 자원·복구

유일한 Agent 삭제 대상은 이 설계 파일이다. 테스트가 같은 호출에서 생성한 합성 fixture는 기존 TemporaryDirectory 수명으로 정리하며 공유 부모를 삭제하지 않는다. 새 외부 보존 경로·백업 사본·추가 보고서를 만들지 않는다. 테스트 실행 결과의 요약은 구현 commit과 최종 보고가 보존한다.

현재 HEAD를 마지막 복구 지점으로 삼되 reset·stash·clean을 자동 실행하지 않는다. 필수 검증 실패·무관 변경·범위 확대가 있으면 다음 단계로 넘어가지 않고 현재 원인과 필요한 결정을 보고한다. 같은 실패를 새 근거 없이 반복하지 않는다. 릴리스·clean clone·독립 Agent 평가를 주장하지 않으므로 그 검사는 필수 범위가 아니다.
