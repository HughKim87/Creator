# 실패 정본의 파생 projection·lifecycle 파일 증식

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 10 구조 재점검
- 마지막 검증: 2026-07-23
- 적용 범위: `failures/*.md`, 실패 지식 검증·검색·개정, per-case 파생 record

## 증상

해결 실패 Markdown 25개를 재사용하기 위해 stored `failure_knowledge`가 39개, 관련 source와 lifecycle snapshot·event가 추가됐다. 같은 실패 문서 한 건을 개정하면 새 source, 새 failure projection, 두 대상의 새 lifecycle snapshot 등 record 파일 네 개와 lifecycle event가 늘어났다.

## 확인된 원인

실패 Markdown이 이미 경로·본문·해결 상태·재발 이력의 정본이고 필요한 절도 일관되게 갖고 있는데, 범용 지식 모델의 source·immutable projection·대상별 lifecycle을 다시 적용했다. 정본 경로와 hash, 현재 해결 여부가 Markdown·source·projection·lifecycle에 중복됐고, Git과 Markdown이 보존하는 개정 이력까지 record replacement로 다시 표현했다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 05~09 실패 projection 운영 | 25개 정본에서 revision을 거치며 39개 failure projection과 관련 source·lifecycle이 누적 | 구조 문제 1건 | Stage 10에서 canonical Markdown 직접 파싱·검색·maintenance로 전환하고 새 per-case 저장 경로를 중단 |

## 해결과 검증

- `KnowledgeService`가 해결 실패 Markdown을 strict UTF-8로 직접 파싱해 transient view를 만들고 저장하지 않는다.
- `ContextService`는 canonical 실패 문서를 current 후보로 직접 검색해 문서 항목으로 package에 포함한다.
- `MaintenanceService`는 모든 실패 정본의 해결 상태·필수 절·중복 제목을 직접 검사한다.
- 임시 프로젝트의 실패 문서를 검증·검색·개정한 전후 `data/records`와 `data/events` 파일 집합과 bytes가 같고, 관련 55개 회귀와 전체 98개 회귀가 통과했다.
- 기존 stored failure projection은 삭제하지 않고 legacy direct-ID 읽기만 유지해 역사와 호환성을 보존했다.

## 재사용 규칙

- 이미 일관된 canonical 문서가 필요한 필드를 소유하면 per-item source·projection·lifecycle을 추가하기 전에 실행 시 직접 파싱할 수 있는지 먼저 검토한다.
- 파생물이 필요해도 정본과 같은 현재 상태를 다시 소유하게 하지 않는다.
- Git과 canonical 본문이 개정 이력을 충분히 보존하면 같은 이력을 immutable projection revision으로 중복하지 않는다.
- 새 구조의 효과는 파일 수가 아니라 대표 생성·개정 흐름 전후의 실제 파일 집합과 검색·검증 결과로 확인한다.

## 근거

- [Stage 10 계획·진단·완료 근거](../docs/build/stage-10-agent-autonomy-structure-optimization.md)
- [지식 유형·실패 정본 직접 재사용 계약](../docs/KNOWLEDGE_TYPES_CONTRACT.md)
- [선택적 컨텍스트 계약](../docs/CONTEXT_PACKAGE_CONTRACT.md)
- [유지보수 계약](../docs/MAINTENANCE_AUTOMATION_CONTRACT.md)
- [KnowledgeService 회귀](../tests/test_knowledge_types.py)
- [ContextService 회귀](../tests/test_context.py)
