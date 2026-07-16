# 프로젝트 청사진 교차검증 프로토콜

- 역할: 다른 AI 에이전트가 청사진 보고서의 사실·판단·우선순위를 독립적으로 재현하고 반증하게 하는 검증 계약
- 읽는 시점: `gpt/project_blueprint_report_2026-07-16.md`를 교차검증할 때
- 보존 조건: 청사진이 `superseded`될 때까지 유지하고, 후속 보고서는 새 검증 프로토콜을 만든다.
- 검증 대상: 이 파일이 포함된 `video/backroom` 브랜치의 현재 원격 커밋
- 검증 모드: 읽기 전용. 파일·상태·브라우저·외부 시스템을 변경하지 않는다.
- 적용 원칙: P2 결정적 검증, P3 에이전트 교체 가능성, P4 컨텍스트 예산
- 결과 상태: `CONFIRMED`, `PARTIAL`, `REFUTED`, `STALE`, `NOT_TESTED`만 사용
- 주의: 보고서의 개선안은 제안이며, 확인된 현재 사실과 분리해 판정한다.

## 1. 교차검증 목표

교차검증자는 보고서를 요약하거나 동의하는 역할이 아니다. 아래 세 가지를 독립적으로 수행한다.

1. 수치와 상태를 같은 저장소에서 재현한다.
2. 각 P0·P1 판단을 반증할 수 있는 증거를 먼저 찾는다.
3. 사실 오류, 오래된 수치, 과도한 우선순위, 빠진 위험을 명시한다.

최종 판정은 다음 기준을 따른다.

| 상태 | 의미 |
|---|---|
| `CONFIRMED` | 두 개 이상의 독립 근거가 주장을 지지함 |
| `PARTIAL` | 핵심 방향은 맞지만 범위·수치·인과에 수정이 필요함 |
| `REFUTED` | 반대 증거가 더 강하거나 재현에 실패함 |
| `STALE` | 작성 후 상태가 바뀌어 현재 사실로 쓸 수 없음 |
| `NOT_TESTED` | 권한·도구·시간 제약으로 검증하지 못함 |

## 2. 검증 전 안전 조건

- `inputs/`의 미디어·자막 내용은 열거나 복사하지 않는다.
- `.env`, 키, 토큰, 쿠키, 브라우저 프로필, 자격 증명 파일을 읽지 않는다.
- `outputs/AGENT_CONTROL.json`과 워크플로 상태는 읽기만 한다.
- `projectctl start`, `projectctl finish`, 편집 기억 `apply`, 기준본 승격을 실행하지 않는다.
- 브라우저·로컬 서버·Premiere를 열지 않는다.
- `git reset`, `git clean`, 삭제, 이동, 커밋, 푸시를 실행하지 않는다.
- 네트워크 자료는 이 로컬 구조 진단에 필요하지 않다. 외부 근거를 추가하면 출처와 확인 시각을 기록한다.

## 3. 시작 순서

아래 문서를 끝까지 읽는다.

1. `PROJECT_BOOTSTRAP.md`
2. `docs/INDEX.md`
3. `PROJECT_RULES.md`
4. `docs/DESIGN_PRINCIPLES.md`
5. `gpt/project_blueprint_report_2026-07-16.md`
6. 이 문서

검증 시작 시 아래 세 값을 결과 문서에 기록한다.

```powershell
tools\git_project.bat branch --show-current
tools\git_project.bat rev-parse HEAD
tools\git_project.bat status --short
```

예상 브랜치는 `video/backroom`이다. 커밋 해시는 이 문서에 고정하지 않고 검증자가 실행 시점 값을 기록한다. 작업 트리가 깨끗하지 않으면 변경 경로와 검증 영향부터 분리한다.

## 4. 공통 재현 명령

### 4.1 프로젝트 검사

```powershell
tools\project_preflight.bat
tools\projectctl.bat verify
```

확인 항목:

- preflight 성공 여부
- doccheck 오류·경고 수
- 단위 테스트 수와 실패 수
- workflow gate의 `edit_full`, `validation`, `final` 차단 이유
- 성공 출력의 문자 수가 제안 목표 2,000자를 넘는지

성공 출력 길이는 다음처럼 별도로 측정한다.

```powershell
$text = tools\projectctl.bat verify 2>&1 | Out-String
$text.Length
```

### 4.2 Git 경계

```powershell
$trackedOutputs = tools\git_project.bat -c core.quotepath=false ls-files outputs
($trackedOutputs | Measure-Object).Count
tools\git_project.bat log -1 --oneline -- outputs
Get-Content .gitignore -Encoding UTF8
```

판정 기준:

- `outputs/` 추적 파일이 1개 이상이면 “영상별 산출물을 커밋하지 않는다”는 규칙과 실제 상태가 충돌한다.
- `.gitignore`가 `outputs/` 추적을 의도한다고 쓰여 있으면 단순 실수가 아니라 정책 정본 충돌이다.
- Git 추적 해제·history rewrite는 검증 범위를 넘어가므로 수행하지 않는다.

### 4.3 로컬 규모

```powershell
$roots = @('inputs', 'outputs')
foreach ($root in $roots) {
  $files = Get-ChildItem $root -File -Recurse -Force
  [PSCustomObject]@{
    Root = $root
    Files = $files.Count
    Bytes = ($files | Measure-Object Length -Sum).Sum
  }
}
```

수치는 작성 이후 파일 생성으로 변할 수 있다. 달라졌다는 이유만으로 `REFUTED`로 처리하지 말고, 차이가 어떤 새 파일에서 생겼는지 확인해 `STALE` 또는 `PARTIAL`로 판정한다.

### 4.4 빠른 재개 예산

```powershell
$resume = @(
  'PROJECT_BOOTSTRAP.md',
  'docs/INDEX.md',
  'SESSION_HANDOFF.md',
  'outputs/SESSION_HANDOFF.md'
)
$lines = 0
$chars = 0
foreach ($path in $resume) {
  $content = Get-Content $path -Raw -Encoding UTF8
  $lines += ($content -split "`r?`n").Count
  $chars += $content.Length
}
[PSCustomObject]@{ Files = $resume.Count; Lines = $lines; Chars = $chars }
```

판정 기준은 변경 제안 0001의 5개 문서 이하, 200줄 이하, 10,000자 이하 목표다. 현재 구조가 목표를 넘는다는 사실과, 그 목표가 아직 `proposed` 상태라는 사실을 분리해 적는다.

### 4.5 단일 활성 작업 제어

```powershell
tools\projectctl.bat context
Get-Content outputs\AGENT_CONTROL.json -Raw -Encoding UTF8
rg -n -C 5 "active task conflict|active_task" tools\projectctl.py tools\projectctl.schema.json
```

`projectctl start`를 실제로 호출하지 않는다. 다음 두 조건이 모두 보이면 보고서 주장을 확인한 것으로 본다.

1. 사용자 응답 대기 작업이 `active_task`를 점유한다.
2. 다른 task ID를 시작하면 충돌하도록 코드가 설계되어 있고 `waiting_user`나 `paused` 상태가 없다.

### 4.6 에이전트별 강제 차이

```powershell
Get-Content tools\guard\agent_guard.py -Raw -Encoding UTF8
Get-Content tools\guard\codex_config.template.toml -Raw -Encoding UTF8
Get-Content tools\guard\gemini_settings.template.json -Raw -Encoding UTF8
Get-Content .githooks\pre-commit -Raw -Encoding UTF8
Get-Content .github\workflows\ci.yml -Raw -Encoding UTF8
```

확인 항목:

- Claude 훅이 저장소에서 실행되는지
- Codex·Gemini 설정이 저장소 강제인지 사용자 적용 템플릿인지
- Python 부재 시 pre-commit이 통과하는지
- CI가 Git 경계와 change ID를 검사하는지

### 4.7 현재 워크플로 게이트

```powershell
Get-Content outputs\SESSION_HANDOFF.md -Raw -Encoding UTF8
Get-Content outputs\WORKFLOW_STATE.json -Raw -Encoding UTF8
tools\run_python.bat tools\workflow_gate.py audit
```

판정 기준:

- 연속 A/V와 앱 검증이 pending인지
- approved 기준본과 생성 잠금 해제가 없는지
- 그 상태에서 전체 편집·검증·최종 전환이 차단되는지
- 이 차단을 프레임워크 결함이 아니라 정상 게이트 작동으로 구분했는지

### 4.8 `gpt/` 소유권 등록

```powershell
rg -n "gpt/|\"gpt\"" README.md PROJECT_RULES.md docs\INDEX.md tools\doccheck\check_docs.py tests\test_skill_asset_lifecycle.py
tools\run_doccheck.bat
```

확인 항목:

- `gpt/`의 역할이 교차검증·진단으로 한정되는지
- 운영 규칙이나 영상 산출물의 정본으로 사용하지 않는지
- doccheck allowlist만 고치고 소유권 문서를 빠뜨리지 않았는지
- 미분류 최상위 폴더를 거부하는 기존 회귀 테스트가 유지되는지

## 5. 주장별 판정표

| ID | 검증할 주장 | 최소 근거 | 반증 질문 |
|---|---|---|---|
| CV-01 | 자동 검사 기반은 양호하다 | projectctl verify, 테스트 결과 | 통과가 빠뜨린 중요 규칙은 무엇인가? |
| CV-02 | outputs Git 정책과 실제 추적 상태가 충돌한다 | 규칙, `.gitignore`, `git ls-files` | 명시적으로 허용된 예외 기록이 있는가? |
| CV-03 | Git 경계 위반을 doccheck가 잡지 못한다 | doccheck 결과, 검사 코드 | 별도 CI나 훅이 이미 잡고 있는가? |
| CV-04 | 사용자 대기 작업이 독립 작업 등록을 막는다 | control JSON, projectctl 코드 | 안전한 pause/waiting 상태가 다른 곳에 있는가? |
| CV-05 | 빠른 재개와 verify 출력이 제안 목표를 넘는다 | 직접 문자·줄 수 측정 | 목표 자체가 승인된 운영 기준인가? |
| CV-06 | 에이전트별 로컬 강제력이 다르다 | guard·템플릿·훅·CI | 공통 외부 강제층이 따로 있는가? |
| CV-07 | 현재 전체 편집 차단은 정상 동작이다 | workflow state와 audit | 실제 A/V 승인 증거가 누락된 것뿐인가? |
| CV-08 | 산출물 정리는 자동 삭제보다 inventory가 안전하다 | CURRENT·manifest·memory 참조 | inventory 비용이 실제 위험보다 큰가? |
| CV-09 | `gpt/` 등록이 역할 중복을 통제한다 | 소유권 문서와 doccheck | planning_research와 경계가 여전히 모호한가? |

## 6. 필수 반증 절차

각 P0·P1 항목마다 다음 순서를 지킨다.

1. 주장을 지지하는 파일을 읽는다.
2. 같은 주장을 반박할 수 있는 규칙·코드·Git 기록을 검색한다.
3. 수치를 직접 재계산한다.
4. 사실, 해석, 권고를 각각 판정한다.
5. 보고서와 다른 결론이면 더 강한 근거를 경로와 함께 제시한다.

다음과 같은 검증은 불충분하다.

- 보고서 문장을 다시 인용하고 `CONFIRMED`로 표시
- 테스트 통과만으로 저장소 정책 전체가 맞다고 판단
- 현재 수치가 조금 바뀐 것을 핵심 인과의 반증으로 처리
- 자동 검사 결과를 사용자 창작 승인으로 확대 해석

## 7. 결과 문서 템플릿

다른 에이전트는 아래 형식을 그대로 사용한다.

```markdown
# 프로젝트 청사진 교차검증 결과

- 검증 에이전트:
- 검증 시각과 시간대:
- 브랜치:
- 검증 커밋:
- 작업 트리 상태:
- 전체 판정: CONFIRMED / PARTIAL / REFUTED
- 파일 변경: 없음

## 주장별 결과

| ID | 판정 | 재현 근거 | 반증 결과 | 필요한 수정 |
|---|---|---|---|---|
| CV-01 |  |  |  |  |
| CV-02 |  |  |  |  |
| CV-03 |  |  |  |  |
| CV-04 |  |  |  |  |
| CV-05 |  |  |  |  |
| CV-06 |  |  |  |  |
| CV-07 |  |  |  |  |
| CV-08 |  |  |  |  |
| CV-09 |  |  |  |  |

## 새로 발견한 문제

- 없음 / 경로·근거·영향

## 우선순위 재평가

1. [우선순위 1]
2. [우선순위 2]
3. [우선순위 3]

## 검증 한계

- NOT_TESTED 항목과 이유

## 최종 권고

- 원 보고서 유지 / 수정 후 유지 / 폐기
```

## 8. 합격 기준

교차검증 완료로 인정하려면 다음 조건을 모두 만족해야 한다.

- CV-01~CV-09가 모두 판정됨
- P0·P1마다 반증 시도가 기록됨
- 직접 실행한 명령과 근거 경로가 남음
- 사실 오류와 우선순위 이견이 분리됨
- 파일을 변경하지 않았음
- `NOT_TESTED`를 통과처럼 표현하지 않음

## 9. 결과 반영 규칙

- 수치만 오래됐으면 보고서의 수치와 확인 시각을 갱신한다.
- 핵심 인과가 틀렸으면 해당 문제의 우선순위를 내리고 근거를 교체한다.
- 새 P0 위험이 확인되면 기존 청사진을 바로 실행하지 않고 사용자에게 충돌을 보고한다.
- 두 에이전트의 결론이 다르면 다수결이 아니라 재현 가능한 근거의 강도로 결정한다.
- 교차검증 결과는 새 파일로 보존하되, 운영 규칙이나 현재 영상 상태의 정본으로 사용하지 않는다.
