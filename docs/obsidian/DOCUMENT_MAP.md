# 전체 활성 문서 지도

- 목적: 활성 문서의 권위·유형·소유 위치와 연결을 검토한다.
- 읽는 시점: Obsidian 전체 검토, 새 문서 생성 전, 단계 시작·종료 시.
- 책임: 정본 링크에서 파생되는 Stage 01.5 검토 화면.
- 상태: 활성.
- 관련 권위: [정보·문서 책임 구조](../INFORMATION_ARCHITECTURE.md).

## 시작·상태·가이드

- [AGENTS](../../AGENTS.md) — 권위 정본 · 시작 라우터
- [PROJECT_RULES](../../PROJECT_RULES.md) — 권위 정본 · 정책
- [SESSION_HANDOFF](../../SESSION_HANDOFF.md) — 권위 정본 · 현재 상태
- [README](../../README.md) — 파생 표현 · 사용자 가이드

## 핵심 계약과 현재 구축 계획

- [정보·문서 책임 구조](../INFORMATION_ARCHITECTURE.md) — 권위 정본 · 계약
- [파일 데이터 저장 계약](../FILE_DATA_CONTRACT.md) — 권위 정본 · 계약
- [공통 기록 I/O 계약](../RECORD_IO_CONTRACT.md) — 권위 정본 · 계약·사용 가이드
- [작업 기록·현재 상태 계약](../WORK_STATE_CONTRACT.md) — 권위 정본 · 계약
- [지식 유형 계약과 사용법](../KNOWLEDGE_TYPES_CONTRACT.md) — 권위 정본 · 계약·사용 가이드
- [지식 수명주기 계약과 사용법](../KNOWLEDGE_LIFECYCLE_CONTRACT.md) — 권위 정본 · 계약·사용 가이드
- [선택적 읽기·컨텍스트 패키지 계약](../CONTEXT_PACKAGE_CONTRACT.md) — 권위 정본 · 계약·사용 가이드
- [유지보수·검증 자동화 계약](../MAINTENANCE_AUTOMATION_CONTRACT.md) — 권위 정본 · 계약·사용 가이드
- [유튜브 촬영 전 근거 패키지 계약](../domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md) — 권위 정본 · 도메인 계약·사용 가이드
- [마스터 구축 계획](../build/MASTER_BUILD_PLAN.md) — 권위 정본 · 단계 계획
- [Stage 10 에이전트 자율 운영·구조 최적화](../build/stage-10-agent-autonomy-structure-optimization.md) — 현재 initiative의 진단·계획·검증 owner

## 전체 활성 문서

- [자동 생성 활성 문서 inventory](GENERATED_DOCUMENT_INVENTORY.md) — 보호·역사 경계를 제외한 모든 활성 Markdown 경로의 완전 목록
- 이 지도는 owner와 범주 진입점만 소유한다. 새 문서마다 수동 행을 추가하지 않는다.

## 작업 규칙

- [단계 작업 규칙](../../rules/stage-work.md)
- [실패 기록 규칙](../../rules/failure-records.md)
- [문서 작업 규칙](../../rules/document-work.md)
- [역사 검토 규칙](../../rules/history-review.md)
- [버전 관리 규칙](../../rules/version-control.md)
- [보호 데이터 작업 규칙](../../rules/user-data-work.md)

## 실패·요구사항·시점 증거

- [실패 지식 색인](../../failures/README.md)
- [통합 요구사항 기준서](../../reports/2026-07-22_프로젝트_의도_통합_요구사항_기준서.md)
- [Stage 00~09 최종 복기](../../reports/2026-07-23_codex_stage00-09_프로젝트_구축_최종_복기_보고서.md)
- 다른 실패 사례와 시점 보고서는 위 자동 inventory에서 찾고, 현재 지시로 사용하지 않는다.

## Obsidian 파생 검토 화면

- [검토 환경 계약](OBSIDIAN_REVIEW_CONTRACT.md)
- [시작 화면](START_HERE.md)
- [이 전체 지도](DOCUMENT_MAP.md)
- [Stage 00~09 완료 시점 보기](stages/README.md) — 기존 파생 화면 묶음; 새 단계 파일을 추가하지 않음

## 제외 경계

- `backup/` — 역사 경계만 표시, 내부 문서 미색인
- `inputs/`, `outputs/` — 보호 경계만 표시, 사용자 지정 없이는 미색인
- `.git/`, `.obsidian/` — 저장소·앱 내부 상태, 문서 지도 미포함
