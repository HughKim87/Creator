# E3 후편집 피크 목표 경계값 개선 설계

- 목적: 승인된 E3 구현 결함만 수정하고 단계별 검증·커밋·정리·보고를 완료한다.
- 읽는 시점: 이번 E3 단계 실행·전환·복구 시.
- 책임: Creator main 유지보수 에이전트. 사용자가 E3 전 단계의 로컬 커밋과 이번 설계 정리를 승인했다.
- 상태: 한시 설계. 구현·검증·설계 snapshot 대조 뒤 정리 단계에서 제거하며 Git에서 복구한다.
- 관련 권위: 사용자 E3 진행 승인, session-close 스킬, PROJECT_RULES.md 및 선택된 Core 작업 계약·단계 설계·버전 관리·정리 규칙.

## 계약과 근거

저장소·워크트리는 `D:/AI Agent/GitHub/Creator`, 역할은 Host, 브랜치는 `main`이다. 진입 시 부모와 Core submodule에 미커밋 변경이 없고 gitlink가 일치했다. Core는 읽기 전용이다. 기존 ignored runtime/jobs는 보존한다.

분석 원본은 이 대화의 후편집 구현·회귀·커밋 경험과 현재 exact 코드다. E1은 현재 main에서 이미 해결됐고 중복 구현하지 않는다. 실제 게임 미디어나 다른 세션 원문은 수집하지 않았다.

E3는 `execution_gap`에 해당하는 Extension 구현 결함이다. postprocess.py의 loudness_config는 -9 및 -8.8 dBTP를 허용하지만 normalize_audio가 0.4를 빼면서 FFmpeg의 TP 유효 범위 [-9,0] 밖 값을 전달한다. 기존 FFmpeg와 합성 sine/null 출력으로 두 실패와 -1 기본값 정상 종료를 직접 확인했다. R22의 프로필 준수·최종 측정 요구는 충분하며 Core·규칙 문구를 추가할 필요가 없다.

| 요청 조건 | 변경 표면 | 선택 필수 검증 |
|---|---|---|
| 유효 프로필에서 내부 FFmpeg TP 범위를 벗어나지 않음 | scripts/postprocess.py의 normalize_audio | -9/-8.8/-8.6/-1에서 측정·정규화 양쪽 TP와 실제 FFmpeg AAC 결과 검사 |
| 기본 여유값·최종 통합 음량/피크 gate 보존 | 같은 함수, 기존 최종 검사 불변 | -1→-1.4 유지, 기존 최종 초과 시 미게시 회귀 |
| 범위 밖/비정상 프로필을 새로 허용하지 않음 | 기존 loudness_config 불변 | 유효 범위 밖·NaN/bool 입력 거부 확인 |
| 승인 범위·복구·보고 | 기존 테스트 파일·state/main.md·기존 종료 보고 | 정확한 단계별 snapshot, 문서·링크·Git 상태 대조 |

최소 수정은 normalize_audio 안에서 내부 목표를 `max(-9, true_peak_dbtp - 0.4)`로 한 번 계산하여 첫 측정과 두 번째 정규화에 함께 쓰는 것이다. 사용자 목표값과 최종 verify_audio는 변경하지 않는다. 모든 소스에서 두 목표를 항상 달성한다고 약속하지 않으며, 최종 목표에 못 미치면 기존처럼 미게시한다. 일반 -1 프로필은 경계 보정의 near-miss이며 기존 결과를 유지해야 한다.

코드 변경은 `.agents/skills/edit-gameplay-video/scripts/postprocess.py`, 회귀는 `extension/tests/test_gameplay_postproduction.py`에 한정한다. Core·규칙·모델·실제 영상·설치·외부 전송·push·gitlink 변경·새 adapter·E1 재수정은 제외한다. E2 실제 전편/다른 게임 평가는 기존 보류를 유지한다. 일반화는 FFmpeg에 종속된 프로젝트 구현에만 적용하며 Core 후보는 없다.

## 전체 단계와 전환

| 단계 | 진입·작업 정의 | goal·성공 조건과 커밋 |
|---|---|---|
| 0 설계 | 사용자 E3 승인과 clean 대상 확인 후 이 설계만 작성 | 필수 항목·승인 범위 일치, 정확한 설계 단독 커밋과 blob 대조 후 구현 진입 |
| 1 구현·검증 | 0단계 pass/snapshot 확인. 코드·기존 회귀·현재 상태만 변경 | 후편집 전체 검사와 컷 CLI 기존 검사 pass, 구문·UTF-8·diff 검사 pass. 정확한 3파일 커밋과 snapshot 대조 후 정리 진입 |
| 2 정리 | 1단계 pass/commit 확인. 이 설계와 현재 상태만 변경 | 설계가 0단계 snapshot에서 복구 가능하고 고유 근거가 코드/검사/Git에 남으며 활성 참조를 해제한 뒤 이 설계만 삭제. 정리 단독 커밋·대상 부재 확인 |
| 3 보고 | 정리 snapshot 확인. 기존 보고와 현재 상태만 갱신 | E1 내용 보존, E3 결정·검사·한계·단계 commit 기록. 보고 단독 커밋 뒤 부모/Core/gitlink clean과 정확한 경로 확인 후 종료 |

단계 공통 판정: goal과 선택 필수 검증·실제 커밋 확인이 모두 충족되면 pass, 알려진 결함은 fail, 미실행 필수는 not_run이다. Core/규칙 변경 의미 감사·실제 게임 의미/청취·clean clone 릴리스 검증은 변경 범위 밖으로 not_applicable이며 실제 게임 능력 통과로 보고하지 않는다. 실패하면 해당 단계에 머물러 원인을 확인하고 같은 원인의 무진전 반복을 하지 않는다. 새 무관한 변경이 생기면 local change 게이트로 정지한다.

## 현재 단계 실행 방법

0단계에서는 이 문서의 경로·UTF-8·필수 항목과 대상 동일성을 확인하고 이 파일만 커밋한다. 각 다음 단계에서는 위 표의 진입·goal을 확인하고 해당 단계의 변경만 stage한다. 1단계 검증 명령은 ROOT에서 `PYTHONPATH=extension/tests`로 `python -B -m unittest test_gameplay_postproduction test_edit_gameplay_video_skill -v`다. Windows hardlink/mandatory lock을 테스트하는 명령은 필요 시 승인된 테스트 실행 확장을 사용하며 구현을 약화하지 않는다. 단계 snapshot은 git show/diff와 현재 파일의 일치를 확인하며, 코드 commit 이후 같은 코드 검사 실행으로 확인한다. 선택 집합 통과 뒤 새로운 실패나 변경이 없으면 전체 저장소 회귀를 확대·반복하지 않는다.

복구는 마지막 검증된 로컬 commit이 소유한다. 승인 없는 reset/stash/사용자 변경 삭제를 하지 않는다. 범위·보장·필수 검증을 바꿔야 하면 사용자에게 결정을 받는다.

## 임시 자원·보존·정리

- 이번 한시 설계의 정확한 제거 대상은 `D:/AI Agent/GitHub/Creator/extension/work/session-close-post-peak-2026-10-23.md` 한 파일이다. 삭제 전 비링크·내부 경로·0단계 blob 일치와 활성 참조를 확인한다. 설계/승인/수정 근거는 Git commit·코드·회귀·기존 보고에 보존한다.
- 합성 검사는 기존 TemporaryDirectory 내부 수명을 따른다. 기존 `extension/.runtime/gameplay-skill-tests/fixture-*` 및 `extension/.runtime/tmp*` 중 해당 호출이 새로 만든 디렉터리만 해당 호출에서 정리한다. 부모 runtime, 기존 fixture/jobs/사용자 자료를 일괄 삭제하지 않는다. 새 검사는 기존 fixture를 재사용하며 별도 scratch owner를 추가하지 않는다.
- 최종 보고는 기존 `D:/AI Agent/GitHub/Creator/extension/docs/reports/SESSION_CLOSE_GAMEPLAY_2026-10-23.md`를 갱신해 Git 추적·보고 단계에서 커밋한다. 같은 목적의 새 보고나 외부 보존 자료를 만들지 않는다. 이 보고는 임시 자료가 아니다.
- 현재 상태는 `state/main.md`가 소유하며 완료 과정은 상태에 누적하지 않는다. 설계는 최종 트리에서 제거하고 단계별 Git 이력은 유지한다. 최종 부모/Core가 예상 경계에서 clean이고 미결 결정이 없을 때만 종료한다.
