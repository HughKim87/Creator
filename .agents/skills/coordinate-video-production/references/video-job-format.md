# Video job format v3

## End-to-end automation policy

Creative delegation is decided only by the active project policy clause `creator-video-creative-delegation-v1`. This format records that decision; it does not define trigger phrases. When the clause applies, record `execution_mode: autonomous_local_pipeline`, `thumbnail_contract.approval_mode: delegated_by_user`, and `thumbnail_contract.instruction_source: explicit_user`, with the clause ID retained as the semantic authority. Otherwise record `review_gated` and do not infer delegation from the execution mode.

새 작업은 `video-job-v3`를 사용한다. 작업 기록은 영상 하나의 단계, 실행 worktree, 썸네일 생성·승인 계약과 검증된 산출물만 기록한다.

```json
{
  "schema_version": "video-job-v3",
  "job_id": "2026-07-25-example-topic",
  "topic": "영상 주제",
  "status": "active",
  "execution_mode": "review_gated",
  "thumbnail_contract": {
    "generation_mode": "one_shot_imagegen",
    "allow_local_text_composite": false,
    "approval_mode": "review_gated",
    "instruction_source": "explicit_user"
  },
  "execution_context": {
    "worktree": {
      "root": "C:/absolute/path/to/worktree",
      "branch": "codex/ainotebook",
      "expected_branch": "codex/ainotebook",
      "status": "valid",
      "checked_at": "2026-07-25T00:00:00+09:00"
    }
  },
  "browser": {
    "surface": "chrome",
    "profile_label": "<optional-profile-label>",
    "profile_directory": "<required-profile-directory>",
    "required_origin": "https://notebooklm.google.com",
    "connection_scope": "browser_runtime",
    "status": "needs_connection",
    "verification_method": "",
    "last_verified_at": ""
  },
  "paths": {
    "work_dir": "extension/work/2026-07-25-example-topic",
    "input_dir": "extension/inputs/2026-07-25-example-topic",
    "output_dir": "extension/outputs/2026-07-25-example-topic"
  },
  "stages": {
    "research": {
      "status": "pending",
      "skill": "notebooklm-research-topic",
      "artifacts": [],
      "validation": "",
      "note": ""
    },
    "video": {
      "status": "pending",
      "skill": "notebooklm-generate-video",
      "artifacts": [],
      "playback_check": null,
      "validation": "",
      "note": ""
    },
    "captions": {
      "status": "pending",
      "skill": "video-to-srt",
      "artifacts": [],
      "validation": "",
      "note": ""
    },
    "title_thumbnail": {
      "status": "pending",
      "skill": "youtube-title-thumbnail",
      "artifacts": [],
      "validation": "",
      "note": ""
    },
    "upload_package": {
      "status": "pending",
      "skill": "prepare-youtube-upload",
      "artifacts": [],
      "validation": "",
      "note": ""
    }
  },
  "next_action": "Run notebooklm-research-topic",
  "updated_at": "2026-07-25T00:00:00+09:00"
}
```

## 실행 컨텍스트

- 새 작업의 browser 값은 `resolve_browser_profile.py`로 확정한다. 스킬 호출에 profile directory나 alias가 있으면 입력값을, 없으면 Git에서 제외된 worktree-local `extension/.runtime/video-workflow-defaults.json`을 사용한다.
- resolver 결과를 `VIDEO_JOB.json`에 현재 작업값으로 기록하고 runtime 기본값과 `SESSION_HANDOFF.md`는 수정하지 않는다.
- 진행 중 작업의 하위 단계는 `VIDEO_JOB.json`의 값을 사용한다. 사용자가 작업 프로필 변경을 명시한 경우에만 resolver 결과로 현재 작업값을 갱신한다.
- `connect-chrome-profile`과 하위 단계 스킬은 프로필 기본값을 소유하지 않고 이 작업 기록의 확정값만 받는다.
- `browser.profile_label`은 선택적 표시명이다. 별도 입력이 없으면 `profile_directory`와 같은 값을 기록한다.
- 위 JSON의 꺾쇠 placeholder는 실제 작업을 만들 때 확정값으로 교체한다.
- `execution_mode`는 `autonomous_local_pipeline` 또는 `review_gated`다. 이 값은 단계 사이의 자동 진행만 제어하며 창작 승인 권한을 부여하지 않는다.
- `thumbnail_contract.generation_mode`는 `one_shot_imagegen` 또는 `local_text_composite`다.
- `thumbnail_contract.allow_local_text_composite`는 불리언이다. 웹 ChatGPT와 같은 완성형 생성을 요구받으면 `false`다.
- `thumbnail_contract.approval_mode`는 `review_gated` 또는 `delegated_by_user`이며 활성 정책의 `creator-video-creative-delegation-v1` 판정을 그대로 기록한다.
- `thumbnail_contract.instruction_source`는 `explicit_user` 또는 `default`다. `delegated_by_user`의 의미 권위는 활성 정책의 `creator-video-creative-delegation-v1`이며, 로컬 합성 허용은 별도의 명시적 사용자 지시를 기록한다.
- `check_worktree.py --root .`의 `status`, `root`, `branch`, `expected_branch`를 그대로 기록한다.
- 새 작업 생성 전과 단계 전환 전에 다시 검증하고 `checked_at`을 갱신한다.
- v2 검증기는 현재 root·branch와 기록이 다르면 실패한다.
- NotebookLM 단계가 시작되거나 완료된 경우 browser는 `connected`여야 하고 검증 방법과 시간대 포함 시각이 있어야 한다.
- 계정 주소, 쿠키, 토큰, 브라우저 ID, 확장 인스턴스 ID와 전체 프로필 파일 경로는 기록하지 않는다.

## 단계와 산출물

- 단계와 skill 이름은 정의된 다섯 개를 정확히 사용한다.
- 완료 단계에는 실제 존재하는 로컬 산출물 또는 NotebookLM URL과 검증 요약이 있어야 한다.
- `video` 완료 시 `playback_check`를 `{ "elapsed_seconds": 17.0, "progressed": true, "paused": true }` 형식으로 기록한다. 경과 시간은 0초보다 크고 30초 이하여야 한다.
- `title_thumbnail` 완료에는 승인된 레거시 패키지 또는 작업의 `thumbnail_contract`와 일치하고 문구·생성·시각 승인을 모두 받은 v3 패키지가 필요하다.
- `upload_package` 완료에는 준비 패키지와 수동 업로드 가이드가 필요하다.
- v3 수동 업로드 패키지는 영상·썸네일·SRT·제목·썸네일 패키지의 SHA-256을 기록하고 현재 파일과 일치해야 한다.
- v2 최종 output은 MP4·썸네일·SRT·가이드 네 파일만 포함한다.

상태 규칙은 기존과 같다. job은 `active`, `needs_user`, `blocked`, `complete`; stage는 `pending`, `in_progress`, `needs_user`, `blocked`, `complete`다. 한 번에 하나의 stage만 활성 상태일 수 있고 앞 단계가 완료되기 전에는 뒤 단계가 `pending`이어야 한다.

생성·변경 후 다음을 실행한다.

```powershell
python .agents/skills/coordinate-video-production/scripts/validate_video_job.py `
  extension/work/<job-id>/VIDEO_JOB.json `
  --root . `
  --check-artifacts
```

다음 단계 시작과 전체 완료에는 `status: valid`, `worktree.status: valid`가 필요하다. 기존 `video-job-v1`·`video-job-v2`는 읽기·검증 호환만 유지한다.
