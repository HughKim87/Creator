---
name: youtube-title-thumbnail
description: 완성 영상·SRT·리서치 근거와 선택적 채널 패턴을 분석해 YouTube 제목 후보, 먼저 승인받을 클릭 중심 썸네일 문구, 완성형 16:9 썸네일과 검증 패키지를 만든다. 사용자가 영상 제목·썸네일 제작, YouTube 패키징, research-to-video 워크플로의 제목·썸네일 단계를 요청할 때 사용한다. 문구 승인 전에는 이미지를 생성하지 않고 업로드나 게시 전에 멈춘다.
---

# YouTube Title and Thumbnail

## Automatic mode for topic-only production requests

Creative delegation is owned only by the active project policy clause `creator-video-creative-delegation-v1`. This skill does not define delegation triggers. When the active video job records that clause and `thumbnail_contract.approval_mode: delegated_by_user`, select the title, thumbnail copy, one-shot generated image, and final visual without an intermediate response; record and validate those choices. Otherwise keep `review_gated`. This never authorizes YouTube upload or publication.

완성 영상의 실제 약속을 제목과 썸네일로 압축한다. 기술 검증을 창작 승인으로 간주하지 않는다.

`coordinate-video-production`에서 호출되면 [하위 스킬 호출 계약](../coordinate-video-production/SKILL.md#하위-스킬-호출-계약)에 따라 단계 결과를 반환한다. 단독 호출에서는 이 스킬의 정지 경계를 적용한다. coordinator가 전달한 내용 검수의 미해결 중대 오류가 없어야 제작을 시작하며, 공개할 경미한 한계를 제목·썸네일에서 과장하지 않는다.

## 입력과 저장 위치

다음을 확정한다.

- 정확한 완성 영상과 검증된 SRT
- 사용한 리서치 근거
- 선택적 채널 URL·최근 승인 썸네일 패턴
- `extension/work/<job-id>/`와 `extension/outputs/<job-id>/`

영상과 SRT의 길이·주제·파일명을 확인한다. 기술 패키지, 생성 원본, 마스터와 미리보기는 `work/<job-id>/`에 둔다. `outputs/<job-id>/`에는 최종 업로드 썸네일만 둔다.

## 성과 근거를 요청받은 경우의 벤치마크

사용자가 벤치마크를 요청하거나 실제 데이터에 근거한 조회수·클릭률 중심 추천을 요구하면, 제목 후보 작성 전에 유사 영상의 실제 패키징을 확인한다. 목표는 문구를 복제하는 것이 아니라 대상 시청자에게 어떤 질문과 시각적 단서가 제시됐는지 파악하는 것이다. 단순 어법 수정이나 승인 제목의 그대로 적용에는 이 조사를 강제하지 않는다. 사용자가 조사를 생략하도록 지시한 경우 창작 후보로 진행하되 성과 근거가 없는 잠정안임을 밝힌다.

1. 영상 주제·시청자·언어·형식이 가까운 사례부터 찾는다. 한국 시청자 대상이면 한국 영상을 우선하고, 편집 롱폼과 쇼츠·방송 다시보기는 구분한다. 보통 여러 채널의 3~5개 사례를 비교하되 수를 채우려고 관련 없는 사례를 넣지 않는다. 확보 수와 한계를 밝히며 대형 채널의 성공만으로 작은 채널의 진입 가능성을 판단하지 않는다. 가능한 경우 작은 채널과 낮은 조회수 사례도 비교한다.
2. 사례마다 URL, 실제 제목, 채널, 공개 조회수, 업로드 경과 또는 날짜, 확인 시각을 기록한다. 채널 규모를 비교에 쓰면 확인한 현재 구독자 수임을 표시한다. 제목·조회수 확인과 썸네일 직접 확인을 구분하고, 썸네일을 실제로 본 경우에만 문구·구도·시각적 우선순위를 기록한다. 보지 못한 썸네일은 제목에서 추정하지 않고 `not_observed`로 둔다.
3. 관측 사실과 해석을 나눈다. 공개 조회수는 노출수·CTR·제목의 인과 효과를 입증하지 않는다. 업로드 경과, 채널 규모, 시의성, 광고·이벤트 등 확인된 교란 요인을 함께 고려하고, 높은 조회수 한 건을 검증된 성공 공식으로 표현하지 않는다. 확인하지 못한 수치·조건은 불명으로 남긴다.
4. 확인한 사례와 제한을 먼저 짧게 제시한 뒤 후보를 만든다. 적용할 질문 구조나 시각 원리, 가져오지 않을 사례별 사실, 우리 영상에서 약속에 답하는 위치를 연결한다. 경쟁 영상의 매출 순위·수치·경험을 우리 영상의 사실로 옮기지 않는다. 서로 다른 후보는 실제 비교에서 얻은 관점과 영상 내용에 근거해 구별한다.
5. 페이지·이미지·지표에 접근할 수 없으면 확보된 사실과 확인 불가 범위를 공개한다. 추측을 실측으로 채우거나 조사한 것처럼 말하지 않는다. 그 상태에서 후보를 제공하면 근거가 제한된 편집 판단으로 표시한다. 실제 게시 후 성과는 별도 채널 분석 자료로 확인한다.

패키지 작업에서는 [근거 기록 형식](references/package-format.md#벤치마크-관측-기록)에 관측과 적용 판단을 보존한다. 채팅으로 후보만 요청한 경우에는 채팅의 근거 비교로 충분하며 패키지·보고서 생성을 추가하지 않는다.

## 제목 설계

1. 후보 작성 전에 검증된 SRT에서 대상 시청자, 핵심 메시지 한 문장, 실제 답하는 질문과 답하지 않는 범위를 추출한다. 대상이 이미 아는 것과 지금 궁금해할 질문을 구분해 클릭할 이유를 정한다. 이를 뒷받침하는 cue 번호·짧은 인용과 SRT 해시를 패키지의 `editorial.brief`에 기록한다. 자료 소개를 직접 실험·성능 입증으로 바꾸지 않는다.
2. 제목과 썸네일 문구를 한 세트로 구상한다. 후보 수는 사용자 요청을 따르고, 지정이 없으면 5세트를 기본으로 한다. 경쟁 구도·사용자의 선택·예상 밖의 한계 등 영상이 뒷받침하는 서로 다른 클릭 이유를 탐색한다. 같은 제품명 뒤의 단어만 바꾸거나, 영상에 맞지 않는 유형을 채우지 않는다.
3. 제목 앞부분만 읽어도 대상과 관심 이유가 전달되게 쓴다. 검색 중심이면 찾을 표현을, 추천 중심이면 질문·변화·이득을 앞세울 수 있다. 유입 경로 근거가 없으면 가정으로 밝힌다. 제품·버전명은 구분에 필요한 만큼 쓰고, 생략하면 비교 대상이나 약속이 바뀌는 이름은 유지한다. 40~65자는 편집상 참고 범위이며 최소 길이가 아니다. 짧아도 뜻이 명확하면 채택하고, 긴 제목은 앞부분의 의미와 읽기 부담을 검토한다. 기술 상한은 100자다.
4. 사용자가 제안한 표현의 질문 초점과 말투를 보존하며 가독성과 어법을 다듬는다. 물음표만 붙여 영상에 없는 승리·위기·효능을 암시하지 않는다. 클릭 후 영상의 어느 부분에서 질문에 답하는지 확인하고, 도입부가 그 질문이나 확인 범위를 안내하는지도 검토한다. 원본 도입부가 약속을 받치지 못하면 약속을 좁히거나 한계로 보고한다.
5. 영상 충실도와 답변 가능성을 먼저 통과시킨 뒤, 명확성·호기심·구체적인 시청 이득·제목과 썸네일의 역할·채널 적합성으로 하나를 `draft`로 선정한다. 각 후보에 클릭 이유와 약점을 붙이고, 1순위에는 다른 후보보다 추천하는 이유를 설명한다. 하나만 요청하면 1순위와 이유만 보고한다. 점수나 순위는 편집 판단이며 조회수·CTR·시청 지속 시간 예측치가 아니다.
6. 사용자가 승인하거나 `thumbnail_contract.approval_mode: delegated_by_user`로 선택 권한을 명시적으로 위임한 경우에만 `approved`로 바꾼다.

## 썸네일 문구

이미지를 만들기 전에 문구만 제안한다.

1. 시청자가 겪는 문제나 강한 질문을 `hook`으로 만든다.
2. 영상이 제공하는 예상 밖의 해답을 `payoff`로 만든다.
3. 소재와 사용자 지시에 맞춰 시각적 우선순위를 선택한다. 신제품 공개에서는 제품명, 문제 해결에서는 문제, 비교에서는 비교 대상이 중심이 될 수 있다. `scope`는 의미상 범위이며 작은 배지를 의무화하지 않는다. 선택 이유를 `editorial.brief.visual_priority`에 기록한다.
4. 제목과 썸네일은 클릭 이유와 영상 범위를 함께 전달한다. 핵심 질문을 공유해도 되며, 설명만 중복하는 구성은 피한다. 각 역할을 `editorial.brief.title_thumbnail_roles`에 기록한다. 호기심을 만들기 위해 영상에 없는 위기·효능을 암시하지 않는다.
5. 제목도 함께 만드는 경우 위에서 정한 세트별로 문구·클릭 이유·약점을 보여준다. 문구만 요청하면 요청 개수를 따르고, 지정이 없으면 3~5개를 제안한다.

`thumbnail_contract.approval_mode: review_gated`에서는 사용자가 정확한 문구를 승인하기 전 이미지 생성 도구를 호출하지 않는다. `delegated_by_user`는 작업 기록이 활성 정책의 `creator-video-creative-delegation-v1` 판정을 참조할 때만 사용한다. 상위 작업의 `execution_mode`만으로 승인 위임을 추정하지 않는다.

선택된 제목은 `title.approved_text`, 승인 문구는 `approval.copy.text_blocks`에 기준 원문으로 기록한다. 생성 프롬프트와 `thumbnail.text`는 이 원문을 사용한다. 사용자가 선택한 표현을 임의로 축약하지 않는다. 줄바꿈·크기는 배치 변경이지만 단어·질문 초점·약속의 변경은 문구 수정이다. 기존 승인으로 수정 문구를 통과시키지 말고 현재 승인 범위에 따라 새 결정을 기록한다.

## 이미지 생성

문구와 이미지 생성 승인을 받은 뒤 [references/thumbnail-brief-template.md](references/thumbnail-brief-template.md)를 읽는다.

기본 모드는 `one_shot_imagegen`이다. 상위 작업의 `thumbnail_contract`와 패키지의 `generation_contract`를 먼저 대조한다.

- built-in image generation으로 승인 문구·주제·구도·조명을 하나의 완성형 썸네일로 생성한다.
- 정확한 한글·제품명과 16:9 안전 여백을 프롬프트에 명시한다.
- 생성 문구가 틀리면 같은 완성형 이미지를 편집하거나 다시 생성한다.
- `local_text_composite`는 `generation_contract.allow_local_text_composite: true`이고, 사용자가 정확한 로컬 합성을 요청했거나 완성형 생성에서 문자 오류가 두 번 이상 반복된 뒤 전환을 명시적으로 승인한 경우에만 사용한다.
- 로컬 합성 패키지에는 `local_composite_authorization.reason`, `approved_by`, `approved_at`과 반복 실패 시 `one_shot_attempts`를 기록한다.
- 로컬 합성 시 `scripts/render_thumbnail.py`를 사용하고 배경·폰트·문구를 패키지에 기록한다.

생성 원본을 보존한 뒤 업로드용 이미지를 정확히 1280×720 JPEG 또는 PNG로 정규화하고 320×180 미리보기를 만든다.

## 시각 검수와 승인

다음을 모두 확인한다.

- 승인 문구가 글자 단위로 정확하고 잘리지 않음
- 모바일에서 선택한 제품명·질문·비교 대상의 우선순위가 읽힘
- 제목과 썸네일의 역할이 영상의 약속에 맞게 설명됨
- 영상에 없는 효능·수치·비교를 약속하지 않음
- 시각 요소가 소재와 관심 이유를 뒷받침함. 설명 도식과 상징적 출시 이미지는 목적에 맞춰 선택하며, 상징물을 실제 기능의 증거처럼 제시하지 않음
- 배경과 글자가 하나의 완성형 디자인으로 보임

최종 이미지와 320×180 미리보기를 검수한다. `approval_mode: review_gated`에서는 사용자에게 보여주고 승인 전에는 완료하지 않는다. `approval_mode: delegated_by_user`일 때만 에이전트가 최종 시각을 선택하고 `visual.method`를 `delegated_by_user`로 기록한다.

`editorial.review`에 내용 일치·모바일 가독성·클릭 이유의 구체적 판단과 검수한 썸네일 해시를 기록한다. `assessment_kind: editorial_judgment`, `performance_status: not_measured`를 사용한다. `clickability_reviewed`는 검토 수행 여부일 뿐 효과 입증이 아니다. 이미지 문구 판독은 직접 시각 검수가 소유하며 문자열·해시 검사가 대신하지 않는다.

## 승인과 패키지

[references/package-format.md](references/package-format.md)에 따라 새 작업은 `youtube-title-thumbnail-v3` 패키지를 `work/<job-id>/`에 만든다.

- `generation_contract`와 `approval_policy`를 상위 `thumbnail_contract`와 동일하게 기록한다.
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
python scripts/validate_package.py <package.json> --require-approved --require-editorial
```

두 번째 명령이 `status: valid`, `approval_ready: true`, errors·warnings 0일 때만 `title_thumbnail`을 완료한다.

## 반환과 정지

- 요청 개수에 맞는 제목·썸네일 문구 세트, 후보별 클릭 이유·약점과 1순위 선정 이유
- 승인된 썸네일 문구와 클릭 전략
- 생성 모드, 원본, 마스터, 업로드 파일과 모바일 미리보기
- 승인 상태와 검증 결과
- 채널 근거 상태

패키지 검증 후 멈춘다. 실제 YouTube 업로드·게시·공개 범위 변경은 하지 않는다.

## Claude 실행 경로

Claude(Cowork)에는 built-in image generation이 없다. `one_shot_imagegen`은 사용자의 ChatGPT 웹에서 같은 완성형 생성으로 수행한다. 생성 모드와 승인 순서는 바꾸지 않는다.

1. `$connect-chrome-profile`의 Claude 실행 경로로 작업 기록의 프로필에 등록된 Chrome을 선택하고 `https://chatgpt.com`을 연다. 로그인 화면·사용량 한도는 `needs_user`로 반환한다.
2. 승인된 문구를 글자 그대로 포함한 완성형 프롬프트(16:9, 안전 여백, 정확한 한글·제품명)를 새 대화에 입력해 생성한다. 이미지 생성 승인 전에는 입력하지 않는다.
3. 생성 이미지는 ChatGPT의 다운로드로 사용자 다운로드 폴더에 저장한다. 다운로드 폴더 접근은 `device_request_folder_access`로 한 번 요청하고, 해당 파일만 `work/<job-id>/`의 `generated_source`로 복사한다. 다른 다운로드 파일을 열거·읽지 않는다.
4. 패키지 `thumbnail`에 `generator: chatgpt_web`을 기록한다. 이 필드가 없으면 Codex built-in 생성으로 본다. 문구 오류 시 같은 대화에서 편집·재생성하며 로컬 합성 전환 조건은 위 규칙과 같다.
5. 생성 이후의 정규화·미리보기·시각 검수·검증은 위 절차와 같다.
