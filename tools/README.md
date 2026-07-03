# 프로젝트 내부 도구

이 폴더는 영상 분석/편집 자동화에 필요한 휴대용 실행 파일과 의존성 정보를 둔다.

## FFmpeg

- 용도: 프레임 추출, 영상 메타데이터 확인, 러프컷 생성
- 설치 위치: `tools/ffmpeg/`
- 실행 파일:
  - `tools/ffmpeg/bin/ffmpeg.exe`
  - `tools/ffmpeg/bin/ffprobe.exe`
  - `tools/ffmpeg/bin/ffplay.exe`
- 버전: `8.1.2-essentials_build-www.gyan.dev`
- 다운로드 출처:
  - FFmpeg 공식 다운로드 안내: https://ffmpeg.org/download.html
  - Windows 빌드: https://www.gyan.dev/ffmpeg/builds/
  - 패키지: `ffmpeg-release-essentials.zip`
- SHA256: `DB580001CAA24AC104C8CB856CD113A87B0A443F7BDF47D8C12B1D740584A2EC`
- 설치일: 2026-07-02

대용량 바이너리는 `.gitignore`에서 제외한다. 프로젝트 안에는 두되, Git에는 문서와 설정만 남긴다.

## 실행 예시

```powershell
tools\ffmpeg\bin\ffmpeg.exe -version
tools\ffmpeg\bin\ffprobe.exe -version
```

`video-watch` 스킬은 시스템 PATH에 FFmpeg가 없어도 이 프로젝트 내부 경로를 자동으로 찾도록 보완했다.

## Python

- 용도: 영상 분석/편집 보조 스크립트 실행
- 프로젝트 내부에 별도 Python 배포판은 포함하지 않았다.
- 2026-07-02 검증에 사용한 실행 파일:
  - `C:\Users\Hugh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- 현재 Windows `py` 런처는 존재하지만 기본 Python 버전이 연결되어 있지 않아 바로 실행되지 않는다.
- 스킬 문서의 `<python>`은 사용 가능한 Python 실행 파일로 바꿔 실행한다.

## 검증 결과

성공:

```powershell
C:\Users\Hugh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  skills\video-watch\scripts\watch.py `
  workspace\inputs\crazy_arcade\2026-06-26 19-42-34.mkv `
  --no-whisper --start 00:02:00 --end 00:03:00 `
  --max-frames 6 --resolution 1024 `
  --out-dir temp\video-watch\install_verify_000200_000300_utf8
```

산출 프레임:

- `temp/video-watch/install_verify_000200_000300_utf8/frames/frame_0001.jpg`
- `temp/video-watch/install_verify_000200_000300_utf8/frames/frame_0004.jpg`

추가 검증:

- 2026-07-02에 원본을 다시 가져온 뒤 `workspace/inputs/crazy_arcade/2026-06-26 19-42-34.mkv`
  크기가 약 6.69GB로 바뀌었다.
- FFprobe 기준 길이 `02:24:42`, 끝부분 패킷 `8681.x`초까지 확인됐다.
- `02:15:00` 단일 프레임 추출과 `02:15:00-02:20:00` 구간 프레임 추출이 성공했다.
- 이 원본 기준으로 후반부 화면 분석과 러프컷 생성이 가능하다.
- Premiere XML 생성 도구 `skills/premiere-editing-export/scripts/make_premiere_xml.py` 문법 검사를 통과했다.
- `CRA_PLAY_EDIT_ASSIST_3P_TEST.xml`, `CRA_PLAY_EDIT_ASSIST_V1.xml` 생성과 XML 파싱 검증이 성공했다.

## remux_mkv_to_mp4.bat (2026-07-03 추가)

OBS 녹화본(mkv)을 Premiere CS6에서 쓸 수 있게 mp4로 무손실 변환하는 공용 도구.

- 사용법: `.mkv` 파일(여러 개 가능)을 이 bat 파일 위로 드래그&드롭
- 결과: 원본 옆에 `<원본이름>_remux.mp4` 생성 (재인코딩 없음, `-c copy`)
- 같은 이름의 결과 파일이 있으면 건너뜀 (덮어쓰기 안 함)
- 내부적으로 `tools/ffmpeg/bin/ffmpeg.exe` 사용
