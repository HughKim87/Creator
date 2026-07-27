# ainotebook Worktree State

- 갱신일: 2026-07-27
- 적용 범위: `C:\Users\Hugh\Claude\Projects\Building WorkFlow\Workspace\ainotebook` 워크트리와 `codex/ainotebook` 브랜치에서 진행하는 YouTube 영상 작업
- 역할: ainotebook 워크트리의 현재 work·blocker·검증 상태·첫 다음 행동의 단일 owner

## 현재 작업

- 작업: `2026-07-26-omx-omc-beginners` — OMx·OMC를 AI 입문자 관점에서 소개하는 영상 제작 및 수동 업로드 패키지
- 상태: `ainotebook` 워크트리 `codex/ainotebook`에서 Chrome Main profile(`Default`)로 NotebookLM 리서치·영상 생성·SRT까지 완료했다. 기존 썸네일은 사용자가 요구한 웹 ChatGPT 방식이 아닌 로컬 텍스트 합성이었으므로 승인과 완료 판정을 철회했다. 웹 ChatGPT와 동일한 내장 이미지 생성 방식의 새 원샷 후보는 `extension/work/2026-07-26-omx-omc-beginners/thumbnail-one-shot-v2-upload.jpg`에 있으며, 공식 outputs 썸네일은 사용자 승인 전까지 교체하지 않는다. 실제 YouTube 업로드·게시·공개 상태 변경은 수행하지 않는다.
- blocker·사용자 결정 대기: 새 원샷 썸네일과 선택 제목·썸네일 문구·최종 시각의 명시적 사용자 승인이 필요하다. 승인 전에는 기존 수동 업로드 가이드와 패키지를 사용하지 않는다.
- 첫 다음 행동: 사용자에게 새 원샷 썸네일을 제시하고 제목·문구·최종 시각 승인을 요청한다. 승인되면 공식 outputs 썸네일을 교체하고 제목·썸네일 패키지와 수동 업로드 패키지의 SHA-256을 재계산해 네 파일 업로드 패키지를 다시 검증한다.

## 검증된 현재 상태

- `extension/work/2026-07-26-omx-omc-beginners/VIDEO_JOB.json`은 `video-job-v3`, job status `needs_user`, `title_thumbnail: needs_user`, `upload_package: pending`이다.
- 썸네일 계약은 `one_shot_imagegen`, 로컬 텍스트 합성 금지, `review_gated`, `explicit_user`로 고정했다.
- 제목·썸네일 패키지는 v3 초안으로 일반 검증을 통과하되 최종 승인 검증은 실패해야 한다.
- 수동 업로드 패키지는 v3 해시 계약을 기록했지만 `preparation.status: pending`이며, 기존 가이드 상단에 사용 중지 경고를 추가했다.
- 자막 검수 기록은 `status: reviewed`, 158개 큐 전체 검수 완료, 교정 전 표현 잔존 0건이다.
- 패키지에는 채널명만 저장하며 채널 ID와 placeholder는 저장하지 않는다.
- 지정 워크트리와 `codex/ainotebook` 브랜치도 유효하다.

## 실패 기록

- `YouTube 로컬 파일 자동 주입 | worktree·temp·현재 workspace 경로 3회 | Chrome file chooser가 Not allowed로 차단 | 사용자 결정에 따라 자동 업로드 경로를 폐기하고 수동 업로드 준비 스킬로 전환 | 향후 Chrome·브라우저·YouTube API 업로드 시도 금지`
- `업로드 메타데이터 저장 확인 | 별도 Studio 탭의 변경을 원래 사용자 탭에 저장된 것으로 잘못 판단 | 실제 탭에서 재입력·검증했으나 자동화 신뢰성이 부족함을 확인 | 향후 외부 저장을 완료 조건에서 제외`

## AI Notebook 채널 컨텍스트

- 채널 URL: `https://youtube.com/channel/UC3N06byafrjXpMS7C5AJ6tg?si=vL_rBw_mfT__zelu`
- 채널 ID: `UC3N06byafrjXpMS7C5AJ6tg`
- 채널 목적: AI를 쉽게 학습하고 배우며 핵심 개념을 얻을 수 있는 영상을 제작한다.
- 사용 범위: 채널 근거 확인, 영상 주제와 난이도 설정, 제목·썸네일 방향, 설명문 및 수동 업로드 가이드의 대상 채널 식별에 필요할 때 사용한다.
- 혼용 금지: `main` 브랜치와 `김실버유튜브` 메인 워크트리에서 작업하는 YouTube 채널은 이 채널과 별개다. 메인 작업의 채널 URL·ID·콘텐츠 방향을 이 워크트리에 가져오거나, 이 채널 정보를 메인 작업에 사용하지 않는다.
- 패키지 경계: 채널 ID는 이 상태 문서에서 대상 채널을 식별하고 검증하는 근거로만 보존한다. 수동 업로드 패키지에는 기존 계약대로 채널명만 기록하며 채널 ID를 저장하지 않는다.
