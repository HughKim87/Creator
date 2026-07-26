# YouTube title-thumbnail package v2

새 작업은 기술 패키지를 `extension/work/<job-id>/youtube-title-thumbnail.json`에 UTF-8로 저장한다. 상대 경로는 패키지 파일의 폴더를 기준으로 해석한다. `outputs/<job-id>/`에는 최종 업로드 썸네일만 둔다.

```json
{
  "schema_version": "youtube-title-thumbnail-v2",
  "source": {
    "video": "../../outputs/example-job/video.mp4",
    "captions": "../../outputs/example-job/captions.ko.srt",
    "channel_evidence": {
      "status": "verified",
      "note": "최근 공개 영상의 제목과 썸네일 패턴을 확인함"
    }
  },
  "title": {
    "selected": "검색어가 앞에 있는 40~65자 제목",
    "status": "approved",
    "candidates": [
      {
        "text": "후보 제목",
        "angle": "comparison"
      }
    ],
    "rationale": "영상의 검색 의도와 실무 이득을 약속함"
  },
  "thumbnail": {
    "generation_mode": "one_shot_imagegen",
    "generated_source": "thumbnail-source.png",
    "master": "thumbnail-master.png",
    "upload": "../../outputs/example-job/thumbnail.jpg",
    "mobile_preview": "thumbnail-preview-320.jpg",
    "text": [
      "시청자가 겪는 문제",
      "예상과 다른 핵심 해답"
    ],
    "badge": "영상에서 다룰 범위",
    "copy_strategy": {
      "hook": "시청자가 지금 클릭할 문제나 질문",
      "payoff": "영상이 제공할 구체적인 해답",
      "scope": "제품명·비교 범위·근거"
    },
    "generation_prompt": "승인 문구를 정확히 포함한 완성형 썸네일 프롬프트",
    "generated_at": "2026-07-26T08:00:00+09:00"
  },
  "approval": {
    "copy": {
      "status": "approved",
      "method": "explicit_user",
      "approved_at": "2026-07-26T07:50:00+09:00"
    },
    "image_generation": {
      "status": "approved",
      "method": "explicit_user",
      "approved_at": "2026-07-26T07:55:00+09:00"
    },
    "visual": {
      "status": "approved",
      "method": "explicit_user",
      "approved_at": "2026-07-26T08:05:00+09:00"
    }
  },
  "validation": {
    "facts_traceable": true,
    "text_exact": true,
    "mobile_preview_reviewed": true,
    "clickability_reviewed": true,
    "title_thumbnail_not_duplicate": true
  }
}
```

## 생성 모드

- `one_shot_imagegen`: 기본값. 승인 문구·시각 요소·구도를 완성형 이미지 하나로 생성한다. `generated_source`를 기록한다.
- `local_text_composite`: 사용자가 정확한 로컬 합성을 요청하거나 생성 모델의 문자 오류가 반복되어 사용자가 대체 방식을 승인한 경우에만 사용한다. 이 모드에서는 `generated_source` 대신 `background`와 `font`를 기록한다.

## 승인 계약

- `copy`, `image_generation`, `visual`을 각각 기록한다.
- 상태는 `pending` 또는 `approved`, 방법은 `explicit_user` 또는 `delegated_by_user`다.
- `delegated_by_user`는 사용자가 썸네일 승인 생략이나 임의 확정을 명시한 경우에만 사용한다. “끝까지 진행”이나 일괄 진행은 승인 생략이 아니다.
- 문구 승인과 생성 승인은 `generated_at`보다 빠르거나 같아야 하고, 시각 승인은 생성 이후여야 한다.
- 원문 대화나 계정 정보는 저장하지 않고 안전한 승인 방법과 시각만 기록한다.

`channel_evidence.status`는 `verified`, `unavailable`, `not_provided` 중 하나다. 제목 후보는 최소 5개다. 자동 검증은 사용자 승인을 대신하지 않는다.

기존 `youtube-title-thumbnail-v1`은 검증 호환만 유지한다. 새 작업에는 v2를 사용한다.
