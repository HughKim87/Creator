# Obsidian 검토 환경 계약

- 목적: 프로젝트 루트를 그대로 검토하면서 보호 경로를 노출하지 않는 최소 공유 설정을 정의한다.
- 읽는 시점: Obsidian 공유 설정이나 보호 경계를 변경할 때
- 책임: 프로젝트 에이전트가 안전 설정을 유지하고 사용자가 정책 변경을 승인한다.
- 상태: 활성 계약
- 관련 권위: [정보·문서 책임 구조](../INFORMATION_ARCHITECTURE.md), [상시 정책](../../PROJECT_RULES.md)

## 결정과 경계

| 항목 | 선택 | 경계 |
|---|---|---|
| 볼트 | 프로젝트 루트 | 복제 볼트 없음 |
| 시작 화면 | 루트 `README.md` | 별도 router·inventory 없음 |
| 보호 제외 | `.git/`, `.obsidian/`, `backup/`, `inputs/`, `outputs/` | 내부를 열거·색인하지 않음 |
| 사용 방식 | 읽기·탐색 우선 | 직접 편집도 project rule을 우회하지 않음 |
| 설정 공유 | `.obsidian/app.json`의 안전 제외만 | workspace, UI, 테마, plugin 상태는 로컬 |
| plugin | community plugin 없음 | 기본 링크·검색만 사용 |

## 사용자 시작 경로

1. 프로젝트 목적과 구조는 [README](../../README.md)
2. 현재 작업은 [SESSION_HANDOFF](../../SESSION_HANDOFF.md)
3. 정책과 작업 규칙은 [PROJECT_RULES](../../PROJECT_RULES.md)와 [AGENTS](../../AGENTS.md)
4. 완료 상세는 Git 이력

## 갱신·검증

- 설정을 바꾸면 보호 제외와 local link를 검사한다.
- Obsidian이 없어도 루트 Markdown에서 현재 work와 활성 정본에 접근할 수 있어야 한다.
- 별도 router나 전체 문서 inventory는 distinct user need가 확인되기 전 만들지 않는다.

## 문서 소유 파생 artifact

아래 block이 Git에 공유하는 유일한 Obsidian 설정의 exact 정본이다.

<!-- project-artifact:v1 path=.obsidian/app.json verify=json-semantic -->
```json
{"defaultViewMode":"preview","showUnsupportedFiles":false,"userIgnoreFilters":[".git/",".obsidian/","backup/","inputs/","outputs/"]}
```
<!-- /project-artifact -->
