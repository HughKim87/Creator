# 컨텍스트 효율적 작업 재개 구조 개선 제안서

- 역할: 작업 재개 시 과도한 문서 로드와 검증 출력을 줄이기 위한 설계 제안서
- 읽는 시점: 진입 규칙, 핸드오프, 프로젝트 제어 도구 또는 관련 스킬을 개선하기 전
- 보존 조건: 제안이 승인·구현·검증될 때까지 유지하고, 구현 후에는 결과 문서에서 이 문서를 역사적 설계 근거로 연결한다.
- 상태: `proposed` — 아직 적용하지 않음
- 범위: Tier-1/로컬 진입 경로, 핸드오프 읽기 계약, `projectctl`, `edit_memory`, `handoff-manager`, 문서 검사
- 작성일: 2026-07-16

## 1. 제안 요약

현재 문제는 폴더 배치보다 "어떤 상황에서 어떤 문서를 얼마만큼 읽을지"를 결정하는 제어 구조에 있다. 상위·하위 진입 규칙, 상세 핸드오프, 상태 원본, 검증 도구가 각각 합리적인 역할을 갖지만, 단순 재개에서도 모두 연결되어 컨텍스트가 급격히 증가한다.

다음 다섯 가지를 제안한다.

1. Tier-1 안전 규칙과 Tier-1 작업 상태를 분리한다.
2. 작업 재개를 `fast_resume`, `audit`, `mutation` 3개 모드로 나눈다.
3. `outputs/SESSION_HANDOFF.md`의 첫 부분을 유일한 재개 캡슐로 사용하고 근거 문서는 필요할 때만 읽는다.
4. 성공한 검증은 요약만 출력하고 상세 정보는 실패 또는 `--verbose`에서만 출력한다.
5. 파일별 크기뿐 아니라 실제 필수 읽기 경로의 총량과 읽기 전용 도구의 무변경성을 자동 검사한다.

새 `RESUME.json` 같은 별도 상태 파일은 만들지 않는다. 재개 상태의 단일 정본은 계속 `outputs/SESSION_HANDOFF.md`로 유지한다.

## 2. 확인된 현황

### 2.1 상위·하위 진입 규칙 충돌

- Tier-1 `../../AGENTS.md`는 모든 작업 전에 Tier-1 `PROJECT_RULES.md`를 읽도록 한다.
- Tier-1 `../../PROJECT_RULES.md`는 매 세션 Tier-1 `SESSION_HANDOFF.md`까지 읽도록 한다.
- 로컬 `AGENTS.md`는 `PROJECT_BOOTSTRAP.md`와 `docs/INDEX.md`를 먼저 읽고 `PROJECT_RULES.md`는 조건부로 읽도록 한다.
- Tier-1 `SESSION_HANDOFF.md`에는 현재 영상 작업과 무관한 AI 도구 리서치 상태가 들어 있다.

결과적으로 하위 영상 프로젝트에서 작업해도 Tier-1 작업 상태와 로컬 작업 상태를 모두 읽게 된다. Tier-1 안전 규칙 상속은 필요하지만 Tier-1 활성 작업 상태 상속은 필요하지 않다.

### 2.2 핸드오프의 요약과 근거가 동시 필수화됨

현재 `outputs/SESSION_HANDOFF.md` 첫 10줄에는 다음 내용이 이미 있다.

- 현재 단계와 후보
- 기준본 유무
- 확장 잠금 상태
- 검증 범위별 상태

그러나 이어지는 읽기 순서가 계약, 편집 기억, 워크플로 상태, 후보 상태, 설계, 오디오 분석까지 9개 문서를 다시 읽도록 한다. 현재 경로에서 확인한 관련 문서는 합계 1,496줄, 61,166자다. 이 수치에는 로컬 전체 규칙, 문서 유지 규칙, 281줄의 `tools/README.md`, 스킬 지침, 검증 명령 출력이 포함되지 않는다.

### 2.3 개별 파일 크기만 제한함

`docs/AGENT_MAINTENANCE.md`는 시작 문서와 핸드오프의 개별 줄 수를 제한한다. 현재 주요 문서는 각각 목표 상한에 거의 도달했다. 하지만 여러 문서가 한 경로로 연결될 때의 합계 제한은 없다.

따라서 개별 문서가 규칙을 준수해도 실제 콜드 스타트 컨텍스트는 계속 증가할 수 있다.

### 2.4 검증 명령 출력과 부작용

- `tools/projectctl.py`의 `verify_project()`는 5개 검사 결과를 반환한다.
- 각 검사는 성공 여부와 관계없이 최대 2,000자의 상세 출력을 보존한다.
- `verify`는 전체 결과를 JSON으로 출력한다.
- `tools/edit_memory.py`는 `status`와 `validate`에서도 공통 `initialize()`를 실행한다.
- `initialize()`는 `metadata.updated_at`을 현재 시간으로 갱신한다.
- `validate()`는 경고 요약뿐 아니라 전체 스냅샷을 반환한다.

읽기 검증이 파일을 변경하고 성공 결과가 전체 상태를 다시 출력하는 것은 컨텍스트 효율과 읽기 전용 계약을 동시에 해친다.

### 2.5 스킬 모드 미분리

현재 `handoff-manager`는 생성·수정·감사·재개 준비를 하나의 워크플로로 다룬다. 정밀 감사에는 적합하지만 "핸드오프 읽고 준비" 같은 요청에도 전체 근거 확인과 검증을 유도한다.

## 3. 목표와 비목표

### 3.1 목표

- 단순 재개에서 프로젝트가 추가하는 필수 컨텍스트를 10,000자 이하로 제한한다.
- 단순 재개는 최대 5개 문서, 200줄 이하에서 완료한다.
- 상태 변경 전에는 필요한 계약과 근거를 지연 로드한다.
- 성공한 검증 출력은 2,000자 이하로 제한한다.
- `status`와 `validate`는 DB 내용, 메타데이터, 수정시간을 변경하지 않는다.
- 안전 규칙, 실패 기억, 승인 게이트는 축소 과정에서도 유지한다.

### 3.2 비목표

- 영상별 상태 원본을 새 파일로 복제하지 않는다.
- 자동 검증을 제거하거나 사용자 승인을 우회하지 않는다.
- 실패 원장과 역사적 거절 근거를 삭제하지 않는다.
- 현재 편집 후보를 승인·승격하거나 전체 편집을 시작하지 않는다.
- 이번 제안 단계에서 규칙·도구·스킬을 실제 수정하지 않는다.

## 4. 제안하는 재개 모델

### 4.1 `fast_resume`

적용 요청 예시:

- "핸드오프 읽어"
- "작업 준비해"
- "현재 어디까지 했어?"
- "다음에 뭘 하면 돼?"

필수 읽기:

1. Tier-1 안전 커널
2. 로컬 `PROJECT_BOOTSTRAP.md`
3. 로컬 `docs/INDEX.md`
4. 루트 `SESSION_HANDOFF.md`
5. `outputs/SESSION_HANDOFF.md`의 재개 캡슐과 현재 목표

허용 작업:

- 현재 단계, 후보, 첫 미착수 작업, 차단 요소, 금지 행동 보고
- 필요한 다음 문서 목록 제시
- 파일을 변경하지 않는 compact preflight

금지 작업:

- 상세 근거 문서 일괄 로드
- 전체 테스트·감사
- DB `validate`
- 상태 승격 또는 후보 변경
- 핸드오프 수정

### 4.2 `audit`

적용 요청 예시:

- "핸드오프 검증해"
- "상태가 맞는지 감사해"
- "오래된 지침 정리해"
- 핸드오프를 수정하기 전의 사실 확인

추가 읽기:

- 현재 단계의 계약과 상태 파일
- 직접 연결된 근거 파일
- 실패 원장과 최신 usable revision
- 필요한 범위의 도구 지침

허용 작업:

- 경로, 수치, 상태, 검증 수준 대조
- stale/superseded 지침 식별
- 읽기 전용 검증

### 4.3 `mutation`

적용 요청 예시:

- "계속 진행해"
- "승인했으니 다음 단계로 가"
- "핸드오프 업데이트해"
- "도구를 고쳐"

추가 절차:

- `projectctl start`로 작업 점유
- 변경 대상의 계약과 소유권 확인
- 필요한 상태 원본만 로드
- 변경 후 검증과 `projectctl finish`

## 5. 문서 구조 개선안

### 5.1 Tier-1 진입점

제안 대상:

- `../../AGENTS.md`
- `../../PROJECT_RULES.md`
- 신규 후보 파일명: TIER1_SAFETY_KERNEL.md (Tier-1 `docs/` 아래 생성 제안)

제안 내용:

- Tier-1 루트에서 작업할 때만 Tier-1 `SESSION_HANDOFF.md`를 읽는다.
- `Workspace/<project>/`에서 시작하면 Tier-1 안전 커널만 읽고 로컬 진입점으로 넘긴다.
- 안전 커널에는 보안, 외부 쓰기, 삭제·덮어쓰기, 권한, 백업 충돌 규칙만 둔다.
- Tier-1 연구 상태와 하위 프로젝트 상태를 서로 자동 상속하지 않는다.

권장 의사코드:

```text
if cwd is inside Workspace/<project>:
    read Tier-1 safety kernel
    read local AGENTS/bootstrap/index
    do not read Tier-1 session handoff
else:
    read Tier-1 project rules and Tier-1 session handoff
```

### 5.2 로컬 부트스트랩과 인덱스

제안 대상:

- `PROJECT_BOOTSTRAP.md`
- `docs/INDEX.md`

제안 내용:

- "계속 작업"의 기본 모드를 `fast_resume`으로 명시한다.
- `tools/README.md`는 도구 변경·장애 진단 때만 읽도록 제한한다.
- 사전 점검의 정확한 한 줄 명령은 부트스트랩에 직접 둔다.
- 작업을 실제 시작하기 전까지 단계 계약과 근거 문서를 읽지 않는다.
- `projectctl verify`는 단순 준비가 아니라 변경 후 검증 또는 명시적 감사에만 사용한다.

### 5.3 출력 핸드오프

제안 대상:

- `outputs/SESSION_HANDOFF.md`

권장 섹션:

1. 재개 캡슐: 15줄 이하
2. 현재 목표와 첫 미착수 작업
3. 허용·금지 행동
4. 검증 범위 요약
5. 압축 실패 원장
6. 필요 시 읽는 근거 문서

현재의 9개 문서 읽기 순서는 다음과 같이 바꾼다.

```text
필수: 이 핸드오프만
단계 변경 시: WORKFLOW_CONTRACT + WORKFLOW_STATE
편집 기억 변경 시: EDIT_MEMORY_KERNEL + edit memory database/view
근거 재검증 시: 현재 design/audio analysis
```

상태 사실은 핸드오프에 유지하되 상세 측정값과 긴 설명은 기존 근거 문서에 남긴다. 핸드오프에는 해당 근거의 현재 상태와 경로만 기록한다.

### 5.4 문서 유지 규칙

제안 대상:

- `docs/AGENT_MAINTENANCE.md`
- `tools/doccheck/check_docs.py`

추가 검사:

- `fast_resume` 필수 문서 수
- 필수 경로 합계 줄 수와 문자 수
- 핸드오프의 필수 읽기 링크 수
- 시작 문서가 긴 도구 README를 무조건 읽도록 하는지
- 상위 세션 상태가 하위 프로젝트 재개 경로에 포함되는지
- 재개 캡슐에 단계·후보·첫 행동·금지 행동이 있는지

## 6. 도구 개선안

### 6.1 `projectctl`

제안 대상:

- `tools/projectctl.py`
- `tests/test_projectctl.py`

제안 인터페이스:

```bat
tools\projectctl.bat context
tools\projectctl.bat verify
tools\projectctl.bat verify --verbose
```

기본 `verify` 출력:

```text
ok=true
doccheck=PASS warnings=8
workflow_gate=PASS
unit_tests=PASS count=73
git_diff_check=PASS
git_cached_diff_check=PASS
```

상세 출력 정책:

- 성공한 검사는 기본적으로 상세 로그를 출력하지 않는다.
- 실패한 검사만 마지막 관련 로그를 출력한다.
- `--verbose`에서만 현재와 같은 전체 JSON을 출력한다.
- 내부 반환값은 유지해 `finish`와 테스트가 검사 정보를 사용할 수 있게 한다.

### 6.2 `edit_memory`

제안 대상:

- `tools/edit_memory.py`
- `tests/test_edit_memory.py`
- `docs/EDIT_MEMORY_KERNEL.md`

명령별 연결 정책:

| 명령 | DB 열기 | 스키마 생성 | `updated_at` 변경 | 기본 출력 |
|---|---|---:|---:|---|
| `init` | read-write | 허용 | 허용 | 초기화 결과 |
| `apply` | read-write | 기존 DB 요구 | 이벤트 적용 시 허용 | 적용·skip 수 |
| `export` | read-only 권장 | 금지 | 금지 | 출력 경로·이벤트 수 |
| `status` | read-only | 금지 | 금지 | 압축 상태 |
| `validate` | read-only | 금지 | 금지 | 오류·경고·이벤트 수 |

추가 옵션:

```bat
tools\run_python.bat tools\edit_memory.py validate --db <database>
tools\run_python.bat tools\edit_memory.py validate --db <database> --verbose
```

회귀 테스트는 `status`와 `validate` 실행 전후에 다음이 같은지 확인한다.

- DB 파일 해시
- DB 수정시간
- `metadata.updated_at`
- 이벤트 수
- baseline pointer

## 7. 스킬 개선안

제안 대상:

- 개인 handoff-manager 스킬 패키지의 지침 파일 (프로젝트 외부 설치 영역)

제안 내용:

- 요청을 먼저 `resume`, `audit`, `update` 중 하나로 분류한다.
- `resume`은 기존 핸드오프를 수정하지 않으므로 전체 근거 재검증을 요구하지 않는다.
- `audit`과 `update`에서만 최신 usable version, 실패 원장, 검증 표면을 대조한다.
- "핸드오프 읽고 준비" 예시를 `resume` 트리거로 명시한다.
- `resume`에서는 파일을 최대 5개까지만 읽고 추가 문서는 실제 다음 작업이 시작될 때 지연 로드한다.

## 8. 적용 순서

### 1단계: 정확성 문제 수정

1. `edit_memory status/validate` 읽기 전용화
2. 무변경 회귀 테스트 추가
3. `projectctl verify` compact 출력 추가

### 2단계: 재개 경로 축소

1. Tier-1/로컬 진입 규칙 통합
2. 상위 세션 핸드오프의 하위 자동 로드 제거
3. 로컬 핸드오프의 9개 필수 읽기 순서 제거
4. 부트스트랩에 `fast_resume` 계약 추가

### 3단계: 스킬과 자동 검사

1. `handoff-manager` 모드 분리
2. doccheck에 합계 컨텍스트 예산 검사 추가
3. 재개 시뮬레이션 테스트 추가

### 4단계: 실제 세션 검증

1. 새 세션에서 "핸드오프 읽고 작업 준비해" 실행
2. 읽은 파일 목록과 출력 문자 수 기록
3. 상태 파일과 DB가 변경되지 않았는지 확인
4. 다음 행동과 금지 행동을 올바르게 보고하는지 확인
5. 실제 변경 요청에서 필요한 계약이 지연 로드되는지 확인

## 9. 승인 기준

다음 조건을 모두 만족하면 개선이 완료된 것으로 본다.

- `fast_resume` 필수 문서가 5개 이하이다.
- 프로젝트가 추가하는 필수 재개 컨텍스트가 200줄, 10,000자 이하이다.
- Tier-1 작업 상태가 하위 영상 프로젝트 세션에 자동 로드되지 않는다.
- 핸드오프만으로 현재 단계, 후보, 첫 미착수 작업, 차단 요소, 금지 행동을 알 수 있다.
- 성공한 `projectctl verify` 출력이 2,000자 이하이다.
- `edit_memory status/validate` 전후 DB 해시와 수정시간이 동일하다.
- 상세 감사 모드에서는 기존 실패 원장과 근거를 모두 추적할 수 있다.
- doccheck와 전체 단위 테스트가 통과한다.

UI의 전체 컨텍스트 잔여율은 플랫폼 시스템 지침과 도구 정의도 포함하므로 승인 기준으로 사용하지 않는다. 대신 프로젝트가 직접 추가하는 문서·출력 총량을 측정한다.

## 10. 레드팀 검토

### 안전 규칙 누락 위험

상위 전체 규칙을 읽지 않게 하면 안전 규칙이 누락될 수 있다.

대응:

- Tier-1 안전 커널을 별도로 만들고 항상 읽는다.
- 안전·권한·백업 충돌은 계속 Tier-1이 우선한다.
- 안전 커널 변경 시 Tier-1 전체 규칙과의 동기화 검사를 추가한다.

### 오래된 핸드오프 신뢰 위험

`fast_resume`이 상세 근거를 확인하지 않으면 stale 상태를 그대로 전달할 수 있다.

대응:

- `fast_resume`은 보고만 허용하고 상태 변경을 금지한다.
- 실제 변경 전 `mutation` 모드에서 관련 상태 원본과 계약을 확인한다.
- 핸드오프에 갱신일, source_id, 후보 ID와 상태 포인터를 유지한다.

### 상태 원본 증가 위험

별도 요약 JSON이나 자동 생성 재개 파일은 상태 원본을 늘릴 수 있다.

대응:

- 새 상태 파일을 만들지 않는다.
- `outputs/SESSION_HANDOFF.md`의 첫 섹션을 기계가 읽을 수 있는 고정 형식으로 사용한다.
- 도구는 이 섹션을 출력할 수 있지만 별도 저장하지 않는다.

### 실패 기억 손실 위험

핸드오프를 줄이면서 과거 실패와 사용자 거절 근거가 사라질 수 있다.

대응:

- 실패 원장은 압축 표 형태로 핸드오프에 유지한다.
- 상세 이벤트는 edit memory에 유지한다.
- `fast_resume`은 활성 금지 사항만 읽고, `audit/mutation`은 전체 실패 근거를 확인한다.

### 도구 호환성 위험

`validate`에서 자동 초기화를 제거하면 아직 초기화되지 않은 DB 사용이 실패할 수 있다.

대응:

- `validate`는 명확한 `database_not_initialized` 오류를 반환한다.
- 초기화는 사용자가 명시한 `init`에서만 수행한다.
- 기존 DB와 신규 DB를 나눈 회귀 테스트를 추가한다.

## 11. 변경 범위와 승인 필요 사항

### 로컬 프로젝트 안에서 적용 가능한 변경

- `PROJECT_BOOTSTRAP.md`
- `docs/INDEX.md`
- `docs/AGENT_MAINTENANCE.md`
- `outputs/SESSION_HANDOFF.md`
- `tools/projectctl.py`
- `tools/edit_memory.py`
- 관련 테스트와 문서 검사

### 별도 권한 또는 범위 승인이 필요한 변경

- Tier-1 `../../AGENTS.md`
- Tier-1 `../../PROJECT_RULES.md`
- Tier-1 안전 커널 신규 생성
- 개인 `handoff-manager` 스킬 수정

Tier-1 진입 규칙을 그대로 두고 로컬 문서만 줄이면 효과가 제한된다. 전체 개선을 위해서는 로컬 변경과 Tier-1 변경을 하나의 승인된 구현 계획으로 묶되, 파일 소유권과 검증은 각각 분리하는 것이 권장된다.

## 12. 제안 상태

- 적용된 변경: 없음
- 제안된 변경: 본 문서의 Tier-1, 로컬 문서, 도구, 테스트, 스킬 개선안
- 백업: 신규 문서이므로 불필요
- 다음 결정: 사용자가 제안 범위와 적용 순서를 승인한 뒤 구현 계획을 확정한다.
