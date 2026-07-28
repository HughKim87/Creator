# 재현 가능한 프로젝트 기반 전체 설계

- 문서 역할: `overall-design`
- 목적: 새 컴퓨터에서도 검증 가능한 품질을 재현하고 다른 도메인에 이식할 수 있는 프로젝트 기반의 단계 지도와 불변식을 소유한다.
- 독자: 개선 방향을 승인하는 사용자와 현재 단계를 설계·실행하는 프로젝트 에이전트
- 권위: 사용자 목표와 `PROJECT_RULES.md`; 현재 상태는 [세션 핸드오프](../../SESSION_HANDOFF.md)가 별도로 소유한다.
- 상태: 활성
- 선택 근거: [방향 분석과 근거](../reports/codex_2026-07-28_재현가능한_프로젝트_기반_방향분석과_개선계획.md)

## 최종 목표

1. tracked clone과 선언된 bootstrap만으로 비보호 결정론적 검증을 재현한다.
2. 규칙을 실행·검증·실패 처리·증거에 연결해 결과의 최저 품질선을 만든다.
3. 모든 controlled 작업을 설계와 실행으로 나누고 단계 gate 없이는 전이하지 않는다.
4. 성공·실패를 다음 작업의 더 짧은 절차로 환류한다.
5. 문서·규칙·자동화가 실제 효과보다 커지지 않는지 단계마다 재평가한다.
6. 영상 domain과 결합하지 않은 Core를 추후 게임 개발 프로젝트에서도 사용한다.

## 불변식과 금지 범위

- Core는 특정 domain identity·artifact owner·업무 사실을 소유하지 않는다.
- Extension은 상위 router가 선택한 Core interface만 사용하며 Core가 Extension을 직접 라우팅하지 않는다.
- 구조 품질은 자동 gate가, 창작·의미 품질은 replay·검수·사용자 승인이 소유한다.
- 보호 데이터·외부 서비스·비용·게시·설치는 exact 승인 없이 단계 성공 조건에 넣지 않는다.
- 현재 상태는 `SESSION_HANDOFF.md`, 단계별 exact gate는 현재 phase design, 완료 상세는 Git이 소유한다.
- 미래 단계는 짧은 `planned` 계약만 유지하고 exact 파일 범위·명령·구현 상세는 활성화 전까지 확정하지 않는다.

## 단계 지도

| 단계 | 선행 | 한 문장 목표 | 성공 정의 | 상세 설계 |
|---|---|---|---|---|
| M0 기준·목표 계약 | 없음 | 재현성과 품질의 의미를 측정 가능하게 고정 | Q0~Q5 owner, baseline, M1 설계 질문과 승인 경계가 확정됨 | [M0 설계](project-foundation/M0_BASELINE_AND_SUCCESS_GATES.md) |
| M1 Fresh Clone·Core 순수성 | M0 | 임의 경로 clone에서 기반을 재현하고 domain 역의존 제거 | Q0~Q3 전건 통과, Core domain identity·owner 직접 열거 0 | [M1 설계](project-foundation/M1_FRESH_CLONE_AND_CORE_PURITY.md) |
| M2 설계·실행 계약 | M1 | 작업 크기에 맞는 설계 선행을 시스템 불변식으로 고정 | ready design 없는 mutation 차단, quick 문서 과잉 0 | [M2 설계](project-foundation/M2_DESIGN_EXECUTION_CONTRACT.md) |
| M3 단일 품질 gate | M2 | 사람이 명령을 기억하지 않아도 결정론적 검증 실행 | 한 명령으로 Q0~Q3, 실패 유형과 recovery 구분 | [M3 설계](project-foundation/M3_SINGLE_QUALITY_GATE.md) |
| M4 제작 실행 엔진 | M3 | 영상 작업의 다음 단계를 검증 가능한 상태 전이로 실행 | 합성 workflow 통과, 승인 gate에서 fail-closed | [M4 설계](project-foundation/M4_VIDEO_WORKFLOW_ENGINE.md) |
| M5 학습·복잡성 감사 | M4 | 실제 시간·채택·재작업·규칙 효과로 투자 판단 | 장문 task 보고 없이 KPI 재계산, 무효 자동화 축소 후보화 | [M5 설계](project-foundation/M5_LEARNING_AND_COMPLEXITY_AUDIT.md) |
| M6 Core 이식 pilot | M5 | 동일 Core를 영상과 게임 domain에서 수정 없이 검증 | 두 extension conformance 통과, 상호 참조 0 | [M6 설계](project-foundation/M6_CORE_EXPORT_GAME_PILOT.md) |

## 단계 전환 계약

1. `SESSION_HANDOFF.md`가 현재 phase design 하나를 선택한다.
2. 현재 단계는 entry gate를 확인한 뒤 한 execution slice만 수행한다.
3. slice gate가 통과해야 다음 slice로 이동한다.
4. 모든 exit gate가 통과하면 문서량·수동 단계·잔여 위험을 재평가한다.
5. 다음 단계가 여전히 필요할 때만 상세 phase design을 작성하고 필요한 승인을 받는다.
6. 사용자 교정이 목표·범위·gate를 바꾸면 현재 phase를 무효화하고 설계부터 갱신한다.

## 전체 완료 조건

- 임의 ASCII·한글·공백 경로 clone에서 bootstrap과 Q0~Q3이 재현된다.
- 외부 capability가 없으면 품질을 낮춰 성공하지 않고 `needs_user` 또는 `unavailable`로 멈춘다.
- 실제 결과의 수동 시간·첫 채택·재작업·규칙 효과를 계산할 수 있다.
- 같은 Core revision이 영상과 게임 extension에서 수정 없이 통과한다.
- required-read 설계 문서와 시작 문맥이 각각의 읽기 예산을 지킨다.
