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
    "required_origin": "https://notebooklm.google.com",
    "connection_scope": "per_session",
    "status": "needs_connection",
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
- Browser surface는 `chrome`, 기본 `profile_label`은 `Profile 4`, `connection_scope`는 `per_session`이다.
- Browser status: `needs_connection`, `connected`, `needs_user`, `unavailable`.
- 새 Codex 작업·대화를 시작하면 저장된 상태와 관계없이 브라우저 연결을 다시 확인한다. 이전 세션의 `connected` 값은 연결 증거가 아니다.
- `profile_label`은 사용자가 보는 안전한 표시명만 저장한다. 프로필 폴더 경로, 계정 주소, 쿠키, 토큰, 로컬 저장소 또는 비밀번호는 저장하지 않는다.
- At most one stage may be `in_progress`, `needs_user`, or `blocked`.
- A stage may become `complete` only after its artifacts and validation summary are recorded.
- Later stages remain `pending` until every earlier stage is `complete`.
- `updated_at` uses an ISO 8601 timestamp with timezone.
- Local paths are repository-relative. URLs are allowed only for NotebookLM artifacts and source records.
