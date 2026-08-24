# 저장소 역할 분리 단계 0 설계

- 목적: 현재 Creator 부모와 Core의 기준선을 측정하고, 보호 경로를 제외한 파일의 최종 소유자를 확정할 근거를 만든다.
- 읽는 시점: 저장소 역할 분리 단계 0을 실행·검토·재개할 때.
- 책임: 작업 에이전트가 현재 파일과 의존 관계를 감사하고 사용자가 정확한 분리표를 확인한다.
- 상태: 활성 단계 설계. 단계 0 결과 확인 전에는 단계 1로 전환하지 않는다.
- 관련 권위: `REPOSITORY_ROLE_SEPARATION_DESIGN.md`, `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`.
- 문서 분류: `phase-design`
- phase ID: `STAGE_0`
- lifecycle: `passed`
- optional evidence owner: 없음. 이 문서와 감사 결과 외 자료는 `startup-required 아님`.
- 첫 다음 행동: 보호 경로를 제외한 부모·Core Git 기준선과 추적 파일 책임을 측정한다.
- 종료 조건: 분리표의 모든 이동·삭제 후보에 현재 owner, inbound dependency, 대상 owner, 복구 commit이 있고 사용자가 이를 확인하면 완료 설계로 전환한다.

## 원하는 결과

- 부모와 Core의 branch, HEAD, gitlink, remote, 작업 트리 상태를 현재 실행 결과로 기록한다.
- 보호 경로를 선제 제외한 추적 파일을 `Maintainer 이전`, `Creator 유지`, `저장소별 재작성`, `제외`로 분류한다.
- 새 Maintainer 최소 파일 집합과 Creator에서 나중에 제거할 정확한 후보를 제시한다.
- 혼합 파일은 양쪽 저장소에서 남길 책임을 분리해 설명한다.

## 허용 행동

- Git metadata와 보호 경로를 제외한 추적 파일·문서·코드의 읽기와 검색
- 단계 0 설계, 감사 결과, `SESSION_HANDOFF.md`의 현재 상태 갱신
- 문서 구조·링크·크기와 분류 근거에 한정한 검사

## 제외 범위

- 파일 이동·삭제·이름 변경과 기존 구현 수정
- 새 Git 저장소·폴더·원격 생성
- Core 변경, commit, push, main·태그·릴리스 조작
- 실제 영상 사용 테스트와 전체 회귀
- `inputs`, `outputs`, `extension/inputs`, `extension/outputs`의 열거·읽기·검색

## Entry gate

- 전체 설계 fingerprint가 `SESSION_HANDOFF.md`와 일치한다.
- 사용자 지시로 단계 진행이 승인됐다.
- 보호 경로와 외부 효과가 제외 범위에 남아 있다.

## 감사 방법

1. 부모와 Core의 Git 기준선을 각각 읽는다.
2. 보호 경로를 pathspec과 glob에서 선제 제외하고 부모 추적 파일을 수집한다.
3. 루트, `scripts/`, `extension/tests/`, dependency 선언에서 import·subprocess·route·문서 링크를 추적한다.
4. 각 후보를 현재 owner, inbound dependency, 대상 owner, 처리, 복구 commit으로 기록한다.
5. 분리표의 경로가 실제 추적 파일과 일치하는지 직접 대조한다.

## 분류 기준

| 판정 | 의미 |
|---|---|
| Maintainer 이전 | Core 유지보수에 필요하고 영상 Host 운영에는 필요하지 않다 |
| Creator 유지 | 영상 제작·도메인 운영에 필요하고 Maintainer에는 포함하지 않는다 |
| 저장소별 재작성 | 같은 파일명이 필요하지만 정책·상태·진입 책임이 역할마다 다르다 |
| 제외 | Core submodule 자체이거나 보호 경로·생성물 등 이번 분리 대상이 아니다 |

## Slice gates

- 기준선 측정: `pass`는 부모·Core의 실제 Git 결과가 모두 확보된 상태다.
- 보호 경계: `pass`는 모든 재귀 목록·검색 명령이 보호 경로를 선제 제외한 상태다.
- 분리표 완전성: `pass`는 모든 이동·삭제 후보에 다섯 필드가 있고 실제 경로가 확인된 상태다.
- 의존 근거: `pass`는 혼합 파일과 실행기의 inbound dependency가 확인된 상태다.

## Exit gate

- 단계 0 결과를 사용자에게 보고한다.
- 정확한 분리표를 사용자가 확인한다.
- 다음 단계 전환: 사용자 확인 전에는 `not_run`이다.

## 감사 결과

### 기준선

| 대상 | 측정 결과 | 원격 도달성 | 작업 트리 |
|---|---|---|---|
| Creator 부모 | branch `codex/agent-core-integration`, HEAD `69257b3` | 같은 SHA의 원격 branch 확인 | 이번 설계·상태 문서만 변경 |
| Core | branch `codex/legacy-rule-absorption`, HEAD·gitlink `e1c7c63` | 같은 SHA의 원격 branch 확인 | clean |

### 정확한 분리표

| 현재 경로 | 현재 owner·inbound dependency | 대상 owner | 처리 | 복구 commit |
|---|---|---|---|---|
| `.agents/skills/**` | Creator; 실제 영상·리서치·브라우저 절차 | Creator | 유지, Maintainer에 포함하지 않음 | `69257b3` |
| `.obsidian/app.json` | Creator; `extension_registry.py`, README | Creator | 유지 | `69257b3` |
| `extension/config/**`, `docs/**`, `examples/**`, `reports/**`, `rules/**`, `schemas/**`, `src/**`, `work/.gitkeep` | Creator; Extension 문서·Runtime·도메인 import | Creator | 유지 | `69257b3` |
| `extension/tests/**` 중 아래 세 파일 외 전부 | Creator; Extension source·Skills·도메인 계약 | Creator | 유지 | `69257b3` |
| `extension/tests/test_claude_entrypoint.py` | 혼합; 루트 `CLAUDE.md` 계약 | 양쪽 Consumer | Creator 유지, Maintainer용 대응 test 작성 | `69257b3` |
| `extension/tests/test_staged_design_routing.py` | 혼합; 루트 설계·handoff route | 양쪽 Consumer | Creator 유지, Maintainer용 대응 test 작성 | `69257b3` |
| `extension/tests/test_verification_pipeline.py` | 혼합; `verify.py`, inventory, clone conformance | 양쪽 Consumer | 역할별 pipeline test로 분리·재작성 | `69257b3` |
| `AGENTS.md`, `CLAUDE.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, `README.md` | 혼합; 각 Consumer의 진입·정책·상태·개요 | 각 저장소 | 역할별 재작성 | `69257b3` |
| `.gitmodules`, Core gitlink | 혼합; Core 공개 계약과 revision | 각 저장소 | Creator 유지, Maintainer에 독립 submodule 연결 | `69257b3` |
| `.gitattributes` | 혼합; 저장소 text·binary 정책 | 각 저장소 | Creator 유지, Maintainer 최소본 작성 | `69257b3` |
| `.gitignore` | Creator 중심; 보호 경로·Extension Runtime·생성 데이터 | 각 저장소 | Creator 유지, Maintainer용 최소본 별도 작성 | `69257b3` |
| `package.json`, `scripts/node_verify.mjs` | Creator; Node Runtime gate | Creator | 유지, Maintainer에 포함하지 않음 | `69257b3` |
| `pyproject.toml` | 혼합; Python 범위와 Creator thumbnail capability | 각 저장소 | 역할별 dependency 선언으로 재작성 | `69257b3` |
| `scripts/export_conformance.py` | Creator; `extension/src/domain_conformance.py`, `game_pilot.py` | Creator | 유지 | `69257b3` |
| `scripts/bootstrap.py` | 혼합; Core Python과 Creator Node·Pillow·browser 상태 | 각 저장소 | Maintainer 최소 preflight와 Creator preflight로 분리·재작성 | `69257b3` |
| `scripts/run_test_inventory.py` | 혼합; Core·shared-data·Extension test inventory | 각 저장소 | Maintainer inventory와 Creator inventory로 분리·재작성 | `69257b3` |
| `scripts/verify.py` | 혼합; Core gate·Maintainer Runtime·Extension registry·모든 test | 각 저장소 | Maintainer gate와 Creator Host gate로 분리·재작성 | `69257b3` |
| `scripts/clone_conformance.py` | Maintainer; `verify.py`와 pipeline test가 clean-clone 재현에 사용 | Maintainer | 새 Maintainer 검증 뒤 Creator에서 제거 | `69257b3` |
| `core/` | 독립 Agent-Core submodule | Agent-Core | 이동·복사하지 않고 양쪽 Consumer가 gitlink로 참조 | `e1c7c63` |
| 현재 분리 설계·단계 설계 | 한시 migration owner; handoff가 route | 분리 작업 | 완료 전 유지, 최종 상태 흡수 뒤 종료 | `not_applicable` |

### 새 Maintainer 최소 집합

- 독립 저장소 기본: `.gitattributes`, `.gitignore`, `.gitmodules`, Core gitlink.
- 진입과 상태: `AGENTS.md`, `CLAUDE.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, `README.md`.
- Runtime과 gate: `pyproject.toml`, `scripts/bootstrap.py`, `scripts/run_test_inventory.py`, `scripts/verify.py`, `scripts/clone_conformance.py`의 Maintainer 전용 구현.
- Consumer 회귀: 진입 route, 단계 설계 route, Maintainer verification pipeline 대응 tests.
- 포함 금지: `.agents/skills`, `.obsidian`, `extension/`, `package.json`, Node gate, 영상·YouTube·게임 참조.

### 게이트 판정

- 기준선 측정: `pass`.
- 보호 경계: `pass`; 모든 목록·검색에서 네 보호 경로를 선제 제외했다.
- 분리표 완전성: `pass`; 경로 제거 후보는 `scripts/clone_conformance.py` 하나이며 owner·inbound dependency·대상 owner·복구 commit을 확인했다.
- 의존 근거: `pass`; 혼합 실행기의 직접 import·subprocess·test reference를 확인했다.
- 사용자 확인과 단계 1 전환: `pass`; 사용자가 분리표 보고 뒤 진행을 지시했다.

## 복구

단계 0은 유지 문서만 추가·갱신한다. 오류가 있으면 구현으로 이어가지 않고 문서의 잘못된 판정만 교정한다. 저장소 내부 백업은 만들지 않으며 기존 Git commit을 복구 기준으로 사용한다.
