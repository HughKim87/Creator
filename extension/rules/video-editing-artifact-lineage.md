# 영상 편집 산출물 계보 규칙

- 목적: 편집 결과를 원본에서 재현 가능하게 유지하고 요청하지 않은 파생 파일의 증가를 막는다.
- 읽는 시점: 영구 증거, timeline, XML, 검토본, 사용자 전달 산출물을 만들거나 재사용할 때.
- 책임: 영상 편집 작업 에이전트가 source lineage와 산출물 수명을 유지하고 사용자가 영구 산출물과 보호 데이터 경계를 승인한다.
- 상태: 활성 소비 도메인 규칙.
- 관련 권위: `PROJECT_RULES.md`와 `extension/docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md`가 상위 권위다.

### R04 — 원본 단일 계보와 산출물 예산

- 조건: 영구 증거, timeline, XML 또는 검토 산출물을 만든다.
- 행동: 영구 화면·오디오·전사·XML clip은 exact 원본 미디어에서 직접 유도하고, 사용자에게 약속한 산출물만 만든다. `working_candidate` v2 payload와 cut decision·contact sheet·WAV·RMS·임시 frame·보조 전사는 작업 계약이 선언한 하나의 Git 제외 scratch root나 메모리에서 필요한 범위만 유지한다. task evidence는 활성 규칙 owner가 아니며, 반복 가능한 지식은 기존 rule-governance를 거쳐 가장 좁은 기존 rule 또는 candidate owner에만 반영한다. 사용자가 별도 산출물로 요청하지 않으면 내부 자료를 deliverable 폴더에 두지 않는다. XML 하나를 약속했다면 v2 payload는 내부 gate 입력이지 전달 sidecar가 아니다. `approved_delta`가 재사용할 `current` 또는 `approved` 기준본은 fingerprint 문자열만 남기지 않고 exact v2 artifact나 불변 snapshot을 하나의 보호 evidence owner로 승격해 `artifact_id / editorial_fingerprint / payload_fingerprint / task_payload_fingerprint / source_manifest / consumer / validation / superseded_by 또는 expiry`를 함께 유지한다. 전달 시 `source_manifest.path`는 XML이 실제 참조할 absolute canonical path여야 한다. source는 쓰기·삭제 공유를 거부하는 mandatory read handle로 잠근 채 처음 hash·size를 검사하고 XML 생성 뒤와 원자적 publish 직전에 같은 handle을 다시 검사한다. 이 snapshot을 보장할 수 없는 platform이나 filesystem에서는 fail closed한다. 기존 출력은 덮어쓰지 않는다.
- 예외: 편집본은 사용자 재생 비교와 결함 확인에만 사용할 수 있으며 후속 편집 source나 영구 증거가 될 수 없다.
- 검증: v2 source byte hash·size와 mandatory locked handle이 가리키는 exact source를 대조하고, 선언 경로가 absolute canonical path인지 확인한다. XML 생성 중 source byte가 바뀌거나 lock을 얻지 못하면 XML과 임시 파일이 0개이고 기존 출력은 그대로인지 결함 주입으로 확인한다. source lineage와 작업 시작 전후의 신규 영구 파일 목록에서 원본 이외 reference·계약 밖 산출물·deliverable 폴더의 내부 sidecar가 각각 0개인지 확인한다. 보존 evidence에는 source 범위·자료 유형·장면 의미·검증 상태·소비자·만료 조건이 있다. closeout 뒤 disposable scratch와 채택되지 않은 `working_candidate`는 0개이고, 아직 소비 중인 `current` 또는 `approved` 기준본은 exact evidence owner 하나에 남아 있는지 확인한다.

## 수명

- `working_candidate` v2 payload는 Git 제외 task scratch이며 채택되지 않으면 closeout에서 제거한다. timeline·XML·사용자 deliverable은 보호 파생물이며 Git에서 제외한다.
- `current` 또는 `approved`로 채택되어 후속 `approved_delta`의 기준이 되는 v2 artifact는 보호 evidence owner로 승격해 대체 revision과 보존 만료가 확정될 때까지 유지한다. editorial fingerprint만으로 exact 기준본을 대체하지 않는다.
- 분석 cache·contact sheet·WAV·RMS 배열·임시 frame·재전사는 기본적으로 task scratch이며 closeout에서 일괄 제거한다. 현재 작업 전부터 있던 자료나 보호 산출물에는 이 정리 경계를 소급 적용하지 않는다.
- 재사용 가능한 분석 자료를 남길 때는 `자료유형_시작시각[-종료시각]_장면-의미.ext`처럼 source 범위와 목적이 드러나는 이름을 사용하고, index는 자료의 목록·용도·검증 상태만 소유한다. 단일 영상의 정확한 시각·프레임·파일명은 일반 rule에 복사하지 않는다.
- 세션 원문과 버전별 보고서는 운영 규칙이나 runtime 의존성이 될 수 없다.

## 재현 사례

| ID | 상황 | 기대 판정 |
|---|---|---|
| TC04 | XML만 요청했는데 검토 MP4와 contact sheet도 만들려 함 | XML 외 산출물을 만들지 않는다 |
