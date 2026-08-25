# Creator 영상 Host 현재 상태

- 목적: 다음 세션이 완료된 저장소 역할 분리를 재개하지 않고 Creator의 첫 미완료 작업부터 시작하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤.
- 책임: 작업 에이전트가 현재 Creator 작업과 승인 경계를 유지하고 사용자가 영상 결과와 외부 효과를 소유한다.
- 상태: Creator와 Agent Core Maintainer의 저장소 역할 분리 완료. 영상 다운로드 경로 보강 완료.
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`.
- 활성 전체 설계: 없음.
- 활성 단계 설계: 없음.
- handoff mode: `portable`.
- uncommitted dependency: 없음.

## 현재 목표

Creator 영상 Host의 검증된 영상 제작·수동 업로드 패키지 workflow를 운영한다.

## 핵심 용어와 입력

- `Core`: `core/`의 읽기 전용 submodule.
- `Extension`: 영상·YouTube·게임 도메인 구현과 계약.
- `Skills`: 실제 도구 사용 절차.
- 보호 경로: `inputs`, `outputs`, `extension/inputs`, `extension/outputs`.
- 영상 획득·자막 owner: `.agents/skills/video-to-srt/SKILL.md`.

## 현재 단계

- 저장소 역할 분리 단계 0~6: 완료.
- Creator 활성 구현 단계: 없음.
- Extension 규칙 흡수안 검토·선별·보강: 완료.

## 구현·검증 상태

- Creator는 Host 소비 계약과 읽기 전용 Core 경계를 유지한다.
- Agent Core Maintainer는 별도 로컬 저장소와 원격을 사용하는 독립 Maintainer로 분리됐다.
- Creator와 Maintainer의 최종 로컬 폴더 이름 전환이 완료됐다.
- 사용자 확인에 따라 Maintainer 관련 작업은 종료됐다.
- 완료된 역할 분리 설계·단계 문서는 휴지통으로 이동했고 Git 이력을 복구 경계로 유지한다.
- `video-to-srt`는 정상 UI 다운로드를 우선하고 미등록 우회 경로를 임의로 사용하지 않으며, 특정 경로 실패를 전체 획득 불가로 확대하지 않는다.

## 직전 게이트

- `video-to-srt` 자막 Runtime 관련 타겟 테스트 5개가 통과했다.
- `scripts/verify.py`의 Creator 전체 152개 테스트, Core 소비 통합 gate, Node·Python Runtime 검사가 모두 통과했다.
- 스킬 frontmatter·이름·TODO·diff 구조 검사가 통과했다.
- 실제 NotebookLM 다운로드는 보호 데이터·외부 세션이 필요해 `not_run`이다.

## 승인 상태

- 승인됨·완료: 개선 제안의 필요 항목 선별, `video-to-srt` 다운로드 계약 보강, 한시 제안서·역사 설계문서 정리, 현재 변경의 commit·push.
- 미승인: 보호 경로 접근, 추가 외부 쓰기, 후속 commit·push.

## 차단

- 없음.

## 알려진 위험

- 실제 영상 사용성은 자동 검사로 판정하지 않으며 사용자가 운영 중 확인한다.
- `skill-creator` 공식 `quick_validate.py`는 기본·번들 Python 둘 다 `PyYAML` 부재로 실행 불가했다. 이 세션에서는 동일 구조 항목을 설치 없이 별도 검사했고 전체 Creator gate로 보강했다.

## 중요 산출물

- `.agents/skills/video-to-srt/SKILL.md`: 활성 영상 획득·자막 절차 정본.
- `SESSION_HANDOFF.md`: 활성 현재 상태 정본.

## 첫 다음 행동

1. 새 영상 제작은 `coordinate-video-production`으로 시작하고 검증된 worktree·browser profile·job 상태를 사용한다.
2. NotebookLM 영상을 획득할 때 `video-to-srt`의 정상 다운로드 경로와 실패 보고 계약을 적용한다.
3. commit이나 push가 필요하면 정확한 변경과 검증 결과를 먼저 보고하고 별도 지시를 받는다.

## 다음 세션 시작 prompt

시작 3문서만 먼저 읽고 완료된 저장소 역할 분리와 제안서 검토를 재개하지 않는다. 보호 경로에 접근하지 말고, 실제 영상 제작 요청에서만 해당 workflow skill을 선택한다.
