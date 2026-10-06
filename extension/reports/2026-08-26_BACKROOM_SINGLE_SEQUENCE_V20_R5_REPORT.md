# 백룸 단일 시퀀스 v20-r5 편집 보고서

> 상태: **superseded / 사용자 의미 검수 실패**. 사용자 정상 재생에서 timeline 1:05의 괴물 발견 원인이 누락되고 결과 위주로 과도하게 압축된 것이 확인됐다. 이 문서의 `semantic_gate: passed_internal` 판정과 88/100 점수는 철회하며 현재 후보 평가에 사용하지 않는다. 후속 교정은 r6가 소유한다.

## 결론

`backrooms_single_sequence_v20_r5.xml`은 v20-r4의 head-trim 기준에서 전체 구간을 다시 microbeat 단위로 편집한 Premiere CS6 v4 후보였다. 기존 결과를 덮어쓰지 않았고 outputs에는 XML 하나만 추가했다. 당시 내부 구조·의미·source media 검증을 통과로 판정했지만, 의미 판정은 후속 사용자 정상 재생에서 무효화됐다.

## 산출물

- XML: `outputs/07_edit_export/backrooms_single_sequence_v20_r5.xml`
- SHA-256: `b8dea6d2e98ac9afdd97b53677d029255a6d0c93084a8d6c827500ab839ddf11`
- size: 525,896 bytes
- profile: `premiere-cs6-v4`
- source reference: 승인된 MP4 한 개
- 별도 timeline JSON: outputs에 생성하지 않음

## 편집 결과

| 항목 | 결과 |
|---|---:|
| sequence | 1 |
| video clips | 114 |
| stereo audio clips | track당 115 |
| total frames | 27,790 |
| duration | 463.1667초 |
| video clip 평균 | 4.063초 |
| video clip 중앙값 | 3.375초 |
| video clip 최대 | 13.767초 |
| 10초 초과 | 1개 |
| 20초 초과 | 0개 |

v20-r4보다 271.2667초 짧아졌지만 목표 길이나 상한을 정해 맞춘 결과가 아니다. 각 구간의 정보, 행동, 반응, 화면 상태와 발화 호흡을 보고 남길 박자를 선택한 결과다.

## 적용한 판단

- v18은 current나 사용자 승인본으로 간주하지 않고 과거 microbeat 경계와 split-edit의 기술 근거로만 사용했다.
- v18 경계 92개를 현재 후보와 교차 검토해 재사용했다.
- v18에 없거나 현재 서사에서 필요한 구간은 source SRT·contact sheet·audio silence를 함께 검토해 22개 manual microbeat로 만들었다.
- 반복 비명 2곳, 추격 중 같은 애원의 반복, 문 앞 정지 대기, 같은 의미의 도발 반복을 줄였다.
- 화면상 위협 출현과 이동 판단이 계속 진행되는 13.767초 구간은 길다는 이유만으로 자르지 않았다.
- J/L 계열 split edit는 과거 근거가 있고 화면·음성 기능이 다른 5개 영상 구간의 6개 audio 조각에만 유지했다. 특정 기법 수나 비율을 목표로 삼지 않았다.

## 검증

| 계층 | 상태 | 근거 |
|---|---|---|
| timeline model | passed | 114 video, 115 audio, A/V total 일치, gap 0, bounds·source order·lineage 통과 |
| semantic gate | passed_internal | SRT 의미 순서, 113개 모든 video 경계 frame pair, exact assembled audio 순차 검수 |
| XML structure | passed | XMEML v4, 단일 sequence, stereo track 각 115 clips, source reference 1 |
| source video decode | passed | 선택된 114개 video 전 구간 실제 decode 성공 |
| source audio decode | passed | 선택된 115개 audio를 463.1667초 WAV로 exact assembly 성공 |
| audio boundary | passed_internal | 최대 normalized sample jump 0.126, 0.25 초과 0개 |
| regression | passed | video-editing 관련 48/48 tests |
| Premiere import | pending_user | 전체 r5 XML은 아직 미확인 |
| 정상 속도 전체 재생 | not_run | frame·segment 검증은 연속 시청을 대체하지 않음 |
| 사용자 승인 | not_run | current·approved·final 아님 |

## 철회된 자체 평가

당시 내부 검증 점수 **88/100**은 사용자 의미 검수 실패로 **철회됐다**. 아래 수치는 실패 당시 판단의 역사 기록일 뿐 현재 품질 점수가 아니다.

- 이야기·microbeat 선택: 26/30
- 화면·음성 연결과 기법 선택: 18/20
- XML·source media 기술 정확성: 30/30
- 실제 시청 검증과 승인: 14/20

감점 12점은 Premiere 전체 import와 정상 속도 연속 재생, 사용자 체감 템포 확인이 아직 없기 때문이다. 따라서 이 점수는 완성본 점수가 아니라 앱 검수 전 후보의 내부 품질 점수다.

## 후속 상태

r5는 더 이상 검수 후보가 아니다. 후속 교정과 재생 검수는 r6가 소유한다.
