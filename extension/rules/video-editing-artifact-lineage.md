# 영상 편집 산출물 계보 규칙

- Purpose: 편집 결과를 원본에서 재현 가능하게 유지하고 요청하지 않은 파생 파일의 증가를 막는다.
- Read when: 영구 증거, timeline, XML, 검토본, 사용자 전달 산출물을 만들거나 재사용할 때.
- Authority: `PROJECT_RULES.md`와 `extension/docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md`가 상위 권위다.

### R04 — 원본 단일 계보와 산출물 예산

- 조건: 영구 증거, timeline, XML 또는 검토 산출물을 만든다.
- 행동: 영구 화면·오디오·전사·XML clip은 exact 원본 미디어에서 직접 유도하고, 사용자에게 약속한 산출물만 만든다. 기존 출력은 기본적으로 덮어쓰지 않는다.
- 예외: 편집본은 사용자 재생 비교와 결함 확인에만 사용할 수 있으며 후속 편집 source나 영구 증거가 될 수 없다.
- 검증: source lineage와 신규 파일 목록을 대조하고, 원본 이외 source reference와 요청하지 않은 미디어가 각각 0개인지 확인한다.

## 수명

- timeline·XML·사용자 deliverable은 보호 파생물이며 Git에서 제외한다.
- 분석 cache·RMS 배열·임시 frame·재전사는 재생성 가능한 runtime으로 유지한다.
- 세션 원문과 버전별 보고서는 운영 규칙이나 runtime 의존성이 될 수 없다.

## 재현 사례

| ID | 상황 | 기대 판정 |
|---|---|---|
| TC04 | XML만 요청했는데 검토 MP4와 contact sheet도 만들려 함 | XML 외 산출물을 만들지 않는다 |
