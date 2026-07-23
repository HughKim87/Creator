# Obsidian 검토 환경 계약

- 목적: 프로젝트 정본을 복제하지 않고 현재 owner와 전체 추적 문서를 구분해 탐색한다.
- 읽는 시점: Obsidian 시작 경로·inventory·공유 설정을 변경하거나 보호 경계를 검증할 때
- 책임: 프로젝트 에이전트가 파생 router를 유지하고 사용자가 정책 변경을 승인한다.
- 상태: Stage 01.5 활성 계약
- 관련 권위: [정보·문서 책임 구조](../INFORMATION_ARCHITECTURE.md), [상시 정책](../../PROJECT_RULES.md)

## 결정과 경계

| 항목 | 선택 | 경계 |
|---|---|---|
| 볼트 | 프로젝트 루트 | 복제 볼트 없음 |
| 기본 화면 | 현재 owner 우선 | 완료 단계·보고서는 필요할 때 inventory에서 탐색 |
| 보호 제외 | `.git/`, `.obsidian/`, `backup/`, `inputs/`, `outputs/` | 내부를 열거·색인하지 않음 |
| 사용 방식 | 읽기·탐색 우선 | 직접 편집도 project rule을 우회하지 않음 |
| 설정 공유 | `.obsidian/app.json`의 안전 제외만 | workspace, UI, 테마, plugin 상태는 로컬 |
| plugin | community plugin 없음 | 기본 링크·검색만 사용 |

## Router와 inventory

- [START_HERE](START_HERE.md)는 현재 work, current initiative, startup policy로 먼저 연결한다.
- [DOCUMENT_MAP](DOCUMENT_MAP.md)은 owner·계약·rule·history의 범주 진입점만 소유한다.
- [GENERATED_DOCUMENT_INVENTORY](GENERATED_DOCUMENT_INVENTORY.md)는 보호·backup을 제외한 전체 추적 Markdown을 나열한다. 완료 stage와 `reports/`가 포함되므로 active owner 목록으로 해석하지 않는다.
- 완료 stage는 [master](../build/MASTER_BUILD_PLAN.md)의 owner 표와 Git에서 찾는다. 단계별 수동 보기 파일을 만들거나 유지하지 않는다.
- 현재 상태 값과 정본 본문을 파생 router에 복사하지 않는다.

## 사용자 시작 경로

1. [Obsidian 시작 화면](START_HERE.md)
2. 현재 작업은 [SESSION_HANDOFF](../../SESSION_HANDOFF.md)
3. exact owner가 불명확할 때 [문서 진입 지도](DOCUMENT_MAP.md)
4. 전체 경로가 필요할 때만 [자동 inventory](GENERATED_DOCUMENT_INVENTORY.md)

## 갱신·검증

- Markdown path set이나 H1이 바뀔 때만 inventory를 재생성한다.
- router를 바꾸면 현재 owner 링크, 전체 inventory 링크, 보호 경계, local link를 검사한다.
- Obsidian이 없어도 같은 Markdown 링크로 현재 work와 모든 정본에 접근할 수 있어야 한다.
- 새 파생 화면은 기존 router가 목적을 충족하지 못하는 distinct user need가 있을 때만 만든다.

## 문서 소유 파생 artifact

아래 block이 Git에 공유하는 유일한 Obsidian 설정의 exact 정본이다.

<!-- project-artifact:v1 path=.obsidian/app.json verify=json-semantic -->
```json
{"defaultViewMode":"preview","showUnsupportedFiles":false,"userIgnoreFilters":[".git/",".obsidian/","backup/","inputs/","outputs/"]}
```
<!-- /project-artifact -->
