# 백룸 v9 캘리브레이션 구조 감사

- 감사일: 2026-07-15
- 대상: `backrooms_v9_calibration.xml`
- 결과: `READY_FOR_USER_CALIBRATION_REVIEW`
- 전체 v9 승격: 금지

## 입력 추적

- 현재 전체 기준본: v8
- 기획 기준: `outputs/05_planning/video_plan_backrooms_v8_2026-07-14.md`
- 후보 기준: `outputs/06_analysis/backrooms_v8_6step_candidate_map_2026-07-14.md`
- 누적 편집문법: `outputs/07_edit_export/backrooms_editing_method_2026-07-12.md`
- 사용자 수정 지시: 훅 강화, 진입 단축, 설명보다 화면, 논지 축소, 캐릭터·코미디 회복, 문장 보존과 후보범위 보존 분리

## 구조 결과

| 시퀀스 | 길이 | V트랙 | 채널별 오디오 클립 | 판정 |
|---|---:|---:|---:|---|
| `CAL_A_훅과빠른진입` | 64.167초 | 2 | 4 | 통과 |
| `CAL_B_추격과코미디` | 73.983초 | 1 | 15 | 통과 |
| `CAL_C_주제회수와아이러니` | 60.783초 | 2 | 19 | 통과 |

- 실제 시퀀스: 정확히 3개.
- 총 비디오 클립: 48개.
- 연결 오디오 컷: 38개, L/R 각각 38개.
- V2 무음 컷어웨이: 10개, 오디오 클립 생성 0개.
- 모든 비디오·오디오 클립에서 타임라인 `end-start`와 원본 `out-in` 프레임 수 일치.
- A의 실제 백룸 진입 시작: 32초 이내.
- 연결 오디오 경계의 SRT 발화 내부 교차: 0건.

## 실패 원인과 생성기 개선

초기 XML 실패는 원본 FPS가 잘못된 것이 아니었다. 원본은 `60/1`이다.

- 잘못된 계산: `round((source_end-source_start) × fps)`
- XML의 실제 계산: `round(source_end × fps) - round(source_start × fps)`
- 사례: `B_HIDE 2244.040~2249.978`은 전자가 356프레임, 후자가 357프레임이다.

콘텐츠 빌더가 V1 타임라인 시작점을 직접 누적하지 않도록 바꿨다. 연결 컷의 `timeline_start`는 비워 두고, XML 생성기가 원본 메타데이터와 절대 in/out 프레임으로 순차 배치한다. 문제 구간은 공용 XML 생성기 회귀검사에 추가했다.

## 검증 페이지

- 파일: `outputs/review_2026-07-15/subtitle_review_v9_calibration_interactive_v1.html`
- 인라인 스크립트 문법: 통과.
- 원본 상대 경로 존재: 통과.
- 재생기 카드: `position: static`.
- `position: sticky`·`position: fixed`: 사용하지 않음.
- V1 원본 오디오와 V2 무음 화면을 분리 재생하는 구조: 존재.
- 인앱 브라우저의 로컬 파일 접근 제한으로 Codex 측 실제 재생은 미실행. 앱·오디오 검증으로 승격하지 않는다.

## 자동 검사

- Premiere XML·컷리스트·검증 페이지 관련 검사: 23개 통과.
- 검증 페이지 인라인 스크립트 별도 구문 검사: 통과.
- 사용자 입력·원본·v8 역사본 변경: 없음.
- 새 MP4: 없음.

## 남은 게이트

1. Premiere CS6에서 A·B·C 가져오기 확인.
2. 비명·웃음·호흡과 컷 끝 잔향을 실제로 듣기.
3. 사용자에게 A·B·C 대표 리듬 승인받기.
4. 승인된 편집문법만 전체 v9에 적용하기.
