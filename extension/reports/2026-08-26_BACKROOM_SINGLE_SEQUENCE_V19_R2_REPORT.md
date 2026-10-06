# 백룸 단일 시퀀스 v19-r2 작업 보고서

- 목적: 목표 시간을 먼저 정하지 않고, 백룸 영상의 사건·공간·반응을 처음부터 끝까지 이어지는 하나의 Premiere XML로 구성한 결과와 검증 범위를 기록한다.
- 읽는 시점: `backrooms_single_sequence_v19_r2.xml`을 Premiere에서 검토하거나 다음 revision을 설계하기 전.
- 책임: 작업 에이전트가 source lineage와 기술·의미 검증 수준을 구분하고, 사용자가 실제 재생 결과와 최종 방향을 승인한다.
- 상태: `app-validation: failed`. 단일 sequence XML은 생성·파싱·선택 source 디코딩을 통과했지만 Premiere 가져오기에서 일반 오류로 거절됐다. 후속 사용 금지.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, `extension/reports/2026-08-26_BACKROOM_EDITING_RESUME_PLAN.md`, 사용자의 최신 교정.

## 1. 결과

- 결과 XML: `outputs/07_edit_export/backrooms_single_sequence_v19_r2.xml`
- SHA-256: `80c5314310eb1fdb5750bc28f05b89eb963fa822c984c8c8749a0e48ef3ab7b4`
- Premiere profile: `premiere-cs6-v4`
- sequence: `BACKROOM_SINGLE_SEQUENCE_V19_R2` 하나
- 구성: 영상 73개 clip, stereo 오디오 2트랙·146개 clip
- timeline: 52,055 frames at 60fps

52,055 frames는 편집 뒤 측정된 결과다. 14분이나 다른 길이를 목표·상한·합격 기준으로 사용하지 않았다. 필요한 사건을 고르고 발화를 완결된 cue 바깥으로 보존한 결과로만 기록한다.

이 XML은 `generated`, `parsed`, 선택 source 범위의 `media-validated`까지만 확인됐다. Premiere 실제 가져오기 실패로 `app-validation: failed`이며 `current`·추천본·완성본이 아니다.

## 2. 무엇을 만들었는가

v18의 166개 영상 clip을 완성본으로 승격하지 않고 source map으로만 사용했다. 이 중 서로 다른 이야기 기능을 가진 118개 clip의 source 범위를 회수하고, 반복 기능 48개는 제외했다.

남긴 진행은 다음 순서다.

1. 첫 진입과 실제 플레이 전환
2. 환경음·대공간·자기보호 판단으로 드러나는 공간 공포
3. 첫 사망과 곧바로 나오는 거짓 적응
4. 영화로 볼 때와 직접 들어왔을 때의 차이, 사다리·열쇠 목표
5. Level 0 탈출과 주차장 전환
6. 아몬드 물·정신력, 주차장 추격, 문·시선 규칙 학습
7. 어두운 새 층과 인간형 적, 죽음을 받아들이며 바뀌는 플레이 방식
8. 빛 규칙, Smiler, 이동 기술 학습과 반복 시도
9. 익숙해져도 처음 상황의 공포는 남는다는 회수
10. 출구 통과 뒤 남은 긴장, 소리의 의미 이해, 무서워서 끝내는 게 아니라는 농담과 종료

제외한 핵심 반복은 두 번째 공포·리스폰 묶음, 주차장 배회, 동일한 `자신감→재공포→사망` 기능을 다시 수행하는 구간이다. 원본 시간 순서를 바꾸거나 미래 장면을 끼우지 않았다.

## 3. 경계 보정

첫 단일-sequence preflight인 v19-r1은 한 sequence 형식은 맞았지만 SRT 기준 82개 source 점프 중 58개가 cue 내부와 맞물렸다. r1은 추천본으로 승격하지 않았다.

v19-r2에서는 다음을 적용했다.

- 같은 사건 안에서 3초 이하로 잘게 나뉜 source는 연속 범위로 합쳤다.
- 인·아웃이 SRT cue 내부면 해당 cue의 시작·끝 바깥 frame으로 확장했다.
- cue 확장으로 서로 겹친 인접 범위는 하나의 연속 clip으로 합쳐 말의 반복과 중복 재생을 막았다.
- 고정 컷 길이나 최종 영상 길이는 사용하지 않았다.

r2의 72개 source 점프 가운데 SRT 기준 실질적인 `same-cue skip`, 양쪽 cue 내부 절단, 다음 cue 중간 진입은 0개다. 두 경계가 `out-midcue`로 계산됐지만, 각각 60fps frame 격자 때문에 다음 cue 시작보다 약 9ms와 10ms 뒤에 놓인 양자화 사례다. 실제 청취 전에는 무결하다고 단정하지 않는다.

## 4. 검증

| 계층 | 결과 | 근거 |
|---|---|---|
| generated | 통과 | 새 경로에 v19-r2 생성, v18·v3-r1·v19-r1 미변경 |
| strict UTF-8 / XML parse | 통과 | NUL 0, XMEML v4 파싱 |
| structure | 통과 | sequence 1, 영상 73, 오디오 2트랙·146, clipitem ID 220개 모두 고유 |
| link | 통과 | 누락 link reference 0, 각 영상 clip과 stereo audio 연결 |
| timeline | 통과 | 공백 0, 겹침 0, source 역행 0 |
| source lineage | 통과 | 현재 worktree의 승인된 원본 MP4 한 개만 참조 |
| media decode | 통과 | 73개 선택 범위의 H.264 영상+AAC stereo 동시 decode, 실패 0 |
| SRT 경계 preflight | 제한 통과 | 실질 cue 내부 점프 0, frame 양자화 경계 2개 |
| 순차 의미 검수 | 제한 통과 | v18 장면명·전체 SRT·source 순서로 인과와 반복 기능 검토 |
| 관련 회귀 테스트 | 통과 | Premiere CS6·workflow·subtitle·runtime·handoff routing 51/51 |
| 정상 속도 전체 A/V 청취 | `not_run` | 자동 decode와 SRT는 실제 청취를 대체하지 않음 |
| Premiere import·재생 | **실패** | 사용자가 v19-r2 가져오기에서 `가져오기 도구에서 일반 오류`를 확인 |
| 사용자 승인 | `not_run` | 이 artifact에 대한 판단 전 |

## 5. 자체 검증 점수

이전 임시 점수 58/100은 Premiere 실패 확인으로 철회했다. 현재 증거 기준 점수는 **52/100**이다.

| 항목 | 배점 | 점수 | 이유 |
|---|---:|---:|---|
| 단일 연속 sequence·시간 비목표 계약 | 10 | 10 | 형식과 최신 지시 충족 |
| source lineage·비파괴 revision | 10 | 10 | 원본 한 개, 이전 결과 미변경 |
| 이야기 선택·반복 압축 | 20 | 14 | SRT·장면 지도상 기능 구분, 실제 연속 시청 전 |
| 발화·화면 경계 | 15 | 8 | SRT 경계 보정 완료, 실제 청취·화면 접합 미검증 |
| XML 구조·링크 | 10 | 4 | XML parser 검사는 통과했지만 Premiere importer가 거절 |
| 선택 source 디코딩 | 10 | 6 | 모든 범위 decode 통과, 완성 timeline 재생은 아님 |
| 정상 속도 연속 A/V 검수 | 15 | 0 | `not_run` |
| Premiere 검증 | 5 | 0 | `not_run` |
| 사용자 승인 | 5 | 0 | `not_run` |

52점은 영상 완성도나 승인 비율이 아니라 현재 증명된 범위의 진단 점수다. 이 XML은 가져오지 못하므로 편집 결과로 사용할 수 없다.

## 6. Premiere import 실패 진단

확인된 사실은 다음과 같다.

- v19-r2는 3줄뿐이고 XML 본문 한 줄의 길이가 약 248,012자다. v18은 16,646줄·최대 215자, calibration-v3-r1은 606줄·최대 128자다.
- v18과 calibration-v3-r1은 `file/media/audio/channelcount`를 사용한다. v19-r2는 `channelcount`를 `file/media/audio/samplecharacteristics` 아래에 잘못 배치한다.
- v19-r2는 비교 XML에 없는 `sequence/media/audio/format/samplecharacteristics/rate`와 clip별 `logginginfo`·`labels`를 생성하며, 비교 XML에 있는 `file/timecode/reel`은 누락한다.

Premiere 대화상자는 일반 오류만 제공하므로 어느 한 차이가 직접 원인인지까지는 확정되지 않았다. 다만 기존 자동 테스트가 Premiere 실제 import 호환성을 증명하지 못했고, 생성기가 알려진 XML 구조와 다른 문서를 만든 것이 확인됐다.

같은 결과를 만들려는 세 번째 실패가 확정됐으므로 이 세션에서는 v19-r3를 만들지 않는다. 다음 재시작에서는 전체 편집보다 먼저, 알려진 import 가능 구조를 그대로 따르는 최소 1-clip XML로 generator 계약을 재검증해야 한다.

## 7. 다음 검수

v19-r2는 후속 검수에 사용하지 않는다. generator의 Premiere 호환 구조를 다시 검증한 새 작업에서만 다음 candidate를 만든다.

특히 다음을 확인한다.

- 첫 진입 종료→환경음 첫 인지 접합
- 첫 사망→거짓 적응의 말끝과 리스폰 화면
- 주차장 추격→안전실→문 규칙의 호흡
- 빛 규칙→불 꺼짐 체감의 공간 이해
- Smiler 시도→근성게임 재정의→구간 통과의 반복 밀도
- 적응 메시지→마지막 탈출→방송 종료의 의미 회수
- frame 양자화로 표시된 첫 진입 뒤 경계와 Smiler 학습 구간 경계

새 candidate가 실제 Premiere import를 통과하기 전에는 전체 sequence를 다시 생성하거나 current 포인터를 갱신하지 않는다.
