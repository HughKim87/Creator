# Creator 통합·정리 판정

- 목적: 제거될 브랜치에 재사용 개선이 남지 않도록 출처별 흡수 판정과 자료 처분 대상을 기록한다.
- 읽는 시점: 단일 workspace 전환 검토와 기존 자료·worktree 처분 승인 시.
- 책임: main 유지보수 세션이 실제 파일·검사를 갱신하고 사용자가 자료 처분을 승인한다.
- 상태: 개선 통합과 단일 workspace 코드 구현 완료. 기존 자료 이동·삭제와 worktree 제거 미실행.
- 관련 권위: `../docs/WORKSPACE.md`, 루트 `PROJECT_RULES.md`.

## 개선사항 출처 대조

태그는 원래 Git 이력을 고정한다. 아래 판정은 현재 main의 기능 소유자를 기준으로 하며 과거 브랜치 전체를 덮어쓰지 않는다. 개인 설정·원본·출력은 공통 코드에 포함하지 않는다.

| 출처 | 확인 범위와 판정 | main 소유자 |
|---|---|---|
| `before-codex-wardogs` | 공통 조상 이후 공통 코드·규칙 변경 없음. 썸네일 제작 자료는 영상별 데이터이며 원위치 보존 | 공통 기능 추가 불필요; 자료 이전 승인 대상으로 분리 |
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

`before`와 `before-*` 태그를 유지한다. 현재 작업은 원래 worktree와 ignored 자료를 변경하지 않는다. 로컬 metadata inventory는 `extension/data/consolidation/baseline.json`이며 inputs·비밀·브라우저 프로필·링크 경계는 제외됐다. 이 목록은 파일 내용 백업이 아니다. ignored 자료를 처분하기 전에는 별도 복구본 또는 검증된 재생성 조건을 확보해야 한다.

## 자료 정리 승인

기존 자료·worktree는 아직 이동·삭제하지 않았다. 최종 XML이 참조하는 원본·PNG·WAV를 포함한 종속 자산은 단순 중간본으로 처분하지 않는다. 해당 작업의 최종 승인 근거와 dependency를 대조한 뒤 정확한 유지·보관·삭제 목록을 제시한다. 사용자 확인 전에는 이 절을 실행 승인으로 해석하지 않는다.

## 단일 workspace 구현 검증

- `creator_workspace.py`와 `creator_job.py`가 job 생성·경로 조회·실행·provenance를 소유한다. 같은 job 중복 실행, GPU 충돌, 실패·취소·프로세스 종료 후 잠금 해제, 코드 버전 변경과 경로 이탈을 검사했다.
- 관련 합성 회귀 80개 중 sandbox에서 79개 pass, junction 검사 1개는 별도 권한으로 pass. 추가 편집/workflow 관련 48개 중 47개 pass, NTFS 원자적 no-clobber 검사 1개는 별도 권한으로 pass. 중복 검사 수를 독립 표본으로 합산하지 않는다.
- 기존 Qwen 환경에서 참고 구간·음성 cache·엔진 검사 18개 pass. C# 앱 재빌드와 writing-context / pipeline / candidate-isolation / recovery 네 검사 프로그램, 새 workspace 경로 검사 프로그램 pass. 실제 모델 음성 생성·Premiere import·전체 제작은 not_run이다. 기존 환경의 SoX·flash-attn 안내는 이번에 설치로 해소하지 않았다.
- 변경한 제작 스킬 6종은 기존 환경의 PyYAML로 공식 quick_validate pass. 번들 무결성과 PowerShell 문법 검사 pass. 실제 브라우저 병행 실행은 not_run이며 같은 프로필은 순차 사용한다.
- `audit_branch_absorption.py`는 before 태그들의 net tracked 변경 193개를 재현해 unreviewed 0을 확인한다. 다른 네 worktree의 Git 제외되지 않은 미추적 파일도 0개였다. 이는 의미 검토·관련 기능 검사를 대체하지 않는다. ignored 작업 스크립트·자료는 이전 gate에서 별도로 확인한다.
- 부모 Git bundle을 독립 임시 저장소로 fetch해 7개 before ref와 전체 객체 무결성을 확인했다. 각 worktree의 Core bundle도 complete history로 verify했다. receipt는 로컬 `extension/data/consolidation/recovery/verification.json`이다.

## 자료 이전·정리 제안 — 실행 미승인

정확한 파일별 목록은 로컬 `extension/data/consolidation/cleanup-plan.json`이다. 계획기는 읽기 전용이며 이동·삭제 기능이 없다. metadata와 출력 XML 참조만 읽었고 원본 입력·비밀 설정은 열지 않았다. 아래는 최종 보존 후보이며 승인·상호 호환이 검증되지 않은 파일을 확정본으로 바꾸어 부르지 않는다.

| 작업 | 보존 권장안 | 이전 후 위치 |
|---|---|---|
| wardogs | post-r27 최종 MP4·전체 SRT·설명, thumbnail-r2 master | `extension/jobs/wardogs/outputs/` |
| Zeus 월간 리뷰 | r9 XML + 실제 참조 자산. 이전 버전 처분 전 최종성 확인 | `extension/jobs/zeus-month-review/outputs/` |
| 도깨비 첫날 리뷰 | 사용자 확정 post-r6 XML·SRT + 참조 자산 | `extension/jobs/dokkaebi-play-review/outputs/` |
| 도깨비 음성 리뷰 | 사용자 편집본 SRT를 우선 보존하고 voice-cut-r6 XML은 별도 기준본으로 보관. 동일 편집이라고 가정하지 않음 | `extension/jobs/dokkaebi-voice-review/` |
| 도깨비 덱 | cut-r4 XML·SRT. 미선택 썸네일 시안은 work archive에 보존 | `extension/jobs/dokkaebi-deck/` |
| 백룸 쇼츠 | 명시된 final-r6 폴더의 결과와 필요한 metadata | `extension/jobs/backroom-shorts/` |
| NotebookLM 5개 작업 | 각 기존 output의 MP4·SRT·썸네일·가이드 네 파일 그대로 | `extension/jobs/<기존-ID>/outputs/` |

공용 도구는 main의 기존 FFmpeg·whisper.cpp·Qwen·GPT-SoVITS를 유지하고, wardogs의 qwen-asr, ainotebook의 models/python-deps, Replier의 replier-llm을 catalog 위치로 이전하는 안이다. 기존 Windows venv는 이동 후 실행 검증 전 원래 환경을 처분하지 않는다. 다운로드를 반복하는 방식으로 대체하지 않는다.

나머지 15,338개 metadata 항목(논리 크기 약 188.12 GiB)은 **검토·archive 후보**다. 중복·재생성 가능·영구 삭제 가능을 증명한 목록이 아니다. 특히 main `.runtime/wardogs-c-drive-media-archive`는 nested output까지 포함해 약 113.53 GiB이며 원본 보존 역할이 있을 수 있어 일괄 삭제하면 안 된다. 보존 후보 XML의 참조 수는 Zeus 519, 도깨비 첫날 935, 음성 리뷰 272, 덱 1이다. 참조 원본의 내용·이동 후 앱 재생은 아직 검사하지 않았다.

권장 archive 위치는 `D:/AI Agent/Creator-Archive/2026-10-21/`이다. 사용자 승인 후 기존 파일을 최종·공용 도구·복구 archive로 나누고, 각 파일의 source/target·해시·크기를 기록해 되돌릴 수 있게 한다. 동일 볼륨 이동과 다른 볼륨 copy+hash 검증을 구분한다. archive로 보존하는 동안 전체 디스크 사용량이 그 크기만큼 줄지는 않는다. 영구 삭제는 검증된 재생성 가능 항목과 승인된 정확한 대상에만 별도로 적용한다.

제거 대기 worktree는 wardogs(`C:/Users/Hugh/.codex/worktrees/wardogs/Creator`), `D:/AI Agent/GitHub/Creator-24HReplier`, `Creator-ainotebook`, `Creator-dokkaebi` 네 곳이다. 별도 브랜치만 있는 TRYALLGAME·backroom도 before 태그와 bundle에 복구 지점이 있다. worktree 안의 독립 Core·도구 Git·링크·private 설정·원본 inputs는 상위 폴더 승인에 묶어 삭제하지 않는다. 해당 owner의 보존과 새 경로 검증을 마친 뒤 제거 승인 범위를 대조한다.
