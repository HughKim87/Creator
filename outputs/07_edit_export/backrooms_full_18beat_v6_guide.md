# Backrooms 전체 18비트 v6 사용 가이드

## 먼저 확인할 파일

1. 빠른 훅·초반 확인: `roughcut_hook_opening_v6.mp4`
2. 전체 편집 확인: `roughcut_full_v6.mp4`
3. 자막별 포함·제외 확인: `../review_2026-07-14/subtitle_review_full_v6.html`
4. Premiere 작업 시작: `backrooms_full_18beat_v6.xml`

v5는 러프컷 경계 검사에서 교체된 내부 검토본이다. 최신 기준은 v6이다.

## Premiere CS6 가져오기

1. Premiere에서 `파일 > 가져오기`를 선택한다.
2. `backrooms_full_18beat_v6.xml`을 고른다.
3. 미디어 연결 창이 나오면 `inputs/2026-06-30 00-23-03.mp4`를 연결한다.
4. `00_원본`, `01_후보타임라인`, `02_시퀀스` 구조와 20개 편집 시퀀스를 확인한다.
5. `FULL_전체18비트_v6`을 처음부터 끝까지 재생한다.
6. 오디오가 L/R 모노 두 트랙으로 보일 수 있으므로 볼륨만 맞추고 트랙을 임의로 삭제하지 않는다.

## 확인 우선순위

- 00:00~00:13: 엔티티 등장·비명·사망으로 훅이 완결되는지.
- 훅 직후: 사망 화면에서 게임 소개로 전환이 명확한지.
- 초반: 게임 도입, 탈출 목표, 초기 공포, 엔티티·그림자 설명이 과하게 늘어지지 않는지.
- 중반: 바닥 추락과 두 번째 맵 전환이 이해되는지.
- 추격: 추가된 1940초대 접근 장면과 기존 B08 추격이 반복처럼 느껴지지 않는지.
- 후반: 통영상 위주로 풀리지 않고 리듬이 유지되는지.

## 파일 역할

- `cutlist_full_18beat_v6.csv`: 검증과 품질 감사용 단일 정본.
- `cutlist_full_18beat_v6_multisequence.csv`: Premiere XML 생성용 파트+전체 시퀀스 기록.
- `full_edit_v6_added_timestamp_decisions_2026-07-14.csv`: 사용자 선택 66개를 사용·일부 사용·제외로 판정한 근거.
- `edit_quality_profile_v4.csv`: 비트별 편집 모드.
- `backrooms_full_18beat_v6_quality_report_2026-07-14.md`: 사람이 읽는 품질 검증 결과.
- `backrooms_full_18beat_v6_audit_2026-07-14.md`: 구조·도구 검증 결과.
