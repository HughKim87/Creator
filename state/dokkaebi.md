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
