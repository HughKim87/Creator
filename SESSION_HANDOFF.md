# SESSION_HANDOFF.md — 김실버유튜브

최종 갱신: 2026-07-04 (Claude Cowork 세션 — 진행 중 영상 없음, 도구·문서 제네릭 정리 완료)

규칙 원본:
- Tier-1: `C:\Users\Hugh\Claude\Projects\Building WorkFlow\PROJECT_RULES.md`
- Tier-2: 이 폴더의 `PROJECT_RULES.md` / 공통 원칙 `00_공통_작업원칙.md` / 흐름 `01_유튜브_제작_워크플로우.md`

## 현재 상태

- **진행 중인 영상 편집 없음. 다음 영상 대기.**
- `temp/`, `workspace/`는 비어 있음(이전 프로젝트 데이터 정리 완료). 다음 영상 원본을 `workspace/inputs/`에 넣고 시작.
- 스킬·워크플로우·도구는 특정 영상에 종속되지 않는 범용 상태로 정리됨.

## 다음 영상 시작하는 법

워크플로우(`01_유튜브_제작_워크플로우.md`)대로:
- 새 소재부터면 1단계(소재 조사) → 2 기획 → 3 대본 → 4 자막 → 5 영상분석 → 6 편집자료 → 7 검수.
- 이미 촬영된 플레이 영상 편집이면 5단계(영상 분석)부터 진입 → 6단계(편집 자료 생성).

## 편집 환경 전제 (사용자 Premiere CS6 — 영상 무관, 항상 적용)

- **mkv 원본은 편집 전에 mp4로 무손실 remux.** CS6가 mkv 미지원 → 미디어 오프라인. `tools/remux_mkv_to_mp4.bat` 사용.
- **CS6는 XML 오디오를 L/R 링크 모노 2트랙으로 가져옴(정상·해결 불가).** 볼륨만 2회 조정, 재시도 금지.
- **컷리스트가 기준 입력.** 화면(프레임) 검증으로 컷 경계를 먼저 다듬은 뒤 XML/EDL/러프컷을 생성한다(생성 전 검증). 이 전제들은 `skills/premiere-editing-export/SKILL.md`에도 있음.

## 편집 작업 시 반복 체크 (지난 제작 회고에서 정리)

1. 컷리스트 확정 전에 화면 검증부터. 자막으로 후보만 넓히고 바로 XML 만들지 않는다.
2. 설명 브리지 컷(대기방·설정창처럼 화면 변화 약한 구간)은 짧게. 컷리스트에 '짧은 브리지'로 표시.
3. 플레이 컷은 시작-결과-반응을 함께 확인. 결과 후 로비가 길면 압축.
4. 컷리스트 헤더 컷 수와 실제 행 수를 검산. XML 생성 전 행 수·총 길이 확인.
5. XML 생성은 최종 기준 컷리스트 확정 후에만. 이미 Premiere 작업 중이면 새 XML보다 수정 지시서 우선.

## 환경 주의사항 (샌드박스/도구)

- **Windows→샌드박스 파일 동기화 버그**: Write/Edit로 수정한 파일이 샌드박스 마운트에서 널바이트 섞인 손상 상태로 보일 수 있다(Windows 원본은 정상). 샌드박스에서 실행할 스크립트는 heredoc으로 재구성하거나 Windows 원본 기준.
- 샌드박스 bash는 호출당 45초 제한 + 호출 간 프로세스 유지 안 됨. 대용량 ffmpeg는 사용자 PC `.bat` 실행 또는 /tmp 변환 후 분할 복사.
- 사용자 PowerShell은 `.ps1` 차단 → 항상 `.bat`로 제공.
- XML 생성 후 pathurl의 샌드박스 경로를 Windows 경로로 sed 치환 필요:
  `s|file://localhost//sessions/<세션>/mnt/|file://localhost/C:/Users/Hugh/Claude/Projects/Building%20WorkFlow/Workspace/|`
- `make_premiere_xml.py`의 XML 쓰기는 기존 파일 덮어쓰기 거부 — 새 이름으로 생성.

## Git/파일 상태

- `temp/`, `workspace/` 비어 있음. `skills/`, `tools/`(remux 배치·ffmpeg), 규칙·워크플로우 문서 유지.
- `workspace/`는 의도적 git 미추적(대용량 미디어 이그노어).

## 다음 세션 시작 프롬프트

```text
Tier-1/Tier-2 PROJECT_RULES.md를 읽고 이 SESSION_HANDOFF.md 기준으로 진행해.
진행 중 영상 없음 — 다음 영상 대기 상태. 도구·문서는 범용으로 정리돼 있다.
다음 영상이 정해지면 워크플로우대로(새 소재는 1단계, 촬영본 편집은 5→6단계) 진행.
CS6 전제(mkv→mp4 remux, XML 오디오 L/R 2트랙 정상)와 '생성 전 화면 검증' 원칙 적용.
```
