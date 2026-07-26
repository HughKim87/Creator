---
name: coordinate-video-production
description: 영상 하나의 NotebookLM 리서치·동영상 생성·SRT·문구 승인 기반 제목과 썸네일·사용자용 네 파일만 남기는 수동 YouTube 업로드 준비 단계를 검증된 worktree에서 관리한다. 사용자가 새 영상 제작, 진행 중 작업의 다음 단계, 여러 단계를 끝까지 진행하거나 영상 제작 스킬의 안전한 연결을 요청할 때 사용한다.
---

# Coordinate Video Production

영상별 상태를 관리하고 다섯 제작 스킬을 순서대로 연결한다. 단계 작업은 해당 스킬에 맡긴다.

## 첫 실행 게이트

이 스킬을 읽은 뒤 첫 실행 명령으로 **라우팅된 worktree를 활성 실행 root로 확정**한다. 파일 조회·생성·변경, 브라우저 연결과 작업 기록 판정보다 먼저 실행한다.

```powershell
$activation = python .agents/skills/coordinate-video-production/scripts/activate_worktree.py `
  --root . | ConvertFrom-Json
if ($activation.status -ne 'valid') { throw ($activation | ConvertTo-Json -Depth 8) }
$activeRoot = $activation.active_root
$activeBranch = $activation.active_branch
```

- 사용자가 이번 요청에서 다른 브랜치를 명시한 경우에만 `--expected-branch`로 덮어쓴다. 현재 브랜치를 기대값으로 채우지 않는다.
- `activate_worktree.py`가 `redirected: true`를 반환하면 `active_root`가 스킬의 **유일한 작업 기준**이다. 이후 모든 셸 명령은 `workdir=$activeRoot`로 실행하고, 모든 상대 경로·작업 기록·검증 명령은 `$activeRoot`를 기준으로 해석한다.
- `active_root`를 확보한 뒤에는 원래 세션 cwd의 파일을 다시 조회하지 않는다. `.`를 원래 cwd를 뜻하는 상태로 사용하지 않는다.
- `active_root`의 재검증이 `valid`가 아니면 영상 파일이나 브라우저를 만지지 않는다. `main`으로 대체하지 않는다.
- 유효한 대상 root의 `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`를 `$activeRoot`에서 읽는다.
- 대상 handoff가 비-NotebookLM 작업이고 이 스킬을 owner에서 제외하면 그 작업을 영상 단계로 승계하지 않는다.
- 셸의 `Set-Location`이나 한 번의 명령에 지정한 `workdir`는 부모 Codex 세션의 cwd를 영구 변경하지 않을 수 있다. 따라서 “현재 세션이 전환됐다”고 추정하지 말고, 최종 보고에는 `workflow root`와 `workflow branch`를 명시한다. 실제 앱 세션 cwd를 별도로 확인하지 않았다면 이를 “현재 워크트리”라고 표현하지 않는다.
- 최종 보고에 검증한 절대 root와 branch, 그리고 `redirected` 여부를 포함한다.

## 작업 기록

[references/video-job-format.md](references/video-job-format.md)에 따라 새 작업마다 `extension/work/<job-id>/VIDEO_JOB.json`을 만든다.

- 새 작업은 `video-job-v2`를 사용하고 worktree 검증 결과를 `execution_context`에 기록한다.
- `execution_mode`는 `autonomous_local_pipeline` 또는 `review_gated`로 기록한다.
- 사용자가 “수동 업로드 가이드까지 쭉 진행”, “끝까지 진행”, “중간 과정은 알아서 진행”처럼 로컬 제작 전 과정을 맡기면 `autonomous_local_pipeline`을 사용한다. 개별 제목·썸네일 검토를 요청하거나 선택 위임이 불명확하면 `review_gated`를 사용한다.
- 기본 Chrome 프로필 표시명과 디렉터리는 `Profile 4`, 기본 origin은 NotebookLM이다.
- 기술 패키지와 생성 원본은 `work/<job-id>/`, 최종 사용자 파일은 `outputs/<job-id>/`에 둔다.
- `.gitignore`나 추적 정책을 임의로 바꾸지 않는다.

작업 기록 생성·변경 직후와 각 단계 시작 전에 실행한다.

```powershell
python .agents/skills/coordinate-video-production/scripts/validate_video_job.py `
  extension/work/<job-id>/VIDEO_JOB.json `
  --root . `
  --check-artifacts
```

`status: valid`와 `worktree.status: valid`가 아니면 진행하지 않는다.

## Chrome 게이트

`research`와 `video` 전에 작업 기록의 프로필과 origin으로 `$connect-chrome-profile`을 실행한다.

- `connected`와 검증 방법을 반환할 때만 NotebookLM 단계를 시작한다.
- 같은 런타임의 검증 바인딩은 재사용하고 새 런타임에서는 다시 검증한다.
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

첫 `pending` 단계만 실행한다. 앞 단계가 모두 `complete`가 아니면 뒤 단계를 시작하지 않는다.

## 실행과 승인

1. 실제 산출물과 작업 기록을 확인한다.
2. 활성·사용자 대기·차단 단계가 있으면 그 상태부터 해결한다.
3. 다음 스킬 하나만 실행하고 산출물을 검증한다.
4. 검증 후에만 단계 상태와 경로를 갱신한다.
5. `autonomous_local_pipeline`이면 검증 직후 다음 `pending` 단계로 계속한다. `needs_user`, `blocked`, `complete` 또는 아래 외부 경계에 도달할 때만 멈춘다.

`review_gated`의 썸네일 단계는 다음 순서를 강제한다.

`문구 후보 → 문구 승인 → 이미지 생성 승인 → 완성형 생성 → 최종 시각 승인`

`autonomous_local_pipeline`에서는 제목 선정, 썸네일 문구·이미지 생성·최종 시각 선택, 설명·챕터 작성 같은 로컬·가역적 중간 결정을 에이전트가 수행하고 각 승인을 `delegated_by_user`로 기록한다. 이 모드는 결제, 권한 변경, 공유, YouTube 업로드·게시·공개 범위 변경을 승인하지 않는다.

## 최종 output

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
- worktree와 작업 기록 검증 통과
- 제목·썸네일 승인 포함 검증 통과
- 수동 패키지 errors·warnings 0, `external_actions: none`
- archive 적용 후 output 파일 네 개와 archive 재검증 통과

최종 보고에는 job ID, root·branch, 최종 제목, 네 output 파일, archive와 검증 결과를 반환한다. 실제 YouTube 업로드·게시·공개 범위 변경이나 결과 확인은 하지 않는다.
