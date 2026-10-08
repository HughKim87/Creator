# Creator dokkaebi 워크트리 상태

- 목적: 새 촬영 원본 "도깨비의 세계 오픈런 방송"의 영상 편집을 main과 분리된 워크트리에서 진행한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md 뒤.
- 책임: 에이전트가 이 브랜치의 편집 상태를 유지하고 사용자가 방향·결과를 승인한다.
- 상태: active — 자막 교정·시청자 관점 분석·방향 A 선택·1차 구성 설계 완료. 2차 편집(실제 컷) 미착수.
- handoff mode: same-workspace. 원본과 산출물이 Git 제외 경로(inputs/, extension/outputs/)에 있다.
- 관련 권위: extension/docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md 및 PROJECT_RULES.md의 영상 편집 rule route.

## 현재 단계

- 워크트리: D:/AI Agent/GitHub/Creator-dokkaebi, 브랜치 claude/dokkaebi (기준 main bc341ae). core submodule 3e0ebe7.
- 원본(읽기 전용): inputs/2026-10-08 11-01-06.mp4 — 12,728,534,764 bytes, 16481.917s, 1920×1080 60fps h264, AAC 48k stereo. 해시 미기록.
- 사용자 원본 자막: inputs/2026-10-08 11-01-06.srt (whisper small 추정, 1,694큐).
- 산출물 계약: Premiere Pro CS6용 xmeml v4 XML 하나, 1920×1080·60fps. 출력 위치 extension/outputs/.
- 작업 profile: new_full_edit, 게임 방송 프로필. 방향: A "첫날 플레이 종합 리뷰"(사용자 선택).
- 활성 설계 정본: extension/outputs/dokkaebi-edit/dokkaebi-edit-design-A.md (스파인, 시청자 궁금증↔블록, B0~B21 블록 후보 범위와 #큐 근거, 전환 목록, 위험).

## 완료된 산출물 (extension/outputs/dokkaebi-asr/)

- 2026-10-08 11-01-06.corrected-full.srt — 원본 타임스탬프 기준 오타 교정 전체 자막(NPC 포함), 1,687큐, validate_srt valid.
- 2026-10-08 11-01-06.streamer-only.srt — 진행자 발화만, 1,507큐, valid. 편집·후편집 자막의 기준.
- dokkaebi-subtitle-review.json — 큐별 원문·large-v3-turbo 인식·교정문·화자 라벨(streamer/npc/mixed/noise)·사용자 확인 여부.
- dokkaebi-npc-lines.md — NPC·혼합 판정 목록(사용자 검토용).
- dokkaebi-content-analysis.md — 내용 지도와 시청자 궁금증 분석.
- dokkaebi-large-v3-turbo.srt / .transcript.json / dokkaebi-asr-notes.json — 독립 재전사(faster-whisper large-v3-turbo, Creator-ainotebook runtime 모델). 보조 근거.
- audio16k_a.flac, audio16k_b.flac — 분석용 16kHz 오디오(0~8240s, 8240s~). 작업 종료 시 정리 대상.

## 직전 게이트

- 자막: 사용자 피드백 반영 완료. 진행자 확정 #85·87·166·299·301·427·428·1594~1596·1606(급소/똥꼬 찌르기는 진행자). 문구 확정 #990·1230·1482·1483·1530. 나머지 애매 목록은 현 분류 유지(사용자 확인).
- 화자 분류는 텍스트(사극 말투·세계관 내용) 기반. 실제 청취 검수 not_run.
- 편집 규칙 개선 커밋 fe86d7a: 자막 확보·정확도/화자 확인 → 내용 분석 → 시청자 관점 분석 → 편집 설계 순서(WORKFLOW_CONTRACT 다섯 작업 층, R03, R05, R06).
- 검증: VM 환경에서 extension 테스트 30건 실패하나 수정 전 main과 동일(PowerShell 7 부재 21, 플랫폼 snapshot 보장 불가 4, core 계약 경로 5). Windows에서 scripts/verify.py 미실행.

## 승인 상태

- 승인: 워크트리 생성, 산출물 형식(CS6 XML), 자막 교정 결과, 편집 규칙 개선과 커밋, 방향 A.
- 미승인: 편집 문법(calibration.required=true), 보스전 압축 방식(내부 컷/배속), 목표 길이, B0 도입 구성, 후편집 스타일 상속, push·main 병합.

## 차단

- 없음. 단 원본 화면은 아직 한 프레임도 확인하지 않았다.

## 알려진 위험

- Cowork VM: CPU 2코어·RAM 3GB, 백그라운드 프로세스 불가(호출 종료 시 종료), 호출당 180초 제한. 장시간 처리(ASR 등)는 파일을 클라우드 컨테이너로 스테이징해 실행했다(400MB/파일 제한 → 분할).
- 클라우드·VM 모두 HuggingFace 등 모델 다운로드 차단. 모델은 Creator-ainotebook/extension/.runtime/models/whisper/large-v3-turbo에 있음.
- 워크트리는 VM git으로 만들고 경로 파일을 Windows 형식으로 맞췄다. VM에서 git 실행 시 GIT_DIR=<Creator>/.git/worktrees/Creator-dokkaebi, GIT_WORK_TREE=<Creator-dokkaebi> 지정 필요. Windows git 정상 인식은 사용자 미확인.
- main 폴더의 SESSION_HANDOFF.md에 dokkaebi 행을 미커밋 상태로 추가해 둠(이 브랜치 커밋 내용과 동일).
- NPC 음성과 진행자 발화가 겹치는 mixed 25큐는 오디오 경계 위험.

## 첫 다음 행동

1. dokkaebi-edit-design-A.md를 읽고 §6 미정 항목(보스전 압축 방식, 목표 길이, B0 도입)을 사용자에게 확인한다.
2. calibration: B15~B16(02:19:51~02:36:55, 분노→전환점) 구간을 정상 속도로 화면·오디오 확인하며 microbeat 2차 편집해 단일 sequence 검수 XML을 만들고 편집 문법 승인을 받는다.
3. 승인 후 B0~B21 전체 2차 편집 → 의미·구조 gate → CS6 XML. 이후 후편집은 video-post-production 규칙과 사용자 확인.

## 다음 세션 시작 prompt

시작 3문서를 읽은 뒤 이 state 파일과 extension/outputs/dokkaebi-edit/dokkaebi-edit-design-A.md를 읽고 「첫 다음 행동」 1번부터 진행한다. 방향 A는 확정이며 방향안을 다시 만들지 않는다.
