# 백룸 영상 편집 현재 상태

- 목적: 컷편집 r11(고정)에서 에이전트가 직접 후편집을 진행하도록 재개한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md 다음.
- 책임: 에이전트는 후편집 산출물 제작·사전 검사, 사용자는 실제 재생 평가·채택을 소유한다.
- 상태: active. 컷편집 r11 사용자 고정(2026-10-06). 샘플 v6 사용자 승인("괜찮네") 후 전체 후편집 v1 제작·사전 검사 완료(2026-10-06), 사용자 재생 평가 대기.
- 관련 권위: extension/docs/domain/youtube/BACKROOM_POST_PRODUCTION_PLAN_20261006.md(후편집 설계), BACKROOM_EDIT_PLAN_20261005.md(이야기·장면·컷 원칙), BACKROOM_EDITING_EXECUTION_PLAN.md §0~§3(편집 원칙·9/24 스파인).
- handoff mode: same-workspace. extension/data/backroom-review-20260923/ 아래 미커밋 스크립트·JSON(s1work 포함)과 outputs의 XML에 의존한다.

## 현재 단계

- 컷편집 고정본: outputs/07_edit_export/backrooms_full_2026-10-05_r11.xml (21:37.9, 408컷, 60fps, 원본 inputs/2026-06-30 00-23-03.mp4 하나만 참조). 컷 위치·순서는 바꾸지 않는다. 사용자가 outputs 폴더를 정리해 r9·r10·r11만 남아 있다(r11만 사용).
- 후편집: 사용자가 "후편집을 에이전트가 직접 해 달라"고 지시했다. 설계 문서의 레이어(§3)와 작업 순서(§4)를 따른다. 처음 5분(r11 0:00–5:24)에 모든 레이어를 적용한 샘플을 먼저 만들어 확인받은 뒤 전체로 확장한다.
- 후편집 설계 핵심: 타겟 3층(영화 유입 라이트층·로어 팬·예능층). 긴장 구간은 효과 없이 게임 소리·고요 유지, 놀람 뒤와 쉬는 구간에만 강조 자막·코믹 효과음·짧은 줌, 전체 발화 자막, 레벨/엔티티/규칙 정보 자막, "한 시간만" 다짐 카운터, VHS 질감은 카드·전환에만, YouTube 오디오 보관함 음원, -14 LUFS 근처.

## 후편집 샘플 v2 (2026-10-06)

- 결과물: outputs/07_edit_export/backrooms_r11_post_sample_0000-0620_v2.mp4 (r11 0:00–6:20.28, 22817프레임, -14.3 LUFS / -1.7 dBTP), 같은 레이어를 얹은 Premiere용 outputs/07_edit_export/backrooms_full_r11_post_sample_0000-0620_v2.xml(V2 카드·V3 강조·V4 자막 PNG, A3 효과음, 시퀀스 마커; 기존 408컷 in/out/start 동일) + backrooms_r11_post_sample_v2_assets/(PNG·WAV·SRT). v1 MP4는 폐기본(자막 경계 겹침·도입부 게임 자막 겹침 수정 전).
- 큐시트·검사 기록: extension/data/backroom-review-20260923/postprod/post_sample_v2_cuesheet.json. 재현 스크립트: postprod/scripts/(작업 VM의 ~/work에서 실행하던 것을 복사; 경로는 VM 기준).
- 샘플 범위를 5:24가 아니라 6:20까지로 한 이유: 5:24 직후 말이 이어지고, Level 0 업적 화면(6:01 "Escape Level 0")과 Level 1 카드까지 한 장으로 보여야 카드 스타일 판단이 가능.
- 확정한 사실: 시작 구역 = Level 0(게임 업적 화면으로 확인). Level 1 정식 이름은 화면 미확인 → 카드에 번호만.
- 계획 대비 조정: 엔티티 카드를 2:08(사망 빌드업, 긴장 구간)이 아니라 1:44 본인 설명 "엔티티라는 존재입니다"에 맞춤. Level 0 카드(0:22) 추가.
- 음성 인식: 사용자 승인으로 작업 VM에 sherpa-onnx(pip --user) + whisper-turbo int8(~/asr, 작업 폴더 밖) 설치. 토큰 디코딩 버그(한글 다바이트 토큰 누락)를 hex 토큰 파일로 우회. r11 전체 276개 음성 구간 중 일부만 전사(postprod/asr_r11_partial.json) → 확장 전에 ~/work/asr.py를 이어서 돌린다(호출당 ~165초 예산, 재개 가능). VM 백그라운드 프로세스는 호출이 끝나면 죽으므로 긴 작업은 호출 단위로 쪼갠다.
- 미확인 대사 9곳은 큐시트 subtitles.uncertain에 기록(1:13 한 마디, 4:28 한 마디는 자막 생략).

## 샘플 v3 (2026-10-06, 사용자 지적 반영)

- 사용자 지적: 자막이 너무 작다. 유튜브는 대부분 모바일 시청 → 이전 크기의 3배 이상. 이 규칙을 전체 확장에도 그대로 적용한다.
- 반영: 자막 ASS 56→168(외곽선 9), 최대 2줄, 실측 폭 1760px 이하로 줄바꿈하고 긴 문장은 시간 분할. 강조 자막 160. 카드는 큰 자막과 겹치지 않도록 좌상단으로 옮기고 글자 약 1.5배.
- 결과물: outputs/07_edit_export/backrooms_r11_post_sample_0000-0620_v3.mp4, backrooms_full_r11_post_sample_0000-0620_v3.xml, backrooms_r11_post_sample_v3_assets/. v1·v2는 폐기본. 큐시트: postprod/post_sample_v3_cuesheet.json.

## 제목·썸네일 후보 (2026-10-06)

- outputs/08_thumbnail/: 썸네일 A(스마일러+한 시간만 하고 끌래요), B(노란 복도+별거 아니네 했다가), C(영화 vs 실제 분할), 제목 후보 4개(제목_썸네일_후보.md). 사용자가 C 구도 선택 → 보강안 C5(가운데 큰 "백룸") → 영화 타이틀 느낌 폰트 C6(금빛 세리프)·C7(붉은 호러 세리프)·C8(빈티지) 제시, 사용자 C7 확정. 제목 A/B 테스트 후보 3개는 제목_썸네일_후보.md. 폰트 VM ~/fonts(OFL). outputs/08_thumbnail/_to_delete/_tmp_base.jpg 는 임시 파일, 짝 제목 3번. 생성 스크립트 postprod/scripts/thumbs.py, thumbs_c.py.

## v3 (2026-10-06)

- 사용자 요청: 3:05 비명 구간에 펑펑 우는 밈. 페페_흑흑.jpg를 3:04.8–3:07.0 오른쪽에 추가(M35). 해당 청크만 재렌더 → outputs/07_edit_export/backrooms_r11_post_full_v3.mp4 (최신, 그 외 v2와 동일).

## 자막 싱크 개선 v2 (2026-10-06)

- 사용자 지적: 전체적으로 자막 싱크가 어긋남. 승인(모델 설치 포함) 후 전체 범위 재정렬.
- 결과물: outputs/07_edit_export/backrooms_r11_post_full_v2.mp4 (자막 시간만 변경, 그 외 v1과 동일). 보고: postprod/sync_v2_report.json.
- 방법: VM ~/asr에 sherpa-onnx Korean zipformer(글자 단위 시간) 추가 → 자막 이벤트를 글자 시간에 정렬 → Whisper로 바뀐 창을 독립 재인식해 이전보다 나쁘면 되돌림. 382개 중 254개 이동(중앙값 0.29초 앞당김, 1초 넘게 25개), 바뀐 자막의 Whisper 일치도 0.74→0.84, 나빠진 것 0.
- 자막 정본: ~/work/pp/subs_synced.json (make_ass.py가 읽음).

## 전체 후편집 v1 (2026-10-06)

- 결과물: outputs/07_edit_export/backrooms_r11_post_full_v1.mp4 (21:37.9, 77874프레임, -14.3 LUFS). 큐시트·검사: postprod/post_full_v1_cuesheet.json. 스크립트: postprod/scripts/ (VM ~/work/pp에서 실행; build_subs→reflow→make_ass, make_assets→make_cardclips, make_memeclips, make_audio, run_chunks.sh → concat).
- 추가 내용(6:20 이후): 자막 265개 이벤트(전체 382), 카드 13개(COOP OPEN, 문 규칙, 눈 규칙, 열쇠 4개, NEXT LEVEL×3, 스마일러), 강조 자막 7개, 밈 20개, "한 시간만" 카운터 6회(마지막 1:16:38). 6:12 Level 1 카드에 Habitable Zone 추가(업적 화면 확인).
- 전사: ~/work/asr.json(VAD 276구간) + win.json(클립 단위 재인식). 불확실 대사는 큐시트 subtitles.uncertain.
- 미착수: 썸네일·제목·챕터·엔드스크린(설계 §3.6), 전체 Premiere XML 레이어(현재 v3 XML만).

## 샘플 v6 (2026-10-06, 밈·강조 자막)

- 사용자 결정: 밈은 한국 유튜브에서 쓰는 것만, 사용자 밈 폴더 D:\외장하드백업\개인자료\유튜브_김실버\밈 (세션에 읽기 연결)에서 고른다. 자체 제작 그래픽은 쓰지 않는다.
- 사용자 규칙: 자막은 그대로 두고 밈만 추가 / 이미지마다 크기 조절, 최대 화면 가로·세로 절반 / 영상 내용을 가리지 않게 좌·우 / 참고 이미지 빨간 영역 크기·위치(약 35%×35%, 세로 중앙). 강조 텍스트(적응 완료·튜토리얼 등)는 일반 자막보다 크고 다른 폰트.
- 반영: 밈 12개(위치·출처는 postprod/post_sample_v6_cuesheet.json), 680×370 상자, 좌(515,505)/우(1440,505) 중심. 강조 자막 Black Han Sans(OFL, VM ~/fonts) 230.
- 렌더 주의: 알파 오버레이는 overlay format=yuv420으로 고정해야 RGB 왕복 변환으로 화면 전체가 미세하게 바뀌지 않는다(v5에서 발견).
- 결과물: outputs/07_edit_export/backrooms_r11_post_sample_0000-0620_v6.mp4. v4·v5는 미전달 폐기본. XML은 이번에 갱신하지 않음(v3 XML에 밈 레이어 없음).

## 직전 게이트

- 판정: pass (기술·구조 범위). r11 XML의 408개 video clip in/out/start가 candidate와 일치, 원본 sha256·size 렌더 전후 일치. 모든 내부 경계 822곳을 목소리 기준·약한 말끝 기준으로 검사. 사용자 재생 평가: r8 처음 5분 positive, 이후 지적(출구 찾기, 스테이지 전환, 말끝 절단, 마무리 중복)을 r9~r11에서 반영했고 사용자가 r11 고정을 지시했다.

## 승인 상태

- 위임됨: 후편집 실행(에이전트가 직접), 컷편집 r11 고정.
- 미결: 설계 문서 §5 선택 항목(자막 범위, 효과 강도, 오프닝, 레벨 카드 스타일). 사용자가 직접 해 달라고 했으므로 각 항목의 "권장"안으로 진행하고, 5분 샘플에서 확인받는다.
- 승인 필요: 음성 인식 도구(Whisper 계열) 설치. Core 정책상 설치는 항상 사용자 승인. commit·push·삭제·외부 전송·업로드·Core 변경은 범위 밖.

## 차단

- 정확한 전체 자막에 음성 인식이 필요하다. 사용자 컴퓨터의 작업 VM(device_bash, Linux, 2 CPU, 3GB RAM)에는 Whisper가 없고, 예전 Windows용 whisper.cpp medium(extension/.runtime 쪽)은 이 VM에서 실행할 수 없다. 재시작 조건: 설치 승인 또는 다른 전사 방법 결정. 기존 부분 전사(extension/data/backroom-review-20260923/full-individual-*.wav.json, 경계 ±7초씩)는 보조로만 쓸 수 있다.

## 알려진 위험

- 에이전트는 영상을 재생하거나 소리를 들을 수 없다. 모든 경계 검사는 음성 대역(250–3500Hz) RMS와 정지 화면 확인이다. 원본 SRT는 구간에 따라 수 초 어긋나고 오인식이 많다.
- 렌더는 Linux 스크립트로 한다(extension/src/video_editing/delivery.py의 Windows 전용 source lock 대신 렌더 전후 hash·size 검사). 출력은 덮어쓰기 금지(O_EXCL), 에이전트는 파일 삭제 권한이 없다 → 새 판은 새 이름으로.
- 채팅의 computer:// 폴더 링크는 이 앱에서 열리지 않는다. 경로는 Win+R 붙여넣기용 텍스트로 안내한다.
- FCP7 XML의 텍스트·모션·이미지 트랙이 Premiere CS6 프로필에서 어디까지 가져와지는지 미확인. 후편집을 XML 레이어로 줄지, ffmpeg로 최종 MP4를 직접 렌더할지 5분 샘플에서 결정한다(아래 1번).

## 사용자 작업 원칙 (반복 실수 방지)

- 이미 정한 설계·지시를 다시 묻지 않는다. 장별 확인을 반복 요구하지 않는다. 사용자를 결함 찾는 첫 검수자로 쓰지 않는다 — 결과를 내기 전에 에이전트가 전수 검사한다(대사 연결, 말끝, 무음, 스테이지 전환).
- 대사는 앞뒤가 이어지고 개연성이 있어야 한다. 맥락 없는 대사로 시작하지 않는다.
- 이유 없는 무음은 제거하되, 화면을 보여줄 이유가 있으면 유지한다.
- 장면·스테이지 전환에는 어떻게 거기까지 갔는지 최소 연결을 남긴다.
- 목표 길이를 먼저 정하지 않는다. 9/24 스파인(실행계획 §3)이 최상위 이야기 설계다.

## 활성 입력과 상태 정본

- 입력: inputs/2026-06-30 00-23-03.mp4, inputs/2026-06-30 00-23-03.srt.
- r11 구간표: extension/data/backroom-review-20260923/s1work/r11_clips.json. 생성: full_r11_assemble.py → full_r11_render.py. 상태: full11-candidate-v2.json, editorial-state-20261005-full-r11.json, full11-analysis-map.json(r11 시각 ↔ 원본 frame ↔ 장면 기능).
- 경계 도구: s1work/soft_edges.py(약한 말끝), s1work/insert_snap.py(구간 삽입+경계 보정), s1work/gap_scan.py(편집 밖 로딩 화면 탐지), s1work/sil_*.py(무음 측정·판정). 무음 판정 근거: s1work/silences.json, silence_decisions.json, sheet_00–15.jpg.
- r11 주요 위치(후편집 큐 기준): 0:00 인게임 도입, 2:08 첫 사망, 5:01 NPC 자기암시, 5:24 출구 찾기, 6:12 Level 1 도착, 6:54 "한 시간만", 8:17 승인 대표본(추격·문 규칙·도발), 11:46 살아있는 공략, 12:48 이번 스테이지만, 13:37 엘리베이터 새 층, 14:14 STAY IN THE LIGHT, 14:22 한 스테이지만 더, 14:45 혼자 생쇼, 16:43 첫 Smiler, 17:54 배관 통로, 18:57 출구 지나침, 19:45 EAST SUBSTATION, 21:25 마무리, 21:34 "너무 긴장을 했어"(검은 화면 종료).

## 첫 다음 행동

0. 사용자의 전체 v3 재생 평가를 받는다. 지적은 해당 청크만 재렌더해 v2로(새 이름).
1. (완료) 사용자의 v2 샘플 재생 평가를 받는다(카드 스타일, 강조 자막 밀도, 효과음 톤, 자막 정확도, MP4 vs XML 출력 방식). 지적은 v3로 반영(새 이름).
2. 승인되면 ~/work/asr.py로 나머지 전사를 끝내고, 같은 규칙으로 6:20–21:37.9 큐시트(§3.2·§3.3 위치, "한 시간만" 카운터 PNG 포함)를 만든 뒤 전체 렌더한다.
3. 엔드스크린·썸네일 후보·챕터 문안(§3.6)은 전체 확장 뒤.
