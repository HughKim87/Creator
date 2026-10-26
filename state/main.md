# Creator main 공통 개발 상태

- 목적: 공통 구현 유지보수의 현재 재개 지점과 검증 경계를 소유한다.
- 읽는 시점: 시작 문서 뒤.
- 책임: main 유지보수 세션과 사용자.
- 상태: write-video-script 신설·제작 총괄 연결·제작 묶음 검증 완료. 실제 대본의 낭독·시청 성과는 별도 검증 범위.
- handoff mode: same-workspace. 실제 job 자료와 도구 설치는 로컬이며 전달·재설치는 별도다.
- 관련 권위: PROJECT_RULES.md, extension/docs/WORKSPACE.md.

## 현재 단계

`write-video-script`가 녹음 전 영상 목적·실제 근거·이야기 구성·초안·국소 수정·검토를 소유한다. 총괄 요청 표에서 필요한 작업만 연결하며, 기존 편집·NotebookLM 생성에 대본 단계를 강제하지 않는다. 스킬은 채널별 고정 길이·말투·연출을 포함하지 않고, 사용자 의도와 제외 범위를 보존하는 방법만 공유한다. 기존 김실버 자료·최신 job 상태·미디어·다른 TTS 작업은 변경하지 않았다.

2026-10-26 실행기 국소 수정 완료(same-workspace). 사용자 지시로 `run_job`의 미커밋 일괄 차단을 제거하고 각 run에 기준 commit/catalog와 별도의 working_tree dirty/status digest를 기록한다. main·job/GPU 잠금·commit/catalog 변경 수용 검사는 유지한다. 변경 범위는 creator_workspace.py, 해당 회귀, WORKSPACE.md 운영 설명이며 기존 TTS 구현 변경·Core·게시 작업은 제외했다. 검증은 격리 fixture에서 실행·재개·잠금·경로·변경 보존 16개 통과, git diff --check 통과. working_tree 기록은 내용 snapshot이 아니며 실제 영상 생성·업로드는 이 수정 검증에서 not_run. 후속 사용자 지시로 이번 변경분만 로컬 커밋하도록 승인됐으며 다른 TTS 수정과 push는 제외한다.

활성 공통 구현 단계는 없다. `coordinate-video-production`은 영상 종류·요청 범위를 먼저 선택하고 기존 전문 스킬에 입력·결과·검증을 연결한다. NotebookLM 고정 5단계의 기록·검수·재개 절차는 해당 스킬의 `references/notebooklm-workflow.md`에 있으며, 게임 편집·자막·쇼츠·패키징·분석·댓글의 부분 요청은 각 전문 상태·패키지를 사용한다. 고정 VIDEO_JOB 엔진·스키마를 범용 작업 엔진으로 바꾸지 않았다.

복수 최종 결과는 새 작업의 `outputs/upload/`·`outputs/shorts/`로 분리하며 수동 패키지 정리는 전용 output_dir에만 적용한다. 다른 미디어·ZIP은 정리 전 preflight에서 차단하고 확인된 동일 패키지 중간 파일만 archive_files로 지정한다. 제목은 text_only/package/performance, 신작 조사는 facts_only/calendar 모드를 구분한다. 연결된 공개 자료·채널 진단·타임스탬프 브라우저 절차는 현재 지원 API를 사용한다.

앞서 보강한 한국어 계산·좌표 처리는 `extension/src/youtube_analysis.py`와 각 스킬의 scripts, 합성 회귀는 `extension/tests/test_youtube_skill_tools.py`가 소유한다. Core·실제 영상·게시물은 변경하지 않았다.

보완한 채널 코치·타임스탬프·쇼츠는 `.agents/skills/youtube-channel-coach/`·`.agents/skills/youtube-timestamp-hashtag/`·`.agents/skills/create-shorts/`가 프로젝트 정본이다. 총괄·NotebookLM 연결·업로드 준비·채널 코치·게임 편집은 프로젝트 상대 링크로 참조하며 캐시·개인 사본 fallback과 자동 동기화는 하지 않는다. 가져오기 출처와 원본 해시는 각 SKILL.md에 기록했다. 제작 묶음의 등록·해시는 총괄의 `references/skill-bundle.json`과 검사 도구가 소유하며 신규 대본 스킬도 포함한다. 쇼츠의 UI·스크립트·검토 페이지·참고 자료도 포함한다. 쇼츠 회귀는 legacy extension 사본 대신 프로젝트 정본을 검증한다.

영상별 현재 상태·승인·미디어는 각 `extension/jobs/<job-id>/`가 소유한다. 이전 Core 갱신의 raw 근거는 `maintenance/agent-core-update-20261023/verification.json`에 있다. 기존 E3 오디오 피크 결과는 [이전 종료 보고](../extension/docs/reports/SESSION_CLOSE_GAMEPLAY_2026-10-23.md)의 역사 근거이며 이번 스킬 연결 검증과 혼합하지 않는다.

## 직전 게이트

`pass` — 신규 스킬 공식 형식 검사와 YAML·상대 링크 확인, 제작 묶음 무결성, 신규 연결/누락/변조/독립 프로젝트 복사/줄바꿈 회귀 6개와 기존 쇼츠 묶음 4개·YouTube 도구 11개를 통과했다. 이 결과는 등록·연결·도구 검사이며 대본의 설득력·사용자 낭독·실제 시청 성과를 입증하지 않는다.

## 승인 상태

현재 요청은 `main`에서 대본 스킬 신설·총괄 연결·해당 검증과 이번 파일만의 로컬 커밋을 승인했다. Core·개인 설치·기존 채널 자료·다른 작업·원격 push·게시·미디어 편집은 이번 범위가 아니다. 아래 기존 유지보수의 보류는 유지한다.

이번 요청은 지금까지의 스킬 보완·프로젝트 이관·연결 정리·HTML 줄바꿈 수정과 관련 코드·문서·검증의 로컬 Git stage·commit을 승인했다. push, 새 의존성 설치·실제 미디어 처리·기존 혼합 결과 이동·외부 게시는 승인 범위가 아니다. 무결성 목록 완전성 강화·중복 사본 정리·공식 Chrome 런타임 의존 변경은 보류를 유지한다. E2 실제 게임 전편·일반화 평가는 기존 보류를 유지한다.

## 차단

현재 공통 유지보수의 차단은 없다. 새 영상 작업은 exact job 입력·목적·승인과 필요한 도구 준비를 적용한다.

## 알려진 위험

신규 대본 스킬의 제품 UI 발견·직접 호출과 실제 다음 영상 제작 품질은 미검증이다. 참고 자료의 합성 사례와 형식/연결 회귀를 독립된 생성 모델 행동 평가로 해석하지 않는다.

이번 도구는 합성 입력으로 검증했으며 실제 한국어 채널 CSV·댓글·게시 성과 검증은 하지 않았다. 채널 코치와 타임스탬프의 설치 캐시 사본은 그대로 남겼지만 프로젝트 실행 원본이 아니다. 플러그인 갱신 시 프로젝트 정본을 덮어쓰지 않는다. 로컬 커밋은 원격 백업을 뜻하지 않으며 runtime·실제 job 자료는 계속 Git 제외 로컬 자료다.

개인 `C:/Users/Hugh/.codex/skills/create-shorts/`와 legacy `extension/skills/create-shorts/`는 보존했으며 현재 프로젝트 실행 원본이나 fallback이 아니다. 이번에는 실제 브라우저·캘린더·Studio를 실행하거나 기존 영상 결과를 정리하지 않았다.

기존 실제 게임 영상 재미·연속 A/V·직접 청취·실모델 추론·Premiere·job runner 전체 및 shared_data 쓰기 검증은 미실행이다. 이전 E3의 최종 피크 거부와 E2 보류를 유지한다. ignored jobs/runtime과 사용자 자료는 보존하며 다른 job의 상태·승인을 승계하지 않는다.

## 첫 다음 행동

1. 새 공통 요청의 범위를 `PROJECT_RULES.md`·현재 Git 변경·스킬 보완 커밋 이력에 대조한다. 추가 Git 쓰기는 그 요청의 승인 범위에서만 수행한다.
2. 제작 연결 요청이면 `.agents/skills/coordinate-video-production/SKILL.md`의 요청 표로 범위와 전문 owner를 선택한다. 새 대본·기존 대본 수정/검토는 `write-video-script`로 연결하고 실제 요청의 결과를 확인한다. 게임 편집은 해당 전문 스킬의 준비 단계와 exact job 상태·입력·가능한 A/V 검수 방법을 확인한다.
3. 보류한 E2 실제 전편 평가를 요청받으면 해당 범위·방법을 확정하고 합성 검증과 실제 사용 검증을 분리한다.
