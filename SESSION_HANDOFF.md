# 세션 핸드오프

- 갱신일: 2026-07-23
- 역할: 채팅 기억 없이 현재 검증 상태와 첫 다음 행동을 재구성하는 단일 활성 상태 정본
- 현재 단계: Stage 04 작업 기록·현재 상태 — 98/100 완료 준비, 경계 커밋 대기
- 이전 단계: Stage 03 공통 기록 읽기·쓰기 98/100 완료, 경계 커밋 `0601489`
- 백업 정책: 별도 복제 없음. 활성 프로젝트는 Git 이력을 복구 근거로 사용한다.

## 1. 시작 순서와 권위

새 대화·세션을 시작할 때 다음 세 파일을 한 번만 끝까지 읽는다.

1. `AGENTS.md`
2. `PROJECT_RULES.md`
3. `SESSION_HANDOFF.md`

매 메시지마다 반복하지 않는다. 규칙이나 현재 상태가 바뀌었다는 알림이 있을 때만 다시 읽는다. 이후에는 `AGENTS.md`에서 현재 행동과 일치하는 `rules/*.md`만 읽고 정확한 단계 계획이나 작업 자료를 선택한다.

권위 순서는 사용자의 최신 명시적 지시 → `PROJECT_RULES.md` → 이 핸드오프 → 현재 단계 계획서다. 요구사항 정본은 `reports/2026-07-22_프로젝트_의도_통합_요구사항_기준서.md`, 구축 순서 정본은 `docs/build/MASTER_BUILD_PLAN.md`다.

## 2. 현재 목표와 경계

현재 목표는 작업 결과·실패·판단·경험을 출처와 함께 선별 축적하고 다음 작업에 필요한 지식만 다시 사용하는 **데이터 기반 지식 운영 기반**이다. 영상 제작 기능은 기반 검증 후 연결할 후속 영역이다.

- `backup/`은 역사 경계다. 활성 실행에 의존하지 않고 현재 자동 진행에서는 내부를 열거·열람하지 않는다.
- `inputs/`, `outputs/`는 사용자가 정확한 대상과 목적을 지정하기 전에는 열거·열람·요약하지 않는다.
- 설치, 외부 게시, 보호 데이터 접근, 삭제·이동, 새 비용, 실질적 범위 확대는 자동 권장 선택에 포함되지 않는다.
- 현재 상태와 첫 다음 행동은 이 문서 하나만 소유한다. README와 Obsidian 화면은 이 문서를 연결만 한다.

## 3. Stage 01~09 실행 승인

- 사용자는 Stage 01부터 Stage 09까지 미확정 선택에서 합리적 권장안을 자동 선택하고 성공 게이트 통과 후 계속 진행하도록 승인했다.
- 단계별 필수 기능, 검증, 네 가지 확인, 실패 지식 정리, 최종 자체 검토·100점 평가는 생략하지 않는다.
- 같은 목표가 3회 연속 실패하면 시도·원인·최고 연속 횟수·위험·재개 방법을 기록하고 접근법을 바꿔 승인된 범위 안에서 별도 승인 없이 재개한다.
- Stage 09까지 성공 게이트를 통과하면 전체 결정·구현·실패·점수를 복기한 최종 보고서를 작성한다.
- Stage 03부터 각 단계 성공 게이트와 점수 확정 뒤 검증된 비보호 프레임워크 변경을 커밋해야 다음 단계로 전환한다. 첫 Stage 03 커밋은 미커밋 Stage 01~02 변경을 함께 포함할 수 있고 Stage 04부터 단계별 독립 커밋을 만든다.

### 3.1 활성 구조화 작업 포인터

- work ID: `7c2c45dc-6a91-4d40-9f04-11f65c418404`
- 상태: `completed`
- snapshot: `data/records/7c2c45dc-6a91-4d40-9f04-11f65c418404.json`
- event 정본: `data/events/work_events.jsonl`
- snapshot hash: `sha256:b4832e2b79bc0433b550fc683da59f23cd0e72b9632a1cea34427554a2f79f93`

요청·승인·제외 범위와 완료 근거는 위 구조화 기록이 소유한다. 이 핸드오프는 프로젝트 단계와 첫 다음 행동만 요약한다.

## 4. 완료된 단계

| 단계 | 판정 | 핵심 결과 |
|---|---:|---|
| Stage 00 | 96/100 완료 | 세션 시작 규칙, 상시·작업 규칙 분리, 실패 지식 폴더, 단계 게이트 구축. 커밋 `8dc034e` |
| Stage 01 | 98/100 완료 | 권위 역할과 문서 유형의 두 축, 문서 언어·배치·생성·보존 계약 구축. 누적 커밋 `0601489` |
| Stage 01.5 | 98/100 완료 | 프로젝트 루트 Obsidian 볼트, 시작 화면, 56개 활성 문서 지도, 11개 단계 보기, 보호 제외 설정 구축. 누적 커밋 `0601489` |
| Stage 02 | 98/100 완료 | JSON 공통 외피, UUIDv4 단일 주소, 엄격 검증, SHA-256, 원자 저장, 13개 회귀 테스트 구축. 누적 커밋 `0601489` |
| Stage 03 | 98/100 완료 | RecordStore·UTF-8 JSON CLI, 기대 hash 갱신, 원자 JSONL append, 오류 상태 2~8, 25개 테스트. 커밋 `0601489` |
| Stage 04 | 98/100 완료 준비 | 작업 요청·event 원장·replay snapshot·상태 전이·세션 독립 재개, 실제 work 완료, 36개 테스트. 경계 커밋 대기 |

Stage 04의 검증된 비보호 변경만 현재 작업트리에 있으며, 사용자 상시 승인에 따라 경계 커밋 성공 뒤 Stage 05로 전환한다.

## 5. 최근 단계 검증 근거

- Stage 01.5: Obsidian 1.12.7 실제 앱 이동, 56개 활성 문서 지도, 보호 대상 링크 0개, 98/100.
- Stage 02 기능: 유효·무효 fixture, 엄격한 UTF-8·JSON·ID·버전·시간·해시 검증, `data/records/<id>.json`, 같은 디렉터리 임시 파일과 원자 교체.
- Stage 02 테스트: 정상 저장·재읽기, Unicode·공백 루트, 잘못된 바이트·NUL·중복 키, 보호 경로, 중복 ID, 덮어쓰기, 교체 실패 보존, 파생 삭제를 포함한 13개 전부 성공.
- Stage 02 구조: 활성 Markdown·지도 직접 대상 각 59개, Stage 02 텍스트 11개, 1,460개 단언, 보호 변경 0건.
- Stage 02 네 가지 확인 모두 통과, 미해결 실패 0건, 자체 점수 98/100.
- 상세 결정·점수·감점: `docs/build/stage-02-file-data-foundation.md#9-사용자-결정-기록`.
- Stage 03 기능: init·create·get·list·update·append·list-events를 library와 CLI 단일 진입점으로 제공.
- Stage 03 테스트: Stage 02 포함 25개, Unicode CLI·기대 불일치·잠금 충돌·저장 유형 우회·stream 손상·교체 실패 보존 전부 성공.
- Stage 03 구조: 활성 Markdown·지도 직접 대상 각 64개, 1,580개 단언, 실제 프로젝트 `data/` 변경 0건, 보호 변경 0건.
- Stage 03 네 가지 확인 모두 통과, 미해결 실패 0건, 자체 점수 98/100. 상세는 `docs/build/stage-03-record-io.md#9-사용자-결정-기록`.
- Stage 04 기능: immutable 요청, 추가 전용 work event, bounded snapshot, 기대 hash 전이, 실패·차단·거부 의미 검증, event-first 복구, UTF-8 stdin CLI를 제공한다.
- Stage 04 실제 검증: work `7c2c45dc-6a91-4d40-9f04-11f65c418404`를 requested→in_progress→completed로 기록하고 원장 replay 뒤 같은 snapshot hash를 확인했다.
- Stage 04 테스트·구조: 누적 36개 테스트, 활성 Markdown 67개·지도 누락 0·링크 오류 0, Python 9개 AST·JSON Schema 4개 파싱, 보호 변경 0건.
- Stage 04 네 가지 확인 모두 통과, 미해결 실패 0건, 자체 점수 98/100. 상세는 `docs/build/stage-04-work-state.md#9-사용자-결정-기록`.

## 6. 실패 원장

현재 미해결 실패와 활성 연속 실패 횟수는 없다.

- Stage 01.5 구조 게이트에서 최고 연속 실패 3회를 두 번 기록했다. 첫 묶음은 구형 .NET 상대 경로 API, 루트 파일 빈 부모, 실제 끊어진 링크였고 링크를 수정한 뒤 전체 재개했다.
- 재개 묶음은 보호 경로 링크, Git sandbox 소유권, `safe.directory` 인수 처리였고 권위 설정 직접 검사로 방법을 바꾼 뒤 전체 게이트가 성공했다.
- 해결 지식은 `failures/windows-validation-command-assumptions.md`, `failures/active-document-link-rot.md`, `failures/obsidian-protected-path-link-leakage.md`에 보존했다.
- Stage 02의 시스템 Python 부재와 ID-주소 중복 가능성은 `failures/runtime-discovery-system-python.md`, `failures/record-id-address-ambiguity.md`에 보존했다.
- Stage 03의 Windows stdio, 잠금-검증 경쟁 구간, 저장 유형 승인 우회, 구조 정본 드리프트는 각각 연결된 `failures/` 사례에 보존했다.
- Stage 04의 event 시각 역행, PowerShell JSON 인수 따옴표 손실, 패치 문맥 불일치는 각각 `failures/work-event-time-regression.md`, `failures/powershell-native-json-argument-quoting.md`, `failures/apply-patch-markdown-prefix.md`에 보존했다.
- 모든 장기 실패 지식의 탐색 정본은 `failures/README.md`다.

## 7. 활성 위험

- Obsidian의 사용자 직접 마우스 탐색은 독립 관찰하지 않았고 URI 기반 실제 앱 이동과 창 상태로 검증했다.
- 활성 문서 지도 갱신은 Stage 08 자동화 전까지 수동이다. 각 단계 종료 시 새 활성 문서 수록과 전체 링크 검사를 반복한다.
- JSON Schema와 Python 실행 검증이 일부 제약을 이중 표현한다. 필드 집합은 회귀 검사하지만 정규식·교차 필드 의미의 완전한 자동 동기화는 아직 없다.
- Stage 03 JSONL은 전체 원자 재작성 방식이라 큰 stream에서 비효율적이며 stale lock은 자동 삭제하지 않는다. Stage 08 전까지 승인된 잔여 위험이다.
- 핸드오프의 활성 work ID·hash 연결과 Obsidian 활성 문서 지도는 Stage 08 자동화 전까지 수동 갱신한다.

## 8. 정확한 재개 체크포인트

첫 미착수 행동:

1. `rules/version-control.md`에 따라 Stage 04 전체 diff와 보호 경로 0건을 다시 확인한다.
2. Stage 04 독립 경계 커밋을 만들고 커밋 객체·포함 경로·커밋 후 작업트리를 검증한다.
3. 성공한 커밋 hash를 이 핸드오프의 완료 표에 반영하면서 Stage 05 work를 새로 만들고 `docs/build/stage-05-knowledge-types.md`를 읽는다.
4. Stage 05 범위·제외·권장 결정을 보고한 뒤에만 구현한다.

## 9. 다음 세션 시작 프롬프트

> `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`를 새 세션 시작 시 한 번 읽고 현재 행동과 일치하는 `rules/*.md`만 선택하라. Stage 00은 커밋 `8dc034e`, Stage 01~03 누적 경계는 `0601489`이며 Stage 04는 98/100 성공 게이트를 통과해 독립 커밋만 남았다. work `7c2c45dc-6a91-4d40-9f04-11f65c418404`는 completed다. Stage 04 커밋을 검증한 뒤 Stage 05를 새 work로 시작하라. 권장 선택과 성공 후 Stage 09까지 전환은 사전 승인됐다. 각 단계 성공 뒤 독립 커밋을 검증해야 다음 단계로 이동한다. 기능·검증·네 가지 확인·실패 지식·100점 평가를 생략하지 말고, 3회 실패 시 기록 후 방법을 바꿔 승인 범위 안에서 재개하라. 보호 데이터·설치·외부 게시·삭제·이동·실질적 범위 확대는 자동 승인 대상이 아니다.
