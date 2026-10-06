# 백룸 calibration-v3-r1 XML 작업 보고서

> **폐기·점수 철회:** 이 artifact는 사용자가 요구한 한 편의 연속 영상이 아니라 A/B/C를 세 개의 독립 sequence로 만들었고, 과거 편집본의 측정 길이를 목표처럼 잘못 해석한 설계에서 나왔다. 사용자 교정에 따라 `rejected_superseded`로 판정하며, 아래 85점과 `ready` 주장은 모두 철회한다. 후속 작업·Premiere import·current 승격에 사용하지 않는다. 대체 후보는 `outputs/07_edit_export/backrooms_single_sequence_v19_r2.xml`이다.

- 목적: v18 참고본과 r2 검증 근거를 사용해 덮어쓰지 않는 새 Premiere XML 후보를 만들고 검증 결과와 한계를 기록한다.
- 읽는 시점: `backrooms_calibration_v3_r1.xml`을 Premiere에 가져오거나 다음 편집 revision을 만들기 전.
- 책임: 작업 에이전트가 source lineage·구조·decode·의미 범위를 분리하고, 사용자가 실제 재생과 편집 방향을 승인한다.
- 상태: `rejected_superseded`. 아래 생성·검증 기록은 역사 근거이며 점수·ready·후속 지시는 무효다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, `extension/reports/2026-08-26_BACKROOM_EDITING_RESUME_PLAN.md`, `extension/reports/2026-08-26_BACKROOM_V18_DIAGNOSIS.md`.

## 1. 결과

새 XML 후보를 생성했다.

- 경로: `outputs/07_edit_export/backrooms_calibration_v3_r1.xml`
- SHA-256: `36FE2CD5E8E1F1562224ECB8F07DF0C2F7F5BC87CB7B964A7B9CEB06881018A1`
- 크기: 25,011 bytes
- 역할: A/B/C 대표 구간의 독립 Premiere sequence를 담은 calibration candidate
- parent 근거: v18의 이야기·장면 지도와 `integrated-calibration-v2-r2`의 안전한 연속 경계
- 상태: `candidate_technical_preflight_passed_pending_app_av_user`

원본 `inputs/2026-06-30 00-23-03.full-edit-v18.xml`은 수정하지 않았다. 새 XML은 v18 전체 편집본이나 완성본이 아니다.

## 2. runtime 복원

Creator manifest가 요구하는 Gyan FFmpeg 8.1.2 고정 package를 공식 versioned URL에서 복원했다.

- package: `ffmpeg-8.1.2-essentials_build.zip`
- archive bytes: 109,728,040
- archive SHA-256: `DB580001CAA24AC104C8CB856CD113A87B0A443F7BDF47D8C12B1D740584A2EC`
- 설치 위치: `extension/.runtime/ffmpeg/ffmpeg-8.1.2-essentials_build`
- 설치 특성: Git 제외 local capability

처음 확인한 rolling URL은 FFmpeg 9.0.1을 반환해 manifest hash와 달랐다. 이 build는 설치하지 않고, versioned 8.1.2 package로 교체했다.

manifest 검증 결과:

- file count: 45
- bytes: 318,594,126
- tree SHA-256: `a31ffe4dec39a70c17b56c540a290065890496b5f48b2e2beb8737fe8425e09a`
- `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe` critical SHA: 모두 일치
- version probe: 통과
- synthetic audio probe: 통과
- 선택적 whisper.cpp: absent, 비차단

## 3. source 검증

`inputs/2026-06-30 00-23-03.mp4`를 실제 probe했다.

| 항목 | 결과 |
|---|---|
| 컨테이너 길이 | 4924.066667초 |
| 파일 크기 | 3,799,793,770 bytes |
| 비트레이트 | 6,173,423 bps |
| 영상 | H.264, 1920×1080, 60fps |
| 음성 | AAC, 48kHz, stereo |

기존 handoff, v18 XML source duration, 현재 파일의 크기·길이·stream이 일치한다. 전체 파일 hash는 계산하지 않았다.

## 4. 편집 결정

### A — 첫 진입

- sequence: `CAL_V3R1_A_첫진입_연속`
- source frames: `19345–20607`
- source time: `322.416667–343.450000`
- duration: 1262 frames, 21.033333초

v18의 39.483초 첫 컷은 첫 진입 뒤 로딩·추가 공간 이동까지 이어져 훅으로 과도했다. r2의 첫 진입 사건을 유지하고 60fps frame 바깥쪽으로 약간 확장해 경계 음성을 덜 자르도록 했다.

### B — 규칙·허세 붕괴

- sequence: `CAL_V3R1_B_규칙허세붕괴_연속`
- source frames: `139993–141073`
- source time: `2333.216667–2351.216667`
- duration: 1080 frames, 18.000000초

v18의 28.750초 범위는 r2 전체와 추가 문맥을 포함했지만 감정 피크가 늦어질 수 있다. r2의 `첫 반응 → 도발 → 허세 → 공포 인정 → 도주` 범위를 유지했다.

### C — 적응 뒤 남은 공포

- sequence: `CAL_V3R1_C_적응공포잔존_연속`
- source frames: `260536–261281`
- source time: `4342.266667–4354.683333`
- duration: 745 frames, 12.416667초

v18은 같은 발화를 세 조각으로 나누며 0.350초를 두 번 생략했다. 실제 청취 근거 없이 호흡을 자르지 않도록 r2의 연속 source를 복원했다.

세 sequence는 서로 붙인 한 편집본이 아니다. 각 sequence 내부에는 영상 1개, stereo audio 2개가 있고 내부 하드컷은 없다.

## 5. 시각·음성 근거

- A contact sheet: 경고 화면·플레이어 전환·백룸 첫 공간 진입이 확인됐다. v18 뒤쪽의 로딩·추가 이동은 A 후보에서 제외했다.
- B contact sheet: 문·창문 너머 위협의 접근과 도주 공간이 확인됐다.
- C contact sheet: 어두운 파이프 통로를 계속 이동하며 화면 변화가 작아 음성 메시지의 연속성이 중요하다.
- A/B/C waveform: 세 범위 모두 음성·환경 신호가 존재한다.
- 기존 r2 VAD·무음·RMS 분석과 현재 frame 경계는 일치한다.

실제 음성을 귀로 연속 청취하거나 Premiere에서 재생하지는 않았다. faster-whisper와 model cache가 없으며, `video-to-srt` 규칙에 따라 승인 없이 설치하지 않았다. 기존 SRT·VAD·파형과 보수적인 연속 source 보존으로 대체했다.

## 6. 검증 결과

### XML artifact gate

- strict UTF-8: 통과
- NUL: 0
- XML parse: 통과
- XMEML version: 4
- project: `BACKROOM_CALIBRATION_V3_R1`
- sequence count: 3
- 각 sequence video/audio 구조: video 1, audio track 2×1
- clip IDs: 9개, 전부 unique
- link refs: 각 clip에서 video+stereo audio 3개 일치
- duration·start·end·in·out: 기대 frame과 일치
- source path: 현재 worktree MP4 한 개만 참조
- A/B/C video+audio 동시 decode: 모두 exit 0

### 관련 회귀 테스트

| 모듈 | 결과 |
|---|---:|
| `test_video_editing_premiere_cs6.py` | 8/8 통과 |
| `test_video_editing_workflow.py` | 18/18 통과 |
| `test_video_editing_subtitle.py` | 9/9 통과 |
| `test_local_runtime.py` | 6/6 통과 |
| `test_video_to_srt_runtime.py` | 3/3 통과 |
| 합계 | 44/44 통과 |

### 전체 Creator gate

`scripts/verify.py`는 도움말 옵션이 없어 `--help` 실행도 전체 검증을 시작했다. 중복 실행 하나를 종료한 뒤 실제 검증 하나를 유지했지만, `run_test_inventory.py`가 20분 이상 CPU를 계속 점유하며 완료되지 않아 중단했다.

이는 XML artifact나 관련 44개 테스트의 실패가 아니다. 전체 inventory 결과는 `not_completed_long_running`으로 기록하며 전체 gate 통과를 주장하지 않는다.

## 7. 자체 점수

이 점수는 완성 영상 품질 점수가 아니라 `calibration XML preflight readiness` 점수다.

| 평가 범위 | 배점 | 점수 | 근거 |
|---|---:|---:|---|
| source lineage | 15 | 15 | 상태 기록·XML·현재 media metadata 일치 |
| runtime 무결성 | 10 | 10 | tree·critical SHA·probe 통과 |
| XML 구조 무결성 | 20 | 20 | parse·sequence·link·frame gate 통과 |
| source media decode | 15 | 15 | 세 범위 영상+음성 동시 decode 통과 |
| 발화 경계 보호 | 15 | 15 | 내부 하드컷 0, 안전 경계를 frame 바깥쪽으로 확장 |
| 시각·의미 정합성 | 15 | 10 | frame·SRT·이야기 역할 확인, 연속 A/V 미청취 |
| Premiere import·재생 | 5 | 0 | `not_run` |
| 사용자 실제 방향 승인 | 5 | 0 | `not_run` |
| 합계 | 100 | 85 | 기술 preflight 후보, 승인본 아님 |

### 자체 판정

- 기술 preflight: `passed`
- source lineage: `passed`
- 구조·link·decode: `passed`
- 시각·의미 사전 검수: `scoped_pass`
- 실제 연속 A/V 청취: `not_run`
- Premiere import: `not_run`
- 사용자 승인: `not_run`
- 최종 상태: `candidate_ready_for_app_av_review`

85점은 다음 단계로 넘길 수 있는 XML 후보라는 뜻이며, 영상 완성도 85점이나 사용자 승인 85점을 뜻하지 않는다.

## 8. 폐기 판정

이 artifact에 대한 Premiere 검수·승격·후속 확장은 수행하지 않는다. 세 sequence 구조와 85점은 사용자 교정으로 무효이며, 후속 후보는 `outputs/07_edit_export/backrooms_single_sequence_v19_r2.xml`이다.
