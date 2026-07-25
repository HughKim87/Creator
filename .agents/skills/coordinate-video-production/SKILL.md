---
name: coordinate-video-production
description: 영상 하나의 NotebookLM 리서치·동영상 생성·SRT·제목과 썸네일·수동 YouTube 업로드 준비 단계를 작업 기록으로 관리하고 다음에 실행할 정확한 스킬을 선택한다. 사용자가 새 영상 제작을 시작하거나, 진행 중인 영상의 다음 단계를 묻거나, 여러 제작 단계를 이어서 진행해 달라고 할 때 사용한다.
---

# Coordinate Video Production

영상별 상태만 관리하고 기존 5개 제작 스킬을 순서대로 연결한다. 각 단계의 실제 작업은 해당 스킬에 맡긴다.

## 작업 기록

새 영상마다 `extension/work/<job-id>/VIDEO_JOB.json`을 하나 만든다. 생성하거나 변경할 때 [references/video-job-format.md](references/video-job-format.md)를 읽는다.

- `job-id`는 `YYYY-MM-DD-topic-slug` 형식의 짧은 영문 소문자 ID로 정한다.
- NotebookLM 단계의 기본 브라우저는 Chrome, 기본 프로필 표시명과 디렉터리는 `Profile 4`로 기록한다. 사용자가 다른 프로필을 명시한 경우에만 바꾼다.
- 보호 원본은 `extension/inputs/<job-id>/`, 파생 산출물은 `extension/outputs/<job-id>/`에 둔다.
- 모델과 도구 의존성은 `extension/.runtime/`에 둔다.
- 영상·음성·자막·썸네일·로그를 Git에 추가하지 않는다.
- 완료된 단계의 실제 산출물 경로와 검증 결과만 작업 기록에 남긴다.

## Chrome 연결 게이트

`research` 또는 `video` 단계 전에 다음을 적용한다.

1. 작업 기록의 `browser.profile_directory`와 `required_origin`을 입력으로 `$connect-chrome-profile`을 먼저 실행한다. 기존 기록에 `profile_directory`가 없으면 `Profile 4`로 보완한다.
2. 연결 스킬이 `connected`와 검증 방법을 반환할 때만 단계 스킬을 실행하고, 그 스킬이 넘긴 Chrome 바인딩과 탭을 재사용한다.
3. 연결 스킬이 공식 진단·프로필 대상 dry-run·사용자 승인 후 프로필 창 실행·연결 재시도를 완료하기 전에는 수동 프로필 전환을 요구하거나 작업 상태를 `needs_user`로 바꾸지 않는다.
4. 탭 제어 API가 Chrome 프로필 메뉴를 누르지 못한다는 이유만으로 지정 프로필 창을 열 수 없다고 보고하지 않는다.
5. 같은 Codex 작업의 살아 있는 검증 컨텍스트는 사용자 턴 사이에 재사용한다. 새 Codex 작업 또는 새 브라우저 런타임에서는 과거 `connected` 기록과 관계없이 다시 검증한다.
6. 내장 브라우저, 다른 계정, 별도 Playwright, Computer Use 또는 웹 검색으로 우회하지 않는다.

## 단계 선택

아래 순서를 고정한다.

| 단계 | 사용할 스킬 | 완료 근거 |
|---|---|---|
| `research` | `$notebooklm-research-topic` | 노트북 URL, 출처 수, 출처 품질 게이트 |
| `video` | `$notebooklm-generate-video` | 완성 아티팩트, 길이, 재생·다운로드 가능 상태 |
| `captions` | `$video-to-srt` | MP4, 검증된 SRT, 원본 전사 JSON |
| `title_thumbnail` | `$youtube-title-thumbnail` | 승인된 제목, 썸네일, 검증 패키지 |
| `upload_package` | `$prepare-youtube-upload` | 수동 업로드 안내서와 `external_actions: none` 검증 |

`VIDEO_JOB.json`에서 첫 번째 `pending` 단계를 다음 단계로 선택한다. 앞 단계가 모두 `complete`가 아니면 뒤 단계를 시작하지 않는다.

## 실행 규칙

1. 작업 기록과 실제 산출물의 존재를 먼저 확인한다.
2. `in_progress`, `needs_user`, `blocked` 단계가 있으면 새 단계를 시작하지 않고 그 상태부터 처리한다.
3. 다음 단계 하나만 해당 스킬로 실행한다.
4. NotebookLM 리서치·영상 생성처럼 시간이 필요한 작업은 해당 스킬의 대기 규칙을 따른다. 영상 생성 완료 확인은 5분 간격으로만 수행한다.
5. 단계 산출물을 검증한 뒤 상태를 `complete`로 바꾸고 경로·URL·검증 요약을 기록한다.
6. 한 단계를 마칠 때마다 결과와 다음 단계를 보고하고 멈춘다. 사용자의 다음 진행 지시 없이 연속 실행하지 않는다.

## 사용자 확인 게이트

- `$connect-chrome-profile`이 공식 복구 절차를 완료한 뒤 `needs_user` 또는 `unavailable`을 반환하면 그 결과와 필요한 사용자 행동을 기록한다.
- 생성·권한·유료 사용 문제가 있으면 `blocked`로 기록한다.
- 제목과 썸네일은 사용자 승인 전까지 `title_thumbnail`을 완료로 처리하지 않는다.
- 실제 YouTube 업로드·게시·공개 범위 변경은 단계에 포함하지 않는다. 마지막 단계는 수동 업로드 자료 준비로 끝낸다.

## 완료

다섯 단계가 모두 `complete`이고 마지막 패키지가 `external_actions: none`이면 작업 상태를 `complete`로 바꾼다. 기존 업로드가 기록되어 있으면 중복 업로드 경고를 유지한다.

반환한다.

- job ID와 작업 기록 경로
- 현재 완료 단계와 검증 근거
- 현재 blocker 또는 필요한 사용자 행동
- 다음 단계와 사용할 스킬
- 최종 완료 시 영상·SRT·썸네일·수동 업로드 안내서 경로
