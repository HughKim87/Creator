# Manual upload package

Resolve artifact paths relative to the JSON package directory. `existing_upload` is optional and must be used only to prevent accidental duplicate uploads.

```json
{
  "schema_version": "youtube-manual-upload-v1",
  "channel": {
    "name": "Channel name",
    "id": "UC..."
  },
  "artifacts": {
    "video": "video.mp4",
    "thumbnail": "thumbnail.jpg",
    "captions": "captions.ko.srt",
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
    "keep_files": ["description.ko.md"]
  },
  "existing_upload": {
    "video_id": "optional",
    "visibility": "private",
    "note": "Do not upload a duplicate."
  }
}
```

`preparation.keep_files` is optional. When present, each path is resolved relative to the package and is retained by the safe output cleanup script together with the package, generated guide, and four referenced artifacts.

Do not add external-action approvals or browser profile fields. This package authorizes local preparation only.
