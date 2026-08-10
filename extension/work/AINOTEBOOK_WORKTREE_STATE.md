# ainotebook Worktree State

- 갱신일: 2026-08-11
- 적용 범위: `C:\Users\Hugh\Claude\Projects\Building WorkFlow\Workspace\ainotebook` worktree와 `codex/ainotebook` branch에서 진행하는 YouTube 영상 제작
- 역할: ainotebook worktree의 현재 작업·blocker·검증 상태·첫 다음 행동을 소유하는 단일 startup 문서

## 현재 상태

- 상태: `idle`; 활성 영상 job, blocker, 사용자 결정 대기 항목이 없다.
- 검증된 실행 위치: workflow root는 `C:\Users\Hugh\Claude\Projects\Building WorkFlow\Workspace\ainotebook`, branch는 `codex/ainotebook`이며 worktree activation 결과는 `valid`, `redirected: false`다.
- 영상별 주제·승인·단계 상태·산출물 근거는 각 `extension/work/<job-id>/VIDEO_JOB.json`이 소유한다. 완료된 영상의 상세는 이 문서에 복제하지 않는다.

## 영상 제작 workflow

- 단일 실행 owner: [Coordinate Video Production](../../.agents/skills/coordinate-video-production/SKILL.md)
- 제작 단계는 `research` → `video` → `captions` → `title_thumbnail` → `upload_package` 순서이며, 첫 `pending` 단계와 그 단계의 skill만 실행한다.
- 새 영상은 worktree activation과 browser profile resolution을 거쳐 `video-job-v3` 작업 기록을 생성·검증한 뒤 시작한다. 진행 중 영상은 사용자 지시가 없는 한 기존 `VIDEO_JOB.json`의 실행 문맥과 승인 계약을 유지한다.
- 최종 결과는 사용자가 직접 YouTube에 올릴 네 파일을 준비하는 데서 끝난다. YouTube 업로드·게시·예약·공개 범위 변경, 유료 작업, 외부 쓰기, Core 변경은 이 workflow 범위가 아니다.
- 보호된 `extension/inputs/<job-id>/`와 `extension/outputs/<job-id>/`는 새 작업에서 exact 항목과 목적이 확정된 뒤에만 접근한다.

## AI Notebook 채널 컨텍스트

- 채널 URL: `https://youtube.com/channel/UC3N06byafrjXpMS7C5AJ6tg?si=vL_rBw_mfT__zelu`
- 채널 ID: `UC3N06byafrjXpMS7C5AJ6tg`
- 채널 목적: AI를 쉽게 학습하고 핵심 개념을 얻을 수 있는 영상을 제작한다.
- 혼용 금지: `main` branch와 `김실버유튜브` 메인 worktree의 YouTube 채널은 별개다. 두 채널의 URL·ID·콘텐츠 방향을 서로 가져오지 않는다.
- 패키지 경계: 채널 ID는 대상 채널 식별과 검증에만 사용하고, 수동 업로드 패키지에는 채널명만 기록한다.

## 첫 다음 행동

1. 새 영상 요청이 오면 `PROJECT_RULES.md` → 이 문서 → `coordinate-video-production` skill 순서로 읽는다.
2. worktree activation을 다시 검증한 뒤 새 `VIDEO_JOB.json`을 만들거나 사용자가 지정한 기존 job의 첫 `pending` 단계를 재개한다.

## 다음 session 시작 prompt

`ainotebook` root에서 `PROJECT_RULES.md`와 `extension/work/AINOTEBOOK_WORKTREE_STATE.md`를 읽는다. 활성 job이 없으므로 사용자 요청 전에는 영상별 파일을 열지 않는다. 새 영상 또는 재개 요청이 오면 `coordinate-video-production` skill로 root·branch를 검증하고 per-job `VIDEO_JOB.json`을 단일 실행 상태 owner로 사용한다. 외부 업로드·게시와 Core 변경은 별도 승인 없이는 수행하지 않는다.
