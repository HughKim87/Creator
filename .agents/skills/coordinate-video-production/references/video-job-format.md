# Video job format v2

새 작업은 `video-job-v2`를 사용한다. 작업 기록은 영상 하나의 단계, 실행 worktree와 검증된 산출물만 기록한다.

```json
{
  "schema_version": "video-job-v2",
  "job_id": "2026-07-25-example-topic",
  "topic": "영상 주제",
  "status": "active",
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

## 실행 컨텍스트

- `check_worktree.py --root .`의 `status`, `root`, `branch`, `expected_branch`를 그대로 기록한다.
- 새 작업 생성 전과 단계 전환 전에 다시 검증하고 `checked_at`을 갱신한다.
- v2 검증기는 현재 root·branch와 기록이 다르면 실패한다.
- NotebookLM 단계가 시작되거나 완료된 경우 browser는 `connected`여야 하고 검증 방법과 시간대 포함 시각이 있어야 한다.
- 계정 주소, 쿠키, 토큰, 브라우저 ID, 확장 인스턴스 ID와 전체 프로필 파일 경로는 기록하지 않는다.

## 단계와 산출물

- 단계와 skill 이름은 정의된 다섯 개를 정확히 사용한다.
- 완료 단계에는 실제 존재하는 로컬 산출물 또는 NotebookLM URL과 검증 요약이 있어야 한다.
- `title_thumbnail` 완료에는 승인된 v1 패키지 또는 문구·생성·시각 승인을 모두 받은 v2 패키지가 필요하다.
- `upload_package` 완료에는 준비 패키지와 수동 업로드 가이드가 필요하다.
- v2 최종 output은 MP4·썸네일·SRT·가이드 네 파일만 포함한다.

상태 규칙은 기존과 같다. job은 `active`, `needs_user`, `blocked`, `complete`; stage는 `pending`, `in_progress`, `needs_user`, `blocked`, `complete`다. 한 번에 하나의 stage만 활성 상태일 수 있고 앞 단계가 완료되기 전에는 뒤 단계가 `pending`이어야 한다.

생성·변경 후 다음을 실행한다.

```powershell
python .agents/skills/coordinate-video-production/scripts/validate_video_job.py `
  extension/work/<job-id>/VIDEO_JOB.json `
  --root . `
  --check-artifacts
```

다음 단계 시작과 전체 완료에는 `status: valid`, `worktree.status: valid`가 필요하다. 기존 `video-job-v1`은 읽기·검증 호환만 유지한다.
