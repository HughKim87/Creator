# 프로젝트 내부 도구

이 폴더는 입력 자료와 무관하게 여러 영상에 재사용하는 로컬 도구만 둔다.
특정 영상 전용 코드는 관련 `outputs/<stage>/support/`에 둔다.

## 현재 상태

프로젝트 임시 폴더는 사용하지 않는다. 재사용할 프레임은 원본 시간 기반 공용 자산으로 관리한다.

| 도구 | 상태 |
|---|---|
| `tools/ffmpeg/bin/ffmpeg.exe` | 존재 |
| `tools/ffmpeg/bin/ffprobe.exe` | 존재 |
| `tools/ffmpeg/bin/ffplay.exe` | 존재 |
| `tools/remux_mkv_to_mp4.bat` | 존재 |
| `tools/source_frame_assets.py` | 존재 |
| `tools/register_source_assets.py` | 존재 |
| `tools/projectctl.py`, `tools/projectctl.bat` | 존재 |
| `tools/projectctl.schema.json` | 존재 |
| `tools/workflow_gate.py` | 존재 |
| `tools/edit_memory.py` | 존재 |
| `tools/project_preflight.py`, `tools/project_preflight.bat` | 존재 |
| `tools/run_python.bat` | 존재 |
| `tools/git_project.bat` | 존재 |
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
- 저장소 Python 명령은 실행 파일을 추측하지 말고 `tools\run_python.bat`으로 실행한다.
- `tools/projectctl.bat`와 `tools/run_doccheck.bat`도 같은 `run_python.bat` 실행기를 사용한다.

```bat
tools\run_python.bat -m unittest discover -s tests -p "test_*.py"
tools\run_python.bat tools\workflow_gate.py audit
```

`run_python.bat`은 앱 제공 Python을 먼저 확인하고, 일반 `python`과 `py -3`은 실제
최소 실행이 성공할 때만 사용한다. `where` 결과만 보고 실행 가능하다고 간주하지 않는다.

## 프로젝트 사전점검

넓은 파일 조회, Python 실행, Git 상태 확인 전에 아래 명령을 한 번 실행한다.

```bat
tools\project_preflight.bat
```

- 필수 제어 파일 존재 여부를 확인한다.
- 실제로 존재하는 검색 루트만 반환한다. 존재를 확인하지 않은 선택 경로를 `rg`나 재귀 조회에 넘기지 않는다.
- `run_python.bat`으로 Python 실행 경로를 검증한다.
- `git_project.bat`으로 저장소의 `safe.directory`를 적용한 Git 호출을 검증한다.
- `projectctl context`를 포함하므로 별도 상태 조회가 필요 없다.

저장소 Git 명령은 샌드박스 소유권 차이 때문에 직접 `git`을 호출하지 않고 아래 래퍼를 사용한다.

```bat
tools\git_project.bat status --short
tools\git_project.bat diff --check
```

### Python 파일 생명주기

- 새 `.py`가 필요하면 먼저 기존 모듈의 책임과 입력 계약을 확인한다.
- 여러 영상에 같은 계약으로 재사용할 코드는 `tools/` 또는 담당 스킬에 두고 문서화한다.
- 입력 자료나 특정 편집본에 의존하는 코드는 관련 `outputs/<stage>/support/`에 두며 테스트도 함께 둔다.
- 작업 전용 코드는 첫 20줄 안에 `Lifecycle: task-scoped`와 `Cleanup:` 조건을 기록한다.
- 사용 후에는 `keep`·`merge`·`promote`·`cleanup` 판단을 보고한다. 공용 승격은 입력별 상수를 제거하고 교차 영상 계약을 검증한 뒤에만 한다.
- doccheck는 신규 Python의 위치, 공용 도구 등록, 작업 전용 수명 표시를 검사한다.

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
- AI 에이전트 표준 진입점과 포인터 파일 구조
- `inputs/`·`outputs/`·공용 프레임워크의 폴더 소유권 위반
- 오래된 상태 문구와 동적 커밋 상태 고정
- 과거 세션 절대경로와 과거 원본 파일명
- 프로젝트 `temp/`, 스킬의 임시 출력 경로, 중복 백업 파일
- 단계 스킬의 `source_id`·자산 목록·현재본 포인터 누락
- 원본 자산 목록이나 `CURRENT.json`에 등록되지 않은 출력 미디어
- 신규 Python 도구의 문서 등록 누락과 설명 없는 작업 한정 스크립트
- 기본 로드 문서 과대화 경고
- `skills/*/SKILL.md`의 입력, 출력, 게이트, 중단 조건, AI 확정 금지, 요청 예시

문서나 스킬을 수정한 뒤 최종 답변 전에 실행한다.

## projectctl (에이전트 공통 제어)

Claude·Codex·Gemini가 같은 작업 상태와 종료 검사를 사용하게 하는 공용 명령이다.
영상별 사실은 복제하지 않고 `outputs/SESSION_HANDOFF.md`를 계속 단일 정본으로
사용한다. `outputs/AGENT_CONTROL.json`에는 활성 작업, 담당 에이전트, 마지막으로
검증 완료된 작업의 짧은 영수증만 기록한다. 형식은 `tools/projectctl.schema.json`이다.

```bat
tools\projectctl.bat context
tools\projectctl.bat start --task <ascii-slug> --title "<작업명>" --agent <codex|claude|gemini>
tools\projectctl.bat verify
tools\projectctl.bat finish --task <ascii-slug> --summary "<완료 요약>"
```

- `status`, `context`, `verify`는 상태 파일을 수정하지 않는다.
- `start`는 이미 다른 활성 작업이 있으면 실패해 세션 간 작업 충돌을 드러낸다.
- `finish`는 doccheck, workflow gate, 전체 단위 테스트, staged/unstaged
  `git diff --check`가 모두 통과한 경우에만 활성 작업을 완료 처리한다.
- 상태 파일이 손상됐거나 스키마 버전이 다르면 자동 초기화하지 않고 중단한다.
- 이 도구는 작업 조율 장치다. 콘텐츠 판단과 실제 진행 상태는 핸드오프에 기록한다.

## workflow gate

`workflow_gate.py`는 `docs/WORKFLOW_CONTRACT.json`을 읽어 단계 상태, 규칙 원장,
편집 변경 원장과 `CURRENT.json`의 승격 주장을 교차 검사한다. 닫힌 게이트는 정상
상태일 수 있지만, 모순된 승격은 오류다.

```powershell
<python> tools/workflow_gate.py audit
<python> tools/workflow_gate.py assert-transition --to planning
<python> tools/workflow_gate.py assert-transition --to edit_calibration
<python> tools/workflow_gate.py assert-transition --to edit_full
<python> tools/workflow_gate.py assert-transition --to validation
<python> tools/workflow_gate.py assert-transition --to final
```

- `audit`: 상태 정합성을 검사한다. 복구 상태에서 모든 전진 단계가 닫혀 있어도
  모순이 없으면 성공한다.
- `assert-transition`: 요청한 단계의 필수 증거와 활성 규칙이 모두 통과했을 때만
  성공한다.
- 모든 전환은 `phase_order`의 바로 이전 단계가 `approved_for_next_phase`여야 한다. 개별 transition에 이 조건이 빠져도 도구가 자동 차단한다.
- 계약 감사는 대표 샘플의 초반·중간·후반 범위, AI 범위별 선검증, 사용자에게 한 가지 권고안만 제시, MP4 현재 요청 허가, 영향 범위 롤백 정책도 검사한다.
- `validation_scopes`의 오디오 신호·편집 의미·연속 A/V·앱·사용자 방향을 따로 검사하며, `passed` 범위에는 존재하는 근거 파일이 필요하다.
- 브라우저 같은 한 도구 표면의 실패가 오디오 신호처럼 무관한 범위를 차단하면 감사 오류다.
- `task_blocked=true`는 필수 범위 식별, 기존 근거·프로젝트 도구·동등 방법 확인, 대안 없음이 모두 기록된 경우에만 허용된다.
- `current_deliverable`은 final 게이트가 닫혀 있으면 허용하지 않는다.
- `calibration_generation_allowed`는 AI 자체 검토 기획으로 제한된 대표 샘플만 허용한다.
- `generation_lock_released`는 사용자 승인 대표 샘플과 승인 기준본이 있어야만 전체 편집에 대해 해제할 수 있다.

## edit memory

`edit_memory.py`는 편집 판단을 규칙 문장 대신 이벤트, 수정 계보, 타임라인 노드·연결,
피드백, 평가 증거, 이중 기준본으로 저장한다. 데이터 계약은
`docs/EDIT_MEMORY_KERNEL.md`를 따른다. 영상별 데이터베이스와 생성 뷰는
`outputs/07_edit_export/edit_memory/`에 둔다.

```bat
tools\run_python.bat tools\edit_memory.py apply --db <database> --input <event-batch.json>
tools\run_python.bat tools\edit_memory.py validate --db <database>
tools\run_python.bat tools\edit_memory.py export --db <database> --output <CURRENT.json>
```

## 검증 상태

기존 검증 자산은 원본 시간 목록에 등록해 재사용한다. 새 원본 영상이 들어오면 아래 순서로 확인한다.

1. `ffmpeg.exe -version` 실행 확인
2. `ffprobe.exe`로 원본 길이 확인
3. `source_frame_assets.py`로 짧은 원본 구간 프레임 조회·추출
4. 필요 시 `synccheck`로 컷 경계 검증

## guard (결정적 가드레일)

`tools/guard/agent_guard.py`는 Claude Code hooks(`.claude/settings.json`)가
호출하는 차단 스크립트다. 규칙 원본은 `PROJECT_RULES.md`이고, 이 스크립트는
그중 "절대 금지" 항목만 기계적으로 강제한다.

- PreToolUse: git push, reset --hard, clean -f, 재귀 강제 삭제,
  `inputs/` 쓰기, 미디어/자막 삭제, `temp/`·`runs/`·중복 출력·백업 경로 쓰기, 비밀 파일 접근 차단.
- Stop: 문서(.md/.py/.bat) 변경이 있으면 doccheck를 실행하고, 실패 시
  종료를 막고 오류를 되돌려준다. `stop_hook_active`로 무한 루프를 방지한다.
- 실패 시 개방(fail-open): 입력 파싱 실패나 도구 부재 시 차단하지 않는다.
- Claude Code 전용. Codex, Gemini는 `tools/guard/`의 사용자 설정 템플릿
  (`codex_config.template.toml`, `gemini_settings.template.json`)을 1회 적용한다.

테스트: 샘플 훅 JSON을 stdin으로 넣어 exit 코드를 확인한다(차단=2, 허용=0).

### git pre-commit (전 에이전트 공통)

`.githooks/pre-commit`이 커밋 직전 doccheck를 강제한다. 어느 에이전트가
작업했든 동일하게 적용된다. 새 클론에서는 1회 설정이 필요하다:

```
git config core.hooksPath .githooks
```

`--no-verify` 우회는 규칙 위반이며 agent_guard가 차단한다. 줄바꿈 정책은
`.gitattributes`가 관리한다.

## 원본 시간 프레임 자산

`source_frame_assets.py`는 고정 원본의 절대 시간으로 프레임을 조회·추출한다. 동일한
`source_id`·원본 시각·해상도가 이미 등록돼 있으면 기존 파일을 반환하고 새 이미지를 만들지 않는다.

```powershell
python tools\source_frame_assets.py "원본.mp4" `
  --source-id <source_id> --start 00:10:00 --end 00:11:00 --count 12 `
  --width 1024 --asset-root outputs\06_analysis\source_assets\<source_id> `
  --manifest outputs\06_analysis\source_asset_manifest.csv
```

- 파일명과 CSV에는 원본 밀리초와 원본 프레임 번호가 들어간다.
- 같은 원본 지문에 이미 등록된 `source_id`가 있으면 다른 ID 사용을 거부한다.
- 같은 `source_id`에 다른 원본 지문을 섞으려 하면 명시적 승격 전까지 거부한다.
- 편집본 시각은 컷리스트로 원본 시각을 해석한 뒤 조회한다.
- 기존 자산은 삭제하거나 덮어쓰지 않는다.
- 실행 결과는 `reused`, `created` 수와 실제 경로를 JSON으로 출력한다.

이미 존재하는 접촉시트·오디오·프레임 묶음은
`outputs/06_analysis/source_asset_catalog.csv`에 원본 시작·끝 시각과 용도를 기록한 뒤 등록한다.

```powershell
python tools\register_source_assets.py `
  --catalog outputs\06_analysis\source_asset_catalog.csv `
  --manifest outputs\06_analysis\source_asset_manifest.csv
```

등록 시 원본 크기·수정 시각·FPS와 자산 해시를 확정한다. 같은 자산 ID나 경로를 중복 등록하면 실패한다.

## synccheck

`tools/synccheck/`의 스크립트는 새 원본 경로와 컷리스트를 명령행 인자로 받아 실행한다. 과거 세션 절대경로나 특정 원본 파일명은 기준으로 삼지 않는다.

예시:

```powershell
python tools\synccheck\vadcheck.py "inputs\원본.mp4" "inputs\원본.srt" --clip "B03:00:12:10-00:13:00"
python tools\synccheck\align.py "inputs\원본.mp4" "inputs\원본.srt" --clip "B03:00:12:10-00:13:00"
python tools\synccheck\full_scan.py "inputs\원본.mp4" "outputs\07_edit_export\cutlist.csv"
python tools\synccheck\build_v9.py "outputs\07_edit_export\cutlist.csv" "outputs\07_edit_export\cutlist_adjusted.csv" --start 3=00:12:09.5
```

- `full_scan.py`는 제안만 출력하고 파일을 수정하지 않는다.
- `build_v9.py`는 명시한 경계 수정만 반영해 새 CSV를 만든다. 기존 CSV는 덮어쓰지 않는다.
- `synccheck`는 발화·자막 경계 위험을 찾는 보조 도구다. microbeat의 기능, 유지·제거,
  편집 템포를 결정하는 도구로 사용하지 않는다.

## 편집 품질 일관성 감사

`edit_quality_audit.py`는 콘텐츠 기준 단일 시퀀스 컷리스트를 비트별로 묶어 컷 수·선택 길이·
평균·최장 컷을 계산하고, 모드별 장구간과 후반 밀도 편차를 검토 대상으로 표시한다.

```powershell
python tools/edit_quality_audit.py <콘텐츠_컷리스트.csv> <품질_프로필.csv> `
  --output <새_감사보고서.md>
```

- 경고선은 목표 컷 길이가 아니라 재검토 기준이다.
- 긴 컷의 화면·문장·사건 근거는 프로필의 `waive`·`justification`에 기록하며 보고서에 `WAIVED`로 남는다.
- 근거 없는 경고는 `REVIEW`로 남고 보고서 상태가 `REVIEW_REQUIRED`가 된다.
- 같은 컷이 두 번 들어 있는 멀티시퀀스 CSV는 거부한다.
- 기존 감사 보고서는 덮어쓰지 않는다.
