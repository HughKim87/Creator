# 저장소 기준선

- 역할: Stage 00의 Git 추적 프레임워크 기준선.
- 읽는 시점: Stage 00 검증 또는 이후 이식 비교 시.
- 보존 조건: 신규 구조 전환이 안정화될 때까지.
- 데이터 경계 정본: `PROJECT_RULES.md`의 `User Data Boundary`.

## 1. 범위

기준선은 `git ls-files -- backup`이 반환한 추적 파일에서 금지 경로를 먼저 제외한 뒤
작성했다. ignored·미추적 파일시스템은 재귀 열거하지 않았고 사용자 데이터의 존재 여부,
경로, 이름, 수, 크기, 해시를 수집하거나 보고하지 않았다.

## 2. Git 기준

| 항목 | 값 |
|---|---|
| 브랜치 | `feature/refactoring` |
| HEAD | `dc7f18b4715bff99b806872f742bf1602e2d0418` |
| `core.hooksPath` | `.githooks` |
| `backup/` worktree diff | 0 |
| `backup/` index diff | 0 |
| 원격 주소·원격 CI | 수집·확인하지 않음 |

## 3. 추적 프레임워크 매니페스트

| 역할 | 파일 수 |
|---|---:|
| code | 30 |
| test | 10 |
| contract | 22 |
| doc | 24 |
| 합계 | 86 |

- 86개 경로는 모두 고유하고 SHA-256이 존재한다.
- 총 프레임워크 파일 크기는 647,725바이트다.
- 매니페스트 역할은 code/test/contract/doc만 허용한다.
- `BACKUP_MANIFEST.json` schema version은 2다.

## 4. 결정성

동일한 Git 추적 입력에서 매니페스트를 두 번 생성했다.

- pass 1 SHA-256: `87d9bfe3938c42b04bcf1234bc48dce4c0823f44277ed74e7938b6d2546c4f54`
- pass 2 SHA-256: `87d9bfe3938c42b04bcf1234bc48dce4c0823f44277ed74e7938b6d2546c4f54`
- 전체 JSON 바이트 일치: `True`

## 5. 현재 훅과 CI

### 확인한 사실

- 현재 pre-commit은 루트 검사기 또는 Python이 없으면 종료 코드 0으로 끝난다.
- 현재 CI는 아직 루트에 없는 검사기와 테스트 경로를 참조한다.

### 제한된 추론

- 로컬 훅은 fail-closed 기준을 충족하지 않는다.
- 현재 CI 명령은 체크아웃된 루트에서 실패할 것으로 예상되지만 원격 실행은 확인하지
  않았다.

## 6. 증거

- `BACKUP_MANIFEST.json`: 활성 프레임워크 매니페스트
- `evidence/inventory_generate_manifest.ps1`: Git 추적 목록 기반 생성기
- `evidence/inventory_manifest_determinism.txt`: 두 번의 전체 JSON 해시와 일치 판정
- `BACKUP_MANIFEST.json` 하나만 해시 기준 정본으로 유지하며 동일 JSON 복제본은 저장하지 않음
- `evidence/inventory_pre_git_state.txt`, `inventory_post_git_state.txt`: Git 무변경 증거

구체계 테스트 실행 결과는 이 문서가 아니라 `BASELINE_TESTS.md`에서 관리한다.
