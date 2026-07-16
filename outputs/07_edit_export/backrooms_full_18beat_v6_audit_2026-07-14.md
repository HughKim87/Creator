# Backrooms 전체 18비트 v6 구조 감사

## 입력과 출력

- 원본 영상: `inputs/2026-06-30 00-23-03.mp4`
- 원본 자막: `inputs/2026-06-30 00-23-03.srt`
- 사용자 첨부 원본 보존: `inputs/user_feedback/subtitle_review_result_full_v3_2026-07-14.json`
- 정본 컷리스트: `cutlist_full_18beat_v6.csv`
- 다중 시퀀스 컷리스트: `cutlist_full_18beat_v6_multisequence.csv`
- Premiere XML: `backrooms_full_18beat_v6.xml`
- 전체 러프컷: `roughcut_full_v6.mp4`
- 훅·초반 러프컷: `roughcut_hook_opening_v6.mp4`
- 자막 검증 페이지: `../review_2026-07-14/subtitle_review_full_v6.html`

## 구조 결과

- 정본: 113컷, 1개 전체 시퀀스.
- XML 입력: 파트 시퀀스 19개와 전체 시퀀스 1개, 총 20개 시퀀스.
- XML 컷 행: 파트 113개 + 전체 113개 = 226개.
- 선택 길이: 734.43초.
- XML 생성 도구의 구조 검증 통과.
- 정본 안의 원본 시간 중복: 0건.
- 훅 원본과 본문 원본 중복: 0건.
- 0초 이하 컷, 중복 cut_id, 누락된 18비트: 없음.

## 버전 판정

- v4: 사용자 거절. 훅의 보여주려는 사건이 완결되지 않았고 본문과 중복됨.
- v5: 내부 1차 검토본. 러프컷 검사에서 도입 말끝과 초기 공포 반응 경계가 짧게 잘리는 문제를 발견.
- v6: 해당 경계를 확장해 다시 생성한 최신 검토본. v5는 사용하지 않는다.

## 검증 등급

- Parsed: 통과
- Structure-validated: 통과
- Tool-validated: 통과
- Roughcut-rendered: 통과
- Visual-sampled: 통과
- App-validated: 미실시
- User-approved: 미실시

따라서 v6는 Premiere 가져오기와 사용자 청감 검토가 가능한 상태지만, 최종 승인 상태는 아니다.
