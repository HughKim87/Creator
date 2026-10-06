# 백룸 단일 시퀀스 v20-r2 작업 보고서

- 목적: v20-r1의 자연스러운 연결은 유지하면서 서사 기능이 없는 혼잣말과 반복 반응을 제거해 템포를 높인다.
- 사용자 근거: “자연스럽게 편집된 느낌은 너무 좋지만 너무 루즈하고 지루하다. 앞뒤와 상관없는 의미 없는 혼잣말은 제거해도 된다.”
- 상태: `candidate`; 구조·선택 media·SRT·전환 frame 검증 통과, 실제 Premiere import·연속 재생·사용자 승인은 대기.
- XML: `outputs/07_edit_export/backrooms_single_sequence_v20_r2.xml`
- timeline JSON: `outputs/07_edit_export/backrooms_single_sequence_v20_r2_timeline.json`
- XML SHA-256: `90902ddb5fc4b13594cb68094ba7c9d7aa1de8d1e22acd80fa33ebdc0c3a8aad`
- timeline SHA-256: `b03d2a77a7eb408536f379c711b7681828b66e7c3073365c4207d4b3ea2d5c91`

## 결과와 delta

| 항목 | v20-r1 | v20-r2 | 변화 |
|---|---:|---:|---:|
| video clips | 65 | 63 | -2 |
| frames | 66,846 | 44,631 | -22,215 |
| 측정 초 | 1,114.1 | 743.85 | -370.25 |

시간을 목표로 줄인 것이 아니다. 다음 네 기능 중 하나도 없는 구간을 제거했다.

- 새 정보
- 행동 변화
- 감정 변화
- 공간 변화

## 제거·보존 기준

제거한 대표 유형:

- 방송 인사와 채팅 감사
- 긴 웃음·비명과 같은 반응의 반복
- 이미 드러난 공포를 다시 설명하는 혼잣말
- 진행과 무관한 자기평가와 가정
- 행동 사이의 망설임과 같은 문장의 반복

보존한 대표 유형:

- 백룸 공간을 처음 인지하는 반응
- 첫 사망 뒤의 거짓 적응
- 사다리·열쇠·문·시선·빛 규칙 발견
- 이동 기술의 소개, 실패와 성공
- 빛 안에서도 공격받는 반례
- 반복해도 공포가 남는다는 핵심 발언
- 출구를 지나침, 재발견, 통과 뒤 신체 긴장

## 검증

| 항목 | 결과 |
|---|---|
| timeline model | 통과 |
| XML | XMEML v4, sequence 1 |
| clips | video 63, stereo audio 2×63 |
| link·ID | 누락 0, ID 고유 |
| v18 schema contract | 예상 밖 element path 0 |
| SRT | cue 내부 in/out 0, same-cue skip 0 |
| 선택 media decode | 63/63 video+stereo audio 통과 |
| 컷 전후 화면 | 62/62 frame pair 확인 |
| 관련 회귀 테스트 | 49/49 통과 |
| Premiere import | `pending_user` |
| 정상 속도 전체 A/V | `not_run` |
| 사용자 승인 | `not_run` |

## 자체 점수

현재 증거 기준 후보 준비도는 **79/100**이다.

| 항목 | 배점 | 점수 | 이유 |
|---|---:|---:|---|
| 사용자 템포 피드백 반영 | 10 | 10 | 기능 없는 발화 370.25초 제거 |
| 시간 비목표·단일 sequence | 10 | 10 | 목표 길이 없이 하나의 흐름 유지 |
| source lineage·비파괴 revision | 10 | 10 | 승인 source 한 개, r1 보존 |
| 이야기 인과·반복 압축 | 20 | 18 | 핵심 사건 보존, 반복 설명 제거 |
| 발화·오디오 경계 | 15 | 13 | SRT 위험 0·decode 통과, 실제 청취 전 |
| 화면·공간 연속성 | 10 | 8 | 모든 전환 frame 확인, 동작 재생 전 |
| XML 구조·Premiere 계약 | 10 | 10 | 앱 검증 generator 계약과 일치 |
| 정상 속도 전체 A/V | 10 | 0 | `not_run` |
| v20-r2 실제 Premiere import | 3 | 0 | `pending_user` |
| 사용자 승인 | 2 | 0 | `not_run` |

79점은 완성도 승인이 아니라 검증 범위다. 실제 재생에서 빠르지만 거칠거나 여전히 지루한 구간이 확인되면 다음 delta에서 조정한다.

## 다음 검수

Premiere에서 v20-r2를 처음부터 끝까지 재생해 다음을 판단한다.

- 빨라진 템포가 조급하거나 뚝뚝 끊겨 보이지 않는가
- 남아 있는 혼잣말이 사건·행동·감정·공간 중 실제 기능을 갖는가
- 주차장 추격과 빛 규칙 구간이 반복처럼 느껴지지 않는가
- 출구 발견과 종료가 너무 급하게 끝나지 않는가

확인 전에는 `current`, `approved`, `final`로 승격하지 않는다.
