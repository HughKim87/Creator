# Premiere CS6 XML 효과 호환표

- 목적: Premiere Pro CS6가 xmeml XML import에서 실제로 읽는 효과·요소를 확인된 사실로만 기록해, 확인되지 않은 효과를 해결책으로 제안하거나 산출물에 넣지 않게 한다.
- 읽는 시점: XML 산출물에 효과·속성(속도, 확대, 키프레임, 오버레이, 오디오 채널 등)을 넣으려 할 때.
- 책임: 영상 편집 작업 에이전트가 확인 결과를 추가하고 사용자가 앱 import·재생 결과를 확인한다.
- 상태: 참고 사실 표. 운영 규칙이 아니며 R03의 확인 절차가 이 표를 사용한다.
- 관련 권위: `extension/rules/video-editing-intake-and-instructions.md`(R03), `VIDEO_EDITING_RULE_CANDIDATES.md`(CAND08).

## 판정 기준

- `✓ app`: 사용자 CS6에서 import·재생이 확인됨.
- `✓ export 구조`: 사용자 CS6가 내보낸 같은 효과의 XML 구조를 그대로 따름(import 재확인은 사용자 몫).
- `✗`: 실제 import에서 무시·변환 실패가 확인됨.
- 표에 없는 효과는 미확인이다. 넣기 전에 export 구조 확인이나 짧은 샘플 import를 먼저 한다.

## 확인된 효과·요소

| 효과·요소 | 판정 | 확인 일자 | 근거·메모 |
|---|---|---|---|
| 오디오 Gain 필터(`Gain(dB)` value) | ✗ | 2026-10-14 | CS6가 내보낸 XML의 Gain value 3을 그대로 넣어 가져오면 모든 클립에 "+6db 넘는 오디오 레벨 → +6db로 클램프" 경고. 값을 dB로 읽지 않음(선형 배율로 해석 추정, 미검증). XML에 넣지 않고 Premiere에서 오디오 게인으로 직접 적용 |
| Time Remap(클립 속도) | ✗ | 2026-10-10 | 모든 클립에서 "Time Remap 효과가 변환되지 않았습니다"로 무시됨. XML로 배속을 전달할 수 없다 |
| Basic Motion scale·center(확대·위치) | ✓ export 구조 → 사용자 사용 | 2026-10-11 | video clipitem 안 `<file/>` 뒤·`<link>` 앞에 `<filter><effect>` (effectid basic, parameter scale·rotation·center·centerOffset). center = ((X−960)/1920, (Y−540)/1080) |
| 투명 PNG still 오버레이(자막·카드·강조, 프레임별 연출) | ✓ 사용자 사용 확정 | 2026-10-11 | alphatype straight, stillframe. CS6 키프레임 대신 프레임별 PNG로 움직임을 구움 |
| 스테레오 WAV 효과음 2트랙 | ✓ 사용자 사용 확정 | 2026-10-11 | sourcetrack 1/2, outputchannelindex 1/2 |
| 말소리 배속 + 오디오 피치 유지(앱 기능) | 앱 기능은 동작, 음질 거부 | 2026-10-10 | 사용자 판단: 목소리가 이상함. 말소리 구간에는 배속을 쓰지 않는다(CAND15) |

## 출처와 재사용 한계

`before-claude-dokkaebi`의 동일 경로에서 흡수했다. 원래 반영 커밋은 `59d4240`과 후속 `ca499da`다. 이 표는 당시 기록된 앱 관측의 보존이며 이번 통합에서 CS6 import를 재현한 결과가 아니다. 새 버전·다른 효과에 성공을 확장하지 않는다.
