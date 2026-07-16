# 구체계 이식 카탈로그

## 1. 판정 기준

- `PRESERVE`: 구체계의 관찰 가능한 의미와 연결 테스트를 비교 기준으로 보존
- `PORT_WITH_TESTS`: 신규 경계에 이식하되 먼저 특성·실패 테스트를 확보
- `REDESIGN`: 개념과 검증 의미는 유지하지만 상태·신뢰·실행 구현을 교체
- `RETIRE`: 신규 runtime에는 넣지 않고 역사적 `backup/`에만 보존

아래 근거는 파일과 테스트 이름을 정적으로 확인한 결과다. 테스트의 존재는 확인했지만
이 인벤토리 역할에서는 `backup/`에서 실행하지 않았으므로 통과를 주장하지 않는다.
실행 결과는 별도 `BASELINE_TESTS.md`의 동작 기준선과 교차검증해야 한다.

## 2. 기능 및 파일 묶음

| ID | 기능 또는 파일 묶음 | 등급 | 정적 근거와 연결 테스트 | 주요 의존 파일 | 이식 단계 | 롤백 방법 |
|---|---|---|---|---|---|---|
| M01 | `source_id`, 원본 시간·프레임 좌표, 동일 지문 불변성 | `PRESERVE` | `tools/source_frame_assets.py`의 `validate_source_identity`, `canonical_name`; `test_source_frame_assets.py::test_same_fingerprint_cannot_use_a_new_source_id`, `test_source_id_cannot_mix_a_changed_fingerprint`, `test_canonical_name_uses_source_time_and_frame` | 소스 매니페스트, `ffprobe` 메타데이터 | 02 계약, 04 구현 | 신규 결과를 폐기하고 동결된 manifest·구체계 결과와 비교 |
| M02 | 소스 프레임 생성과 자산 등록 | `PORT_WITH_TESTS` | `tools/source_frame_assets.py`, `tools/register_source_assets.py`; 재사용·경로 거부·SHA 검사를 다루는 `test_source_frame_assets.py`, `test_register_source_assets.py` | FFmpeg/FFprobe, 자산 catalog·manifest | 04 | 신규 자산 등록을 중단하고 구체계 산출물은 읽기 전용 비교 기준으로 유지 |
| M03 | 자막·음성 동기화 검사 | `PORT_WITH_TESTS` | `tools/synccheck/{align,full_scan,pause_scan,vadcheck,build_v9,srt_slice}.py`에 분석 함수가 있으나 루트 `tests/`에 대응 테스트가 확인되지 않음 | FFmpeg, SRT, cutlist, VAD 라이브러리 | 04~05 | 이식 전 특성 출력과 종료 코드를 동결하고 차이가 나면 신규 경로 사용 중지 |
| M04 | Premiere XML 생성과 절대 소스 프레임 경계 | `PRESERVE` | `skills/premiere-editing-export/scripts/make_premiere_xml.py`; `test_make_premiere_xml.py`의 프레임 길이, 중복 ID 거부, cutaway, 절대 경계 테스트 | cut CSV, source media, FFprobe | 04 | 구체계 XML과 신규 XML의 구조·프레임 차이를 비교하고 신규 XML 폐기 |
| M05 | 편집 품질 감사와 waiver 가시성 | `PORT_WITH_TESTS` | `tools/edit_quality_audit.py`; `test_edit_quality_audit.py`의 long compress, density cliff, waiver justification 테스트 | cutlist, section profile | 04 | 신규 감사 결과를 비활성화하고 구체계 리포트와 동일 입력 비교 |
| M06 | 편집 이벤트·revision·working/approved baseline | `REDESIGN` | `tools/edit_memory.py`는 별도 SQLite reducer이며 `test_edit_memory.py`에 idempotency, batch rollback, rejected baseline 테스트가 존재. 목표 구조는 분산 상태를 프로젝트별 단일 SQLite 정본으로 합쳐야 함 | workflow state, edit ledger, CURRENT view | 03 | 마이그레이션 전 DB·이벤트를 동결하고 실패 DB를 보존한 뒤 마지막 통과 schema로 복귀 |
| M07 | 단계 계약, `default_deny`, 직전 승인, validation scope | `PRESERVE` | `docs/WORKFLOW_CONTRACT.json`의 `default_deny: true`, 즉시 직전 승인 정책; `tools/workflow_gate.py`; `test_workflow_gate.py`의 closed gate, contract error, predecessor approval 테스트 | workflow state, rule registry, evidence paths | 02~03 | 신규 계약을 비활성화하고 동결 계약·테스트를 비교 기준으로 복원 |
| M08 | 사람 A/V 승인과 기술 성공의 분리 | `REDESIGN` | `WORKFLOW_CONTRACT.json`은 기술 성공을 품질 승인으로 보지 않고 `continuous_av`를 별도 scope로 둔다. `test_audio_signal_can_pass_while_continuous_av_is_pending`은 분리를 검사하지만 실제 승인자 provenance는 자동 테스트로 대체할 수 없음 | 승인자 identity/provenance, 리뷰 렌더, validation state | 02 신뢰 경계, 05 실제 파일럿 | 사람 승인 없는 상태로 즉시 닫고 마지막 승인 baseline으로 복귀 |
| M09 | FFmpeg roughcut 실행 | `PORT_WITH_TESTS` | `skills/premiere-editing-export/scripts/make_roughcut.py`가 시스템/프로젝트 FFmpeg 탐색과 subprocess 실행을 수행하나 전용 루트 테스트가 확인되지 않음 | FFmpeg, cut CSV, source media | 04~05 | 신규 실행을 중지하고 입력 불변을 확인한 뒤 동결 결과와 비교 |
| M10 | MKV→MP4 remux 배치 래퍼 | `REDESIGN` | `tools/remux_mkv_to_mp4.bat`은 개별 FFmpeg 실패를 출력하지만 누적 실패 종료 코드를 보존하지 않고 마지막에 정상 종료할 수 있다. 대응 테스트가 확인되지 않음 | bundled FFmpeg, 사용자 원본 경로 | 01 fail-closed 실행, 04 기능 | 신규 래퍼가 실패하면 산출물을 등록하지 않고 원본과 실패 로그를 보존 |
| M11 | Python/Git 실행 래퍼와 Git 루트 탐지 | `PORT_WITH_TESTS` | `tools/run_python.bat`, `git_project.bat`, `project_preflight.py::git_root`; `test_tool_wrappers.py`의 Python 3, safe.directory, scan-root 테스트 | Python, Git, 저장소 루트 | 01 | 단일 신규 CLI를 비활성화하고 직접 실행의 실제 종료 코드를 사용 |
| M12 | 문서 검사와 저장소 위생 검사 | `REDESIGN` | `tools/doccheck/check_docs.py`는 구체계 문서·폴더 계약에 결합됨. 현재 루트 훅은 검사기 결손을 성공 처리하므로 신규 루트 경계용 fail-closed 검사로 교체 필요 | AGENTS 진입점, 문서 경로, Git 파일 목록 | 01 | 신규 검사 변경을 되돌리고 마지막 통과 검사 버전을 복원하되 결손 성공은 허용하지 않음 |
| M13 | `projectctl` 활성 작업·검증 receipt 상태 | `REDESIGN` | `tools/projectctl.py`; `test_projectctl.py`에 missing/corrupt state, owner conflict, failed verification, compact receipt 테스트가 존재. 목표는 Stage 03 단일 상태 DB에 통합 | handoff, Git 상태, workflow gate | 03 | 상태 DB와 이벤트를 동결하고 생성 뷰를 폐기한 뒤 마지막 호환 schema로 복귀 |
| M14 | FFmpeg 공급·라이선스 계약 | `REDESIGN` | `tools/README.md`와 remux 래퍼는 `tools/ffmpeg/bin/{ffmpeg,ffprobe,ffplay}.exe`를 기대하지만 해당 실행 파일은 Git 추적 매니페스트에 없다. 존재·해시·버전·라이선스는 검증하지 않음 | 패키지/도구 잠금 정책 | 01 설계, 04 사용 | 신규 공급 경로를 제거하고 추적 프레임워크 코드만 이전 기준과 비교 |
| M17 | 역사적 에이전트 보고서·중복 운영 진입 문서 | `RETIRE` | `claude/`, `gpt/`, `gemini/`, 구체계 `PROJECT_BOOTSTRAP.md`·`PROJECT_RULES.md` 등은 설계 근거이나 신규 runtime 정본이 아님 | 현재 실행 계획과 신규 최소 진입점 | 01 | 신규 문서에 복사하지 않고 필요 시 `backup/`의 역사 자료를 직접 참조 |
| M18 | 도메인 skill 문서 | `PORT_WITH_TESTS` | `skills/*/SKILL.md`는 작업 절차 계약을 담지만 구체계 폴더·상태 경계에 결합돼 있다. `test_skill_asset_lifecycle.py`가 source identity, manifest/CURRENT, 폴더 소유권을 검사 | 신규 도메인 계약, 외부 작업 공간 | 02 이후 필요한 수직 기능만 | 이식한 skill만 제거하고 `backup/` 원본은 변경 없이 유지 |

## 3. 매니페스트 역할별 포함 확인

| 매니페스트 역할 | 수 | 카탈로그 적용 범위 |
|---|---:|---|
| code | 30 | M02~M14 |
| test | 10 | M01~M13, M18의 연결 테스트 |
| contract | 22 | M07, M08, M12, M17, M18 |
| doc | 24 | M14, M17 및 정적 설계 근거 |

사용자 데이터와 Git ignored·미추적 파일은 카탈로그 입력이 아니다. 그 경계는
`PROJECT_RULES.md`의 `User Data Boundary`를 따른다.

## 4. 선행 테스트 공백

- M03 동기화 검사, M09 roughcut, M10 remux에는 명시적 대응 테스트가 확인되지 않았다.
- M08의 기존 테스트는 validation scope 분리만 증명할 수 있고 실제 사람 승인 provenance를
  증명하지 못한다.
- M14는 문서·래퍼의 기대 경로만 확인했다. 실행 파일의 존재·해시·버전·라이선스는
  Git 추적 프레임워크 인벤토리 밖이므로 확인하지 않았다.
- 이 공백은 성공으로 간주하지 않고 각 지정 단계의 실패·특성 테스트 입력으로 넘긴다.

## 5. 공통 롤백 원칙

- `backup/`은 수정하지 않는다.
- 태그는 생성하지 않았다. 승인된 detached legacy worktree는 검증 후 제거했다.
- 이식 실패 시 신규 코드·생성 뷰·산출물만 사용 중지하고, 실패 DB·이벤트·로그·manifest를
  먼저 동결한다.
- 추가 구체계 실행은 승인 범위의 별도 worktree에서만 수행하고 단계 종료 후 정리한다.
  중첩 `backup/`에서는 직접 실행하지 않는다.
