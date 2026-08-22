# Agent Core 순수화 및 분리 구조 단계 설계

- 목적: 현재 `Agent-Core`를 외부 Maintainer와 Host가 submodule로 소비할 수 있는 순수 Core로 재정의하고, 그 이후 Maintainer·Host 저장소를 안전하게 구성하기 위한 실행 순서와 성공 조건을 고정한다.
- 읽는 시점: Core 순수화 작업을 시작하거나 재개할 때, Maintainer·Host 저장소 생성 가능 여부를 판단할 때, 각 단계의 완료를 판정할 때.
- 책임: 사용자가 목표·범위·Core 변경·외부 쓰기·자격증명 변경을 승인하고, 작업 Agent가 단계 순서·최소 변경·검증 근거를 유지한다.
- 상태: 사용자 검토용 활성 설계 후보. 이 문서 자체는 Core 변경, 저장소 생성, commit 또는 push를 승인하지 않는다.
- 관련 권위: 최신 사용자 지시, `D:\AI Agent\Agent Core\PROJECT_RULES.md`, `docs/CHARTER.md`, `docs/INFORMATION_ARCHITECTURE.md`, `docs/COMPLETION.md`, `docs/HOST_ENTRY_CONDITIONS.md`, `docs/COMPATIBILITY.md`.
- 배치와 종료 조건: 이 문서는 `D:\AI Agent\Sandbox`의 작업 근거문서다. 전체 구조가 실제 Host 2개에서 검증되면 검증된 계약만 각 저장소의 정본에 흡수하고, 이 문서는 역사적 설계 snapshot으로 종료한다.

---

## 1. 작업 의도

현재 `Agent-Core`는 독립 저장소 안에서 정책, 진입 파일, 현재 상태, 규칙, 검증 도구를 모두 소유하는 구조다. 이 구조는 독립 Core 자체 검증에는 성공했지만, 최종 사용 방식인 다음 구조는 아직 보장하지 않는다.

```text
Agent-Core                  순수 Core 저장소
    ↑ write submodule
Agent-Core-Maintainer       Core 공식 변경 주체

Agent-Core
    ↑ read-only submodule
각 Host 저장소              Core 소비 주체
```

최종 목적은 Core와 Maintainer를 같은 저장소에 합치는 것이 아니다. `Agent-Core` 전체를 재사용 가능한 Core로 만들고, 별도 Maintainer와 각 Host가 동일한 Core 저장소를 서로 다른 권한으로 submodule 연결하는 것이다.

따라서 이 작업은 Maintainer 저장소 생성부터 시작하지 않는다. 먼저 현재 Core가 외부 소비 환경에서 상태·정책·진입 책임을 잘못 소유하지 않는지 판정하고 바로잡아야 한다.

---

## 2. 확정 요구사항

### 2.1 저장소 구조

1. `HughKim87/Agent-Core`는 순수 Core만 소유한다.
2. `Agent-Core-Maintainer`는 별도 저장소로 만든다.
3. 각 실제 Host도 별도 저장소다.
4. Maintainer와 Host는 `Agent-Core` 저장소 전체를 submodule로 연결한다.
5. 배포 전용 하위 폴더, 모양이 다른 배포 브랜치, Core·Maintainer 통합 저장소를 만들지 않는다.
6. Core는 별도의 소비자용 사용 안내서 `docs/CONSUMER_GUIDE.md`를 제공하고, 루트 `README.md`는 이 문서를 링크한다.

### 2.2 권한 구조

| 소비자 | Core fetch/update | Core push | 인증 방식 |
|---|---:|---:|---|
| Maintainer | 허용 | 허용 | 쓰기 가능한 Core Deploy Key |
| 일반 Host | 허용 | 거부 | 읽기 전용 Core Deploy Key |

- 같은 GitHub 계정과 같은 PC를 사용하더라도 clone별 로컬 `core.sshCommand`에 서로 다른 키를 지정한다.
- 개인키는 저장소에 넣지 않는다.
- 실제 키 저장 위치는 `D:\AI Agent\Sandbox\SSH Key`다.

### 2.3 작업 위치

- 모든 신규 로컬 작업은 `D:\AI Agent\Sandbox` 아래에서 수행한다.
- 기존 `D:\AI Agent\Agent Core` 작업 트리를 직접 실험장으로 사용하지 않는다.
- Core 후보는 Sandbox의 격리 clone에서 만든다.

### 2.4 완료 주장 제한

- 합성 fixture 통과를 실제 Host 검증이라고 하지 않는다.
- 첫 Host 하나만으로 범용 Host 연결 완료를 주장하지 않는다.
- 필수 검사가 `not_run`이면 완료로 판정하지 않는다.
- Core 변경, commit, push, 원격 저장소 생성, Deploy Key 등록은 각각 해당 승인 경계를 지킨다.
- 각 구현 단계는 검증한 로컬 후보 commit 상태로 보고한다.
- 작업 도중 push하지 않는다. push는 사용자가 정확한 commit을 확인한 뒤 별도로 지시한 경우에만 가능하다.

---

## 3. 현재 구현에서 확인된 근거

### 3.1 현재 Core가 독립 프로젝트로 설계돼 있다는 근거

| 근거 문서 | 현재 정의 | 후속 작업에서 확인할 문제 |
|---|---|---|
| `docs/CHARTER.md` | Host 도메인 프로젝트는 독립 Core 밖의 후속 범위 | 최종 소비 구조가 현재 Core 보장에 아직 포함되지 않음 |
| `docs/INFORMATION_ARCHITECTURE.md` | 저장소 루트가 곧 Core이며 `AGENTS.md`, `CLAUDE.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`가 루트 정본 | 외부 Host가 read-only submodule로 소비할 때 상태·진입 소유권이 맞는지 재판정 필요 |
| `docs/COMPLETION.md` | 독립 Core 1차 완료, 실제 Host 미검증 | 독립 완료와 소비 완료를 구분해야 함 |
| `docs/HOST_ENTRY_CONDITIONS.md` | Host 연결 방식과 진입 파일 처리가 미결이며 실제 Host 2개 검증 요구 | Core 변경보다 먼저 소비 계약을 확정해야 함 |
| `docs/COMPATIBILITY.md` | 공개 경로 제거·개명과 규칙 소유자 변경은 비호환 변경 | 순수화 과정에서 버전·이전 절차 필요 가능성 |

### 3.2 이번 세션에서 직접 검증된 사실

1. 같은 PC와 같은 GitHub 계정에서도 clone별 Deploy Key를 사용해 권한을 분리할 수 있다.
2. 쓰기 Key clone은 Core 원격 push에 성공했다.
3. 읽기 전용 Key clone은 fetch에 성공하고 push는 거부됐다.
4. 같은 결과가 합성 submodule 구조에서도 재현됐다.
5. Codex는 Host 루트에서 시작하면 하위 `core/AGENTS.md`를 시작 지침으로 읽지 않고, `core`에서 직접 시작하면 읽는다.
6. Claude는 Host 루트에서 시작해도 Core 파일을 읽을 때 하위 `core/CLAUDE.md`를 지연 로드한다.

위 결과는 인증과 지침 로딩 메커니즘의 증거다. 실제 Core 정책과 실제 Host 상태가 함께 정상 작동한다는 증거는 아니다.

### 3.3 아직 검증하지 않은 핵심

- 현재 Core의 어떤 파일이 Maintainer로 이동해야 하는가.
- Host가 자신의 현재 상태를 Core 변경 없이 유지할 수 있는가.
- Core 정책이 Host의 루트 정책·도메인 규칙과 실제로 결합되는가.
- Core 검증기가 submodule 위치와 Host 제공 선언을 처리하는가.
- 실제 서로 다른 Host 2개가 Core 변경 없이 사용할 수 있는가.

---

## 4. 작업 원칙

1. **Core 먼저:** Core 순수화 게이트 전에는 Maintainer·Host 저장소를 만들지 않는다.
2. **소유권 먼저:** 해결책보다 정책·상태·진입·검증의 소유자를 먼저 확정한다.
3. **전체 Core 소비:** Host는 `Agent-Core` 전체 저장소를 submodule로 사용한다.
4. **Host 상태 분리:** Host의 현재 상태와 도메인 정보는 Host 저장소가 소유한다.
5. **Core 불변:** 일반 Host 작업은 Core 작업 트리를 변경하지 않아야 한다.
6. **권한과 지침 분리:** Agent 지침은 행동 안내이고, 원격 쓰기 차단은 Deploy Key가 담당한다.
7. **검증 수준 정직성:** 구조 검사, 합성 fixture, 실제 Host 검증을 서로 대체하지 않는다.
8. **승인 분리:** 로컬 후보 작성, commit, push, 자격증명 변경, 원격 생성의 승인을 합치지 않는다.

---

## 5. 단계별 설계

## 단계 0 — 요구사항 기준선 확정

### 작업 목표

Core·Maintainer·Host의 최종 관계와 금지 방향을 이후 모든 판단의 기준으로 고정한다.

### 작업 의도

중간에 검토했던 통합 저장소, 배포 하위 폴더, 별도 배포 브랜치 같은 후보를 최종안으로 다시 오인하지 않게 한다. 이후 파일 분류와 설계 변경은 이 기준선에 직접 대응해야 한다.

### 주요 작업

- §2의 확정 요구사항을 현재 작업 계약으로 사용한다.
- 다음을 명시적 제외 범위로 둔다.
  - Core·Maintainer 통합 저장소
  - 모양이 다른 배포 브랜치
  - Host별 Core 복사본
  - Core 정리 전 Maintainer·Host 생성
  - 합성 검증을 실제 Host 검증으로 확대 보고

### 성공 게이트

- [ ] `Agent-Core`, Maintainer, Host의 책임이 각각 한 문장으로 설명된다.
- [ ] 모든 후속 단계가 확정 요구사항 중 하나 이상에 대응한다.
- [ ] 금지된 구조가 계획에 포함되지 않는다.
- [ ] 사용자만 결정할 변경·외부·자격증명 게이트가 분리돼 있다.

---

## 단계 1 — 현재 Agent-Core 전 파일 소유권 분류

### 작업 목표

현재 추적 파일 전체를 Core 필수, Maintainer 소유, Host 제공 계약, 제거 후보 중 하나로 분류한다.

### 작업 의도

현재 저장소는 독립 Core 운영에 필요한 파일과 외부 소비자가 사용할 공통 Core가 같은 루트에 있다. 파일을 옮기기 전에 무엇이 재사용 가능한 Core이고 무엇이 특정 저장소의 현재 상태인지 분리해야 한다.

### 주요 작업

- 모든 추적 파일을 다음 기준으로 판정한다.
  1. 도메인·특정 저장소 없이 재사용되는가.
  2. Host가 read-only submodule 안에서 수정할 필요가 없는가.
  3. Core 보장 중 하나를 직접 제공하거나 검증하는가.
  4. 다른 저장소가 소유해야 할 현재 상태나 운영 정보가 아닌가.
  5. 실제 소비자와 검사가 존재하는가.
- 우선 감사 대상:
  - `AGENTS.md`, `CLAUDE.md`
  - `PROJECT_RULES.md`, `SESSION_HANDOFF.md`
  - `README.md`
  - `docs/COMPLETION.md`, `docs/HOST_ENTRY_CONDITIONS.md`, `docs/AGENT_ENTRY.md`
  - `rules/handoff.md`, `rules/core-change-control.md`
  - `src/core_check/context.py`, 선언·게이트 관련 모듈
- 각 파일에 `유지`, `이동`, `변경`, `제거 후보` 처분을 부여한다.
- 현재 파일만으로 충족되지 않는 신규 Core 필수 파일 후보를 식별한다.
- 신규 필수 파일 후보 `docs/CONSUMER_GUIDE.md`의 단일 책임을 다음과 같이 정의한다.
  - Maintainer와 일반 Host의 Core 연결 방식 차이
  - submodule 최초 설정, clone, update, 버전 고정 절차
  - 소비 저장소 루트가 제공해야 하는 진입·정책·상태 파일
  - Core 검증 명령과 결과 해석
  - 읽기 전용 Host의 금지 행동과 키 비추적 원칙
  - 실패 복구와 키 폐기 확인 지점

### 성공 게이트

- [ ] 모든 추적 파일에 소유자가 정확히 하나 배정된다.
- [ ] 판정 보류 또는 복수 소유 파일이 0개다.
- [ ] 각 이동·변경·제거 후보에 구체적인 이유와 영향 소비자가 기록된다.
- [ ] Core 공개 계약 변경 가능성이 별도로 표시된다.
- [ ] 현재 파일로 충족되지 않는 신규 필수 문서 후보와 단일 책임이 기록된다.
- [ ] 실제 파일 변경은 아직 0건이다.

---

## 단계 2 — 순수 Core 공개 계약과 Host 제공 계약 설계

> 상세 단계 설계와 판정: [Agent-Core 단계 2 — 순수 Core 공개 계약 설계](Agent-Core_단계2_순수_Core_공개계약_설계.md)

### 작업 목표

Core가 제공하는 불변 인터페이스와 Maintainer·Host가 자신의 루트에서 제공해야 하는 가변 정보를 분리한다.

### 작업 의도

read-only submodule은 공통 규칙과 검증 기능을 제공해야 하지만, Host의 현재 상태·도메인 규칙·보호 경로를 소유할 수 없다. 이 경계가 없으면 Host가 Core를 수정하거나 Core의 개발 상태를 자기 상태로 오인하게 된다.

### 주요 작업

- Core 제공 계약 정의:
  - 공통 규칙 소유자
  - 규칙 선택 인터페이스
  - 검증 CLI와 종료 상태
  - 결과 구조
  - 호환성·버전 선언
  - 소비자용 사용 안내서 `docs/CONSUMER_GUIDE.md`
- 소비 저장소 제공 계약 정의:
  - 루트 Agent 진입
  - 현재 상태
  - 도메인 규칙
  - 보호 경로 선언
  - Core submodule 경로와 버전 포인터
- Codex와 Claude의 실제 진입 차이를 반영한다.
- Core가 특정 Host 이름·절대경로 없이 Host 제공 계약을 읽는 방식을 정한다.
- 공개 파일 이동·개명 시 호환성 버전과 이전 절차를 설계한다.
- 루트 `README.md`는 Core 개요와 안내서 링크만, `docs/CONSUMER_GUIDE.md`는 실제 소비 절차만 소유하도록 중복 없는 경계를 정한다.

### 성공 게이트

- [ ] Host가 Core submodule 내부에서 갱신해야 하는 파일이 0개다.
- [ ] Core가 특정 Maintainer·Host 이름이나 경로를 하드코딩하지 않는다.
- [ ] Core 개발 상태와 Host 현재 상태의 정본이 분리된다.
- [ ] Codex·Claude 각각의 진입 경로와 정책 우선순위가 설명된다.
- [ ] 비호환 변경 여부와 이전 방법이 판정된다.
- [ ] 이전 대화를 모르는 Maintainer·Host가 안내서만으로 설정·갱신·검증 절차를 재현할 수 있게 목차와 명령 계약이 확정된다.
- [ ] `README.md`와 `docs/CONSUMER_GUIDE.md` 사이에 절차 정본 중복이 없다.
- [ ] 정확한 파일별 변경안이 사용자 승인 대상으로 준비된다.

---

## 단계 3 — Sandbox 격리 clone에서 Core 순수화 후보 구현

### 작업 목표

승인된 설계를 실제 원본과 분리된 Core clone에 최소 변경으로 구현한다.

### 작업 의도

현재 검증된 Core를 직접 손상시키지 않고, 새 소비 계약이 전체 게이트를 통과하는지 확인할 후보를 만든다.

### 작업 위치

```text
D:\AI Agent\Sandbox\Agent-Core-Redesign
```

### 주요 작업

- 실제 Core 원격의 검증된 기준점을 clone한다.
- 단계 1·2에서 승인된 파일만 이동·변경·제거한다.
- Core 검증기를 새 계약에 맞춘다.
- `docs/CONSUMER_GUIDE.md`를 만들고 루트 `README.md`에서 연결한다.
- 회귀 테스트와 결함 주입 테스트를 갱신한다.
- 호환성 선언과 필요한 이전 절차를 갱신한다.
- 직접 검증과 변경 범위 대조를 마친 결과를 로컬 후보 commit으로 만든다.
- 기존 `D:\AI Agent\Agent Core`는 수정하지 않는다.

### 성공 게이트

- [ ] 실제 변경 경로가 승인 목록과 정확히 일치한다.
- [ ] 원본 Core 작업 트리 변경이 0건이다.
- [ ] 특정 Host·Maintainer 이름이 Core 후보에 유입되지 않는다.
- [ ] 개인키·토큰·로컬 인증 경로가 추적되지 않는다.
- [ ] 소비자 안내서에 개인키 본문, 토큰, 사용자별 비밀 경로가 포함되지 않는다.
- [ ] 사용자 변경이나 무관한 파일을 포함하지 않는다.
- [ ] 결과가 식별 가능한 로컬 후보 commit이며 원격 push는 0건이다.

---

## 단계 4 — 순수 Core 자체 회귀·무결성 검증

### 작업 목표

순수화 후보가 기존 Core 보장을 잃지 않았는지 현재 checkout과 clean clone에서 검증한다.

### 작업 의도

소비 구조를 개선하면서 규칙 라우팅, 안전 경계, 상태 복원, 완료 판정, 재현성을 깨뜨리는 회귀를 방지한다.

### 주요 작업

- 전체 단위·회귀 테스트 실행
- 무결성·링크·문서 역할 검사
- 규칙 라우팅 구조·의미 재현
- 지원 Python 버전 검사
- Windows clean clone 게이트
- 텍스트·줄바꿈·추적 상태 검사
- 필수 의존성 0 유지 확인
- 소비자 안내서의 내부 링크, 명령, 권한 설명 검사

### 성공 게이트

- [ ] 모든 필수 검사가 `pass`다.
- [ ] 필수 검사 중 `not_run`이 0개다.
- [ ] 현재 checkout과 clean clone 결과가 같다.
- [ ] 미추적 파일에 의존한 통과가 0건이다.
- [ ] clean clone에서 소비자 안내서의 설정·갱신·검증 흐름을 그대로 재현할 수 있다.
- [ ] 기존 Core 보장 G1~G6의 도달 수준이 축소되지 않는다.

---

## 단계 5 — 읽기 전용 submodule 소비 통합 검증

### 작업 목표

동일한 Core 후보를 Maintainer 역할과 Host 역할에 submodule로 연결해 실제 책임 분리가 작동하는지 확인한다.

### 작업 의도

독립 Core 자체 통과만으로 외부 소비 가능성을 주장하지 않는다. 부모 저장소의 상태·정책·버전 포인터와 자식 Core의 불변성이 함께 유지되는지 확인한다.

### 작업 위치

```text
D:\AI Agent\Sandbox\Core-Consumer-Validation\maintainer-fixture
D:\AI Agent\Sandbox\Core-Consumer-Validation\host-fixture
```

### 주요 작업

- 두 부모 저장소에 동일 Core 후보를 submodule 연결한다.
- Maintainer 역할은 Core 변경·검증·포인터 갱신 흐름을 확인한다.
- Host 역할은 Core 읽기·실행·버전 갱신 흐름을 확인한다.
- Host 상태 변경과 Core 상태 변경을 분리한다.
- Codex·Claude 콜드 세션에서 실제 정책·상태 선택을 확인한다.
- Core 검사 실행 전후의 부작용을 비교한다.

### 성공 게이트

- [ ] Host 작업 후 Core 작업 트리 변경이 0건이다.
- [ ] Host 상태 갱신이 부모 저장소에만 발생한다.
- [ ] Maintainer와 Host가 동일 Core 계약을 소비한다.
- [ ] Codex·Claude가 Core 개발 상태를 Host 상태로 오인하지 않는다.
- [ ] Core 검사 실행 후 생성·수정 artifact가 승인 경계 밖에 생기지 않는다.
- [ ] 합성 fixture 결과는 `synthetic`으로만 표시된다.

---

## 단계 6 — 검증된 Core 후보 확정과 원격 반영

### 작업 목표

Sandbox에서 검증된 정확한 snapshot만 공식 `Agent-Core` 이력에 반영한다.

### 작업 의도

작업 트리의 우연한 상태가 아니라 clean clone에서 재현되는 commit을 복구 가능한 공식 Core 버전으로 만든다.

### 주요 작업

1. 변경 범위와 승인 목록 최종 대조
2. 후보 commit 생성
3. 후보 commit의 별도 clean clone 전체 게이트
4. 사용자에게 diff·호환성·검증 결과 보고
5. 별도 push 승인
6. `HughKim87/Agent-Core` 원격 반영

### 성공 게이트

- [ ] commit에 승인되지 않은 경로가 없다.
- [ ] 후보 commit clean clone이 전체 필수 게이트를 통과한다.
- [ ] commit 메시지의 검증 주장이 실제 실행 결과와 일치한다.
- [ ] 사용자가 정확한 원격 push를 별도로 승인한다.
- [ ] 원격 Core가 검증된 commit SHA를 가리킨다.
- [ ] 이전 검증 버전으로 복구 가능한 Git 지점이 존재한다.

---

## 단계 7 — 별도 Maintainer 저장소 구성

### 작업 목표

공식 Core를 개발하고 push할 수 있는 유일한 정상 운영 경로를 별도 Maintainer 저장소에 구성한다.

### 작업 의도

Core 개발 상태와 작업 절차를 Core 소비 계약에서 분리하면서도, Maintainer가 submodule 안에서 공식 Core를 직접 개선할 수 있게 한다.

### 대상

```text
Remote: HughKim87/Agent-Core-Maintainer
Local:  D:\AI Agent\Sandbox\Agent-Core-Maintainer
Core:   core\  → HughKim87/Agent-Core
Key:    D:\AI Agent\Sandbox\SSH Key\agent-core-maintainer
```

### 주요 작업

- 비공개 Maintainer 저장소 생성
- Maintainer 루트 진입·정책·현재 상태 구성
- Core를 `core/` submodule로 연결
- Core 저장소에 쓰기 가능한 Deploy Key 등록
- submodule clone의 로컬 `core.sshCommand`에 해당 키 지정
- Core 수정·검증·push·부모 gitlink 갱신 흐름 검증

### 성공 게이트

- [ ] Maintainer에서 Core fetch가 성공한다.
- [ ] 승인된 테스트 브랜치의 Core push가 성공한다.
- [ ] 부모 저장소가 Core commit 포인터 변경을 감지한다.
- [ ] Maintainer 현재 상태가 Core submodule 밖에 존재한다.
- [ ] 개인키와 로컬 SSH 설정이 Git에 추적되지 않는다.
- [ ] Core 자체 게이트를 Maintainer에서 실행할 수 있다.

---

## 단계 8 — 첫 일반 Host 저장소 구성과 실사용 검증

### 작업 목표

동일한 공식 Core를 읽기 전용으로 소비하는 첫 Host를 구성하고 실제 Agent 작업에서 검증한다.

### 작업 의도

합성 구조가 아니라 외부 소비자의 정책·상태·도메인 작업과 Core가 함께 작동하는지 확인한다.

### 대상

```text
Remote: HughKim87/Agent-Core-Host
Local:  D:\AI Agent\Sandbox\Agent-Core-Host
Core:   core\  → HughKim87/Agent-Core
Key:    D:\AI Agent\Sandbox\SSH Key\agent-core-host
```

### 주요 작업

- 비공개 Host 저장소 생성
- Host 루트 진입·정책·상태·보호 경계 구성
- Core를 `core/` submodule로 연결
- Core 저장소에 읽기 전용 Deploy Key 등록
- clone별 로컬 `core.sshCommand` 구성
- Core fetch/update와 push 거부 검증
- Codex·Claude 새 세션의 실제 Host 작업 검증

### 성공 게이트

- [ ] Host에서 Core clone·fetch·update가 성공한다.
- [ ] Host Key의 Core push가 거부된다.
- [ ] 금지된 원격 브랜치가 생성되지 않는다.
- [ ] 실제 Host 작업 후 Core 변경이 0건이다.
- [ ] Host의 상태·도메인 정보는 Host 저장소에만 기록된다.
- [ ] Codex·Claude가 대화 기억 없이 올바른 첫 행동을 선택한다.

---

## 단계 9 — 두 번째 실제 Host와 운영 완료 판정

### 작업 목표

서로 다른 두 번째 실제 프로젝트에서도 Core 변경 없이 동일 계약을 재사용해 범용성을 검증한다.

### 작업 의도

하나의 Pilot Host에 우연히 맞춘 결합을 범용 Core라고 오판하지 않는다.

### 주요 작업

- 첫 Host와 구조·도메인이 다른 실제 프로젝트를 선택한다.
- 동일 Core 버전을 read-only submodule로 연결한다.
- Host 고유 상태·규칙·보호 경계를 제공한다.
- 실제 작업과 Core 게이트를 실행한다.
- 두 Host의 공통 변경 요구를 비교한다.

### 성공 게이트

- [ ] 두 번째 Host에서도 Core 변경 없이 작업이 가능하다.
- [ ] 두 Host 모두 Core 작업 트리 변경이 0건이다.
- [ ] 두 Host 모두 Core 원격 push가 거부된다.
- [ ] Maintainer만 Core push에 성공한다.
- [ ] Host별 상태와 보호 경계가 서로 독립적이다.
- [ ] 두 Host를 위해 Core에 특정 도메인 분기가 추가되지 않는다.
- [ ] 모든 필수 게이트가 통과한 경우에만 전체 구조 완료를 선언한다.

---

## 6. 단계 전환과 승인 게이트

| 전환 | 필요한 사용자 결정 |
|---|---|
| 단계 1 → 2 | 파일 소유권 분류와 문제 정의 확인 |
| 단계 2 → 3 | 정확한 Core 변경 경로·이동·제거 승인 |
| 단계 5 → 6 | 후보 Core가 요구사항을 충족한다는 결과 확인 |
| 단계 6 commit | Core commit 지시 또는 위임 |
| 단계 6 push | 정확한 Core 원격 push 승인 |
| 단계 7 | Maintainer 원격 생성과 쓰기 Deploy Key 등록 승인 |
| 단계 8 | Host 원격 생성과 읽기 Deploy Key 등록 승인 |
| 단계 9 | 두 번째 실제 Host 대상과 접근 범위 승인 |

한 단계의 필수 게이트가 `fail` 또는 `not_run`이면 다음 단계로 넘어가지 않는다.

---

## 7. 복구 원칙

- Core 후보 구현은 Sandbox clone에서만 수행한다.
- 단계 완료 이력은 Git commit으로 남기고 저장소 내부 백업 사본을 만들지 않는다.
- 원격 반영 전에는 항상 후보 commit clean clone을 검증한다.
- Deploy Key 개인키는 저장소 밖에 두고 삭제·교체 시 정확한 키만 대상으로 한다.
- 원격 생성이나 권한 설정이 부분 실패하면 완료로 보고하지 않고 생성된 정확한 자원과 복구 방법을 보고한다.

---

## 8. 전체 완료 조건

다음 조건이 모두 충족돼야 전체 작업을 완료로 판정한다.

- [ ] `Agent-Core`가 특정 Maintainer·Host에 의존하지 않는 순수 Core다.
- [ ] Host가 Core submodule 내부 파일을 수정하지 않고 상태를 유지한다.
- [ ] Core 자체 회귀·무결성·clean clone 게이트가 통과한다.
- [ ] Maintainer는 Core fetch와 승인된 push가 가능하다.
- [ ] 일반 Host는 Core fetch가 가능하고 push는 거부된다.
- [ ] 개인키·토큰·로컬 인증 설정이 어떤 저장소에도 추적되지 않는다.
- [ ] 첫 실제 Host에서 clean clone과 실제 Agent 작업이 통과한다.
- [ ] 두 번째 서로 다른 실제 Host에서 Core 변경 0건으로 통과한다.
- [ ] Core 사용 안내서가 최초 설정, clone, update, 버전 고정, 검증, 실패 복구 절차를 제공한다.
- [ ] 실행하지 않은 필수 검사가 0개다.
- [ ] 검증된 계약과 현재 상태가 각 소유 저장소의 정본에 반영된다.

---

## 9. 첫 다음 행동

이 문서 승인 후 처음 수행할 작업은 **단계 1 — 현재 `Agent-Core` 전 파일 소유권 분류**다.

단계 1에서는 분석 결과만 작성하고 실제 Core 파일을 이동·수정·삭제하지 않는다. 분류 결과와 정확한 변경 후보를 사용자에게 보고한 뒤, 단계 2 설계와 Core 변경 승인으로 넘어간다.
