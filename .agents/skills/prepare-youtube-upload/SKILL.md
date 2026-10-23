---
name: prepare-youtube-upload
description: 완성 영상, 승인된 제목·썸네일, SRT, 설명과 설정을 검증해 사용자가 직접 업로드할 네 파일만 최종 outputs에 남기고 기술 자료와 이전 산출물은 별도 work archive로 이동하는 수동 YouTube 업로드 패키지를 만든다. 사용자가 업로드 자료 준비, 최종 폴더 정리, 영상 제작 워크플로 완료를 요청할 때 사용한다. YouTube Studio는 조작하지 않는다.
---

# Prepare YouTube Upload

로컬 업로드 자료와 복사 가능한 가이드를 만든다. 브라우저나 YouTube를 조작하지 않는다.

`coordinate-video-production`에서 호출되면 [하위 스킬 호출 계약](../coordinate-video-production/SKILL.md#하위-스킬-호출-계약)의 요청 경로·범위·종료점에 따라 결과를 반환한다. NotebookLM 전체 제작은 기존 VIDEO_JOB, 게임/부분 작업은 해당 job의 현재 전문 검수·승인·패키지 근거를 사용한다. 후자의 준비를 위해 NotebookLM 생성·가짜 단계 완료를 요구하지 않는다. 가이드 초안 요청은 아래 초안 모드로 처리하고 최종 준비 완료로 기록하지 않는다. 단독 호출에서는 이 스킬의 완료·정지 경계를 적용한다. 최종 자료의 기존 검증·승인·네 파일 계약은 동일하다.

## 입력과 위치

[references/manual-upload-package-format.md](references/manual-upload-package-format.md)에 따라 새 작업은 `youtube-manual-upload-v3` JSON을 `extension/jobs/<job-id>/work/`에 둔다.

- 영상·썸네일·SRT는 `extension/jobs/<job-id>/outputs/`에 둔다.
- 제목·썸네일 패키지와 기술 메타데이터는 `work/<job-id>/`에 둔다.
- 가이드는 `outputs/<job-id>/YOUTUBE-MANUAL-UPLOAD.md`로 생성한다.
- `outputs/<job-id>/`의 최종 파일은 MP4·썸네일·SRT·가이드 네 개뿐이다.

위 네 파일은 **패키지 전용 출력 폴더**의 계약이다. 롱폼과 쇼츠 등 복수 결과를 처음부터 제작하는 작업은 `outputs/upload/`에 이 네 파일, 형제 `outputs/shorts/`에 쇼츠 결과를 둔다. `preparation.output_dir`·`guide`·세 미디어 artifact 경로를 같은 upload 폴더로 맞추고 job의 `paths.output_dir`는 공통 outputs root로 유지한다. 단일 패키지와 기존 배치의 읽기 호환은 유지한다. 기존 파일의 이동·중복 복사는 이 연결만으로 실행하지 않는다.

## 미완성 작업의 가이드 초안

가이드를 먼저 요청받거나 썸네일이 대기·차단된 경우 [초안 형식](references/manual-upload-package-format.md#가이드-초안)을 사용해 `work/<job-id>/YOUTUBE-MANUAL-UPLOAD-DRAFT.md`를 직접 작성한다. 확보한 자료의 제목·설명·설정·수동 업로드 순서를 제공하고 미확정 항목을 표시한다. 영상 내용 검수에서 확인된 문제도 미완성 항목에 포함한다.

이 경로는 최종 JSON의 `ready` 검증을 우회하지 않는다. 초안에는 `prepare_upload_package.py`와 finalizer·retention을 사용하지 않는다. coordinator에는 초안 경로와 남은 항목을 반환하며 기존 제작 단계 상태를 유지한다. 최종 준비 때는 승인된 최신 입력과 내용 검수 결과로 정식 패키지·가이드를 생성한다.

## 검증과 가이드

coordinator가 새 제작·패키지 재완료를 요청하면 먼저 전달된 `publish_timing`을 확인한다. 이 스킬은 브라우저를 열지 않고 coordinator 또는 프로젝트의 [youtube-channel-coach](../youtube-channel-coach/SKILL.md)가 읽기 전용으로 확인한 분석 결과를 사용한다. 정보가 빠졌다면 호출자에게 반환하며 일반적인 오전·저녁 시각을 실측처럼 만들어 넣지 않는다. 단독 호출에서 분석을 요청받지 않았고 전달된 추천도 없으면 기존 패키지 작성 범위를 유지한다.

새 제작·수정본은 승인된 제목과 현재 네 입력 해시, 전달받은 공개 시간 추천을 패키지에 기록한 뒤 `scripts/finalize_upload_package.py <youtube-manual-upload.json> --require-publish-timing`으로 먼저 검증한다. 이때 guide 생성 전 읽기 전용 `retention_preflight`로 출력 소유 범위도 확인한다. 통과하면 `--apply`를 붙여 아래의 검증·가이드 생성·archive 계획/적용·적용 후 재검증을 한 번에 실행한다. 이 도우미는 원문이나 해시를 자동 승인·교정하지 않으며, `--require-editorial` 계약까지 검사한다. 기존 패키지의 열람·검증이나 추천 없는 단독 호출은 이 옵션 없이 호환 검증한다. preflight는 가이드가 아직 없어도 수행할 수 있지만 그 계획을 파일 이동에 적용할 수 없으며 가이드 생성 후 정식 계획을 다시 만든다.

아래는 구버전 호환 또는 실패 진단을 위한 개별 명령이다. 완료 도우미가 성공한 단계는 반복하지 않는다. 개별 실행에서는 먼저 쓰기 없이 검증한다.

```powershell
python scripts/prepare_upload_package.py <youtube-manual-upload.json> --check
```

다음을 확인한다.

- 영상·썸네일·SRT와 제목·썸네일 패키지가 존재하고 비어 있지 않음
- 썸네일이 정확히 1280×720이고 2MB 이하임
- 제목과 썸네일이 승인 패키지와 일치함
- v2 제목·썸네일의 문구·생성·최종 시각 승인이 모두 완료됨
- 제목·썸네일 패키지의 생성·승인 계약이 작업 계약과 일치함
- 영상·썸네일·SRT·제목·썸네일 패키지의 현재 SHA-256이 수동 패키지의 `artifact_hashes`와 일치함
- 채널 ID나 외부 작업 승인이 없음
- final output 파일명이 정확히 네 개임
- coordinator 호출에서는 현재 영상·SRT의 내용 검수가 완료되고 미해결 중대 오류가 없음. 공개할 경미한 한계는 `metadata.description`에 반영해 가이드에도 포함함
- coordinator의 새 제작·재완료에서는 `publish_timing`의 확인 근거·시간대·실측 기반/잠정 구분·한계와 미래의 추천 시각이 검증됨. 가이드 생성기가 「추천 공개 시간」을 렌더하며 이 정보는 YouTube 설명란에 자동 추가하지 않음

검증이 통과하면 가이드를 생성한다.

```powershell
python scripts/prepare_upload_package.py <youtube-manual-upload.json>
```

## 한국어 설명·검색 의도와 챕터

설명 초안을 만들거나 보완할 때 영상이 실제로 답하는 검색 질문을 최대 3개 고르고, 제목과 설명 첫 두 줄이 대상·제공할 답을 자연스럽게 전달하는지 확인한다. 검색 수요를 조사하지 않았다면 `편집상 가정`으로 표시한다. 추천/홈 중심 영상에 키워드를 억지로 반복하지 않는다. 동의어·약칭·게임명·버전명을 자연스럽게 쓰며 태그 개수나 키워드 일치만으로 SEO 효과를 보장하지 않는다. 기존 실적 진단 요청은 `youtube-title-thumbnail`이 담당한다. 승인 제목을 바꾸는 제안은 기존 제목 수정 절차로 반환한다.

챕터 요청 또는 설명 구성에 챕터가 유용한 경우 검증된 **최종 영상 SRT**에서 주제/사건 전환을 먼저 고른다. 기존 설명의 유효한 챕터는 보존하고 누락/오류만 보완한다. 후보 탐색과 시간 검사에 다음 도구를 사용할 수 있다.

```powershell
python -B .agents/skills/prepare-youtube-upload/scripts/chapters.py suggest <최종자막.srt> --duration 600 --target 7
python -B .agents/skills/prepare-youtube-upload/scripts/chapters.py validate <검토챕터.json> --duration 600
```

`suggest`는 한글 어절 변화·발화 사이 간격으로 후보와 근거 발화를 제시한다. 실제 사건 전환·무발화 구간은 화면으로 확인하고 제목을 사람이 작성한다. `target`은 후보 상한이며 분량을 채우는 의무가 아니다. JSON은 `[{"start":"00:00","title":"처음 확인할 질문"},{"start":"00:30","title":"실제 비교"},{"start":"01:10","title":"선택 기준"}]` 형식이다. 한국어 어절 수를 고정하지 않고 짧고 구체적으로 쓴다.

검증은 00:00 시작·최소 3개·오름차순·마지막을 포함한 각 구간 최소 10초·실제 영상 길이를 확인한다. 근거: [YouTube 챕터 도움말](https://support.google.com/youtube/answer/9884579?hl=ko) (2026-10-23 확인). 유효한 형식이어도 계정/영상의 실제 챕터 표시는 별도이며 도구가 보장하지 않는다. 짧거나 전환이 없는 영상에는 챕터를 억지로 만들지 않는다.

검토·검증한 블록만 기존 `metadata.description`에 포함해 가이드로 전달한다. 초안은 work 근거로 두며 최종 output 네 파일을 늘리지 않는다. 프로젝트의 [youtube-timestamp-hashtag](../youtube-timestamp-hashtag/SKILL.md)가 기존 게시물 설명을 처리할 때도 같은 시간·내용 검토를 재사용할 수 있으나 이 스킬은 Studio를 조작하지 않는다. 참고 아이디어: [yt-seo](https://github.com/Jakeschincariol/youtube-agent-skill/tree/main/skills/yt-seo), [yt-chapters](https://github.com/Jakeschincariol/youtube-agent-skill/tree/main/skills/yt-chapters).

## 최종 폴더 정리

가이드 생성 후 archive 계획을 먼저 확인한다.

```powershell
python scripts/retain_upload_package.py <youtube-manual-upload.json>
```

계획이 `status: ready`이고 `unowned_outputs`·`unexpected_directories`가 비어 있으며 archive 대상이 `preparation.output_dir` 안의 이 패키지 소유 비최종 파일만 가리키는지 확인한 뒤 적용한다. 형제 쇼츠 폴더는 정리 범위가 아니다. 같은 폴더의 미디어·ZIP·자막 등 다른 결과는 기본적으로 이동하지 않고 `unowned_outputs`로 반환해 적용을 차단한다. 과거 패키지의 중간 결과임이 확인된 파일만 `preparation.archive_files`에 정확한 파일명으로 기록할 수 있으며, 쇼츠 같은 별도 최종 결과를 이 목록에 넣지 않는다.

```powershell
python scripts/retain_upload_package.py <youtube-manual-upload.json> --apply
```

- 파일을 삭제하지 않고 `work/<job-id>/archive/`로 이동한다.
- 기존 archive 파일을 덮어쓰지 않는다.
- 디렉터리, 심볼릭 링크, output 밖의 경로는 이동하지 않는다.
- 적용 후 dry-run을 다시 실행해 archive 대상과 예상치 못한 디렉터리가 모두 비어 있는지 확인한다.
- 적용 후 `unowned_outputs`도 비어 있어야 한다. 계획 뒤 결과가 추가되거나 archive 원본 해시가 바뀌면 재계획하며 기존 계획으로 이동하지 않는다.

이 archive 이동은 사용자가 승인한 영상 완성 절차다. 실행 전에는 항상 정확한 파일 목록을 dry-run으로 확인한다.

## Manual-only 경계

- Chrome, YouTube Studio와 YouTube API를 열거나 조작하지 않는다.
- 업로드, 메타데이터 저장, 자막 추가, 공개 범위 변경, 게시·예약·삭제·교체를 하지 않는다.
- 채널명만 기록하고 대상 채널은 사용자가 Studio에서 직접 확인한다.
- 로컬 패키지와 가이드가 검증되고 최종 output 계약이 충족되면 에이전트 작업은 완료다.

## 완료 기준

- `prepare_upload_package.py --check`가 `status: ready`, errors·warnings 0
- 가이드 생성 완료
- archive 적용 후 `outputs/<job-id>/`에 정확히 네 파일만 존재
- retention 재검증의 archive 대상과 예상치 못한 디렉터리 0
- `external_actions: none`

공개 시간 추천은 가이드 안에 보존한다. 분석은 `youtube-channel-coach`가, 로컬 렌더링은 이 스킬이 소유하며 추천은 예약 실행 권한을 뜻하지 않는다.

최종 보고에는 네 파일의 절대 경로와 archive 경로를 반환한다. 이후 수동 업로드 여부를 blocker나 후속 작업으로 남기지 않는다.

## main의 작업별 폴더

새 작업은 `scripts/creator_job.py init --job <job-id>`로 만든 main의 `extension/jobs/<job-id>/`를 사용한다. coordinator가 전달한 기존 작업은 그 exact 경로를 재사용하며 자동 이동하지 않는다. 로컬 명령은 job runner 안에서 실행하고 출력·검수·임시 파일을 해당 job에 기록한다. 도구·모델은 `creator_job.py runtime --component <component>`가 반환한 공용 경로를 사용한다. 다른 job의 파일·승인·현재 프로필로 대체하지 않는다.
