# 백룸 Premiere generator probe v1 보고서

- 목적: 앱에서 검증된 v18 XML 계약을 수정된 generator가 독립적으로 재현하는지 확인한다.
- 상태: `local-validation: passed`, `app-import: passed`
- 결과: `outputs/07_edit_export/backrooms_premiere_generator_probe_v1.xml`
- SHA-256: `a2dc186830d88bf60bdb5405d65376b418140c08a090e68fcccefa77629eb7c3`

## generator 교정

Premiere CS6 v4 프로필에만 다음 계약을 적용했다. 기존 sequence-v5 바이트 출력은 유지했다.

- audio `channelcount`를 `file/media/audio`의 직접 자식으로 이동
- file timecode의 `reel/name`과 source video `duration` 복원
- sequence audio format에서 불필요한 rate·channelcount 제거
- clipitem의 rate·logginginfo·labels와 video sourcetrack 제거
- master clipitem과 sequence·track child 순서를 v18 구조에 맞춤
- video link에는 groupindex를 넣지 않고 audio link에만 groupindex 사용
- 60fps non-NTSC rate를 v18처럼 timebase만으로 기록

## 검증 결과

| 항목 | 결과 |
|---|---|
| 관련 회귀 테스트 | 49/49 통과 |
| XML header | v18과 같은 선언·DOCTYPE |
| XMEML | version 4, sequence 1 |
| clips | video 1, audio track 2, audio clip 2 |
| timeline/source | 0–2,369 / 19,495–21,864 frames |
| source path | 현재 worktree의 승인된 MP4 |
| link | 누락 target 0 |
| schema drift | v18에 없는 element path 0 |
| 직렬화 | 258 lines, 최대 128자 |

## 남은 게이트

사용자가 이 generator 출력 자체도 Premiere와 호환된다고 확인했다. 따라서 최소 fixture 범위의 generator 앱 호환 계약은 통과했다. 전체 sequence의 실제 import·재생은 별도 검증한다.

이 fixture는 편집 후보가 아니며 `current`, `approved`, `final` 지위가 없다.
