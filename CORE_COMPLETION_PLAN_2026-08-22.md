# Agent Core 완료 작업 계획

- 목적: Agent Core와 Maintainer를 끝없이 개선하는 대신, 이미 약속한 Core 구축 의도를 충족하기 위한 필수 작업과 최종 종료 조건을 고정한다.
- 읽는 시점: 다음 개선작업을 시작하기 전과 각 단계의 완료 여부를 판정할 때.
- 책임: 작업 에이전트는 이 문서에 포함된 범위만 구현·검증하고, 사용자는 승인 정책의 의미와 원격 게시 여부를 결정한다.
- 상태: 외부 검토를 교차 반영한 실행 전 고정 계획. 구현 완료 문서가 아니며, 단계별 성공 게이트가 모두 통과하기 전에는 프로젝트 완료를 선언하지 않는다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, `core/docs/ARCHITECTURE.md`, `core/docs/COMPATIBILITY.md`.

---

## 1. 작업 의도

현재 후보는 현재 파일 구성과 Python 3.12 환경에서는 통과하지만, 처음부터 문서에 선언된 다음 조건을 충분히 검증하지 못했다.

- `R1` L7 선택 기능이 없어도 필수 Core가 성립한다.
- `R2` 선언된 최소 Python 버전에서 Core가 동작한다.
- `R3` Core의 선택 기능과 특정 Consumer의 필수 의존성을 구분한다.
- `R4` 사용자 승인 조건은 정본 한 곳에서만 정의된다.
- `R5` 로컬 사본 검증과 실제 원격 submodule 검증을 구분한다.
- `R6` 검증 실행이 작업 트리를 오염시키지 않는다.

이 문서는 위 조건을 충족하는 데 필요한 작업만 소유한다. 새로운 기능, 점수 상승을 위한 리팩터링, 일반적인 문서 미화는 추가하지 않는다.

### 1.1 요구사항 추적표

각 요구는 재현된 반례, 그 요구가 조용히 깨지는 실패 모드, 소유 단계, 통과를 판정할 게이트를 모두 가져야 한다. 빈 칸이 있는 요구는 구현을 시작하지 않는다.

| ID | 재현된 반례 | 실패 모드 | 소유 단계 | 판정 게이트 |
|---|---|---|---|---|
| `R1` | L7 제거 시 `verify` findings 17건. `layer-boundaries` 11 · `markdown-links` 6 | 일부만 남은 손상 설치를 `not_applicable`로 통과시킨다 | 1 | L7 전무에서 exit 0, 일부 결손에서 `fail` |
| `R2` | 3.10에서 `datetime.UTC` ImportError. 수집 테스트가 167종에서 111종으로 줄어든다 | 인터프리터 부재를 `not_applicable`로 세탁한다. 수집 실패한 case가 집계에서 사라진다 | 1 · 3 | 실제 3.10 실행이 `pass`. 부재는 `not_run`이며 전체 실패 |
| `R3` | Extension이 선택 기능인 `shared_data`를 항상 호출한다 | 선택 key를 `maintainer` 필수로 만들어 기존 Host 계약을 조인다 | 2 | `shared_data` 없는 Host gate 통과, 없는 Maintainer는 누락을 명시 보고 |
| `R4` | 두 SKILL.md의 `delegated_by_user` 트리거 강도가 상충한다 | 정적 fixture 통과를 실제 자연어 해석 검증으로 확대 보고한다 | 2 | 모든 fixture case가 정본 조항에 도달하고 결함 주입 시 실패 |
| `R5` | 고정된 gitlink가 원격에 없는 커밋을 가리켜 clone이 불가능하다 | 로컬 URL clone 성공을 원격 도달성으로 보고한다 | 3 · 원격 게시 | 결과에 `local`·`remote` 범위가 구분되고 원격 부재는 명시적 실패 |
| `R6` | `extension/work`에 테스트 임시 폴더 41개. 어떤 게이트도 탐지하지 못했다 | 탐지기 없이 청소만 해 다음 실행에서 재발한다 | 3 · 4 | 검증 실행 전후의 추적·비추적 상태가 동일 |

## 2. 완료 상태 정의

프로젝트 상태는 다음 두 단계로 구분한다.

### 2.1 로컬 구현 완료

- 이 문서의 0~4단계가 모두 통과했다.
- Core와 Maintainer 후보가 각각 로컬 Git commit으로 고정됐다.
- 두 작업 트리가 clean이다.
- 아직 원격 도달성을 검증하지 않았으므로 최종 배포 완료라고 부르지 않는다.

### 2.2 원격 사용 검증 완료

- 별도 push 승인을 받은 뒤 Core 후보를 먼저 게시했다.
- Maintainer 후보가 원격에서 가져올 수 있는 Core commit을 가리킨다.
- 실제 원격 URL을 이용한 `clone --recurse-submodules`와 전체 gate가 통과했다.

이 두 상태를 혼합하거나 로컬 검증 결과를 원격 사용 검증으로 확대 보고하지 않는다.

---

## 3. 고정된 설계 결정

다음 방향을 권장 기본안으로 사용한다.

1. Core Kernel의 최소 Python은 3.10으로 유지한다.
2. `shared_data`는 물리적으로 제거할 수 있는 L7 선택 기능으로 유지한다.
3. Maintainer Extension은 `shared_data v1`을 명시적인 필수 의존성으로 선언한다.
4. 일반 Host는 `shared_data` 없이도 Core를 사용할 수 있어야 한다.
5. 창작 승인 조건은 `PROJECT_RULES.md` 한 곳만 소유한다.
6. `agent-core-consumer:v1`의 선택 key `required_core_capabilities`로 Consumer별 필수 capability를 선언한다. key가 없으면 요구 없음이며 `contract_version`은 2로 유지한다.
7. Maintainer 최소 Python은 3.11로 유지하고 `pyproject.toml`을 정본으로 삼는다. Core 3.10 하한과 Maintainer 3.11 하한을 서로 다른 범위로 보고한다.
8. Node 지원 범위는 `package.json`의 `engines.node`만 정본으로 삼고 다른 검사기가 그 값을 읽는다.
9. 필수 검증 단계는 `pass`, `fail`, `not_run`만 사용한다. 필수 단계의 `not_run`은 전체 실패이며 `not_applicable`로 세탁하지 않는다.
10. 작업 중 push, main 병합, 태그·릴리스 게시는 수행하지 않는다.
11. 각 단계의 성공 게이트는 정상·실패·경계 세 경로를 모두 포함한다. 정상 경로만 통과한 단계는 통과가 아니다.
    - 정상: 선언된 구성과 지원 Runtime에서 기대 결과가 나온다.
    - 실패: §1.1의 실패 모드를 주입했을 때 게이트가 실제로 실패한다.
    - 경계: 선택 기능 부재, 최소 지원 버전, 빈 선언처럼 계약의 끝값에서 판정이 갈린다.
12. 각 단계는 실행한 명령·Runtime·검사 목록과 `R1`~`R6` 중 어느 요구를 덮었는지 기록한다.

창작 승인 조건의 실제 의미를 변경해야 한다면 사용자 확인을 먼저 받는다. 나머지 항목은 기존 문서에 선언된 Core 의도를 구현과 검사에 일치시키는 작업이다.

---

## 4. 0단계 — 저장소 밖 복구 지점 확보

### 목표

원격에 아직 게시되지 않은 현재 Core `07d9bd1`과 Maintainer 작업 브랜치 후보를 단일 PC 작업 사본의 손상으로부터 복구할 수 있게 한다.

### 의도

push는 별도 승인이 필요하지만, 1~4단계를 단일 로컬 사본 위에 계속 쌓는 것도 복구 위험이 있다. 원격 게시 없이 현재 Git 객체와 branch를 보존하는 저장소 밖 bundle을 먼저 만든다.

### 작업 범위

- 두 저장소의 현재 branch·HEAD·작업 트리 상태를 기록한다.
- `D:\AI Agent\Sandbox\Recovery\`처럼 Core와 Maintainer 저장소 밖의 전용 경로에 각각 `git bundle`을 만든다.
- bundle에는 현재 작업 branch와 후보 commit이 반드시 포함돼야 한다.
- bundle에서 임시 clone을 만들고 원래 후보 commit ID를 복원할 수 있는지 확인한다.
- 보호 경로와 작업 파일을 복사하지 않고 Git 객체만 보존한다.

### 성공 게이트

- `git bundle verify`가 두 bundle에서 통과한다.
- bundle에서 복원한 Core HEAD가 `07d9bd1`, Maintainer HEAD가 작업 시작 직전 기록한 정확한 후보와 일치한다.
- 복원 검증 후 원본 저장소에는 새 추적·비추적 부산물이 생기지 않는다.
- 원격 push나 원격 ref 변경이 발생하지 않는다.

---

## 5. 1단계 — Core 선택 기능 계약과 Python 3.10 복구

### 목표

L7의 물리적 부재가 필수 Core를 무너뜨리지 않게 하고, Core가 선언한 최소 Python 3.10에서 실제로 동작하게 한다.

### 의도

현재는 `shared_data`가 선택 기능으로 선언됐지만 호환성 파서가 entry module과 모든 schema의 존재를 필수로 요구한다. 그 밖에도 모듈 계층 선언, Kernel 문서 링크, Kernel 테스트 배치가 L7 파일의 존재를 전제로 한다. 또한 구현과 테스트가 Python 3.11부터 제공되는 `datetime.UTC`를 사용한다. 문서의 선택 기능·지원 버전 선언과 실제 동작을 네 결합 지점 전체에서 일치시켜야 한다.

### 작업 범위

- 선택 기능의 설치 상태를 다음 세 상태로 구분한다.
  - 관련 구현·계약 문서·schema·선택 테스트가 전부 없음: `not_applicable`
  - 일부만 존재: 손상된 설치로 `fail`
  - 전부 존재: CLI·schema·버전 검증 후 `pass` 또는 `fail`
- Kernel 호환성 파싱이 entry module, `__main__.py`, request/result schema와 schema 목록의 물리적 존재 때문에 실패하지 않도록 책임을 분리한다.
- `core-module-layers:v1`의 L7 배정을 선택 기능 설치 상태와 함께 판정한다. L7 전체 부재는 `not_applicable`, 일부 파일만 남은 상태는 `fail`이어야 한다.
- `docs/EXPERIMENTAL.md`와 `docs/KERNEL_SCOPE.md`가 L7 구현 안의 계약 문서에 직접 의존하지 않게 한다. L7 부재 상태에서도 Kernel 문서 링크 검사가 통과해야 한다.
- L7 테스트 6파일을 Kernel 필수 테스트와 물리적으로 분리한다. 선택 기능이 있으면 선택 테스트를 실행하고, L7 전체가 없으면 테스트 자체도 함께 빠져야 한다.
- `datetime.UTC` 사용을 Python 3.10 호환 표현으로 교체한다.
- 구현뿐 아니라 Python 3.10에서 import되는 관련 테스트도 함께 수정한다.
- 선택 기능이 없는 Core에서 Kernel module이 L7을 import하지 않는지 확인한다.

### 성공 게이트

- Python 3.10에서 Core `verify`와 `gate`가 통과한다.
- L7 전체가 없는 임시 Core에서 `verify`와 `gate`가 exit 0이다.
- L7 전체가 없는 임시 Core에서 `layer-boundaries`, `markdown-links`, `regression-tests` 위반이 발생하지 않는다.
- L7의 구현·계약 문서·schema·계층 배정·선택 테스트 중 일부만 누락한 경우 gate가 실패한다.
- L7이 완전한 현재 구성에서는 `shared_data` 공개 계약 검사가 통과한다.
- L7이 완전한 현재 구성에서는 관련 테스트 모듈이 전부 수집되고 현재 Python 환경의 Core 회귀 테스트가 모두 통과한다.

---

## 6. 2단계 — Maintainer 의존성과 승인 정책 단일화

### 목표

Core에는 선택적인 `shared_data`가 Maintainer에는 왜 필요한지 명시하고, 영상 제작 스킬의 창작 승인 조건을 하나의 정본으로 통일한다.

### 의도

선택 기능을 사용하는 특정 Consumer가 있다는 사실은 그 기능이 모든 Host의 Kernel이어야 한다는 뜻이 아니다. Maintainer만의 필수 의존성을 명시해야 한다. 또한 현재 영상 제작 스킬에는 `끝까지 진행`의 승인 의미가 서로 반대인 문장이 공존하므로 사용자 소유 판단을 결정론적으로 만들 필요가 있다.

### 작업 범위

- Maintainer의 `agent-core-consumer:v1` 블록에 선택 key `required_core_capabilities: {"shared_data": 1}`을 두고, 일반 Host에서 key가 없으면 요구 없음으로 해석한다.
- Core 소비 계약 파서는 이 선택 key가 있을 때 capability ID와 양의 버전을 검증하되 기존 key 부재 Consumer를 그대로 허용한다.
- 선택 key 추가는 기존 Consumer를 조이지 않는 호환 변경으로 처리하고 `contract_version`은 2로 유지한다.
- Maintainer 통합 gate가 이 의존성을 검사한다.
- 창작 승인 조건은 `PROJECT_RULES.md` 한 곳에만 둔다.
- `coordinate-video-production`과 `youtube-title-thumbnail`은 정본 조건을 참조하고 자체적인 `supersedes` 또는 상충 해석을 소유하지 않는다.
- 스킬은 실행 절차만 소유하고 보호·승인·권위 경계를 새로 만들 수 없다는 경계를 검사한다.
- `approval-mode-intents-v1.json` fixture에 대표 사용자 발화, 기대 `approval_mode`, 근거가 되는 `PROJECT_RULES.md` 조항 ID를 기록한다.
- 두 SKILL.md에는 승인 모드의 트리거 조건을 독자적으로 서술하지 못하게 하고 정본 링크만 허용한다.
- fixture 검사는 정책·문서의 구조적 일치만 소유한다. 실제 Agent의 자연어 의미 판정까지 검증했다고 확대 보고하지 않는다.

### 성공 게이트

- `shared_data`가 없는 일반 Host의 Core gate가 통과한다.
- `shared_data`가 없는 Maintainer에서는 누락된 필수 capability가 명시적으로 보고된다.
- `shared_data v1`이 있는 Maintainer에서는 통합 gate가 통과한다.
- 승인 mode fixture의 모든 case가 하나의 정본 조항과 기대 mode를 가진다.
- 두 SKILL.md에 독자적인 `delegated_by_user`·`review_gated` 트리거 조건이나 `supersedes` 문장을 주입하면 검사가 실패한다.
- 이 성공 게이트는 실제 Agent 자연어 해석 검증이 아니라 정적 계약 일치 검증으로 보고된다.

---

## 7. 3단계 — 검증기 신뢰성 완성

### 목표

필수 검사가 조용히 생략되거나 로컬 검증이 원격 검증으로 오인되는 경로를 제거한다.

### 의도

현재 게이트는 현재 런타임과 현재 설치 상태의 정상 경로에는 강하지만 최소 버전, 선택 기능 부재, 실제 원격 도달성, 테스트 부산물에는 약하다. 완료 보고는 검사 결과뿐 아니라 검사 범위가 요구사항을 포함한다는 증거를 가져야 한다.

### 작업 범위

- 선언된 최소 Python 버전에서 실제 Core gate를 실행하는 별도 필수 단계를 만든다. 결과 상태는 `pass`, `fail`, `not_run`만 허용한다.
- Python 3.10 인터프리터가 없으면 최소 버전 단계는 `not_run`이고 전체 gate는 실패한다. 자동 설치·다운로드는 하지 않으며, 필요한 Runtime 확보는 별도 승인 뒤 수행한다.
- Maintainer Python 3.11 이상 프로세스가 절대 경로로 확인된 Python 3.10을 하위 실행해 Core 범위만 검사하도록 분리한다.
- `scripts/bootstrap.py`는 `pyproject.toml`의 Maintainer 하한과 Core 호환성 선언의 Kernel 하한을 각각 읽고 서로 다른 범위로 보고한다.
- `scripts/verify.py`는 하위 명령의 원본 stdout을 먼저 파싱하고, 보고용 결과에서만 길이를 제한한다.
- Node 지원 범위는 `package.json.engines.node`에서 읽고 `pyproject.toml`, `bootstrap.py`, `node_verify.mjs`의 독립 상수·비교식을 제거하거나 파생 판정으로 바꾼다.
- 썸네일 선택 테스트의 실행 여부는 `python` 명령 이름이 아니라 PIL import 가능 여부로 판단한다.
- 생략된 선택 테스트의 이름과 이유를 결과에 기록한다.
- 각 테스트 모듈의 수집 성공 여부와 실행·skip 수를 보고한다. import 오류로 테스트 파일 내부 case가 집계에서 사라지면 전체 실패다.
- 테스트 fixture는 시스템 임시 경로를 사용하거나 생성 직후 cleanup을 등록한다.
- 로컬 Core URL을 사용하는 clone 검증과 실제 원격 URL을 사용하는 clone 검증을 서로 다른 결과로 보고한다.
- 검증 전후의 Git 상태를 비교해 새 부산물이 생기면 실패시킨다.

### 성공 게이트

- 필수 테스트는 환경변수나 실행 파일 별칭 때문에 생략되지 않는다.
- 실제 Python 3.10에서 Core 최소 버전 단계가 `pass`이며, 인터프리터 부재·실행 실패는 `not_run` 또는 `fail`로 전체 결과를 실패시킨다.
- Maintainer bootstrap은 Core 3.10과 Maintainer 3.11 하한을 구분해서 보고하고 현재 Maintainer Runtime을 `pyproject.toml` 기준으로 판정한다.
- 2,000자를 넘는 유효한 bootstrap JSON fixture도 원본 기준으로 정상 파싱된다.
- `package.json.engines.node`를 바꾸면 모든 Node 판정 결과가 함께 바뀌고 별도 상수 drift 검사가 통과한다.
- 선택 테스트가 생략되면 정확한 테스트 이름과 사유가 보고된다.
- 모든 예상 테스트 모듈이 수집되며 수집 오류나 누락 case가 0이다.
- 전체 테스트 실행 전후의 추적·비추적 상태가 동일하다.
- 로컬 clone 결과에는 `local` 범위가, 실제 원격 clone 결과에는 `remote` 범위가 표시된다.
- 원격 Core commit이 없을 때 remote 검증은 명시적으로 실패하고 local 검증 성공으로 가려지지 않는다.

---

## 8. 4단계 — 최종 마감 검증과 로컬 커밋

### 목표

0~3단계 결과를 깨끗한 후보 commit으로 고정하고 로컬 구현 완료 여부를 판정한다.

### 의도

완료 판정은 현재 작업 폴더의 우연한 상태가 아니라 재현 가능한 commit과 clean clone 증거에 기반해야 한다. 검증 과정에서 생긴 자료도 의도에 맞게 흡수하거나 제거해 작업 트리를 정리한다.

### 작업 범위

- 3단계의 작업 트리 오염 탐지기를 먼저 적용한 뒤 현재 `extension/work`에 남은 테스트 임시 폴더 41개를 정확한 생성 패턴과 경로로 재확인해 정리한다. 현재 실측 분포는 `manual-upload-package-*` 12개, `title-thumbnail-package-*` 14개, `youtube-upload-retention-*` 15개다.
- 외부 진단·계획 검토 문서의 유효한 내용은 구현·테스트·상태 정본에 흡수하고 한시 자료의 보존 여부를 결정한다.
- Core 전체 테스트와 Core 자체 gate를 실행한다.
- Maintainer 전체 테스트와 Core·Consumer 통합 gate를 실행한다.
- Python 3.10에서는 Core Kernel과 설치된 L7의 선언된 Core 범위를 실행하고, Python 3.11 이상에서는 Maintainer 전체 범위를 실행한다.
- ASCII·한글·공백 경로의 clean clone을 검증한다.
- Core 변경만 Core commit으로 고정한다.
- Maintainer가 검증된 Core commit을 가리키도록 gitlink와 Maintainer 변경을 별도 commit으로 고정한다.
- 두 저장소의 최종 Git 상태가 clean인지 확인한다.

### 성공 게이트

- 0~3단계의 모든 성공 게이트가 통과하고 필수 단계의 `not_run`이 0건이다.
- Core와 Maintainer clean clone이 각자 선언한 Runtime·capability 범위에서 동일한 결과를 낸다.
- 보호 경로를 열거·읽기·스테이지하지 않았다.
- Core와 Maintainer 작업 트리가 clean이다.
- 후보 commit ID, 실행한 검사, 제외된 외부 검증을 최종 보고에 구분해 기록한다.
- 새로운 commit은 원격에 push되지 않은 상태로 사용자에게 보고한다.

---

## 9. 원격 게시 단계 — 별도 승인 필요

이 단계는 개선 구현에 포함하지 않으며 사용자의 별도 push 승인 뒤에만 수행한다.

1. Core 작업 브랜치를 push한다.
2. 원격 ref에서 Core 후보 commit의 도달성을 확인한다.
3. Maintainer 작업 브랜치를 push한다.
4. 로컬 URL override 없이 실제 원격 URL로 `clone --recurse-submodules`를 실행한다.
5. 원격 clean clone에서 전체 gate를 실행한다.
6. `main`과 작업 브랜치의 포함 관계·충돌 후보를 보고한 뒤 main 반영 여부를 별도로 결정한다.

### 성공 게이트

- 다른 빈 경로에서 원격 Core와 Maintainer를 가져올 수 있다.
- submodule이 정확한 Core 후보 commit을 checkout한다.
- 원격 clean clone 전체 gate가 통과한다.
- 이 증거가 있을 때만 `원격 사용 검증 완료`로 보고한다.

---

## 10. 이번 완료 범위에서 제외하는 작업

다음은 현재 종료 조건을 막지 않으므로 이번 작업에 추가하지 않는다.

- 프로젝트 패키지 이름과 설명의 일반 정리
- 모든 Markdown 문서에 대한 포괄적인 형식 통일
- 점수 상승만을 목적으로 한 리팩터링
- 현재 종료 조건과 무관한 신규 기능
- 실제 Creator 프로젝트 적용
- main 병합, 태그, 릴리스 게시
- 실제 외부 서비스 쓰기와 사용자 데이터 작업

제외 항목은 현재 작업 도중 발견됐다는 이유만으로 자동 승격하지 않는다. 필수 종료 조건을 직접 방해하는 재현 증거가 생긴 경우에만 사용자에게 범위 변경을 요청한다.

이 제외 목록은 새 기능과 미화 작업에만 적용된다. §1.1의 `R1`~`R6` 위반은 제외 대상이 아니며 §11.1이 처리한다.

## 11. 최종 종료 규칙

다음 조건을 모두 만족하면 새 개선 목록을 만들지 않고 작업을 종료한다.

1. 0~4단계 성공 게이트가 모두 통과했다.
2. Core와 Maintainer 후보가 로컬 commit으로 고정됐다.
3. 두 작업 트리가 clean이다.
4. 미검증 항목은 실패나 성공으로 과장하지 않고 범위와 이유를 기록했다.
5. 원격 게시가 승인되지 않았다면 `로컬 구현 완료·원격 게시 대기`로 보고한다.
6. 원격 게시와 실제 원격 clone까지 통과했다면 `원격 사용 검증 완료`로 보고한다.
7. 각 단계는 실행한 명령·Runtime·검사 목록·상태를 기록하고, 필수 검사의 `not_run`이 하나라도 있으면 그 단계와 전체 계획은 통과가 아니다.
8. §1.1 추적표의 모든 행이 재현된 반례·실패 모드·판정 게이트를 갖고, 각 게이트가 §3.11의 정상·실패·경계 세 경로로 통과했다.

### 11.1 사후 결함 환류

종료 선언 뒤에 발견된 것이라도 §1.1의 `R1`~`R6` 위반은 새 개선 제안이 아니라 **미완료 결함**이다. 다음을 수행한다.

1. 해당 요구의 추적표 행을 미충족으로 되돌리고 재현 절차를 반례 칸에 적는다.
2. 그 위반이 통과하도록 방치한 게이트를 지목한다. 게이트가 없었으면 없었다고 적는다.
3. 반례를 결함 주입 회귀 검사로 추가해 같은 위반이 다시 통과하지 못하게 한다.
4. 소유 단계를 미통과로 되돌리고 §2의 완료 판정을 다시 계산한다.

이 절은 작업 후 분석을 억제하지 않는다. 분석은 언제든 허용하며, 억제되는 것은 §10의 새 기능·미화 작업뿐이다. 요구 위반을 발견하고도 종료 상태를 유지하는 것은 §5의 확대 보고 금지 위반이다.
