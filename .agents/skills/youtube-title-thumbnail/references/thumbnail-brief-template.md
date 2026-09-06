# Thumbnail generation brief

문구와 이미지 생성 승인이 끝난 뒤에만 읽는다. 기본값은 문구·시각 요소·구도를 한 번에 설계하는 완성형 생성이다.

## 완성형 image_gen

```text
Use case: ads-marketing
Asset type: finished 16:9 YouTube thumbnail, not a background
Primary request: create a premium, immediately clickable thumbnail from the approved copy and the video's actual promise
Exact text: reproduce every approved Korean and product-name character exactly; add no other words
Copy hierarchy: follow editorial.brief.visual_priority; emphasize the product for a launch, the problem for a solution, or the alternatives for a comparison as appropriate
Composition: integrate typography and subject into one art-directed image; keep generous safe margins; preserve strong hierarchy at 320×180
Visual subject: support the video's actual promise with an explanatory or symbolic subject; do not present a metaphor as demonstrated capability
Style: polished editorial advertising quality, strong contrast, deliberate depth and lighting, no cheap template look
Constraints: no cropped or duplicated text, fake logos, watermarks, random English, unreadable microtext, or decorative UI clutter
```

생성 후 다음을 직접 확인한다.

- 승인 문구가 글자 단위로 정확한가
- 제목과 썸네일이 선택된 역할에 따라 클릭 이유와 범위를 전달하는가
- 320×180에서 의도한 시각적 우선순위가 즉시 읽히는가
- 제품명·질문·비교 대상의 크기가 소재와 사용자 지시에 맞는가
- 배경과 문구가 따로 붙인 템플릿처럼 보이지 않는가
- 영상에서 실제로 다루는 약속과 시각물이 일치하는가

문자 오류가 있으면 먼저 같은 완성형 이미지를 편집하거나 다시 생성한다. 로컬 합성으로 전환하려면 사용자에게 결과 차이를 설명하고 승인을 받는다.

## 로컬 문자 합성

`generation_mode: local_text_composite`일 때만 사용한다. 또한 v3 계약의
`generation_contract.allow_local_text_composite`가 `true`이고
`instruction_source`가 `explicit_user`여야 한다. 사용자가 로컬 합성을
직접 요청하지 않았다면 완성형 생성에서 문자 오류가 두 번 이상 반복되고,
차이를 설명한 뒤 사용자가 전환을 승인한 기록까지 있어야 한다.

```text
Use case: ads-marketing
Asset type: 16:9 YouTube thumbnail background
Primary request: visualize the approved copy's problem and payoff
Composition: reserve a deliberate text area and keep the focal subject on the opposite side
Text: no text anywhere
Constraints: no letters, numbers, labels, logos, brand marks, watermarks, or tiny decorative clutter
```

배경을 받은 뒤 `scripts/render_thumbnail.py`로 정확한 문구를 합성하고 320×180 미리보기를 검수한다.
