# Backrooms 전체 18비트 v7 구조 감사

## 입력과 산출물

- source_id: `backrooms_20260630`
- 원본 영상: `inputs/2026-06-30 00-23-03.mp4`
- 원본 자막: `inputs/2026-06-30 00-23-03.srt`
- 기준본: `cutlist_full_18beat_v6.csv`
- 콘텐츠 컷리스트: `cutlist_full_18beat_v7.csv`
- 다중 시퀀스 컷리스트: `cutlist_full_18beat_v7_multisequence.csv`
- Premiere XML: `backrooms_full_18beat_v7.xml`
- 변경 결정표: `full_edit_v7_change_decisions_2026-07-14.csv`
- AI 재평가: `spine_review_v7_ai_reassessment_2026-07-14.json`
- 검증 페이지: `../review_2026-07-14/subtitle_review_full_v7_interactive_v2.html`

## v6→v7 적용 결과

- 113컷·734.43초에서 88컷·578.28초로 변경했다.
- 기존 컷 26개를 제거하고 B14 행동 증거 1개를 추가했다.
- B10 성공 컷 시작과 B15 대표 도전 끝, B17 의존 회수 끝을 말 단위로 줄였다.
- B02·B07·B10·B11·B15의 역할 과부하·표기 불일치를 재설계했다.
- B03·B04·B05·B09·B17의 반복 설명과 중복 반응을 함께 제거했다.
- B05→B06은 공포 사건→영화와 현실 차이 자각→떨림 증거의 연속 핵심 전환으로 라벨을 통일했다.

## 구조 검사 결과

- 콘텐츠 컷리스트: 88컷, 18비트와 훅 모두 존재.
- 선택 길이: 578.28초.
- 원본 시간 중복: 0건.
- 0초 이하 컷과 중복 `cut_id`: 0건.
- 다중 시퀀스 CSV: 파트 88행 + 전체 88행 = 176행.
- Premiere XML의 `02_시퀀스`: 훅·B01~B18 파트 19개 + 전체 1개 = 20개.
- 전체 시퀀스: 비디오 88클립, 오디오 L/R 2트랙 각각 88클립.
- 모든 전체 시퀀스 클립에서 타임라인 `end-start`와 원본 `out-in` 프레임 수가 일치한다.
- 전체 시퀀스 길이: 34,695프레임(60fps 기준 약 578.25초, 컷별 프레임 반올림 결과).
- XML 생성 도구가 원본 1개와 176행을 읽어 20개 시퀀스를 생성했다.

## 품질 감사

- 1차 감사: B03·B05 `AVG_LONG` 2건.
- 원본 사건과 대사 인과를 재확인하고 `edit_quality_profile_v7.csv`에 예외 근거를 기록했다.
- 2차 감사: `READY`, 미해결 검토 0건, 근거 있는 예외 2건.
- 예외는 경고 삭제가 아니라 `WAIVED`로 남았다.

## 검증 등급

- Generated: 통과
- Parsed: CSV·JSON·XML 파싱 통과
- Structure-validated: 컷·비트·시퀀스·프레임·오디오 구조 통과
- Tool-validated: Premiere XML 생성기와 편집 품질 감사 도구 통과
- App-validated: 미실시
- User-approved: 미실시

## 제한과 레드팀

- 새 v7 MP4는 만들지 않았다. 기존 v6 러프컷은 v7 재생 근거가 아니다.
- 자동 감사가 `READY`여도 B07 점프컷과 B11 콜백의 체감은 전체 순서 재생으로만 판단할 수 있다.
- B14 행동 증거를 추가했기 때문에 후반 박자는 좋아질 가능성이 크지만, B15와 붙였을 때 반복 도전처럼 느껴질 위험은 남아 있다.
- Premiere CS6 가져오기와 전체 재생 전에는 최종 사용 가능이나 최종 컷 흐름으로 확정하지 않는다.
