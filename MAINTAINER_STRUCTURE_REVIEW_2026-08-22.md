# Agent Core Maintainer 구조 진단 (2026-08-22)

- 목적: `Agent-Core-Maintainer` 소비 저장소와 고정된 Core `cfbd7e2`의 구조를 분석하고 재현된 개선 대상만 소유한다.
- 읽는 시점: Core·Maintainer 작업 브랜치의 push·병합 순서를 결정하기 전, 또는 Host 적용 범위를 판단할 때.
- 책임: 사용자가 처리 순서와 승인 경계를 소유하고 작업 에이전트가 각 항목의 재현과 수정을 수행한다.
- 상태: 한시 자료. 내용을 정본에 흡수한 뒤 종료한다. 현재 상태를 소유하지 않는다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`가 상위다.

---

## 0. 검증 환경과 한계

이 진단은 **파일을 변경하지 않았다.** 실행이 필요한 검사는 저장소 사본에서만 수행했고 작업 트리는 깨끗한 상태 그대로다.

| 항목 | 값 |
|---|---|
| 대상 | `D:\AI Agent\Sandbox\Agent-Core-Maintainer` |
| 부모 브랜치 | `codex/agent-core-integration` (작업 트리 clean) |
| Core submodule | `cfbd7e2` / `codex/legacy-rule-absorption` / core 0.3.0 · contract 2 |
| 실행 Python | 3.10.12 |

**결정적 한계 하나**: 이 검증 환경의 Python은 3.10이다. Core가 `python_min: "3.10"`을 선언하므로 3.10 실행은 정당한 지원 범위 검증이지만, **사용자 개발 환경(3.11 이상 추정)에서의 통과 여부는 이 진단으로 반증되지 않는다.** 아래 H2는 "3.10에서 깨진다"이지 "모든 환경에서 깨진다"가 아니다. 반면 H1·H3·H4·M1~M4는 Python 버전과 무관하다.

확인하지 않은 것: 실제 Host 적용, Deploy Key fetch·push 권한, Codex·Claude 실제 진입 동작, 보호 경로(`inputs`/`outputs`) 내용, Windows 환경에서의 `clone_conformance.py` 실행.

---

## 요약

Core 자체 계약 검사와 소비 계약 검사는 **전부 통과한다**(`verify` 19종, 위반 0). 이전 진단의 H1·H2·H3(게이트 환경변수 우회, 소비 검사 실행 보고, context 중복 route)는 실제로 수정되어 있음을 코드에서 확인했다.

그러나 **L7 `shared_data` 흡수가 격리되지 않았다.** 이 저장소가 문서로 보장한 "선택 기능은 없어도 필수 Core가 성립한다"는 성질이 지금은 성립하지 않으며, 그 여파가 Core 게이트·Extension·clone 가능성까지 이어진다. 발견 13건 중 높음 4건은 모두 여기에서 갈라져 나온다.

| 등급 | 건수 | 성격 |
|---|---:|---|
| 높음 | 4 | 선언된 보장과 실제 동작의 불일치 |
| 중간 | 4 | 라우팅·정본 경계 밖의 지시 채널 |
| 낮음 | 5 | 정체성 잔재와 잠재 결함 |

---

## 1. 저장소 구조

| 영역 | 소유 | 검사 대상 여부 |
|---|---|---|
| `core/` (submodule) | Agent Core 0.3.0 — 공통 정책·규칙·검증기·L7 `experimental/shared_data` | Core 자체 gate |
| `PROJECT_RULES.md` | 소비 계약(`maintainer`), 도메인 route 6종, 보호 경로 4종 | 소비 gate |
| `AGENTS.md` / `CLAUDE.md` / `SESSION_HANDOFF.md` | 진입 포인터와 현재 상태 | 소비 gate |
| `extension/` | YouTube·영상 도메인 규칙 6종, 스키마, src 15모듈, 테스트 143종 | `extension/rules/`만 route 검사 |
| `.agents/skills/` | 실행되는 스킬 9종 (SKILL.md 16파일, 스크립트 11개) | **없음** |
| `scripts/` | `verify.py` 통합 게이트, `bootstrap.py`, `clone_conformance.py` | 없음 |

계약 표면은 정확히 구성되어 있다. `consumer-contract`·`consumer-entry`·`consumer-state`·`consumer-rule-routes`·`consumer-submodule` 7종이 위반 0으로 통과하고, 시작 컨텍스트는 8,756자 / 예산 20,000자로 여유가 있다.

---

## 2. 높음

### H1. L7을 제거하면 Core 필수 검증이 성립하지 않는다

**위치**: `core/docs/COMPATIBILITY.md`의 `optional_capabilities` 선언 → `core/src/core_check/declarations.py:260`

`declared_compatibility()`가 선언된 `entry_module` 디렉터리의 **존재를 필수로 요구**한다. 이 함수는 `verify`, `gate`, `_min_python()`, 그리고 모든 `CompatibilityTest`가 호출하는 공통 경로다. 따라서 `experimental/`을 지우면 선택 기능이 비활성화되는 것이 아니라 Core 전체가 검사 불가 상태가 된다.

```
# experimental/ 만 제거한 Core 사본
$ python -B -m core_check --core-root . verify
{ "error": "shared_data.entry_module 디렉터리가 없다: experimental/shared_data",
  "kind": "CheckError", "ok": false }
exit=2

$ python -B -m core_check --core-root . gate
ok= False  failed_step= preflight-contract
  preflight-contract  fail      shared_data.entry_module 디렉터리가 없다
  core-integrity      not_run   preflight 실패로 실행하지 않았다
  regression-tests    not_run   preflight 실패로 실행하지 않았다
```

**위반한 자기 기준**

- `core/docs/ARCHITECTURE.md` §4: "L7이 없어도 Core import, Core 자체 `verify`, Core 자체 `gate`가 성립해야 한다. **L7 전체를 제거했을 때 Core 필수 보장이 줄어들면 그 기능은 격리되지 않은 것이다.**"
- `core/docs/EXPERIMENTAL.md` §1 격리 규칙: "부재: 실험 기능이 없으면 등록 건수가 0이고 게이트는 `not_applicable`로 보고한다. 실패가 아니다."
- `core/docs/KERNEL_SCOPE.md` §4: "선택 기능 부재는 이유가 있는 `not_applicable`이며 실패가 아니다."

**권고**: `declared_compatibility()`에서 `entry_module` 경로를 **상대경로 안전성만** 판정하고 존재 확인은 하지 않는다(보호 경로 처리와 같은 원칙). 존재 여부는 `_optional()` 단계가 판정해 없으면 `not_applicable`, 있으나 실패하면 `fail`로 나눈다. 회귀 검사로 "`experimental/` 제거 후에도 `verify`가 exit 0"을 고정한다.

---

### H2. 선언한 최소 Python 3.10에서 필수 게이트가 실패한다

**위치**: `core/experimental/shared_data/{record,store,cli,knowledge,lifecycle,work_state}.py` — 6개 모듈이 `from datetime import UTC` 사용. `UTC`는 Python **3.11**에 추가됐다.

Core는 `python_min: "3.10"`을 선언하고 preflight도 3.10.12를 `pass`로 통과시킨다. 그 다음 단계에서 무너진다.

```
$ python3 -B -m core_check --core-root core --consumer-root . gate      # Python 3.10.12
ok= False   failed_step= regression-tests
  preflight-runtime      pass   Python 3.10.12 / core 0.3.0
  core-integrity         pass   검사 12종, 위반 0
  regression-tests       fail   ImportError: cannot import name 'UTC' from 'datetime'
                                Ran 111 tests — FAILED (failures=1, errors=8)
  optional-features      fail   shared_data: ImportError ... 'UTC'
  consumer-integrity     pass   검사 7종, 위반 0
```

Core 테스트 실패 9건은 전부 `shared_data` 계열이다(`test_shared_{context,data,knowledge,lifecycle,work}` 로더 오류 5, `test_shared_cli` 4). Extension도 같은 원인으로 무너진다.

```
$ python3 -B -m unittest discover -s extension/tests -q                 # Python 3.10.12
Ran 143 tests — FAILED (errors=7)
# 7건 전부 test_youtube_domain / test_export_conformance,
# 경로는 core_clients._run_json → experimental.shared_data → datetime.UTC
```

**여기서 진짜 문제는 버전 숫자가 아니라 검사 부재다.** Core에는 `test_running_runtime_satisfies_declaration`이 있지만 이는 "실행 중인 런타임 ≥ 선언값"만 본다. 3.10 ≥ 3.10이므로 통과한다. **코드가 실제로 요구하는 하한이 선언값과 같은지는 아무도 검사하지 않는다.** `core/docs/VERIFICATION.md` §6이 "실행하지 않은 환경·Python 검사를 지원 범위로 선언하지 않는다"고 못 박은 지점이 그대로 발생했다.

**권고**: 둘 중 하나를 **선택하고 검사로 고정**한다.

1. `shared_data`를 3.10 호환으로 되돌린다 — `from datetime import timezone` + `timezone.utc`. 변경 6파일, 의미 동일.
2. `python_min`을 `"3.11"`로 올린다. 이는 공개 계약 변경이므로 `COMPATIBILITY.md` §4 기준의 이전 절차 판단이 필요하다.

어느 쪽이든 **선언된 `python_min`에서 gate를 1회 실제 실행하는 검사**를 추가해야 재발하지 않는다.

---

### H3. 고정된 gitlink가 원격에 없는 커밋을 가리켜 clone이 불가능하다

**위치**: 부모 커밋의 `core` gitlink = `cfbd7e2`

```
$ git ls-tree HEAD core
160000 commit cfbd7e2bb80eae6120fd9b0bee533152d7a0eb6d  core

$ cd core && git branch -r --contains cfbd7e2
(비어 있음 — 어떤 원격 브랜치에도 없음)

$ git branch --contains cfbd7e2
* codex/legacy-rule-absorption          # 로컬 단일 사본

$ cd .. && git for-each-ref --format='%(refname:short) -> %(upstream:short)' refs/heads
codex/agent-core-integration ->         # upstream 없음 (미push)
main -> origin/main [behind 1]
```

`core/docs/CONSUMER_GUIDE.md` §3이 규정한 `git clone --recurse-submodules` 경로는 지금 이 저장소에서 성립하지 않는다. 부모 브랜치도 원격에 없고, 있더라도 submodule 커밋을 fetch할 수 없다.

`SESSION_HANDOFF.md`는 이를 "알려진 위험 — 후보 커밋은 로컬에만 있으며 push하지 않았다"로 이미 기록하고 있다. 다만 **승인 대기 사항으로만 적혀 있고, 그 결과가 "현재 저장소는 재현·복구 불가 상태"라는 점은 드러나지 않는다.** `core/PROJECT_RULES.md` §10은 "복구 지점은 검증된 Git commit이 소유한다"고 규정하는데, 단일 로컬 사본은 복구 지점이 아니다.

**권고**: 처리 순서상 가장 먼저다. push 승인을 받아 Core 작업 브랜치 → 부모 작업 브랜치 순으로 올리고, 그 시점에 `main`의 `behind 1`도 함께 정리한다. push 전까지는 Host 적용이나 태그·릴리스를 시작하지 않는다.

---

### H4. Extension이 "선택" 기능을 필수로 요구한다

**위치**: `extension/src/core_clients.py:82-106`, `extension/src/domain_conformance.py:31`

```python
# core_clients.public_core_manifest — 항상 shared_data를 호출한다
info = _run_json([sys.executable, "-B", "-m", "experimental.shared_data", "info"], core_root=root)

# domain_conformance.validate_public_manifest — 없으면 예외
if manifest["capability"] != "shared_data" or manifest["capability_version"] != 1:
    raise ValueError("shared_data v1 공개 기능이 필요하다")
```

`shared_data`는 Core에서 `optional_capabilities`로 선언되어 있다. 그러나 Extension에는 그 기능이 없을 때의 경로가 없다. H1과 합치면, `optional`이라는 이름이 Core 안에서도(제거 시 붕괴) 소비 저장소에서도(부재 시 예외) 실제로는 필수를 뜻한다.

**권고**: 둘 중 하나를 명시적으로 선택한다.

- `shared_data`를 필수 Kernel로 **승격**한다 — `core/docs/EXPERIMENTAL.md` §2의 승격 조건 5개를 문서로 판정한 뒤 `optional_capabilities`에서 뺀다. 실제 소비자(Extension)가 이미 존재하므로 조건 1은 충족되어 보인다.
- 또는 Extension에 부재 경로를 넣는다 — `capability`가 없으면 `not_applicable` manifest로 축약하고 domain conformance를 건너뛴다.

지금처럼 **선언은 optional, 구현은 required**인 상태가 가장 나쁘다. 어느 쪽으로 정하든 H1의 격리 수정과 함께 가야 일관된다.

---

## 3. 중간

### M1. 스킬 계층이 라우팅·검증 밖의 두 번째 지시 채널이다

`.agents/skills/`에는 SKILL.md 16개(총 76KB)와 실행 스크립트 11개가 있다. 이들은 **에이전트가 실제로 읽고 실행하는 지시문**이지만,

- `core-rule-routes:v1` 표에 route되지 않는다 (route는 `extension/rules/` 6종만 가리킨다).
- 소비 계약의 `rule_roots`에 포함되지 않는다 → `consumer-rule-routes` 검사 대상 밖.
- 5개 표준 헤더(목적·읽는 시점·책임·상태·관련 권위)를 갖지 않는다 → `consumer-document-headers` 대상 밖.
- 어떤 게이트도 이 파일들을 읽지 않는다.

`core/PROJECT_RULES.md` §4는 "논리적 작업 하나당 일치하는 소유자를 한 번씩 읽는다"로 시작 문맥을 제한하는데, 스킬은 그 제한 밖에서 활성화된다. `core/docs/CHARTER.md` 설계 원칙 4("필요한 규칙만 route해 시작 문맥을 제한한다")가 절반만 적용되고 있다.

**권고**: `rule_roots`에 `.agents/skills`를 추가하는 것이 정답은 아니다(스킬은 조건부 규칙이 아니라 실행 절차다). 대신 소비 정책에 **스킬과 규칙의 경계를 한 줄로 선언**한다 — "스킬은 절차만 소유하고 승인·보호·권위 판단을 소유하지 않는다" — 그리고 그 선언을 검사로 만든다(아래 M2가 그 필요를 보여준다).

### M2. 위임 정책이 이중 정본이고, 두 스킬의 승인 경계 표현이 어긋난다

같은 사실이 두 곳에 있다.

```
PROJECT_RULES.md:45
  coordinate-video-production에서 ... 끝까지 진행 ... 요청하면, 제목·썸네일 문구·
  생성 이미지·최종 시각 선택은 되돌릴 수 있는 로컬 창작 선택으로 위임된 것으로 기록한다.

.agents/skills/coordinate-video-production/SKILL.md:10-12
  When the user provides a topic and asks for a new video, says `끝까지 진행` ...
  set thumbnail_contract.approval_mode: delegated_by_user ...
  This section supersedes older wording that treated `끝까지 진행` ...
  as insufficient evidence of creative delegation.
```

스킬 쪽이 "supersedes"라고 선언하지만, `core/PROJECT_RULES.md` §2의 권위 순서(최신 사용자 지시 > Core 정책 > 소비 정책 > route된 소유자)에 **스킬은 아예 등장하지 않는다.** 권위 밖의 문서가 권위를 주장하고 있다.

더 실질적인 문제는 다른 스킬과의 어긋남이다.

```
coordinate-video-production/SKILL.md:10
  → `끝까지 진행` 이면 thumbnail_contract.approval_mode: delegated_by_user 로 설정한다

youtube-title-thumbnail/SKILL.md:43
  → delegated_by_user 는 "사용자가 창작 승인 생략이나 임의 확정을 명시한 계약이
     있을 때만" 사용한다. 상위 작업의 execution_mode 만으로 승인 위임을 추정하지 않는다.
```

상위 스킬은 "끝까지 진행"을 명시적 위임으로 취급하고, 하위 스킬은 그보다 강한 명시성을 요구한다. 두 문장을 동시에 만족시키는 해석이 자명하지 않다. **창작 승인 경계는 이 프로젝트에서 사용자가 소유한 판단**이므로(`core/PROJECT_RULES.md` §6) 해석 여지를 남길 자리가 아니다.

**권고**: 위임 조건의 정본을 `PROJECT_RULES.md` 한 곳으로 확정하고, 두 SKILL.md는 그 조항을 **링크로만** 참조하도록 줄인다. `youtube-title-thumbnail`의 문장은 정본과 같은 기준으로 다시 쓴다.

### M3. `bootstrap.py`가 Python 하한을 상수로 박는다

```python
# scripts/bootstrap.py:48
python_supported = sys.version_info >= (3, 11)      # 선언이 아니라 상수
```

Core는 `python_min`을 선언에서 읽도록 만들어져 있고(`gate._min_python()`), 그 성질을 `test_gate_reads_minimum_from_declaration_not_constant`가 검사한다. Maintainer의 bootstrap은 같은 종류의 사실을 상수로 복제하며, **값도 다르다**(Core 3.10 / bootstrap 3.11).

```
$ python3 -B scripts/bootstrap.py --json      # Python 3.10.12
ok= False
python= {'status': 'unavailable', 'supported_range': '>=3.11', 'version': '3.10.12'}
```

즉 Core가 지원한다고 선언한 런타임에서 Maintainer 게이트는 첫 단계에서 멈춘다. H2와 같은 뿌리지만 이쪽은 **불일치를 만드는 구조** 자체가 문제다.

**권고**: `bootstrap.py`가 `core/docs/COMPATIBILITY.md`의 `python_min`을 읽게 한다. Maintainer가 Core보다 높은 하한을 요구해야 한다면 그 값을 `pyproject.toml` 한 곳에서 읽고 "Core 하한보다 높다"는 사실을 명시적으로 기록한다.

### M4. Node 지원 범위가 4개 파일에 중복 선언된다

`>=20 <22`가 `package.json`(engines), `pyproject.toml`(`[tool.project-foundation] node`), `scripts/bootstrap.py`(문자열 3회), `scripts/node_verify.mjs`(`major >= 20 && major < 22`)에 각각 있다. `core/docs/INFORMATION_ARCHITECTURE.md` §1 "모든 활성 사실은 scope 안에서 정본이 정확히 하나다"에 어긋난다.

**권고**: `package.json`의 `engines.node`를 정본으로 두고 나머지가 그 값을 읽는다. `node_verify.mjs`는 `package.json`을 읽어 비교하면 된다.

---

## 4. 낮음

| ID | 항목 | 근거 | 권고 |
|---|---|---|---|
| L1 | 프로젝트 정체성 잔재 | `pyproject.toml`·`package.json`의 `name = "kim-silver-project-foundation"`, description "Domain-neutral project foundation for deterministic local verification." — 현재 저장소는 Agent Core Maintainer다. | 이름·설명을 현재 정체성으로 교체한다. |
| L2 | 썸네일 테스트가 조용히 빠질 수 있다 | `scripts/verify.py:64` `optional_ready = shutil.which("python") is not None` — PIL 설치 여부와 무관한 실행 파일 존재를 먼저 본다. `python` 없이 `python3`만 있는 환경(다수 Linux·macOS)에서는 PIL이 있어도 테스트 2종이 제외되고 `"unavailable"`로만 보고되며 게이트는 통과한다. 이번 환경에는 `python`이 있어 발현하지 않았다. | `which` 검사를 제거하고 PIL import 결과만 사용한다. 제외가 발생하면 제외된 테스트 이름을 함께 출력한다. |
| L3 | 절단된 stdout을 JSON으로 파싱한다 | `scripts/verify.py:57` `"stdout": completed.stdout[-2000:]` → `:141` `json.loads(bootstrap["stdout"])`. 표시용 절단이 파싱 전에 적용된다. 현재 bootstrap 출력은 760자라 발현하지 않지만, 항목이 늘면 `invalid_json`으로 오진단된다. | 원본 stdout을 파싱하고 절단본은 보고용으로만 보관한다. |
| L4 | 추적 md 22개가 어떤 검사에도 잡히지 않는다 | 소비 검사가 보는 md는 계약 표면 4개 + `extension/rules/` 6개뿐이다. `README.md`(14KB, `.obsidian/app.json`의 정본 block 보유), `extension/README.md`, `extension/docs/domain/youtube/` 3종, `extension/reports/` 1종, 스킬 16종이 밖에 있다. 그중 17개는 5개 표준 헤더가 없다. | 최소한 `extension/docs/`를 검사 대상에 넣는다(도메인 계약 정본이 있는 곳이다). 스킬은 M1의 경계 선언과 함께 다룬다. |
| L5 | `main`이 `origin/main`보다 1 뒤 | `main -> origin/main [behind 1]` | H3의 push 작업과 함께 정리한다. |

---

## 5. 처리 순서

의존 관계를 반영한 순서다. 각 항목의 작업 등급은 `core/PROJECT_RULES.md` §3 기준이다.

| 순서 | 대상 | 이유 | 등급 |
|---:|---|---|---|
| 1 | **H3** push 승인과 실행 | 복구 지점이 로컬 단일 사본인 동안에는 다른 수정의 실패 비용을 되돌릴 수 없다. 이 저장소 `SESSION_HANDOFF.md`의 첫 다음 행동과 같다. | `controlled` |
| 2 | **H2** 결정: `timezone.utc` 환원 또는 `python_min` 3.11 상향 | H1·H4의 수정 범위가 이 결정에 따라 달라진다. 먼저 정한다. | `controlled` |
| 3 | **H1** `entry_module` 존재 확인 제거 + 격리 회귀 검사 | Core 변경이므로 승인 필요. "L7 제거 후에도 verify exit 0"을 검사로 고정한다. | `controlled` |
| 4 | **H4** `shared_data` 승격 판정 또는 Extension 부재 경로 | H1이 정리된 뒤라야 "optional의 의미"가 확정된다. | `controlled` |
| 5 | **M3 · M4 · L3** 선언 복제 제거 | 서로 독립적이고 국소적이다. H2 결정 이후 한 번에 정리한다. | `standard` |
| 6 | **M1 · M2** 스킬 경계 선언과 위임 정본 단일화 | 승인 경계 문서 변경이므로 사용자 확인이 필요하다. | `controlled` |
| 7 | **L1 · L2 · L4 · L5** | 배포 위생. 앞 단계 수정이 끝난 뒤 처리한다. | `standard` |

---

## 6. 이번에 실행한 검사

| 검사 | 결과 |
|---|---|
| `core_check --core-root core verify` | `pass` — 12종, 위반 0 |
| `core_check --core-root core --consumer-root . verify` | `pass` — 19종, 위반 0 |
| `core_check --core-root core --consumer-root . gate` | `fail` — `regression-tests`, `optional-features` (Python 3.10) |
| Core 회귀 테스트 (3.10) | 111종 중 실패 1 · 오류 8 — 전부 `shared_data` |
| Extension 테스트 (3.10, 사본) | 143종 중 오류 7 — 전부 `core_clients` → `shared_data` |
| L7 제거 반사실 검증 | `verify` exit 2, `gate` preflight 실패 |
| `scripts/bootstrap.py` (3.10) | `ok: false` |
| Git·submodule 참조 도달성 | gitlink `cfbd7e2`가 어떤 원격에도 없음 |

## 7. 실행하지 않은 검사

- Python 3.11 이상에서의 전체 게이트 — 이 환경에 3.10만 있다. **H2의 발현 범위는 이 진단으로 확정되지 않는다.**
- `scripts/verify.py`와 `scripts/clone_conformance.py` 전체 실행 — Node 부재와 Windows 전용 경로 처리로 이 환경에서 유효하지 않다.
- 실제 Host 적용, Deploy Key fetch·push 권한, Codex·Claude 실제 진입 동작.
- 보호 경로(`inputs`, `outputs`, `extension/inputs`, `extension/outputs`) — 계약상 열거·읽기하지 않았다.
- 스킬 스크립트 11종의 동작 검증 — 정적으로만 읽었다.

이 문서는 현재 checkout 수준의 진단이며 `self-operated`나 `cross-agent` 수준이 아니다.
