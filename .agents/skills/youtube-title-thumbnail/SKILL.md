---
name: youtube-title-thumbnail
description: 완성 영상·SRT·리서치 근거와 선택적 채널 패턴을 분석해 YouTube 제목 후보, 먼저 승인받을 클릭 중심 썸네일 문구, 완성형 16:9 썸네일과 검증 패키지를 만든다. 사용자가 영상 제목·썸네일 제작, YouTube 패키징, research-to-video 워크플로의 제목·썸네일 단계를 요청할 때 사용한다. 문구 승인 전에는 이미지를 생성하지 않고 업로드나 게시 전에 멈춘다.
---

# YouTube Title and Thumbnail

완성 영상의 실제 약속을 제목과 썸네일로 압축한다. 기술 검증을 창작 승인으로 간주하지 않는다.

## 입력과 저장 위치

다음을 확정한다.

- 정확한 완성 영상과 검증된 SRT
- 사용한 리서치 근거
- 선택적 채널 URL·최근 승인 썸네일 패턴
- `extension/work/<job-id>/`와 `extension/outputs/<job-id>/`

영상과 SRT의 길이·주제·파일명을 확인한다. 기술 패키지, 생성 원본, 마스터와 미리보기는 `work/<job-id>/`에 둔다. `outputs/<job-id>/`에는 최종 업로드 썸네일만 둔다.

## 제목 설계

1. 대상 시청자, 핵심 변화, 실무 이득과 주의점을 추출한다.
2. 비교형·사용법형·경고형·총정리형을 포함해 40~65자 후보 5개를 만든다.
3. 핵심 검색어를 앞 4~5단어 안에 두고 과장과 소스에 없는 확정 표현을 제외한다.
4. 명확성, 검색 의도, 영상 충실도, 호기심과 채널 적합성으로 하나를 `draft`로 선정한다.
5. 사용자가 승인하거나 선택 권한을 위임한 경우 `approved`로 바꾼다. 상위 작업의 `execution_mode`가 `autonomous_local_pipeline`이면 권장안을 직접 선정하고 `delegated_by_user`로 기록한다.

## 썸네일 문구

이미지를 만들기 전에 문구만 제안한다.

1. 시청자가 겪는 문제나 강한 질문을 `hook`으로 만든다.
2. 영상이 제공하는 예상 밖의 해답을 `payoff`로 만든다.
3. 제품명·비교 범위·근거는 작은 `scope` 또는 배지로 둔다.
4. 제목을 반복하는 설명형 문구, “뭐부터?”, “입문자 가이드”, 도구 이름 나열만으로 끝나는 문구를 기본안으로 선택하지 않는다.
5. 후보 3~5개에 클릭 이유와 약점을 붙여 사용자에게 보여준다.

`review_gated`에서는 사용자가 정확한 문구를 승인하기 전 이미지 생성 도구를 호출하지 않는다. `autonomous_local_pipeline`에서는 후보의 클릭 이유와 약점을 내부 검토한 뒤 가장 적합한 문구를 선정하고, 문구와 이미지 생성 승인을 `delegated_by_user`로 기록해 중단 없이 진행한다.

## 이미지 생성

문구와 이미지 생성 승인을 받은 뒤 [references/thumbnail-brief-template.md](references/thumbnail-brief-template.md)를 읽는다.

기본 모드는 `one_shot_imagegen`이다.

- built-in image generation으로 승인 문구·주제·구도·조명을 하나의 완성형 썸네일로 생성한다.
- 정확한 한글·제품명과 16:9 안전 여백을 프롬프트에 명시한다.
- 생성 문구가 틀리면 같은 완성형 이미지를 편집하거나 다시 생성한다.
- `local_text_composite`는 사용자가 정확한 로컬 합성을 요청하거나 문자 오류가 반복되어 대체 방식을 승인한 경우에만 사용한다.
- 로컬 합성 시 `scripts/render_thumbnail.py`를 사용하고 배경·폰트·문구를 패키지에 기록한다.

생성 원본을 보존한 뒤 업로드용 이미지를 정확히 1280×720 JPEG 또는 PNG로 정규화하고 320×180 미리보기를 만든다.

## 시각 검수와 승인

다음을 모두 확인한다.

- 승인 문구가 글자 단위로 정확하고 잘리지 않음
- 모바일에서 문제 → 해답 → 범위 순서가 읽힘
- 제목과 썸네일이 같은 문장을 반복하지 않음
- 영상에 없는 효능·수치·비교를 약속하지 않음
- 일반적인 로봇·UI 템플릿이 아니라 영상의 핵심 메커니즘을 보여줌
- 배경과 글자가 하나의 완성형 디자인으로 보임

최종 이미지와 320×180 미리보기를 검수한다. `review_gated`에서는 사용자에게 보여주고 승인 또는 명시적 위임 전에는 완료하지 않는다. `autonomous_local_pipeline`에서는 에이전트가 동일한 검수 기준으로 최종 시각을 선택하고 `visual.method`를 `delegated_by_user`로 기록한 뒤 계속한다.

## 승인과 패키지

[references/package-format.md](references/package-format.md)에 따라 `youtube-title-thumbnail-v2` 패키지를 `work/<job-id>/`에 만든다.

- `copy`, `image_generation`, `visual` 승인을 각각 기록한다.
- 문구·생성 승인 시각은 이미지 생성 시각보다 빠르거나 같아야 한다.
- 시각 승인 시각은 이미지 생성 이후여야 한다.
- 원문 대화는 저장하지 않는다.

작업 중 구조 검증:

```powershell
python scripts/validate_package.py <package.json>
```

완료 처리 전 승인 포함 검증:

```powershell
python scripts/validate_package.py <package.json> --require-approved
```

두 번째 명령이 `status: valid`, `approval_ready: true`, errors·warnings 0일 때만 `title_thumbnail`을 완료한다.

## 반환과 정지

- 제목 후보 5개와 선정 이유
- 승인된 썸네일 문구와 클릭 전략
- 생성 모드, 원본, 마스터, 업로드 파일과 모바일 미리보기
- 승인 상태와 검증 결과
- 채널 근거 상태

패키지 검증 후 멈춘다. 실제 YouTube 업로드·게시·공개 범위 변경은 하지 않는다.
