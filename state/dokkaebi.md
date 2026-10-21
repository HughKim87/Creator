# Creator dokkaebi 워크트리 상태

- 목적: 촬영 원본 "도깨비의 세계 오픈런 방송"의 영상 편집을 main과 분리된 워크트리에서 진행한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md 뒤.
- 책임: 에이전트가 이 브랜치의 편집 상태를 유지하고 사용자가 방향·결과를 승인한다.
- 상태: active — 컷 r20 + 후편집 post-r6 사용자 승인(2026-10-11 '이걸로 쓰면 되겠어'). workflow 개선 v4 중 꼭 필요한 항목 반영 완료(2026-10-11). 남은 일: 썸네일 시안, 보류된 개선 항목 결정.
- handoff mode: same-workspace. 원본과 산출물이 Git 제외 경로(inputs/, extension/outputs/)에 있다.
- 이력: 끝난 판(calibration r1 ~ 컷 r20·후편집 r6)의 결정 근거·도구 사용법은 [state/history/dokkaebi.md](history/dokkaebi.md)에 원문 그대로 있다. 과거 판을 다시 고칠 때만 연다.
- 관련 권위: extension/docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md, PROJECT_RULES.md의 영상 편집 rule route.

## 현재 단계

- 워크트리: D:/AI Agent/GitHub/Creator-dokkaebi, 브랜치 claude/dokkaebi (기준 main bc341ae). core submodule 3e0ebe7.
- 원본(읽기 전용): inputs/2026-10-08 11-01-06.mp4 — 12,728,538,341 bytes, sha256 9e0347164e9c303b74a2eb95ff499ff249fbde74777608f0fb446e7b05b43e16, 988,914 frames(60fps), 1920×1080 h264, AAC 48k stereo. 자막 원본 inputs/2026-10-08 11-01-06.srt.
- 확정 산출물(바꾸지 않음):
  - 컷: extension/outputs/dokkaebi-edit/dokkaebi-full-r20.xml (sha256 be417d5e40f74e643325c92ee930366f348d008b08ce9e27cbfc98dcd2008696, 55,134프레임=15분 18.9초, 366클립).
  - 후편집: extension/outputs/dokkaebi-edit/dokkaebi-post-r6.xml (sha256 a2a5fc20eff5e6de3b8b2aad323436dc7526a933363eed9f997bb7ffa7348923) + dokkaebi-post-r6-assets/(PNG 930·WAV 4). 자막 430.
  - 다음 판 이름: 컷 r21(plan_r21), 후편집 post-r7.
- 산출물 계약: Premiere Pro CS6용 xmeml v4 XML, 1920×1080·60fps, 출력 extension/outputs/. MP4 금지(사용자 요청 전), 파트 분할 금지.
- 작업 폴더: extension/outputs/dokkaebi-work/ (body/ = 컷 도구, post/ = 후편집 도구·cuesheet_r2.json·build_post.py·verify_post.py·subs_r20.py). 사용법은 이력 파일 「컷 r20 + 전체 후편집 r6」·「후편집 진행」·「빠른 재개 요약」.
- 설계 정본: extension/outputs/dokkaebi-edit/dokkaebi-edit-design-A.md(방향 A), post/post-design-r1.md(후편집).
- workflow 개선: 설계 v4(extension/docs/domain/youtube/VIDEO_EDITING_IMPROVEMENT_DESIGN_2026-10.md) §14의 '꼭 필요' 항목 반영·커밋 완료. '보류' 항목은 사용자 결정 대기.

## 새 작업: 리뷰 영상 "지금 시작해도 괜찮을까?" (2026-10-13 시작)

- 요청(사용자 2026-10-13): 촬영 대본에 맞춰 원본 플레이 화면으로 새 영상을 만든다. 첫날 편집(r20·post-r6)과 별개의 새 영상이며 이 워크트리에서 작업한다.
- 입력(사용자 지정): inputs/도깨비의세계_촬영대본.md(v3), inputs/도깨비의세계_팩트체크와교정.md, 원본 mp4. 자막은 whisper 원본 대신 이전 세션 교정본 extension/outputs/dokkaebi-asr/2026-10-08 11-01-06.corrected-full.srt를 쓴다(사용자 지시).
- 사용자 결정(2026-10-13): 나레이션은 TTS 임시 → 나중에 녹음본으로 교체. 원본 진행자 목소리 인서트 없음(원본 오디오는 진행자 목소리가 섞여 있어 타임라인에 넣지 않음). 산출물은 CS6 XML만.
- 산출물 r1(검토 전): extension/outputs/dokkaebi-review/dokkaebi-review-r1.xml (sha256 890a8fa7…, 39,822프레임=11분 3.7초, 영상 119클립 + 나레이션 1개) + dokkaebi-review-r1-assets/narration-tts-r1.wav(48k 스테레오, PCM md5 c3ca71bd… 클라우드 원본과 일치).
- 작업 폴더 extension/outputs/dokkaebi-review-work/: scene-map-r1.md(매칭표), edl_r1.txt(문단별 원본 시작/최대 길이), plan_r1.json(클립), narration_r1.json(문단·줄 시각), narration-tts-r1.flac, frames_r1/(화면 확인 시트), sheets.py·check_dark.py.
- TTS: 클라우드에서 sherpa-onnx vits-mimic3 ko_KO-kss_low(오프라인, 대본 외부 전송 없음). 음질 낮음(기계음·일부 발음 오류) — 길이 맞춤용 임시. 숫자·2D/3D는 읽기용으로 바꿔 넣음.
- 검사: 화면 시트로 후보 57곳 확인(창 모드·작업표시줄 구간 00:06~00:09, 검은 로딩 화면 제외). 클립마다 3프레임 밝기 검사 → 검은/단색 0(어두운 UI 5프레임은 내용 있음). XML 파싱·연속성(빈틈·겹침 0) 확인. 원본 크기 변동 없음. not_run: Premiere CS6 가져오기, 정상 속도 시청.
- 미포함: 자막·정보 카드(패치·오프라인 모드·선물 기간 등 화면 근거 없는 문단), BGM.
- r2(2026-10-13, 사용자: TTS가 여자 목소리라 가이드로 못 씀 / 정보 카드는 팩트체크 후 이미지로 원본 위에): extension/outputs/dokkaebi-review/dokkaebi-review-r2.xml (sha256 abb0e55e…) + dokkaebi-review-r2-assets/(narration-male-r2.wav PCM md5 fc46adf3…, 카드 PNG 168). 영상 V1은 r1과 같음.
  - 목소리: r1 TTS를 WORLD(pyworld)로 음높이 ×0.42(중앙값 약 266→110Hz)·포먼트 ×0.82 변환. 문단 시각 그대로라 장면 길이 불변. 남성 한국어 오프라인 모델은 접근 가능한 곳에 없음(huggingface·외부 TTS 차단). 청취 not_run.
  - 정보 카드 8개(V2, 왼쪽 위, post-r6 카드 양식·맑은 고딕 Bold, 12프레임 등장/8프레임 퇴장): 3.7 도술 초기화, 5.4 오프라인 모드, 5.7 같은 서버, 5.8 경쟁 콘텐츠, 6.2 의복·탈것, 6.3 유료 요소, 7.5 10/10 점검, 7.7 특별 선물. 근거: 공식 커뮤니티 notice 12257(10/10 점검), event 10676(특별 선물 ~10/21 08:00), notice 1132(라이브 시연회 Q&A), notice 12167(10/9 라이브 — 도술 초기화 바로 제공 어려움) — 2026-10-13 Chrome으로 직접 읽음. 10/12·10/13 점검 공지는 대본 범위 밖이라 반영 안 함.
  - 검사: 카드 8개를 실제 배경 프레임에 합성해 확인, 카드 겹침 0, XML pathurl 170개 전부 존재, 원본 크기 불변. not_run: CS6 가져오기·시청.
- r3(2026-10-13, 사용자: r2 목소리 부자연 → 클로바더빙으로 직접 만든 나레이션 도깨비.mp3 제공. 클로바더빙은 Chrome 도구 안전 제한으로 사이트 조작 불가 → 1,000자 이하 대본 6개(dokkaebi-review-work/clova1000/) 제공): dokkaebi-review/dokkaebi-review-r3.xml (sha256 8c32023a…, 34,066프레임=9분 27.8초, 영상 120클립 + 카드 168 + 나레이션) + dokkaebi-review-r3-assets/(narration-clova-r3.wav, 카드 PNG는 r2와 동일 복사).
  - 정렬: 무음 기준 277구간을 sherpa-onnx 한국어 zipformer로 받아써 대본과 글자 대응(일치 91.5%), 문단 순서 역전 0, 낮은 일치 1줄(2.3 첫 줄 37%, 앞뒤 줄로 위치 확인). 작업 자료 dokkaebi-review-work/r3/.
  - 장면 검사: 8.6 끝이 검은 화면(1:40:18) → 02:01:30 장면으로 나눔. 재검사: 검은/단색 0(어두운 UI 4프레임은 내용 있음). XML pathurl 170 전부 존재. not_run: CS6 가져오기·시청.
- 녹음본 자막(2026-10-13, 사용자: 대본을 새로 쓰고 직접 녹음함 — inputs/2026-10-13 15-00-55.mp4, 28분 23초. 대본은 채팅으로 받아 rec13/script_v4_user.txt에 저장, 참고용으로만 사용): dokkaebi-review-work/rec13/ 에 raw.srt(152구간) · corrected.srt(485큐, 22자 이하) · 자막추출_메모.md(교정 25곳, 불확실 5곳, 다시 말한 곳 11곳, 지운 환각 8곳).
  - 방법: VM faster-whisper 1.2.1(pip --user, 사용자 승인) + large-v3-turbo(Creator-ainotebook 모델 폴더 접근 승인), 무음 지점 70구간, beam 5. 녹음은 목소리만(무음 -100dB), 게임 소리 없음.
  - 불확실 5곳 사용자 확인 완료(솔: 인챈트·들어오면·영웅 아이템 도안이·낙화의 전장·점령당한 모두 현재 표기 맞음) → corrected.srt 확정. 이전 리뷰 영상 r1~r3는 옛 대본 기준이라 이 녹음과 맞지 않음.
- 녹음본 컷 r1(2026-10-13, 사용자: 버벅임·중복 제외 컷편집, 애매한 곳 먼저 질문 → 8개 질문 답변 받음): dokkaebi-review/dokkaebi-voice-cut-r1.xml(15:47.0, V1/A1·A2 266클립 + V2 보이스오버 5) + dokkaebi-voice-cut-r1.srt(편집 시간 기준). 결정·근거·검사는 rec13/컷편집_분석_r1.md. 원본 inputs/2026-10-13 15-00-55.mp4 sha256 4afafdfc…, 1,313,957,150 bytes, 102,193프레임.
  - r2(2026-10-13): V010 중복 등 겹침 8곳 수정 + 정보 이미지 18개(V3) → dokkaebi-voice-cut-r2.xml/.srt/-assets. 상세는 rec13/컷편집_분석_r1.md 「r2」. 신수 능력치 발화가 공식 Q&A와 다름(사용자 확인 대기). not_run: CS6 가져오기·사람 시청. 다음 판 voice-cut-r3. → r3(2026-10-13): 첫날 방송 원본 장면 41개 보이스오버 추가, dokkaebi-voice-cut-r3.xml/.srt. 다음 판 voice-cut-r4. → r4(2026-10-13): 사용자 기준 "참고 화면 사이 5초 이하 간격은 앞 장면을 늘려 메움" 적용, dokkaebi-voice-cut-r4.xml/.srt. 다음 판 voice-cut-r6.
- 첫 다음 행동: 사용자 CS6 가져오기·시청 피드백 → 장면 교체(edl 수정 후 plan.py·build_xml.py 재실행, r2 이름). 녹음본이 오면 narration json 대신 녹음 길이로 문단 시각을 다시 잡는다.

## 확정 결정

- 방향 A "첫날 플레이 종합 리뷰", 도입 r10 확정, 게임 방송 프로필(VIDEO_EDITING_PROFILES.md, 2026-10-11 갱신값).
- 편집 문법 10개(개연성 우선, 같은 불평 원인 1회+결론 1회, 미회수·의미 없는 말 삭제, 말 실수는 무음에서 잘라 이음, 과도한 요약 금지, 다른 대상 장면 끼우지 않기, XML만·섹션 끝은 무음, A→B→A 금지, 리뷰 중심·잡담 살짝, 사실과 다른 발언은 빼고 필요하면 자막 보충). 상세는 이력 파일 「도입부 r10 (확정)」.
- '무과금' 표현 금지(1,100원 결제 있음). 버그·밸런스·과금 발언은 진행자 반응으로만. 햄버거 관련 전부 제외. 원본에 없는 감정·사건을 만들지 않음.
- 후편집 사용자 기준: 자막 검은 배경+흰 글씨 한 가지, 강조 줄은 자막 대신 강조 글자, 밈은 소리·화면·맥락·이미지 뜻 확인 뒤, 카드 왼쪽 위, 연출은 깔끔하게 한 번만, '아…씨' 류 추임새 자막 제외, 원본 2초 넘게 점프하는 컷에서 자막 줄 나눔.

## 세션 시작 환경

- 폴더 접근(새 세션마다 다시 요청): Creator-dokkaebi, 밈 폴더 D:/외장하드백업/개인자료/유튜브_김실버/밈(VM $HOME/mnt/밈), C:/Windows/Fonts(malgunbd.ttf, BlackHanSans-Regular.ttf), Creator-ainotebook 모델 폴더 extension/.runtime/models/whisper/large-v3-turbo(VM $HOME/mnt/large-v3-turbo).
- 패키지: 받아쓰기에는 VM에 faster-whisper(pip --user, 사용자 승인) 필요.
- VM 제약: 2코어·RAM 3GB, 호출당 180초, 백그라운드 불가. 받아쓰기 beam 5는 창당 약 15초(호출당 약 8창). 1920×1080 RGBA를 많이 메모리에 들면 강제 종료.
- git(VM): GIT_DIR=$HOME/mnt/Creator/.git/worktrees/Creator-dokkaebi, GIT_WORK_TREE=$HOME/mnt/Creator-dokkaebi, 작성자 HughKim87 <sangwooggu@gmail.com>. .git이 Creator 폴더에 있으므로 Creator 폴더 삭제 권한이 없으면 커밋 뒤 .lock·tmp_obj가 남는다 — 커밋 전에 권한을 받거나 남은 lock을 정리한다.
- 테스트(VM): `PYTHONPATH=extension/src:extension/tests python3 -m unittest <모듈>`. pytest 없음. 일부 테스트는 extension/work/에 임시 폴더를 만들고 삭제 권한이 없으면 남긴다.

## 직전 게이트

- 2026-10-11 workflow 개선(꼭 필요 항목): 규칙 R03·R06·R08·R09·R19·R21 문장 추가와 TC34~TC39, 게임 방송 프로필 갱신, CS6 XML 효과 호환표 신설, CAND08 갱신 → 커밋 59d4240. test_extension_rule_routing·test_worktree_state_files·test_video_editing_workflow 34건 통과. 전체 extension 테스트의 나머지 실패(삭제 권한·PowerShell·schema/node 환경)는 문서 변경과 무관하며 수정 전과 같은 종류.
- 2026-10-11 후편집 post-r6: verify_post(CUT=r20) 통과, 사용자 사용 확정. CS6 가져오기·청취는 사용자 확인.

## 승인 상태

- 승인: 컷 r20·후편집 post-r6 사용(2026-10-11), 방향 A, 산출물 형식(CS6 XML), 자막 교정 결과, 워크트리 생성, workflow 개선 꼭 필요 항목 진행과 단계별 로컬 커밋(2026-10-11).
- 미승인: 개선 설계 §14 보류 항목(N1 writer 비Windows 모드, N5·N6·P6 도구, P2 별도 규칙, N7 PROJECT_RULES 문안, P7, 후보 문서 정리), push·main 병합.

## 차단

- 없음.

## 알려진 위험

- 원본 보호: Premiere CS6 '가져올 때 파일에 XMP ID 쓰기'가 켜져 있으면 XML 가져올 때 원본 hash가 바뀐다(사용자에게 끄기 권고).
- R04는 mandatory lock 없는 platform에서 fail closed를 요구하지만 VM 산출물은 전후 hash·size + O_EXCL 우회(xml_split.py pre/gen/post)로 만들었다. 규칙 예외(N1)는 보류 상태. '안 된다'고 판단하기 전에 이 선례를 확인한다.
- Creator-ainotebook 모델 폴더 안 자기 참조 심볼릭 링크 `large-v3-turbo`는 사용자가 지워야 한다(2026-10-10 실수).
- 짧은(0.5초 미만) 조각 단독 전사는 환각이 나므로 근거로 쓰지 않는다.
- NPC 음성과 진행자 발화가 겹치는 mixed 25큐는 오디오 경계 위험.

## 첫 다음 행동

1. 썸네일 시안 2~3개(후편집 확정 뒤, 사용자 범위 확인). 도깨비 확정 산출물은 바꾸지 않는다.
2. 개선 설계 §14 보류 항목은 사용자가 원할 때만 별도 진행. 다음 영상 편집 시작 전이라면 N5(무음 컷 첫소리 검사)·N6(바뀐 경계 화면 시트)가 우선 후보.

## 다음 세션 시작 prompt

D:/AI Agent/GitHub/Creator-dokkaebi에서 도깨비의 세계 썸네일 시안을 만들어줘. 시작 3문서를 읽은 뒤 state/dokkaebi.md의 「첫 다음 행동」부터. 컷 r20·후편집 post-r6은 확정이며 바꾸지 않는다.

- 2026-10-13: voice-cut-r5 생성(C1~C8 반영, 15:31.5). CS6 임포트 확인 대기. 미답: 24:43 '신수 능력치 없음' 발언 vs 공식 Q&A.
- 2026-10-13: voice-cut-r6 생성(V027 중복 제거, 앞뒤 무음 44곳 정리, 15:04.3). 다음 버전명 voice-cut-r7.
- 2026-10-13: 사용자 직접 편집본(14:49.1) 자막 dokkaebi-user-edit.srt 생성. 이후 편집 기준은 사용자 편집본.

- 2026-10-14: 새 영상 inputs/음성촬영영상.mp4(도술 덱 추천, 8:00) 자막 추출·컷 r1 → extension/outputs/dokkaebi-deck/dokkaebi-deck-cut-r1.xml/.srt (3:45.2). 상세 rec14/컷편집_메모_r1.md. VM faster-whisper는 /tmp/pylib에 설치(세션 디스크 /sessions 가득 참). 다음 판 deck-cut-r2. not_run: CS6 가져오기·시청.
- 2026-10-14: deck-cut-r2 (3:01.5, 군더더기 C1~C6 + 말끝 늘어짐 5곳). 원본이 CS6 XMP 쓰기로 sha256 ef744666…로 바뀜(내용 동일). 다음 판 deck-cut-r3.
- 2026-10-14: deck-cut-r3 = 사용자 Premiere 편집본(앞 1:34 구간) + r2 결정(뒤쪽) 병합, +3dB 유지, 3:01.4. 다음 판 deck-cut-r4.
- 2026-10-14: deck-cut-r4 = r3에서 Gain 필터만 제거(CS6가 +6dB 초과로 클램프 경고). 다음 판 deck-cut-r5.
- 2026-10-14: 도술 덱 영상 제목 4안·썸네일 시안 3개(A 비교·B 덱·C 숫자) → extension/outputs/dokkaebi-deck/thumbnail/. 사용자 선택 대기.
- 2026-10-14: 제목 확정 "덱만 바꿨는데 딜 20% 올랐습니다 | 도깨비의세계 7초 암습 덱". 썸네일 선택 대기.
- 2026-10-14: deck-cut-r4.srt 자막 줄 나눔 개선(71큐, 줄당 23자 이하) + 대본 txt.
