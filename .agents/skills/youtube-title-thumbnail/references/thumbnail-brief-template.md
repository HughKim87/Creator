# Thumbnail background brief

새 배경이 필요할 때만 읽는다. 생성 모델에는 글자를 맡기지 않고 시각 요소와 안전한 여백만 요청한다.

```text
Use case: ads-marketing
Asset type: 16:9 YouTube thumbnail background
Input images: representative video frames used only as style references
Primary request: visualize the video's central comparison or decision
Style/medium: match the video's visual language without copying its text
Composition/framing: strict 16:9; reserve one clean side for large local text; keep detailed focal elements on the opposite side; preserve safe margins
Lighting/mood: high contrast and readable at mobile size
Color palette: derive from the actual video frames
Text: no text anywhere
Constraints: no letters, numbers, labels, captions, logos, brand marks, watermarks, or tiny decorative clutter
```

배경을 받은 뒤 다음을 확인한다.

- 글자 영역이 실제로 비어 있는가
- 생성된 가짜 글자·로고·워터마크가 없는가
- 320×180에서도 핵심 형태가 구분되는가
- 영상의 색·주제와 연결되지만 특정 프레임을 그대로 복제하지 않았는가
