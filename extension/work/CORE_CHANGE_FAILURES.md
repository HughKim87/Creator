# Core 변경 차단 실패 기록

- 목적: 자동·예약·백그라운드·무인 작업이 core 변경을 요구해 안전하게 중단된 사실의 단일 기록을 소유한다.
- 읽는 시점: `core_change_required` 실패를 진단하거나 사용자 승인 후 작업을 재개할 때.
- 책임: 실패한 자동 작업이 항목을 추가하고, 사용자가 core 변경 여부를 결정한다.
- 상태: 활성 append-only 작업 기록.
- 관련 권위: 루트 `PROJECT_RULES.md`가 선택한 core-change-control 절차.

## 기록 형식

새 항목은 다음 형식을 사용한다.

```markdown
## core-change-blocked-YYYYMMDDTHHMMSSZ

- 작업:
- 요청된 core 경로:
- 필요하다고 판단한 이유:
- core 변경 여부: 변경하지 않음
- 결과: failed
- 오류 코드: core_change_required
- 재시작 조건: explicit_user_approval
```

## core-change-blocked-20260728T183445Z

- 작업: 자동 프로젝트 기반 개선 M1-S1~M1-S4
- 요청된 core 경로: `core/src/file_data/store.py`, `core/src/file_data/document_data.py`, `core/tests/test_record_io.py`, `core/tests/test_file_data_foundation.py`, `core/schemas/common-record-v1.schema.json`, `core/schemas/decision-payload-v1.schema.json`, `core/schemas/failure-knowledge-payload-v1.schema.json`, `core/schemas/knowledge-payload-v1.schema.json`, `core/schemas/source-payload-v1.schema.json`, `core/schemas/work-event-payload-v1.schema.json`, `core/schemas/work-request-payload-v1.schema.json`, `core/schemas/work-state-payload-v1.schema.json`, `core/docs/FILE_DATA_CONTRACT.md`, `core/docs/KNOWLEDGE_TYPES_CONTRACT.md`, `core/docs/WORK_STATE_CONTRACT.md`
- 필요하다고 판단한 이유: 임의 경로 clean clone의 source-root 안전 판정, 주입 가능한 neutral storage, project-neutral schema namespace, Core의 YouTube artifact 직접 열거 제거와 Extension-owned registry를 구현해야 M1 gate를 충족한다.
- core 변경 여부: 변경하지 않음
- 결과: failed
- 오류 코드: core_change_required
- 재시작 조건: explicit_user_approval
