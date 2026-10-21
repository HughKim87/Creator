# ainotebook 워크트리 현재 상태

- 갱신일: 2026-10-17
- 적용 범위: `D:\AI Agent\GitHub\Creator-ainotebook` worktree와 `codex/ainotebook` branch의 AI Notebook 채널 및 Extension 제작 workflow.
- 역할: 이 브랜치의 공통 실행 컨텍스트·차단·첫 다음 행동을 소유한다. 루트 `SESSION_HANDOFF.md` 안내판이 이 파일로 연결한다.
- 관련 문서: [Extension](../extension/README.md), [프로젝트 정책](../PROJECT_RULES.md).

## 현재 단계

- 상태: local_files_ready / workflow 자동 게이트 보류. Nanobrowser 수동 업로드용 네 파일은 준비·검증됐다.
- 제작·검수·승인·전달 정본: `extension/work/2026-10-17-nanobrowser/VIDEO_JOB.json`.
- workflow root: `D:\AI Agent\GitHub\Creator-ainotebook`; branch: `codex/ainotebook`.
- 활성 설계: 해당 job의 production_contract 및 단계별 스킬. 남은 범위는 공개 시간 전용 자동 게이트 지원 불일치 판정뿐이다.
- 재개 수준: same-workspace. 원본·생성 원본·검수 자료는 작업 폴더에 보존돼 있다.

## 직전 게이트

- 판정: 부분 pass. 로컬 패키지·제목/썸네일·자막 구조·네 파일/해시·retention 검증 통과. 공개 시간은 Studio 데이터 부족을 확인한 잠정 추천으로 별도 직접 검토했다. 전용 `--require-publish-timing` 자동 옵션은 현재 finalizer 미지원이며 통과로 기록하지 않았다.

## 승인 상태

- 위임: 새 영상 제작과 로컬 창작 선택, NotebookLM 새 노트북·공개 자료 리서치·한국어 영상 생성, 사용자 승인 컷과 일곱 발화 교정.
- 미위임: YouTube 업로드·게시·예약·공개 범위/메타데이터 변경, 유료 작업·설치·자격 증명 접근, 관련 없는 보호 자료, Core 변경, Git commit/push, 별도 유지보수 범위 변경.

## 차단

- 현재 스킬이 요구하는 공개 시간 전용 자동 옵션이 해당 worktree finalizer에 없다. 로컬 네 파일의 사용 가능 여부와 이 자동 게이트 미지원은 별개다. 전체 job의 complete 표시는 보류한다.

## 알려진 위험

- 영상은 공개 자료 기반 설명·활용 시나리오이며 실제 자동화 성능 실험이 아니다. 전체 직접 청취 미실시 범위와 경미한 표현 한계는 job·가이드에 공개했다.
- 가이드의 공개 시간은 잠정 추천이며 실행하지 않았다. 과거 시각이 되면 새 공개 추천 요청 시 다시 확인한다.

## 첫 다음 행동

1. 사용자에게 전달한 `extension/outputs/2026-10-17-nanobrowser/` 네 파일을 유지하고 새 지시 없이는 업로드나 재제작을 하지 않는다.
2. 별도 유지보수가 승인되면 현재 job의 `required_gate_limitations`와 해당 finalizer의 실제 인수를 대조해 스킬 묶음 지원 불일치를 해결한다.
3. 동일 입력 해시·가이드 추천 시각의 유효성을 확인한 뒤 해당 자동 게이트를 실행해 job 종료를 판정한다.

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

시작 정책과 이 상태 문서를 읽는다. Nanobrowser 로컬 수동 업로드 네 파일은 전달 가능한 상태이며 실제 YouTube 작업은 하지 않았다. 공개 시간 전용 자동 게이트 미지원 때문에 job 전체 complete 표시는 보류돼 있다. 현재 job 정본을 읽고 새 사용자 지시 범위만 처리하며, 별도 유지보수나 재제작을 자동 시작하지 않는다.
