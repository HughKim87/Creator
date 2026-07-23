# 자동 생성 전체 추적 문서 inventory

- 목적: 보호·backup 경계를 제외한 추적 Markdown 경로를 결정론적으로 재생성한다.
- 상태: 파생물. 이 파일은 규칙·상태·결정을 소유하지 않는다.
- 사용 경계: 완료 stage와 시점 보고서를 포함하므로 active owner 목록이 아니다. 현재 진입은 `START_HERE.md`를 사용한다.
- 생성 명령: `python -m file_data maintenance-inventory --write`
- 원본 문서 수: 78
- 자기 재귀 방지: 이 생성 파일 자체는 원본 목록에서 제외한다.

## docs

- [선택적 읽기·컨텍스트 패키지 계약](../CONTEXT_PACKAGE_CONTRACT.md) — `docs/CONTEXT_PACKAGE_CONTRACT.md`
- [파일 데이터 저장 계약](../FILE_DATA_CONTRACT.md) — `docs/FILE_DATA_CONTRACT.md`
- [정보·문서 책임 구조](../INFORMATION_ARCHITECTURE.md) — `docs/INFORMATION_ARCHITECTURE.md`
- [지식 수명주기 계약과 사용법](../KNOWLEDGE_LIFECYCLE_CONTRACT.md) — `docs/KNOWLEDGE_LIFECYCLE_CONTRACT.md`
- [지식 유형·실패 정본 직접 재사용 계약](../KNOWLEDGE_TYPES_CONTRACT.md) — `docs/KNOWLEDGE_TYPES_CONTRACT.md`
- [유지보수·검증 자동화 계약](../MAINTENANCE_AUTOMATION_CONTRACT.md) — `docs/MAINTENANCE_AUTOMATION_CONTRACT.md`
- [공통 기록 I/O 계약과 사용법](../RECORD_IO_CONTRACT.md) — `docs/RECORD_IO_CONTRACT.md`
- [작업 기록·현재 상태 계약](../WORK_STATE_CONTRACT.md) — `docs/WORK_STATE_CONTRACT.md`
- [프로젝트 계층형 구축 마스터 계획](../build/MASTER_BUILD_PLAN.md) — `docs/build/MASTER_BUILD_PLAN.md`
- [Stage 00 — 최소 프로젝트 기반](../build/stage-00-project-kernel.md) — `docs/build/stage-00-project-kernel.md`
- [Stage 01.5 — Obsidian 문서 가시화·검토 환경](../build/stage-01-5-obsidian-document-visibility.md) — `docs/build/stage-01-5-obsidian-document-visibility.md`
- [Stage 01 — 정보·문서 책임 구조](../build/stage-01-information-architecture.md) — `docs/build/stage-01-information-architecture.md`
- [Stage 02 — 파일 기반 데이터 토대](../build/stage-02-file-data-foundation.md) — `docs/build/stage-02-file-data-foundation.md`
- [Stage 03 — 공통 기록 읽기·쓰기](../build/stage-03-record-io.md) — `docs/build/stage-03-record-io.md`
- [Stage 04 — 작업 기록·현재 상태](../build/stage-04-work-state.md) — `docs/build/stage-04-work-state.md`
- [Stage 05 — 지식 유형 순차 도입](../build/stage-05-knowledge-types.md) — `docs/build/stage-05-knowledge-types.md`
- [Stage 06 — 지식 수명주기](../build/stage-06-knowledge-lifecycle.md) — `docs/build/stage-06-knowledge-lifecycle.md`
- [Stage 07 — 선택적 읽기·컨텍스트](../build/stage-07-context-retrieval.md) — `docs/build/stage-07-context-retrieval.md`
- [Stage 08 — 유지보수·자동화](../build/stage-08-maintenance-automation.md) — `docs/build/stage-08-maintenance-automation.md`
- [Stage 09 — 도메인 워크플로 확장](../build/stage-09-domain-integration.md) — `docs/build/stage-09-domain-integration.md`
- [Stage 10 — 에이전트 자율 운영·구조 최적화](../build/stage-10-agent-autonomy-structure-optimization.md) — `docs/build/stage-10-agent-autonomy-structure-optimization.md`
- [Stage 11 — 운영 마찰·인지 복잡성 축소](../build/stage-11-operating-friction-reduction.md) — `docs/build/stage-11-operating-friction-reduction.md`
- [유튜브 촬영 전 근거 패키지 계약](../domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md) — `docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md`
- [문서 진입 지도](DOCUMENT_MAP.md) — `docs/obsidian/DOCUMENT_MAP.md`
- [Obsidian 검토 환경 계약](OBSIDIAN_REVIEW_CONTRACT.md) — `docs/obsidian/OBSIDIAN_REVIEW_CONTRACT.md`
- [Obsidian 시작 화면](START_HERE.md) — `docs/obsidian/START_HERE.md`
- [완료 단계 역사 찾기](stages/README.md) — `docs/obsidian/stages/README.md`

## failures

- [실패 지식](../../failures/README.md) — `failures/README.md`
- [활성 문서의 끊어진 로컬 링크](../../failures/active-document-link-rot.md) — `failures/active-document-link-rot.md`
- [`apply_patch`와 Markdown 목록 기호 충돌](../../failures/apply-patch-markdown-prefix.md) — `failures/apply-patch-markdown-prefix.md`
- [영향을 설명하지 않는 형식적 승인](../../failures/approval-without-impact-context.md) — `failures/approval-without-impact-context.md`
- [권위 역할과 문서 유형의 혼합](../../failures/authority-role-type-conflation.md) — `failures/authority-role-type-conflation.md`
- [완료 작업에 다음 행동을 함께 남기는 상태 충돌](../../failures/completed-work-next-action-conflict.md) — `failures/completed-work-next-action-conflict.md`
- [실패 정본의 파생 projection·lifecycle 파일 증식](../../failures/derived-failure-projection-fanout.md) — `failures/derived-failure-projection-fanout.md`
- [역사 지식 범위의 무제한 확대](../../failures/historical-scope-expansion.md) — `failures/historical-scope-expansion.md`
- [진행 중 작업의 체크포인트 전이 부재](../../failures/in-progress-checkpoint-transition-gap.md) — `failures/in-progress-checkpoint-transition-gap.md`
- [변경된 로컬 출처 한 건의 전체 목록 실패 전파](../../failures/mutable-local-source-list-fanout.md) — `failures/mutable-local-source-list-fanout.md`
- [Obsidian 보호 경로 링크 노출](../../failures/obsidian-protected-path-link-leakage.md) — `failures/obsidian-protected-path-link-leakage.md`
- [쓰기 후 검증의 잠금 해제 경쟁 구간](../../failures/post-write-verification-lock-window.md) — `failures/post-write-verification-lock-window.md`
- [PowerShell 외부 프로세스 JSON 인수의 따옴표 손실](../../failures/powershell-native-json-argument-quoting.md) — `failures/powershell-native-json-argument-quoting.md`
- [미래 단계 기능의 조기 구현](../../failures/premature-future-stage-implementation.md) — `failures/premature-future-stage-implementation.md`
- [프로젝트 목적의 과대 해석](../../failures/project-purpose-overreach.md) — `failures/project-purpose-overreach.md`
- [기존 Python bytecode 캐시와 청결 게이트 불일치](../../failures/python-bytecode-cache-cleanliness.md) — `failures/python-bytecode-cache-cleanliness.md`
- [기록 ID와 저장 주소의 분리로 생기는 중복](../../failures/record-id-address-ambiguity.md) — `failures/record-id-address-ambiguity.md`
- [시스템 Python 실행 경로 가정](../../failures/runtime-discovery-system-python.md) — `failures/runtime-discovery-system-python.md`
- [오래된 핸드오프 상태와 죽은 경로](../../failures/stale-handoff-state.md) — `failures/stale-handoff-state.md`
- [저장된 기록 유형의 승인 우회](../../failures/stored-type-approval-bypass.md) — `failures/stored-type-approval-bypass.md`
- [구현 폴더와 정보 구조 계약의 드리프트](../../failures/structure-contract-folder-drift.md) — `failures/structure-contract-folder-drift.md`
- [테스트 fixture의 계약 구조 가정](../../failures/test-fixture-contract-shape-assumption.md) — `failures/test-fixture-contract-shape-assumption.md`
- [후행 공백 정규식의 탭 오해석](../../failures/trailing-whitespace-regex.md) — `failures/trailing-whitespace-regex.md`
- [Windows CLI 표준 입출력 인코딩 불일치](../../failures/windows-cli-utf8-stdio.md) — `failures/windows-cli-utf8-stdio.md`
- [Windows 텍스트 줄바꿈 변환과 실제 크기 측정 불일치](../../failures/windows-text-newline-size-measurement.md) — `failures/windows-text-newline-size-measurement.md`
- [Windows 문서 검증 명령의 환경·문구 가정](../../failures/windows-validation-command-assumptions.md) — `failures/windows-validation-command-assumptions.md`
- [작업 event 시각의 snapshot 역행](../../failures/work-event-time-regression.md) — `failures/work-event-time-regression.md`

## reports

- [의도 역추론 보고서 2건 교차검증 및 점수](../../reports/2026-07-22_claude_역추론보고서_교차검증_점수.md) — `reports/2026-07-22_claude_역추론보고서_교차검증_점수.md`
- [프로젝트 의도 역추론 보고서](../../reports/2026-07-22_claude_프로젝트_의도_역추론_보고서.md) — `reports/2026-07-22_claude_프로젝트_의도_역추론_보고서.md`
- [문서 기반 데이터 구축 체계 제안 보고서](../../reports/2026-07-22_codex_문서_기반_데이터_구축_체계_제안_보고서.md) — `reports/2026-07-22_codex_문서_기반_데이터_구축_체계_제안_보고서.md`
- [프로젝트 의도 역추론 보고서](../../reports/2026-07-22_codex_프로젝트_의도_역추론_보고서.md) — `reports/2026-07-22_codex_프로젝트_의도_역추론_보고서.md`
- [oh-my-codex 도입 리서치·분석 보고서](../../reports/2026-07-22_oh-my-codex_도입_리서치_분석_보고서.md) — `reports/2026-07-22_oh-my-codex_도입_리서치_분석_보고서.md`
- [프로젝트 의도 통합 요구사항 기준서](../../reports/2026-07-22_프로젝트_의도_통합_요구사항_기준서.md) — `reports/2026-07-22_프로젝트_의도_통합_요구사항_기준서.md`
- [Claude Stage 10 교차검증 감사 보고서](../../reports/2026-07-23_claude_stage10_교차검증_감사_보고서.md) — `reports/2026-07-23_claude_stage10_교차검증_감사_보고서.md`
- [두 최종 보고서 교차검증·점수 비교·후속 작업 보고서](../../reports/2026-07-23_claude_교차검증_점수비교_후속작업_보고서.md) — `reports/2026-07-23_claude_교차검증_점수비교_후속작업_보고서.md`
- [Stage 00~09 최종 복기 보고서 교차검증 보고서](../../reports/2026-07-23_claude최종_복기_보고서_교차검증_보고서.md) — `reports/2026-07-23_claude최종_복기_보고서_교차검증_보고서.md`
- [Claude·Codex 최종 복기 보고서 교차검증·비교 보고서](../../reports/2026-07-23_codex_claude_codex_최종_복기_교차검증_비교_보고서.md) — `reports/2026-07-23_codex_claude_codex_최종_복기_교차검증_비교_보고서.md`
- [Stage 00~09 프로젝트 구축 최종 복기 보고서](../../reports/2026-07-23_codex_stage00-09_프로젝트_구축_최종_복기_보고서.md) — `reports/2026-07-23_codex_stage00-09_프로젝트_구축_최종_복기_보고서.md`
- [이번 세션 작업 감사 보고서](../../reports/2026-07-23_codex_이번_세션_작업_감사_보고서.md) — `reports/2026-07-23_codex_이번_세션_작업_감사_보고서.md`
- [Stage 00~09 계획 대비 실제 구축 비교분석 보고서](../../reports/2026-07-23_stage00-09_계획_대비_실제_구축_비교분석_보고서.md) — `reports/2026-07-23_stage00-09_계획_대비_실제_구축_비교분석_보고서.md`
- [Stage 09 유튜브 촬영 전 근거 패키지 검증 보고서](../../reports/2026-07-23_stage09_유튜브_근거_패키지_검증_보고서.md) — `reports/2026-07-23_stage09_유튜브_근거_패키지_검증_보고서.md`

## root

- [Agent Entry Point](../../AGENTS.md) — `AGENTS.md`
- [Always-On Project Rules](../../PROJECT_RULES.md) — `PROJECT_RULES.md`
- [김실버유튜브 프로젝트](../../README.md) — `README.md`
- [세션 핸드오프](../../SESSION_HANDOFF.md) — `SESSION_HANDOFF.md`

## rules

- [Document-Based Data Work Rules](../../rules/document-work.md) — `rules/document-work.md`
- [Failure-Record Work Rules](../../rules/failure-records.md) — `rules/failure-records.md`
- [History Review Rules](../../rules/history-review.md) — `rules/history-review.md`
- [Stage Work Rules](../../rules/stage-work.md) — `rules/stage-work.md`
- [User-Data Work Rules](../../rules/user-data-work.md) — `rules/user-data-work.md`
- [Version-Control Work Rules](../../rules/version-control.md) — `rules/version-control.md`
