# Thumbnail generation brief

문구와 이미지 생성 승인이 끝난 뒤에만 읽는다. 기본값은 문구·시각 요소·구도를 한 번에 설계하는 완성형 생성이다.

## 완성형 image_gen

```text
Use case: ads-marketing
Asset type: finished 16:9 YouTube thumbnail, not a background
Primary request: create a premium, immediately clickable thumbnail from the approved copy and the video's actual promise
Exact text: reproduce every approved Korean and product-name character exactly; add no other words
Copy hierarchy: viewer problem or question first, unexpected payoff second, scope or proof as a small badge
Composition: integrate typography and subject into one art-directed image; keep generous safe margins; preserve strong hierarchy at 320×180
Visual subject: show the video's actual mechanism or decision, not a generic robot or unrelated stock scene
Style: polished editorial advertising quality, strong contrast, deliberate depth and lighting, no cheap template look
Constraints: no cropped or duplicated text, fake logos, watermarks, random English, unreadable microtext, or decorative UI clutter
```

생성 후 다음을 직접 확인한다.

- 승인 문구가 글자 단위로 정확한가
- 제목과 같은 문장을 반복하지 않고 클릭 이유를 보완하는가
- 320×180에서 문제·해답 순서가 1초 안에 읽히는가
- 제품명은 메인 훅이 아니라 범위·근거로 작동하는가
- 배경과 문구가 따로 붙인 템플릿처럼 보이지 않는가
- 영상에서 실제로 다루는 약속과 시각물이 일치하는가

문자 오류가 있으면 먼저 같은 완성형 이미지를 편집하거나 다시 생성한다. 로컬 합성으로 전환하려면 사용자에게 결과 차이를 설명하고 승인을 받는다.

## 로컬 문자 합성

`generation_mode: local_text_composite`일 때만 사용한다.

```text
Use case: ads-marketing
Asset type: 16:9 YouTube thumbnail background
Primary request: visualize the approved copy's problem and payoff
Composition: reserve a deliberate text area and keep the focal subject on the opposite side
Text: no text anywhere
Constraints: no letters, numbers, labels, logos, brand marks, watermarks, or tiny decorative clutter
```

배경을 받은 뒤 `scripts/render_thumbnail.py`로 정확한 문구를 합성하고 320×180 미리보기를 검수한다.
