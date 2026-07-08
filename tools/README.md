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
| `tools/run_doccheck.bat` | 존재 |
| `tools/doccheck/check_docs.py` | 존재 |
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

## doccheck

문서와 스킬 정합성을 검사하는 도구다.

```bat
tools\run_doccheck.bat
```

검사 항목:

- 필수 루트 문서 존재
- 오래된 상태 문구와 동적 커밋 상태 고정
- 과거 세션 절대경로와 과거 원본 파일명
- 기본 로드 문서 과대화 경고
- `skills/*/SKILL.md`의 입력, 출력, 게이트, 중단 조건, AI 확정 금지, 요청 예시

문서나 스킬을 수정한 뒤 최종 답변 전에 실행한다.

## 검증 상태

과거 검증 산출물은 삭제됐다. 새 원본 영상이 들어오면 아래 순서로 다시 확인한다.

1. `ffmpeg.exe -version` 실행 확인
2. `ffprobe.exe`로 원본 길이 확인
3. `video-watch`로 짧은 구간 프레임 추출
4. 필요 시 `synccheck`로 컷 경계 검증

## synccheck

`tools/synccheck/`의 스크립트는 새 원본 경로와 컷리스트를 명령행 인자로 받아 실행한다. 과거 세션 절대경로나 특정 백룸 원본 파일명은 기준으로 삼지 않는다.

예시:

```powershell
python tools\synccheck\vadcheck.py "workspace\inputs\원본.mp4" "workspace\inputs\원본.srt" --clip "B03:00:12:10-00:13:00"
python tools\synccheck\align.py "workspace\inputs\원본.mp4" "workspace\inputs\원본.srt" --clip "B03:00:12:10-00:13:00"
python tools\synccheck\full_scan.py "workspace\inputs\원본.mp4" "workspace\outputs\07_edit_export\cutlist.csv"
python tools\synccheck\build_v9.py "workspace\outputs\07_edit_export\cutlist.csv" "workspace\outputs\07_edit_export\cutlist_adjusted.csv" --start 3=00:12:09.5
```

- `full_scan.py`는 제안만 출력하고 파일을 수정하지 않는다.
- `build_v9.py`는 명시한 경계 수정만 반영해 새 CSV를 만든다. 기존 CSV는 덮어쓰지 않는다.
