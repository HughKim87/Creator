# 백룸 단일 시퀀스 v20-r1 작업 보고서

- 목적: 목표 시간을 먼저 정하지 않고 백룸의 공간·사건·반응을 하나의 연속 Premiere sequence로 편집한다.
- 상태: `superseded_by_user_tempo_feedback`; 자연스러운 연결은 긍정 평가를 받았지만 루즈하고 무의미한 혼잣말이 많아 v20-r2로 교정.
- XML: `outputs/07_edit_export/backrooms_single_sequence_v20_r1.xml`
- timeline JSON: `outputs/07_edit_export/backrooms_single_sequence_v20_r1_timeline.json`
- XML SHA-256: `16417be96127fe71dc6cc57d68632fe3c89dcd5714e3a23d057cd7202f44a567`
- timeline SHA-256: `5c27c88311800ccc056dcf8045d6f0be762e92c8ae3173bede588b4a567be0de`

## 1. 편집 결과

- sequence 1개
- video 65 clips
- stereo audio 2 tracks, 각 65 clips
- 66,846 frames at 60fps
- 측정 길이 1,114.1초

길이는 편집 뒤 측정한 결과다. 목표 시간, 상한, 컷 길이 규칙으로 사용하지 않았다.

## 2. 이야기 구조

1. 인게임 진입과 백룸 공간의 첫 인지
2. 환경음·대공간·자기보호 판단으로 커지는 공포
3. 첫 사망과 곧바로 나오는 거짓 적응
4. 관람과 직접 플레이의 차이, 사다리·열쇠 목표
5. Level 0 탈출과 주차장 진입
6. 추격·안전실·문과 시선 규칙 학습
7. 어두운 새 층과 플레이 방식 변화
8. 빛 규칙과 이동 기술의 발견, 실패와 성공
9. 반복해도 남아 있는 공포와 출구 발견
10. 소리의 의미 회수와 방송 종료

## 3. v19-r2에서 바로잡은 부분

초·중반 선택은 v18 장면 지도, 전체 SRT, 원본 대표 화면으로 다시 확인한 뒤 유지했다. 후반은 v19-r2를 그대로 사용하지 않았다.

- 불이 꺼진 뒤 왜 위험한지 설명하고 다음 밝은 구역으로 이동하는 판단을 복원했다.
- 쉬프트 점프 기술이 갑자기 등장하지 않도록 기술 소개와 첫 시도를 추가했다.
- 반복 사망을 나열하지 않고 `기술 발견→실패→재시도→성공` 변화가 보이게 묶었다.
- `적응했다`는 말만 남기지 않고 빛 안에서도 공격받는 반례와 공포 잔존 발언을 연결했다.
- 출구를 지나친 이유, 다시 찾는 행동, 통과 뒤 몸의 긴장을 연속 의미 단위로 보존했다.

이 교정으로 clip 수는 73개에서 65개로 줄었지만 측정 길이는 867.583초에서 1,114.1초로 늘었다. 시간 목표를 바꾼 것이 아니라 짧은 반응 조각 사이에서 빠졌던 원인·행동·결과를 복원한 결과다.

## 4. 검증 결과

| 항목 | 결과 | 근거 |
|---|---|---|
| timeline model | 통과 | frame equation, 연속성, bounds, source order, lineage |
| XML header·schema | 통과 | 앱 검증된 XMEML v4 계약, v18에 없는 element path 0 |
| sequence | 통과 | 1개 |
| clip·link | 통과 | video 65, audio 130, ID 고유, 누락 link 0 |
| source | 통과 | 승인된 현재 MP4 한 개만 참조 |
| SRT 경계 | 통과 | cue 내부 in/out 0, same-cue skip 0 |
| 선택 media decode | 통과 | 65/65 video+stereo audio, 실패 0 |
| 대표 화면 검수 | 제한 통과 | 7개 이야기 구간 대표 화면 확인 |
| 컷 전후 화면 | 제한 통과 | 64개 transition의 out/in frame pair 확인 |
| 관련 회귀 테스트 | 통과 | 49/49 |
| Premiere import | `pending_user` | generator fixture는 통과, 이 전체 XML은 미확인 |
| 정상 속도 전체 A/V | `not_run` | segment decode·정지 frame은 실제 연속 시청을 대체하지 않음 |
| 사용자 승인 | `not_run` | candidate 지위 유지 |

## 5. 자체 점수

현재 증거 기준 후보 준비도는 **78/100**이다.

| 항목 | 배점 | 점수 | 이유 |
|---|---:|---:|---|
| 시간 비목표·단일 sequence | 10 | 10 | 최신 지시 충족 |
| source lineage·비파괴 revision | 10 | 10 | 원본 한 개, 기존 결과 미변경 |
| 이야기 인과·반복 압축 | 20 | 17 | 후반 원인·행동·결과 복원, 전체 정상 속도 시청 전 |
| 발화·오디오 경계 | 15 | 13 | SRT 위험 0·decode 통과, 실제 청취 전 |
| 화면·공간 연속성 | 10 | 8 | 모든 transition frame 확인, 동작 중 접합 재생 전 |
| XML 구조·Premiere 계약 | 10 | 10 | 앱 검증 generator 계약과 일치 |
| 선택 media decode | 10 | 10 | 65/65 통과 |
| 정상 속도 전체 A/V | 10 | 0 | `not_run` |
| v20-r1 실제 Premiere import | 3 | 0 | `pending_user` |
| 사용자 승인 | 2 | 0 | `not_run` |

78점은 완성도 승인 점수가 아니라 현재 증명된 검증 범위다. 실제 Premiere 재생에서 말끝, 움직임, 리듬 문제가 발견되면 점수와 후보 지위를 즉시 낮춰야 한다.

## 6. 다음 검수

Premiere에서 v20-r1을 가져와 하나의 sequence와 연결된 stereo audio를 확인한다. 이후 처음부터 끝까지 정상 속도로 재생하며 특히 다음을 본다.

- 첫 진입에서 공간 공포로 넘어가는 속도
- 첫 사망 뒤 거짓 적응의 호흡
- 주차장 추격·안전실·규칙 학습의 연결
- 빛 규칙 설명과 실제 위반 장면의 이해 가능성
- 이동 기술의 발견·실패·성공이 반복이 아니라 변화로 보이는지
- 출구를 지나침→재발견→긴장 회수의 리듬
- 방송 종료 직전 농담과 마지막 말의 여운

사용자 확인 전에는 `current`, `approved`, `final`로 승격하지 않는다.
