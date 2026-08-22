# 완료 작업 계획 검토

- 목적: `CORE_COMPLETION_PLAN_2026-08-22.md`의 진단 정확성·게이트 달성 가능성·누락 항목을 재현 근거와 함께 판정한다.
- 읽는 시점: 계획의 1단계를 시작하기 전, 또는 각 단계 성공 게이트의 정의를 확정할 때.
- 책임: 사용자가 설계 질문 3건과 범위 변경을 결정하고, 작업 에이전트는 확정된 게이트만 구현한다.
- 상태: 한시 자료. 내용을 계획 문서와 검사에 흡수한 뒤 종료한다.
- 관련 권위: `CORE_COMPLETION_PLAN_2026-08-22.md`가 계획의 정본이며 이 문서는 그 검토 의견만 소유한다.

---

## 0. 검토 방법과 한계

계획의 주장을 문서 대조가 아니라 **실행으로** 확인했다. 파일은 변경하지 않았고, 반사실 검증은 전부 저장소 사본에서만 수행했다. 작업 트리는 검토 전과 같다.

이 환경의 Python은 3.10.12 하나뿐이다. 따라서 계획 §1의 "Python 3.12 환경에서는 통과한다"는 직접 재현하지 못했고, `datetime.UTC`를 주입해 3.11 이상을 **모사**한 실행으로 간접 확인했다(§2 참조). 이 모사는 정황 근거이지 3.12 통과의 증명이 아니다.

---

## 1. 총평

**방향과 범위 규율은 타당하다. 다만 1단계 성공 게이트는 현재 정의로 달성할 수 없다.**

계획에서 특히 좋은 부분은 세 가지다.

- §2가 `로컬 구현 완료`와 `원격 사용 검증 완료`를 분리한 것. 이전 진단의 H3(원격에 없는 gitlink)를 "지금 못 고치는 것"이 아니라 "지금 주장하지 않는 것"으로 처리했다. `core/docs/VERIFICATION.md` §6의 확대 보고 금지와 정확히 맞는다.
- §9의 제외 목록과 "발견됐다는 이유만으로 자동 승격하지 않는다"는 문장. 진단 보고서가 나온 직후 흔히 생기는 범위 팽창을 미리 막았다.
- §10의 종료 규칙. 이 프로젝트에 지금까지 없던 것이 "언제 멈추는가"였고, 그것을 조건으로 고정했다.

보강이 필요한 것은 아래 순서다.

| 구분 | 건수 | 내용 |
|---|---:|---|
| 달성 불가한 게이트 | 1 | 1단계 §4 — L7 결합이 4개인데 계획은 1개만 다룬다 |
| 정의가 비어 있는 게이트 | 2 | 2단계 승인 모드 일치 검사, 3단계 최소 버전 실행 경로 |
| 누락된 항목 | 3 | `bootstrap.py` 3.11 상수, 절단 stdout 파싱, node 범위 중복 |
| 결정이 필요한 질문 | 3 | 의존성 선언 위치, Maintainer 최소 Python, 복구 지점 |

---

## 2. 계획이 정확히 짚은 것

전부 재현했다. 이 항목들은 그대로 진행해도 된다.

**§4 의도 — 호환성 파서가 물리적 존재를 요구한다**: 정확하다. 그리고 계획이 쓴 "entry module과 모든 schema"보다 실제로는 더 넓다. `declared_compatibility()`는 `entry_module` 디렉터리, 그 안의 `__main__.py`, `request_schema`, `result_schema`, `schemas` 목록의 **모든 파일**을 각각 `must_exist`로 요구한다(`declarations.py:245-284`). 이 중 하나만 없어도 `verify`가 exit 2다.

**§4 의도 — `datetime.UTC` 사용**: 정확하다. 구현 6개 모듈(`record`, `store`, `cli`, `knowledge`, `lifecycle`, `work_state`)과 테스트 5개 파일이 사용한다. 3.11+ 전용 API는 이것 하나뿐이며 `tomllib`·`ExceptionGroup`·`typing.Self`·`StrEnum` 사용은 없다. 즉 §4의 교체 범위는 이 한 종류로 닫힌다.

계획이 명시하지 않은 사실 하나를 덧붙인다. **3.10에서는 167개 중 56개가 실행되지 않는다.**

```
Python 3.10.12                     Ran 111 tests — FAILED (failures=1, errors=8)
datetime.UTC 주입(3.11+ 모사)       Ran 167 tests — FAILED (failures=1, errors=3)
```

3.10에서 줄어든 56개는 실패가 아니라 **모듈 로더 단계에서 사라진 것**이다. 5개 테스트 파일이 import 실패로 각각 오류 1건으로 접혀 그 안의 테스트가 집계에서 빠진다. 이것이 §6 의도의 "필수 검사가 조용히 생략되는 경로"의 실제 사례이므로, 3단계 게이트의 근거로 이 숫자를 쓰면 좋다.

모사 실행에서 남은 실패 4건은 전부 `test_shared_cli`이며, 이 테스트가 하위 프로세스를 띄우면서 주입 shim이 전달되지 않은 결과다. 즉 **실제 3.11 이상에서는 167개가 통과한다는 계획의 전제와 모순되지 않는다.**

**§7 — `extension/work` 임시 폴더 41개**: 정확하다. 41개 전부 `manual-upload-package-*`이며 전부 untracked다. 생성 주체도 특정된다.

```
extension/tests/test_manual_upload_package.py:41-44
    tempfile.TemporaryDirectory(
        prefix="manual-upload-package-",
        dir=REPO / "extension" / "work",     # 저장소 안에 fixture를 만든다
    )
```

여기서 중요한 것은 청소가 아니라 **어떤 게이트도 이 오염을 탐지하지 못했다**는 사실이다. `core-no-side-effects`는 `core/`만, `consumer-no-side-effects`는 계약 표면만 지문화한다. `extension/work`는 둘 다의 밖이다. §6 마지막 항목("검증 전후의 Git 상태를 비교해 새 부산물이 생기면 실패시킨다")이 이 구멍을 정확히 겨냥하고 있으므로, §7의 청소보다 §6의 탐지기를 먼저 넣는 편이 낫다.

**§5 의도 — 두 스킬의 승인 의미 충돌**: 실재한다. 다만 표현을 정확히 하면 "서로 반대인 문장"이라기보다 **트리거 조건의 강도가 다르다**.

```
coordinate-video-production/SKILL.md:10
  `끝까지 진행` → thumbnail_contract.approval_mode: delegated_by_user 로 설정

youtube-title-thumbnail/SKILL.md:43
  delegated_by_user 는 "사용자가 창작 승인 생략이나 임의 확정을 명시한 계약이
  있을 때만" 사용한다. 상위 작업의 execution_mode 만으로 승인 위임을 추정하지 않는다.
```

상위 스킬은 `끝까지 진행`을 명시적 위임으로 취급하고, 하위 스킬은 그보다 강한 명시성을 요구한다. `PROJECT_RULES.md:45`는 상위 스킬 쪽 해석을 지지한다. 따라서 §5의 작업은 "반대 문장 제거"가 아니라 **하위 스킬 문장을 정본 기준으로 다시 쓰는 것**이다.

---

## 3. 1단계 성공 게이트는 현재 정의로 달성 불가

계획 §4의 성공 게이트 두 번째 줄이다.

> L7 전체가 없는 임시 Core에서 `verify`와 `gate`가 exit 0이다.

이것을 실제로 시도했다. **L7과 Kernel의 결합은 네 곳이고, 계획의 작업 범위는 그중 하나만 다룬다.**

먼저 계획대로 1단계를 마친 상태를 모사했다. 즉 호환성 파서가 더 이상 물리적 존재를 요구하지 않는 상태(`optional_capabilities`를 비운 사본)에서 `experimental/`을 제거하고 `verify`를 실행했다.

```
ok= False   총 findings: 17

layer-boundaries  11건
  experimental/__init__.py                     L7 배정 대상 파일이 없다
  experimental/shared_data/__init__.py         L7 배정 대상 파일이 없다
  ... (선언된 L7 파일 11개 전부)

markdown-links     6건
  docs/EXPERIMENTAL.md   깨진 링크: ../experimental/shared_data/RECORD_STORAGE_CONTRACT.md
  docs/EXPERIMENTAL.md   깨진 링크: ../experimental/shared_data/KNOWLEDGE_LIFECYCLE_CONTRACT.md
  docs/EXPERIMENTAL.md   깨진 링크: ../experimental/shared_data/EVIDENCE_CONTEXT_CONTRACT.md
  docs/EXPERIMENTAL.md   깨진 링크: ../experimental/shared_data/WORK_STATE_CONTRACT.md
  docs/KERNEL_SCOPE.md   깨진 링크: ../experimental/shared_data/RECORD_STORAGE_CONTRACT.md
  docs/KERNEL_SCOPE.md   깨진 링크: ../experimental/shared_data/KNOWLEDGE_LIFECYCLE_CONTRACT.md
```

같은 사본에서 회귀 테스트도 실행했다.

```
Ran 111 tests — FAILED (failures=2, errors=9)
  test_shared_{context,data,knowledge,lifecycle,work}   로더 오류 5건
  test_shared_cli                                        오류 3 · 실패 1
  test_integrity.CompatibilityTest / RealRepositoryTest  오류 1 · 실패 1
```

정리하면 이렇다.

| # | 결합 지점 | 정본 | 제거 시 결과 | 계획 §4에 있는가 |
|---:|---|---|---|:---:|
| 1 | 호환성 선언의 존재 검증 | `docs/COMPATIBILITY.md` → `declarations.py` | `verify` exit 2 | **있음** |
| 2 | 모듈 계층 배정 | `docs/ARCHITECTURE.md`의 `core-module-layers:v1`이 L7 파일 11개를 열거 | `layer-boundaries` 11건 | 없음 |
| 3 | 문서 링크 | `docs/EXPERIMENTAL.md`(4) · `docs/KERNEL_SCOPE.md`(2)가 L7 계약 문서를 직접 링크 | `markdown-links` 6건 | 없음 |
| 4 | 테스트 배치 | L7 테스트 6파일이 `core/tests/`에 있음 | `regression-tests` 실패 | 없음 |

계획 §4의 작업 범위에 다음 세 줄을 추가해야 게이트가 성립한다.

- **모듈 계층**: `core-module-layers:v1`에서 L7 배정을 선택적으로 해석한다. 선언된 L7 파일이 없으면 위반이 아니라 `not_applicable`로 처리하고, 일부만 있으면 §4가 이미 정의한 "손상된 설치"로 `fail`한다. 이 규칙은 계획이 §4에서 세운 3상태 모델과 그대로 일치하므로 새 개념이 아니다.
- **문서 링크**: L7 계약 문서 참조를 Kernel 문서에서 제거하거나, L7 부재 시 허용되는 참조로 선언한다. `EXPERIMENTAL.md`가 실험 기능의 격리를 규정하는 문서이면서 실험 구현 파일에 직접 의존하는 현재 구조 자체가 격리 위반이다.
- **테스트 배치**: L7 테스트 6파일을 `experimental/tests/`로 옮기고 Kernel 회귀 실행에서 분리하거나, 최소한 `experimental` import 실패 시 `skipUnless`로 건너뛰게 한다. 옮기는 쪽이 §3.2("물리적으로 제거할 수 있는 L7")와 일관된다.

이 셋을 넣지 않으면 1단계는 "게이트는 통과했는데 L7은 여전히 제거 불가"로 끝난다.

---

## 4. 정의가 비어 있는 성공 게이트

### 4.1 §5 — "관련 정책과 두 스킬이 같은 승인 모드를 산출한다"

**무엇으로 판정하는지가 없다.** 스킬은 자연어이고 `같은 승인 모드를 산출한다`는 실행 결과가 아니다. 이대로 두면 판정이 사람의 읽기에 남고, 그것은 게이트가 아니다.

이 저장소에는 이미 같은 문제를 푼 패턴이 있다. `core/tests/fixtures/rule-routing-intents-v1.json`과 `extension/tests/fixtures/rule-routing-intents-v1.json`이 발화·`prior_owners`·`expected_owners`·`forbidden_owners`를 `selection_contract: exact`로 고정하고, 테스트는 **의미 판정이 아니라 fixture의 유효성**만 검사한다.

승인 모드에도 같은 구조를 권한다.

- `approval-mode-intents-v1.json`: 발화(`끝까지 진행`, `제목만 골라줘`, `썸네일은 내가 승인할게` 등)와 기대 `approval_mode`를 짝지운다.
- 정본은 `PROJECT_RULES.md` 한 곳이고, fixture의 각 case는 정본의 어느 조항에서 나오는지 참조한다.
- 검사 1: 두 SKILL.md가 승인 조건을 **독자적으로 서술하지 않는다**(정본 링크 외에 `delegated_by_user` / `review_gated`의 트리거 조건 문장을 포함하지 않는다).
- 검사 2: fixture의 모든 case가 정본 조항으로 도달 가능하다.
- 검사 3: `supersedes`류의 권위 상승 문장이 스킬에 없다.

§5 성공 게이트의 마지막 줄("정책 충돌 또는 스킬의 독자적인 권위 상승 문장을 주입하면 검사가 실패한다")은 검사 1·3의 결함 주입 테스트로 그대로 구현된다. 실제 에이전트의 자연어 해석은 이 검사가 소유하지 않으며, 그 사실을 게이트 설명에 명시해야 `core/docs/VERIFICATION.md` §6의 확대 보고 금지를 지킨다.

### 4.2 §6 — "선언된 최소 Python 버전에서 실제 Core gate를 실행하는 검증 경로"

**3.10이 없는 개발 환경에서 이 단계가 무엇으로 판정되는지가 없다.** 여기서 실수하면 이 프로젝트가 이미 한 번 고친 결함이 그대로 재발한다.

이전 진단의 H1은 환경변수 하나로 필수 테스트 단계가 `not_applicable`이 되어 게이트가 통과하던 문제였고, 그것은 수정됐다. 3.10 실행 경로를 "인터프리터가 없으면 건너뛴다"로 만들면 같은 세탁이 다시 생긴다.

게이트 정의에 다음을 명시할 것을 권한다.

- 선언된 `python_min` 실행 결과는 `pass` / `fail` / `not_run` 세 값만 갖는다. **`not_applicable`을 쓰지 않는다.**
- 해당 인터프리터가 없으면 `not_run`이며, `core/docs/VERIFICATION.md` §2에 따라 전체 실패다.
- 따라서 4단계의 `로컬 구현 완료` 판정에는 3.10 인터프리터가 **실제로 있는 환경 1회 실행**이 필요하다. 없으면 `로컬 구현 완료`가 아니라 `최소 버전 미검증`으로 보고한다.

§7 작업 범위의 "Python 3.10과 현재 Python에서 약속된 범위를 각각 실행한다"에서 `약속된 범위`가 무엇인지도 확정해야 한다. 아래 5.1이 그 이유다.

---

## 5. 계획이 빠뜨린 항목

### 5.1 `scripts/bootstrap.py`가 Python 하한을 상수로 박는다 — 1·3·4단계와 직접 충돌

```python
# scripts/bootstrap.py:48
python_supported = sys.version_info >= (3, 11)
```

```
$ python3 -B scripts/bootstrap.py --json          # Python 3.10.12
ok= False
python= {'status': 'unavailable', 'supported_range': '>=3.11', 'version': '3.10.12'}
```

`scripts/verify.py:164-173`의 최종 `ok`는 `bootstrap["ok"] and bootstrap_payload.get("ok")`를 포함한다. 즉 **1단계가 Core를 3.10에서 완전히 살려내도 Maintainer 통합 게이트는 3.10에서 첫 단계에서 멈춘다.** §7의 "Python 3.10에서 실행한다"는 이 상태로는 성립하지 않는다.

이것은 이름 정리 같은 미화가 아니라 §1 작업 의도의 "선언된 최소 Python 버전에서 Core가 동작한다"를 직접 막는 항목이므로, §9 제외 목록이 아니라 작업 범위에 들어가야 한다. 최소 변경은 `bootstrap.py`가 Core의 `python_min` 선언을 **읽어서** 판정하게 하는 것이다. Core가 이미 `gate._min_python()`에서 같은 일을 하고 있고, `test_gate_reads_minimum_from_declaration_not_constant`가 그 성질을 검사한다. 같은 원칙을 Maintainer에 적용하면 값이 다시 갈라지지 않는다.

Maintainer가 Core보다 높은 하한을 요구해야 한다면(아래 6.2) 그 사실을 값 복제가 아니라 **선언 관계**로 표현해야 한다.

### 5.2 절단된 stdout을 JSON으로 파싱한다

```python
# scripts/verify.py:57      표시용 절단
"stdout": completed.stdout[-2000:],
# scripts/verify.py:141     그 절단본을 파싱
bootstrap_payload = json.loads(bootstrap["stdout"])
```

현재 bootstrap 출력은 760자라 발현하지 않는다. 항목이 늘어 2000자를 넘는 순간 `invalid_json`으로 오진단되고, 그 오진단은 §6이 없애려는 "실패 원인을 잘못 지목하는 게이트"에 정확히 해당한다. 3단계 작업 범위에 한 줄로 흡수하면 된다.

### 5.3 Node 지원 범위가 4개 파일에 중복 선언된다

`>=20 <22`가 `package.json`(engines), `pyproject.toml`(`[tool.project-foundation]`), `bootstrap.py`(문자열 3회), `node_verify.mjs`(비교식)에 각각 있다. 5.1과 같은 종류의 결함이므로 함께 정리하거나, 함께 정리하지 않기로 §9에 **명시적으로** 넣는 편이 낫다. 지금은 제외 목록에도 작업 범위에도 없어 다음 세션에서 다시 논의 대상이 된다.

---

## 6. 결정이 필요한 설계 질문

### 6.1 Maintainer 필수 의존성 선언을 어디에 두는가 — 계약 세대 영향 있음

§5는 "기계 판독 선언을 둔다"고만 하고 위치를 정하지 않는다. 이것은 `core/docs/COMPATIBILITY.md` §4의 "선언 schema 변경 = 비호환 변경"에 걸릴 수 있는 결정이다.

실제로 확인해 봤다. 현재 `consumer_contract()` 파서는 **미지 key를 거부하지 않는다.**

```
소비 계약 블록에 "required_core_capabilities": {"shared_data": 1} 주입
$ core_check --core-root core --consumer-root . verify
ok= True | findings= 없음
```

따라서 다음 형태를 권한다.

- `agent-core-consumer:v1` 블록에 **선택 key** `required_core_capabilities`를 추가한다. 없으면 요구 없음이다.
- 이는 "결과 필드 추가" 계열의 **호환 변경**이므로 `contract_version` 상승이 필요 없고, 기존 Host 저장소는 아무 영향을 받지 않는다. §3.4("일반 Host는 `shared_data` 없이도 사용")가 구조로 보장된다.
- 다만 이 key를 `maintainer` 역할에서 **필수**로 만들면 그 순간 schema 조임이 되어 비호환 변경이 된다. 그렇게 하지 않기를 권한다.

§5 작업 범위에 "선택 key로 두며 `contract_version`을 올리지 않는다"를 명시하면 나중에 이 판단을 다시 하지 않아도 된다.

### 6.2 Maintainer의 최소 Python을 3.11로 유지할 것인가

§3.1은 "Core Kernel의 최소 Python은 3.10"이라고만 정하고 Maintainer는 언급하지 않는다. `pyproject.toml`은 `requires-python = ">=3.11"`이다. 두 값이 다른 것 자체는 정당할 수 있다 — Core는 배포되는 커널이고 Maintainer는 개발 저장소다.

정해야 할 것은 값이 아니라 **표현 방식**이다.

- 유지한다면: `pyproject.toml`을 Maintainer 하한의 정본으로 두고, `bootstrap.py`는 그 값과 Core 선언을 각각 읽어 "Core 하한 3.10, Maintainer 하한 3.11"을 구분해 보고한다. 3.10에서 Core 게이트만 실행하는 경로가 열려야 §6의 최소 버전 검증이 성립한다.
- 낮춘다면: `pyproject.toml`을 `>=3.10`으로 내리고 bootstrap이 Core 선언을 그대로 따른다. 이쪽이 단순하지만 Maintainer 전용 도구가 3.11 기능을 쓰게 되면 다시 갈라진다.

어느 쪽이든 §3에 결정으로 적어야 5.1의 수정 방향이 확정된다.

### 6.3 복구 지점을 언제 확보하는가 — 순서에 대한 유일한 이견

계획은 push를 §8로 완전히 미룬다. 검증되지 않은 작업을 올리지 않는다는 원칙으로서는 옳다. 다만 현재 사실은 이렇다.

```
부모 브랜치 codex/agent-core-integration  → upstream 없음
core gitlink cfbd7e2                      → 어떤 원격 브랜치에도 없음
                                             로컬 codex/legacy-rule-absorption 단일 사본
```

**이미 검증을 마친 후보 `cfbd7e2`조차 이 PC 한 곳에만 있다.** 여기서 1~4단계를 더 쌓으면 단일 실패 지점 위에 네 단계를 더 올리는 것이 된다. `core/PROJECT_RULES.md` §10은 "복구 지점은 검증된 Git commit이 소유하며 저장소 안에 백업 사본을 만들지 않는다"고 규정하는데, 로컬 단일 사본은 그 조문이 뜻하는 복구 지점이 아니다.

push 승인 없이 이 위험만 낮추는 방법을 권한다.

- 1단계 시작 전에 Core와 Maintainer의 현재 후보를 **저장소 밖 경로**로 `git bundle` 한다. 저장소 안에 사본을 만들지 않으므로 §10 조문과 충돌하지 않고, 원격 게시도 아니므로 §3.6과도 충돌하지 않는다.
- 이 항목을 §4 앞의 0단계로 넣고, 성공 게이트는 "번들에서 clone해 현재 후보가 복원된다" 한 줄이면 충분하다.

§8을 뒤로 미루는 결정 자체에는 동의한다. 바꾸자는 것은 push 시점이 아니라 **복구 지점의 존재 시점**이다.

---

## 7. 종료 규칙(§10)에 대한 의견

여섯 조건은 적절하고, 특히 4번("미검증 항목은 실패나 성공으로 과장하지 않고 범위와 이유를 기록했다")이 이 프로젝트에서 가장 자주 깨지던 지점을 정확히 막는다.

한 줄만 보강하기를 권한다.

> 7. 각 단계의 성공 게이트는 실행한 검사 목록과 함께 기록하며, `not_run`이 하나라도 있으면 그 단계는 통과가 아니다.

지금 §10은 "성공 게이트가 통과했다"를 조건으로 두는데, 4.2에서 본 것처럼 **무엇이 통과로 계산되는가**가 게이트마다 다르게 해석될 여지가 남아 있다. 이 한 줄이 그 여지를 닫는다.

---

## 8. 권장 반영 순서

계획 구조를 바꾸지 않고 추가·확정만 하는 최소 편집이다.

| 순서 | 대상 | 편집 |
|---:|---|---|
| 1 | §3 | 6.1(선택 key, `contract_version` 유지)과 6.2(Maintainer 하한)를 고정된 설계 결정으로 추가 |
| 2 | §4 앞 | 0단계 신설 — 저장소 밖 `git bundle` 복구 지점 (6.3) |
| 3 | §4 작업 범위 | 모듈 계층·문서 링크·테스트 배치 세 결합 추가 (§3) |
| 4 | §5 | 승인 모드 fixture 검사 방식 확정 (4.1) |
| 5 | §6 | `not_run` 규칙 명시 (4.2), `bootstrap.py` 선언 읽기 (5.1), 절단 파싱 (5.2) |
| 6 | §9 | node 범위 중복(5.3)을 제외로 확정하거나 §6으로 이동 |
| 7 | §10 | 7번 조건 추가 |

---

## 9. 이번 검토에서 실행한 검사

| 검사 | 결과 |
|---|---|
| `declared_compatibility` 존재 요구 범위 확인 | entry_module·`__main__.py`·request/result_schema·schemas 전부 요구 — 계획 진단 정확 |
| 3.10 Core 회귀 테스트 | 111종 / 실패 1 · 오류 8 |
| `datetime.UTC` 주입(3.11+ 모사) 회귀 테스트 | 167종 / 실패 1 · 오류 3 — 잔여 실패는 하위 프로세스 격리 때문 |
| 1단계 완료 모사 + L7 제거 후 `verify` | findings 17 = `layer-boundaries` 11 · `markdown-links` 6 |
| 같은 조건의 회귀 테스트 | 실패 2 · 오류 9 (L7 테스트 6파일이 `core/tests/`에 잔존) |
| `extension/work` 실측 | 41개, 전부 untracked, 생성 지점 `test_manual_upload_package.py:41-44` |
| 소비 계약 미지 key 주입 | `verify` ok — 선택 key 추가는 호환 변경 |
| `scripts/bootstrap.py` (3.10) | `ok: false` — Maintainer 게이트 3.10 실행 불가 |

## 10. 실행하지 않은 검사

- **Python 3.11 이상에서의 실제 실행.** 이 환경에 3.10만 있어 shim 모사로 대체했다. 계획 §1의 3.12 통과 주장은 반증되지 않았고 증명되지도 않았다.
- `scripts/verify.py` 전체와 `scripts/clone_conformance.py` — Node 부재와 Windows 전용 경로 처리로 이 환경에서 유효하지 않다.
- 원격 fetch·push 권한, 실제 `clone --recurse-submodules`.
- 보호 경로(`inputs`, `outputs`, `extension/inputs`, `extension/outputs`) — 계약상 열거·읽기하지 않았다.
- 두 스킬의 실제 자연어 해석 동작 — 4.1의 fixture 검사도 이것을 소유하지 않는다.

이 문서는 현재 checkout 수준의 검토이며 계획의 구현 결과를 판정하지 않는다.
