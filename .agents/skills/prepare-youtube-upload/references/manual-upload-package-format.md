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

아래 네 파일 계약은 `preparation.output_dir`에만 적용한다. 동일 job의 복수 최종 결과는 `outputs/upload/`와 `outputs/shorts/` 같은 형제 폴더에 분리한다. `guide`와 video/thumbnail/captions는 upload 폴더 안의 네 파일을 가리킨다. 상대 경로 기준은 기존처럼 패키지 파일의 부모 폴더이며 형제 결과·job 전체를 archive 대상으로 삼지 않는다.

`preparation.archive_files`는 선택적인 파일명 배열이다. 과거 **동일 패키지 소유 중간 결과**를 확인한 경우에만 정확한 이름을 추가한다. 미디어·이미지·자막·ZIP 같은 비최종 결과는 이 목록에 없으면 `unowned_outputs`로 보고하고 이동을 차단한다. 최종 네 파일·경로 이동 문자열·중복 이름은 목록에 허용하지 않는다. 이 필드는 다른 결과물을 정리할 권한을 만들지 않는다.

`final_output_files`는 사용자가 YouTube Studio에서 선택하거나 복사할 다음 네 파일만 포함한다.

- MP4 영상
- 최종 썸네일
- SRT 자막
- 제목·설명·설정·해시가 포함된 수동 업로드 가이드

기술 JSON, 설명문 원본, 전사 JSON, 검수 기록, 이전 썸네일과 생성 원본은 `outputs`에 남기지 않는다. 활성 기술 파일은 `work/<job-id>/`에 두고, 구형 output 파일은 `archive_dir`로 이동한다. 정리 스크립트는 파일을 삭제하거나 기존 archive 파일을 덮어쓰지 않는다.

`artifact_hashes`는 가이드 생성과 retention 전에 현재 네 입력과 다시 비교한다. 썸네일이나 제목·썸네일 패키지가 바뀌면 기존 수동 패키지는 즉시 무효이며, `preparation.status`를 `pending`으로 되돌리고 해시와 가이드를 재생성한다.

기존 `youtube-manual-upload-v1`·`youtube-manual-upload-v2`는 검증과 레거시 정리 호환만 유지한다. 새 작업에는 v3를 사용한다.

채널 ID, placeholder 채널 ID, 외부 작업 승인과 Chrome 프로필 필드는 넣지 않는다. 대상 채널은 사용자가 YouTube Studio에서 직접 확인한다.

## 공개 시간 추천

coordinator의 새 제작·패키지 재완료에는 아래 `publish_timing`을 최상위 필드로 추가한다. 기존 패키지에 없는 경우의 읽기 호환은 유지한다. `--require-publish-timing`은 누락과 현재 기준 이미 지난 추천을 거부하며, 옵션 없이 과거 패키지를 다시 렌더하면 지난 시각이라는 안내를 표시한다. 추천 변경은 이 필드를 갱신하고 가이드를 다시 생성한다.

```json
{
  "publish_timing": {
    "recommended_at": "2026-10-16T08:00:00+09:00",
    "timezone": "Asia/Seoul",
    "basis": "provisional",
    "analytics_status": "insufficient_data",
    "channel_verified": true,
    "checked_at": "2026-10-15T10:00:00+09:00",
    "source": "YouTube Studio → 분석 → 시청자층",
    "period": "화면에 표시된 지난 28일의 시작일 ~ 종료일",
    "audience_activity": "시청자 데이터가 충분하지 않아 이 보고서를 조회할 수 없습니다.",
    "rationale": "뉴스성 소재의 빠른 전달과 사용자가 지정한 아침 공개 조건을 고려한 시험 시간입니다.",
    "limitations": ["시청자 이용 시간대 실측에 근거한 최적 시각은 아닙니다."]
  }
}
```

- 예시 시각은 형식 설명이며 새 영상에 그대로 복사하지 않는다. `recommended_at`·`checked_at`은 UTC offset이 있는 ISO 시각이고, 추천은 확인 시각 이후여야 한다. `timezone`은 실제 offset과 일치하는 IANA 시간대다.
- `basis`: `analytics`는 확인한 이용 시간대 분포를 근거로 한 추천, `provisional`은 데이터 부족·접근 불가 등 한계를 공개한 잠정 추천이다. 둘 다 조회수나 최적 시간을 보장하지 않는다.
- `analytics_status`: `available`, `insufficient_data`, `unavailable`. 데이터가 부족하거나 접근 불가이면 `analytics`를 사용할 수 없다. `unavailable`이면 `period`·`audience_activity`에 확인 불가와 실제 원인을 적고 `limitations`에도 공개한다.
- `channel_verified`: 대상 채널을 대조했는지 여부다. `available`·`insufficient_data`에는 `true`가 필요하다. 채널 ID·이메일·브라우저 식별자 대신 실제 표시 채널명은 `channel.name`에만 기록한다.
- `source`·`period`·`audience_activity`는 실제 확인 범위를, `rationale`는 분포·소재 시의성·사용자 시간 제약을 반영한 판단을 기록한다. 잠정 추천의 `limitations`는 비어 있을 수 없다.
- 이 정보는 가이드의 「추천 공개 시간」에 렌더한다. 업로드 완료를 권하는 시간과 시청자에게 공개하는 시간을 혼동하지 않고, 공개·예약은 사용자가 직접 설정한다. 최종 파일 개수는 네 개로 유지한다.

## 가이드 초안

초안은 최종 패키지 JSON과 별개인 `work/<job-id>/YOUTUBE-MANUAL-UPLOAD-DRAFT.md`다. 다음 내용을 현재 확보한 자료만으로 작성한다.

- 상태: 초안 — 최종 업로드 준비 미완료
- 남은 항목: 제목 승인·썸네일·내용 검수 등 실제 미완성 항목과 다음 행동
- 확보한 파일: 실제 확인한 MP4·SRT 경로. 없는 파일은 `미준비`로 표시
- 제목·설명: 복사할 문구와 각각의 확정/초안 상태. 오류가 남은 주장은 설명의 확정 사실로 반복하지 않음
- 설정: 언어·카테고리·아동용 여부·공개 상태의 확정값 또는 미정 표시. 채널은 Studio에서 직접 확인
- 수동 순서: 채널 확인 → 영상 선택 → 제목·설명 입력 → 완성된 썸네일 선택 → SRT 추가 → 검사·공개 상태 확인. 준비가 끝난 뒤 수행할 절차임을 표시

초안에는 workflow 완료·검증 통과 문구, 존재하지 않는 파일의 경로·해시, 외부 작업 승인 정보를 넣지 않는다. 최종 output 네 파일에는 포함하지 않으며 초안 생성으로 제작 차단이 해소되었다고 기록하지 않는다.
