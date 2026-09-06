# YouTube title-thumbnail package v3

## Project automation override

Creative delegation is decided only by the active project policy clause `creator-video-creative-delegation-v1`. This package records the result and does not define trigger phrases. When the clause applies, use `approval_policy.mode: delegated_by_user` and `approval_policy.instruction_source: explicit_user`, with the clause ID retained as the semantic authority; otherwise use `review_gated`. This never authorizes external YouTube actions.

새 작업은 `youtube-title-thumbnail-v3` 기술 패키지를 `extension/work/<job-id>/youtube-title-thumbnail.json`에 UTF-8로 저장한다. 상대 경로는 패키지 파일의 폴더를 기준으로 해석한다. `outputs/<job-id>/`에는 승인된 최종 업로드 썸네일만 둔다.

```json
{
  "schema_version": "youtube-title-thumbnail-v3",
  "generation_contract": {
    "required_mode": "one_shot_imagegen",
    "allow_local_text_composite": false,
    "instruction_source": "explicit_user"
  },
  "approval_policy": {
    "mode": "review_gated",
    "instruction_source": "explicit_user"
  },
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
    "approval_method": "explicit_user",
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
- `local_text_composite`: `generation_contract.allow_local_text_composite: true`일 때만 가능하다. 이 모드에서는 `generated_source` 대신 `background`와 `font`를 기록한다.
- 로컬 합성에는 `thumbnail.local_composite_authorization`이 필요하다. `reason`은 `explicit_user_request` 또는 `repeated_text_errors`, `approved_by`는 `explicit_user`, `approved_at`은 시간대 포함 시각이다.
- `reason: repeated_text_errors`이면 `one_shot_attempts`가 2 이상이어야 한다.
- `generation_contract`는 상위 `VIDEO_JOB.json`의 `thumbnail_contract`와 일치해야 한다.

## 승인 계약

- `copy`, `image_generation`, `visual`을 각각 기록한다.
- 상태는 `pending` 또는 `approved`, 방법은 `explicit_user` 또는 `delegated_by_user`다.
- `approval_policy.mode: review_gated`이면 승인된 제목과 `copy`·`image_generation`·`visual`의 방법은 모두 `explicit_user`여야 한다.
- `approval_policy.mode: delegated_by_user`는 활성 정책의 `creator-video-creative-delegation-v1` 판정을 기록한 경우에만 사용한다.
- 승인 위임은 `approval_policy.instruction_source: explicit_user`이고 의미 권위가 활성 정책의 `creator-video-creative-delegation-v1`일 때만 유효하다.
- 문구 승인과 생성 승인은 `generated_at`보다 빠르거나 같아야 하고, 시각 승인은 생성 이후여야 한다.
- 원문 대화나 계정 정보는 저장하지 않고 안전한 승인 방법과 시각만 기록한다.

`channel_evidence.status`는 `verified`, `unavailable`, `not_provided` 중 하나다. 제목 후보는 최소 5개다. 자동 검증은 사용자 승인을 대신하지 않는다.

기존 `youtube-title-thumbnail-v1`·`youtube-title-thumbnail-v2`는 검증 호환만 유지한다. 새 작업에는 v3를 사용한다.

## 새 제작의 근거·원문 계약

새 작업과 새 문구 revision에는 아래 필드를 추가하고 `--require-editorial`로 검증한다. 기존 패키지에 필드가 없으면 읽기 호환은 유지하되 `editorial_status: legacy_unrecorded`로 표시한다. 필드가 있으면 일반 검증에서도 확인한다. 구조 검증은 해석의 타당성이나 실제 CTR을 입증하지 않는다.

```json
{
  "title": {"approved_text": "선택된 제목의 정확한 원문"},
  "approval": {"copy": {"text_blocks": ["제품명", "승인된 질문 전체"]}},
  "editorial": {
    "version": 1,
    "captions_sha256": "현재 SRT의 SHA-256",
    "brief": {
      "audience": "관심사와 사전 지식으로 설명한 대상",
      "core_message": "실제 영상의 핵심 메시지 한 문장",
      "promise_boundary": "영상에서 답하는 범위와 답하지 않는 범위",
      "evidence": [{"cue": 1, "excerpt": "해당 자막 cue에 존재하는 짧은 인용"}],
      "visual_priority": "무엇을 먼저 읽게 할지와 이유",
      "title_thumbnail_roles": "제목과 썸네일이 각각 전달하는 역할"
    },
    "review": {
      "thumbnail_sha256": "직접 검수한 업로드 썸네일의 SHA-256",
      "assessment_kind": "editorial_judgment",
      "content_fit": "영상 내용에서 질문에 답하는 근거",
      "mobile_readability": "320x180에서 직접 확인한 내용",
      "click_rationale": "타깃이 궁금해할 이유에 대한 편집 판단"
    },
    "performance_status": "not_measured"
  }
}
```

이 예시는 기존 패키지에 합칠 필드만 보여준다. 승인 방법·시각 등 기존 필수 필드는 유지한다. 인용은 지정 cue의 실제 텍스트에 포함되어야 한다. 승인 원문과 생성 문구는 블록 단위로 일치해야 하며 블록 내부 줄바꿈을 공백으로 바꾸는 배치 차이만 허용한다. 선택 원문을 새 문구로 덮어써 과거 승인을 재사용하지 않는다.

기존 `validation.title_thumbnail_not_duplicate`는 하위 호환 필드다. 새 계약에서는 문장 공유 금지가 아니라 `title_thumbnail_roles`에 기록한 역할 분담의 검토 완료를 뜻한다. 실제 게시 후의 성과는 채널 분석 자료가 소유하며 제작 전 검증 패키지의 합격 조건으로 두지 않는다.
