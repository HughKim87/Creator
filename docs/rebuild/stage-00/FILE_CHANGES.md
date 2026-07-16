# Stage 00 파일 변경 목록

- 역할: 이번 정정의 읽기·쓰기 범위와 파일 책임 기록.
- 읽는 시점: diff 검토 또는 후속 단계 인계 시.
- 보존 조건: Stage 00 보고서와 함께 유지.

## 1. 운영 규칙과 라우팅

| 경로 | 변경 | 역할 |
|---|---|---|
| `AGENTS.md` | 신규 | 9줄 최소 시작 라우터 |
| `PROJECT_RULES.md` | 신규 | 단일 운영 규칙·사용자 데이터 경계 정본 |
| `SESSION_HANDOFF.md` | 전면 정리 | 최신 재개 상태와 다음 행동만 유지 |
| `.gitignore` | 수정 | 어느 깊이의 사용자 데이터 디렉터리도 Git 제외 |

## 2. 실행 계약

| 경로 | 변경 | 역할 |
|---|---|---|
| `docs/rebuild/AGENT_EXECUTION_PLAN.md` | 수정·이동 | 데이터 경계 정본 참조와 저장 지표 수정 |
| `docs/rebuild/stage-00/AGENT_STAGE_00_BASELINE_FREEZE.md` | 수정·이동 | Git 추적 프레임워크 전용 인벤토리 계약 |
| `docs/rebuild/stage-01/AGENT_STAGE_01_TRUSTED_FOUNDATION.md` | 수정·이동 | 자동 검사·부정 테스트·훅 집행 요구 |
| `docs/rebuild/stage-03/AGENT_STAGE_03_SINGLE_STATE_MODEL.md` | 수정·이동 | 외부 작업 공간과 저장소 경계 명확화 |
| `docs/rebuild/research/PROJECT_STRUCTURE_RESEARCH.md` | 수정·이동 | 사용자 데이터 파일별 측정값 제거 |

## 3. Stage 00 보고서

- `STAGE_REPORT.md`, `REPOSITORY_BASELINE.md`, `COMMAND_RESULTS.md`,
  `RISKS_AND_ROLLBACK.md`, `MIGRATION_CATALOG.md`: schema v2 기준으로 정정
- `GOLDEN_FIXTURE_PLAN.md`: 실제 값은 외부 승인 작업 공간에만 두도록 명시
- `BASELINE_TESTS.md`, `KNOWN_FAILURES.md`: 실제 테스트·종료코드·정책상 미실행 결과 반영
- `BACKUP_MANIFEST.json`: Git 추적 프레임워크 86개만 포함

## 4. Stage 00 증거

- `evidence/inventory_generate_manifest.ps1`: 재귀 열거 제거, Git 추적 목록과 선차단 사용
- pass 1/2, pre/post snapshot, repository paths: schema v2로 제자리 재생성
- `inventory_validation.txt`, `final_validation.txt`: 최종 검증 결과로 갱신
- `evidence/behavior_execution_results.txt`: 45개 통과, 29개 정책상 미실행,
  자식 `7`의 래퍼 `0` 왜곡 기록
- 실행 전 pending 상태 표식은 실제 결과 파일로 대체되어 제거
- 동일한 매니페스트 전체 JSON 4개와 중복 경로 TSV는 정본·결정성 해시로 통합해 제거
- `.gitignore`: 단계 기록 전체 제외를 제거하고 임시 worktree·runtime은 저장소 밖에서 관리

## 5. 보호 결과

- `backup/` 변경 0
- 사용자 데이터 파일 자체 변경 0
- 실제 사용자 데이터 식별자·파일별 메타데이터가 활성 문서·보고서·증거에 남은 수 0
- commit/tag/push 0
- detached legacy worktree 1개는 실행·독립 검증 후 제거
- 빈 runtime 임시 폴더와 worktree 부모 폴더 제거
- 중복 백업 파일 0

Stage 00 보고서·재현 가능한 작은 증거는 프로젝트의 순차 구축 기록으로 Git 추적한다.
