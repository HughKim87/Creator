---
name: connect-chrome-profile
description: 호출자가 전달한 Chrome 프로필을 공식 실행 도구로 열고, 현재 제공되는 브라우저 제어 API와 실행 전후 델타로 정확한 탭을 검증한다. 특정 프로필로 웹 작업을 시작하거나 영상 제작 중 Chrome 연결을 재사용·복구할 때 사용한다.
---

# Chrome 프로필 연결

호출자의 프로필과 서비스에 연결된 정확한 Chrome 탭을 반환한다. 목적은 프로필과 로그인 상태의 보장이며 특정 플러그인 이름이나 예전 API의 존재가 아니다.

## 입력

- `profile_directory`: 필수. 호출자가 전달한 프로필 디렉터리 식별자.
- `target_origin`: 필수. 호출자가 전달한 HTTPS 서비스 origin.
- 선택적 Chrome 탭 멘션.

이 스킬에는 프로필과 origin 기본값이 없다. 빠진 값만 `needs_user`로 반환한다. 프로필 이름은 실행 식별자다. 프로필 파일·쿠키·계정 주소로 이를 추론하지 않는다.

## 도구와 실행 경로

현재 세션의 `mcp__cua_repl.js`를 사용한다. 이 도구의 첫 호출은 도구 안내대로 `await cua.getState();` 하나만 실행해 문서와 실행 전 목록을 읽는다. 이미 초기화했다면 같은 런타임을 재사용한다. Chrome 탭을 바인딩할 때 자동 반환되는 전체 브라우저 문서도 먼저 읽는다.

`chrome:control-chrome`나 예전 `agent.browsers.*` 스킬 파일이 없다는 이유로 중단하지 않는다. 오래된 cache·backup 스킬을 활성 플러그인으로 대신 가져오지 않는다. 실제 호출 도구가 노출되지 않은 경우에만 도구 검색과 노출된 지원 API 문서를 확인하고 `control_tool_unavailable`로 구분한다. 도구 부재와 확장 연결 부재, 로그인 필요를 혼동하지 않는다.

프로필 실행은 `scripts/launch-profile.py`가 현재 설치된 공식 Chrome 패키지의 `open-chrome-window.js --dry-run --json`을 찾아 검증한다. 버전 경로나 SKILL.md 존재를 하드코딩하지 않는다.

```powershell
python .agents/skills/connect-chrome-profile/scripts/launch-profile.py --profile-directory <caller-profile>
```

기본 명령은 실행 계획만 확인한다. `profileDirectory`가 입력과 같고 `status: ready`일 때만 같은 명령에 `--launch`를 추가한다. 런처는 프로필 경로 문자열을 환경변수에 설정할 뿐 파일을 읽지 않는다. `launch_requested`는 접수 결과이며 연결 성공이 아니다.

## 연결·재사용

1. 같은 런타임에서 이 스킬이 이미 검증한 `profile_directory`와 `target_origin`의 바인딩이 있으면 탭의 가시 상태와 URL을 probe한다. 정상이라면 창을 다시 열지 않고 `same_runtime`으로 재사용한다. 탭만 사라졌다면 검증된 브라우저 ID로 탭을 복구하고 확인한다. 새 런타임에서는 파일에 기록된 connected만으로 프로필을 믿지 않는다.
2. 새 연결에는 `cua.getState()`의 실행 전 목록을 baseline으로 보관한다. Chrome이 아직 목록에 없어도 정상적인 연결 전 상태이며, 설치 부재로 판정하지 않는다.
3. 공식 런처 dry-run을 확인하고 실행 직전 시각을 기록한 뒤 `--launch`를 한 번 실행한다. 백그라운드 런처의 종료를 무한히 기다리지 않고 실제 목록 변화를 확인한다.
4. 최대 20초 동안 실행 후 `cua.getState()`로 목록을 갱신한다. `scripts/select-profile-delta.mjs`의 `normalizeChromeSnapshot`으로 Chrome extension만 추리고 `selectProfileDelta`에 baseline과 current를 전달한다. 현재 API에서는 항상 실행 전 목록을 얻으므로 `discoveryMode: "baseline_delta"`를 사용한다. 빈 목록도 baseline이다.
5. 유일한 실행 델타가 선택되면 `cua.getTab(result.tab.id, { browser: result.browserId })`로 정확한 탭을 바인딩한다. 새 브라우저만 선택되고 탭이 없으면 `cua.createBrowserTab(result.browserId, target_origin, { sessionName: "🔎 영상 제작" })`로 같은 브라우저에 생성한다. 일반 `"chrome"` 별칭, 목록 순서, 기존 서비스 탭을 프로필 근거로 사용하지 않는다.
6. about:blank인 선택 탭만 `tab.goto(target_origin)`으로 이동한 뒤 `tab.getAXState()`를 읽는다. 브라우저 문서의 `tab.playwright`는 같은 탭 안에서 지원되는 제어 API이며 별도 Playwright가 아니다.
7. 서비스 화면과 로그인 상태, origin을 확인한다. `matchesTargetOrigin`은 정확한 origin 외에 확인된 NotebookLM 이전 주소 `https://notebooklm.google.com` → `https://notebook.google.com`만 허용한다. 이 경우 입력은 유지하고 `resolved_origin`을 결과와 작업 기록에 추가한다. 유사 도메인이나 임의의 redirect는 허용하지 않는다.
8. 연결된 탭과 메모리의 바인딩을 후속 단계에 그대로 넘긴다. 단계가 바뀌었다고 새 창·새 연결·새 노트북을 만들지 않는다.

선택기 import는 파일 처리용 Node 도구에서 활성 작업 root의 절대 경로로 한다. 브라우저 조작은 `cua_repl`에서만 수행한다. 선택기는 가시 목록을 받는 순수 함수이며 브라우저 저장소를 읽지 않는다.

## 실제 오류의 처리

- 확장 통신 오류가 실제 발생하면 현재 도구의 제공된 문제 해결 문서를 먼저 읽고 같은 호출을 한 번만 재시도한다. 동일 원인의 무진전 반복은 하지 않는다.
- 20초 뒤 실행 델타가 없으면 `profile_launch_delta_not_found`, 여러 후보면 `profile_launch_delta_ambiguous`로 반환한다. 이를 플러그인 미설치라고 단정하지 않는다.
- 공식 런처가 없으면 `launcher_unavailable`, 실행 오류면 `profile_launch_failed`, 로그인 화면이면 `login_required`로 필요한 조치만 설명한다.
- 런처 실행 프로세스의 성공 응답보다 실제 Chrome 목록과 서비스 가시 상태가 연결의 완료 근거다.
- `Preferences`, `Secure Preferences`, `Extensions` 등 프로필 파일과 계정 주소·쿠키·비밀번호를 읽거나 기록하지 않는다.
- 내장 브라우저, 다른 프로필, 별도 Playwright, 웹 검색으로 로그인·프로필 검증을 우회하지 않는다. 현재 `cua_repl`의 검증된 Chrome extension 제어는 이 스킬의 정식 실행 경로다.

## 반환과 단계 진행

`status`: `connected`, `needs_user` 또는 `unavailable`.
그 밖의 값은 `surface: chrome`, `profile_directory`, `target_origin`, `resolved_origin`, `verification_method`(`same_runtime`, `explicit_tab_mention`, `profile_targeted_launch`), `selection_mode`, `selection_reason`, `extension_ready`, `tab_url`, `retry_count`, `user_action`.

명시적 탭 멘션은 현재 도구의 `cua.getTab({ mention })`로 검증한다. 멘션만으로 프로필이 증명되지 않으면 프로필 실행 델타 절차를 사용한다.

브라우저 ID·확장 인스턴스 ID·탭 바인딩은 메모리에서만 보관한다. 작업 기록의 프로필·검증 시각·resolved_origin은 재개 입력이며 새 런타임의 검증을 대신하지 않는다. coordinator가 위임된 제작을 수행 중이면 connected 직후 첫 미완료 단계로 이어간다.

## Claude 실행 경로

Claude(Cowork)에는 `cua_repl`과 공식 런처 실행 경로가 없다. 대신 Claude in Chrome 확장 연결을 사용하며, 위 Codex 절차와 같은 입력·반환 계약을 지킨다.

1. `list_connected_browsers`로 연결된 Chrome 확장 목록을 읽는다. 연결이 없으면 `unavailable`과 `user_action`(Chrome 실행·확장 연결)을 반환한다.
2. 활성 worktree의 Git 제외 runtime 설정 `extension/.runtime/video-workflow-defaults.json`의 `claude_in_chrome.device_profiles`에서 입력 `profile_directory`에 등록된 `deviceId`를 찾는다. 등록은 사용자가 해당 확장의 프로필을 직접 확인해 준 경우에만 추가하며, 프로필 파일·쿠키·계정 주소로 추론하지 않는다. 등록이 없거나 등록된 장치가 목록에 없으면 `needs_user`로 확인을 요청한다.
3. 등록된 장치를 `select_browser`로 선택하고 새 탭에서 `target_origin`을 연다. 화면과 로그인 상태, origin을 확인한다. 이전 주소 허용 규칙(`matchesTargetOrigin`)은 Codex 경로와 같다.
4. 성공하면 `verification_method: claude_in_chrome_device`로 `connected`를 반환한다. 장치 ID·탭 ID는 메모리에서만 보관하며 작업 기록에 쓰지 않는다.
5. 내장 브라우저와 다른 장치로 우회하지 않는다. 로그인 화면이면 `login_required`로 반환한다.
