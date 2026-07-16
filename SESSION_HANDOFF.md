# 프로젝트 재구축 실행 핸드오프

- 역할: 멀티에이전트 재구축 계획의 현재 상태를 다음 세션에 전달하는 단일 재개 정본
- 상태: 실행 계획 작성·구조 검증 완료, 구현 미착수, Stage 00 착수 승인 대기
- 갱신일: 2026-07-16 23:50 KST
- 현재 브랜치: `feature/refactoring`
- 현재 HEAD: `eba0d74c63977c1507f5cf74e52ac800bcc72776`

## 읽기 순서

1. `SESSION_HANDOFF.md`
2. `AGENT_EXECUTION_PLAN.md`
3. 현재 착수할 단계의 `AGENT_STAGE_XX_*.md`
4. 직전 단계가 완료됐다면 `reports/rebuild/stage-XX/STAGE_REPORT.md`
5. Stage 00~01 조정이 필요할 때만 `PROJECT_STRUCTURE_RESEARCH.md`
6. 이식 대상을 확인할 때만 `backup/`의 관련 코드·테스트·계약

현재 루트에는 `PROJECT_RULES.md`와 `AGENTS.md`가 아직 없다. 이후 생성되면 가장 먼저
읽는다. `backup/PROJECT_RULES.md`, `backup/AGENTS.md`,
`backup/SESSION_HANDOFF.md`는 역사 자료이며 현재 실행 지침이 아니다.

## 현재 목표

반복되는 실패, 거짓 성공, 상태 분산, 개선 후 퇴행을 끊기 위해 구체계를 기준선으로
보존하면서 신규 프레임워크를 단계적으로 재구축한다. 작은 증상 수정이 아니라 실행,
검증, 상태, 승인, 복구, 운영 지표를 하나의 구조로 다시 설계하는 것이 목표다.

현재 요청으로 승인된 범위는 실행 계획 문서와 이 핸드오프 작성까지다. Stage 00의
보고서 생성, 의존성 설치, worktree·태그·커밋·푸시, 실제 구현은 아직 승인되지 않았다.

## 핵심 용어와 결정

- `backup/`: 구체계 전체를 보존한 역사 자료. 읽기 전용이며 신규 runtime 정본이 아님
- Stage 00: 구현 전에 구체계 기준선, 해시, 보존·이식 목록, 골든 비교 기준을 동결하는
  안전 단계
- Stage 01: 기존 `PROJECT_STRUCTURE_RESEARCH.md`가 말한 “0단계 최소 골격”에 대응
- 프레임워크 저장소: 현재 Git 루트. 코드·계약·테스트·규범 문서만 둘 예정
- 외부 작업 공간: 실제 영상 원본, SQLite 상태 DB, 산출물, 생성 상태 뷰를 둘 예정이며
  아직 생성하지 않음
- 상태 정본: Stage 03 이후 프로젝트별 `workflow.sqlite` 하나. JSON·Markdown 상태는
  읽기 전용 생성 뷰
- 전환 상태: `cutover_candidate → provisional_cutover → stabilized`
- 파일럿 모드: legacy 직접 실행인 `direct_shadow`, 또는 사용자 위험 승인을 받은
  `frozen_legacy_baseline`
- Graphify·Obsidian: 핵심 안정성 계층이 아니라 Stage 08의 선택적 측정 파일럿

기존 리서치의 실측 사실은 유지하지만 실행 순서가 충돌하면
`AGENT_EXECUTION_PLAN.md`와 단계별 지시서를 따른다. 리서치가 제안한 최소 골격부터
바로 만들지 말고 반드시 Stage 00을 먼저 통과한다.

## 입력과 근거

| 경로 | 상태 | 역할 |
|---|---|---|
| `AGENT_EXECUTION_PLAN.md` | active, controlling, untracked | Stage 00~08 순서·공통 역할·승인 게이트 |
| `AGENT_STAGE_00_BASELINE_FREEZE.md` | active, pending start, untracked | 첫 착수 단계의 상세 작업 지시서 |
| `AGENT_STAGE_01_TRUSTED_FOUNDATION.md` | active, pending Stage 00 | fail-closed 최소 루트 구축 |
| `AGENT_STAGE_02_DOMAIN_CONTRACTS.md` | active, pending | 도메인 상태·승인 계약 |
| `AGENT_STAGE_03_SINGLE_STATE_MODEL.md` | active, pending | SQLite 단일 상태와 사람 승인 신뢰 경계 |
| `AGENT_STAGE_04_VERTICAL_SLICE_MIGRATION.md` | active, pending | 첫 수직 기능 이식과 artifact 장애 일관 승격 |
| `AGENT_STAGE_05_SHADOW_PILOT.md` | active, pending | 실제 리뷰 렌더·A/V 승인·최소 복구 파일럿 |
| `AGENT_STAGE_06_CUTOVER.md` | active, pending | 가역적 임시 전환과 즉시 롤백 |
| `AGENT_STAGE_07_OPERATIONS_DOCUMENTATION.md` | active, pending | 정기 백업·지표·문서·30일 안정화 |
| `AGENT_STAGE_08_KNOWLEDGE_TOOLS_PILOT.md` | active, optional | Obsidian·Graphify 독립 파일럿 |
| `PROJECT_STRUCTURE_RESEARCH.md` | active evidence, sequence superseded, untracked | 로컬 실측·외부 조사·최소 골격 근거 |
| `backup/gpt/project_blueprint_report_2026-07-16.md` | historical evidence | GPT 구조 진단 |
| `backup/claude/project_improvement_blueprint_2026-07-16.md` | historical evidence | Claude 구조 청사진 |
| `backup/gemini/blueprint_report.md` | historical evidence | Gemini 안정화·효율화 제안 |
| `backup/` | historical, read-only | 기존 프로젝트 전체 |

## 재개 체크포인트

- 브랜치: `feature/refactoring`
- HEAD: `eba0d74` (`기존 파일 백업`)
- 구현 상태: `src/`, `tests/`, `docs/`, 루트 `AGENTS.md`, 루트
  `PROJECT_RULES.md` 모두 아직 없음
- 외부 작업 공간과 실제 상태 DB: 없음
- Stage 보고서: 아직 없음
- 계획 상태: 마스터 1개와 Stage 00~08 지시서 9개 작성 완료
- 첫 미착수 행동: 사용자에게 Stage 00의 읽기·진단과
  `reports/rebuild/stage-00/` 증거 생성 착수 승인을 받기
- Git 상태: 계획 문서와 리서치는 미추적. `SESSION_HANDOFF.md`의 이전 버전은 index에
  추가돼 있고 현재 개정은 working tree에만 있어 최종 확인 결과 `AM` 상태
- 커밋·태그·푸시: 이번 작업에서 수행하지 않음
- `backup/` Git 상태: 변경 0건

## 완료된 작업

1. 기존 프로젝트 전체를 `backup/`으로 이동한 커밋 `eba0d74`를 기준선으로 확인했다.
2. `PROJECT_STRUCTURE_RESEARCH.md`에 로컬 구조와 기존 보고서, 외부 근거를 결합한 최소
   골격 제안을 작성했다.
3. 다른 에이전트들이 분리 수행할 수 있도록 다음 문서를 루트에 작성했다.
   - 공통 역할, 파일 소유권, 표준 작업 패킷, 증거 패키지를 정의한 마스터 계획
   - Stage 00~08 각각의 목적, 사전조건, 허용·금지 범위, 세부 작업, 테스트, 완료 기준,
     중단 조건, 롤백 지시서
4. 세 독립 Agent에게 전체 구조, Stage 00~03, Stage 04~08을 나눠 설계·감사하게 했다.
5. 감사에서 확인된 다음 차단 문제를 문서에 반영했다.
   - DB와 파일을 하나의 원자적 트랜잭션으로 오인한 문제
   - XML만 있고 실제 A/V 리뷰 영상 생성 경로가 없던 문제
   - Stage 06과 07 사이의 백업·복구 순환 의존
   - 실패 DB를 복원 과정에서 잃을 수 있던 문제
   - 원격 CI 미확인과 안정화 완료 상태 혼합
   - `Phase`와 lifecycle 상태 혼합
   - 에이전트가 사람 승인을 가장할 수 있던 신뢰 경계 부재
   - legacy 직접 실행 예외와 완료 기준 충돌
   - Obsidian vault에 실제 프로젝트 상태를 복제할 위험
6. 최종 재감사에서 실행 차단급 모순이 없다는 Agent 판정을 받았다.

## 검증 상태

### 확인 완료

- 생성됨: 마스터 계획 1개, 단계 지시서 9개
- 구조 검증됨: 모든 문서 UTF-8 strict decode, NUL 0건, 닫히지 않은 코드 블록 0건
- 참조 검증됨: 마스터가 Stage 00~08 파일을 각각 정확히 1개 참조
- 섹션 검증됨: 모든 단계에 목적, 시작 조건, 완료 기준, 중단 조건, 롤백,
  `backup/` 보호 규칙 존재
- 계약 검증됨: fail-closed, 승인 provenance, crash-consistent artifact,
  실제 리뷰 렌더, 복구, 원격 CI waiver, 안정화 지표 문구 존재
- 독립 Agent 감사: 초안 조건부 불합격 사항을 수정한 뒤 최종 통과 판정
- Git 확인: `backup/` 변경 0건
- 루트에는 현재 실행 가능한 doccheck가 없어 기존 `backup/` 도구는 실행하지 않았으며,
  이번 검증은 별도 UTF-8·섹션·참조·Git 상태 정적 검사로 수행

### 아직 확인되지 않음

- 신규 Python 패키지 생성·설치: 미수행
- 단위·계약·통합 테스트: 코드가 없어 미수행
- 훅·CI 교체와 실제 원격 CI: 미수행
- clean-clone: Stage 01 체크포인트 커밋 승인 전이므로 미수행
- 실제 미디어 파일럿과 A/V 사용자 승인: 미수행
- SQLite backup/restore와 Restic 복구: 미수행
- Obsidian·Graphify 버전·가격·보안 재확인과 설치: Stage 08 전까지 보류
- 계획의 구현 착수에 대한 사용자 승인: 없음

현재 검증은 문서 구조와 교차계약 수준이다. Agent 감사 통과를 코드, CI, 앱 또는 사용자
품질 승인으로 확대 해석하지 않는다.

## 실패 원장

| objective | attempt/version | result/cause | consecutive count | next condition |
|---|---|---|---:|---|
| 기존 파일 백업 이동 | 초기 전체 이동 | Git 외 제어 파일 범위를 잘못 해석해 반복 수정 발생 | 0, 최종 배치 성공으로 reset | `backup/` 기존 파일 내용 수정 금지 |
| 기존 파일 백업 이동 | AGENTS 경로 수정 | 이동만 해야 할 기존 파일 내용을 수정함 | 0, 원본 해시 복구로 reset | 기존 파일은 읽기 전용, 신규 문서는 루트에만 생성 |
| 기존 파일 백업 이동 | 취소 기록 파일 생성 | `backup/` 안에 신규 운영 파일을 생성함 | 0, 파일 제거로 reset | 백업 내부 신규 운영 파일 생성 금지 |
| 구조 리서치 | 로컬+외부 교차분석 | 성공 | 0 | 실행 순서는 마스터 계획 우선 |
| 멀티에이전트 실행 계획 | 초안 독립 감사 | DB/파일 승격, A/V 렌더, 복구 순환 등 P0/P1 확인 | 1 | 지적 항목을 단계 계약에 반영 |
| 멀티에이전트 실행 계획 | 보완본 최종 재감사 | 모든 차단 항목 해소, 실행 준비 문서 통과 | 0, 확인된 성공으로 reset | 사용자 Stage 00 승인 |

현재 활성 연속 실패 카운트는 없다.

## 활성 차단 요소와 위험

- Stage 00 착수에 대한 사용자 승인이 아직 없다.
- 계획 문서 10개와 `PROJECT_STRUCTURE_RESEARCH.md`는 아직 Git 미추적 상태다.
- 이 핸드오프는 이전 staged 버전과 현재 working-tree 버전이 다르다. 다음 세션은
  `git status`와 staged/unstaged diff를 모두 확인해야 한다.
- 루트 `.githooks/pre-commit`은 검사기 결손을 성공으로 처리하는 fail-open 상태이며
  Stage 01 전까지 신뢰할 수 없다.
- 루트 `.github/workflows/ci.yml`은 현재 없는 `tools/`, `tests/` 경로를 참조하는 stale
  상태이며 실제 원격 성공을 확인하지 않았다.
- `PROJECT_STRUCTURE_RESEARCH.md`의 직접 0단계 구현 순서는 마스터 계획에 의해
  superseded됐다. 실측 근거만 사용한다.
- Stage 00의 대용량 해시는 시스템 부담이 될 수 있다. 민감 파일은 읽거나 해시하지
  않고, `backup/` 자체에서 테스트를 실행하지 않는다.
- legacy worktree, 보존 태그, 체크포인트 커밋, 패키지 설치, 외부 저장소와 비용 발생은
  각각 별도 사용자 승인이 필요하다.
- 문서 계획 통과만으로 기존 훅·CI 결함이나 신규 구조의 실제 안정성이 개선된 것은 아니다.

## 다음 작업

1. 사용자에게 Stage 00 착수 범위를 제시하고 승인을 받는다.
   - 읽기 전용 저장소·`backup/` 인벤토리
   - `reports/rebuild/stage-00/` 증거 파일 생성
   - 민감 파일 비열람
   - `backup/` 자체에서 테스트 실행 금지
   - 태그·커밋·worktree는 별도 승인 전 생성 금지
2. 승인되면 조정 에이전트가 Stage 00 작업 패킷을 세 역할로 나눈다.
   - 기준선 인벤토리
   - 동작 기준선 수집
   - 독립 검증
3. Stage 00 완료·사용자 검토 전에는 Stage 01 파일이나 패키지를 만들지 않는다.
4. Stage 00 보고서가 통과하면 Stage 01의 신규 루트 쓰기와 의존성 설치 승인을 별도로
   받는다.
5. Graphify·Obsidian은 Stage 07 안정화 이전에 설치하지 않는다.

## 다음 세션 시작 프롬프트

```text
루트 SESSION_HANDOFF.md를 먼저 읽고 AGENT_EXECUTION_PLAN.md와
AGENT_STAGE_00_BASELINE_FREEZE.md를 끝까지 읽어라.
backup/은 역사적 읽기 전용 자료이며 그 안에서 테스트하거나 파일을 만들지 마라.
현재 구현은 미착수이고 첫 행동은 Stage 00 착수 승인 확인이다.
승인되지 않았다면 계획·진단 범위를 임의로 구현하지 마라.
승인됐다면 reports/rebuild/stage-00/만 쓰고, 민감 파일을 열거나 해시하지 말며,
Git 추적·미추적 파일을 모두 포함한 backup 무변경 증거를 남겨라.
Stage 00 검증과 사용자 승인이 끝나기 전 Stage 01로 넘어가지 마라.
```

## 백업·중복 결정

- `SESSION_HANDOFF.md`만 현재 재개 상태의 정본이다.
- 별도 handoff 또는 `NEXT_SESSION_TASK.md`를 만들지 않는다.
- 프로젝트의 중복 백업 금지 원칙에 따라 이 문서의 별도 복사본을 만들지 않았다.
- `backup/SESSION_HANDOFF.md`는 historical이며 갱신하지 않았다.
- 일반 운영 규칙은 이 문서에 복제하지 않고 `AGENT_EXECUTION_PLAN.md`와 단계 지시서로
  연결했다.
