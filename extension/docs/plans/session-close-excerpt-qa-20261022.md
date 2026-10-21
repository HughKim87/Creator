# 원본 발췌·청취 검증 실행 보강 설계

- 목적: 승인된 E2·E3의 실행 누락을 기존 Extension 절차 안에서 보완한다.
- 읽는 시점: 이번 개선의 구현·검증·정리 단계에서만.
- 책임: 에이전트가 승인 범위의 단계별 로컬 커밋을 수행하고 사용자가 범위 변경을 결정한다.
- 상태: 활성 전체 설계. 현재 단계는 state/main.md가 소유한다.
- 관련 권위: 2026-10-22 사용자 개선 지시, session-close, Creator 정책 및 Core 작업·단계·버전 관리 규칙.

## 계약과 소유권

대상은 D:/AI Agent/GitHub/Creator의 main이다. Core는 읽기 전용이며 gitlink도 바꾸지 않는다. E2·E3는 기존 영상 규칙과 validator가 충분하지만 실제 요청 해석·검수 전달에서 적용을 누락한 execution_gap이다. 새 schema·validator·전역 스킬·route를 추가하지 않고 기존 workflow와 규칙의 실행 순서를 보강한다. 원본 발췌가 지정된 작업과 발화 경계 검수가 적용 대상이며 새 대사 작성·무음 영상·단순 기술 검사에는 발췌나 청취 통과를 강제하지 않는다.

허용 범위는 Extension 문서·기존 관련 검사 실행·현재 상태·보고서·단계별 로컬 커밋이다. 실제 영상 재편집·청취 통과 선언·미디어 이동·설치·외부 게시·push는 제외한다. 이번 대화와 현재 소유 문서만 근거로 사용한다. 보호 미디어와 다른 job은 열지 않는다.

## 단계와 필수 게이트

0. 이 설계를 단독 커밋하고 snapshot 경로·내용을 확인한다.
1. E2: video-editing-intake-and-instructions.md 및 VIDEO_EDITING_WORKFLOW_CONTRACT.md에서 원본 발췌/새 대사 요청 구분, 실제 대사와 source 좌표 확인, 교정의 anchor·feedback 연결, 결과 대조 순서를 명시한다. 기존 task·editorial state owner를 사용하며 별도 유지 문서를 늘리지 않는다. 관련 editorial_state 회귀와 발췌/창작/미확정 source/피드백 누락 수동 시나리오를 확인하고 단계 커밋한다.
2. E3: video-editing-validation-and-delivery.md 및 같은 workflow에서 자동 사전검수·직접 청취·완료 주장을 분리하는 실행·보고 순서를 보강한다. MP4 검수본도 품질 미검증을 최종 완료로 부르지 않으며 XML 후보/완료 경로는 유지한다. review_delivery 및 editorial_state 회귀와 ASR-only/직접 검수/기술 검사만 요청한 경우의 시나리오를 확인하고 단계 커밋한다.
3. 이 작업에서 만든 정확한 임시 설계 extension/docs/plans/session-close-excerpt-qa-20261022.md만 제거하고 별도 정리 커밋한다. 고유 설계·검증 근거는 앞선 Git 이력과 최종 보고서에서 복원한다. 다른 설계·사용자 자료는 정리하지 않는다.
4. Core 제안서 extension/docs/reports/CORE_ARTIFACT_STORAGE_PROPOSAL_2026-10-22.md와 최종 보고서 extension/docs/reports/SESSION_CLOSE_EXTENSION_2026-10-22.md를 보존하고 별도 보고 커밋한다. Core 제안은 도메인 중립 원칙·예외·소유자·반례·검증을 제시하며 구현하지 않는다. 기존 job 재검토 보고서는 역사 분석임을 명시하고 job 상태는 최종 보고서를 가리킨다.

각 단계는 직전 단계 goal·필수 게이트 pass·실제 커밋 snapshot 확인 후 전환한다. 구조·문구 대조와 관련 합성 회귀는 실제 A/V·독립 Agent 재현과 구분한다. route가 변하지 않으므로 새 route fixture/콜드 재현은 비해당이며 의미 gate를 완화하지 않는다. 문서만 바꾸는 이번 작업에 구현을 복사하는 새 테스트를 쓰지 않는다.

## 현재 단계별 실행 조건

각 구현 단계는 main·Core 상태와 승인된 예상 변경만 있는지 확인하고 정확한 문서만 stage한다. 공통 현재 상태는 state/main.md만 갱신한다. 미해결 검사 실패나 무관한 변경이 있으면 다음 단계로 넘어가지 않는다. 복구 근거는 직전 검증 커밋이며 사용자 파일 reset·stash·clean은 하지 않는다.

필수 게이트는 문서의 scope/최신 교정/원본 근거/청취 상태 대조, 기존 관련 회귀, git diff --check, snapshot 경로·내용 일치, Core 불변, 최종 main clean이다. 회귀 실패가 기존 환경 원인이면 사실을 확인하고 통과로 바꾸지 않는다. 실제 영상 품질은 이번 구현의 성공 조건이 아니며 not_run으로 보존한다.

## 종료 조건

E2·E3 실행 순서가 기존 소유 문서에 반영되고 필수 게이트와 단계 커밋이 확인돼야 한다. Core는 미수정이며 제안서만 남긴다. 임시 설계 삭제는 별도 커밋되고 보고서는 내부에 존재해야 한다. Git 추적 밖 job 근거·상태는 same-workspace이며 독립 clone 재현으로 주장하지 않는다. 범위가 확장되는 결정만 다시 확인한다.
