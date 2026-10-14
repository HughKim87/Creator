# Creator main 공통 개발 상태

- 목적: 재사용 가능한 Extension·스킬·workflow 개선과 유지보수의 현재 상태를 소유한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md, SESSION_HANDOFF.md 뒤.
- 책임: main 작업 에이전트가 공통 개발 상태를 유지하고 사용자가 범위와 외부 효과를 승인한다.
- 상태: 영상 제작 스킬의 Claude 실행 경로 구현·검증 완료, 미커밋(커밋은 사용자 소유).
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md의 「워크트리별 상태 문서」.

## 현재 단계

- 영상 제작 스킬 7종을 Codex와 Claude(Cowork) 양쪽에서 쓰도록 Claude 실행 경로를 추가했다. 작업 트리 변경만 있고 커밋하지 않았다.
  - `check_worktree.py`/`activate_worktree.py`: `CREATOR_HOST_PATH_MAP`이 있으면 root를 호스트(Windows) 경로로 기록하고 실행은 `local_root`에서 한다. 변수가 없으면 기존과 같다.
  - `scripts/claude_runtime.sh`: Claude 연결 폴더용 git shim과 경로 매핑.
  - `validate_video_job.py`: `verification_method: claude_in_chrome_device` 허용.
  - `video-to-srt`: 플랫폼별 python-deps 경로(Windows는 기존 `python-deps`). Claude 전사는 클라우드 작업공간에서 실행.
  - `connect-chrome-profile`·`youtube-title-thumbnail`·`coordinate-video-production`·`video-to-srt` SKILL.md에 「Claude 실행 경로」 절 추가. skill-bundle manifest 갱신.
- inputs/outputs 보호 경로는 접근하지 않았다.
- 활성 전체 설계: 없음.
- 활성 단계 설계: 없음.

## 직전 게이트

- 판정: 작업 트리 수준 pass. 관련 unittest(worktree routing·job validation·chrome contract·video-to-srt·thumbnail·session improvements·export conformance) 통과. Linux VM 전체 회귀는 305개 중 기존과 같은 31개 실패(기존 환경 의존 실패, 신규 0).
- 실측: Claude에서 `activate_worktree.py`가 `codex/ainotebook`으로 redirect, Codex가 만든 완료 job `2026-10-14-rea` 검증 valid, Claude in Chrome으로 NotebookLM 로그인 확인, 클라우드 faster-whisper(large-v3-turbo, 2코어 약 3배속) 동작.
- not_run: Windows(Codex)에서의 회귀 실행, ChatGPT 웹 썸네일 생성 실사용.

## 승인 상태

- 위임: main의 영상 스킬 Claude 실행 경로 구현·검증(사용자 승인 2026-10-14), Claude용 faster-whisper 설치, 테스트 임시 폴더 정리.
- 미위임: 커밋·브랜치 병합(사용자 소유), 보호 경로 정리, push·외부 게시·업로드.

## 차단

- 없음.

## 알려진 위험

- ainotebook 워크트리에는 아직 이 변경이 없다. 병합 전에는 Claude 제작이 `claude_in_chrome_device` 검증에서 막힌다.
- Claude in Chrome 장치와 프로필의 대응은 ainotebook의 Git 제외 runtime 설정(`claude_in_chrome.device_profiles`)에 사용자 확인으로 등록했다. 확장 재설치 시 deviceId가 바뀔 수 있다.
- Claude 연결 폴더 셸에서는 Windows worktree가 prunable로 보인다. 그 셸에서 `git worktree prune`을 실행하면 안 된다.
- 기존 스킬 등록의 공식 quick_validate는 PyYAML 부재로 not_run이다.

## 첫 다음 행동

1. 사용자가 변경을 검토·커밋하고 `codex/ainotebook`에 병합했는지 확인한다.
2. 공통 개선 요청을 받으면 영향받는 Extension·스킬·workflow owner를 확인하고 해당 범위의 구현과 검증을 진행한다.
3. 개별 영상 요청을 받으면 PROJECT_RULES.md의 「워크트리별 상태 문서」에 따라 영상 작업용 워크트리에서 진행한다.
