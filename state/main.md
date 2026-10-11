# Creator main 공통 개발 상태

- 목적: 재사용 가능한 Extension·스킬·workflow 개선과 유지보수의 현재 상태를 소유한다.
- 읽는 시점: core/PROJECT_RULES.md, PROJECT_RULES.md, SESSION_HANDOFF.md 뒤.
- 책임: main 작업 에이전트가 공통 개발 상태를 유지하고 사용자가 범위와 외부 효과를 승인한다.
- 상태: 공통 개발 대기. 승인된 개별 영상 작업 자료 정리 완료.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md의 「워크트리별 상태 문서」.

## 현재 단계

- 공통 스킬·도구·합성 검증을 유지하고, 승인된 개별 영상의 작업 기록과 로컬 자료를 main에서 제거했다.
- inputs/outputs 보호 경로는 이번 정리에서 접근·삭제하지 않는다.
- 활성 전체 설계: 없음.
- 활성 단계 설계: 없음.

## 직전 게이트

- 판정: pass. 개선 초안을 기존 도메인 규칙에 흡수하고 작업용 자료를 제거했다. 정식 번들·helper·규칙·상태·workflow·기존 개선 회귀 검사 통과.
- 공통 스킬 source는 extension/skills/create-shorts/, 설치본은 C:/Users/Hugh/.codex/skills/create-shorts/다. 번들 구조와 helper의 재현 가능한 검증은 extension/tests/test_create_shorts_bundle.py와 extension/tests/test_create_shorts_skill.py가 소유한다. 합성 시험 자료는 Git 제외 임시 폴더에서 생성하고 시험 종료 후 제거한다.

## 승인 상태

- 위임: main의 영상별 자료와 불필요한 개선 작업 자료 정리, 필요한 개선의 구현·검증·로컬 커밋.
- 미위임: 보호 경로 정리, 다른 워크트리 변경, push·외부 게시·업로드.

## 차단

- 없음.

## 알려진 위험

- 보호 경로 안 개별 영상 자료의 잔존 여부는 미조사다. 해당 자료까지 정리하려면 정확한 대상·목적 승인이 필요하다.
- create-shorts의 실제 장편 전체 실행·독립 에이전트 선택·직접 청취 검증은 별도 범위다. ASR을 청취 검증으로 주장하지 않는다.
- 기존 스킬 등록의 공식 quick_validate는 PyYAML 부재로 not_run이며 평면 YAML 구조 검사로 구분했다. 의존성 설치 없음.

## 첫 다음 행동

1. 공통 개선 요청을 받으면 영향받는 Extension·스킬·workflow owner를 확인하고 해당 범위의 구현과 검증을 진행한다.
2. 개별 영상 요청을 받으면 PROJECT_RULES.md의 「워크트리별 상태 문서」에 따라 영상 작업용 워크트리에서 진행한다.
