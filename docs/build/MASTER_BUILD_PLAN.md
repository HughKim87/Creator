# 프로젝트 계층형 구축 마스터 계획

- 문서 유형: 번호 구축 단계의 순서·경계 정본
- 목적: 기반 구축 단계를 의존 순서대로 연결하고, controlled 단계가 필요한 경우에만 공통 경계를 제공한다.
- 읽는 시점: 번호 stage를 착수·종료하거나 단계 순서·경계를 변경할 때
- 작성 책임: 프로젝트 에이전트
- 승인 책임: 사용자는 단계 목적·보호·외부·비가역 경계와 명시한 전환을 승인하고, 에이전트는 승인 범위의 가역적 세부를 결정한다.
- 현재 상태와 첫 다음 행동: [SESSION_HANDOFF](../../SESSION_HANDOFF.md)

## 1. 적용 범위

이 문서는 `docs/build/stage-*.md`의 번호 구축 작업에만 적용한다.

- `quick`·`standard` 작업은 [AGENTS.md](../../AGENTS.md)와 관련 task rule로 진행하며 이 문서, 번호 stage, 100점표, 별도 보고서, 경계 커밋을 기본 요구로 사용하지 않는다.
- 사용자가 단계·게이트를 지정했거나 정책·구조·삭제·보호·외부 경계를 다루는 `controlled` 작업만 exact stage owner와 이 문서를 사용한다.
- 완료 stage의 상세 이력은 해당 stage owner와 Git에 남고 현재 작업의 기본 문맥으로 읽지 않는다.

## 2. 구축 원칙

1. 이전 단계의 검증된 결과만 다음 단계의 입력으로 사용한다.
2. 현재 단계에 필요하지 않은 미래 기능을 미리 구현하지 않는다.
3. 승인된 목적 안의 안전하고 가역적인 세부는 에이전트가 가장 좁은 합리적 기본값으로 결정한다.
4. 사람에게는 목표·보호·외부 효과·되돌리기 어려운 비용·실질적 범위 변경만 확인한다.
5. 단계 번호, 문서 수, 테스트 수, 점수 자체를 사용자 가치의 증거로 사용하지 않는다.
6. 중요한 결정·결과·blocker·첫 다음 행동만 현재 owner에 남기고 명령·재시도 역사를 복제하지 않는다.
7. 해결된 material failure는 `failures/`에 재사용 가치가 있을 때만 승격한다.

## 3. 단계 지도

| 단계 | 이름 | 핵심 결과 | 선행 단계 |
|---:|---|---|---|
| 00 | 최소 프로젝트 기반 | 활성 시작 경로, 최소 규칙, 현재 상태, 사용자 개요 | 없음 |
| 01 | 정보·문서 책임 구조 | 정본 데이터·운영 문서·파생 문서의 소유권과 배치 계약 | 00 |
| 01.5 | Obsidian 문서 가시화·검토 환경 | 전체 문서 지도와 권위·상태·연결 검토 | 01 |
| 02 | 파일 기반 데이터 토대 | 파일 형식, ID, 버전, 인코딩, 원자적 저장 계약 | 01.5 |
| 03 | 공통 기록 읽기·쓰기 | 검증된 생성·조회·갱신·추가·복구 진입점 | 02 |
| 04 | 작업 기록·현재 상태 | 작업 요청, 이벤트, 결과, 현재 상태와 재개 경로 | 03 |
| 05 | 지식 유형 순차 도입 | 출처·지식·결정·실패 지식 | 04 |
| 06 | 지식 수명주기 | 검토, 검증, 충돌, 대체, 폐기, 개정 이력 | 05 |
| 07 | 선택적 읽기·컨텍스트 | 필요한 문맥만 구성하는 제한된 컨텍스트 | 06 |
| 08 | 유지보수·자동화 | 최신성, 중복, 재생성, 비용 관측 | 07 |
| 09 | 도메인 워크플로 확장 | 사용자 선택 도메인을 공통 기반에 연결 | 08 |
| 10 | 에이전트 자율 운영·구조 최적화 | 문서 정본, 사람·에이전트 경계, 실패 fanout 억제 | 09 |
| 11 | 운영 마찰·인지 복잡성 축소 | 위험 비례 작업 등급, 필수 읽기·게이트·활성 표면 경량화 | 10 |

## 4. 단계 owner

| 단계 | 계획·결과 owner |
|---:|---|
| 00 | [stage-00-project-kernel.md](stage-00-project-kernel.md) |
| 01 | [stage-01-information-architecture.md](stage-01-information-architecture.md) |
| 01.5 | [stage-01-5-obsidian-document-visibility.md](stage-01-5-obsidian-document-visibility.md) |
| 02 | [stage-02-file-data-foundation.md](stage-02-file-data-foundation.md) |
| 03 | [stage-03-record-io.md](stage-03-record-io.md) |
| 04 | [stage-04-work-state.md](stage-04-work-state.md) |
| 05 | [stage-05-knowledge-types.md](stage-05-knowledge-types.md) |
| 06 | [stage-06-knowledge-lifecycle.md](stage-06-knowledge-lifecycle.md) |
| 07 | [stage-07-context-retrieval.md](stage-07-context-retrieval.md) |
| 08 | [stage-08-maintenance-automation.md](stage-08-maintenance-automation.md) |
| 09 | [stage-09-domain-integration.md](stage-09-domain-integration.md) |
| 10 | [stage-10-agent-autonomy-structure-optimization.md](stage-10-agent-autonomy-structure-optimization.md) |
| 11 | [stage-11-operating-friction-reduction.md](stage-11-operating-friction-reduction.md) |

## 5. Controlled stage 계약

현재 stage owner는 다음을 간결하게 소유한다.

1. 목표와 완료 후 가능한 일
2. 선행조건과 승인 근거
3. 구현 범위와 exact 제외·보호 경계
4. 인과 순서와 단계별 성공 게이트
5. 대표 정상·실패 흐름과 필요한 검증
6. 실제 결과, material failure, blocker, 남은 위험
7. 현재 stage에 명시적으로 필요한 점수·commit·전환 조건

진단·계획·실행·검증·최종 보고는 같은 initiative owner에 누적한다. 독립 독자나 사용자의 별도 산출물 요구가 없으면 단계별 보고서를 추가하지 않는다.

## 6. 공통 승인 게이트

### 6.1 착수

- 이전 의존 단계와 필요한 경계 commit이 완료됐다.
- 사용자 또는 추적 가능한 standing approval이 현재 목표·범위·제외·전환을 포함한다.
- 보호 입력, 외부 효과, 삭제·이동, blocker와 사람 결정 필요 항목을 확인했다.
- 변경 목적과 제외 범위를 사용자에게 간결하게 보고했다.

### 6.2 완료

한 번의 consolidated checkpoint에서 다음을 모두 확인한다.

| 확인 | 통과 근거 |
|---|---|
| 사용자 결과 | 약속한 변화와 실제 diff·산출물이 일치하고 의도적 제외가 공개됨 |
| 실제 작동 | 대표 정상·실패 흐름과 관련 검사가 기대 결과를 냄 |
| 범위·안전 | 보호·외부·비가역·미래 기능·무관 변경 침범 0 |
| 상태·문서 | material 결정·결과·blocker·첫 다음 행동의 owner가 일치 |
| 실패·위험 | durable threshold를 넘는 실패가 정리되고 미해결 material blocker가 숨겨지지 않음 |

파일 수나 종료 코드만으로 통과시키지 않는다. 실패 원인을 수정한 뒤에는 영향받은 consolidated checkpoint를 다시 실행한다.

### 6.3 독립 검증

독립 validator나 subagent는 사용자 또는 exact stage owner가 요구한 경우에만 사용한다. 과거 stage의 검증 방식은 새 작업으로 자동 승계하지 않는다. 필요한 경우 입력 격리·인원·재사용 여부는 현재 stage owner가 정의한다.

### 6.4 최종 자체 검토·점수

- 모든 controlled stage는 최종 diff·검증·상태·잔여 위험을 자체 검토하지만 숫자 점수는 사용자나 exact stage owner가 요구할 때만 기록한다.
- 점수가 필요하면 별도 rubric 문서를 만들지 않는다. 기본값은 사용자 목적, 실제 검증, 안전·범위, 문서 일관성, 유지보수성·인지 복잡성을 각 20점으로 평가한다.
- 차단 결함, 필수 검사 실패, 숨긴 실패, 복수 active owner는 점수와 무관하게 실패다.
- current scope에서 고칠 수 있는 감점은 먼저 보완·재검증한다.

### 6.5 단계 경계 commit

- 사용자 또는 exact stage owner가 승인한 commit boundary에만 적용한다.
- 최신 branch·worktree·diff를 조회하고 approved non-protected paths만 stage한다.
- commit 메시지는 실제 stage 결과를 설명한다.
- commit object, 포함 경로, 보호 경로 0, 결과 status를 확인한 뒤 다음 단계로 이동한다.

## 7. 변경 관리

- 단계 순서·경계는 이 문서, 단계 내부 구현은 해당 owner가 소유한다.
- 정책과 task 절차는 계획에 복사하지 않고 정확한 owner를 링크한다.
- 완료 stage를 현재 상태처럼 다시 쓰지 않는다.
- 단계 통합·분할·삭제는 이유, 영향, 복구 경계와 사용자 권한을 확인한다.

## 8. 현재 상태

현재 stage, blocker, 첫 다음 행동은 [SESSION_HANDOFF.md](../../SESSION_HANDOFF.md)만 소유한다.

## 9. 관련 시점 근거

- [프로젝트 의도 통합 요구사항 기준서](../../reports/2026-07-22_프로젝트_의도_통합_요구사항_기준서.md)
- [Codex 프로젝트 의도 역추론 보고서](../../reports/2026-07-22_codex_프로젝트_의도_역추론_보고서.md)
- [Claude 프로젝트 의도 역추론 보고서](../../reports/2026-07-22_claude_프로젝트_의도_역추론_보고서.md)
- [문서 기반 데이터 구축 체계 제안 보고서](../../reports/2026-07-22_codex_문서_기반_데이터_구축_체계_제안_보고서.md)

위 보고서는 당시 분석 근거이며 현재 실행 지시가 아니다.
