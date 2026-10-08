---
name: coordinate-video-production
description: 영상 하나의 NotebookLM 리서치·동영상 생성·SRT·문구 승인 기반 제목과 썸네일·사용자용 네 파일만 남기는 수동 YouTube 업로드 준비 단계를 검증된 worktree에서 관리한다. 사용자가 새 영상 제작, 진행 중 작업의 다음 단계, 여러 단계를 끝까지 진행하거나 영상 제작 스킬의 안전한 연결을 요청할 때 사용한다.
---

# Coordinate Video Production

## Default end-to-end delegation

Creative delegation is owned only by the active project policy clause `creator-video-creative-delegation-v1`. This skill does not define or override delegation triggers. When that clause applies, record `execution_mode: autonomous_local_pipeline`, `thumbnail_contract.approval_mode: delegated_by_user`, and `thumbnail_contract.instruction_source: explicit_user`; use the clause ID as the semantic authority, choose the reversible local title and thumbnail elements, and continue through `prepare-youtube-upload`. When the clause does not apply, use `review_gated`. A later explicit review request changes only the named stage as defined by the same clause.

영상별 상태를 관리하고 다섯 제작 스킬을 순서대로 연결한다. 단계 작업은 해당 스킬에 맡긴다.

## 첫 실행 게이트

이 게이트는 영상 제작·재개에 적용한다. 스킬·Extension 유지보수에서는 사용자가 지정한 개발 브랜치와 root를 사용하며 제작 worktree로 이동하지 않는다.

이 스킬을 읽은 뒤 첫 실행 명령으로 **라우팅된 worktree를 활성 실행 root로 확정**한다. 파일 조회·생성·변경, 브라우저 연결과 작업 기록 판정보다 먼저 실행한다.

```powershell
$activation = python .agents/skills/coordinate-video-production/scripts/activate_worktree.py `
  --root . | ConvertFrom-Json
if ($activation.status -ne 'valid') { throw ($activation | ConvertTo-Json -Depth 8) }
$activeRoot = $activation.active_root
$activeBranch = $activation.active_branch
```

- 사용자가 이번 요청에서 다른 브랜치를 명시한 경우에만 `--expected-branch`로 덮어쓴다. 현재 브랜치를 기대값으로 채우지 않는다.
- 초기 검사에 `expected_root`가 있으면 활성화 스크립트가 그 경로를 다시 검증한 `active_root`만 사용한다.
- `activate_worktree.py`가 `redirected: true`를 반환하면 `active_root`가 스킬의 **유일한 작업 기준**이다. 이후 모든 셸 명령은 `workdir=$activeRoot`로 실행하고, 모든 상대 경로·작업 기록·검증 명령은 `$activeRoot`를 기준으로 해석한다.
- `active_root`를 확보한 뒤에는 원래 세션 cwd의 파일을 다시 조회하지 않는다. `.`를 원래 cwd를 뜻하는 상태로 사용하지 않는다.
- `active_root`의 재검증이 `valid`가 아니면 영상 파일이나 브라우저를 만지지 않는다. `main`으로 대체하지 않는다.
- 유효한 대상 root의 `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`를 `$activeRoot`에서 읽는다.
- 대상 handoff가 비-NotebookLM 작업이고 이 스킬을 owner에서 제외하면 그 작업을 영상 단계로 승계하지 않는다.
- 셸의 `Set-Location`이나 한 번의 명령에 지정한 `workdir`는 부모 Codex 세션의 cwd를 영구 변경하지 않을 수 있다. 따라서 “현재 세션이 전환됐다”고 추정하지 말고, 최종 보고에는 `workflow root`와 `workflow branch`를 명시한다. 실제 앱 세션 cwd를 별도로 확인하지 않았다면 이를 “현재 워크트리”라고 표현하지 않는다.
- 최종 보고에 검증한 절대 root와 branch, 그리고 `redirected` 여부를 포함한다.

## 작업 기록

진행 중 영상은 지정된 작업의 `VIDEO_JOB.json`을 먼저 확인하고 기존 browser·완료 단계·승인 범위를 재사용한다. 새 작업용 기본값 해석을 재개 작업에 반복하지 않는다.

지정 worktree가 없으면 누락을 전체 제작 불가로 보고하지 않는다. 승인된 제작 범위 안에서 route의 정확한 root·branch, 기존 브랜치와 로컬 기준 ref를 확인하고 충돌 없는 경로에 생성한 뒤 활성화 검사를 재실행한다. 기준 ref가 불명확하거나 기존 경로가 다른 데이터이면 생성하지 않고 그 결정만 확인한다. 다른 작업의 runtime 파일을 임의 검색·복사하거나 빈 디렉터리를 검증된 worktree로 간주하지 않는다.

[references/video-job-format.md](references/video-job-format.md)에 따라 새 작업마다 `extension/work/<job-id>/VIDEO_JOB.json`을 만든다.

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
- 새 작업은 `video-job-v3`를 사용하고 worktree 검증 결과를 `execution_context`에 기록한다.
- `execution_mode`는 `autonomous_local_pipeline` 또는 `review_gated`로 기록한다.
- `execution_mode`는 단계 사이의 자동 진행만 제어한다. 제목·문구·이미지·최종 시각의 승인 권한을 부여하지 않는다.
- `thumbnail_contract`에 `generation_mode`, `allow_local_text_composite`, `approval_mode`, `instruction_source`를 기록한다. `approval_mode`와 위임 근거는 활성 정책의 `creator-video-creative-delegation-v1` 판정에서만 가져오며, 이 스킬이 사용자 표현을 별도로 재해석하지 않는다.
- 사용자가 웹 ChatGPT와 같은 생성을 요구하면 `generation_mode: one_shot_imagegen`, `allow_local_text_composite: false`, `instruction_source: explicit_user`로 기록한다.
- 기술 패키지와 생성 원본은 `work/<job-id>/`, 최종 사용자 파일은 `outputs/<job-id>/`에 둔다.
- `.gitignore`나 추적 정책을 임의로 바꾸지 않는다.

작업 기록 생성·변경 직후와 각 단계 시작 전에 실행한다.

```powershell
python .agents/skills/coordinate-video-production/scripts/validate_video_job.py `
  extension/work/<job-id>/VIDEO_JOB.json `
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

- Chrome 초기 선택 권한은 `$connect-chrome-profile`에만 있다. fresh 런타임에서는 이 스킬을 browser runtime bootstrap보다 먼저 실행한다. 이 스킬과 하위 NotebookLM 스킬은 연결 전후에 `agent.browsers.get("extension")`, `getDefault()`, `getForUrl()`로 브라우저를 다시 선택하지 않는다.
- `connected`와 검증 방법을 반환할 때만 NotebookLM 단계를 시작한다.
- 반환된 exact Chrome 바인딩과 검증 탭만 하위 단계에 넘긴다. 같은 런타임의 검증 바인딩은 probe 성공 시 재사용하고, 명시적 unavailable·disconnected 오류나 새 런타임에서는 `$connect-chrome-profile`로 다시 검증한다.
- 내장 브라우저, 다른 프로필, 별도 Playwright, Computer Use와 웹 검색으로 우회하지 않는다.
- 연결 검증 시각을 기록하고 단계 검증기가 확인하게 한다.

## 단계 순서

| 단계 | 스킬 | 완료 근거 |
|---|---|---|
| `research` | `$notebooklm-research-topic` | 노트북 URL과 출처 품질 |
| `video` | `$notebooklm-generate-video` | 완성 영상, 길이, 30초 이내 재생 확인 후 일시정지, 다운로드 상태 |
| `captions` | `$video-to-srt` | MP4, SRT, 원본 전사와 전체 검수 |
| `title_thumbnail` | `$youtube-title-thumbnail` | 승인된 제목·문구·생성·최종 시각과 썸네일 |
| `upload_package` | `$prepare-youtube-upload` | 업로드용 네 파일, 별도 archive와 수동 가이드 |

첫 `pending` 단계만 실행한다. 앞 단계가 모두 `complete`가 아니면 뒤 단계를 시작하지 않는다. 다만 아래의 업로드 가이드 초안은 단계 완료와 별개인 준비 작업으로 허용한다.

## 하위 스킬 호출 계약

하위 스킬에 호출자가 `coordinate-video-production`임을 밝히고 현재 작업 기록 경로, `execution_mode`, 해당 단계의 승인 범위와 검증된 입력을 전달한다. 하위 스킬의 “멈춘다”, “후속 단계 전에 종료한다”는 문구는 단독 호출의 작업 경계다. coordinator 호출에서는 해당 단계의 결과를 반환하며, coordinator가 검증·상태 갱신 후 현재 실행 모드에 따라 이어간다. 하위 스킬을 호출하는 데 별도 Agent 생성은 필요하지 않다.

`autonomous_local_pipeline`에 이미 포함된 다음 단계는 하위 스킬의 반환만을 이유로 다시 승인받지 않는다. 로그인·한도·오류 등 실제 차단, 위임되지 않은 결정, 비용·권한·외부 효과 경계는 그대로 반환하고 해당 상태에서 멈춘다. `review_gated`에서는 기존 단계별 승인 경계를 유지한다.

## 업로드 가이드 초안

사용자가 가이드를 먼저 요청하거나 썸네일 단계가 대기·차단된 경우, 확보한 영상·SRT·제목·근거로 `$prepare-youtube-upload`의 초안 경로를 실행할 수 있다. 작업 폴더에 `YOUTUBE-MANUAL-UPLOAD-DRAFT.md`를 만들고 미확정 제목·썸네일·내용 검수 등 남은 항목을 표시한다. 확인되지 않은 항목은 확정하지 않는다.

초안은 `upload_package.note`에 경로와 미완성 항목만 기록한다. 기존 활성 단계·차단 사유·`next_action`을 유지하고 `upload_package`는 `pending`으로 둔다. 초안을 완료 산출물에 넣거나 finalizer·archive를 실행하지 않는다. 최종 조건이 충족되면 현재 자료로 최종 가이드를 새로 생성한다.

## 영상 내용 검수

자막 전체 검수가 끝난 뒤 제목·썸네일 제작 전에 영상의 핵심 사실·비교·선택 권고를 실제 사용한 리서치 근거와 대조한다. `content_review`에 검수한 MP4·SRT 경로와 해시, 검토 범위, 발견한 주장 위치·근거·처리 결과를 [작업 기록 형식](references/video-job-format.md#영상-내용-검수-기록)에 따라 기록한다. 기계 검사는 기록·해시·완료 조건을 확인하며 주장 자체의 진위를 대신 판정하지 않는다.

결제·제품 선택·기능 이해·영상 결론을 바꿀 수 있는 사실 오류나 근거 없는 핵심 단정은 `material`, 그 밖의 표현 한계는 `minor`로 분류하고 이유를 남긴다. 중대한 오류는 영상 수정 또는 실제 근거 재확인으로 해결한다. 설명란 주의 문구, 사용자 승인, SRT만의 사실 교정으로 해결 처리하지 않는다. 경미한 한계는 정확한 정정·범위를 최종 설명란과 가이드에 공개할 수 있다.

미해결 중대 오류가 있으면 `title_thumbnail`을 `blocked`로 두고 job의 차단 사유와 수정 행동을 기록한다. 기술적으로 완료된 영상·자막 단계는 유지한다. 검수 미완료도 제목·썸네일 제작 전에 해결한다. 내용 수정에 별도 권한·비용이 필요하면 그 결정만 요청한다. 영상·SRT 변경 시 검수 해시와 영향받는 제목·썸네일·수동 패키지를 다시 확인한다.

새 작업에는 `content_review`를 포함한다. 기존 기록의 읽기·검증 호환은 유지하되, 이 스킬로 제작을 재개하거나 패키지를 다시 완료할 때 기록이 없으면 `pending` 검수를 추가한다. 이미 제목·썸네일과 업로드 단계가 완료였다면 파일·승인 근거를 보존한 채 해당 단계만 `pending`, job은 `active`로 되돌리고 내용 검수부터 수행한다. 과거의 기술 검증 결과를 내용 검수 완료로 변환하지 않는다.

## 실행과 승인

1. 실제 산출물과 작업 기록을 확인한다.
2. 활성·사용자 대기·차단 단계가 있으면 그 상태부터 확인한다. 후속 단계는 차단을 해결한 뒤 실행하며, 가이드 초안 요청은 위 초안 경로로 처리할 수 있다.
3. 다음 스킬 하나만 실행하고 산출물을 검증한다.
4. 검증 후에만 단계 상태와 경로를 갱신한다.
5. `autonomous_local_pipeline`이면 검증 직후 다음 `pending` 단계로 계속한다. `needs_user`, `blocked`, `complete` 또는 아래 외부 경계에 도달할 때만 멈춘다. 대기·차단 상태에서 가이드 초안을 준비할 수 있으면 이를 반환한 뒤 해당 상태를 유지한다.

`thumbnail_contract.approval_mode: review_gated`의 썸네일 단계는 다음 순서를 강제한다.

`문구 후보 → 문구 승인 → 이미지 생성 승인 → 완성형 생성 → 최종 시각 승인`

`thumbnail_contract.approval_mode: delegated_by_user`는 활성 정책의 `creator-video-creative-delegation-v1` 판정이 작업 기록에 남은 경우에만 사용한다. 이때 해당 창작 선택을 `delegated_by_user`로 기록한다. `autonomous_local_pipeline`이어도 `approval_mode: review_gated`이면 썸네일 단계에서 `needs_user`로 멈춘다.

창작 위임의 의미는 활성 정책의 `creator-video-creative-delegation-v1`이 소유하고, 생성 모드와 패키지 기록 형식은 `$youtube-title-thumbnail`의 `references/package-format.md`가 소유한다.

## 제목·썸네일 수정

수정 전 정확한 이전 산출물을 기존 archive 절차로 보존한다. `scripts/revise_thumbnail_package.py <VIDEO_JOB.json> --scope title|copy|image --revision <새 번호>`의 dry-run을 확인하고 `--apply`로 해당 단계와 업로드 패키지만 무효화한다. 제목만 수정하면 문구·이미지 승인은 유지하고 제목 승인과 역할 검토를 다시 수행한다. 문구 수정은 문구·생성·시각 승인을, 이미지 수정은 생성·시각 승인을 다시 확인한다. 영상·자막·리서치가 독립적으로 유효하면 완료 상태를 유지한다.

사용자 결정은 기존 정책에 따라 판정하고 패키지에 기록한다. `needs_user`에는 기다리는 정확한 영상 단계와 결정 대상을 `note`·`next_action`으로 남긴다. 재개 시 현재 승인과 실제 산출물을 확인해 첫 미완료 단계부터 이어간다. 새 승인을 추정하거나 Core의 대화 해석 규칙을 이 스킬에서 다시 정의하지 않는다.

수정 후 문구·이미지 검수, 승인 포함 검증, 수동 패키지의 제목·해시 갱신을 완료한다. 새 제작은 `--require-editorial`을 포함한다. 최종 처리는 `$prepare-youtube-upload`의 `finalize_upload_package.py`로 가이드 생성·archive 적용 후 재검증까지 실행한 뒤 job을 완료한다.

## 최종 output 파일

수동 가이드를 만든 뒤 `$prepare-youtube-upload`의 archive dry-run을 확인하고 적용한다. 파일을 삭제하지 않는다.

완료 시 `outputs/<job-id>/`에는 정확히 다음만 남긴다.

- MP4 영상
- 최종 썸네일
- SRT 자막
- `YOUTUBE-MANUAL-UPLOAD.md`

기술 JSON, 설명 원본, 전사·검수 기록, 생성 원본과 이전 썸네일은 `work/<job-id>/` 또는 `work/<job-id>/archive/`에 둔다.

## 완료

다음을 모두 충족할 때만 job을 `complete`, `next_action`을 `none`으로 기록한다.

- 다섯 단계 `complete`
- 현재 영상·SRT에 대한 `content_review.status: reviewed`, 미해결 중대 오류 0, 공개할 경미한 한계가 최종 설명란·가이드에 반영됨
- worktree와 작업 기록 검증 통과
- 제목·썸네일 승인 포함 검증 통과
- `VIDEO_JOB.json`의 `thumbnail_contract`와 제목·썸네일 패키지의 생성·승인 계약 일치
- 수동 패키지 errors·warnings 0, `external_actions: none`
- 수동 패키지에 기록된 네 입력 해시가 현재 영상·썸네일·SRT·제목·썸네일 패키지와 일치
- archive 적용 후 output 파일 네 개와 archive 재검증 통과

최종 보고에는 job ID, root·branch, 최종 제목, 네 output 파일, archive와 검증 결과를 반환한다. 실제 YouTube 업로드·게시·공개 범위 변경이나 결과 확인은 하지 않는다.
