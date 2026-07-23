# 세션 핸드오프

- 갱신일: 2026-07-23
- 역할: 채팅 기억 없이 현재 검증 상태와 첫 다음 행동을 재구성하는 단일 활성 상태 정본
- 현재 단계: Stage 00~09 구축·최종 복기·커밋 완료 — 새 기능 자동 착수 없음
- 이전 작업: 최종 복기 보고서 최초 독립 커밋 `4a64391`
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

- work ID: `763e0e85-d729-43a4-b83f-8b218b5b661d`
- 상태: `completed`
- snapshot: `data/records/763e0e85-d729-43a4-b83f-8b218b5b661d.json`
- event 정본: `data/events/work_events.jsonl`
- snapshot hash: `sha256:c083e8e05bcc8cf9b368c023ce92adfd343863be8269b82453de2d0cd468c7e5`

요청·승인·제외 범위와 완료 근거는 위 구조화 기록이 소유한다. 이 핸드오프는 프로젝트 단계와 첫 다음 행동만 요약한다.

## 4. 완료된 단계

| 단계 | 판정 | 핵심 결과 |
|---|---:|---|
| Stage 00 | 96/100 완료 | 세션 시작 규칙, 상시·작업 규칙 분리, 실패 지식 폴더, 단계 게이트 구축. 커밋 `8dc034e` |
| Stage 01 | 98/100 완료 | 권위 역할과 문서 유형의 두 축, 문서 언어·배치·생성·보존 계약 구축. 누적 커밋 `0601489` |
| Stage 01.5 | 98/100 완료 | 프로젝트 루트 Obsidian 볼트, 시작 화면, 56개 활성 문서 지도, 11개 단계 보기, 보호 제외 설정 구축. 누적 커밋 `0601489` |
| Stage 02 | 98/100 완료 | JSON 공통 외피, UUIDv4 단일 주소, 엄격 검증, SHA-256, 원자 저장, 13개 회귀 테스트 구축. 누적 커밋 `0601489` |
| Stage 03 | 98/100 완료 | RecordStore·UTF-8 JSON CLI, 기대 hash 갱신, 원자 JSONL append, 오류 상태 2~8, 25개 테스트. 커밋 `0601489` |
| Stage 04 | 98/100 완료 | 작업 요청·event 원장·replay snapshot·상태 전이·세션 독립 재개, 실제 work 완료, 36개 테스트. 커밋 `519ff30` |
| Stage 05 | 97/100 완료 | source·knowledge·decision·failure projection 순차 도입, 55개 테스트, 48개 실제 record·21개 실패 정본 hash 검증. 커밋 `b9ef127` |
| Stage 06 | 97/100 완료 | event-first 수명주기, 승인 전이, drift·충돌·대체·폐기, 68개 테스트, 54개 snapshot·66개 event replay. 커밋 `93c516e` |
| Stage 07 | 97/100 완료 | 직접 선택·실제 필드 필터·current 문자열 후보·비영구 package, 79개 테스트, 대표 평가 3건 96% 이상 절감. 커밋 `a383bbd` |
| Stage 08 | 97/100 완료 | 수동 read-only scan·fail-closed verify·결정론 inventory·입력 기반 재평가, 누적 87개 테스트. 커밋 `73c9435` |
| Stage 09 | 97/100 완료 | 별도 유튜브 evidence pack adapter, 실제 domain work·candidate 환류, 누적 95개 테스트. 커밋 `825e9ab` |

Stage 05는 05A 출처 → 05B 지식 → 05C 결정 → 05D 실패 projection 순으로 각각 검증한 뒤 하나의 Stage 05 경계 커밋으로 닫는다.

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
- Stage 05 소단계: 05A는 누적 42개, 05B는 47개, 05C는 51개, 05D와 전체는 55개 테스트로 각각 독립 통과했다.
- Stage 05 실제 데이터: source 23건, knowledge 1건, decision 1건, failure_knowledge 21건이며 전체 common-record 외피·참조·projection hash를 검증했다.
- Stage 05 구조: 활성 Markdown 70개·실패 정본 21개·Python 11개·JSON Schema 8개, 지도·로컬 링크·보호 링크 오류 0건.
- Stage 05 네 가지 확인 모두 통과, 미해결 실패 0건, 자체 점수 97/100. 상세는 `docs/build/stage-05-knowledge-types.md#9-사용자-결정-기록`.
- Stage 06 기능: candidate/current/review_required/superseded/rejected/retired 상태, 승인 전이, 양방향 충돌, current 선택, event-first rebuild, 사건 기반 audit, failure projection 원본 보존 개정을 구현했다.
- Stage 06 실제 데이터: 기존 46개 지식 record를 등록하고 drift·stale record 6건을 새 record로 대체했으며 candidate 1·current 47·superseded 6, 재감사 finding 0을 확인했다.
- Stage 06 테스트·구조: 누적 68개 테스트, 54개 snapshot과 66개 event 전수 replay, 활성 Markdown 72개·링크 497개 오류 0, Python 8개 AST·JSON Schema 10개 파싱, 보호 변경 0건.
- Stage 06 네 가지 확인 모두 통과, 미해결 실패 0건, 자체 점수 97/100. 상세는 `docs/build/stage-06-knowledge-lifecycle.md#9-사용자-결정-기록`.
- Stage 07 기능: 직접 문서·current record 선택, 유형·상태·scope·source role 필터, current 단순 문자열 후보, 선택·제외 이유·크기·fingerprint package를 구현했다.
- Stage 07 실제 평가: 활성 Markdown 74개 기준선에서 기존 지식·새 지식·실패 재사용 package가 각각 필수 2/2, 금지·무관 0, 12,000자 이하, 96% 이상 절감, 재실행 일치를 통과했다.
- Stage 07 테스트·구조: 누적 79개 테스트, lifecycle 65개 snapshot·91개 event replay, current 실패 23건 전수 검증, Markdown 74개·링크 510개 오류 0, Python 9개 AST·JSON Schema 11개 파싱, 보호 변경 0건.
- Stage 07 네 가지 확인 모두 통과, 미해결 실패 0건, 자체 점수 97/100. 상세는 `docs/build/stage-07-context-retrieval.md#9-사용자-결정-기록`.
- Stage 08 기능: `maintenance-scan/verify/inventory/evaluate`를 구현하고 Hook·CI·예약·자동 병합·삭제·current 변경은 제외했다.
- Stage 08 실제 결과: drift·중복·구조 오류 0, inventory 10,130 bytes 일치, scan 약 1.9초, 활성 Markdown 78개·링크 607개·Python 10개·schema 11개, 누적 87개 테스트 성공.
- Stage 08 컨텍스트 재평가: 315,486자 기준선에서 기존·신규·실패 package가 10,203자·3,690자·4,418자, 96.77%·98.83%·98.60% 절감, 필수 1·금지/무관 0·재현성 통과.
- Stage 08 네 가지 확인 모두 통과, 미해결 실패 0건, 자체 점수 97/100. 상세는 `docs/build/stage-08-maintenance-automation.md#9-사용자-결정-기록`.
- Stage 09 기능: 별도 `youtube_domain` service·CLI, 요청/결과 schema, 계약, 추적 example을 추가하고 공통 `ContextService`만 소비했다.
- Stage 09 실제 실행: domain work `82dee601-21d1-400a-8d0e-98bc8f32c0ea` 완료, current knowledge/source와 문서 각 1건, 3,690자·6,028 bytes·98.83% 절감, 두 fingerprint와 비영구성 검증.
- Stage 09 승인·환류: 창작 방향은 user `review_required`, knowledge `a77456b1-28e8-4d31-8f51-c04cff89c2db`는 candidate이며 current 검색 0·도메인 입력 exit 2를 확인했다.
- Stage 09 테스트·구조: 누적 95개 성공, 활성 Markdown 80개·링크 628개·Python 14개·schema 13개, drift·중복·오류 0, inventory 10,521 bytes. 외부 앱은 해당 없음, 사용자 창작 확인은 미수행으로 분리 보고했다.
- Stage 09 네 가지 확인 모두 통과, 미해결 실패 0건, 자체 점수 97/100. 상세는 `docs/build/stage-09-domain-integration.md#9-사용자-결정-기록`.
- 최종 복기 보고서는 11개 단계의 결정·구현·실패·점수·경계 커밋·잔여 위험·다음 선택을 교차 정리했다. 최종 보고 변경 후 81개 문서·636개 링크·14개 Python·13개 schema, drift·중복·오류 0, 누적 95개 테스트를 통과했다.

## 6. 실패 원장

현재 미해결 실패와 활성 연속 실패 횟수는 없다.

- Stage 01.5 구조 게이트에서 최고 연속 실패 3회를 두 번 기록했다. 첫 묶음은 구형 .NET 상대 경로 API, 루트 파일 빈 부모, 실제 끊어진 링크였고 링크를 수정한 뒤 전체 재개했다.
- 재개 묶음은 보호 경로 링크, Git sandbox 소유권, `safe.directory` 인수 처리였고 권위 설정 직접 검사로 방법을 바꾼 뒤 전체 게이트가 성공했다.
- 해결 지식은 `failures/windows-validation-command-assumptions.md`, `failures/active-document-link-rot.md`, `failures/obsidian-protected-path-link-leakage.md`에 보존했다.
- Stage 02의 시스템 Python 부재와 ID-주소 중복 가능성은 `failures/runtime-discovery-system-python.md`, `failures/record-id-address-ambiguity.md`에 보존했다.
- Stage 03의 Windows stdio, 잠금-검증 경쟁 구간, 저장 유형 승인 우회, 구조 정본 드리프트는 각각 연결된 `failures/` 사례에 보존했다.
- Stage 04의 event 시각 역행, PowerShell JSON 인수 따옴표 손실, 패치 문맥 불일치는 각각 `failures/work-event-time-regression.md`, `failures/powershell-native-json-argument-quoting.md`, `failures/apply-patch-markdown-prefix.md`에 보존했다.
- Stage 05의 진행 체크포인트 부재와 로컬 source 목록 실패 전파는 새 원인 문서로, export·patch 문맥·PowerShell pipe·고정 UTC fixture 재발은 기존 원인 문서에 병합했다.
- Stage 05 경계 게이트의 Git 소유권 옵션·work service API·반환 hash 위치 가정은 최고 연속 실패 3회로 기존 Windows 검증 명령 사례에 병합했고, 실제 객체 선관찰 후 전체 게이트를 재개했다.
- Stage 06의 Windows `rg` 경로 와일드카드와 PowerShell UTF-8 pipe 재발은 기존 원인 정본에 병합했고, decision fixture 계약 구조 가정은 새 원인 문서에 기록했다. 세 원인 모두 수정 후 68개 테스트와 통합 게이트를 통과했다.
- Stage 07의 PowerShell UTF-8 pipe 재발은 손상 knowledge를 lifecycle로 보존·대체한 뒤 기존 원인 정본에 병합했고, Windows 줄바꿈 크기 측정 불일치는 새 원인 문서로 기록했다. 두 원인 모두 수정 후 79개 테스트와 대표 평가를 통과했다.
- Stage 08의 `context-search --query` 공개 옵션 가정은 기존 Windows 검증 명령 사례에 병합했다. `--help` 확인 뒤 실제 `--text`로 새 지식·실패 지식을 각각 1건 검색했고 failure projection을 새 hash로 교체했다.
- Stage 08 통합 게이트 1차는 기존 Python bytecode cache 1개를 발견해 실패 처리했다. 경계 확인 후 cache만 정리하고 같은 환경에서 재생성 0과 전체 게이트 성공을 확인해 새 실패 정본에 보존했다.
- Stage 08 work 완료 전이에 `next_action`을 함께 보낸 1회 계약 실패는 새 실패 정본에 보존했다. 실패 전후 hash 불변을 확인하고 `next_action`을 제거한 전이로 work를 `completed` 상태로 닫았다.
- Stage 09의 중첩 미추적 Markdown inventory 누락과 예상 native stderr 조기 중단은 기존 Windows 검증 명령 사례에 병합했다. `--untracked-files=all`과 exit code 직접 판정으로 각각 회귀 검증했다.
- Stage 09의 별도 `src/youtube_domain` AST 검증 누락은 구현 폴더·정보 구조 드리프트 사례에 병합하고 Python 검증을 `src/**/*.py`로 일반화했다.
- 최종 보고 교차검사기의 literal `Stage 01.5` 가정은 기존 Windows 검증 명령 사례에 병합했다. 실제 표 행 pattern과 단계 점수 행 11개 count로 보정해 성공했다.
- 모든 장기 실패 지식의 탐색 정본은 `failures/README.md`다.

## 7. 활성 위험

- Obsidian의 사용자 직접 마우스 탐색은 독립 관찰하지 않았고 URI 기반 실제 앱 이동과 창 상태로 검증했다.
- 사람이 분류한 문서 지도는 수동 검토 화면으로 유지하고, 전체 활성 경로 inventory는 Stage 08 결정론 파생 명령으로 재생성한다. verify는 둘의 핵심 연결과 전체 로컬 링크를 검사한다.
- JSON Schema와 Python 실행 검증이 일부 제약을 이중 표현한다. 필드 집합은 회귀 검사하지만 정규식·교차 필드 의미의 완전한 자동 동기화는 아직 없다.
- Stage 03 JSONL은 전체 원자 재작성 방식이라 큰 stream에서 비효율적이며 stale lock은 자동 삭제하지 않는다. Stage 08 전까지 승인된 잔여 위험이다.
- 핸드오프의 활성 work ID·hash와 단계 경계 설명은 여전히 사람이 명시적으로 갱신하며 verify는 경로 연결만 검사한다.
- drift했던 source `51a05a01-1c72-4f66-91f6-c763d7f3050a`와 의존 지식은 역사 record로 보존하고 current replacement에 연결했다. 옛 source의 explicit verify 실패는 superseded 근거이며 기본 current 결과에서 제외된다.
- lifecycle snapshot 탐색과 maintenance scan은 현재 record·문서 수에 선형이고 다중 record 개정은 완전한 단일 트랜잭션이 아니다. event-first·사전 검증·보존 대체로 보완했고 실제 scan 약 1.7초라 5초 경고 전에는 인덱스를 도입하지 않는다.
- context의 current record·활성 문서 선택은 선형 순회이고 검색 필드는 유형별 명시 분기다. Stage 08 evaluate가 고정 payload 재평가를 자동화했지만 평가 정의 자체는 호출자가 명시한다.
- 첫 유튜브 adapter는 full context를 stdout으로 반환하며 자동 저장하지 않는다. 보호 원본·외부 앱·대본·편집·게시 품질은 검증하지 않았다.
- Stage 09 example의 315,497자 기준선은 Stage 08 경계 snapshot이다. 다른 기준선으로 평가하려면 요청을 명시 갱신해야 한다.
- 재사용 절차 candidate는 current 검색과 기본 domain 입력에서 제외된다. 사용자 또는 standing policy가 별도 승인하기 전에는 승격하지 않는다.

## 8. 정확한 재개 체크포인트

첫 미착수 행동:

1. 새 기능·단계를 자동 시작하지 않고 사용자의 다음 선택을 기다린다.
2. 다음 요청이 오면 최종 복기 보고서의 잔여 위험·선택지와 실제 측정 근거를 먼저 대조한다.
3. 보호 데이터·외부 앱·추가 도메인은 새 승인 범위가 있을 때만 다룬다.

## 9. 다음 세션 시작 프롬프트

> `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`를 새 세션 시작 시 한 번 읽어라. Stage 09 커밋은 `825e9ab`, 최종 복기 보고서 최초 커밋은 `4a64391`, 보고서는 `reports/2026-07-23_codex_stage00-09_프로젝트_구축_최종_복기_보고서.md`(사용자가 2026-07-23 `codex_` 접두어로 파일명 변경), work `763e0e85-d729-43a4-b83f-8b218b5b661d`는 `completed`다. Stage 00~09 구축은 완료됐으므로 새 기능·단계를 자동 시작하지 말고 사용자의 다음 선택을 기다려라. 보호 데이터·설치·외부 게시·삭제·이동·실질적 범위 확대는 새 승인 없이는 수행하지 않는다.

## 10. 실패 지식 record 구조 검토 메모

- 현재 실패 Markdown 한 사례를 개정해 projection을 교체하면 새 `source`, 새 `failure_knowledge`, 두 대상의 `lifecycle_state`가 생성되어 사례 개정당 `data/records/` JSON 네 개가 늘어난다. 별도의 전이 이력은 `data/events/lifecycle_events.jsonl`에도 추가된다.
- 이 네 개 구조는 출처·구조화 해석·각 대상의 현재 상태를 독립적으로 감사하는 범용 지식 수명주기 모델의 결과이며, 실패 사례 하나에 본질적으로 필요한 최소 구조는 아니다.
- 현재 실패 사례에서는 source와 failure projection이 함께 생성·전이되고, 문서 경로와 hash가 `failure_knowledge`에도 있으며, 전이 이력도 event 원장에 보존된다. 따라서 두 대상의 책임과 상태가 실질적으로 중복되는지 재검토할 가치가 있다.
- 단순화 후보는 사례 개정당 하나의 복합 `failure_knowledge` record가 정본 경로·문서 hash·구조화된 증상·원인·해결·현재 상태·이전 및 대체 record ID를 함께 소유하고, 전이 이력은 기존 lifecycle event 원장에 남기는 방식이다.
- 이 내용은 구조 개선 검토 메모이며 아직 승인되거나 구현된 계약이 아니다. 현재 `KNOWLEDGE_TYPES_CONTRACT.md`, `KNOWLEDGE_LIFECYCLE_CONTRACT.md`, 기존 record와 event 보존 정책은 그대로 유효하며 기존 JSON을 임의로 삭제하거나 병합하지 않는다.
- 후속 구현은 별도 사용자 승인 아래 감사 가능성, event replay, drift 탐지, current 선택, 기존 data 이관, 회귀 테스트 영향을 먼저 설계·검증한 뒤 진행한다.
