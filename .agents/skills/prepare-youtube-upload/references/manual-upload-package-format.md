# Manual upload package v3

새 작업은 `youtube-manual-upload-v3` 기술 패키지를 `extension/work/<job-id>/youtube-manual-upload.json`에 저장한다. 상대 경로는 패키지 폴더를 기준으로 해석하며 모든 경로는 프로젝트 루트 안에 있어야 한다.

```json
{
  "schema_version": "youtube-manual-upload-v3",
  "channel": {
    "name": "Channel name"
  },
  "artifacts": {
    "video": "../../outputs/example-job/video.mp4",
    "thumbnail": "../../outputs/example-job/thumbnail.jpg",
    "captions": "../../outputs/example-job/captions.ko.srt",
    "title_thumbnail_package": "youtube-title-thumbnail.json"
  },
  "artifact_hashes": {
    "video": "64자리 SHA-256",
    "thumbnail": "64자리 SHA-256",
    "captions": "64자리 SHA-256",
    "title_thumbnail_package": "64자리 SHA-256"
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

`artifact_hashes`는 가이드 생성과 retention 전에 현재 네 입력과 다시 비교한다. 썸네일이나 제목·썸네일 패키지가 바뀌면 기존 수동 패키지는 즉시 무효이며, `preparation.status`를 `pending`으로 되돌리고 해시와 가이드를 재생성한다.

기존 `youtube-manual-upload-v1`·`youtube-manual-upload-v2`는 검증과 레거시 정리 호환만 유지한다. 새 작업에는 v3를 사용한다.

채널 ID, placeholder 채널 ID, 외부 작업 승인과 Chrome 프로필 필드는 넣지 않는다. 대상 채널은 사용자가 YouTube Studio에서 직접 확인한다.

## 가이드 초안

초안은 최종 패키지 JSON과 별개인 `work/<job-id>/YOUTUBE-MANUAL-UPLOAD-DRAFT.md`다. 다음 내용을 현재 확보한 자료만으로 작성한다.

- 상태: 초안 — 최종 업로드 준비 미완료
- 남은 항목: 제목 승인·썸네일·내용 검수 등 실제 미완성 항목과 다음 행동
- 확보한 파일: 실제 확인한 MP4·SRT 경로. 없는 파일은 `미준비`로 표시
- 제목·설명: 복사할 문구와 각각의 확정/초안 상태. 오류가 남은 주장은 설명의 확정 사실로 반복하지 않음
- 설정: 언어·카테고리·아동용 여부·공개 상태의 확정값 또는 미정 표시. 채널은 Studio에서 직접 확인
- 수동 순서: 채널 확인 → 영상 선택 → 제목·설명 입력 → 완성된 썸네일 선택 → SRT 추가 → 검사·공개 상태 확인. 준비가 끝난 뒤 수행할 절차임을 표시

초안에는 workflow 완료·검증 통과 문구, 존재하지 않는 파일의 경로·해시, 외부 작업 승인 정보를 넣지 않는다. 최종 output 네 파일에는 포함하지 않으며 초안 생성으로 제작 차단이 해소되었다고 기록하지 않는다.
