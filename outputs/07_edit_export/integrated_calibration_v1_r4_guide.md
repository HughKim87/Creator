# integrated-calibration-v1 r4 사용 안내

## 산출물 상태

- source_id: `backrooms_20260630`
- 역할: `calibration_candidate`
- 기준 버전: `integrated-calibration-v1 r3`
- 현재 버전: `integrated-calibration-v1 r4`
- 상태: `candidate_ready_with_playback_gap`
- 검증 수준: Structure-validated, Tool-validated
- 구조·화면 사전점검: 92/100
- 전체 편집 확장: 금지
- 사용자 방향 승인: 필요
- Premiere 앱 검증: 미완료
- MP4 생성: 없음

## 파일

- 컷리스트: `outputs/07_edit_export/integrated_calibration_v1_r4_cutlist.csv`
- microbeat 결정표: `outputs/07_edit_export/integrated_calibration_v1_r4_microbeat_decisions.csv`
- 품질 감사: `outputs/07_edit_export/integrated_calibration_v1_r4_quality_audit.md`
- Premiere CS6 XML: `outputs/07_edit_export/integrated_calibration_v1_r4.xml`
- 검토 페이지: `outputs/review_2026-07-15/integrated_calibration_v1_r4.html`
- 통합 감사: `outputs/07_edit_export/integrated_calibration_v1_r4_audit_2026-07-15.md`

## Premiere CS6에서 확인

1. `파일 > 가져오기`에서 `integrated_calibration_v1_r4.xml`을 선택한다.
2. 연결 창이 뜨면 `inputs/2026-06-30 00-23-03.mp4`를 지정한다.
3. `02_시퀀스` 안의 A/B/C 대표 시퀀스를 연다.
4. CS6의 알려진 구조대로 오디오 A1/A2가 링크 모노 2트랙으로 들어왔는지 확인한다.
5. A의 `A_HOOK_TAUNT` 끝에서 말이 잘리지 않는지 먼저 듣는다.
6. B의 실제 스위치 2.4초가 느리게 느껴지는지 확인한다.
7. C에서 과거 통로 2초가 회고로 읽히고, sign-off→자백의 두 방 앵글과 0.4초 tail이 자연스러운지 확인한다.

## 변경 요약

- 훅: `뭐? 뭐?` 엔티티 접근 추가, 반복 도발 압축, 반복 V2 제거, 11.90초
- B: 위치 설명 제거, 발견 반응부터 시작, 실제 조작·밝은 결과 유지, 13.72초
- C: 중복 적응 문장과 문맥 불완전 긴장 문장 제거, 과거 통로 회고 V2와 엔딩 두 앵글 적용, 화면 tail 포함 20.32초

## 사용 금지 조건

- 원본 영상이나 SRT가 바뀐 경우
- `backrooms_20260630` 원본 지문이 달라진 경우
- 실제 연속 음성 청취 없이 `approved_baseline` 또는 전체 편집으로 승격하려는 경우
- Premiere에서 열지 않았는데 App-validated로 표시하려는 경우

## 남은 확인

- 훅의 cue 내부 무음 경계 `2338.837`
- 훅→본편 리셋의 체감 강도
- B 스위치 조작 2.4초의 실제 템포
- C 회고 V2와 엔딩 두 앵글의 체감 자연스러움
- Premiere CS6 가져오기와 원본 오디오 재생
