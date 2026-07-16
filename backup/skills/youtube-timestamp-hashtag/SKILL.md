---
name: youtube-timestamp-hashtag
description: >
  유튜브 영상 설명란에 타임스탬프와 해시태그를 자동으로 추가하는 워크플로우 스킬.
  YouTube Studio에서 영상 목록을 확인하고, 각 영상의 기존 설명을 먼저 확인한 뒤,
  타임스탬프/해시태그 중 빠진 것만 선별적으로 작업한다.
  다음 상황에서 반드시 이 스킬을 사용한다:
  "유튜브 영상에 타임스탬프 추가해줘", "해시태그 달아줘", "YouTube Studio 설명 업데이트",
  "영상 설명란 정리", "타임스탬프 작업", "유튜브 영상 메타데이터 업데이트",
  또는 YouTube 영상 설명에 타임스탬프/해시태그를 추가하는 모든 요청.
compatibility: "Chrome MCP (mcp__Claude_in_Chrome__*) 필요"
---

# 유튜브 타임스탬프 & 해시태그 자동화 (보조)

유튜브 영상 설명란에 타임스탬프와 해시태그를 효율적으로 추가하는 보조 스킬. Chrome
MCP(`mcp__Claude_in_Chrome__*`)로 YouTube Studio / youtube.com을 직접 제어한다.

- 영상 제작 1~8단계 파이프라인과 독립된 보조 스킬이다. 수요자는 사용자의 유튜브 채널.
- 안전 규칙은 `PROJECT_RULES.md`를 따른다. 설명란 저장은 외부 쓰기·게시 변경이므로
  `PROJECT_RULES.md`의 "외부 쓰기/게시 전 승인" 원칙에 따라 **사용자 확인 없이 저장하지
  않는다.**
- 복원 이력: 이 스킬은 구버전 백업(`277edf4^`)에서 복원됐고, 원본이 "타임스탬프 설명
  반영 / 해시태그 생성 / 저장" 부분에서 잘려 있었다. 5~7단계는 재구성 후 **실제 Studio
  편집 페이지에서 DOM을 실측 검증해 채웠다**(2026-07 기준). Studio UI가 바뀌면 선택자
  재확인이 필요하다.

## 입력

- 대상 영상: 사용자가 준 목록, 또는 YouTube Studio 채널 영상 목록
  `https://studio.youtube.com/channel/{채널ID}/videos`.
- 필수 도구: Chrome MCP(`mcp__Claude_in_Chrome__*`). 미연결이면 진행 불가.
- 영상 유형별 처리 규칙(기본값):

  | 유형 | 처리 방식 |
  |------|-----------|
  | 노래 영상(제목 `[노래]`) | 해시태그만 (타임스탬프 없음) |
  | 짧은 영상(<60초) / 자막 없는 영상 | 해시태그만 |
  | 일반 영상 | AI 패널 타임스탬프 + 해시태그 |

  사용자가 "노래는 타임스탬프 없이"처럼 별도 지시를 했다면 그 규칙을 우선 적용한다.

## 처리 절차

1. **영상 목록 파악** — 처리할 영상을 사용자에게 받거나 Studio 목록에서 최신순으로 뽑는다.

   ```javascript
   const rows = document.querySelectorAll('ytcp-video-row');
   const videos = [...rows].slice(0, N).map(row => {
     const titleEl = row.querySelector('#video-title');
     const allLinks = [...row.querySelectorAll('a')];
     const videoLink = allLinks.find(a => a.href && a.href.includes('/video/'));
     return {
       title: titleEl?.innerText?.trim(),
       id: videoLink?.href?.match(/\/video\/([^/]+)/)?.[1]
     };
   });
   JSON.stringify(videos, null, 2);
   ```

2. **일괄 상태 스캔(핵심 최적화)** — 영상을 하나씩 열지 않는다. Studio 목록 페이지 DOM에
   이미 각 영상의 전체 설명·길이가 로드돼 있으니 한 번에 파싱해 작업 대상만 추린다.

   ```javascript
   // 스크롤해서 모든 영상 로드 후 실행
   const rows = document.querySelectorAll('ytcp-video-row');
   const results = [...rows].map(row => {
     const item = row.__dataHost?.__data?.item;
     const video = item?.video;
     const title = video?.title;
     const id = video?.videoId;
     const desc = video?.description || '';
     const lengthSeconds = parseInt(video?.lengthSeconds || '0');
     const isSong = title?.includes('[노래]');
     const hasTimestamps = /\d+:\d{2}/.test(desc);
     const hasHashtags = /#\S+/.test(desc);
     const needsTimestamp = !hasTimestamps && !isSong && lengthSeconds >= 60;
     const needsHashtag = !hasHashtags;
     return { title, id, lengthSeconds, hasTimestamps, hasHashtags, isSong, needsTimestamp, needsHashtag, needsWork: needsTimestamp || needsHashtag };
   }).filter(v => v.id);
   results.filter(v => v.needsWork);
   ```

   기존 설명 판정: 타임스탬프 `/\d+:\d{2}/`, 해시태그 `/#\S+/`. 작업 결정 매트릭스:

   | 타임스탬프 | 해시태그 | 할 일 |
   |-----------|---------|-------|
   | ✅ 있음 | ✅ 있음 | 스킵 (이미 완료) |
   | ❌ 없음 | ✅ 있음 | 영상 열고 AI 패널로 타임스탬프만 생성 |
   | ✅ 있음 | ❌ 없음 | 영상 열지 않고 해시태그만 생성 후 저장 |
   | ❌ 없음 | ❌ 없음 | 영상 열고 타임스탬프 + 해시태그 생성 |

   노래·짧은 영상은 타임스탬프가 없어도 "해시태그만" 행으로 처리한다.

3. **(타임스탬프 필요 영상만) 영상 열기 + 광고 처리** — `youtube.com/watch?v={VIDEO_ID}`로
   연다(Studio 아님, AI 패널은 youtube.com에서만 작동). 광고 스킵 후 일시정지.

   ```javascript
   for (let i = 0; i < 40; i++) {
     await new Promise(r => setTimeout(r, 1000));
     const skip = document.querySelector(
       '.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern'
     );
     if (skip) { skip.click(); await new Promise(r => setTimeout(r, 1000)); }
     const adOverlay = document.querySelector(
       '.ytp-ad-overlay-container, .ytp-ad-player-overlay'
     );
     if (!adOverlay) break;
   }
   document.querySelector('video')?.pause();
   ```

4. **AI 패널 타임스탬프 요청 + 응답 + 개수 제한** — AI 패널을 열어 한국어 타임스탬프를
   요청하고 12초 뒤 응답을 읽는다.

   ```javascript
   const btn = [...document.querySelectorAll('button')]
     .find(b => b.innerText.trim() === '질문하기');
   btn?.click();
   await new Promise(r => setTimeout(r, 2000));
   const textarea = document.querySelector('textarea[placeholder="질문하기..."]');
   textarea.focus();
   const setter = Object.getOwnPropertyDescriptor(
     window.HTMLTextAreaElement.prototype, 'value'
   ).set;
   setter.call(textarea,
     '이 영상의 주요 장면마다 타임스탬프를 한국어로 만들어줘. 0:00부터 시작해서 형식은 \'0:00 내용\' 으로 해줘.'
   );
   textarea.dispatchEvent(new Event('input', { bubbles: true }));
   textarea.dispatchEvent(new Event('change', { bubbles: true }));
   await new Promise(r => setTimeout(r, 300));
   textarea.dispatchEvent(new KeyboardEvent('keydown',  { key: 'Enter', keyCode: 13, which: 13, bubbles: true }));
   textarea.dispatchEvent(new KeyboardEvent('keypress', { key: 'Enter', keyCode: 13, which: 13, bubbles: true }));
   textarea.dispatchEvent(new KeyboardEvent('keyup',    { key: 'Enter', keyCode: 13, which: 13, bubbles: true }));
   ```

   ```javascript
   // 응답 읽기 (12초 대기)
   await new Promise(r => setTimeout(r, 12000));
   const chatPanel = document.querySelector(
     'ytd-engagement-panel-section-list-renderer[target-id="PAyouchat"]'
   );
   chatPanel.innerText.slice(-2000);
   ```

   **개수 상한(중요)**: 최대 타임스탬프 수 = 영상 길이(분) ÷ 2 (올림, 약 2분에 1개).

   | 영상 길이 | 최대 수 |
   |----------|--------|
   | ~5분 | 3개 |
   | ~10분 | 5개 |
   | ~20분 | 10개 |
   | ~30분 | 15개 |
   | 60분 이상 | 30개 |

   초과 시 **장면 전환 위주로 추리고**, 간격 1분 미만 항목을 먼저 제거한다.

   ```javascript
   const maxTimestamps = Math.ceil(lengthSeconds / 120);
   ```

5. **타임스탬프 정리 → 설명 반영** — 추린 타임스탬프를 `0:00 내용` 형식으로 정렬한다(첫
   항목은 반드시 `0:00`). 기존 설명 본문은 보존하고, 그 아래에 `타임스탬프` 블록을 붙인다.

6. **해시태그 생성** — 영상 주제·게임명 기반 관련 해시태그 3~5개를 설명 맨 끝에 붙인다
   (과다 금지). 기존 해시태그가 있으면 건드리지 않는다.

7. **Studio 편집 페이지에서 설명 반영 + 저장** — 영상 편집 페이지
   `https://studio.youtube.com/video/{VIDEO_ID}/edit`에서 처리한다. (아래 선택자는
   2026-07 Studio에서 실측 검증함. UI 변경 시 재확인.)
   - 설명 입력란: `#description-textarea #textbox` (contenteditable). 값은 `innerText`
     직접 대입이 아니라 **포커스 → 전체 선택 → `execCommand('insertText')`**로 넣어야
     Studio 내부 모델이 갱신되고 저장 버튼이 활성화된다.
   - 저장 버튼: `ytcp-button#save`(텍스트 "저장"). 변경 전에는 `disabled`, 설명이 실제로
     바뀌면 활성화. 되돌리기는 `#discard`("변경사항 실행취소").

   ```javascript
   const box = document.querySelector('#description-textarea #textbox');
   box.focus();
   document.execCommand('selectAll', false, null);
   document.execCommand('insertText', false, finalDescription); // 최종 설명 전체
   await new Promise(r => setTimeout(r, 500));
   const save = document.querySelector('#save');
   const enabled = save && !(save.hasAttribute('disabled') || save.getAttribute('aria-disabled') === 'true');
   enabled; // true면 저장 가능 상태 (실제 save.click()은 사용자 승인 후)
   ```

   **`save.click()`(저장 확정)은 사용자가 최종 설명을 확인·승인한 뒤에만 한다.**

## 출력

- 영상별 처리 결과표: `제목 / 추가한 타임스탬프 수 / 추가한 해시태그 / 스킵 사유`.
- 저장 전 각 영상의 최종 설명 미리보기.

## 게이트

1. Chrome MCP가 연결돼 있다.
2. 각 영상의 기존 설명을 먼저 확인해 **빠진 항목만** 작업한다(중복 추가 금지).
3. 타임스탬프 수가 상한(길이 분 ÷ 2, 올림) 이하다.
4. 저장 전 최종 설명을 사용자에게 보여주고 승인받았다.

## 중단 조건

- Chrome MCP 미연결 → 진행하지 않는다.
- Studio/AI 패널 DOM 구조가 바뀌어 파싱·전송이 실패 → 멈추고 현재 DOM을 확인한다.
- 저장 동작을 확인할 수 없으면 저장하지 않고 최종 텍스트만 사용자에게 전달한다.
- 사용자 승인 없이 설명을 저장(게시)하지 않는다.

## 다음 단계 전달물

- 파이프라인 다음 단계 없음. 수요자는 사용자의 유튜브 채널.
- 전달물: 영상별 반영된(또는 반영 대기) 설명 텍스트와 처리 결과표.

## AI가 확정하지 말 것

- 설명 최종 저장(게시) 여부 — 항상 사용자 승인.
- 타임스탬프 내용·시점의 정확성(AI 생성물이라 검토 필요).
- 해시태그 최종 선택.

## 좋은 요청 예시

```text
YouTube Studio 최신 영상 5개 설명란 정리해줘.
기존에 타임스탬프/해시태그 있는 건 그대로 두고, 빠진 것만 채워줘.
노래 영상은 해시태그만. 저장 전에 최종 설명 보여주고 물어봐.
```
