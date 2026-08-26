# Creator 백룸 영상 편집 현재 상태

- 목적: 새 Codex 세션이 긴 대화 기록 없이 백룸 영상 편집을 올바른 방향으로 재개하게 한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md 다음.
- 책임: 작업 에이전트가 검증된 현재 상태와 재개 지점을 유지하고, 사용자가 편집 방향과 승인 상태를 결정한다.
- 상태: 중단 인계. 현재 승인 후보 없음.
- 관련 권위: core/PROJECT_RULES.md, PROJECT_RULES.md, 영상 편집 관련 extension/rules.
- handoff mode: same-workspace
- 로컬 의존성: 보호 입력·출력과 local FFmpeg runtime은 Git만으로 복원되지 않으며 uncommitted 변경이 있다.

## 현재 단계

- 단계: 이전 세션의 반복 실패 중단 후 새 세션 재개 대기.
- 활성 전체 설계: 없음.
- 활성 단계 설계: 없음.
- 현재 편집 후보: 없음.
- current / approved / final revision: 없음.
- 직전 게이트: v21-r2 사용자 방향 검수 실패.
- 중단 이유: 인과 누락을 막는다는 이유로 긴 원본 구간을 통째로 남겨, 사용자가 요구한 촘촘한 microcut과 실제 편집 리듬을 포기했다.
- 실패 카운터: 이전 세션의 중단 조건은 종료됐다. 새 세션은 이전 횟수를 이어받지 않고 새 카운터로 시작한다.

## 작업 위치

- worktree: D:\AI Agent\GitHub\Creator-backroom
- branch: codex/backroom-video
- HEAD: fc7e0fd8a623350ad612b317e6cf389317ac2a4c
- 기준 commit 메시지: docs(backroom): define editing resume plan
- tracked dirty files:
  - SESSION_HANDOFF.md
  - extension/reports/2026-08-26_BACKROOM_EDITING_RESUME_PLAN.md
  - extension/src/video_editing/premiere_xml.py
  - extension/tests/test_video_editing_premiere_cs6.py
- 여러 과거 보고서가 untracked다. 새 세션은 사용자가 요청하지 않는 한 정리·삭제·commit하지 않는다.
- 기존 변경은 사용자 작업으로 취급하고 덮어쓰지 않는다.

## 사용자가 원하는 편집 방향

한 편의 연속 Premiere XML을 만든다. 목표 러닝타임이나 고정 컷 길이를 먼저 정하지 않는다.

반드시 동시에 만족해야 한다.

1. 촘촘한 microcut
   - 무의미한 혼잣말, 앞뒤와 무관한 발화, 같은 반응 반복, 죽은 이동과 망설임을 적극적으로 제거한다.
   - 단순히 긴 원본 구간을 이어 붙이는 rough assembly나 통편집은 금지한다.

2. 사건 개연성
   - 상황 설정 → 발견/원인 → 행동 → 결과 → 다음 상태가 보이게 한다.
   - 괴물을 보여주지 않고 도망·비명·망했다는 반응부터 시작하면 안 된다.
   - 방·출구·계단·새 스테이지는 찾기·접근·진입·전환에 필요한 화면을 남긴다.
   - 무음이어도 발견 전 긴장, 방향 확인, 문을 여닫는 행동처럼 인과 기능이 있으면 유지한다.

3. 자연스러운 경계
   - 말 시작을 첫 음절에 붙여 자르지 않는다. 새 화면을 인지할 짧은 source-native handle을 장면별로 둔다.
   - 같은 공간에서 화면이 탁탁 튀는 jump cut을 피한다.
   - J/L cut, action cut, 시선·움직임 match, cutaway, 호흡 유지 중 실제 문제에 맞는 기법을 선택한다.
   - 기법을 정해진 개수나 비율로 억지 적용하지 않는다.
   - 영상과 음성 경계는 필요하면 다르게 쓸 수 있지만 인과를 왜곡하면 안 된다.

4. 사용자 승인
   - 구조 검사, decode, contact sheet, 내부 의미 검수는 사용자 승인이나 정상 속도 전체 재생을 대신하지 않는다.
   - 기술 검증을 통과했다는 이유로 current / approved / final로 승격하지 않는다.

## 정확히 승인된 보호 입력

다음 파일은 백룸 편집과 source 검증 목적으로 사용자가 제공·승인했다.

- inputs/2026-06-30 00-23-03.mp4
  - 원본 영상·음성
- inputs/2026-06-30 00-23-03.srt
  - 발화와 의미 경계 보조
- inputs/2026-06-30 00-23-03.full-edit-v18.xml
  - 과거 장면 위치와 Premiere CS6 구조 참고
  - 승인본이나 편집 기준본으로 승계하지 않는다.

inputs, outputs, extension/inputs, extension/outputs의 다른 항목은 정확한 경로와 목적 승인 없이 열거하거나 읽지 않는다.

## 구현과 호환성 상태

- Premiere CS6 XMEML v4 generator의 1-clip fixture는 사용자 Premiere import를 통과했다.
- extension/src/video_editing/premiere_xml.py와 extension/tests/test_video_editing_premiere_cs6.py에 아직 commit되지 않은 관련 변경이 있다.
- 관련 영상 편집 회귀 테스트는 직전 실행에서 48/48 통과했다.
- 이 사실은 새 전체 편집본의 import·재생·의미 품질을 보증하지 않는다.
- commit, push, current 승격은 수행하지 않았다.

## 사용 금지 결과

| artifact | 상태 | 확인된 원인 |
|---|---|---|
| outputs/07_edit_export/backrooms_single_sequence_v20_r8.xml | superseded / 사용자 의미 실패 | 오프닝 중간 절단, 원인 없는 도주, 층·방 전환 누락, 결과와 반응만 남긴 과압축 |
| outputs/07_edit_export/backrooms_single_sequence_v21_r1.xml | internal superseded | 안전실 문 행동과 후반 퍼즐 공간 이동이 다시 잘릴 위험을 내부 경계 검수에서 확인 |
| outputs/07_edit_export/backrooms_single_sequence_v21_r2.xml | rejected_user_direction / use-prohibited | 최대 7분 46초 원본 블록을 통째로 남긴 통편집. microcut·편집 기법·리듬 요구와 정반대 |

검증된 SHA-256:

- v20-r8: 9d7f196aa04b4086c6212ec01d9e8d87d08331981cb0f482a55af300c99198be
- v21-r1: 4e80f3224c86bf248d2f973593d978c558658d903c577d87fc7ff147d689d412
- v21-r2: 7be66b0ce8e242fcecdc2aaf6f49247328e1db7bf4b29f5f32d06f3c93c3ca3d

세 파일 모두 import·검수·후속 편집 기준으로 사용하지 않고 덮어쓰지 않는다.

## 실패 요약

| attempt | 결과와 확인된 원인 | 새 세션의 예방 조건 |
|---|---|---|
| v20-r8 | microcut을 과도하게 적용해 원인·공간 이동을 삭제했다. | 각 microbeat에 원인 anchor와 다음 상태를 명시한다. |
| v21-r1 | 일부 문 행동과 공간 이동이 경계에서 다시 누락될 위험이 있었다. | 완성 경계뿐 아니라 사건 내부의 상태 전이를 순차 검수한다. |
| v21-r2 | 반작용으로 긴 원본 블록을 유지해 실제 컷 편집을 포기했다. | 개연성은 anchor shot으로 보존하고, 사건 내부는 다시 microcut한다. |

이 표는 과거 세션의 원인 기록이며 새 세션의 활성 실패 횟수가 아니다.

## 활성 차단과 위험

- 기술 차단은 없다.
- 창작 차단: 촘촘함과 개연성을 동시에 만족하는 편집 문법이 아직 사용자에게 승인되지 않았다.
- 전체 XML을 먼저 만들면 같은 방향 실패를 영상 전체에 확산할 위험이 크다.
- v18이나 과거 XML을 current로 간주하면 안 된다.
- SRT만으로 컷을 결정하면 화면 행동과 공간 연결을 놓친다.
- contact sheet만으로 정상 속도 리듬과 음성 호흡을 승인하면 안 된다.

## 재개 checkpoint

먼저 대표 사건 하나에서 편집 문법을 증명한다. 전체 영상부터 다시 만들지 않는다.

대표 source 범위:

- 원본 36:22.380~38:23.500
- 기능: 괴물 발견 → 추격 → 막다른 길 → 안전실 발견·진입 → 문을 닫아 차단 → 다시 문을 열어 주변 확인 → 괴물이 가까이 있음을 확인하고 방으로 후퇴 → 문 규칙 이해
- 이 범위를 통째로 유지하라는 뜻이 아니다. 사건 anchor를 남기면서 내부를 촘촘하게 microcut할 교정 구간이다.
- 목표 시간은 정하지 않는다.

이 구간에서 반드시 증명할 것:

- 괴물이 화면이나 명확한 원인 단서로 먼저 제시된다.
- 도주 방향과 막다른 길 판단이 연결된다.
- 안전실을 발견하고 실제로 들어가는 화면이 남는다.
- 문을 여는 행동, 가까운 괴물 확인, 방으로 재진입하는 행동이 남는다.
- 착하게 살게요 같은 반복 발화는 감정 상승에 필요한 최소만 남긴다.
- 숨 고르기와 아몬드 물은 추격 직후 회복 기능이 있는 만큼만 남긴다.
- 문 닫으면 못 들어온다는 대사가 앞선 행동으로 뒷받침된다.
- 같은 공간의 불필요한 jump cut은 action/movement match나 필요한 J/L cut으로 완화한다.

## 승인 상태

- 보호 입력 세 파일의 위 목적 접근: 승인됨.
- 새 calibration XML 생성: 사용자가 백룸 편집 재개를 요청한 범위에서 허용됨.
- 전체 편집 확장: 대표 calibration의 사용자 방향 확인 뒤 진행.
- commit·push·삭제·current 승격: 승인되지 않음.
- 과거 결과 덮어쓰기: 금지.

## 첫 다음 행동

1. 시작 문서 3개와 현재 행동에 해당하는 영상 편집 규칙을 완전히 읽는다.
2. v20-r8, v21-r1, v21-r2를 import하거나 편집 입력으로 사용하지 않는다. v18은 장면 위치와 XML 구조 참고에만 쓴다.
3. 원본 MP4·SRT에서 36:22.380~38:23.500을 다시 보고, 유지할 사건 anchor와 제거할 microbeat를 frame 단위로 표기한다.
4. 고정 길이 없이 촘촘한 microcut, action cut, 필요한 J/L cut과 source-native handle을 적용한 단일-sequence calibration XML을 새 revision 이름으로 만든다.
5. 기존 protected output을 덮어쓰지 않는다. timeline JSON이나 별도 보고서는 만들지 않는다.
6. XML 구조, A/V 연속성, 선택 구간 decode, audio assembly, 모든 경계의 전후 화면과 발화 호흡을 검증한다.
7. 결과를 사용자에게 Premiere용 XML 링크로 전달하고 편집 방향 승인을 받는다.
8. 승인 전에는 전체 영상으로 확장하거나 current / approved / final로 승격하지 않는다.

## 다음 세션 시작 prompt

시작 문서 3개를 읽고 SESSION_HANDOFF.md만 현재 상태 정본으로 사용한다. 현재 승인 후보는 없다. v20-r8은 인과를 잘라낸 과압축 실패, v21-r1은 내부 경계 실패, v21-r2는 긴 원본 블록을 남긴 통편집 실패이므로 모두 사용 금지다. 원본 36:22.380~38:23.500의 괴물 발견·추격·안전실·문 차단 사건을 대표 교정 구간으로 삼아, 원인 anchor와 공간 연결은 남기고 무의미한 혼잣말·반복 반응·죽은 이동은 frame 단위로 제거한 촘촘한 microcut calibration XML을 먼저 만든다. 목표 시간이나 고정 컷 길이는 두지 않는다. 하드컷만 이어 붙이지 말고 action cut, 필요한 J/L cut, 움직임 match, 발화 전 source-native handle을 문제별로 적용한다. calibration을 기술 검증해 사용자에게 XML 링크로 전달하고, 방향 승인 전에는 전체 영상으로 확장하지 않는다. 이전 세션의 실패 횟수는 승계하지 않는다.
