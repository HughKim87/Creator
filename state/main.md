# Creator main 공통 개발 상태

- 목적: 재사용 가능한 Extension·스킬·workflow 개선과 유지보수의 현재 상태를 소유한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md, SESSION_HANDOFF.md 뒤.
- 책임: main 작업 에이전트가 공통 개발 상태를 유지하고 사용자가 범위와 외부 효과를 승인한다.
- 상태: 제목·썸네일 설계 개선과 길이·후보 수 검증 변경 완료. 사용자 승인으로 main 로컬 커밋에 반영한다. 영상 워크트리 반영은 미위임이다.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md의 「워크트리별 상태 문서」.

## 현재 단계

- 세션 종료 E1 활성: game-trend-brief의 조회수 전망 근거를 개선했다. 활성 설계는 extension/docs/domain/youtube/SESSION_CLOSE_E1_20261016.md이며 현재 1단계 검증을 마치고 커밋 확인 후 정리 단계로 전환한다. E2 외부 코치·E3 썸네일 단독 계약은 보류했다.

- 제목·썸네일의 성과 근거를 요청받으면 유사 영상의 실제 패키징을 먼저 비교하고, 공개 조회수·직접 본 썸네일·편집 판단을 구분한다. 선택 근거 기록은 패키지 안내가 소유하며 단순 문장 수정에는 조사를 강제하지 않는다. 현재 활성 E1 작업은 없다.

- 제목은 시청자의 질문을 출발점으로 썸네일과 한 세트로 설계한다. 후보별 클릭 이유·약점과 1순위 이유를 보고하고 내용 충실도·도입부의 약속 안내를 검토한다. 길이 40~65자는 참고 범위로 전환했으며 검증기는 비어 있지 않은 한 줄·최대 100자·후보 최소 1개·선정 제목 포함을 확인한다. 후보 수는 사용자 요청을 따르고 기본값은 5개다. 승인·성과 미측정 계약은 유지했다. 기존 영상 자료는 수정하지 않았다.
- 수동 업로드 가이드는 `publish_timing`의 공개 날짜·요일·시각·시간대와 채널 분석 근거/잠정 추천·한계를 보존한다. coordinator가 Studio 읽기 전용 확인을 수행하고 로컬 생성기가 렌더한다. 새 제작·재완료는 `--require-publish-timing`으로 누락·과거 시각을 검사하며, 기존 패키지 읽기 호환은 유지한다. main 작업 트리 수준으로 검증됐으며 실제 채널 데이터 수집·기존 영상 가이드 수정은 이번 유지보수 범위가 아니다.
- 로컬 음성 UI에 Qwen / GPT-SoVITS V5 Turbo 선택을 추가했다. 전용 설치·실행 환경과 엔진별 목소리 저장을 사용하며 관련 검증을 완료했다. 운영 진입점은 `scripts/Start-QwenTTS.cmd`, 설정은 `extension/config/qwen-tts-local.json`과 `sovits-local.json`이다.
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

- 조회수 전망 E1: 비교 조건·예측 근거 부족·가정 계산 등 합성 시나리오 6개를 수동 문맥 대조했다. 기존 회귀 21개, 스킬 번들 무결성, UTF-8·최소 frontmatter·Markdown fence와 diff 검사 pass. 공식 quick_validate는 PyYAML 부재로 not_run이며 독립 Agent 행동 재현과 실제 조회수 효과는 미검증이다.

- E1: 관련 package/session 합성 검사 18개, 스킬 번들 무결성, diff 검사 pass. 적용·구어체·중간 요청·near-miss·접근 제한·지표 해석의 6개 시나리오를 수동 문맥 검토했다. 독립 Agent 행동 재현 및 실제 CTR 효과는 not_run.

- 제목 개선: 제목 패키지·세션 개선 합성 검사 18개 pass(임시 경로를 extension/work로 지정). 짧은 제목, 66~100자, 후보 1·3·5·10개와 승인 보존, 빈 값·초과·줄바꿈·선정 누락 거부를 확인했다. 번들 무결성과 diff 검사 pass. 실제 제작·게시 후 클릭률 검증은 not_run이며 공식 skill-creator quick_validate는 PyYAML 부재로 not_run이다.
- 공개 시간 추천 변경: 관련 합성 회귀 28개, 스킬 번들 무결성, diff 검사 pass. 추천 재렌더·데이터 부족의 잠정 구분·시간대·과거 시각 거부·finalizer 연결을 검증했다. 실서비스에서 새 제작 전체 실행은 not_run이다. 공식 skill-creator quick_validate는 PyYAML 부재로 not_run이다.
- 로컬 음성 UI: 한국어 WAV 생성, 엔진 왕복 전환, 원본 없이 저장된 목소리 재사용, 중단 후 작업 소유 프로세스 종료, 관련 회귀 통과. 실측 근거는 ignored runtime의 `qwen-tts/verification/dual-engine-evidence.json`에 있다. 본인 목소리의 지각적 유사도와 전용 모델 학습은 not_run.
- 판정: 작업 트리 수준 pass. 관련 unittest(worktree routing·job validation·chrome contract·video-to-srt·thumbnail·session improvements·export conformance) 통과. Linux VM 전체 회귀는 305개 중 기존과 같은 31개 실패(기존 환경 의존 실패, 신규 0).
- 실측: Claude에서 `activate_worktree.py`가 `codex/ainotebook`으로 redirect, Codex가 만든 완료 job `2026-10-14-rea` 검증 valid, Claude in Chrome으로 NotebookLM 로그인 확인, 클라우드 faster-whisper(large-v3-turbo, 2코어 약 3배속) 동작.
- not_run: Windows(Codex)에서의 회귀 실행, ChatGPT 웹 썸네일 생성 실사용.

## 승인 상태

- 위임: game-trend-brief의 조회수 전망 근거 개선(E1), 설계·개선·정리 로컬 커밋과 이번 임시 설계 제거, 저장소 밖 종료 보고. E2 외부 코치·E3 썸네일 단독 계약은 보류했다.

- 위임: 제목·썸네일 스킬의 제목 설계·패키지 형식·길이 및 후보 수 검증과 관련 검사 개선 및 해당 변경의 main 로컬 커밋(2026-10-15). 다른 워크트리 병합·기존 영상 제목 변경은 미위임.
- 위임: 수동 업로드 가이드에 채널 분석 기반 공개 시간 추천을 포함하는 공통 스킬·형식·로컬 생성기와 관련 검증 변경 및 해당 변경의 로컬 커밋(2026-10-15). 다른 브랜치 병합·기존 영상 자료 변경은 미위임.
- 위임: 기존 음성 화면의 Qwen/GPT-SoVITS 선택 구현, GPT-SoVITS 전용 로컬 설치와 검증, 해당 TTS 변경의 로컬 커밋. 유료 서비스·녹음 외부 전송·본인 전용 모델 학습·push는 미위임.
- 위임: main의 영상 스킬 Claude 실행 경로 구현·검증(사용자 승인 2026-10-14), Claude용 faster-whisper 설치, 테스트 임시 폴더 정리.
- 미위임: 승인 범위 밖의 커밋·브랜치 병합(사용자 소유), 보호 경로 정리, push·외부 게시·업로드.

## 차단

- 없음.

## 알려진 위험

- 제목 개선은 main 작업 트리에만 있다. 영상 워크트리 적용 전에는 승인된 병합이 필요하며, 편집 기준 개선이 실제 CTR 상승을 입증하지는 않는다.
- 공개 시간 추천 개선은 main에만 반영한다. 영상 제작 워크트리에는 사용자가 공통 변경을 병합한 뒤 적용된다.
- 로컬 음성 UI의 GPT-SoVITS는 참고 음성 복제만 지원한다. Qwen의 20~60초 처리와 달리 3~10초 참고 구간을 사용하며, 긴 녹음은 같은 SRT가 필요하다. 엔진 전환 후 최초 생성에는 모델 로딩 시간이 추가된다.
- ainotebook 워크트리에는 아직 이 변경이 없다. 병합 전에는 Claude 제작이 `claude_in_chrome_device` 검증에서 막힌다.
- Claude in Chrome 장치와 프로필의 대응은 ainotebook의 Git 제외 runtime 설정(`claude_in_chrome.device_profiles`)에 사용자 확인으로 등록했다. 확장 재설치 시 deviceId가 바뀔 수 있다.
- Claude 연결 폴더 셸에서는 Windows worktree가 prunable로 보인다. 그 셸에서 `git worktree prune`을 실행하면 안 된다.
- 기존 스킬 등록의 공식 quick_validate는 PyYAML 부재로 not_run이다.

## 첫 다음 행동

1. 사용자가 공통 변경을 `codex/ainotebook`에 병합했는지 확인한 뒤 해당 워크트리에서 새 제작을 진행한다.
2. 공통 개선 요청을 받으면 영향받는 Extension·스킬·workflow owner를 확인하고 해당 범위의 구현과 검증을 진행한다.
3. 개별 영상 요청을 받으면 PROJECT_RULES.md의 「워크트리별 상태 문서」에 따라 영상 작업용 워크트리에서 진행한다.
