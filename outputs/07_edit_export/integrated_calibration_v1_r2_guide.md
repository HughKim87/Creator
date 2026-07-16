# integrated-calibration-v1 r2 사용 안내

## 목적

통합 기획의 초반·중간·후반 편집 문법만 확인하는 최소 대표 캘리브레이션이다. 전체 편집본이나 승인 기준본이 아니다.

## 주요 파일

- Premiere XML: `outputs/07_edit_export/integrated_calibration_v1_r2.xml`
- 멀티시퀀스 컷리스트: `outputs/07_edit_export/integrated_calibration_v1_r2_cutlist.csv`
- 7B 결정표: `outputs/07_edit_export/integrated_calibration_v1_r2_microbeat_decisions.csv`
- 검토 페이지: `outputs/review_2026-07-15/integrated_calibration_v1_r2.html`
- 감사 보고서: `outputs/07_edit_export/integrated_calibration_v1_r2_audit_2026-07-15.md`
- 자동 품질 감사: `outputs/07_edit_export/integrated_calibration_v1_r2_quality_audit.md`

## Premiere 확인

1. Premiere에서 `integrated_calibration_v1_r2.xml`을 가져온다.
2. `02_시퀀스` 빈의 A/B/C 세 시퀀스를 확인한다.
3. A는 V1만, B는 V1만, C는 V1과 종료부 무음 V2를 사용한다.
4. 원본 링크, 오디오 A1/A2, 마지막 자백까지 V2가 유지되는지 확인한다.

## 검토 순서

1. 검토 페이지에서 블라인드 모드를 켜고 A/B/C를 순서대로 본다.
2. “허세→붕괴→학습→익숙해져도 긴장 잔존”이 설명 없이 읽히는지 확인한다.
3. 발화 중간 절단, 급한 호흡, 전원 전후 화면 변화, 종료부 검은 프레임을 확인한다.
4. 통과 뒤에만 사용자 방향 체크포인트를 열고 전체 편집 확장 여부를 결정한다.

## 제한

- MP4를 생성하지 않았다.
- 브라우저 로컬 재생과 사람 수준 음성 청취, Premiere 앱 검증은 아직 통과하지 않았다.
- 사용자 승인 전 `approved_baseline`, `current_deliverable`, `edit_full`로 승격하지 않는다.

## 지원 파일 수명주기

`outputs/07_edit_export/support/build_integrated_calibration_v1.py`, 검토 페이지 생성기와 관련 테스트는 사용자 승인 또는 거부가 끝날 때까지 유지한다. 이후 승인된 산출물을 재현할 필요가 없을 때 정리한다.
