---
name: coordinate-video-production
description: 영상 종류와 요청 범위에 따라 소재·리서치·대본·NotebookLM 생성·게임 편집·자막·제목과 썸네일·쇼츠·업로드 준비·성과·댓글 전문 스킬을 연결하고 작업 상태와 결과를 검증한다. 영상 제작 총괄, 여러 단계 연결, 기존 작업 재개에 사용한다. 부분 요청은 해당 범위만 수행한다.
---

# Coordinate Video Production

총괄은 요청 범위, 전문 스킬 선택, 입력·결과 전달, 재개와 완료 판정을 소유한다. 리서치·생성·컷·자막·패키징·쇼츠·분석·댓글의 작업 방법은 각 전문 스킬을 읽어 수행한다. 스킬 호출은 해당 SKILL.md를 읽고 절차를 실행하는 것이며 별도 Agent 생성이나 실제 실행을 보장하는 함수 호출이 아니다.

## 요청 범위를 먼저 선택

기존 대화·작업 기록에서 영상 종류, 제공 자료, 요청한 결과와 종료점을 확인한다. 주제만 있다는 이유로 게임 원본을 생성 영상으로 대체하거나, 게임이라는 단어만으로 설명 영상을 실황 편집으로 분류하지 않는다. 명확한 부분 요청이 전체 제작 기본값보다 우선한다.

| 요청과 입력 | 호출할 기존 스킬 | 호출 범위와 종료점 |
|---|---|---|
| 소재를 골라 달라 / 무엇을 만들지 미정 | [game-trend-brief](../game-trend-brief/SKILL.md) | 소재·기획 근거까지만. 제작 요청이 함께 있을 때 선정 결과를 제작으로 전달 |
| 신작·업데이트 날짜·공식 사실이 필요 | [korean-game-research](../korean-game-research/SKILL.md) | 필요한 사실·출처. 캘린더 등록까지 자동 확대하지 않음 |
| 영상 목적·흐름·새 대본·기존 대본 수정/검토 | [write-video-script](../write-video-script/SKILL.md) | 요청한 기획·대사·화면 구성까지. 녹음/편집·제목 패키지·게시로 자동 확대하지 않음 |
| 설명 영상용 근거 조사만 | [notebooklm-research-topic](../notebooklm-research-topic/SKILL.md) | 노트북·검수 출처까지 |
| 준비된 NotebookLM 노트북에서 영상 생성만 | [notebooklm-generate-video](../notebooklm-generate-video/SKILL.md) | 기존 출처에서 생성·재생·다운로드 가능 상태까지 |
| 주제에서 설명 영상 전체 제작 | NotebookLM 리서치 → 생성 → 자막 → 제목·썸네일 → 업로드 준비 | [NotebookLM 전체 제작 연결](references/notebooklm-workflow.md)의 기존 5단계 |
| 게임 원본 컷편집·수정·후편집 | [edit-gameplay-video](../edit-gameplay-video/SKILL.md) | 요청한 모드의 영상·자막·검수. 기존 컷 수정은 해당 revision에서 재개 |
| 완성 영상에서 자막만 | [video-to-srt](../video-to-srt/SKILL.md) | 로컬 전사·정제·검증 절. NotebookLM 다운로드·영상 재생성을 추가하지 않음 |
| 제목·썸네일만 | [youtube-title-thumbnail](../youtube-title-thumbnail/SKILL.md) | 요청한 문구/이미지/패키지까지. 필요한 실제 영상·SRT 근거를 전달 |
| 완성 자료의 설명·챕터·수동 업로드 가이드 | [prepare-youtube-upload](../prepare-youtube-upload/SKILL.md) | 초안 또는 최종 준비 모드. 부족한 승인·자료를 임의 생성하지 않음 |
| 긴 영상에서 쇼츠·후보·선택본 출력 | [create-shorts](../create-shorts/SKILL.md) | 후보/선택/최종 중 요청 모드. 후보 선택과 불확실 발화 확인 경계 유지 |
| 주간 편성·채널 진단·공개 시간 | [youtube-channel-coach](../youtube-channel-coach/SKILL.md) | 요청한 모드만. 단일 영상 성과는 아래 진단으로 연결 |
| 게시 영상의 CTR·검색 유입·유지율 | `youtube-title-thumbnail`의 [실적 진단](../youtube-title-thumbnail/references/performance-review.md) | 관측·가설·다음 선택. 기존 게시물 수정으로 확대하지 않음 |
| 댓글 분류·답글·반복 질문 소재 | [youtube-comment](../youtube-comment/SKILL.md) | 답글 초안·소재 후보. 실제 댓글 게시·고정은 포함하지 않음 |
| 기존 게시물 설명의 타임스탬프·해시태그 수정 | [youtube-timestamp-hashtag](../youtube-timestamp-hashtag/SKILL.md) | 정확한 대상·외부 쓰기 승인이 있는 요청만 전문 owner로 전달 |

이 표의 프로젝트 상대 링크를 해당 기능의 관리 원본으로 사용한다. 같은 이름의 플러그인·개인 사본이 노출돼도 프로젝트 원본을 읽는다. 프로젝트 원본이 없으면 누락으로 보고하고 외부 사본으로 자동 대체하거나 덮어쓰지 않는다. 선택한 스킬이 없으면 해당 호출의 누락만 알리고 가능한 독립 작업을 진행한다. 자동 설치하거나 다른 기능을 실행한 것으로 기록하지 않는다.

직접 말할 경험·설명·리뷰 영상에서 대본이 요청되면 `write-video-script`를 선택한다. 기존 채널 의도·자료·대본·제외 범위를 전달하고, 실제 촬영·녹음의 순서를 보존한다. 대본만 요청하면 그 결과에서 종료한다. 이미 확정된 대본을 쓰는 편집이나 NotebookLM 생성 영상에 새 대본 작성을 필수 단계로 끼워 넣지 않는다. 영상 제작까지 요청된 경우에도 대본 결과를 실제 녹음·생성 음성이나 편집 완료로 간주하지 않고 필요한 입력을 다음 전문 owner에 넘긴다.

여러 결과를 요청하면 선행 관계가 있는 것만 연결한다. 게임 편집과 업로드 준비를 함께 요청했다면 편집 → 최신 편집본 SRT 확인 → 제목·썸네일 → 수동 패키지 순서로 연결하고, 편집 스킬이 이미 검증한 SRT를 이유 없이 재전사하지 않는다. 쇼츠·댓글·성과 분석은 요청한 경우의 별도 결과이며 롱폼 제작 완료의 필수 단계가 아니다.

동일 job에서 업로드 패키지와 쇼츠 등 여러 최종 결과를 요청받으면 **첫 출력 전에** `outputs/upload/`는 업로드 네 파일, `outputs/shorts/`는 쇼츠 MP4·ZIP으로 구분해 각 호출에 exact 출력 범위를 전달한다. 검토본·로그는 기존 `work/` owner에 둔다. 네 파일 검증·archive는 수동 패키지의 `preparation.output_dir`인 `outputs/upload/`에만 적용하며 형제 결과 폴더를 스캔·이동하지 않는다. 단일 결과의 기존 outputs 배치는 유지한다. 기존 결과가 섞여 있으면 자동 이동하거나 쇼츠를 scratch로 재분류하지 말고 정리 범위를 먼저 재확정한다.

전달할 때 경로를 `NotebookLM 전체 제작 / 게임 편집 / 부분 작업 / 기획 / 게시 후 분석` 중 하나로 명시한다. 최종 수동 패키지가 요청됐으면 업로드 준비 스킬이 요구하는 기존 자산·승인·내용 검수와 공개 시간 근거를 확인하고, 필요한 공개 시간 분석만 채널 코치에 요청한다. 가이드 초안·설명 문구만 요청한 경우 최종 패키지의 모든 자산 생성으로 확장하지 않는다. 사용자가 제공한 유효한 자료는 해당 전문 검증을 거쳐 재사용한다.

소재 브리핑만, 댓글 답글 하나만, 제목 어법 수정만 같은 요청에는 새 job·브라우저 연결·전체 분석을 강제하지 않는다. 경로/대상/결정이 결과를 바꾸고 기존 근거로 특정할 수 없을 때 해당 미정 항목만 확인한다.

## 창작 선택과 요청 범위

Creative delegation is owned only by the active project policy clause `creator-video-creative-delegation-v1`. 총괄은 이 조항의 적용 판단을 전달하며 새로운 위임 trigger를 정의하지 않는다. 적용되는 작업에만 `execution_mode: autonomous_local_pipeline`, `thumbnail_contract.approval_mode: delegated_by_user`, `thumbnail_contract.instruction_source: explicit_user`와 조항 근거를 기록한다. 그 밖에는 기존 `review_gated`를 유지한다. 이미 승인된 다음 단계는 하위 스킬 반환만으로 다시 승인받지 않는다.

위임은 현재 요청 범위에서만 유효하다. 분석·제목·자막만 요청했으면 전체 영상 생성이나 게시로 확장하지 않는다. 외부 쓰기·비용·설치·보호 자료 접근과 전문 스킬의 사용자 선택 경계는 현재 승인에 따라 판정한다.

## 첫 실행 게이트

미디어를 읽거나 로컬 제작 산출물·NotebookLM 아티팩트를 관리할 때 main과 exact job을 먼저 확정한다. 새 job이 필요할 때만 `python -B scripts/creator_job.py init --job <job-id>`로 초기화한다. 기존 작업은 같은 job을 재사용하고 상태를 먼저 읽는다. 이 스킬 유지보수에는 제작 활성화를 실행하지 않는다.

```powershell
$activation = python -B .agents/skills/coordinate-video-production/scripts/activate_worktree.py `
  --root . --job <job-id> | ConvertFrom-Json
if ($activation.status -ne 'valid') { throw ($activation | ConvertTo-Json -Depth 8) }
$activeRoot = $activation.active_root
$activeBranch = $activation.active_branch
```

- 기본 기대 브랜치는 main이다. 사용자가 이번 요청에서 다른 브랜치를 지정했을 때만 `--expected-branch`로 전달하며 현재 브랜치를 기대값으로 채우지 않는다.
- `expected_root`가 있으면 재검증된 `active_root`만 사용한다. `redirected: true`이면 이후 모든 명령과 상대 경로를 그 root에 맞추고 원래 cwd를 다시 사용하지 않는다.
- 실제 작업 root의 시작 문서와 job 상태를 확인한다. 비-NotebookLM 작업은 그 전문 owner의 기존 상태·timeline·revision을 사용하며 NotebookLM 단계로 승계하지 않는다.
- 로컬 명령은 `python -B scripts/creator_job.py run --job <job-id> -- <명령>`으로 실행한다. GPU는 `--gpu`, 공용 도구는 runtime catalog를 사용한다. 원본·결과 접근은 exact 대상과 목적의 승인 범위 안에서만 한다.
- `check_skill_bundle.py --root .`는 버전 관리되는 로컬 제작 스킬 묶음을 확인한다. 외부 개인·플러그인 스킬의 현재 가용성과 일치 여부를 대신 보증하지 않는다. 제작 중 `--record-reviewed`로 불일치를 덮지 않는다.
- job 잠금·경로·산출물 배치는 [단일 작업 공간](../../../extension/docs/WORKSPACE.md)과 선택한 전문 스킬을 따른다. 일반 부분 작업을 위해 `VIDEO_JOB.json`을 만들지 않는다.

## 상태와 재개

NotebookLM 전체 제작과 그 재개에만 [VIDEO_JOB 형식](references/video-job-format.md), 검증기와 고정 5단계 엔진을 사용한다. 다른 경로의 결과를 기존 research/video 단계에 가짜 완료로 넣거나 `skipped` 같은 미지원 상태를 만들지 않는다. 이 연결 개선은 엔진이나 v3 스키마를 범용 작업 엔진으로 바꾸지 않는다.

게임 편집은 기존 editorial-state·timeline·job state, 쇼츠는 기존 manifest·선택 revision, 부분 미디어 작업은 job의 기존 `state.md`에 요청 범위·호출 owner·현재 입력 버전·확인된 결과·남은 경계만 기록한다. 제목·수동 업로드는 각 기존 패키지를 정본으로 참조한다. 같은 근거를 새 공통 JSON으로 복제하지 않는다. 단순 채팅 결과는 채팅으로 완료한다.

재개 시 요청 범위와 최신 실제 산출물·해시·revision을 대조해 첫 미완료 작업을 선택한다. 범위 밖의 기존 pending 단계나 선택되지 않은 스킬은 이번 부분 요청의 차단이 아니다. 입력이 바뀌면 그 결과에 의존한 검수·자막·패키지만 무효화하고 유효한 독립 결과는 재사용한다.

## 하위 스킬 호출 계약

선택한 전문 스킬을 읽고 다음을 전달한다. 이미 확정된 값은 사용자에게 다시 묻지 않는다.

- 호출자가 `coordinate-video-production`임과 **이번에 요청한 작업·모드·종료점**.
- exact job/root와 기존 상태/패키지 위치. 채팅 작업이면 해당 입력 식별자.
- 승인된 입력, 최신 산출물 경로·해시·revision, 사용할 근거와 미검증 범위.
- 이번 요청의 실행·창작 위임과 자료 접근 범위. 하위 스킬의 별도 선택 경계.
- 필요한 결과와 해당 스킬이 소유한 검증. 브라우저 작업일 때만 확정 프로필·origin과 유효한 연결을 전달.

반환에서는 실제 결과 참조, 최신 버전, 실행한 검사와 `not_run`, 승인/선택 상태, 남은 오류·필요 입력을 확인한다. 반환의 상태 이름은 각 전문 형식을 유지하며 구조 검사·ASR·화면 표본을 실제 청취나 의미 승인으로 바꾸지 않는다.

단독 스킬의 마지막 정지는 총괄이 **이미 요청된 다음 작업**으로 넘기는 반환점이다. 다만 `create-shorts`의 후보 선택·불확실 발화 확인 등 실제 사용자 결정, 로그인·한도·실패·비용·권한 경계는 그대로 유지한다. 하위 스킬을 호출하는 데 별도 Agent 생성은 필요하지 않다.

## 전문 내용의 단일 소유

녹음 전 대본의 목적·근거·구성·수정은 `write-video-script`, 컷 설계·발화/음향 검수는 게임 편집, 전사·자막 품질은 자막, 제목·이미지와 승인·실적 분석은 제목/썸네일, 설명·챕터·최종 네 파일은 업로드 준비, 쇼츠 선정·렌더는 쇼츠, 댓글 분류·한국어 답글은 댓글 스킬이 소유한다. 해당 방법·임계값·도구 코드를 총괄에 복사하지 않는다.

총괄은 필요한 부분만 호출하고 결과의 동일성·선행 조건·요청 완료를 확인한다. 실제 전문 검수는 담당 스킬을 실행한 근거로 남긴다. 채널 말투는 기존 [공통 참고](../youtube-title-thumbnail/references/channel-voice.md)를 재사용한다.

## NotebookLM 전체 제작과 Chrome

이 경로를 선택한 경우에만 [NotebookLM 전체 제작 연결](references/notebooklm-workflow.md)을 읽는다. 그 문서가 작업 기록, 단계 전환, 영상 내용 검수 결속, 공개 시간 분석 전달, 기존 수정·완료 절차를 소유한다. 생성 UI·대기·전사·썸네일 생성·업로드 가이드의 세부 방법은 각 전문 스킬이 소유한다.

브라우저가 필요한 호출에만 `connect-chrome-profile`을 사용한다. NotebookLM의 프로필 설정은 두 계층만 사용한다. 프로필 directory나 alias가 있으면 그 입력을 사용하고, 없으면 worktree-local 기본값을 자동 사용한다. `resolve_browser_profile.py` 결과를 작업의 `browser.profile_directory`·origin에 기록하며 `SESSION_HANDOFF.md`를 프로필 설정에 사용하거나 수정하지 않는다. 재개 작업의 확정 프로필을 새 기본값으로 덮지 않는다. 상세 기록은 NotebookLM 연결 문서를 따른다.

NotebookLM 리서치만·생성만 요청한 부분 작업도 하위 스킬이 요구하는 `browser.profile_directory`·`browser.required_origin`을 확정한다. resolver의 기존 `--config`·프로필 입력·`--required-origin` 인터페이스를 사용하고 해당 job의 기존 `state.md`에 확정값과 연결 검증을 기록해 전달한다. 이를 위해 전체 VIDEO_JOB를 만들거나 5단계 엔진을 실행하지 않는다. 기존 VIDEO_JOB가 있으면 그 유효한 연결값을 재사용하되 독립 부분 요청으로 전체 상태를 완료 처리하지 않는다.

### 영상 내용 검수

NotebookLM 제작의 사실·비교·권고 검수와 중대 오류의 단계 차단은 [기존 검수 절차](references/notebooklm-workflow.md#영상-내용-검수)를 따른다. 게임·쇼츠·독립 부분 작업은 각 전문 owner의 검수 범위를 따른다. 분석만 맡은 작업에 영상 수정·전체 검수를 새 필수 단계로 추가하지 않는다.

## 완료와 전달

선택한 호출의 필수 입력과 검증이 충족됐는지 확인하고 요청한 결과·경로·실행 검사·한계를 보고한다. 로컬 제작은 검증한 workflow root·branch·redirected 여부도 전달한다. 결과 형식은 전문 스킬을 따른다. 네 파일 규칙은 수동 업로드 패키지를 요청했을 때 적용하며 쇼츠 ZIP·편집 후보·댓글 초안에 강제하지 않는다.

부분 요청 완료를 전체 VIDEO_JOB 완료로 기록하지 않는다. 반대로 전체 제작을 요청받고 필요한 작업이 남았으면 부분 결과만으로 전체 완료라 하지 않는다. 사용자 업로드·게시·실적 확인은 제작 스킬의 자동 후속 작업이 아니다.
