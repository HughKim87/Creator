---
name: video-watch
description: |
  Claude가 영상을 직접 "보고" 분석하게 하는 스킬. ffmpeg로 프레임을 추출하고 자막/전사와 함께 읽어
  영상 내용을 파악한다. 로컬 녹화본(mkv 등)과 YouTube 등 URL 모두 지원.
  "이 영상 봐줘", "영상에서 무슨 일이 일어나는지 확인해줘", "이 유튜버 영상 훅 분석해줘",
  "몇 분 몇 초에 뭐가 나오는지 봐줘", "전에 뽑은 프레임 재사용해줘" 같은 요청에서 사용한다.
license: MIT (원본: bradautomates/claude-video v0.2.0)
---

# video-watch — 영상 시청/분석

Claude는 영상 입력이 없다. 이 스킬은 `scripts/watch.py`로 프레임(JPEG)과
타임스탬프 전사를 만들어, Claude가 프레임을 `Read`로 보고 전사와 결합해
영상 내용에 근거한 답을 하게 한다.

원본: https://github.com/bradautomates/claude-video (MIT). 이 폴더의 사본은
영상 제작 프로젝트용으로 관리한다.

## 이 프로젝트에서의 두 가지 용도

1. **내 녹화본 분석** (로컬 mkv): 하이라이트/컷포인트 탐색.
   - 원본 mkv 옆에 이미 `.srt` 자막이 있으면 **Whisper를 쓰지 말고**
     `--no-whisper`로 프레임만 뽑고, srt를 직접 Read해서 전사로 사용한다.
     (기존 Whisper 복구 자막이 더 정확하고, API 비용이 없다)
   - 프로젝트 원본의 화면 검증은 `tools/source_frame_assets.py`로 원본 시간 자산을
     조회·추출한다. `watch.py`는 자동 장면 탐색이 추가로 필요할 때만 보조로 쓴다.
2. **타 채널 벤치마킹** (YouTube URL): 잘되는 게임 영상의 훅(첫 3~10초),
   구성, 화면 연출 분석. yt-dlp가 자막을 무료로 가져온다.

## 입력

- 로컬 영상 파일 또는 공개 URL
- 프로젝트 원본이면 기존 자산 목록의 안정된 `source_id`
- 분석할 구간의 시작/끝 시간 또는 확인할 타임스탬프
- 기존 SRT/VTT가 있으면 원본 자막 경로
- 6단계에서 호출되는 경우 `gameplay-video-analysis`의 후보 구간 ID

## 출력

- 시간표시가 있는 프레임 이미지 묶음
- 사용 가능한 전사 또는 기존 자막 참조
- 화면에서 확인한 사실과 불확실한 부분
- 후속 단계에서 인용할 수 있는 타임스탬프

## 사용 게이트

- 전체 영상을 무작정 추출하지 않는다. 먼저 확인할 구간이나 타임스탬프를 정한다.
- 6단계 작업에서는 `gameplay-video-analysis`의 후보 구간을 기준으로 호출한다.
- 프로젝트 원본은 공용 자산 목록을 먼저 조회하고 편집본 시각을 원본 시각으로 변환한다.
- `--out-dir`은 필수이며 프로젝트 `temp/`나 시스템 임시 폴더를 사용하지 않는다.
- 출력 경로는 영상 ID·원본 구간·추출 프로필로 고정한다. 날짜나 실행 번호로 새 폴더를 만들지 않는다.
- 같은 출력 폴더가 있으면 스크립트를 다시 실행하지 않고 기존 프레임과 전사를 읽는다.
- 기존 SRT가 있으면 기본적으로 `--no-whisper`를 사용한다.
- 프레임 추출 결과만으로 영상의 메시지, 대표 후보, 편집 판단을 확정하지 않는다.

## 중단 조건

- 원본 영상이나 URL에 접근할 수 없는 경우
- 구간 시간이 원본 길이를 벗어나거나 실제 패킷 끝 시간과 맞지 않는 경우
- 로그인, 비공개, 네트워크 제한 때문에 URL 영상을 받을 수 없는 경우
- 추출한 프레임만으로 화면 의미를 판단하기 어렵고 자막·오디오 근거가 없는 경우

## 다음 단계 전달물

- 확인한 구간 ID
- `source_id`, 원본 시작/끝 시각, 프레임 폴더 경로와 `asset_ids`
- 확인한 화면 사실
- 확인 불가 또는 추가 확인 필요 지점
- 6단계 후보지도에 반영할 타임스탬프

## AI가 확정하지 말 것

- 프레임 몇 장만 보고 대표 후보를 확정하지 않는다.
- 자막·오디오 근거 없이 화면 의미를 단정하지 않는다.
- 사용자의 승인 없이 컷리스트, XML, 러프컷 생성을 다음 작업으로 넘기지 않는다.

## 좋은 요청 예시

```text
6단계 후보 B03의 12:10~13:00 구간만 video-watch로 확인해줘.
화면에 실제 전투/대화/메뉴 중 무엇이 나오는지 타임스탬프별로 정리하고,
대표 후보 확정은 하지 말고 확인 필요 지점을 따로 표시해줘.
```

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
# 로컬 원본 — 공용 원본 시간 자산 조회·추출
python tools/source_frame_assets.py "영상.mkv" --source-id <existing_source_id> --start 21:00 --end 22:00 --count 12 --asset-root outputs/06_analysis/source_assets/<existing_source_id> --manifest outputs/06_analysis/source_asset_manifest.csv

# YouTube 벤치마킹 — 훅 분석 (첫 15초 집중)
python3 "${SKILL_DIR}/scripts/watch.py" "https://youtu.be/..." --start 0 --end 15 --out-dir outputs/06_analysis/external_reviews/video_id/range_000000_000015_balanced

# 전사만 (프레임 없이 빠르게 내용 파악)
python3 "${SKILL_DIR}/scripts/watch.py" "https://youtu.be/..." --detail transcript --out-dir outputs/06_analysis/external_reviews/video_id/transcript
```

주요 옵션:

- `--detail transcript|efficient|balanced|token-burner` — 정밀도 (기본 balanced, 프레임 100장 상한)
- `--start T` / `--end T` — 구간 집중 (`SS`, `MM:SS`, `HH:MM:SS`). 구간 지정 시 프레임 밀도 자동 증가
- `--timestamps T1,T2,…` — 지정 시각의 프레임 강제 추출 (전사에서 "여기 보세요" 같은 순간)
- `--max-frames N` — 프레임 상한 축소 (토큰 절약)
- `--resolution W` — 프레임 폭 px (기본 512; 화면 글자를 읽어야 하면 1024)
- `--out-dir DIR` — 필수. 접근 가능한 `outputs/06_analysis/` 하위의 명시적 위치를 사용한다.
  기존 폴더가 있으면 도구를 실행하지 말고 그 안의 프레임·전사를 재사용한다.
- `--no-whisper` — Whisper 비활성 (이 프로젝트 기본 권장)

## 실행 후 절차

1. 스크립트가 출력한 프레임 경로 전부를 **한 메시지에서 병렬 Read**한다
   (`t=MM:SS` 표시로 시간 정렬).
2. 전사(또는 기존 srt)와 프레임을 결합해 타임스탬프를 인용하며 답한다.
3. 프로젝트 원본에서 재사용할 근거는 `source_frame_assets.py`의 공용 자산 목록에 등록한다.
   자동 장면 탐색으로 만든 프레임 묶음도 `register_source_assets.py`로 원본 범위와 함께 등록한다.

## 한계와 주의

- 10분 이하 영상에서 정확도가 가장 좋다. 긴 영상은 전체 훑기보다
  `--start/--end` 집중 실행이 낫다 (프레임 상한 2fps/모드별 상한).
- 토큰 비용은 프레임 수가 지배한다. 80프레임(512px) ≈ 이미지 토큰 5~8만.
  세션과 무관하게 공용 자산 목록에 있는 프레임은 다시 추출하지 않는다.
- 비공개/로그인 필요 영상은 불가. 공개 URL과 로컬 파일만.
- **Cowork 샌드박스에서는 URL 다운로드 불가** (네트워크 허용 목록에 YouTube 없음,
  프록시 403 확인: 2026-07-02). URL 분석은 (a) 영상을 직접 받아 `inputs/`에 넣거나
  (b) Claude Code 등 로컬 터미널 환경에서 실행한다. 로컬 파일 분석은 샌드박스에서 정상 동작.
- **원본 보호**: 이 스킬은 원본 영상을 읽기만 한다. 기존 산출물을 삭제하거나 덮어쓰지 않는다.
- 긴 MKV에서 후반부 탐색이 실패하면 파일 메타데이터가 아니라 실제 패킷 끝 시간을
  확인한다. `tools/README.md`의 FFmpeg 검증 메모를 참고한다.
