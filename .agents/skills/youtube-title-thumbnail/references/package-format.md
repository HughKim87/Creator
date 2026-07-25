# YouTube title-thumbnail package v1

런타임 폴더에 UTF-8 JSON으로 저장한다. 상대 경로는 JSON 파일이 있는 폴더를 기준으로 해석한다.

```json
{
  "schema_version": "youtube-title-thumbnail-v1",
  "source": {
    "video": "video.mp4",
    "captions": "captions.srt",
    "channel_evidence": {
      "status": "verified",
      "note": "최근 공개 영상 10개의 제목과 썸네일을 확인함"
    }
  },
  "title": {
    "selected": "검색어가 앞에 있는 40~65자 제목",
    "status": "draft",
    "candidates": [
      {
        "text": "후보 제목",
        "angle": "comparison"
      }
    ],
    "rationale": "영상의 핵심 비교와 실무 이득을 함께 약속함"
  },
  "thumbnail": {
    "background": "../../work/example-job/thumbnail-background.png",
    "master": "../../work/example-job/thumbnail.png",
    "upload": "thumbnail.jpg",
    "mobile_preview": "../../work/example-job/thumbnail-preview-320.jpg",
    "text": [
      "첫 문구",
      "둘째 문구",
      "강조 문구"
    ],
    "badge": "짧은 보조 문구",
    "generation_prompt": "글자 없는 배경을 만든 최종 프롬프트"
  },
  "validation": {
    "facts_traceable": true,
    "mobile_preview_reviewed": true,
    "user_approved": false
  }
}
```

최종 output 폴더를 간결하게 유지하려면 배경·마스터·모바일 미리보기는 `work/<job-id>/`에 두고, `outputs/<job-id>/`에는 업로드 이미지와 승인 패키지만 둔다. 상대 경로는 패키지 JSON이 있는 폴더를 기준으로 해석한다.

`channel_evidence.status`는 다음 중 하나다.

- `verified`: 실제 채널 자료를 확인함
- `unavailable`: 제공된 연결 복구 후에도 접근하지 못함
- `not_provided`: 채널 근거가 작업 범위에 없었음

제목 후보는 최소 5개를 넣는다. `title.status`는 사용자 승인 전 `draft`, 명시적 승인 후 `approved`다. 자동 검증이 통과해도 `validation.user_approved`를 자동으로 `true`로 바꾸지 않는다.
