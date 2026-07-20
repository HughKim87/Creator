# 작업 02-1: 구체계 계약 대응표 (초안)

- 입력: `backup/docs/WORKFLOW_CONTRACT.json` (schema_version 1, contract_id `closed_loop_video_workflow`)
- 참조: `docs/rebuild/stage-00/MIGRATION_CATALOG.md` (M01, M06, M07, M08, M13),
  `docs/rebuild/stage-02/AGENT_STAGE_02_DOMAIN_CONTRACTS.md`
- 상태: 초안. 사용자 의미 승인 전. 커밋 전.
- 판정 분류: `KEEP`(의미 유지) / `RENAME`(이름만 변경) / `STORAGE`(저장 계층으로 이동) /
  `RETIRE`(폐기) / `NEW`(새로 필요) / `USER`(사용자 승인 필요)

## 1. 최상위 필드

| 구체계 필드 | 판정 | 신규 대응 | 근거 |
|---|---|---|---|
| `schema_version: 1` | RENAME | 도메인 계약 `schema_version: 2` 직렬화 필드 | 02-3 요구. 알 수 없는 미래 버전은 fail-closed |
| `contract_id` | KEEP | 계약 식별 상수 | 계약 추적성 유지 |
| `role`, `read_when`, `retention` | RETIRE | 문서 주석으로만 | 실행 의미 없음 |
| `state_path`, `rule_registry_path`, `edit_change_ledger_path`, `edit_memory_view_path` | STORAGE | Stage 03 SQLite 단일 상태 + 생성 뷰 | 분산 JSON 상태 파일 제거가 재구축 목표. 경로는 도메인 의미가 아님 |

## 2. 단계 모델 (`phase_order`)

| 구체계 | 판정 | 신규 대응 |
|---|---|---|
| `data_analysis` | RENAME/USER | `intake` (지시서 초안 명칭) |
| `planning` | KEEP | `planning` |
| `edit_calibration` + `edit_full` | USER | 지시서 초안은 단일 `editing`. 구체계의 보정→확장 2단 구조를 phase로 유지할지, editing 내부 세대 정책으로 내릴지 사용자 결정 필요 |
| `validation` | RENAME | `technical_validation` |
| (없음, `final` 내 혼재) | NEW | `human_approval` — 기술 검증과 사람 A/V 승인의 분리(M08) |
| `final` | RENAME | `delivery` |

구체계에는 `LifecycleStatus` 축이 없다. `waiting_user`/`blocked_external`/`failed` 등은
NEW이며 phase와 혼합하지 않는다(지시서 6절).

## 3. `execution_request`

| 필드 | 판정 | 신규 대응 |
|---|---|---|
| `reset_phrases` | RETIRE | 자연어 트리거는 도메인 계약이 아님. 응용 계층 관심사 |
| `same_objective_failure_limit: 3` | KEEP | `FailureRecord` 불변조건: 동일 objective 3연속 실패 시 중단. `PROJECT_RULES.md`와 일치 |
| `counter_scope`, `carry_between_requests: false` | KEEP | 실패 카운터는 사용자 실행 요청 단위. 단 rejection 기억은 reset을 넘어 생존(memory_policy와 함께) |

## 4. `promotion_policy`

| 필드 | 판정 | 신규 대응 |
|---|---|---|
| `default_deny: true` | KEEP | 전이 함수 기본 거부. 허용 목록 밖 전이는 구조화된 거부 사유 반환 (M07 PRESERVE) |
| `waiver_requires_explicit_user_approval` | KEEP | `ApprovalType.WAIVER` + `ActorKind.HUMAN` 필수 |
| `technical_success_is_quality_approval: false` | KEEP | `ApprovalType`에서 기술 검증과 사람 A/V 승인을 별도 타입으로 분리 (M08) |
| `user_is_first_line_qa: false` | KEEP | 에이전트 자체 검토가 사람 승인 선행 조건 |
| `actual_av_review_required_for_final` | KEEP | `delivery` 진입은 `ApprovalType.HUMAN_AV` 승인 이벤트 필수 |
| `current_deliverable_requires_final_gate` | KEEP | `ArtifactRole.CURRENT_DELIVERABLE` 승격은 delivery 게이트 통과 필수 |
| `calibration_may_use_ai_reviewed_provisional_plan`, `user_direction_checkpoint`, `one_user_creative_checkpoint_before_full_expansion` | USER | 보정 체크포인트 의미. phase 구조 결정(2절)과 함께 확정 |
| `data_reanalysis_requires_source_or_audience_change` | KEEP | `SourceFingerprint` 변경 시에만 intake 재진입 허용 |
| `full_rebuild_requires_explicit_user_approval` | KEEP | 새 세대 생성 승인 규칙 |
| `revision_model: working_and_approved_baselines_plus_revision_dag` | KEEP/STORAGE | 의미(working/approved 이중 기준선, 개정 DAG)는 도메인 계약. DAG 저장은 Stage 03 (M06 REDESIGN) |

## 5. `memory_policy`

| 필드 | 판정 | 신규 대응 |
|---|---|---|
| `event_store_is_append_only` | KEEP | `WorkflowEvent` append-only. 삭제·수정 전이 없음 |
| `working_baseline_may_advance_without_user_approval` | KEEP | working baseline 승격은 기술 검증만 요구 |
| `approved_baseline_requires_user_direction` | KEEP | approved baseline 승격은 HUMAN 승인 이벤트 필수 |
| `rejection_memory_survives_execution_request_reset` | KEEP | 거부 기록은 실패 카운터 reset과 독립 |
| `feedback_is_cleared_only_by_explicit_superseding_event` | KEEP | 명시적 supersede 이벤트로만 해제 |
| `overall_score_requires_actual_av_observation` | KEEP | 점수·품질 판단은 HUMAN_AV 증거 필수 |

## 6. `validation_scope_policy`

| 필드 | 판정 | 신규 대응 |
|---|---|---|
| `required_scopes` 5종 | KEEP/RENAME | 검증 scope enum. `app`→`app_validation` 등 명칭은 사용자 승인 후 확정 |
| `allowed_statuses` (`pending/passed/failed/not_required`) | KEEP | 검증 상태 enum. `pending`≠성공 불변조건 유지 |
| `required_scope_fields` (`status/evidence/limitations`) | KEEP | 증거 없는 passed 금지 |
| `scope_check_paths` | STORAGE | JSON 경로 결합은 폐기하고 이벤트·상태 모델로 표현 |
| `tool_surface_failure_scope_is_local`, `passed_scope_survives_unrelated_surface_failure` | KEEP | scope 독립성 불변조건 (M08 연결 테스트 존재) |
| `audio_signal_requires_browser_playback: false` | RETIRE | 도구 구현 세부사항 |
| `blocker_checklist` | KEEP | blocked 판정 전 필수 확인 목록. `blocked_external` 진입 사전조건 |

## 7. `transition_policy` / `transitions`

| 필드 | 판정 | 신규 대응 |
|---|---|---|
| `require_immediate_predecessor_approval` | KEEP | 직전 phase 승인 없이 전이 불가 (M07 PRESERVE 핵심) |
| `transitions.*.requires` 체크 목록 | KEEP/STORAGE | 의미는 phase별 진입 요건으로 보존. `phases.*.checks.*` JSON 경로 형식은 폐기하고 타입화된 요건으로 재표현 |
| `rules_required_before` | STORAGE | rule registry는 Stage 03 저장 설계와 함께 |
| `calibration_generation_allowed`, `generation_lock_released` | KEEP | 세대 생성 잠금. 승인 없는 `generating` 진입 금지 불변조건 (M01·M07) |

## 8. `calibration_policy` / `revision_routing`

| 필드 | 판정 | 신규 대응 |
|---|---|---|
| `calibration_policy` 전체 | USER | 편집 도메인 세부 정책. phase 구조 결정(2절) 후 Stage 04 이식 시 확정. Stage 02 최소 타입에는 미포함 |
| `revision_routing` | KEEP(의미)/USER(명칭) | 개정 사유→재진입 phase 매핑. `source_fingerprint_or_target_audience_changed`→intake 재진입은 M01 불변조건과 일치 |

## 9. `artifact_roles` / rule·verification 필드

| 구체계 | 판정 | 신규 대응 |
|---|---|---|
| `draft`, `calibration_candidate`, `approved_baseline`, `current_deliverable`, `superseded` | KEEP/RENAME | `ArtifactRole` enum. `calibration_candidate`는 phase 결정에 종속(USER) |
| `historical_failure_evidence` | KEEP | 실패 증거 보존 불변조건과 연결. 실패 세대 산출물은 승격 불가 |
| (없음) | NEW | 입력 원본 역할과 산출물 역할의 상호 배제 (지시서 7절) |
| `required_rule_fields`, `verification_statuses` | STORAGE | rule registry는 Stage 03. `superseded` 상태 의미만 도메인에 보존 |

## 10. 구체계에 없어 새로 필요한 것 (NEW)

- `ProjectId`/`SourceId`/`GenerationId`/`ArtifactId`/`EventId` 강타입 ID와 생성·검증 규칙
- `SourceFingerprint` 타입과 동일 지문↔단일 `source_id` 불변조건 (M01은 도구 구현에만 존재)
- `LifecycleStatus` 축 전체와 phase 보존 재개 규칙
- `ActorKind`와 사람 승인 provenance (M08 공백: 구체계는 승인자 신원 증명 없음)
- 승인 이벤트의 대상 해시·세대 기준선 포함과 대상 변경 시 승인 무효화
- `command_id` 멱등성과 외부 공급 `event_id`/`occurred_at`(UTC) 순수 전이 함수
- 직렬화 schema_version, 알 수 없는 필드·버전 fail-closed 정책

## 11. 사용자 승인 필요 항목 (의미 승인 게이트 입력)

1. Phase 명칭과 개수: 특히 `edit_calibration`/`edit_full`을 별도 phase로 유지할지,
   단일 `editing` 내부 세대 정책으로 내릴지
2. 보정 체크포인트(`user_direction_checkpoint`)의 신규 표현 위치
3. `blocked_external` / `waiting_user` / `failed` / 실행 단위 `aborted`의 구분 의미
4. 승인 무효화 조건(대상 해시 변경 시)의 범위
5. 완료 후 재개 정책: 새 세대 생성 vs delivery 재진입
6. 실패 세대·증거 보존 기간
7. 검증 scope 5종의 신규 명칭

이 승인 없이 Stage 03 저장소 구현을 시작하지 않는다.
