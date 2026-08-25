# 영상 편집 산출물 계보 규칙

- 목적: 편집 결과를 원본에서 재현 가능하게 유지하고 요청하지 않은 파생 파일의 증가를 막는다.
- 읽는 시점: 영구 증거, timeline, XML, 검토본, 사용자 전달 산출물을 만들거나 재사용할 때.
- 책임: 영상 편집 작업 에이전트가 source lineage와 산출물 수명을 유지하고 사용자가 영구 산출물과 보호 데이터 경계를 승인한다.
- 상태: 활성 소비 도메인 규칙.
- 관련 권위: `PROJECT_RULES.md`와 `extension/docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md`가 상위 권위다.

### R04 — 원본 단일 계보와 산출물 예산

- 조건: 영구 증거, timeline, XML 또는 검토 산출물을 만든다.
- 행동: 영구 화면·오디오·전사·XML clip은 exact 원본 미디어에서 직접 유도하고, 사용자에게 약속한 산출물만 만든다. contact sheet·WAV·RMS·임시 frame·보조 전사는 task-rule이 선언한 하나의 scratch root에서 필요한 범위만 만들고, 재사용 규칙은 발견 즉시 task-rule에 기록한다. 후속 작업의 명시된 소비자·검증·만료 조건이 모두 있을 때만 자료를 scratch 밖의 하나의 evidence owner로 승격한다. 기존 출력은 기본적으로 덮어쓰지 않는다.
- 예외: 편집본은 사용자 재생 비교와 결함 확인에만 사용할 수 있으며 후속 편집 source나 영구 증거가 될 수 없다.
- 검증: source lineage와 신규 파일 목록을 대조하고, 원본 이외 source reference와 요청하지 않은 미디어가 각각 0개인지 확인한다. 보존 evidence에는 source 범위·자료 유형·장면 의미·검증 상태·소비자·만료 조건이 있고, closeout 뒤 task scratch와 active task-rule owner는 0개다.

## 수명

- timeline·XML·사용자 deliverable은 보호 파생물이며 Git에서 제외한다.
- 분석 cache·contact sheet·WAV·RMS 배열·임시 frame·재전사는 기본적으로 task scratch이며 closeout에서 일괄 제거한다. 현재 작업 전부터 있던 자료나 보호 산출물에는 이 정리 경계를 소급 적용하지 않는다.
- 재사용 가능한 분석 자료를 남길 때는 `자료유형_시작시각[-종료시각]_장면-의미.ext`처럼 source 범위와 목적이 드러나는 이름을 사용하고, index는 자료의 목록·용도·검증 상태만 소유한다. 단일 영상의 정확한 시각·프레임·파일명은 일반 rule에 복사하지 않는다.
- 세션 원문과 버전별 보고서는 운영 규칙이나 runtime 의존성이 될 수 없다.

## 재현 사례

| ID | 상황 | 기대 판정 |
|---|---|---|
| TC04 | XML만 요청했는데 검토 MP4와 contact sheet도 만들려 함 | XML 외 산출물을 만들지 않는다 |
