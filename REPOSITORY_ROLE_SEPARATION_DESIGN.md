# Creator Host와 Agent Core Maintainer 분리 설계

- 목적: 현재 `creator.git`에 섞인 영상 제작 Host와 Agent Core Maintainer 책임을 두 소비 저장소로 안전하게 분리한다.
- 읽는 시점: 분리 작업을 승인·구현·재개하거나 저장소 역할과 완료 수준을 판정할 때.
- 책임: 작업 에이전트가 단계·의존 순서·게이트를 유지하고, 사용자가 역할 의미·삭제·폴더 이동·원격 생성·push를 승인한다.
- 상태: 검토 대기 전체 설계. 구현 승인을 뜻하지 않는다.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, `core/docs/CONSUMER_GUIDE.md`, `core/docs/VERIFICATION.md`.
- 문서 분류: `overall-design`
- 활성 단계: [단계 5 — 로컬 폴더 전환](REPOSITORY_ROLE_SEPARATION_STAGE_5.md)
- 종료 조건: 두 로컬 저장소의 역할 분리와 선택된 원격 반영이 끝나면 완료 설계로 전환하고, 완료 과정은 Git 이력이 소유한다.

---

## 1. 원하는 최종 구조

| 저장소 | 역할 | Core 권한 | 소유 내용 |
|---|---|---|---|
| `Agent-Core` | 도메인 중립 Core | Maintainer 승인 경로에서만 변경 | 공통 정책·규칙·계약·검증기·선택 기능 |
| `Agent-Core-Maintainer` | Core 유지보수 소비 저장소 | fetch·승인된 변경·push | Core 변경 정책·현재 상태·검증·게시 절차 |
| `creator.git` | 영상 제작 Host 소비 저장소 | 읽기 전용 | 영상 Extension·Skills·도메인 정책·작업 상태·입출력 경계 |

Core 코드를 Maintainer에 복사하지 않는다. 두 소비 저장소는 같은 `Agent-Core` 원격을 submodule로 연결하고 각자 gitlink를 고정한다.

## 2. 현재 문제

- 원격 이름과 영상 기능은 `creator.git`이지만 소비 계약은 `maintainer`다.
- 루트 정책·상태·검증기가 Core 유지보수와 영상 제작 책임을 함께 가진다.
- `extension/`과 `.agents/skills/`는 실제 영상 작업 기능이지만 Core 검증의 통합 fixture 역할도 겸한다.
- 현재 로컬 폴더 이름이 `Agent-Core-Maintainer`라 새 전용 Maintainer의 최종 경로와 충돌한다.

이 설계는 기존 Core 개선 이력을 폐기하지 않고 책임만 분리한다.

## 3. 고정 결정

1. 현재 `creator.git`은 최종적으로 `consumer_role: host`가 된다.
2. 새 Maintainer는 초기에는 `D:\AI Agent\Sandbox\Agent-Core-Maintainer-New`에 로컬로 구성한다.
3. 새 Maintainer가 검증되기 전에는 Creator에서 Maintainer 전용 파일을 삭제하지 않는다.
4. 영상 원본·결과 보호 경로는 열거·읽기·이동하지 않는다.
5. Core `e1c7c63`은 분리 기준 후보이며, 분리 과정에서 Core 코드를 변경하지 않는다.
6. 새 Maintainer 원격 저장소 생성과 push는 로컬 결과 보고 뒤 별도 승인으로 진행한다.
7. Creator의 실제 영상 사용성은 사용자가 직접 작업하며 확인하고 자동 Host 테스트 단계로 만들지 않는다.
8. 현재 저장소와 새 Maintainer의 폴더 이름 교환은 모든 로컬 gate와 커밋이 끝난 뒤 마지막에 수행한다.

## 4. 제외 범위

- `inputs/`, `outputs/`, `extension/inputs/`, `extension/outputs/` 접근·복제·이동
- 영상 Extension과 Skills의 기능 재설계
- Core 공개 계약·version 변경
- main 병합, 태그, 릴리스
- 실제 영상 프로젝트를 이용한 자동 Host 테스트
- 완료 점수를 높이기 위한 무관한 문서·형식 정리

## 5. 책임 분류 기준

### Maintainer 전용

- Core 변경 승인·검증·복구·push 상태
- Core 최소 Runtime, 선택 기능 설치 상태, Consumer 호환성 검증
- Core 후보 commit의 clean-clone·submodule 도달성 확인
- Maintainer 역할의 정책·핸드오프·검증 실행기

### Creator 전용

- `extension/`의 영상·YouTube·게임 도메인 코드와 계약
- `.agents/skills/`의 실제 제작 절차
- Creator 승인 정책과 영상 작업 상태
- 영상 관련 package·runtime·artifact 검증
- 보호 경로 선언과 실제 입출력 수명주기

### 저장소별 재작성

- `AGENTS.md`, `CLAUDE.md`
- `PROJECT_RULES.md`
- `SESSION_HANDOFF.md`
- README와 bootstrap·verify 진입점
- dependency 선언과 테스트 inventory

파일 이름만으로 이동하지 않는다. import·route·subprocess·문서 링크·테스트 소유자를 함께 추적해 판정한다.

## 6. 단계 0 — 기준선과 파일 책임 감사

### 작업

- Creator 부모·Core의 branch, HEAD, gitlink, 원격 도달성과 clean 상태를 측정한다.
- 루트, `scripts/`, `extension/tests/`, dependency 선언의 책임을 파일별로 분류한다.
- 혼합 파일은 Maintainer 부분, Creator 부분, 공용 공개 계약 참조로 분해한다.
- 새 Maintainer에 필요한 최소 파일 집합과 Creator에서 제거할 정확한 경로를 보고한다.
- 승인 시점의 설계 fingerprint를 `SESSION_HANDOFF.md`에 기록한다.

### 게이트

- 모든 이동·삭제 후보에 현재 owner, inbound dependency, 대상 owner, 복구 commit이 있다.
- 보호 경로는 조사 범위에서 선제 제외된다.
- 정확한 분리표를 사용자가 확인하기 전에는 단계 1을 시작하지 않는다.

## 7. 단계 1 — 새 Maintainer 로컬 후보 구성

### 작업

- `Agent-Core-Maintainer-New`를 독립 Git 저장소로 만든다.
- Core를 submodule로 연결하고 `e1c7c63`을 고정한다.
- `consumer_role: maintainer` 계약과 전용 진입·상태 파일을 만든다.
- 단계 0에서 승인된 Core 전용 검증기·테스트만 이전한다.
- 현재 Creator commit과 Core SHA를 source lineage로 기록한다.
- 영상 Extension·Skills·도메인 정책을 포함하지 않는다.

### 게이트

- Maintainer 정책·상태·진입 계약 구조가 통과한다.
- 영상·YouTube·게임 도메인 import와 route가 0이다.
- Core 자체 gate와 Maintainer 소비 통합 gate가 통과한다.
- 새 저장소가 독립 Git 이력과 clean 작업 트리를 가진다.

## 8. 단계 2 — Maintainer 재현성 확인

### 작업

- 최소 Python에서 Core 범위를 실행한다.
- Maintainer Runtime에서 소비 통합 inventory를 실행한다.
- commit snapshot을 독립 경로에 clone하고 submodule·gate를 확인한다.
- Creator 로컬 경로나 uncommitted 파일에 의존하지 않는지 확인한다.

### 게이트

- Core·Maintainer 필수 검사와 기대 inventory가 모두 `pass`다.
- clean clone이 같은 Core gitlink와 결과를 재현한다.
- Creator 전용 파일 없이 Core 유지보수 작업을 시작·재개할 수 있다.

## 9. 단계 3 — Creator를 Host로 전환

### 작업

- 루트 소비 계약을 `consumer_role: host`로 변경한다.
- Core 변경·push 책임과 Maintainer 현재 상태를 제거한다.
- Core submodule을 읽기 전용 사용 경계로 전환한다.
- README와 `SESSION_HANDOFF.md`를 영상 제작 프로젝트 목적·상태로 복원한다.
- Maintainer에서 검증된 정확한 전용 파일만 Creator 활성 트리에서 제거한다.
- 혼합 검증기는 영상 Host gate와 Creator 도메인 gate로 축소·분리한다.
- `shared_data v1`은 실제 Creator 의존을 확인해 필요한 경우에만 요구한다.

### 게이트

- Host 계약·진입 포인터·상태·rule route가 통과한다.
- Creator에서 Core 수정·push 책임 참조가 0이다.
- 영상 Extension·Skills·도메인 계약의 링크와 관련 회귀가 통과한다.
- 보호 경로와 사용자 산출물에 변화가 없다.

## 10. 단계 4 — 두 저장소 통합 마감

### 작업

- Maintainer와 Creator가 같은 Core 공개 계약만 사용하고 서로를 import하지 않는지 확인한다.
- 두 부모 저장소의 Core gitlink와 `.gitmodules`를 대조한다.
- 각 저장소에서 변경 영향에 맞는 최종 gate를 한 번씩 실행한다.
- 역할별 README·정책·핸드오프가 실제 상태와 일치하도록 갱신한다.

### 게이트

- Maintainer는 Core 유지보수만, Creator는 영상 작업만 소유한다.
- 두 작업 트리가 clean이고 각 완료 commit에서 관련 gate가 통과한다.
- 실제 영상 사용성은 자동 통과로 주장하지 않고 사용자 운영에 남긴다.

## 11. 단계 5 — 로컬 폴더 전환

### 작업

- 실행 중인 세션과 프로세스가 두 저장소를 사용하지 않는 시점에 부모 경로에서 전환한다.
- 현재 폴더를 `Creator`로, 후보 폴더를 `Agent-Core-Maintainer`로 이동한다.
- 두 저장소를 새 경로에서 다시 열고 root·submodule·Git 상태를 확인한다.

### 게이트

- resolved source·target가 모두 `D:\AI Agent\Sandbox`의 승인된 정확한 경로다.
- 대상 경로가 충돌하지 않고 이동 전 두 저장소가 clean이다.
- 새 경로에서 진입 문서와 Core submodule이 정상 해석된다.

폴더 이동은 되돌리기 비용과 현재 작업공간 단절이 있으므로 실행 직전에 정확한 경로를 다시 보고한다.

## 12. 단계 6 — 조건부 원격 반영

### 작업

- 로컬 결과 보고 뒤 승인된 경우에만 `Agent-Core-Maintainer` 원격을 생성한다.
- Maintainer 후보 브랜치를 push하고 실제 원격 clone을 확인한다.
- Creator는 기존 `creator.git` 후보 브랜치에 Host 전환 commit을 push한다.
- 두 원격 clean clone에서 각자 관련 gate를 실행한다.

### 게이트

- Maintainer 원격에는 영상 도메인 파일이 없다.
- Creator 원격에는 Maintainer 변경·push 책임이 없다.
- Core commit이 두 저장소에서 읽을 수 있고 gitlink가 의도한 SHA와 일치한다.
- main·태그·릴리스는 결과 보고 뒤 별도 결정한다.

## 13. 커밋 경계

| 순서 | 저장소 | 논리적 완료 |
|---:|---|---|
| 1 | 새 Maintainer | 최소 독립 구성과 Core 연결 |
| 2 | 새 Maintainer | 검증기·테스트 이전과 재현성 완료 |
| 3 | Creator | Host 소비 계약과 진입·상태 전환 |
| 4 | Creator | Maintainer 전용 파일 제거와 영상 gate 정리 |
| 5 | 각 저장소 | 최종 상태·경로 정합성 마감 |

한 커밋에 두 저장소의 단계를 섞지 않는다. Core에는 분리 목적의 새 commit을 만들지 않는다.

## 14. 복구

- 단계 1·2 실패: 새 후보 저장소만 폐기하고 Creator는 변경하지 않는다.
- 단계 3 실패: Creator의 Host 전환 commit을 완료로 주장하지 않고 마지막 검증 commit으로 복구한다.
- 폴더 이동 실패: 부모 경로에서 원래 이름으로 되돌리고 새 경로의 Git 상태를 확인한다.
- 원격 단계 실패: 로컬 완료를 유지하고 원격 반영 상태만 `fail`로 기록한다.
- 저장소 내부 백업 사본은 만들지 않고 검증된 commit과 기존 원격을 복구 지점으로 사용한다.

## 15. 승인 경계와 다음 진입

이 문서 작성은 구현·삭제·폴더 이동·원격 생성을 승인하지 않는다.

구현 전에 사용자가 확인할 항목은 다음이다.

1. 최종 3저장소 역할 구조
2. 새 Maintainer 임시·최종 로컬 경로
3. 단계 0의 정확한 분리표
4. 단계별 commit 위임
5. 폴더 이동과 원격 생성·push의 개별 승인 시점

승인되면 단계 0만 활성 단계로 전환하고, 그 결과를 다시 보고한 뒤 단계 1로 진행한다.
