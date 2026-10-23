# NotebookLM 전체 제작 연결

- 목적: NotebookLM 전체 제작의 고정 5단계 기록·검수·재개 계약을 유지한다.
- 읽는 시점: 총괄이 NotebookLM 전체 제작 또는 기존 VIDEO_JOB 재개를 선택한 경우에만.
- 책임: 총괄은 단계 간 상태와 근거 결속을 관리하고 전문 작업은 각 스킬이 수행한다.
- 상태: 활성. 게임 편집·완성 영상 부분 작업에 이 형식을 강제하지 않는다.
- 관련 권위: [총괄](../SKILL.md), [VIDEO_JOB 형식](video-job-format.md), 현재 프로젝트 정책.

공통 작업 공간 활성화와 하위 스킬 전달 계약은 총괄을 따른다. 아래의 단계 이름·내용 검수·완료 조건은 이 NotebookLM 경로에만 적용한다. 독립 부분 요청은 이전 VIDEO_JOB를 완료시키기 위한 작업으로 확대하지 않는다.

## 작업 기록

진행 중 영상은 지정된 작업의 `VIDEO_JOB.json`을 먼저 확인하고 기존 browser·완료 단계·승인 범위를 재사용한다. 새 작업용 기본값 해석을 재개 작업에 반복하지 않는다.

main 작업 공간을 사용하며 영상마다 worktree를 만들지 않는다. 새 job은 `creator_job.py init --job <job-id>`로 만들고, 재개 job은 같은 ID로 inspect한다. 다른 job의 상태·승인·프로필을 승계하지 않는다. 브라우저 연결은 프로필별로 직렬화하고 반환된 exact 탭만 사용한다.

로컬 전사·렌더·생성 명령은 `python -B scripts/creator_job.py run --job <job-id> -- <명령>`으로 실행한다. GPU 작업에는 `--gpu`를 추가한다. 설치·모델은 공용 catalog의 경로를 사용하고 출력·로그·임시는 job 경로를 사용한다. 전역 상태나 공용 runtime에 영상 데이터를 쓰지 않는다. 코드 버전 변경 시 재개 전에 영향 범위를 확인하고 `--accept-code-change`를 명시한다.

[references/video-job-format.md](video-job-format.md)에 따라 새 작업마다 `extension/jobs/<job-id>/VIDEO_JOB.json`을 만든다.

- 프로필 설정은 두 계층만 사용한다. Git에서 제외된 worktree-local `extension/.runtime/video-workflow-defaults.json`은 새 작업의 기본값이고, 영상별 `VIDEO_JOB.json`의 `browser`는 그 작업에 확정된 현재값이다. `SESSION_HANDOFF.md`는 프로필 설정에 사용하거나 수정하지 않는다.
- 새 작업의 프로필은 `.agents/skills/coordinate-video-production/scripts/resolve_browser_profile.py`로 결정한다. 스킬 호출에 프로필 directory나 alias가 있으면 그 입력을 사용하고, 없으면 worktree-local 기본값을 자동 사용한다.
- 결정된 결과는 새 `VIDEO_JOB.json`의 `browser`에 기록한다. runtime 기본값 파일은 수정하지 않는다.
- 진행 중 작업의 하위 단계는 이미 확정된 `VIDEO_JOB.json`의 `browser`를 그대로 전달한다. 사용자가 해당 작업의 프로필 변경을 명시한 경우에만 resolver를 다시 실행하고, 실제로 사용할 새 결과를 작업의 현재값으로 기록한다.
- 사용자가 `메인프로필`처럼 runtime 설정의 `profile_aliases` 키를 입력하면 대응하는 label과 directory를 사용한다. 입력도 worktree-local 기본값도 없을 때만 작업 기록 생성과 browser runtime 초기화 전에 사용자에게 한 번 요청한다.
- 연결 스킬과 하위 단계 스킬 자체에는 프로필 기본값을 두지 않는다.
- 기본값 파일이 없어도 명시 입력을 먼저 병합해 검증한다. resolver의 `--required-origin`으로 호출자가 가진 origin을 전달할 수 있다. `needs_input.missing_fields`에 나온 값만 확인하며, 잘못된 JSON이나 알 수 없는 alias는 입력 누락으로 숨기지 않는다. 이 초기화는 runtime 설정을 자동 저장하지 않는다.
- `browser.profile_label`은 선택적 표시명이다. 별도 값이 없으면 전달받은 `profile_directory`와 같은 문자열을 기록한다.
- `browser.required_origin`은 같은 우선순위로 확정하되, 이 worktree의 runtime 기본값은 NotebookLM origin이다.
- 진행 중 작업은 사용자의 명시적 변경이 없는 한 기존 `VIDEO_JOB.json` 값을 보존한다. runtime 기본값 변경, 연결 스킬, 다른 작업, 현재 Chrome 창에서 값을 추론하거나 덮어쓰지 않는다.
- 새 작업은 `video-job-v3`, `storage_mode: job-folder-v1`을 사용하고 main 검증 결과를 `execution_context`에 기록한다. `paths.input_dir/work_dir/output_dir`는 각각 `extension/jobs/<job-id>/inputs`, `work`, `outputs`로 고정한다. 기존 경로 기록은 읽기 호환만 유지하며 자동 이동하지 않는다.
- `execution_mode`는 `autonomous_local_pipeline` 또는 `review_gated`로 기록한다.
- `execution_mode`는 단계 사이의 자동 진행만 제어한다. 제목·문구·이미지·최종 시각의 승인 권한을 부여하지 않는다.
- `thumbnail_contract`에 `generation_mode`, `allow_local_text_composite`, `approval_mode`, `instruction_source`를 기록한다. `approval_mode`와 위임 근거는 활성 정책의 `creator-video-creative-delegation-v1` 판정에서만 가져오며, 이 스킬이 사용자 표현을 별도로 재해석하지 않는다.
- 사용자가 웹 ChatGPT와 같은 생성을 요구하면 `generation_mode: one_shot_imagegen`, `allow_local_text_composite: false`, `instruction_source: explicit_user`로 기록한다.
- 기술 패키지와 생성 원본은 `extension/jobs/<job-id>/work/`, 최종 사용자 파일은 `extension/jobs/<job-id>/outputs/`에 둔다.
- 위 outputs는 job 공통 root다. 총괄이 쇼츠 등 복수 최종 결과를 함께 요청받은 새 작업은 첫 출력 전에 `outputs/upload/`·`outputs/shorts/`를 분리한다. `paths.output_dir` 자체는 outputs root로 유지하고, 각 전문 스킬에 하위 출력 위치를 전달한다. 수동 패키지의 `preparation.output_dir`·실제 네 파일은 upload 하위 폴더를 가리키므로 기존 검증기를 우회하지 않는다.
- `.gitignore`나 추적 정책을 임의로 바꾸지 않는다.

작업 기록 생성·변경 직후와 각 단계 시작 전에 실행한다.

```powershell
python .agents/skills/coordinate-video-production/scripts/validate_video_job.py `
  extension/jobs/<job-id>/VIDEO_JOB.json `
  --root . `
  --check-artifacts `
  --require-content-review
```

`status: valid`와 `worktree.status: valid`가 아니면 진행하지 않는다.

새 작업의 browser 값은 다음처럼 확정한다. `<profile-input>`이 없으면 관련 옵션을 생략한다.

```powershell
python .agents/skills/coordinate-video-production/scripts/resolve_browser_profile.py `
  --config extension/.runtime/video-workflow-defaults.json `
  --profile-alias <profile-input>
```

프로필 디렉터리를 직접 전달받았으면 `--profile-alias` 대신 `--profile-directory`를 사용한다. 출력의 `browser` 객체를 `VIDEO_JOB.json`에 그대로 기록한다.

## Chrome 게이트

`research`와 `video` 전에 작업 기록의 `browser.profile_directory`와 `browser.required_origin`을 그대로 `$connect-chrome-profile`에 전달한다. 둘 중 하나라도 없으면 연결을 시도하지 않고 작업 기록 검증 실패로 멈춘다.

- Chrome 프로필·초기 탭 선택은 `$connect-chrome-profile`만 소유한다. 현재 제공되는 `cua_repl`의 Chrome extension 경로를 사용하며, 예전 스킬 파일이 없다는 이유만으로 멈추지 않는다.
- `connected`와 검증 방법을 반환할 때만 NotebookLM 단계를 시작한다. 검증된 서비스 이전은 `browser.resolved_origin`으로 기록하고 기존 `browser.required_origin`과 프로필은 보존한다.
- 반환된 exact Chrome 바인딩과 검증 탭만 하위 단계에 넘긴다. 같은 런타임의 검증 바인딩은 probe 성공 시 재사용하고, 명시적 unavailable·disconnected 오류나 새 런타임에서는 `$connect-chrome-profile`로 다시 검증한다.
- 내장 브라우저, 다른 프로필, 별도 Playwright와 웹 검색으로 프로필·로그인 검증을 우회하지 않는다. `cua_repl`에서 검증된 Chrome을 제어하는 것은 정식 경로다.
- 연결 검증 시각을 기록하고 단계 검증기가 확인하게 한다. `autonomous_local_pipeline`은 연결 복구가 검증되면 저장된 첫 미완료 단계로 계속한다. 이전 에이전트의 ‘플러그인 없음’ 메모를 현재 도구 검증 없이 재사용하지 않는다.

## 단계 순서

| 단계 | 스킬 | 완료 근거 |
|---|---|---|
| `research` | `$notebooklm-research-topic` | 노트북 URL과 출처 품질 |
| `video` | `$notebooklm-generate-video` | 완성 영상, 길이, 30초 이내 재생 확인 후 일시정지, 다운로드 상태 |
| `captions` | `$video-to-srt` | MP4, SRT, 원본 전사와 전체 검수 |
| `title_thumbnail` | `$youtube-title-thumbnail` | 승인된 제목·문구·생성·최종 시각과 썸네일 |
| `upload_package` | `$prepare-youtube-upload` | 공개 시간 추천이 포함된 수동 가이드, 업로드용 네 파일과 별도 archive |

첫 `pending` 단계만 실행한다. 앞 단계가 모두 `complete`가 아니면 뒤 단계를 시작하지 않는다. 다만 아래의 업로드 가이드 초안은 단계 완료와 별개인 준비 작업으로 허용한다.

## 공개 시간 분석과 가이드 전달

`upload_package` 시작 전에 프로젝트의 [youtube-channel-coach](../../youtube-channel-coach/SKILL.md)의 「공개 시간만 추천하는 요청」 모드에 대상 채널·현재 요청 제약을 전달한다. 같은 런타임의 검증된 Chrome 연결은 재사용하고, 새 연결은 작업의 확정 프로필과 `target_origin: https://studio.youtube.com`을 `connect-chrome-profile`에 전달한다. NotebookLM의 `browser.required_origin`은 덮어쓰지 않는다.

분석 방법과 잠정 추천의 판단은 채널 코치가 소유한다. 총괄은 해당 채널·확인 시각·기간·시간대·실측/잠정·한계가 있는 반환인지 확인하고 [수동 패키지 형식](../../prepare-youtube-upload/references/manual-upload-package-format.md#공개-시간-추천)의 `publish_timing`으로 전달한다. 데이터 접근 불가를 확인한 반환도 공개된 제한과 잠정 추천으로 전달할 수 있다. 추천 시각의 유효성 검사와 가이드 표시는 업로드 준비 스킬에 맡긴다. 이 호출은 전체 채널 진단·게시·예약을 포함하지 않는다.

## 업로드 가이드 초안

사용자가 가이드를 먼저 요청하거나 썸네일 단계가 대기·차단된 경우, 확보한 영상·SRT·제목·근거로 `$prepare-youtube-upload`의 초안 경로를 실행할 수 있다. 작업 폴더에 `YOUTUBE-MANUAL-UPLOAD-DRAFT.md`를 만들고 미확정 제목·썸네일·내용 검수 등 남은 항목을 표시한다. 확인되지 않은 항목은 확정하지 않는다.

초안은 `upload_package.note`에 경로와 미완성 항목만 기록한다. 기존 활성 단계·차단 사유·`next_action`을 유지하고 `upload_package`는 `pending`으로 둔다. 초안을 완료 산출물에 넣거나 finalizer·archive를 실행하지 않는다. 최종 조건이 충족되면 현재 자료로 최종 가이드를 새로 생성한다.

## 영상 내용 검수

검수는 전체 내레이션 전사와 장면별 화면 문구를 함께 다룬다. 장면 전환별 대표 화면을 확인하고 날짜·숫자·정책 범위·결론을 출처와 대조하며, 오류가 있는 장면은 표시 구간 전체를 확인한다. 모델에게 준 제작 지시를 실제 정책으로 설명하지 않았는지도 확인한다. `review_scope`에 전체 내레이션 검토, 장면별 화면 검토 방법, 직접 청취 수행 여부와 미검증 범위를 각각 기록한다. 직접 청취를 하지 못한 경우 이를 전사 검토로 대체한 성공으로 기록하지 않고 제한을 공개한다.

자막 전체 검수가 끝난 뒤 제목·썸네일 제작 전에 영상의 핵심 사실·비교·선택 권고를 실제 사용한 리서치 근거와 대조한다. `content_review`에 검수한 MP4·SRT 경로와 해시, 검토 범위, 발견한 주장 위치·근거·처리 결과를 [작업 기록 형식](video-job-format.md#영상-내용-검수-기록)에 따라 기록한다. 기계 검사는 기록·해시·완료 조건을 확인하며 주장 자체의 진위를 대신 판정하지 않는다.

결제·제품 선택·기능 이해·영상 결론을 바꿀 수 있는 사실 오류나 근거 없는 핵심 단정은 `material`, 그 밖의 표현 한계는 `minor`로 분류하고 이유를 남긴다. 중대한 오류는 영상 수정 또는 실제 근거 재확인으로 해결한다. 설명란 주의 문구, 사용자 승인, SRT만의 사실 교정으로 해결 처리하지 않는다. 경미한 한계는 정확한 정정·범위를 최종 설명란과 가이드에 공개할 수 있다.

미해결 중대 오류가 있으면 `title_thumbnail`을 `blocked`로 두고 job의 차단 사유와 수정 행동을 기록한다. 기술적으로 완료된 영상·자막 단계는 유지한다. 검수 미완료도 제목·썸네일 제작 전에 해결한다. 내용 수정에 별도 권한·비용이 필요하면 그 결정만 요청한다. 영상·SRT 변경 시 검수 해시와 영향받는 제목·썸네일·수동 패키지를 다시 확인한다.

`autonomous_local_pipeline`의 국소 보정은 이미 승인된 원본·목적·로컬 산출물 범위에서 처리한다. 근거가 확인된 오류의 제거·수정이나 실제 음성으로 확인된 자막 정정이 영상의 주제·구성·선택 권고 방향을 바꾸지 않고 원본을 보존하는 경우, 에이전트가 보정하고 기존 내용·자막·경계 품질 검수를 수행한 뒤 다음 미완료 단계로 계속한다. 내부 보정이나 복구가 필요하다는 이유만으로 사용자 승인 대기로 바꾸지 않는다. 보정 위치·근거·해시는 기존 검수 기록에 남기며 새 승인 단계나 별도 기록 형식을 만들지 않는다.

이 보정은 새 편집 문법을 설계해 전체 분량으로 확장하거나 Premiere timeline·XML을 전달하는 작업과 구분한다. 후자의 calibration·revision 승인 절차를 보정에 자동 적용하지 않는다. 반대로 수정이 짧다는 이유만으로 의미 보존을 확정하지 않는다. 의미·결론·권고 변경 여부나 음성이 불확실하면 추가 근거 확인으로 해소하고, 해소할 수 없어 사용자 판단이 필요한 항목만 요청한다. 사용자의 명시적 검수 요청, 별도 권한·비용·외부 효과 경계, 미해결 중대 오류의 차단은 유지한다. 직접 청취하지 않은 검수를 청취 완료로 기록하지 않는다. 실제 차단이 해소되면 기존 승인과 유효한 산출물을 재사용해 이어간다.

새 작업에는 `content_review`를 포함한다. 기존 기록의 읽기·검증 호환은 유지하되, 이 스킬로 제작을 재개하거나 패키지를 다시 완료할 때 기록이 없으면 `pending` 검수를 추가한다. 이미 제목·썸네일과 업로드 단계가 완료였다면 파일·승인 근거를 보존한 채 해당 단계만 `pending`, job은 `active`로 되돌리고 내용 검수부터 수행한다. 과거의 기술 검증 결과를 내용 검수 완료로 변환하지 않는다.

## 실행과 승인

1. 실제 산출물과 작업 기록을 확인한다.
2. 활성·사용자 대기·차단 단계가 있으면 그 상태부터 확인한다. 후속 단계는 차단을 해결한 뒤 실행하며, 가이드 초안 요청은 위 초안 경로로 처리할 수 있다.
3. 다음 스킬 하나만 실행하고 산출물을 검증한다.
4. 검증 후에만 단계 상태와 경로를 갱신한다.
5. `autonomous_local_pipeline`이면 검증 직후 다음 `pending` 단계로 계속한다. `needs_user`, `blocked`, `complete` 또는 아래 외부 경계에 도달할 때만 멈춘다. 대기·차단 상태에서 가이드 초안을 준비할 수 있으면 이를 반환한 뒤 해당 상태를 유지한다.

썸네일 단계에는 작업의 `thumbnail_contract`와 활성 정책의 `creator-video-creative-delegation-v1` 판정을 전달한다. 승인 순서·이미지 생성·시각 검수·패키지 완료는 [제목·썸네일 전문 스킬](../../youtube-title-thumbnail/SKILL.md)이 소유한다. 총괄은 `autonomous_local_pipeline`을 문구·이미지 승인으로 바꾸지 않으며 반환된 `needs_user`·`blocked`를 유지한다.

## 제목·썸네일 수정

수정 전 정확한 이전 산출물을 기존 archive 절차로 보존한다. `scripts/revise_thumbnail_package.py <VIDEO_JOB.json> --scope title|copy|image --revision <새 번호>`의 dry-run을 확인하고 `--apply`로 해당 단계와 업로드 패키지만 무효화한다. 제목만 수정하면 문구·이미지 승인은 유지하고 제목 승인과 역할 검토를 다시 수행한다. 문구 수정은 문구·생성·시각 승인을, 이미지 수정은 생성·시각 승인을 다시 확인한다. 영상·자막·리서치가 독립적으로 유효하면 완료 상태를 유지한다.

사용자 결정은 기존 정책에 따라 판정하고 패키지에 기록한다. `needs_user`에는 기다리는 정확한 영상 단계와 결정 대상을 `note`·`next_action`으로 남긴다. 재개 시 현재 승인과 실제 산출물을 확인해 첫 미완료 단계부터 이어간다. 새 승인을 추정하거나 Core의 대화 해석 규칙을 이 스킬에서 다시 정의하지 않는다.

수정 후 문구·이미지 검수, 승인 포함 검증, 수동 패키지의 제목·해시 갱신을 완료한다. 새 제작은 `--require-editorial`을 포함한다. 최종 처리는 `$prepare-youtube-upload`의 `finalize_upload_package.py <package.json> --require-publish-timing`으로 검증한 뒤 `--apply`를 추가해 가이드 생성·archive 적용 후 재검증까지 실행하고 job을 완료한다. 추천 시각이 지났다면 공개 시간 분석을 갱신한 뒤 진행한다.

## 최종 output 파일

최종 파일의 구성과 archive 검증은 [업로드 준비 스킬](../../prepare-youtube-upload/SKILL.md)을 따른다. 총괄은 현재 job의 최종 가이드와 네 입력의 해시·승인 결속 및 반환된 정리 후 검증을 확인한다. 파일 생성·정리 방법을 별도로 재구현하지 않는다.

## 완료

다음을 모두 충족할 때만 job을 `complete`, `next_action`을 `none`으로 기록한다.

- 다섯 단계 `complete`
- 현재 영상·SRT에 대한 `content_review.status: reviewed`, 미해결 중대 오류 0, 공개할 경미한 한계가 최종 설명란·가이드에 반영됨
- worktree와 작업 기록 검증 통과
- 제목·썸네일 승인 포함 검증 통과
- `VIDEO_JOB.json`의 `thumbnail_contract`와 제목·썸네일 패키지의 생성·승인 계약 일치
- 수동 패키지 errors·warnings 0, `external_actions: none`
- 새 제작·패키지 재완료는 `--require-publish-timing` 검증 통과, 가이드에 현재 유효한 추천 공개 시간과 분석 근거·한계가 포함됨
- 수동 패키지에 기록된 네 입력 해시가 현재 영상·썸네일·SRT·제목·썸네일 패키지와 일치
- archive 적용 후 output 파일 네 개와 archive 재검증 통과

최종 보고에는 job ID, root·branch, 최종 제목, 네 output 파일, archive와 검증 결과를 반환한다. 실제 YouTube 업로드·게시·공개 범위 변경이나 결과 확인은 하지 않는다.

## Claude 실행 경로

Codex는 위 절차를 그대로 쓴다. Claude(Cowork)는 같은 단계·승인·검증을 지키고 실행 수단만 다음처럼 바꾼다.

- 연결 폴더: 사용자 PC의 main `Creator` 하나를 연결한다. 영상 데이터도 그 안의 명시된 job 폴더를 사용한다.
- 실행 환경: 연결 폴더 셸(`device_bash`)은 매 호출이 새 셸이다. 모든 호출 앞에 `source "$HOME/mnt/Creator/.agents/skills/coordinate-video-production/scripts/claude_runtime.sh"`를 붙인다. 이 helper는 Windows worktree 경로를 마운트 경로로 바꾸는 git shim과 `CREATOR_HOST_PATH_MAP`을 설정해, 작업 기록의 `execution_context.worktree.root`가 Codex와 같은 Windows 경로로 남게 한다.
- 이 셸에서는 Windows worktree가 `prunable`로 보인다. `git worktree prune`·`repair`·`remove`를 실행하지 않는다.
- 명령 변환: PowerShell 블록은 bash로, `python`은 `python3`로 바꾼다. `workdir=$activeRoot`는 매 호출의 `cd "<active_root>"`이며, 활성화 결과의 `active_root`(마운트 경로)에서 실행하고 보고에는 `active_host_root`를 함께 쓴다.
- 하위 스킬: `$skill-name`은 활성 root의 `.agents/skills/<skill-name>/SKILL.md`를 읽어 수행한다. 각 스킬의 「Claude 실행 경로」가 있으면 그 절을 따른다.
- 브라우저: `cua_repl` 대신 `$connect-chrome-profile`의 Claude 실행 경로(Claude in Chrome, `verification_method: claude_in_chrome_device`)를 사용한다. NotebookLM 하위 단계의 탭 조작도 같은 Chrome 탭에서 Claude in Chrome 도구로 수행한다.
- 장시간 작업: 셸 호출은 약 180초에 종료되고 백그라운드 프로세스도 함께 종료된다. 오래 걸리는 처리는 하위 스킬의 Claude 경로가 정한 클라우드 작업공간에서 실행한다.
