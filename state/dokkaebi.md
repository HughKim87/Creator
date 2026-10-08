# Creator dokkaebi 워크트리 상태

- 목적: 새 촬영 원본(dokkaebi)의 영상 편집을 main과 분리된 워크트리에서 진행한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md 뒤.
- 책임: 에이전트가 이 브랜치의 편집 상태를 유지하고 사용자가 방향·결과를 승인한다.
- 상태: active — 교정 전체 자막·스트리머 전용 자막 완료. 사용자 확인 후 1차 내용 분석과 방향 3안 대기.
- handoff mode: same-workspace.
- 관련 권위: extension/docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md 및 영상 편집 rule route.

## 현재 단계

- 워크트리: D:/AI Agent/GitHub/Creator-dokkaebi, 브랜치 claude/dokkaebi, 기준 main bc341ae. core submodule 3e0ebe7.
- 원본 입력 위치: inputs/ (보호 경로, git 무시). 사용자가 원본 영상과 있으면 SRT를 넣는다.
- 산출물 계약: Premiere Pro CS6용 xmeml v4 XML 하나, 1920×1080·60fps. 출력 위치 extension/outputs/.
- 작업 profile: new_full_edit. 방향 미정 — 1차 내용 분석 후 근거가 다른 최대 3개 방향을 제시하고 사용자 선택을 받는다.

## 직전 게이트

- 편집 규칙 개선(사용자 승인): 분석 순서를 `원본 자막 확보·정확도/화자 확인 → 1차 내용 분석 → 시청자 관점 분석 → 편집 설계`로 보강. 변경 파일: VIDEO_EDITING_WORKFLOW_CONTRACT.md(다섯 작업 층·new_full_edit 흐름·방향안 기준), video-editing-story-and-cut-design.md(R05 행동·검증, R06 도입 질문), video-editing-intake-and-instructions.md(R03). extension 테스트는 수정 전 main과 동일한 30건 실패(PowerShell 7·Python 3.11 부재 등 VM 환경 원인)로 회귀 없음. Windows에서 scripts/verify.py 재실행 필요. 미커밋.
- 사용자 화자 피드백 반영: 85·87·166, 1594~1596·1606(급소/똥꼬 찌르기), 299·301을 스트리머로 변경. 427·428 스트리머, 990·1230·1482·1483·1530 문구 사용자 확인. 그 외 애매 목록은 현 분류 유지. 스트리머 전용 1,507큐 valid.
- 사용자 피드백 반영: 1594~1596·1606(급소/똥꼬 찌르기)과 85·87·166(UI 안내 낭독)을 스트리머로 변경. 이후 NPC 분류 목록(dokkaebi-npc-lines.md)에 대해 사용자가 '사극 말투로 구분이 잘 됐다'고 확인. streamer-only 1,505큐 valid.
- 자막 교정(사용자 요청): 첨부 SRT 타임스탬프 기준 1,694큐를 large-v3-turbo 전사와 대조해 전 큐 수동 교정·화자 분류(S 1475 / NPC 178 / 혼합 25 / 잡음 16). 산출물 extension/outputs/dokkaebi-asr/2026-10-08 11-01-06.corrected-full.srt(1,687큐, valid), 2026-10-08 11-01-06.streamer-only.srt(1,498큐, valid), dokkaebi-subtitle-review.json(큐별 원문·ASR·교정·라벨). 원본 타임스탬프 깨진 8큐만 최소 보정(0길이·역전·겹침). 화자 분류는 텍스트 문맥 기반이며 실제 청취 검수 not_run.
- 재전사: extension/outputs/dokkaebi-asr/dokkaebi-large-v3-turbo.srt (2587 cues, validate_srt valid), 원본 전사 JSON과 notes.json 동반. 방법은 notes.json 참조(반복 방지 설정 주 전사 + 이어받기 전사 보충 + 무VAD 재전사 + 기존 SRT 23개 fallback). 의미 전체 읽기 검수 not_done. 모델은 Creator-ainotebook runtime의 faster-whisper large-v3-turbo를 클라우드로 복사해 실행.
- 보조 파일: extension/outputs/dokkaebi-asr/audio16k_a.flac, audio16k_b.flac (분석용 16kHz 오디오, 작업 종료 시 정리 대상).

- 판정: pass. 워크트리·브랜치·core submodule 체크아웃 생성, 안내판 행 추가.

## 승인 상태

- 승인: 워크트리 생성, 산출물 형식(CS6 XML), 분석 후 방향 3안 제시.
- 미승인: 편집 방향, 컷 설계, commit·push.

## 차단

- 없음.

## 알려진 위험

- 워크트리는 Cowork Linux VM의 git으로 생성했고 경로 파일을 Windows 형식으로 맞췄다. Windows git에서 처음 열 때 `git status`로 정상 인식을 확인한다.

## 첫 다음 행동

1. 원본 inputs/2026-10-08 11-01-06.mp4 (12,728,534,764 bytes, 16481.917s, 1920×1080 60fps) 해시 기록은 미완.
2. 방향을 고정하지 않은 1차 내용 분석(전사·화면 표본) 후 최대 3개 방향을 제시한다.
