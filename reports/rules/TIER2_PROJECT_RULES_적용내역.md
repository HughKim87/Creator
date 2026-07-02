# Tier-2 PROJECT_RULES.md 적용 내역

- 작성일: 2026-07-02
- 대상: `PROJECT_RULES.md`
- 상태: 적용 완료, 2026-07-02에 Tier-1 중복 내용 제거

## 적용한 섹션

1. `이 프로젝트의 작업 환경 적용`
2. `영상 편집 자동화 검증 적용`
3. `컷리스트 기준 관리`

## 적용 이유

이번 유튜브 프로젝트는 Windows, PowerShell, 한글 경로, 한글 문서, 대용량 영상, SRT/CSV, Premiere 산출물을 함께 다룬다.
이 조합에서는 기본 인코딩, 기본 Python 명령, Git 기본 경로 표시를 믿으면 같은 문제가 반복된다.

## Tier-2에 둔 이유

- UTF-8, PowerShell, Python 경로 고정 같은 일반 운영 규칙은 Tier-1로 올라갔으므로 이 문서에서는 반복하지 않는다.
- Premiere XML/EDL/러프컷 검증 단계는 유튜브 영상 편집 프로젝트의 도메인 규칙이다.
- 화면 검증 결과와 컷리스트 생성 기준을 일치시키는 규칙은 영상 편집 품질에 직접 연결된다.

## 현재 남긴 Tier-2 보강 내용

- 영상 분석, 프레임 추출, 러프컷 생성에는 프로젝트 내부 `tools/ffmpeg/bin/` FFmpeg를 우선 사용.
- Premiere 산출물의 `App-validated`는 Premiere Pro에서 가져오기, 미디어 연결, 오디오, 시퀀스 재생까지 확인된 상태로 해석.
- Premiere에서 직접 열어보지 않았으면 "Premiere 사용 가능 확정"이라고 쓰지 않음.
- 최신 화면 검증 결과가 있으면 기준 컷리스트를 먼저 갱신한 뒤 XML/EDL/러프컷 생성.
- `한 판 시작-결과-반응`처럼 보존 규칙이 있는 구간은 컷리스트에 판단 근거를 남김.

## 남은 작업

- Tier-1 `Building WorkFlow/PROJECT_RULES.md`는 사용자가 수동 반영했다.
