# Creator 영상 제작 Host

이 저장소는 리서치부터 영상 생성·자막·제목·썸네일·수동 업로드 패키지까지의 영상 작업을 여러 Agent가 같은 규칙과 상태로 이어서 수행하기 위한 프로젝트다.

`core/`는 공통 Agent 정책과 공개 계약을 제공하는 읽기 전용 submodule이다. 실제 영상·YouTube·게임 도메인 기능과 작업 절차는 이 저장소의 `extension/`과 `.agents/skills/`가 소유한다.

## 주요 workflow

### 영상 제작

`리서치 → 영상 생성 → SRT → 제목·썸네일 → 수동 업로드 패키지`

- NotebookLM 출처 조사와 동영상 개요 생성
- 로컬 Whisper 기반 자막 추출·보정
- 영상·SRT·리서치 근거 기반 제목과 썸네일 제작
- 사용자가 직접 업로드할 최종 네 파일 정리

### 촬영 후 영상 편집

`원본 분석 → 방향 선택 → 컷 설계 → 의미 검수 → timeline → Premiere XML`

- 발화·화면·동작·전환 경계 검수
- 편집 결정과 source lineage 보존
- timeline과 XML 구조 검증

### 게임 콘텐츠 조사

- 한국 게임 출시·업데이트 조사
- 실제 YouTube 조회수 기반 소재 브리핑
- 승인된 경우에만 외부 일정이나 후속 작업 연결

## 저장소 구조

| 경로 | 책임 |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Agent별 공통 진입점 |
| `PROJECT_RULES.md` | Host 소비 계약·보호 경계·도메인 route |
| `SESSION_HANDOFF.md` | 현재 단계·차단·첫 다음 행동 |
| `core/` | 읽기 전용 Agent Core submodule |
| `extension/` | 영상·YouTube·게임 도메인 구현과 계약 |
| `.agents/skills/` | 브라우저·NotebookLM·자막·썸네일·업로드 준비 절차 |
| `scripts/` | Creator Runtime preflight와 관련 검증 |

## 시작

```powershell
git submodule update --init --recursive
python -B scripts/bootstrap.py --json
python -B scripts/verify.py
```

Codex 계열 Agent는 `AGENTS.md`, Claude는 `CLAUDE.md`에서 시작한다. 두 진입점 모두 Core 정책, Creator 정책, 현재 상태 순서로 합류한다.

## 데이터 경계

`inputs`, `outputs`, `extension/inputs`, `extension/outputs`는 사용자 원본과 결과를 위한 보호 경로다. 사용자가 정확한 항목과 목적을 지정하기 전에는 열거·읽기·검색·Git 처리하지 않는다.

실제 업로드·게시·캘린더 등록처럼 외부 상태를 바꾸는 행동은 로컬 자료 준비와 분리하며 별도 승인을 받은 경우에만 실행한다.

Obsidian은 프로젝트 루트를 검토하되 로컬 UI와 보호 경로를 색인하지 않는다. 공유 정본은 다음 안전 설정 하나다.

<!-- project-artifact:v1 path=.obsidian/app.json verify=json-semantic -->
```json
{"defaultViewMode":"preview","showUnsupportedFiles":false,"userIgnoreFilters":[".git/",".obsidian/","backup/","inputs/","outputs/"]}
```
<!-- /project-artifact -->
