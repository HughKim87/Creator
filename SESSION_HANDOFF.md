# SESSION_HANDOFF.md — 김실버유튜브

최종 갱신: 2026-07-03 (Claude Cowork 세션)

규칙 원본:
- Tier-1: `C:\Users\Hugh\Claude\Projects\Building WorkFlow\PROJECT_RULES.md`
- Tier-2: 이 폴더의 `PROJECT_RULES.md` / 공통 원칙 `00_공통_작업원칙.md` / 흐름 `01_유튜브_제작_워크플로우.md`

## 현재 상태 요약

크레이지아케이드 편집 준비 패키지가 **실사용 단계**에 도달했다.
사용자가 Premiere Pro **CS6 (6.0.0)** 에서 XML 가져오기까지 검증했고,
현재 편집 기준 산출물은 아래 3개다:

- 러프컷 XML: `workspace/outputs/크레이지아케이드_영상/크아_컷편집_러프/premiere_export/CRA_PLAY_EDIT_ASSIST_V7_원본시퀀스.xml`
  (00_원본 + 02_시퀀스만, 30컷 약 55분, 후보클립 빈 없음)
- 기준 컷리스트: `workspace/outputs/크레이지아케이드_영상/크아_컷편집_러프/프리미어_자료/CRA_PLAY_CUTLIST_V5_시간순확장.csv`
- 대본: `premiere_export/러프컷_v7_대본.txt` (타임라인 위치+원본 TC 병기)

## 이번 세션 주요 완료 내용

1. **원본 3개 전부 mkv→mp4 무손실 remux** (CS6가 mkv 미지원 → 미디어 오프라인 원인)
   - `workspace/inputs/crazy_arcade/`: `2026-06-26_19-42-34_remux.mp4`(6.7GB),
     `2026-06-26_22-08-36_remux.mp4`, `2026-06-27_00-27-47_remux.mp4`
   - 전부 H.264+AAC 스테레오 확인, 길이 일치 검증 완료. 변환용 배치: `tools/run_remux_mkv_to_mp4.bat`, `tools/run_remux_extra.bat`
2. **XML 생성 스크립트 대폭 개선** (`skills/premiere-editing-export/scripts/make_premiere_xml.py`)
   - 사용자 Premiere가 내보낸 참조 XML(`workspace/inputs/crazy_arcade/crazyarcade.xml`) 구조를 그대로 복제:
     xmeml **version 4**, 마스터클립에 `uuid + 자기참조 masterclipid + ismasterclip TRUE`, 클립아이템 rate 없음,
     트랙 `enabled/locked` 위치, `outputchannelindex` 위치, 오디오 모노2트랙 분해+`premiereTrackType="Stereo"`.
   - **다중 원본 지원**: 소스 인자로 폴더 전달 + 컷리스트 `원본파일` 컬럼 → file-N/masterclip-N 자동 생성.
   - 옵션: `--no-master-bin`, `--no-candidates`(후보클립 빈 생략, V7에 사용), `--audio-layout exploded|single`.
3. **CS6 스테레오 제약 결론 확정** (여러 차례 실험)
   - CS6의 FCP7 XML 가져오기는 시퀀스 오디오를 **무조건 L/R 링크 모노 2트랙**으로 만든다.
   - 결정적 증거: CS6가 자기가 내보낸 XML을 재가져오기해도 갈라짐. 단일 클립 방식(V5/V7 single)은 L채널만 나옴.
   - 사용자 결정: **L/R 2트랙 감수하고 진행** (링크되어 있어 편집은 문제없음, 볼륨만 2회 조정).
4. **자막 3파일 전체 재분석 → 컷리스트 확장** (13컷 → 30컷 시간순)
   - 분석 문서: `analysis_new/11_3파일_통합_흐름설계_v1.md`, `analysis_new/12_자막전체_재분석_및_누락후보_v1.md`
   - 사용자 요청으로 훅 배치 제거, 전체 녹화 시간순. 신규 10컷(여친 예고/설치 개그, 비행기 뱃지, 2000판 유저 등)+경계조정 5건.
   - 음량 분석: 메인 -27~-29dB 기준, 22-08 파일 -32dB(**+5dB 게인 보정 필요**), 1승1패 컷 -23dB(낮추기).
5. 산출물 정리: 컷리스트 V2~V5, XML V3~V7 등 이전 버전 파일들이 `premiere_export/`에 남아 있음(모두 보존).

## 사용자 확정 선호 (중요)

- 사용방법 md는 **더 이상 생성하지 않는다** (`--guide` 제거됨).
- 후보클립 빈 불필요 → `--no-candidates`가 사실상 기본.
- 컷 배치는 시간순. 컷 선정은 자막 내용 기반 + **화면 검증 필수** 인식 공유됨.

## 다음 작업 우선순위

1. **V7 XML의 Premiere 최종 확인** — 미디어 연결·재생 확인되면 App-validated 기록.
   (V6 시간순확장 21컷 버전까지는 가져오기 성공 이력 있음. V7은 구조만 축소라 위험 낮음)
2. **신규 컷 화면 검증** — 자막 기반 신규 10컷의 경계(판 시작/종료 순간)를 프레임 추출로 확인.
   특히 컷6-7 경계(메인 16:25), '아!' 연발 구간(메인 17:10~17:39)의 화면 내용.
   방법: `gameplay-video-analysis` 스킬의 라운드맵 방식 (analysis_new/10 참고).
3. 편집 진행 지원 — 자막(SRT) 파일은 remux mp4와 파일명이 달라 Premiere 자동 인식 안 됨. 필요시 이름 맞춘 사본 생성.
4. (보류) 12번 문서의 '선택' 등급 후보들 — 사용자가 원할 때만 추가.

## 환경 주의사항 (다음 세션 필수 숙지)

- **Windows→샌드박스 파일 동기화 버그**: 이 세션에서 Write/Edit 도구로 수정한 파일이
  샌드박스 마운트에서 널바이트 섞인 손상 상태로 보이는 현상 발생 (`make_premiere_xml.py`).
  Windows 쪽 원본은 정상. 우회: 샌드박스에서 실행할 파일은 **bash heredoc으로 샌드박스에 직접 재구성**.
  이 세션의 실행 사본은 scratchpad(`outputs/make_premiere_xml_v7.py`)에 있었으나 **세션 종료 시 사라짐** —
  다음 세션에서 스크립트 실행이 필요하면 Windows 원본(정상)을 기준으로 삼을 것.
- 샌드박스 bash는 호출당 45초 제한 + 호출 간 프로세스 유지 안 됨. 대용량 ffmpeg 작업은
  ① 사용자 PC에서 .bat 실행(더블클릭, PowerShell 정책 회피) ② /tmp에 변환 후 dd 분할 복사(4M×62개 단위).
- 사용자 PowerShell은 스크립트 실행 정책으로 .ps1 차단됨 → 항상 .bat로 제공.
- XML 생성 후 pathurl의 샌드박스 경로를 Windows 경로로 sed 치환 필요:
  `s|file://localhost//sessions/<세션>/mnt/|file://localhost/C:/Users/Hugh/Claude/Projects/Building%20WorkFlow/Workspace/|`
- `write_xml`은 기존 파일 덮어쓰기 거부(의도된 동작) — 새 버전 이름으로 생성할 것.

## 현재 Git/파일 상태

커밋 안 함. 이번 세션 신규 파일(전부 untracked 또는 workspace/ 제외 대상):
- 수정: `skills/premiere-editing-export/scripts/make_premiere_xml.py` (v7, 다중소스+CS6 구조)
- 신규: `tools/remux_mkv_to_mp4.bat` (공용 드래그&드롭 remux 도구. 일회성 bat 2개와 미사용 ps1은 temp/backups/2026-07-03/구버전_정리/로 이동)
- 신규: `프리미어_자료/CRA_PLAY_CUTLIST_V2_통합.csv`, `V3_시간순.csv`, `V4_시간순.csv`, `V5_시간순확장.csv`
- 신규: `reports/research/2026-07-02_mkv_to_mp4_변환_워크플로우.md`, `2026-07-02_premiere_xml_오디오출력_후보클립구조_리서치.md`
- workspace/outputs(git 제외): 현재 유효본 = XML V6 시간순확장(후보클립 포함판)·V7 원본시퀀스, 러프컷_v7_대본.txt,
  러프컷_시간순확장_v6_자막.txt, analysis_new/11·12 문서. 사용자 사본 `CRA_PLAY_EDIT_ASSIST_V7_대본.txt`도 있음(내용 상이, 건드리지 말 것).
- 2026-07-03 폴더 병합: 프로젝트 루트의 `크레이지아케이드_영상/` 전체(analysis_new 01~09, 프리미어_자료의
  컷리스트·EDL, 치트시트, subtitle_recovery_work)를 `workspace/outputs/크레이지아케이드_영상/`으로 이동 통합.
  이제 크아 콘텐츠 관련 파일은 workspace/ 아래 한 곳에만 있다. 주의: workspace/는 .gitignore 대상이라
  기준 컷리스트가 git 추적에서 빠짐 — 필요시 백업은 temp/backups/ 활용.
- 2026-07-03 정리: 실패/구버전 산출물(3P_TEST 시리즈 전부, mkv기반 V1, 러프컷 V2~V5, 자막 v4·v5, run_remux_mkv_to_mp4.ps1)을
  `temp/backups/2026-07-03/구버전_정리/`로 이동. PROJECT_RULES.md에 '.bat 제공' 규칙 추가(백업 후).
- 백업: `temp/backups/2026-07-02/`(스크립트 v1, 컷리스트 원본, 불완전 remux 파일), `temp/backups/2026-07-03/`(이 핸드오프 직전본)

## 다음 세션 시작 프롬프트

```text
Tier-1/Tier-2 PROJECT_RULES.md를 읽고 SESSION_HANDOFF.md 기준으로 이어서 진행해.
현재 편집 기준은 CRA_PLAY_EDIT_ASSIST_V7_원본시퀀스.xml(30컷 시간순, CS6 검증 구조)이다.
우선 V7의 Premiere 가져오기 결과를 확인해 App-validated 여부를 기록하고,
다음으로 자막 기반 신규 컷 10개의 경계를 화면(프레임 추출)으로 검증해 컷리스트를 다듬어라.
CS6는 XML 오디오를 L/R 2트랙으로 가져오는 것이 정상이며 해결 불가 — 다시 시도하지 말 것.
```
