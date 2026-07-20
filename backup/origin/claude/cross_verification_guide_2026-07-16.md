# 교차검증 가이드 — change 0001 구현 + 0002 제안

- 작성일: 2026-07-16
- 대상: Claude 외 다른 AI 에이전트 (Codex, Gemini 등)
- 목적: `refactoring` 브랜치의 change 0001 구현을 독립 검증하고,
  0002 제안·청사진 보고서를 비판적으로 검토한다.
- 원칙: 이 검증은 **읽기 전용**이다. 상태 파일·문서·DB를 수정하지 않는다.
  발견 사항은 이 폴더에 새 보고 파일(`claude/cross_verification_report_<agent>_<날짜>.md`)로 작성한다.

## 0. 검증 범위

| 대상 | 위치 |
|---|---|
| 명세 | docs/changes/0001-governed-context-efficient-resume.md (상태 `implemented`) |
| 구현 커밋 | `refactoring` 브랜치에서 `[change: 0001]` 태그가 붙은 커밋들 |
| 신규 제안 | docs/changes/0002 (상태 `proposed`, 구현 금지) |
| 청사진 보고서 | claude/project_improvement_blueprint_2026-07-16.md |

## 1. 환경 준비

```text
git fetch origin
git checkout refactoring
git config core.hooksPath .githooks
```

- POSIX 환경이면 `.githooks/pre-commit` 실행 권한을 확인한다(`ls -l`; 644면 chmod +x 필요).
- Python 실행은 Windows에서 `tools\run_python.bat`, POSIX에서 `python3`를 쓴다.

## 2. 자동 검증 체크리스트 (명령과 기대값)

각 항목을 실행하고 PASS/FAIL과 실제 출력 요약을 기록한다.

### 2.1 전체 단위 테스트

```text
python3 -m unittest discover -s tests -p "test_*.py"
```

기대: 전체 통과 (100개 이상, skip 2개 허용), 실패 0.

### 2.2 문서 정합성

```text
python3 tools/doccheck/check_docs.py
```

기대: `errors=0`. (컨텍스트 예산 검사 포함: fast_resume 5문서/200줄/10,000자)

### 2.3 SDD 게이트 — 커밋 범위 검사

```text
python3 tools/sdd_gate.py check-range main HEAD
python3 tools/sdd_gate.py audit
```

기대: check-range `failed=0`. audit에서 `[change: 0001]` 커밋들이 compliant,
게이트 도입 전 커밋은 pre-gate로 분리, proposal 0001은 `implemented`.

### 2.4 SDD 게이트 — 행동 검증 (임시 저장소)

프로젝트 밖 임시 git 저장소에 `tools/sdd_gate.py`만 복사해 아래 표를 재현한다.
(방법: 제안 생성은 `propose`, 검사는 `check --message-file`)

| 시나리오 | 기대 |
|---|---|
| docs/changes만 추가 + 상태 proposed | 통과 |
| 프레임워크 파일 변경 + 태그 없음 | 차단 |
| 프레임워크 변경 + `[change: NNNN]` + 상태 proposed | 차단 |
| 프레임워크 변경 + 태그 + 상태 approved | 통과 |
| `[waiver: 자유형식 문장]` | 차단 |
| `[waiver: ID]` + docs/changes/waivers/ID.md 존재 | 통과 |
| inputs/·outputs/·claude/만 변경 | 게이트 제외 |
| 한 커밋에 change ID 2개 | 차단 |
| 태그 없이 커밋한 뒤 check-range | 사후 적발 |

### 2.5 compact 검증 출력 예산

```text
python3 tools/projectctl.py verify
```

기대: 검사명·PASS/FAIL·개수 요약 형식이고 출력이 2,000자 이하.
참고: `workflow_gate`는 outputs/WORKFLOW_STATE.json 부재(진행 중 영상 없음)로
FAIL이 정상이며, 이는 0001 이전부터 있는 기존 동작이다. 나머지 4개 검사는 PASS여야 한다.
`--verbose`에서 전체 JSON이 나오는지도 확인한다.

### 2.6 edit_memory 읽기 전용 계약

임시 디렉토리에서:

```text
python3 tools/edit_memory.py status --db <없는경로>/m.sqlite3      # 기대: 오류 종료, 파일 미생성
python3 tools/edit_memory.py apply --db <없는경로>/m.sqlite3 --input x.json  # 기대: 동일
python3 tools/edit_memory.py init --db m.sqlite3                   # 기대: 생성 성공
python3 tools/edit_memory.py status --db m.sqlite3                 # 기대: 압축 요약(전체 스냅샷 아님)
python3 tools/edit_memory.py validate --db m.sqlite3               # 기대: 오류·경고·이벤트 수만
```

추가: status/validate 실행 전후 DB 파일 해시·수정시간이 같아야 한다.
(회귀 테스트 `tests/test_edit_memory.py`의 ReadOnlyContractTests가 같은 내용을 검사한다.)

### 2.7 시작 문서 예산

```text
wc -l PROJECT_BOOTSTRAP.md docs/INDEX.md SESSION_HANDOFF.md
```

기대: 각각 60·60·20줄 이하, 합계와 문자 수가 doccheck 예산 안.

## 3. 문서 교차검토 (판단 검증)

자동 검사로 잡히지 않는 부분이다. 각 질문에 근거와 함께 답한다.

### 3.1 명세 대 구현 (0001)

- 0001 문서 5~9장의 요구가 실제 코드와 일치하는가? 누락·과잉 구현은 없는가?
- 14장 레드팀 항목(형식적 제안 우회, waiver 자기승인, 훅 우회, 안전 규칙 축소,
  stale 핸드오프, 거버넌스 비용)에 대한 대응이 실제로 구현됐는가?
- 게이트가 증명하지 못하는 것(승인 주체의 신원)이 문서·출력에 정직하게 명시돼 있는가?

### 3.2 설계 비판 (0002 + 청사진)

- 4계층 문서 구조(L0/인덱스/잎/메타)의 실패 모드 중 청사진 7장 위험 표에 빠진 것이 있는가?
- 번호 주소 체계(10~90)가 이 프로젝트의 실제 작업 분포에 맞는가?
- "규칙 하나당 검사기 하나" 원칙의 예외가 필요한 지점이 있는가?
- 하이브리드 경계(지식=문서, 상태=데이터)에서 애매해지는 실제 사례를 3개 이상 들 수 있는가?
- 마이그레이션 로드맵에서 가장 먼저 실패할 단계는 어디라고 보는가?

## 4. 보고 형식

```text
# 교차검증 보고 — <agent> — <날짜>
## 자동 검증: 항목별 PASS/FAIL + 실제 출력 요약
## 명세 대 구현: 일치/불일치 목록 (근거 포함)
## 설계 비판: 3.2 질문별 답변 + 추가 발견 위험
## 종합: 동의/이의/보류 + 다음 행동 제안
```

- 미검증 항목은 "확인 안 함"으로 명시한다. 추측을 결과로 쓰지 않는다.
- 이 저장소의 파일은 수정하지 않는다. 보고 파일 추가만 허용된다.
