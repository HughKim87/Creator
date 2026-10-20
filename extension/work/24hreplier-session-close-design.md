# 24HReplier E1·E2 개선 설계

- 목적: 승인된 요청 기록 오류와 작성·평가 근거 불일치만 고친다.
- 읽는 시점: 이 개선을 실행·검증·재개할 때.
- 책임: codex/24HReplier 작업 에이전트. 사용자는 범위·외부 효과를 결정한다.
- 상태: 승인된 필수안의 실행 설계. 현재 진행은 state/24HReplier.md가 소유한다.
- 관련 권위: 사용자 필수안 승인, session-close 스킬, PROJECT_RULES.md 및 선택된 Core 작업·단계·버전 관리 규칙.

## 계약과 소유권

대상은 D:/AI Agent/GitHub/Creator-24HReplier, codex/24HReplier다. 기존 변경 보존 체크포인트 e9587cc에서 시작한다. Core는 읽기 전용이며 gitlink·정책·규칙·다른 워크트리는 변경하지 않는다. 이 세션에서 직접 확인한 스크립트·운영 요청 조립만 근거로 삼고 다른 세션을 수집하지 않는다.

E1은 실제 예시 전송 누락이 확인된 실험 구현 결함이다. E2는 SceneWriter가 여러 구간을 제공하고 FocusedGrounding이 한 구간만 대조하는 코드상 불일치다. 모두 YouTube 댓글 실험·도메인 구현이 소유하며 Core 일반화 대상이 아니다. 추가 모델 평가·단어 차단·점수 보정은 만들지 않는다. 자연스러운 댓글 품질·5~10초 달성은 이 변경으로 입증하지 않는다.

허용: 아래 정확한 소스·검사·상태 변경, 별도 컴파일·모의 요청 검사, 단계별 로컬 커밋, 최종 보고. 제외: 실제 모델 생성·다운로드·설치·OAuth·게시·push·삭제·초기화. 기존 모든 파일과 실험 데이터는 보존한다. 운영 exe는 이번에 덮어쓰지 않고 별도 검증 출력만 만든다.

## 단계 0: 설계 체크포인트

이 문서와 현재 단계 참조를 로컬 커밋하고 git show로 경로·내용을 확인한 뒤 구현한다. 무관한 local change가 없음을 확인한다.

## 단계 1: E1 실제 요청의 단일 조립·기록

- 변경: extension/tests/replier_generation_context_probe.ps1, extension/tests/replier_generation_grounded_input_probe.ps1, 새 extension/tests/replier_probe_request.ps1 및 extension/tests/replier_probe_request_checks.ps1.
- 동작: system→실제 예시→현재 입력 순서로 요청을 한 번 조립·직렬화한다. 기록과 전송은 같은 JSON을 사용한다. 각 결과는 실제 request_sent를 포함하고 요청 직전에도 파일에 남긴다. 기존 v3/v4 결과를 덮어쓰지 않도록 수정된 실험의 출력은 별도 repaired 파일명으로 저장한다.
- 적용: 위 두 실험의 재실행. 예시가 없는 의도적인 실험도 허용한다. 과거 결과를 새 요청의 성과로 재해석하지 않는다.
- 필수 검증: PowerShell parser, 예시 포함·예시 없음·한글 직렬화·모의 HTTP로 받은 바이트와 기록 JSON 일치. 모델/네트워크 없이 두 실제 Post 함수 경계까지 확인한다.
- 성공: 예시 누락이 검사에서 드러나며 기록과 전송에 같은 요청이 사용된다. 실패는 pass로 기록하지 않는다.
- 커밋: E1 경로와 상태만 stage하고 snapshot을 대조한다. 단계 goal·검사 pass·커밋 확인 후 E2로 전환한다.

## 단계 2: E2 작성 당시 근거를 후보와 함께 보존·재사용

- 변경: extension/src/replier/SceneReaction.cs, 새 extension/src/replier/WritingContext.cs, extension/src/replier/FocusedGrounding.cs(필요한 안내만), extension/src/replier/FitScoring.cs, 새 extension/tests/replier_writing_context_checks.cs. 상태 갱신 포함.
- 동작: 작성에 실제 제공한 구간 ID·사실·원문·시각을 단일 구조로 만들고 후보 Material에 보존한다. 실제 작성 메시지와 사실/관계 평가가 이 스냅샷의 같은 근거를 사용한다. 제목은 배경으로 구분하고 제목만으로 새로운 사건을 전제하지 않는다. 서로 다른 구간을 한 사건으로 합치라는 지시는 주지 않는다.
- 호환: 스냅샷 없는 기존 후보는 기존 배정 근거 경계를 유지한다. 나중의 다른 자막·전체 영상 발췌를 새 후보의 사실 근거로 빌리지 않는다. 평가 캐시 버전을 갱신한다. 후편집에도 원래 근거가 남는다.
- 필수 검증: 모의 작성 요청에 들어간 구간과 실제 후보 스냅샷 일치, 두 번째 제공 구간을 평가에서 잃지 않음, 제공하지 않은 구간 불포함, 후보 원문 고정·취소·legacy 경로·추가 호출 없음. 전체 C# 별도 컴파일과 관련 기존 모의 회귀.
- 한계: 모의 검사는 모델의 의미 판정이나 댓글 자연스러움·실행 시간을 증명하지 않는다. 실제 생성 시험은 not_run으로 보고한다.
- 커밋: E2 경로와 상태만 stage, snapshot·검증·근거 보존을 확인한다.

## 완료와 복구

검증 중 문제가 있으면 같은 단계에서 원인을 고치고 영향 검사만 재실행한다. 범위를 넓히는 결정은 재승인한다. 기존 파일을 reset/stash/삭제하지 않으며 복구 판단은 보존 및 단계별 커밋을 기준으로 한다.

검증 산출물은 extension/.runtime/replier-checks/session-close-e1-e2/에만 만든다. 삭제 금지 지시에 따라 이번 생성물도 제거하지 않는다. 이 설계는 끝나면 완료 설계로 표시해 비활성 보존한다. 따라서 스킬의 임시 설계 삭제·정리 커밋은 사용자 지시로 not_applicable이다. E3 빈 줄 정리는 보류한다.

완료 보고는 D:/AI Agent/GitHub/24HReplier-session-close-report.md에 작성한다. 코드 이력은 커밋이 소유하고 현재 상태에는 남은 문제와 다음 행동만 둔다. 최종 저장소·Core 상태, 커밋 경로와 내용, 보고서 존재를 확인한다. 보존·구조 수정 완료와 실제 댓글 품질 해결을 구분한다.
