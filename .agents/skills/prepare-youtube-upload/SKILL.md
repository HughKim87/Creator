---
name: prepare-youtube-upload
description: 완성 영상, 승인된 제목·썸네일, SRT, 설명과 설정을 검증해 사용자가 직접 업로드할 네 파일만 최종 outputs에 남기고 기술 자료와 이전 산출물은 별도 work archive로 이동하는 수동 YouTube 업로드 패키지를 만든다. 사용자가 업로드 자료 준비, 최종 폴더 정리, 영상 제작 워크플로 완료를 요청할 때 사용한다. YouTube Studio는 조작하지 않는다.
---

# Prepare YouTube Upload

로컬 업로드 자료와 복사 가능한 가이드를 만든다. 브라우저나 YouTube를 조작하지 않는다.

## 입력과 위치

[references/manual-upload-package-format.md](references/manual-upload-package-format.md)에 따라 새 작업은 `youtube-manual-upload-v3` JSON을 `extension/work/<job-id>/`에 둔다.

- 영상·썸네일·SRT는 `extension/outputs/<job-id>/`에 둔다.
- 제목·썸네일 패키지와 기술 메타데이터는 `work/<job-id>/`에 둔다.
- 가이드는 `outputs/<job-id>/YOUTUBE-MANUAL-UPLOAD.md`로 생성한다.
- `outputs/<job-id>/`의 최종 파일은 MP4·썸네일·SRT·가이드 네 개뿐이다.

## 검증과 가이드

먼저 쓰기 없이 검증한다.

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

검증이 통과하면 가이드를 생성한다.

```powershell
python scripts/prepare_upload_package.py <youtube-manual-upload.json>
```

## 최종 폴더 정리

가이드 생성 후 archive 계획을 먼저 확인한다.

```powershell
python scripts/retain_upload_package.py <youtube-manual-upload.json>
```

계획이 `status: ready`이고 archive 대상이 `outputs/<job-id>/`의 비최종 파일만 가리키는지 확인한 뒤 적용한다.

```powershell
python scripts/retain_upload_package.py <youtube-manual-upload.json> --apply
```

- 파일을 삭제하지 않고 `work/<job-id>/archive/`로 이동한다.
- 기존 archive 파일을 덮어쓰지 않는다.
- 디렉터리, 심볼릭 링크, output 밖의 경로는 이동하지 않는다.
- 적용 후 dry-run을 다시 실행해 archive 대상과 예상치 못한 디렉터리가 모두 비어 있는지 확인한다.

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

최종 보고에는 네 파일의 절대 경로와 archive 경로를 반환한다. 이후 수동 업로드 여부를 blocker나 후속 작업으로 남기지 않는다.
