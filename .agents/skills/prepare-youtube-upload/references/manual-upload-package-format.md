# Manual upload package v2

새 작업은 기술 패키지를 `extension/work/<job-id>/youtube-manual-upload.json`에 저장한다. 상대 경로는 패키지 폴더를 기준으로 해석하며 모든 경로는 프로젝트 루트 안에 있어야 한다.

```json
{
  "schema_version": "youtube-manual-upload-v2",
  "channel": {
    "name": "Channel name"
  },
  "artifacts": {
    "video": "../../outputs/example-job/video.mp4",
    "thumbnail": "../../outputs/example-job/thumbnail.jpg",
    "captions": "../../outputs/example-job/captions.ko.srt",
    "title_thumbnail_package": "youtube-title-thumbnail.json"
  },
  "metadata": {
    "title": "Video title",
    "description": "Video description",
    "language": "ko",
    "caption_language": "ko",
    "category": "교육",
    "playlist": "Optional playlist name",
    "made_for_kids": false,
    "visibility_recommendation": "private"
  },
  "preparation": {
    "status": "ready",
    "youtube_actions": "manual_by_user",
    "output_dir": "../../outputs/example-job",
    "guide": "../../outputs/example-job/YOUTUBE-MANUAL-UPLOAD.md",
    "archive_dir": "archive",
    "final_output_files": [
      "video.mp4",
      "thumbnail.jpg",
      "captions.ko.srt",
      "YOUTUBE-MANUAL-UPLOAD.md"
    ]
  }
}
```

## 최종 output 계약

`final_output_files`는 사용자가 YouTube Studio에서 선택하거나 복사할 다음 네 파일만 포함한다.

- MP4 영상
- 최종 썸네일
- SRT 자막
- 제목·설명·설정·해시가 포함된 수동 업로드 가이드

기술 JSON, 설명문 원본, 전사 JSON, 검수 기록, 이전 썸네일과 생성 원본은 `outputs`에 남기지 않는다. 활성 기술 파일은 `work/<job-id>/`에 두고, 구형 output 파일은 `archive_dir`로 이동한다. 정리 스크립트는 파일을 삭제하거나 기존 archive 파일을 덮어쓰지 않는다.

기존 `youtube-manual-upload-v1`은 검증과 레거시 정리 호환만 유지한다. 새 작업에는 v2를 사용한다.

채널 ID, placeholder 채널 ID, 외부 작업 승인과 Chrome 프로필 필드는 넣지 않는다. 대상 채널은 사용자가 YouTube Studio에서 직접 확인한다.
