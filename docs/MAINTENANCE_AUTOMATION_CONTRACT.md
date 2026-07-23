# 유지보수·검증 자동화 계약

- 목적: 실제로 반복된 source drift, 중복, 문서 목록·링크 검사, 컨텍스트 재평가 비용을 가장 작은 수동 fail-closed 명령으로 줄인다.
- 읽는 시점: 기반 최신성·중복·파생 inventory·구조 검증·컨텍스트 평가를 점검하거나 자동화 실패를 진단할 때.
- 책임: 정본은 원 문서·record·event가 계속 소유하고 `MaintenanceService`는 읽기 전용 보고·파생 재생성·검증만 수행한다.
- 상태: Stage 08 활성 계약.
- 선행 계약: [지식 수명주기](KNOWLEDGE_LIFECYCLE_CONTRACT.md), [선택 컨텍스트](CONTEXT_PACKAGE_CONTRACT.md), [Obsidian 검토 환경](obsidian/OBSIDIAN_REVIEW_CONTRACT.md).

## 승인된 자동화와 실행 방식

| 명령 | 기본 동작 | 쓰기 여부 | 성공 기준 |
|---|---|---:|---|
| `maintenance-scan` | source drift, 해결 실패 정본 구조, 의존 record, exact current 중복, inventory 상태, 비용 관측 | 없음 | drift·실패 정본 오류·중복 0, inventory 일치 |
| `maintenance-verify` | scan + Markdown UTF-8/NUL/공백/링크 + `project-data:v1` exact 계약 + `project-artifact:v1` semantic drift + Python AST + JSON schema + 보호 변경 + 현재 상태 링크 | 없음 | 오류 0, scan pass |
| `maintenance-inventory` | 생성될 Obsidian inventory와 현재 파일 비교 | 없음 | bytes 일치 |
| `maintenance-inventory --write` | 정본 경로에서 파생 inventory를 원자 교체 후 재검증 | 파생 파일 1개만 | 쓰기 후 expected bytes 일치 |
| `maintenance-evaluate` | 명시 JSON의 컨텍스트 기대·금지·크기·절감·재현성 평가 | 없음 | 모든 평가 check 통과 |

모든 명령은 사용자가 시작하는 수동 실행이다. Hook, CI, 예약 작업, 백그라운드 감시는 만들지 않는다. 오류·입력 불일치·Git 조회 실패는 성공처럼 처리하지 않고 CLI 비성공으로 반환한다.

## 최신성·중복 경계

- scan은 local source의 현재 bytes와 저장 hash, drift source 의존 record를 읽기 전용으로 찾는다.
- 모든 `failures/*.md` 정본을 strict UTF-8로 직접 파싱해 해결 상태와 필수 절을 확인한다. 사례별 projection이나 lifecycle 상태는 만들거나 갱신하지 않는다.
- `LifecycleService.audit`와 달리 scan은 review event를 추가하거나 상태를 바꾸지 않는다.
- 자동 중복은 current knowledge의 공백 제거·casefold 후 완전 동일 statement와 canonical failure 문서의 완전 동일 제목을 탐지한다.
- 의미 유사도·충돌 판정·병합·삭제·current 선택은 자동화하지 않는다.
- drift·중복 경고 허용치는 각각 0건이다. 발견 시 사람이 결과를 검토하고 기존 lifecycle 명령으로 처리한다.

## 파생 문서 inventory

`docs/obsidian/GENERATED_DOCUMENT_INVENTORY.md`는 Git tracked Markdown과 현재 작업의 명시적 Markdown 변경에서 파생한다.

- `backup`, `inputs`, `outputs`, `.git`, `.obsidian`은 source 목록에서 제외한다.
- 경로·첫 H1 제목만 표시하고 규칙·상태·결정 본문을 복제하지 않는다.
- 생성 시각과 무작위 값을 넣지 않아 같은 source 집합에서 같은 bytes를 만든다.
- 자기 재귀 색인을 막기 위해 생성 파일 자체는 source 목록에서 제외한다.
- 파일을 지운 뒤 같은 명령으로 재생성할 수 있다.
- 사람이 분류한 [전체 문서 지도](obsidian/DOCUMENT_MAP.md)는 시작 화면 역할을 유지하고 generated inventory를 연결한다.

## 검증과 보호 경계

verify는 보호·역사 경계를 먼저 필터링한 활성 Markdown만 읽는다. 로컬 링크가 루트 밖이나 보호 segment로 향하면 실패한다. Git status에서 `inputs`·`outputs` 변경이 보이면 내용을 읽지 않고 경로 수준 오류로만 보고한다.

Python은 AST parse, schema는 JSON parse, 문서는 strict UTF-8·NUL 0·후행 공백 0을 확인한다. README와 Obsidian 지도에서 `SESSION_HANDOFF.md` 연결, 문서 지도에서 generated inventory 연결도 확인한다.

## 비용·효과 관측

scan은 다음을 JSON으로 반환한다.

- 활성 문서 수·Unicode 문자·UTF-8 bytes
- canonical failure 문서 수
- source·knowledge·decision·lifecycle_state·work_state 수와 legacy `failure_knowledge` 수
- lifecycle·work event 수
- generated 파일 수
- 실행 시간 millisecond와 5,000ms 초과 경고

5초는 현재 저장소에서 수동 scan의 경고 기준이며 다른 환경의 강제 성능 보장은 아니다. 오류 0 기준은 성능 경고와 무관하게 유지한다. 자동화가 추가하는 유지 파일은 service 1, test 1, 계약 1, generated inventory 1로 제한해 자기증식을 관찰한다.

## 컨텍스트 재평가

평가 정의는 영구 package가 아니라 호출 JSON으로 제공한다. 각 항목은 이름, ContextService request, 기대·금지 record ID, 최대 문자, 최소 절감률, 최대 무관 record를 가진다.

- 실행 시 현재 활성 Markdown 기준선을 다시 측정해 request에 넣는다.
- 같은 request를 두 번 실행해 완전 일치와 fingerprint 재현성을 검사한다.
- 필수 누락, 금지 포함, 무관 초과, 문자 초과, 절감 미달을 각각 구분한다.
- 평가 결과는 보고만 하며 package·지식·lifecycle을 저장하거나 변경하지 않는다.

## 보존·중단·후속

- superseded·rejected·retired record, legacy failure projection과 과거 event는 보존하고 이번 단계에서 정리 명령을 만들지 않는다.
- 파생 inventory 쓰기 외 상태 변경은 Stage 06~07의 명시 명령과 사용자 승인 경계를 사용한다.
- 자동화가 오류를 숨기거나 수동 비용보다 큰 파일·시간·문맥을 만들면 활성화하지 않고 계약·단계 보고에 원인을 남긴다.
- 도메인별 유지 규칙·추천·영상 제작 자동화는 Stage 09 범위다.
