# ainotebook 워크트리 현재 상태

- 갱신일: 2026-10-15
- 적용 범위: `D:\AI Agent\GitHub\Creator-ainotebook` worktree와 `codex/ainotebook` branch의 AI Notebook 채널 및 Extension 제작 workflow.
- 역할: 이 브랜치의 공통 실행 컨텍스트·차단·첫 다음 행동을 소유한다. 루트 `SESSION_HANDOFF.md` 안내판이 이 파일로 연결한다.
- 관련 문서: [Extension](../extension/README.md), [프로젝트 정책](../PROJECT_RULES.md).

## 현재 단계

- 상태: idle. 새 사용자 요청 대기.
- 활성 전체 설계·단계 설계: 없음.
- workflow root: `D:\AI Agent\GitHub\Creator-ainotebook`; branch: `codex/ainotebook`.
- 영상별 주제·단계·산출물·승인·검수 근거는 각 `extension/work/<job-id>/VIDEO_JOB.json`이 소유한다.
- 재개 수준: same-workspace. 영상별 로컬 자료의 다른 환경 복원은 확인하지 않았다.

## 직전 게이트

- 판정: pass. 상태 문서의 필수 절·참조 경로·NUL 부재와 diff를 확인하고, 특정 영상 기록을 제외하면서 Extension workflow와 채널 컨텍스트를 보존했다.

## 승인 상태

- 위임: 새 영상 요청의 제작 workflow 및 프로젝트 정책에 따른 로컬 창작 선택. 이번 상태 문서 정리와 해당 파일의 Git commit.
- 미위임: YouTube 업로드·게시·예약·공개 범위 변경, 유료 작업, 외부 쓰기, Core 변경, 관련 없는 보호 데이터 접근, 후속 작업의 Git commit·push.

## 차단

- 없음.

## 알려진 위험

- 메인 게임 채널과 AI Notebook 채널을 혼용하지 않는다.
- 과거 영상과의 속도 비교는 exact 기준 파일이 제공된 작업에서만 수행한다.
- 개별 영상의 검수 한계와 미검증 항목은 해당 `VIDEO_JOB.json`에서 확인한다.

## 첫 다음 행동

1. 새 요청을 받으면 `PROJECT_RULES.md`와 아래 `coordinate-video-production` skill을 읽고 worktree root·branch 및 browser profile을 검증한다.
2. 새 영상은 `video-job-v3` 작업 기록을 생성·검증한다. 기존 영상의 재개·수정은 사용자가 지정한 `VIDEO_JOB.json`의 승인·산출물·검수 기록을 확인한 뒤 첫 실행 대상 단계를 판정한다.

## Extension 영상 제작 workflow

- 단일 실행 owner: [Coordinate Video Production](../.agents/skills/coordinate-video-production/SKILL.md).
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

## 다음 session 시작 prompt

시작 정책과 이 상태 문서를 읽는다. 현재 idle이며 새 요청 전에는 영상별 보호 파일을 열지 않는다. Extension 제작 workflow는 `coordinate-video-production` skill을 따르고, 특정 영상 재개·수정은 지정 job의 `VIDEO_JOB.json`을 단일 owner로 사용해 현재 승인과 실제 산출물을 먼저 확인한다.
