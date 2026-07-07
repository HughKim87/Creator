# 프로젝트 내부 도구

이 폴더는 영상 분석/편집 자동화에 필요한 로컬 도구를 둔다.

## 현재 상태

`workspace/`와 기존 `temp/` 내용이 삭제되어 과거 검증 산출물은 남아 있지 않다. 아래 도구 파일 자체는 현재 남아 있다.

| 도구 | 상태 |
|---|---|
| `tools/ffmpeg/bin/ffmpeg.exe` | 존재 |
| `tools/ffmpeg/bin/ffprobe.exe` | 존재 |
| `tools/ffmpeg/bin/ffplay.exe` | 존재 |
| `tools/remux_mkv_to_mp4.bat` | 존재 |
| `tools/synccheck/*.py` | 존재 |

## FFmpeg

- 용도: 프레임 추출, 영상 메타데이터 확인, 러프컷 생성
- 설치 위치: `tools/ffmpeg/`
- 실행 파일:
  - `tools/ffmpeg/bin/ffmpeg.exe`
  - `tools/ffmpeg/bin/ffprobe.exe`
  - `tools/ffmpeg/bin/ffplay.exe`
- 기록된 버전: `8.1.2-essentials_build-www.gyan.dev`
- 설치일: 2026-07-02

실행에 필요 없는 FFmpeg 부속 문서와 preset은 현재 남아 있지 않다. 실행 파일이 남아 있으므로 영상 작업에는 지장이 없다.

## Python

- 프로젝트 내부에 별도 Python 배포판은 포함하지 않았다.
- 2026-07-02 검증에 사용했던 실행 파일:
  - `C:\Users\Hugh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- 스킬 문서의 `<python>`은 실제 사용 가능한 Python 실행 파일로 바꿔 실행한다.

## remux_mkv_to_mp4.bat

OBS 녹화본(mkv)을 Premiere CS6에서 쓸 수 있게 mp4로 무손실 변환하는 공용 도구.

- 사용법: `.mkv` 파일을 bat 파일 위로 드래그&드롭
- 결과: 원본 옆에 `<원본이름>_remux.mp4` 생성
- 같은 이름의 결과 파일이 있으면 건너뜀
- 내부적으로 `tools/ffmpeg/bin/ffmpeg.exe` 사용

## 검증 상태

과거 검증 산출물은 삭제됐다. 새 원본 영상이 들어오면 아래 순서로 다시 확인한다.

1. `ffmpeg.exe -version` 실행 확인
2. `ffprobe.exe`로 원본 길이 확인
3. `video-watch`로 짧은 구간 프레임 추출
4. 필요 시 `synccheck`로 컷 경계 검증
