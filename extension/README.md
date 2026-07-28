# Extension

- 목적: 앞으로 추가되는 YouTube·영상·제작 workflow·스킬·개별 작업과 runtime 데이터를 core와 분리해 소유한다.
- 읽는 시점: 기반 변경이 아닌 실제 작업 기능이나 작업 데이터를 만들거나 수정할 때.
- 책임: 프로젝트 에이전트가 승인 범위 안에서 유지하고, 사용자가 목표·보호 데이터·외부 효과를 승인한다.
- 상태: 활성 확장 영역.
- 관련 권위: 루트 `PROJECT_RULES.md`와 그 startup이 선택한 current-state document.

## 배치

| 위치 | 책임 |
|---|---|
| `rules/` | YouTube·영상·제작 행동에만 적용되는 조건부 작업 규칙 |
| `docs/` | YouTube·영상·workflow 계약과 사용자 가이드 |
| `src/` | 도메인·workflow 구현 |
| `schemas/` | extension payload 구조 |
| `tests/` | extension 회귀와 수직 acceptance test |
| `examples/` | 보호 데이터가 아닌 실행 예시 |
| `reports/` | 사용자가 명시적으로 요청한 시점 보고서 |
| `work/` | 활성 작업과 core 변경 차단 실패 |
| `data/` | 실행 시 생성되는 disposable record·event |
| `inputs/` | 영상별 보호 원본; Git 제외 |
| `outputs/` | 영상·SRT·썸네일·업로드 패키지 같은 보호 파생물; Git 제외 |
| `.runtime/` | 프로젝트 로컬 도구·모델·의존성; Git 제외 |
| `../.agents/skills/` | 저장소 전체에서 자동 발견되는 Codex skill source |

새 작업은 이 영역에 추가한다. extension 작업을 이유로 core 구현·계약·규칙을 자동 변경하지 않는다.

## 활성 영상 owner

| 작업 | 단일 owner | 경계 |
|---|---|---|
| 촬영 전 근거 패키지 | [YouTube evidence pack 계약](docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md) | 대본·편집·파생물 생성 제외 |
| 촬영 후 영상 분석·컷 편집·Premiere XML | [영상 편집 workflow 계약](docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md) | 보호 데이터는 exact 항목·목적 승인 필요 |

영상 편집 작업은 두 계약의 범위를 섞지 않는다. 세션 원문·버전별 보고서·작업별 수치를 운영 규칙의 owner로 사용하지 않는다.

영상 편집 SRT 검증·명시 정리, legacy cut CSV 이관, timeline 다중 진단, `sequence-v5`·`premiere-cs6-v4` XML 생성은 `python -m video_editing`이 소유한다. 보호 데이터가 없는 기본 입력은 `examples/video-edit-timeline-v1.json`이며, 실제 `inputs/`·`outputs/` 경로는 exact 항목과 목적을 승인받은 작업에서만 사용한다.

## 조건부 영상 편집 규칙

영상 편집 workflow 계약을 읽은 뒤 현재 행동과 일치하는 규칙만 한 번 읽는다.

| 행동 | 읽을 규칙 |
|---|---|
| 새 편집 시작, 입력 범위 확정, 사용자 지시·피드백 해석 | [입력·지시 규칙](rules/video-editing-intake-and-instructions.md) |
| timeline·XML·검토 산출물 생성 또는 source lineage 판단 | [산출물 계보 규칙](rules/video-editing-artifact-lineage.md) |
| 사건 선택, 구성 편집, 실제 컷 분할·압축 | [스토리·컷 설계 규칙](rules/video-editing-story-and-cut-design.md) |
| 발화·화면·밝기·전환 경계 검수 | [경계 품질 규칙](rules/video-editing-boundary-quality.md) |
| 작업 재개, revision 전환, 사용자 수정본·승인 반영 | [상태·승인 규칙](rules/video-editing-state-and-approval.md) |
| validator 실행, XML 생성, 완료·전달 상태 보고 | [검증·전달 규칙](rules/video-editing-validation-and-delivery.md) |
| 독립 영상에서 실패가 반복되어 보류 항목의 규칙 승격을 검토 | [영상 편집 규칙 후보](docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md) |

## 파일 추출·정리 규칙

| 행동 | 읽을 규칙 |
|---|---|
| 파일·과거 영상 분석 자료에서 규칙·실패·현재 상태·계보만 추출 | [파일 추출 규칙](rules/file-extraction.md) |
| 추출이 끝난 파일을 유지·정리·삭제·이동 후보로 분류 | [파일 정리 규칙](rules/file-cleanup.md) |

규칙 본문은 각 파일만 소유한다. workflow 계약·보고서·작업 기록에 복제하지 않는다.

## Core 의존 경계

- extension은 `PROJECT_RULES.md`가 선택한 승인된 foundation interface만 사용한다.
- extension 문서와 규칙은 foundation rule을 직접 라우팅하지 않고, 사용자의 상위 route를 따른다.
- foundation은 domain extension을 import하거나 extension owner를 소유하지 않는다.
- foundation interface가 부족하면 임시 우회 구현을 조용히 추가하지 않고, boundary rule의 새 interface 검토 gate를 따른다.
- foundation 변경이 필요하면 사용자의 exact 승인 경계를 먼저 확인한다.
