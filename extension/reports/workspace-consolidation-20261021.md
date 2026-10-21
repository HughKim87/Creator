# Creator 통합·정리 판정

- 목적: 제거될 브랜치에 재사용 개선이 남지 않도록 출처별 흡수 판정과 자료 처분 대상을 기록한다.
- 읽는 시점: 단일 workspace 전환 검토와 기존 자료·worktree 처분 승인 시.
- 책임: main 유지보수 세션이 실제 파일·검사를 갱신하고 사용자가 자료 처분을 승인한다.
- 상태: 개선 통합과 단일 workspace 코드 구현 완료. 최종본·필수 자산·공용 도구 이전, 전체 복구 검증과 기존 worktree 퇴역 완료.
- 관련 권위: `../docs/WORKSPACE.md`, 루트 `PROJECT_RULES.md`.

## 개선사항 출처 대조

태그는 원래 Git 이력을 고정한다. 아래 판정은 현재 main의 기능 소유자를 기준으로 하며 과거 브랜치 전체를 덮어쓰지 않는다. 개인 설정·원본·출력은 공통 코드에 포함하지 않는다.

| 출처 | 확인 범위와 판정 | main 소유자 |
|---|---|---|
| `before-codex-wardogs` | 공통 조상 이후 공통 코드·규칙 변경 없음. 썸네일 제작 자료는 영상별 데이터이며 job·archive에 보존 | 공통 기능 추가 불필요; 최종 썸네일을 wardogs job에 보존 |
| `before-codex-ainotebook` | merge-base 이후 최종 차이는 handoff·전용 상태뿐. `7c331a9`의 연속 제작·브라우저 실행·내용 검수 개선은 main에 반영돼 있으며 job validator는 bytes 동일 | `.agents/skills/`의 제작 7종·browser launcher·job validator·session 개선 검사 |
| `before-codex-backroom-video` | merge-base 이후 차이는 상태 정책의 과거 수정·영상별 계획. `84adf0a`, `9f79ca3`, `fbfb8f3`, `eb08649`의 편집·검수 개선은 `9d23fd1` 등에서 흡수됐고 video_editing 구현은 bytes 동일 | `extension/src/video_editing/`, 편집 규칙과 workflow 계약. 최신 main 정책을 유지 |
| `before-claude-dokkaebi` | 시청자 질문·분석, 재전사·말실수, 무음 판단, 효과 검증, 후편집 자막·밈, 후속 정정 보존은 main의 R03/R04/R05/R07/R09/R19/R21 및 TC34~TC40에 반영. TC 번호는 main 정본 유지 | `extension/rules/` 및 관련 회귀 |
| 같은 도깨비 출처의 잔여 개선 | CS6 효과 호환 관측과 상세 스타일 선택이 main에 빠져 있어 흡수. 관측 사실과 새 검증을 구분하고 단일 영상 선택을 새 영상의 강제값으로 일반화하지 않음 | `PREMIERE_CS6_XML_COMPAT.md`, `VIDEO_EDITING_PROFILES.md`의 선택적 변형 및 CAND08 링크 |
| `before-codex-TRYALLGAME` | 공통 변경은 작업 폴더 ignore. 특정 영상 이름을 추가하는 방식 대신 새 jobs 전체를 Git 제외하는 구조로 대체 | `.gitignore`, `creator_workspace.py` |
| `before-codex-24HReplier` | 앱 전체·생성/판정 근거 일치 개선과 검사·probe 구현을 흡수. `e9587cc`, `cdc3ae7`, `d649c9d`의 코드를 후속 tip `6764ae7`에서 가져옴. 실서비스 실험은 자동 실행하지 않음 | `extension/src/replier/`, `extension/tests/replier_*`, `test_replier.py`, Build/Install/Start 스크립트와 model manifest |

도깨비의 옛 workflow 문구를 통째로 가져오면 main의 국소 보정 위임·시청자 분석 범위가 되돌아간다. 백룸·ainotebook의 옛 파일로 덮어쓰면 최신 TTS·제목·공개 시간·Claude 개선이 삭제된다. 이들 차이는 개선 누락이 아닌 main 후속 발전으로 판정하고 보존한다.

## 검증

- 24HReplier Python 합성 API 12개 pass. 로컬 loopback만 사용했고 실제 서비스 호출 없음.
- Windows C# 앱 빌드 pass. writing-context / pipeline / candidate-isolation / recovery 합성 검사 프로그램 네 개 pass.
- 편집 rule routing 구조 검사 13개 pass.
- CS6 앱 import·게시·실모델 생성 성과는 이번 통합에서 not_run. 브랜치에 기록된 과거 검증을 신규 실측으로 보고하지 않음.

## 복구 범위

`before`와 `before-*` 태그·브랜치를 유지한다. Git 복구 bundle은 로컬 extension/data/consolidation/recovery와 archive/recovery 양쪽에 보존했다. 부모 bundle의 before ref 독립 복구와 Core bundle 다섯 개의 정확한 부모 gitlink 커밋 복구·독립 fsck를 통과했다.

자료 복구는 `D:/AI Agent/Creator-Archive/2026-10-21/`의 original-inventory.json·recovery-ledger.jsonl·migration-state.json이 소유한다. 전체 파일 gate를 통과한 뒤 검증한 cross-volume 원래 사본과 stale Git registration을 퇴역시켰다. 초기 Windows DirEntry inventory의 file ID 0은 원본 ID로 간주하지 않는다. 실제 동일 볼륨 rename receipt 또는 유지된 원래 경로와 크기·수정 시각·현재 SHA-256을 연결한다. C: 사본은 원본을 읽으며 산출한 SHA-256과 대상 read-back 해시를 별도로 대조했다.

## 자료 정리 승인

사용자가 보고서 권장안의 최종본·필수 자산·공용 도구 main 이전, 나머지 archive 보관, 복구 검증 뒤 기존 worktree 네 곳의 퇴역과 main Git clean 마감을 승인했다. 데이터는 영구 폐기하지 않는다. 최종 XML이 참조하는 원본·PNG·WAV도 필수 자산으로 보존한다. 기존에 없던 Zeus 원본 한 파일은 사용자가 제외했다.

## 단일 workspace 구현 검증

- `creator_workspace.py`와 `creator_job.py`가 job 생성·경로 조회·실행·provenance를 소유한다. 같은 job 중복 실행, GPU 충돌, 실패·취소·프로세스 종료 후 잠금 해제, 코드 버전 변경과 경로 이탈을 검사했다.
- 관련 합성 회귀 80개 중 sandbox에서 79개 pass, junction 검사 1개는 별도 권한으로 pass. 추가 편집/workflow 관련 48개 중 47개 pass, NTFS 원자적 no-clobber 검사 1개는 별도 권한으로 pass. 중복 검사 수를 독립 표본으로 합산하지 않는다.
- 기존 Qwen 환경에서 참고 구간·음성 cache·엔진 검사 18개 pass. C# 앱 재빌드와 writing-context / pipeline / candidate-isolation / recovery 네 검사 프로그램, 새 workspace 경로 검사 프로그램 pass. 실제 모델 음성 생성·Premiere import·전체 제작은 not_run이다. 기존 환경의 SoX·flash-attn 안내는 이번에 설치로 해소하지 않았다.
- 변경한 제작 스킬 6종은 기존 환경의 PyYAML로 공식 quick_validate pass. 번들 무결성과 PowerShell 문법 검사 pass. 실제 브라우저 병행 실행은 not_run이며 같은 프로필은 순차 사용한다.
- `audit_branch_absorption.py`는 before 태그들의 net tracked 변경 193개를 재현해 unreviewed 0을 확인한다. 다른 네 worktree의 Git 제외되지 않은 미추적 파일도 0개였다. 이는 의미 검토·관련 기능 검사를 대체하지 않는다. ignored 작업 스크립트·자료는 이전 gate에서 별도로 확인한다.
- 부모 Git bundle을 독립 임시 저장소로 fetch해 7개 before ref와 전체 객체 무결성을 확인했다. 각 worktree의 Core bundle도 complete history로 verify했다. receipt는 로컬 `extension/data/consolidation/recovery/verification.json`이다.

## 승인된 자료 이전 결과

선정 근거는 로컬 cleanup-plan.json이며 실제 이전 기록은 migration-state.json·migration-journal.jsonl이다. 아래 선정 파일을 main의 job으로 보존했다. 기존 파일의 편집 승인 상태를 새로 만들지 않으며 XML 사본은 pathurl만 변경했다. 원본 XML은 archive에 유지한다.

| 작업 | 보존 권장안 | 이전 후 위치 |
|---|---|---|
| wardogs | post-r27 최종 MP4·전체 SRT·설명, thumbnail-r2 master | `extension/jobs/wardogs/outputs/` |
| Zeus 월간 리뷰 | r9 XML + 존재하는 참조 자산. 누락 원본은 사용자 제외 | `extension/jobs/zeus-month-review/outputs/` |
| 도깨비 첫날 리뷰 | 사용자 확정 post-r6 XML·SRT + 참조 자산 | `extension/jobs/dokkaebi-play-review/outputs/` |
| 도깨비 음성 리뷰 | 사용자 편집본 SRT를 우선 보존하고 voice-cut-r6 XML은 별도 기준본으로 보관. 동일 편집이라고 가정하지 않음 | `extension/jobs/dokkaebi-voice-review/` |
| 도깨비 덱 | cut-r4 XML·SRT. 미선택 썸네일 시안은 work archive에 보존 | `extension/jobs/dokkaebi-deck/` |
| 백룸 쇼츠 | 명시된 final-r6 폴더의 결과와 필요한 metadata | `extension/jobs/backroom-shorts/` |
| NotebookLM 5개 작업 | 각 기존 output의 MP4·SRT·썸네일·가이드 네 파일 그대로 | `extension/jobs/<기존-ID>/outputs/` |

main의 기존 FFmpeg·whisper.cpp·Qwen·GPT-SoVITS와 빌드된 Replier를 유지하고, wardogs의 qwen-asr, ainotebook의 Whisper models/python-deps, Replier의 replier-llm을 catalog 위치로 이전했다. ASR 다운로드 조각과 Ollama 설치 ZIP은 archive/tool-downloads로 분리했다. Replier 개인설정은 24hreplier job의 work/replier에 비공개 이전했다. 기존 TTS 목소리·개인 상태는 archive에서 복구할 수 있다. 새 job에 자동 복제하지 않는다.

main의 이전 중간 output·task runtime·TTS 생성물·이전 상태는 archive/main에 보관했고, 네 worktree의 전체 checkout과 독립 Git metadata도 보존했다. main의 약 113.53 GiB wardogs-c-drive-media-archive도 그대로 보관했다. 초기 보호 경로 제외 metadata 목록을 전체 파일 inventory로 대체했으며, 새로운 목록에는 원본 입력과 private 파일도 포함한다. 내용·자격 증명 값은 로그에 출력하지 않는다.

영상 작업 11개를 이전했다. XML의 존재하는 참조는 Zeus 518, 도깨비 첫날 935, 음성 리뷰 기준본 272, 덱 1개이며 각 job 내부로 연결했다. Zeus의 기존 누락 원본 1개는 사용자 지시로 제외 상태를 남겼다. NotebookLM 다섯 작업은 각각 네 파일을 유지했다. 두 도깨비 job의 같은 원본은 작업 간 쓰기 충돌을 피하기 위해 독립 입력으로 보존했다.

기존 worktree 경로는 wardogs(`C:/Users/Hugh/.codex/worktrees/wardogs/Creator`), `D:/AI Agent/GitHub/Creator-24HReplier`, `Creator-ainotebook`, `Creator-dokkaebi`다. D: 세 곳은 파일 identity를 유지하는 동일 볼륨 rename으로 archive에 보관했다. C:는 copy+SHA-256 검증 후 원래 사본을 마지막 gate까지 유지한 뒤 퇴역시켰다. TRYALLGAME·backroom 브랜치도 before 태그와 Git bundle에 보존한다.

## 이전 후 검증과 한계

- 이전·복원 안전성 fixture 12개 pass. job 격리·process/GPU lease fixture 14개 pass. Windows 초기 file ID 0을 무근거로 통과시키지 않으며, 알려진 ID 불일치는 metadata 검사로 낮춰 통과시키지 않는다.
- runtime catalog 구성요소 9개의 경로 존재를 확인했다. FFmpeg·whisper.cpp 실행, faster-whisper·Qwen-ASR import, Ollama 실행과 로컬 model manifest 2개 pass. ASR은 파일 이전과 겹친 첫 60초 probe가 timeout됐고, 이전 종료 후 180초 제한의 오프라인 재검사에서 pass했다. 모델 다운로드·설치·실모델 추론은 실행하지 않았다.
- 수정한 video-to-srt 스킬은 공식 quick_validate를 UTF-8 모드로 pass했다. installer PowerShell 구문 검사 pass. skill 안내와 Replier 설치 metadata가 실제 catalog 경로를 따른다.
- 브랜치 변경 193개를 다시 대조해 unreviewed 0을 확인했다. 이는 역사적 Git merge를 수행했다는 뜻이 아니며 source tag·출처 표·관련 구현 검사를 근거로 내용을 흡수했다.
- XML 구조·경로 변경 범위를 검사했다. Premiere import·정상 속도 재생·전체 새 제작·OAuth 로그인·암호화 설정 복호화는 not_run이다. 개인설정 검증은 비공개 copy/hash/restore 수준으로 기록한다.
- archive는 main에서의 후속 변경과 독립된 로컬 복구본이다. 원본 source tree와 개인설정은 파일별 ledger로 새 빈 폴더에 복원한다. C: 소스 파일의 NTFS 추가 데이터 스트림은 숨김 파일까지 확인해 0개였다. Git code와 Core는 bundle로 별도 복원한다. 자세한 명령과 git pointer의 한계는 WORKSPACE.md가 소유한다. 같은 디스크의 로컬 archive이므로 물리 디스크 고장까지 막는 별도 백업은 아니다.


초기 inventory에서 일반 파일로 보였던 Whisper cache의 Windows LX reparse point 하나는 opaque 항목으로 분리했다. 원본 point는 동일 볼륨으로 archive에 옮기고 raw buffer도 별도 보관했으며, 실제 Windows fixture와 원본 metadata로 buffer·mtime 복원을 확인했다. 링크는 과거 Linux 세션을 가리켜 원래부터 Windows에서 열 수 없었고, 현재 모델 파일은 별도로 정상 보존돼 있다. 외부 Linux 세션 복원은 주장하지 않는다.

## 최종 복구 gate

이전 전 파일 124,534개(논리 크기 261.42 GiB)의 원래 경로와 독립 archive 위치를 연결하고 내용 해시를 검증했다. private 복원 probe는 314개 파일을 바이트 비공개 방식으로 복원·재해시해 통과했다. 존재하는 XML 참조 1,726개를 확인했고 사용자 제외 누락 원본은 1개다.

기존 worktree 네 곳을 퇴역시켰다. C: 원래 사본은 전체 ledger와 archive 대상의 identity·크기·수정 시각을 다시 확인한 뒤 검증된 cross-volume 이동의 마지막 단계로 정리했다. 데이터는 모두 archive에 남아 있다. D: 세 checkout은 archive의 일반 snapshot이며 활성 Git checkout으로 취급하지 않는다. before 태그·원래 브랜치·복구 bundle·archive는 유지한다. 최종 main clean 판정은 로컬 final-receipt.json에 커밋 SHA와 함께 기록한다.
