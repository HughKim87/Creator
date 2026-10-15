# E1 제목·썸네일 벤치마크 개선 설계

- 목적: 성과 근거를 요청받은 제목·썸네일 추천이 실제 유사 영상 확인보다 앞서 나가지 않게 한다.
- 읽는 시점: 이번 E1 구현·검증·정리 전.
- 책임: Creator main 작업 에이전트. 사용자가 main 및 E1 설계·검증·단계별 로컬 커밋을 승인했다.
- 상태: 승인 범위 내 활성 설계. 완료 후 이 파일만 제거하며 이력은 Git이 보존한다.
- 관련 권위: PROJECT_RULES.md, session-close 스킬, Core 작업 계약·단계 작업·버전 관리 규칙.

## 계약과 경계

- 대상: D:/AI Agent/GitHub/Creator, main, host. 시작 HEAD f48077e4ebd7df7bf70aa13f1604cd43b3465836.
- 입력: 이 대화에서 벤치마크 이전의 반복 추천과 이후 실측 비교, 현재 youtube-title-thumbnail 스킬 및 package-format.md. 다른 세션은 수집하지 않는다.
- 원하는 결과: 요청 trigger → 실제 비교 항목 → 관측/해석 분리 → 적용·한계 보고의 절차가 기존 스킬 하나에 있고 패키지 안내가 근거 위치를 제공한다.
- 허용: 해당 스킬·패키지 안내·번들 해시·main 현재 상태 수정, 설계/구현/정리 로컬 커밋 및 저장소 밖 보고.
- 제외: Core, 다른 워크트리, 영상 원본·산출물, 보호 inputs/outputs, 설치, 외부 쓰기, push. 실제 CTR 향상을 주장하지 않는다.
- 소유권: 게임·영상 도메인 품질 절차이므로 기존 Extension 스킬 보강. Core 일반화·route 변경 없음.
- 적용: 벤치마크 요청 또는 실제 데이터에 근거한 제목·썸네일 성과 추천. near-miss: 단순 어법 수정·사용자 승인 제목의 그대로 적용. 최신 사용자 지시로 조사 생략을 요청하면 잠정 창작안으로 보고한다.
- 사용자 추가 결정: 승인 범위를 넘는 변경이 발견될 때만 필요.

## 단계와 완료 조건

0. 이 설계와 활성 상태를 정확한 경로로 커밋한다. git show로 설계 snapshot 및 경로를 확인한 후 구현.
1. SKILL.md에 조건부 벤치마크 절차를 추가하고 references/package-format.md에 선택 근거 기록 위치를 설명한다. 새 필수 schema나 런타임 제한은 도입하지 않는다. 번들 해시는 바뀐 두 파일만 갱신한다.
   - 사례의 URL/제목/채널/조회수/업로드 경과/확인 시각과 실제 본 썸네일 문구·구도를 구분한다.
   - 가능하면 한국 대상 유사 편집 영상과 다른 채널을 비교한다. 작은 채널 및 낮은 성과 사례도 선택 편향 검토에 사용하되 확보 불가를 공개한다.
   - 조회수는 CTR·인과 효과의 증거가 아님을 유지하고, 조회수 확인과 이미지 직접 확인을 구분한다. 확인 불가를 추측으로 채우지 않는다.
   - 최소 게이트: 관련 title package/session improvement unittest, bundle inspect, git diff --check, 적용/near-miss/자료 부족 시나리오 수동 문맥 검토. 문구 정규식 통과를 의미 검증으로 주장하지 않는다.
   - 실패 시 원인과 영향만 해결하고 같은 게이트 재실행. 무관한 코드 개선은 제외. 통과 후 정확한 변경만 커밋하고 git show snapshot 경로 및 blob 일치 확인.
2. 이 설계만 제거하고 main 상태에서 활성 설계 표시를 해제해 정리 커밋한다. 보고를 작성한 뒤 parent/Core Git 상태와 최종 snapshot을 확인한다.

## 임시 자원·보고·복구

- 이번 임시 문서: extension/docs/session-close-benchmark-design.md. 승인된 정리 범위로 완료 후 삭제. 다른 파일 삭제 없음.
- 검사는 bytecode 금지, TEST_TMPDIR=extension/work 경로를 사용한다. 기존 runtime/data/cache 내용은 열거하거나 변경하지 않는다. unittest 소유 TemporaryDirectory만 정상 정리한다.
- 최종 보고: C:/Users/Hugh/.codex/visualizations/2026/10/10/01a12678-a53a-7d13-bffd-5f4877b161fc/session-close-benchmark-report-2026-10-16.md. 보존 문서이며 삭제 대상 아님.
- 단계 실패 또는 새 무관 변경 발견 시 멈추고 상태를 남긴다. 자동 reset/stash/기존 파일 삭제는 하지 않는다. 복구 근거는 마지막 검증 commit.
- 완료: E1 구현·최소 게이트·각 commit 확인·임시 설계 제거·외부 보고·Git clean. 실서비스 CTR 검증 및 독립 Agent 행동 재현은 not_run으로 보고.
