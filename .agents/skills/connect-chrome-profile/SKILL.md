---
name: connect-chrome-profile
description: 사용자가 지정한 Chrome 프로필을 공식 ChatGPT Chrome Extension 복구 절차로 열고, 정확한 확장 인스턴스와 대상 웹 탭의 로그인 상태를 검증해 후속 브라우저 작업에 넘기는 스킬. Profile 4 같은 특정 프로필로 NotebookLM을 사용해야 하거나, 새 Codex 작업에서 이전 Chrome 연결이 이어지지 않거나, 잘못된 프로필·확장 통신 실패·대상 탭 누락을 복구해야 할 때 사용한다.
---

# Chrome 프로필 연결

지정 프로필을 탭 안의 프로필 메뉴로 전환하려 하지 말고, Chrome 플러그인이 제공하는 공식 진단·프로필 창 실행 경로로 연결한다. 연결이 검증되기 전에는 NotebookLM 작업을 시작하지 않는다.

## 입력

- `profile_directory`: Chrome 프로필 디렉터리 식별자. 기본값은 `Profile 4`.
- `target_origin`: 연결 후 열 사이트. NotebookLM 작업의 기본값은 `https://notebooklm.google.com`.
- 선택적 Chrome 탭 멘션: 사용자가 특정 탭을 공유했다면 그 멘션의 `browserId`와 탭 식별자를 최우선 증거로 사용한다.

`Profile 4`는 사용자가 지정한 로컬 프로필 식별자일 뿐 계정 주소가 아니다. 계정 주소, 쿠키, 토큰, 비밀번호 또는 브라우저 저장소로 프로필을 추론하지 않는다.

## 필수 원칙

1. 브라우저 작업 전에 `chrome:control-chrome`를 끝까지 읽고 Chrome 확장 surface를 명시적으로 선택한다.
2. 선택한 Chrome의 전체 `documentation()`을 읽고, 세션 이름을 정한 뒤 가벼운 `openTabs()` 호출로 통신을 확인한다.
3. 같은 Codex 작업의 살아 있는 Chrome 바인딩과 검증 컨텍스트는 다음 사용자 턴에도 재사용한다. 탭 누락만으로 브라우저를 다시 선택하지 않는다.
4. 새 Codex 작업 또는 새 브라우저 런타임에서는 프로필을 다시 검증한다. `VIDEO_JOB.json`의 과거 `connected` 값만 신뢰하지 않는다.
5. 내장 브라우저, 기본 브라우저 자동 선택, 별도 Playwright, Computer Use 또는 웹 검색으로 우회하지 않는다.
6. 탭 제어 API에 프로필 메뉴 전환 기능이 없다는 이유만으로 `Profile 4를 열 수 없다`고 결론 내리지 않는다. 아래 공식 복구 절차를 먼저 완료한다.
7. 공식 복구 절차가 끝나기 전에는 사용자에게 수동 프로필 전환을 요구하거나 작업 상태를 `needs_user`로 바꾸지 않는다.

## 연결 절차

### 1. 현재 런타임 확인

1. 같은 런타임에 해당 `profile_directory`가 검증된 Chrome 바인딩이 있으면 재사용한다.
2. 명시적으로 멘션된 Chrome 탭이 있으면 Chrome 문서의 Tab Claiming 절차로 정확한 브라우저 인스턴스와 탭을 선택한다.
3. 그 외에는 확장 브라우저 목록과 열린 탭의 안전한 메타데이터만 기준선으로 보관한다. 브라우저 프로필 파일이나 계정 정보를 직접 읽지 않는다.

### 2. 확장 통신 실패 진단

첫 가벼운 연결 호출이 실패하면 2초 기다린 뒤 같은 호출을 한 번만 재시도한다. 다시 실패할 때만 `await agent.documentation.get("chrome-troubleshooting")`를 끝까지 읽고 공식 진단 순서를 적용한다.

1. Chrome 플러그인 루트의 공식 `check-extension-installed.js --json`을 사용한다.
2. `CODEX_CHROME_PREFERENCES_PATH`를 기본 Chrome 사용자 데이터 루트 아래 `<profile_directory>/Preferences`로 한정해 지정 프로필만 검사한다.
3. 스크립트 결과에서는 `selectedProfileDirectory`, `installed`, `enabled`, `exitCode`만 판단에 사용한다. 전체 진단 출력이나 로컬 절대 경로를 작업 기록에 저장하지 않는다.
4. `selectedProfileDirectory`가 요청값과 다르면 중단한다. 확장이 없거나 비활성화되어 있으면 필요한 설치·활성화 조치만 사용자에게 요청한다.
5. 직접 `Preferences`, `Secure Preferences`, `Extensions` 또는 다른 프로필 파일을 열어 읽지 않는다.
6. 한 번 통신에 성공한 뒤에는 해당 런타임에서 확장 감지를 반복하지 않는다. 지정 프로필 창을 연 뒤 그 프로필의 새 연결이 나타나지 않는 경우만 별도의 대상 프로필 통신 실패로 취급한다.

### 3. 지정 프로필 창 열기

현재 바인딩이 지정 프로필이라는 정확한 증거가 없으면 다음을 적용한다. 탭 제어로 Chrome 프로필 메뉴를 누르지 않는다.

1. `CODEX_CHROME_PREFERENCES_PATH`를 지정 프로필로 한정하고 공식 `open-chrome-window.js --dry-run --json`을 실행해 `profileDirectory`가 요청값인지 확인한다.
2. Chrome 문제 해결 문서가 요구하는 사용자 확인을 받은 뒤에만 같은 한정값으로 실제 `open-chrome-window.js`를 실행한다. 자체 PowerShell·셸·브라우저 프로필 메뉴 자동화를 만들지 않는다.
3. 실행 전 확장 인스턴스와 열린 탭 기준선을 보관하고, 실행 후 2초 기다린 뒤 브라우저 목록과 열린 탭을 한 번 다시 확인한다.
4. 실행 전후 차이에서 새로 나타난 브라우저 인스턴스 또는 새 `about:blank` 탭이 하나로 식별되면 그 인스턴스를 선택한다.
5. 대상 프로필의 새 연결이 나타나지 않으면 대상 프로필 통신 실패로 보고, 아직 수행하지 않은 경우에만 2단계의 공식 진단을 한 번 실행한다.
6. 진단 후에도 후보가 여러 개이거나 차이가 없으면 추측하지 않는다. 사용자에게 지정 프로필의 NotebookLM 탭을 Chrome 탭 멘션으로 보내 달라고 요청한다.

### 4. NotebookLM 탭 검증

1. 선택한 인스턴스의 새 탭을 claim하거나 새 탭을 만들고 `target_origin`으로 이동한다.
2. URL이 요청 origin인지, NotebookLM 화면이 로드되는지, 로그인된 서비스 화면인지 가시 상태로 확인한다.
3. 계정 주소를 읽거나 기록하지 않는다. 대상 작업의 노트북 제목·URL 같은 비민감한 작업 상태로 필요한 범위만 확인한다.
4. 같은 런타임에서 재사용할 Chrome 바인딩과 `profile_directory` 검증 컨텍스트를 메모리에 유지한다. 브라우저 ID나 확장 인스턴스 ID는 `VIDEO_JOB.json`에 저장하지 않는다.
5. 위 검증이 모두 성공한 뒤에만 `connected`를 반환한다.

## 실패 처리

- 첫 통신 실패는 Chrome 문제 해결 문서에 따라 2초 후 같은 가벼운 호출을 한 번만 재시도한다.
- 확장·네이티브 호스트 확인이 실패하면 공식 문서가 지정한 사용자 조치를 따른다. 임의로 설치하거나 복구하지 않는다.
- 프로필 대상 실행까지 성공했지만 인스턴스를 유일하게 식별하지 못하면 `needs_user`로 반환하고 정확한 Chrome 탭 멘션을 요청한다.
- 실제 프로필 창 실행이 거부되거나 공식 재시도 후에도 확장 통신이 실패하면 `needs_user` 또는 `unavailable`로 반환한다.
- 실패 시 “프로필 전환 메뉴를 제어할 수 없다”는 사실과 “지정 프로필 창을 공식 방식으로 열 수 없다”는 결론을 혼동하지 않는다.

## 반환 계약

다음 필드를 반환한다.

- `status`: `connected`, `needs_user`, `unavailable`
- `surface`: `chrome`
- `profile_directory`
- `target_origin`
- `verification_method`: `same_runtime`, `explicit_tab_mention`, `profile_targeted_launch`
- `extension_ready`
- `tab_url`
- `retry_count`
- `user_action`: 없으면 빈 문자열

호출 스킬은 `status: connected`일 때만 후속 웹 작업을 시작한다.
