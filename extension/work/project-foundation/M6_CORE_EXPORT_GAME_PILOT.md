# M6 Core export·게임 개발 pilot 설계

- 문서 역할: `phase-design`
- 단계 ID: `M6`
- lifecycle: `in_progress`
- 목적: 동일 Core revision을 영상과 최소 게임 개발 extension에서 수정 없이 검증한다.
- 상위 설계: [재현 가능한 프로젝트 기반 전체 설계](../PROJECT_FOUNDATION_DESIGN.md)
- 현재 상태: [세션 핸드오프](../../../SESSION_HANDOFF.md)

## 단계 결과

Core가 복사 가능한 폴더가 아니라 version·compatibility·conformance를 가진 foundation product로 검증된다.

## Entry gate

- `M6-E1`: M1~M3 exit gate 전건 통과
- `M6-E2`: M5에서 실제 재사용 가치와 complexity 비용 확인
- `M6-E3`: game pilot의 최소 결과 계약과 별도 domain owner 승인

## 포함 범위

- Core version·compatibility·migration contract
- export manifest와 conformance runner
- empty-domain sample
- 최소 game-development extension pilot
- 영상·게임 양쪽의 동일 Core conformance

## 제외 범위

- 검증 전 별도 Core repository 운영
- 완성형 게임 제작
- YouTube 보고서·작업 사실·Git history 수출
- 두 extension의 규칙·schema·runtime 공유

## Execution slices와 slice gate

### M6-S1 — export contract

Core export에 포함·제외할 파일, version, compatibility와 migration을 고정한다.

Gate `M6-S1-G`: domain identity·task evidence·보호 데이터가 export manifest에 없다.

### M6-S2 — empty-domain conformance

빈 extension에서 Core 자체 계약을 검증한다.

Gate `M6-S2-G`: domain owner가 없어도 Core 회귀와 startup contract가 통과한다.

### M6-S3 — game pilot

최소 게임 개발 domain의 규칙·artifact·workflow owner를 Extension으로 구현한다.

Gate `M6-S3-G`: Core 변경 없이 새 domain owner를 등록하고 최소 acceptance를 통과한다.

### M6-S4 — dual-domain comparison

영상과 게임 extension에서 동일 Core revision을 검증한다.

Gate `M6-S4-G`: 두 extension 상호 참조 0, Core conformance 결과 일치

### M6-S5 — packaging decision

실제 독립 release 필요와 운영 비용을 비교해 별도 package·repository 여부를 결정한다.

Gate `M6-S5-G`: 재사용 증거 없이 repository를 분리하지 않는다.

## Exit gate

- `M6-X1`: 동일 Core revision이 영상·게임에서 수정 없이 통과
- `M6-X2`: 두 extension의 규칙·schema·runtime 상호 참조 0
- `M6-X3`: Core 변경 없이 새 domain owner 등록
- `M6-X4`: export에 영상 작업 사실·보고서·보호 데이터 0
- `M6-X5`: package·repository 결정이 실제 두 domain 운영 증거에 근거

## 중단·복구 조건

- game pilot 때문에 Core에 게임 vocabulary를 넣으려 하면 중단한다.
- 영상 Extension을 template처럼 복제하면 domain owner를 다시 분리한다.
- 두 domain 증거 전 repository 분리를 요구하면 monorepo conformance를 유지한다.

## Transition gate

Core 제품화 완료 뒤에도 version·migration·conformance 유지 비용이 실제 재사용 효과보다 작은지 정기적으로 재평가한다.

## 첫 활성화 행동

M1~M5 결과에서 domain-neutral Core 파일과 영상 전용 파일의 export 후보 목록을 산출한다.
