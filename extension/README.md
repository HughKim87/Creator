# Extension

- 목적: 앞으로 추가되는 YouTube·영상·제작 workflow·스킬·개별 작업과 runtime 데이터를 core와 분리해 소유한다.
- 읽는 시점: 기반 변경이 아닌 YouTube·영상·제작 workflow·skill·task·runtime·example·report 작업을 분석, 실행, 재개, 검증, 생성 또는 변경할 때.
- 책임: 프로젝트 에이전트가 승인 범위 안에서 유지하고, 사용자가 목표·보호 데이터·외부 효과를 승인한다.
- 상태: 활성 확장 영역.
- 관련 권위: 루트 `PROJECT_RULES.md`와 그 startup이 선택한 current-state document.

## 배치

| 위치 | 책임 |
|---|---|
| `rules/` | YouTube·영상·제작 행동에만 적용되는 조건부 작업 규칙 |
| `docs/` | YouTube·영상·workflow 계약과 사용자 가이드 |
| `src/` | 도메인·workflow 구현 |
| `config/` | Git 제외 local capability의 버전·무결성·재설치 metadata |
| `schemas/` | extension payload 구조 |
| `tests/` | extension 회귀와 수직 acceptance test |
| `examples/` | 보호 데이터가 아닌 실행 예시 |
| `reports/` | 사용자가 명시적으로 요청한 시점 보고서 |
| `work/` | 활성 작업과 core 변경 차단 실패 |
| `data/` | 실행 시 생성되는 disposable record·event |
| `inputs/` | 영상별 보호 원본; Git 제외 |
| `outputs/` | 영상·SRT·썸네일·업로드 패키지 같은 보호 파생물; Git 제외 |
| `.runtime/` | active owner와 설치·재구축 경로가 있는 로컬 도구·모델·의존성 cache; Git 제외 |
| `../.agents/skills/` | 저장소 전체에서 자동 발견되는 Codex skill source |

새 작업은 이 영역에 추가한다. extension 작업을 이유로 core 구현·계약·규칙을 자동 변경하지 않는다.

## 활성 영상 owner

| 작업 | 단일 owner | 경계 |
|---|---|---|
| 촬영 전 근거 패키지 | [YouTube evidence pack 계약](docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md) | 대본·편집·파생물 생성 제외 |
| 촬영 후 영상 분석·컷 편집·Premiere XML | [영상 편집 workflow 계약](docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md) | 보호 데이터는 exact 항목·목적 승인 필요 |

영상 편집 작업은 두 계약의 범위를 섞지 않는다. 세션 원문·버전별 보고서·작업별 수치를 운영 규칙의 owner로 사용하지 않는다.

영상 편집 SRT 검증·명시 정리, legacy cut CSV 이관, timeline 다중 진단, `sequence-v5`·`premiere-cs6-v4` XML 생성은 `python -m video_editing`이 소유한다. 보호 데이터가 없는 기본 입력은 `examples/video-edit-timeline-v1.json`이며, 실제 `inputs/`·`outputs/` 경로는 exact 항목과 목적을 승인받은 작업에서만 사용한다.

과거 영상 spine·분석 문서에서 영상 편집 지식을 환류할 때도 촬영 후 영상 편집 workflow 계약을 domain owner로 사용한다. 범용 파일 추출·정리 절차는 `PROJECT_RULES.md`가 별도로 선택하며 extension이 다시 소유하거나 foundation rule을 직접 라우팅하지 않는다.

## 기반 adapter와 증거 경계

| 책임 | 구현·검증 owner | 경계 |
|---|---|---|
| `VIDEO_JOB` next-step·resume·boundary | [workflow engine](src/video_workflow/engine.py), [engine 회귀](tests/test_video_workflow_engine.py) | deterministic 상태 엔진이며 실제 browser·NotebookLM 실행과 사용자 승인은 [영상 제작 조정 skill](../.agents/skills/coordinate-video-production/SKILL.md)이 소유 |
| workflow 학습·복잡성 후보 | [aggregate learning](src/learning/metrics.py), [learning 회귀](tests/test_learning_metrics.py) | 보호 원문·개별 보고를 보존하지 않는 aggregate-only 계산; 실제 production 표본 전 효과를 주장하거나 rule을 자동 변경하지 않음 |
| Core export consumer·game pilot | [domain conformance](src/domain_conformance.py), [통합 실행점](../scripts/export_conformance.py), [conformance 회귀](tests/test_export_conformance.py) | 같은 Core manifest의 empty·YouTube·최소 game consumer 구조 검증이며 실제 게임 제작·독립 배포 증거가 아님 |

synthetic fixture 통과는 production 작업 완료, 실제 앱 검증, 사용자 승인으로 승격하지 않는다. `.runtime/` 항목은 현재 skill·code에서 참조되고 설치 또는 재구축 방법을 설명할 수 있을 때만 active capability로 유지한다. 과거 보고서의 tool 사용 사실이나 output 존재만으로 참조 없는 binary를 현재 runtime evidence로 보존하지 않는다.

## 관리되는 local runtime

[`local-runtime-v1.json`](config/local-runtime-v1.json)은 ignored `.runtime/` binary·model 자체가 아니라 component role·version·tree hash·critical file hash·license·source·reinstall 경계를 소유한다. FFmpeg는 공용 영상 probe·변환 도구이고, whisper.cpp는 선택적 offline backend다. 기존 `video-to-srt`의 faster-whisper primary backend를 암묵 교체하지 않는다.

tree hash는 각 파일의 `POSIX 상대경로|byte 크기|SHA-256` 행을 상대경로 기준 ordinal 정렬하고 LF와 마지막 LF로 직렬화한 뒤 SHA-256을 계산한다.

clean clone에서 runtime 전체가 없으면 optional `absent`이며 전체 프로젝트 실패가 아니다. 현재 workspace에서 보존 runtime을 요구하고 실제 실행까지 검증할 때는 다음 gate를 사용한다.

```powershell
python -B extension/src/local_runtime.py --require-present --probe
```

manifest와 실제 tree·critical hash가 다르거나 component 일부만 존재하면 `drift/incomplete`로 실패한다. runtime 파일은 계속 Git에서 제외하며 manifest·schema·verifier·synthetic test만 commit한다.

## 영상 편집 규칙 소유

활성 영상 편집 규칙의 조건부 선택은 소비 저장소 루트 `PROJECT_RULES.md`의 단일 route가 소유한다. 이 문서는 도메인 구조와 실제 workflow owner만 안내하며 병렬 규칙 라우터로 사용하지 않는다.

독립 영상에서 실패가 반복되어 보류 항목의 승격을 검토할 때는 [영상 편집 규칙 후보](docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md)를 근거로 사용한다. 후보 문서는 현재 운영 규칙이나 기본 합격값이 아니다.

## Core 의존 경계

- extension은 `PROJECT_RULES.md`가 선택한 승인된 foundation interface만 사용한다.
- extension 문서와 규칙은 foundation rule을 직접 라우팅하지 않고, 사용자의 상위 route를 따른다.
- foundation은 domain extension을 import하거나 extension owner를 소유하지 않는다.
- foundation interface가 부족하면 임시 우회 구현을 조용히 추가하지 않고, boundary rule의 새 interface 검토 gate를 따른다.
- foundation 변경이 필요하면 사용자의 exact 승인 경계를 먼저 확인한다.
