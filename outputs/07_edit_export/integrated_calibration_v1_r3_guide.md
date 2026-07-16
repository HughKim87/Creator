# integrated-calibration-v1 r3 사용 안내

## 주요 파일

- Premiere XML: `outputs/07_edit_export/integrated_calibration_v1_r3.xml`
- 컷리스트: `outputs/07_edit_export/integrated_calibration_v1_r3_cutlist.csv`
- 7B 결정표: `outputs/07_edit_export/integrated_calibration_v1_r3_microbeat_decisions.csv`
- 검토 페이지: `outputs/review_2026-07-15/integrated_calibration_v1_r3.html`
- 자동 품질 감사: `outputs/07_edit_export/integrated_calibration_v1_r3_quality_audit.md`
- 통합 감사: `outputs/07_edit_export/integrated_calibration_v1_r3_audit_2026-07-15.md`

## r3 확인 순서

1. A에서 `NPC 수준?` 동안 엔티티 근접 화면이 유지되는지 본다.
2. `근데 무서워`와 `빨리 가`가 감정 반전과 도주로 각각 읽히는지 본다.
3. B에서 전원 UI 조작이 실제로 보이고 밝은 방이 코미디 뒤 남는지 본다.
4. C에서 “여기까지 하겠습니다”가 잘리지 않고 마지막 자백 뒤 0.4초 화면 여운이 재생되는지 본다.
5. `C_TENSE_BODY`의 “해주고 싶어요”가 앞 문맥 없이 어색한지 실제 음성으로 확인한다.

## Premiere CS6

`파일 > 가져오기`에서 XML을 열고 `02_시퀀스`의 A/B/C를 확인한다. A와 C는 V2가 1개씩 있으며 모두 무음 화면이다. 원본 오디오는 V1의 A1/A2 링크 모노 2트랙으로 유지된다.

## 제한

- r3는 `calibration_candidate`이며 전체 편집본이 아니다.
- MP4를 생성하지 않았다.
- 실제 브라우저 재생·사람 수준 음성 청취·Premiere 앱 검증은 아직 통과하지 않았다.
- 사용자 최종 방향 승인 전 `approved_baseline`, `current_deliverable`, `edit_full`로 승격하지 않는다.
