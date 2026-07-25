# Video job format

`VIDEO_JOB.json`은 영상 하나의 단계 상태와 검증된 산출물만 기록한다. 비밀번호, 쿠키, 토큰, 계정 주소 또는 브라우저 프로필 파일을 기록하지 않는다.

```json
{
  "schema_version": "video-job-v1",
  "job_id": "2026-07-25-example-topic",
  "topic": "영상 주제",
  "status": "active",
  "browser": {
    "surface": "chrome",
    "profile_label": "Profile 4",
    "profile_directory": "Profile 4",
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

## Status rules

- Job status: `active`, `needs_user`, `blocked`, `complete`.
- Stage status: `pending`, `in_progress`, `needs_user`, `blocked`, `complete`.
- `stages`에는 `research`, `video`, `captions`, `title_thumbnail`, `upload_package` 다섯 키만 이 순서대로 둔다.
- Browser surface는 `chrome`, 기본 `profile_label`과 `profile_directory`는 `Profile 4`, `connection_scope`는 `browser_runtime`이다.
- Browser status: `needs_connection`, `connected`, `needs_user`, `unavailable`.
- `verification_method`는 `same_runtime`, `explicit_tab_mention`, `profile_targeted_launch` 중 검증에 사용한 값을 기록한다.
- 같은 Codex 작업의 살아 있는 브라우저 런타임에서는 검증된 바인딩을 재사용한다. 새 Codex 작업 또는 새 브라우저 런타임에서는 저장 상태와 관계없이 연결을 다시 확인한다.
- `profile_label`과 `profile_directory`에는 `Profile 4` 같은 안전한 식별자만 저장한다. 전체 프로필 경로, 브라우저 ID, 확장 인스턴스 ID, 계정 주소, 쿠키, 토큰, 로컬 저장소 또는 비밀번호는 저장하지 않는다.
- `$connect-chrome-profile`이 공식 복구 절차를 완료하기 전에는 Browser 또는 Job status를 `needs_user`로 바꾸지 않는다.
- At most one stage may be `in_progress`, `needs_user`, or `blocked`.
- A stage may become `complete` only after its artifacts and validation summary are recorded.
- Later stages remain `pending` until every earlier stage is `complete`.
- Job status가 `complete`이면 `next_action`은 정확히 `none`이다. 수동 YouTube 업로드와 그 결과 확인은 job 밖의 사용자 작업이다.
- `updated_at` uses an ISO 8601 timestamp with timezone.
- Local paths are repository-relative. URLs are allowed only for NotebookLM artifacts and source records.

생성·변경 후 아래 명령을 실행한다.

```powershell
python .agents/skills/coordinate-video-production/scripts/validate_video_job.py `
  extension/work/<job-id>/VIDEO_JOB.json
```

다음 단계 시작과 전체 완료 처리에는 검증 결과 `status: valid`가 필요하다.
