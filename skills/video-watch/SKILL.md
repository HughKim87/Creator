---
name: video-watch
description: |
  Claude가 영상을 직접 "보고" 분석하게 하는 스킬. ffmpeg로 프레임을 추출하고 자막/전사와 함께 읽어
  영상 내용을 파악한다. 로컬 녹화본(mkv 등)과 YouTube 등 URL 모두 지원.
  "이 영상 봐줘", "영상에서 무슨 일이 일어나는지 확인해줘", "이 유튜버 영상 훅 분석해줘",
  "몇 분 몇 초에 뭐가 나오는지 봐줘" 같은 요청에서 사용한다.
license: MIT (원본: bradautomates/claude-video v0.2.0)
---

# video-watch — 영상 시청/분석

Claude는 영상 입력이 없다. 이 스킬은 `scripts/watch.py`로 프레임(JPEG)과
타임스탬프 전사를 만들어, Claude가 프레임을 `Read`로 보고 전사와 결합해
영상 내용에 근거한 답을 하게 한다.

원본: https://github.com/bradautomates/claude-video (MIT). 이 폴더의 사본은
김실버 프로젝트용으로 관리한다.

## 이 프로젝트에서의 두 가지 용도

1. **내 녹화본 분석** (로컬 mkv): 하이라이트/컷포인트 탐색.
   - 원본 mkv 옆에 이미 `.srt` 자막이 있으면 **Whisper를 쓰지 말고**
     `--no-whisper`로 프레임만 뽑고, srt를 직접 Read해서 전사로 사용한다.
     (기존 Whisper 복구 자막이 더 정확하고, API 비용이 없다)
   - `gameplay-video-analysis` 스킬의 "화면 검증" 단계에서 후보 구간을
     `--start/--end`로 집중 추출하는 데 쓴다.
2. **타 채널 벤치마킹** (YouTube URL): 잘되는 게임 영상의 훅(첫 3~10초),
   구성, 화면 연출 분석. yt-dlp가 자막을 무료로 가져온다.

## 실행 준비

- `SKILL_DIR` = 이 SKILL.md가 있는 폴더의 절대 경로. 스크립트는
  `SKILL_DIR/scripts/watch.py`.
- 필요 바이너리: `ffmpeg`, `ffprobe` (로컬 파일), URL 분석 시 `yt-dlp` 추가.
  - 샌드박스(Linux): ffmpeg 기본 설치됨. yt-dlp 없으면
    `pip install yt-dlp --break-system-packages`.
  - Windows/이 프로젝트: `tools/ffmpeg/bin/`에 휴대용 FFmpeg를 둔다.
    `scripts/frames.py`는 시스템 PATH에 없어도 이 경로를 자동으로 찾는다.
- Whisper API 키(GROQ_API_KEY/OPENAI_API_KEY)는 선택. 이 프로젝트는 대부분
  srt가 이미 있거나 URL 자막으로 충분하므로 기본은 `--no-whisper`.

## 사용법

```bash
# 로컬 녹화본 — 특정 구간 집중 (srt 있으면 --no-whisper)
python3 "${SKILL_DIR}/scripts/watch.py" "영상.mkv" --no-whisper --start 21:00 --end 22:00

# YouTube 벤치마킹 — 훅 분석 (첫 15초 집중)
python3 "${SKILL_DIR}/scripts/watch.py" "https://youtu.be/..." --start 0 --end 15

# 전사만 (프레임 없이 빠르게 내용 파악)
python3 "${SKILL_DIR}/scripts/watch.py" "https://youtu.be/..." --detail transcript
```

주요 옵션:

- `--detail transcript|efficient|balanced|token-burner` — 정밀도 (기본 balanced, 프레임 100장 상한)
- `--start T` / `--end T` — 구간 집중 (`SS`, `MM:SS`, `HH:MM:SS`). 구간 지정 시 프레임 밀도 자동 증가
- `--timestamps T1,T2,…` — 지정 시각의 프레임 강제 추출 (전사에서 "여기 보세요" 같은 순간)
- `--max-frames N` — 프레임 상한 축소 (토큰 절약)
- `--resolution W` — 프레임 폭 px (기본 512; 화면 글자를 읽어야 하면 1024)
- `--out-dir DIR` — 산출물 폴더 지정. **중요**: Claude가 프레임을 Read로 보려면
  접근 가능한 위치여야 한다. 이 프로젝트에서는 `temp/video-watch/<영상명>/`을
  사용한다 (`temp/`는 git 이그노어 대상이라 커밋 안 됨). 샌드박스 기본 임시
  폴더(/tmp)는 Read가 접근 못 하므로 쓰지 않는다.
- `--no-whisper` — Whisper 비활성 (이 프로젝트 기본 권장)

## 실행 후 절차

1. 스크립트가 출력한 프레임 경로 전부를 **한 메시지에서 병렬 Read**한다
   (`t=MM:SS` 표시로 시간 정렬).
2. 전사(또는 기존 srt)와 프레임을 결합해 타임스탬프를 인용하며 답한다.
3. 작업 폴더는 후속 질문이 없으면 삭제, 있으면 유지. `--out-dir`로
   프로젝트 안에 만들었면 `00_공통_작업원칙.md`의 삭제 규칙을 따른다.

## 한계와 주의

- 10분 이하 영상에서 정확도가 가장 좋다. 긴 영상은 전체 훑기보다
  `--start/--end` 집중 실행이 낫다 (프레임 상한 2fps/모드별 상한).
- 토큰 비용은 프레임 수가 지배한다. 80프레임(512px) ≈ 이미지 토큰 5~8만.
  같은 세션에서 이미 본 영상은 재실행하지 말고 컨텍스트로 답한다.
- 비공개/로그인 필요 영상은 불가. 공개 URL과 로컬 파일만.
- **Cowork 샌드박스에서는 URL 다운로드 불가** (네트워크 허용 목록에 YouTube 없음,
  프록시 403 확인: 2026-07-02). URL 분석은 (a) 영상을 직접 받아 `inputs/`에 넣거나
  (b) Claude Code 등 로컬 터미널 환경에서 실행한다. 로컬 파일 분석은 샌드박스에서 정상 동작.
- **원본 보호**: 이 스킬은 원본 영상을 읽기만 한다. 산출물(프레임, 전사)은
  항상 새 폴더에 생성한다.
- 긴 MKV에서 후반부 탐색이 실패하면 파일 메타데이터가 아니라 실제 패킷 끝 시간을
  확인한다. `tools/README.md`의 FFmpeg 검증 메모를 참고한다.
