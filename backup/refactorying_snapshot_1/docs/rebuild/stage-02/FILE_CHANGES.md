# Stage 02 변경 파일 (전부 신규, 미커밋)

## 도메인 계약 `src/video_workflow/domain/`

| 파일 | 의도 |
|---|---|
| `errors.py` | `DomainValidationError`, `SerializationError` — fail-closed 오류 타입 |
| `ids.py` | `ProjectId`/`SourceId`/`GenerationId`/`ArtifactId`/`EventId`/`CommandId` 강타입 ID. `<prefix>-<uuid4>` 정규형, 엄격 파싱, UUID는 응용 계층이 공급 |
| `enums.py` | `Phase`(intake→delivery 초안 명칭), `LifecycleStatus`, `ActorKind`, `ApprovalType`, `ApprovalDecision`, `ArtifactRole`, `GenerationStatus`, `EventKind`. 암묵 문자열 변환 없는 `parse` |
| `values.py` | `SourceFingerprint`(sha256, 64-hex, 엄격 int), `Actor`/`ActorProvenance`(HUMAN은 provenance 필수), UTC 강제 검증기 |
| `records.py` | `WorkflowEvent`(append-only, 외부 공급 id·시각), `ApprovalTarget`(세대/해시 앵커 필수), `ApprovalRecord`(HUMAN 전용 승인 타입 강제), `ArtifactRecord`(계보·자기부모 금지), `FailureRecord`(증거 필수) |
| `state.py` | 불변 `ProjectState`(phase/lifecycle 이축, 세대·산출물·승인·실패·명령 원장), `GenerationState`, `ProcessedCommand`, `initial_state` |
| `commands.py` | 11개 명령 dataclass. `command_id`(멱등성)·`event_id`·UTC `occurred_at`·actor를 외부에서 공급 |
| `transitions.py` | 순수 전이 함수 `transition()`. 허용 목록 밖 기본 거부, 구조화 거부 사유, 세대 생성 잠금(승인 1건=세대 1개), 지문 표류 차단, 신선 승인 검사, 종단 상태 재진입 금지 |
| `serialization.py` | schema_version 2 envelope, canonical JSON(byte-identical), 미지 버전·미지 필드 fail-closed, UTC 직렬화 |
| `__init__.py` | 공개 API 재수출 |

## 테스트

| 파일 | 의도 |
|---|---|
| `tests/support/domain_factories.py` | 결정적 ID/시각 팩토리와 실제 전이로 상태를 쌓는 `Driver`(테스트 공용) |
| `tests/unit/domain/test_ids_and_values.py` | ID·지문·actor·UTC 엄격 검증 (암묵 변환 거부 포함) |
| `tests/unit/domain/test_purity_and_serialization.py` | 도메인 순수성(AST 검사로 I/O import 0건), 직렬화 왕복 byte-identical, fail-closed 정책 |
| `tests/contract/domain/test_negative_matrix.py` | 지시서 9절 필수 부정 18케이스 번호 매트릭스 + 완전성 가드 |
| `tests/property/test_transition_properties.py` | 시드 고정 무작위 250명령×5시드 시퀀스 불변조건·결정성 검증(외부 의존성 없음) |
| `tests/{support,unit/domain,contract/domain,property}/__init__.py` | 패키지 마커 |

## 문서

| 파일 | 의도 |
|---|---|
| `docs/rebuild/stage-02/CONTRACT_MAPPING.md` | 작업 02-1 계약 대응표(이전 세션 초안 보존·사용). 사용자 승인 항목 7건 명시 |
| `docs/rebuild/stage-02/STAGE_REPORT.md` 외 증거 패키지 | 본 단계 기록 |

수정·삭제된 기존 파일: 없음. `backup/` 변경: 없음.
