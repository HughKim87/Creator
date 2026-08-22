# Agent-Core 단계 2 — 순수 Core 공개 계약 설계

- 목적: 순수 Core가 제공하는 불변 계약과 Maintainer·Host 소비 저장소가 제공하는 가변 계약을 분리하고, 단계 3의 정확한 변경 범위를 고정한다.
- 읽는 시점: 단계 2 결과를 검토할 때, 단계 3 Core 순수화 후보를 구현·검증할 때.
- 책임: 사용자가 계약과 비호환 변경을 승인하고, 작업 에이전트가 승인된 계약과 파일별 변경 범위를 유지한다.
- 상태: 활성 단계 설계. 단계 3 구현 결과가 Core 정본 문서에 흡수되고 해당 게이트가 통과하면 완료 설계로 전환한다.
- 관련 권위: [전체 단계 설계](Agent-Core_순수화_및_분리구조_단계설계.md), 현재 `Agent-Core`의 `docs/CHARTER.md`, `docs/COMPATIBILITY.md`, `docs/INFORMATION_ARCHITECTURE.md`.

---

## 1. 이번 단계의 목표와 범위

### 작업 목표

Core와 소비 저장소의 소유 정보를 섞지 않고도 에이전트 진입, 규칙 선택, 상태 복원, 보호 경계, Core 검증이 성립하는 공개 계약을 확정한다.

### 작업 의도

현재 Core는 공통 규칙·검증기뿐 아니라 자체 `AGENTS.md`, `CLAUDE.md`, `SESSION_HANDOFF.md`까지 같은 루트에 둔다. 이 구조를 그대로 submodule로 넣으면 Core 개발 상태와 Host 상태가 함께 존재하고, 특히 Claude가 하위 `CLAUDE.md`를 읽을 때 Host 정책과 Core 개발 정책이 충돌할 수 있다. 해결책은 진입 파일을 숨기는 설정에 의존하는 것이 아니라, Core가 소비 저장소의 진입·현재 상태를 소유하지 않게 만드는 것이다.

### 허용 범위

- 현재 Core 파일과 테스트의 읽기·분석
- 공개 계약, 호환성, 이전 절차, 파일별 변경안 설계
- Sandbox 설계문서 작성

### 제외 범위

- 실제 `Agent-Core` 파일 수정·삭제·개명
- Sandbox 구현 clone 생성
- Maintainer·Host 저장소 생성
- submodule 및 Deploy Key 설정
- Git stage·commit·push

---

## 2. 현재 구현에서 확인된 결합

| 현재 요소 | 현재 동작 | 순수 Core 소비 시 문제 |
|---|---|---|
| `AGENTS.md`, `CLAUDE.md` | Core 루트의 `PROJECT_RULES.md`를 자동 진입으로 읽음 | submodule 내부 자동 지침이 Host 진입과 충돌할 수 있음 |
| `PROJECT_RULES.md` | 같은 루트의 `SESSION_HANDOFF.md`를 필수 시작 문맥으로 지정 | Host 상태 대신 Core 개발 상태를 읽게 됨 |
| `docs/INFORMATION_ARCHITECTURE.md` | 정책·상태·진입 포인터를 모두 한 루트의 역할로 선언 | Core 소유와 소비 저장소 소유를 표현할 수 없음 |
| `context.py` | 하나의 `root`에서 정책·상태·규칙을 모두 찾음 | Core와 소비 저장소를 분리해 구성할 수 없음 |
| `declarations.py` | 하나의 루트를 재귀 검색해 역할 선언 하나를 요구 | 부모 저장소와 submodule의 선언이 동시에 보이면 모호해짐 |
| `integrity.py` | 하나의 루트 전체의 문서·역할·상태를 검사 | Core 자체 검사와 Host 계약 검사를 구분하지 못함 |
| `gate.py` | 하나의 루트가 코드·테스트·상태를 모두 소유한다고 가정 | 순수 Core 또는 read-only Host 중 한쪽을 제대로 표현하지 못함 |
| `test_state_contract.py` | Core 루트의 `SESSION_HANDOFF.md`를 직접 참조 | 현재 상태가 Core 필수 파일이라는 잘못된 계약을 고정함 |

### 에이전트 진입 실측이 주는 제약

- Codex에서는 Host 루트에서 시작하면 루트 `AGENTS.md`가 활성 진입점이 되고, Core 디렉터리에서 시작하면 더 가까운 Core 지침이 우선할 수 있다.
- Claude에서는 Host 루트에서 시작해도 Core 하위 파일을 읽는 시점에 Core의 `CLAUDE.md`가 활성화됐다.
- Claude의 `claudeMdExcludes`는 Host 루트 진입에서는 하위 지침 발견을 막았지만, Core 디렉터리에서 직접 시작하면 Core 지침이 다시 활성화됐다.
- 따라서 제외 설정은 절대 경계가 아니다. 순수 Core에서 `AGENTS.md`와 `CLAUDE.md`를 제거하고 소비 저장소 루트만 진입 파일을 소유해야 두 에이전트의 동작 차이에 의존하지 않는다.

---

## 3. 확정 구조

```text
Agent-Core 저장소
├─ PROJECT_RULES.md                 Core 공통 최소 정책과 Core 규칙 라우터
├─ README.md                        Core 개요와 정본·사용 안내 링크
├─ docs/CONSUMER_GUIDE.md           소비 절차의 단일 소유자
├─ docs/                            Core 계약 정본
├─ rules/                           공통 조건부 규칙
├─ src/core_check/                  공개 검증 CLI
└─ tests/                           Core 자체·소비 계약 회귀 검사

Maintainer 또는 Host 저장소
├─ AGENTS.md                        Codex용 루트 포인터
├─ CLAUDE.md                        Claude용 루트 포인터
├─ PROJECT_RULES.md                 소비 저장소 정책·도메인 route·소비 계약 선언
├─ SESSION_HANDOFF.md               소비 저장소 현재 상태 정본
├─ rules/                           소비 저장소 전용 도메인 규칙 (필요할 때만)
├─ .gitmodules                      Core URL과 submodule 경로
└─ core/                            Agent-Core 전체 submodule 예시 경로
```

`core/`는 예시 경로이며 공개 계약에 고정하지 않는다. 실제 상대 경로는 소비 저장소의 계약 선언이 소유한다.

---

## 4. Core가 제공하는 계약

### 4.1 공통 정책과 규칙

- `PROJECT_RULES.md`는 모든 소비 저장소에 적용되는 최소 안전·승인·검증 정책과 Core 규칙 route만 소유한다.
- Core 정책은 특정 Host 이름, 절대경로, 현재 상태, Deploy Key 위치를 알지 않는다.
- `rules/*.md`는 도메인 중립 절차만 소유한다.
- 소비 저장소 정책은 Core 정책을 약화하거나 대체하지 않고 프로젝트별 조건과 route만 추가한다.

### 4.2 계약·안내 문서

- `docs/CHARTER.md`: Core 목적·보장·비보장
- `docs/KERNEL_SCOPE.md`: Core 포함·제외 판정
- `docs/ARCHITECTURE.md`: Core 내부 계층과 소비 경계
- `docs/INFORMATION_ARCHITECTURE.md`: Core 및 소비 계약의 기계 판독 역할
- `docs/AGENT_ENTRY.md`: 소비 저장소 진입 파일 계약
- `docs/COMPATIBILITY.md`: 버전·런타임·공개 계약 세대
- `docs/VERIFICATION.md`: 검증 수준과 결과 판정
- `docs/CONSUMER_GUIDE.md`: 최초 연결부터 갱신·검증·복구까지의 사용 절차

루트 `README.md`는 개요와 링크만 제공한다. 실제 소비 명령과 절차는 `docs/CONSUMER_GUIDE.md`만 소유한다.

### 4.3 검증 도구

공개 명령 이름과 종료 상태는 유지한다.

| 명령 | Core만 지정 | 소비 저장소 지정 | 책임 |
|---|---|---|---|
| `verify` | 가능 | 가능 | 지정된 범위의 구조·무결성 검사 |
| `context` | 불가 | 필수 | Core 정책, 소비 정책·상태, 선택된 규칙의 결정론적 시작 문맥 구성 |
| `gate` | 가능 | 가능 | preflight, 무결성, 회귀, 문맥, 무부작용을 범위에 맞게 통합 판정 |

종료 상태는 계속 다음 의미를 갖는다.

| 코드 | 의미 |
|---:|---|
| `0` | 실행한 모든 필수 검사가 통과 |
| `1` | 하나 이상의 필수 검사에서 위반 발견 |
| `2` | 계약 누락·잘못된 경로·파싱 실패 등으로 검사 수행 자체가 불가능 |

`not_run`은 실패이며 `not_applicable`만 이유가 있을 때 비실패다.

---

## 5. 소비 저장소가 제공하는 계약

### 5.1 필수 파일과 소유 책임

| 파일·Git 객체 | 소유 내용 |
|---|---|
| `AGENTS.md` | Core 정책 → 소비 정책 → 현재 상태로 가는 Codex 포인터 |
| `CLAUDE.md` | 같은 세 문서로 가는 Claude 포인터 |
| `PROJECT_RULES.md` | 프로젝트 정책, 도메인 route, 소비 계약 선언 |
| `SESSION_HANDOFF.md` | 현재 단계·직전 게이트·승인·차단·위험·첫 다음 행동 |
| `rules/` | 프로젝트에만 필요한 조건부 규칙. 없으면 만들지 않음 |
| `.gitmodules` | Core 원격 URL과 상대 submodule 경로 |
| submodule gitlink | 소비 저장소가 고정한 정확한 Core commit SHA |

Core revision을 별도 문서나 JSON 필드에 복제하지 않는다. submodule gitlink가 유일한 버전 포인터다.

### 5.2 소비 계약 선언

소비 저장소의 `PROJECT_RULES.md`에는 다음 형태의 선언이 정확히 하나 존재한다.

<!-- agent-core-consumer:v1 -->
```json
{
  "contract_version": 2,
  "consumer_role": "host",
  "core_path": "core",
  "state": "SESSION_HANDOFF.md",
  "entry_pointers": {
    "codex": "AGENTS.md",
    "claude": "CLAUDE.md"
  },
  "rule_roots": ["rules"],
  "protected_paths": []
}
```
<!-- /agent-core-consumer:v1 -->

이 블록이 소비 저장소 계약의 기계 판독 정본이다. Core 저장소 안의 안내서가 같은 예시를 제공하더라도 검사기는 소비 저장소의 선언된 정책 파일만 읽으므로 Core 문서 예시를 실제 소비 선언으로 오인하지 않는다.

| 필드 | 제약 |
|---|---|
| `contract_version` | Core의 공개 `contract_version`과 정확히 같아야 함 |
| `consumer_role` | `maintainer` 또는 `host` |
| `core_path` | 소비 저장소 안쪽의 상대경로이며 실제 submodule 경로와 일치 |
| `state` | 소비 저장소 안쪽의 상태 정본 상대경로 |
| `entry_pointers` | 지원하는 Codex·Claude 루트 포인터 경로 |
| `rule_roots` | 소비 저장소 안쪽의 도메인 규칙 디렉터리 목록. 필요 없으면 빈 배열 |
| `protected_paths` | 열거·읽기 없이 경계 판정에만 사용하는 소비 저장소 상대경로 목록 |

모든 선언 경로는 절대경로와 `..` 탈출을 거부한다. `protected_paths`는 존재 여부 확인을 위해 열거하거나 읽지 않는다.

### 5.3 Maintainer와 Host의 차이

| 항목 | Maintainer | 일반 Host |
|---|---|---|
| `consumer_role` | `maintainer` | `host` |
| Core fetch | 허용 | 허용 |
| Core 수정 | 사용자 승인 후 Maintainer 작업으로만 허용 | 금지. 변경이 필요하면 Maintainer로 이관 |
| Core push 자격 | 쓰기 가능한 Core Deploy Key | 읽기 전용 Core Deploy Key |
| Core commit 포인터 갱신 | 검증된 Core commit 뒤 갱신 | 승인된 Core release를 선택해 갱신 |

모델 지침은 권한 경계가 아니다. push 차단은 GitHub Deploy Key가, clone별 키 선택은 로컬 Git `core.sshCommand`가 담당한다.

---

## 6. 에이전트 진입과 권위

### 6.1 시작 문맥

소비 저장소에서 필수 시작 문맥은 다음 세 문서다.

1. Core submodule의 `PROJECT_RULES.md`
2. 소비 저장소 루트의 `PROJECT_RULES.md`
3. 소비 저장소가 선언한 현재 상태 문서

그 뒤 현재 행동에 일치한 Core 규칙과 소비 저장소 규칙만 선택한다. 계약·설계·실패 진단 문서는 기본 문맥에 넣지 않는다.

### 6.2 권위와 충돌 처리

1. 최신 사용자 지시
2. Core 공통 정책
3. 소비 저장소 정책
4. 현재 행동에 route된 Core·소비 저장소 규칙

소비 저장소 정책은 Core의 승인·보호·검증 경계를 완화할 수 없고 프로젝트별로 더 구체적이거나 더 강한 제한만 추가한다. 같은 계층의 route가 충돌하면 진행하지 않고 충돌한 소유자를 보고한다.

### 6.3 Codex와 Claude

- 두 에이전트의 루트 포인터는 같은 세 문서와 같은 읽기 순서를 가리켜야 한다.
- Core submodule에는 `AGENTS.md`와 `CLAUDE.md`를 두지 않는다.
- 따라서 Host 루트, Core 하위 경로 어느 곳에서 세션을 시작해도 Core 내부의 별도 자동 지침이 Host 진입을 덮지 않는다.
- 실제 동등성은 단계 5에서 두 에이전트의 새 비영속 세션으로 다시 검증한다.

---

## 7. CLI 공개 계약 v2

### 7.1 루트 인자

| 인자 | 의미 |
|---|---|
| `--core-root PATH` | Core 자체 검증 대상. 생략 시 실행 중인 `core_check` 패키지에서 Core 루트를 결정 |
| `--consumer-root PATH` | Maintainer 또는 Host 저장소 루트. 소비 계약에서 `core_path`를 읽어 실행 Core와 대조 |
| `--root PATH` | v2 동안만 유지하는 `--core-root`의 deprecated alias. 둘을 동시에 지정하면 종료 2 |

Core는 소비 저장소 이름이나 절대경로를 저장하지 않는다. 실행할 때 전달받은 `--consumer-root`와 그 루트의 상대경로 선언만 사용한다.

### 7.2 목표 호출 형태

Core 자체:

```powershell
python -B -m core_check --core-root <CORE_ROOT> verify
python -B -m core_check --core-root <CORE_ROOT> gate
```

Maintainer·Host:

```powershell
python -B -m core_check --consumer-root <CONSUMER_ROOT> context
python -B -m core_check --consumer-root <CONSUMER_ROOT> gate
```

실행을 위한 `PYTHONPATH` 설정과 submodule 명령은 `docs/CONSUMER_GUIDE.md`가 소유한다.

### 7.3 결과 구조

모든 성공 결과에는 `ok`와 `contract_version`을 포함한다.

- `verify`: `ok`, `contract_version`, `scope`, `ran`, `skipped`, `findings`
- `context`: `ok`, `contract_version`, `required`, `optional`, `excluded`, `chars`, `digest`
- `gate`: `ok`, `contract_version`, `failed_step`, `steps`

Core와 소비 저장소에 같은 상대경로가 있을 수 있으므로 문서 참조는 문자열 하나가 아니라 다음 구조를 사용한다.

```json
{"scope": "core", "path": "PROJECT_RULES.md"}
```

허용 `scope`는 `core`, `consumer` 두 개다. 오류 결과는 기존처럼 `ok: false`, `error`, `kind`를 포함하며 예상하지 못한 오류만 `unexpected: true`를 추가한다. 절대경로와 자격 증명 정보는 결과에 출력하지 않는다.

---

## 8. 검증 계약

### 8.1 Core 자체 검사

- Core 역할 선언·호환성 선언 유일성
- Markdown 링크, JSON, Python AST, UTF-8·줄바꿈
- Core 규칙 route 유일성
- 모듈 계층·import 방향·순환
- 코드의 문서명 하드코딩 금지
- 전체 회귀 테스트
- 실행 전후 Core tree digest 동일

Core 자체 검사는 소비 저장소 상태가 없어도 통과해야 한다.

### 8.2 소비 저장소 검사

- 소비 계약 선언의 유일성·필수 필드·계약 버전
- 선언된 모든 경로가 소비 저장소 안쪽의 상대경로인지 확인
- `core_path`와 실제 submodule 경로·실행 Core가 일치
- 루트 진입 포인터가 같은 Core 정책·소비 정책·상태를 같은 순서로 가리킴
- 소비 정책의 route가 Core와 소비 scope를 구분해 해석됨
- 상태 문서 계약과 크기 예산
- 보호 경로를 읽거나 열거하지 않고 경계만 판정
- 실행 전후 Core와 소비 저장소 tree digest 모두 동일

### 8.3 순회 경계

- Core 검사는 Core 루트 밖으로 나가지 않는다.
- 소비 저장소 검사는 선언된 `core_path` subtree를 부모 문서 재귀 검사에서 제외한다.
- 소비 계약은 고정된 소비 정책 파일 한 개에서만 읽으며 부모 트리 전체에서 선언을 검색하지 않는다.
- 이 경계로 부모와 submodule에 같은 이름의 문서·route 선언이 있어도 중복으로 오판하지 않는다.

---

## 9. 호환성 판정과 이전 절차

### 9.1 판정

이번 변경은 비호환이다.

- 문서 역할 선언의 의미와 schema가 바뀐다.
- 상태와 진입 포인터가 Core 루트에서 소비 저장소 루트로 이동한다.
- CLI가 단일 `root`에서 Core·consumer 이중 root로 바뀐다.
- `context` 결과의 경로가 scope가 있는 객체로 바뀐다.

따라서 단계 3 후보의 목표 버전은 다음과 같다.

| 선언 | 현재 | 목표 |
|---|---:|---:|
| `core_version` | `0.1.0` | `0.2.0` |
| `contract_version` | `1` | `2` |
| `python_min` | `3.10` | `3.10` 유지 |
| 필수 외부 의존성 | 없음 | 없음 유지 |

### 9.2 v1에서 v2로 이전

1. 부모 Maintainer 또는 Host 저장소를 준비한다.
2. Core를 submodule로 연결하고 gitlink로 검증된 Core commit을 고정한다.
3. 부모 루트에 `AGENTS.md`, `CLAUDE.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`를 둔다.
4. 부모 정책에 `agent-core-consumer:v1` 선언과 프로젝트 route·보호 경계를 둔다.
5. Core 내부의 상태·진입 파일에 의존하던 참조를 부모 파일로 옮긴다.
6. 기존 `--root` 호출을 `--core-root` 또는 `--consumer-root` 호출로 바꾼다.
7. 소비 통합 gate를 통과한 뒤에만 부모 gitlink를 갱신한다.

`--root` alias는 v2 동안만 복구 수단으로 남기며 제거는 다음 계약 세대의 별도 승인 대상이다.

---

## 10. 단계 3의 정확한 파일별 변경안

### 10.1 Core에서 제거하거나 외부로 이동

| 파일 | 처분 | 흡수 대상 |
|---|---|---|
| `AGENTS.md` | Core 후보에서 제거 | 소비 저장소 루트 포인터 계약은 `docs/AGENT_ENTRY.md` |
| `CLAUDE.md` | Core 후보에서 제거 | 소비 저장소 루트 포인터 계약은 `docs/AGENT_ENTRY.md` |
| `SESSION_HANDOFF.md` | Maintainer 저장소가 소유 | 상태 내용 계약은 `rules/handoff.md` |
| `docs/COMPLETION.md` | Maintainer 저장소가 소유 | 현재 검증 기준은 `docs/VERIFICATION.md`, 이력은 Git |
| `docs/HOST_ENTRY_CONDITIONS.md` | 확정된 내용을 관련 정본에 흡수 후 제거 | 진입은 `docs/AGENT_ENTRY.md`, 소비 절차는 `docs/CONSUMER_GUIDE.md`, 공개 계약은 이 단계 설계 |

### 10.2 Core에서 변경

| 파일 | 변경 책임 |
|---|---|
| `PROJECT_RULES.md` | 로컬 상태 강제 읽기 제거, Core 최소 정책과 소비 정책의 권위·라우팅 경계 정의 |
| `README.md` | 동적 현재 상태 제거, Core 개요와 `CONSUMER_GUIDE` 링크만 유지 |
| `docs/AGENT_ENTRY.md` | 소비 저장소 루트 진입 계약과 Core 내부 진입 파일 부재를 정본화 |
| `docs/ARCHITECTURE.md` | Core·consumer 두 scope와 L5 이중-root 의존 경계 반영 |
| `docs/CHARTER.md` | 구성된 소비 저장소에서의 G1·G2 보장 범위 반영 |
| `docs/COMPATIBILITY.md` | Core 0.2.0, contract 2, CLI v2와 이전 절차 반영 |
| `docs/INFORMATION_ARCHITECTURE.md` | `core-document-roles:v2`, Core·consumer 소유 구조와 새 안내서 배치 반영 |
| `docs/KERNEL_SCOPE.md` | 진입·상태는 consumer 제공 계약, submodule 소비는 현재 공개 범위로 재분류 |
| `docs/VERIFICATION.md` | Core 자체와 consumer 통합 검증 수준 분리, 동적 완료 현황 제거 |
| `docs/EXPERIMENTAL.md` | 현재 게이트를 Core 내부 상태 문서가 소유한다는 과거 표현 제거 |
| `rules/core-change-control.md` | 선언된 `core_path`, maintainer/host 역할과 권한 차이 반영 |
| `rules/document-work.md` | 시작 문맥을 Core 정책·소비 정책·소비 상태의 세 문서로 갱신 |
| `rules/handoff.md` | 상태 정본을 Core 고정 경로가 아니라 consumer 선언 경로로 조회 |
| `rules/rule-governance.md` | Core 정책 이후 소비 정책·상태를 읽는 새 라우팅 순서 반영 |
| `src/core_check/cli.py` | `--core-root`, `--consumer-root`, deprecated `--root`와 v2 결과 연결 |
| `src/core_check/context.py` | scope가 있는 Core 정책·consumer 정책·state·route 문맥 구성 |
| `src/core_check/declarations.py` | Core 역할 v2와 consumer 계약 선언 파서 분리 |
| `src/core_check/gate.py` | Core-only와 consumer 통합 gate 분리, 양쪽 무부작용 검사 |
| `src/core_check/integrity.py` | Core 검사와 consumer 검사 scope 분리, submodule subtree 중복 순회 방지 |
| `tests/fixtures/rule-routing-intents-v1.json` | router 참조를 Core scope 계약에 맞게 갱신 |
| `tests/test_integrity.py` | 이중-root 정상·결함 주입·CLI·무부작용 회귀 |
| `tests/test_rule_routing.py` | Core·consumer route scope와 exact-set 검증 |
| `tests/test_state_contract.py` | 실제 Core 상태가 아니라 임시 consumer fixture의 상태 계약 검증 |

### 10.3 Core에 신규 생성

| 파일 | 단일 책임 |
|---|---|
| `docs/CONSUMER_GUIDE.md` | Core 연결, clone, update, gitlink 고정, 검증, 권한 구분, 복구 절차 |

### 10.4 변경하지 않음

단계 1에서 `Core 유지·변경 없음`으로 판정한 파일 중 3개에서 과거 단일-root 시작 문맥 표현이 발견됐다. 사용자가 권장안 진행을 승인해 `docs/EXPERIMENTAL.md`, `rules/document-work.md`, `rules/rule-governance.md`를 §10.2에 추가했다. 나머지 12개 파일은 그대로 유지한다. 이후 다른 변경 필요성이 발견되면 범위를 임의로 넓히지 않고 사용자에게 새 범위로 보고한다.

---

## 11. 단계 2 성공 게이트 판정

| 성공 조건 | 판정 | 근거 |
|---|---|---|
| Host가 Core submodule 내부에서 갱신해야 하는 파일 0개 | `pass` | 상태·진입·도메인 정책·보호 경계를 모두 소비 저장소가 소유하도록 설계 |
| Core에 특정 Maintainer·Host 이름·절대경로 하드코딩 0개 | `pass` | 실행 시 consumer root와 상대경로 선언만 사용 |
| Core 개발 상태와 Host 현재 상태 정본 분리 | `pass` | `SESSION_HANDOFF.md`를 소비 저장소 소유로 확정 |
| Codex·Claude 진입과 우선순위 설명 | `pass` | Core 내부 자동 진입 파일 제거와 공통 3문서 순서 확정 |
| 비호환 여부와 이전 방법 판정 | `pass` | contract 2, Core 0.2.0, v1→v2 이전 절차 확정 |
| 소비 안내서의 책임·목차·명령 계약 확정 | `pass` | §4.2, §5, §7, §9에서 단일 책임과 호출 형태 확정 |
| README와 안내서 사이 절차 정본 중복 없음 | `pass` | README는 개요·링크, 안내서는 절차만 소유 |
| 정확한 파일별 변경안 준비 | `pass` | §10에 제거·변경·신규·불변 경로 구분 |
| 실제 Core 구현·회귀 검증 | `not_run` | 단계 3·4 범위이므로 이번 단계에서 실행하지 않음 |
| 실제 Host submodule 검증 | `not_run` | 단계 5 이후 범위 |

단계 2의 설계 게이트는 완료 후보지만, 실제 구현 성공을 뜻하지 않는다. 사용자가 이 계약을 확인한 뒤에만 단계 3을 시작한다.

---

## 12. 단계 3 진입 조건

1. 사용자가 이 문서의 저장소 경계, 소비 계약 선언, CLI v2, `contract_version` 2 판정을 확인한다.
2. 구현 위치는 `D:\AI Agent\Sandbox\Agent-Core-Redesign`으로 제한한다.
3. 기존 `D:\AI Agent\Agent Core`는 읽기 기준선으로만 사용하고 수정하지 않는다.
4. 실제 변경 경로는 §10 목록과 정확히 대조한다.
5. 범위를 벗어나는 변경이 필요하면 구현을 멈추고 사용자에게 보고한다.
6. 직접 검증을 통과한 결과를 로컬 후보 commit으로 만들고 commit SHA로 보고한다.
7. 작업 도중 push하지 않으며, 원격 반영은 사용자의 별도 지시 전까지 금지한다.
