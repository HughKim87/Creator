---
name: connect-chrome-profile
description: 호출자가 전달한 Chrome 프로필 디렉터리를 공식 ChatGPT Chrome Extension 실행 경로로 열고, 실행 델타로 정확한 확장 인스턴스와 대상 웹 탭을 검증해 후속 브라우저 작업에 넘기는 범용 스킬. 특정 프로필로 웹 작업을 시작하거나 새 Codex 작업에서 Chrome 연결을 다시 만들어야 할 때 사용한다.
---

# Chrome 프로필 연결

목표는 하나다. 호출자가 전달한 프로필로 새 Chrome 창을 연 뒤, 그 실행으로 생긴 확장 인스턴스나 탭만 연결한다. `status: connected` 전에는 호출 작업을 시작하지 않는다.

## 입력

- `profile_directory`: 필수. 호출자가 전달한 비어 있지 않은 Chrome 프로필 디렉터리 식별자
- `target_origin`: 필수. 연결 후 열 절대 URL의 origin
- 선택적 Chrome 탭 멘션

이 스킬에는 프로필과 origin 기본값이 없다. 둘 중 하나라도 빠지면 browser runtime을 초기화하거나 Chrome을 열기 전에 `needs_user`를 반환한다.

프로필 이름은 로컬 실행 식별자다. 계정 주소·쿠키·토큰·비밀번호·브라우저 저장소로 프로필을 추론하지 않는다.

## 단일 연결 절차

아래 순서를 그대로 실행하고 다른 연결 경로를 만들지 않는다.

1. `$chrome:control-chrome`를 끝까지 읽는다. 지정 프로필 선택은 이 스킬이 소유하므로 그 스킬의 일반 초기 선택 예시는 적용하지 않는다.
2. 사용자가 Chrome 탭을 명시적으로 멘션했다면 문서의 Tab Claiming 절차로 exact 브라우저와 탭을 검증하고 9번으로 간다.
3. 같은 런타임에 `profile_directory`와 `target_origin`이 이미 검증된 exact 바인딩이 있으면 가벼운 probe를 한다. 성공하면 재사용하고 9번으로 간다. 명시적 `Browser is not available`·disconnected 오류면 바인딩과 검증값을 폐기한다.
4. browser runtime이 이미 초기화돼 있으면 `agent.browsers.list()`의 모든 extension descriptor를 `agent.browsers.get(descriptor.id)`로 바인딩한다. 각 바인딩의 전체 `documentation()`을 별도 호출에서 먼저 읽고, 다음 호출에서 `user.openTabs()`를 읽어 실행 전 `baseline`을 만든다. fresh 런타임이면 아직 browser runtime을 bootstrap하지 않고 `baseline: []`을 사용한다.
5. `CODEX_CHROME_PREFERENCES_PATH`를 기본 Chrome 사용자 데이터 루트의 `<profile_directory>/Preferences` 경로 문자열로 설정한다. 공식 `open-chrome-window.js --dry-run --json`을 실행하고 `profileDirectory`가 입력값과 정확히 같은지 확인한다.
6. `launch_started_at`을 기록한 직후 같은 환경값으로 공식 `open-chrome-window.js`를 실행한다. 이 명령은 지정 프로필에 새 `about:blank` 창을 연다. fresh 런타임이면 2초 뒤 `$chrome:control-chrome`의 bootstrap block을 정확히 한 번 실행한다.
7. 최대 20초 동안 매초 다음 작업을 반복한다.
   - `agent.browsers.list()`를 다시 호출해 extension backend 목록을 refresh한다.
   - 아직 문서를 읽지 않은 descriptor만 exact `id`로 바인딩하고 전체 문서를 먼저 읽는다.
   - 다음 호출에서 현재 exact 바인딩들의 `user.openTabs()`를 읽어 `current`를 만든다.
   - 필수 선택기 `.agents/skills/connect-chrome-profile/scripts/select-profile-delta.mjs`의 `selectProfileDelta()`를 호출한다. fresh 런타임은 `discoveryMode: "post_launch_initial"`, 기존 런타임은 `discoveryMode: "baseline_delta"`를 사용한다. 후보 선택 코드를 즉석에서 다시 작성하지 않는다.
8. 선택기가 탭을 반환하면 그 exact 바인딩의 `user.claimTab(result.tab)`에 반환된 같은 탭 객체를 넘긴다. `new_browser`를 반환하면 그 exact 바인딩에 새 탭을 만든다. `about:blank`이면 선택된 탭만 `target_origin`으로 이동한다.
9. 탭 URL이 `target_origin`인지, 호출자가 요구한 서비스 화면과 로그인 상태가 충족되는지 가시 상태로 검증한다. 모두 성공한 뒤에만 `connected`를 반환한다.

선택기는 활성 worktree의 절대 경로로 import한다.

```js
const { pathToFileURL } = await import("node:url");
const { selectProfileDelta } = await import(
  pathToFileURL("<active-root>/.agents/skills/connect-chrome-profile/scripts/select-profile-delta.mjs").href
);
```

## 금지

- 연결 전후에 `agent.browsers.get("extension")`, `getDefault()`, `getForUrl()`로 브라우저를 선택하지 않는다.
- 목록 순서, 기존 대상 사이트 탭, 일반 `chrome`·`browser` 바인딩을 요청 프로필의 증거로 사용하지 않는다.
- browser runtime을 reset·재import하거나 내장 브라우저, 별도 Playwright, Computer Use, 웹 검색으로 우회하지 않는다.
- `Preferences`, `Secure Preferences`, `Extensions` 등 브라우저 프로필 파일을 읽거나 열거하지 않는다. 따라서 해당 파일을 읽는 `check-extension-installed.js`도 실행하지 않는다.
- 검증 전 사용자에게 프로필 메뉴 전환을 요구하지 않는다.

## 실패

- 실제 확장 통신 실패는 Chrome 문제 해결 문서에 따라 2초 후 같은 호출을 한 번만 재시도한다.
- 20초 뒤에도 선택기가 유일한 실행 델타를 찾지 못하면 추측하지 않는다. `status: unavailable`, `selection_reason: profile_launch_delta_not_found`를 반환한다.
- 공식 프로필 실행이나 확장 통신 자체가 실패하면 확인된 오류를 반환한다. 설치 점검이 필요하면 프로필 파일을 읽지 않는 공식 `installed-browsers.js`, `chrome-is-running.js`, `check-native-host-manifest.js`만 사용한다.
- `unavailable`일 때만 필요한 사용자 조치를 요청한다. 다른 프로필이나 기존 인스턴스를 성공 처리하지 않는다.

## 반환

- `status`: `connected`, `needs_user`, `unavailable`
- `surface`: `chrome`
- `profile_directory`
- `target_origin`
- `verification_method`: `same_runtime`, `explicit_tab_mention`, `profile_targeted_launch`
- `selection_mode`: `same_runtime`, `explicit_tab_mention`, `post_launch_initial`, `existing_browser_new_tab`, `new_browser`
- `selection_reason`
- `extension_ready`
- `tab_url`
- `retry_count`
- `user_action`: 없으면 빈 문자열

호출 스킬은 `status: connected`일 때만 후속 웹 작업을 시작한다. 브라우저 ID와 확장 인스턴스 ID는 메모리에서만 사용하고 작업 파일에 저장하지 않는다.
