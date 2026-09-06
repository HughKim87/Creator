# Creator 영상 Host 현재 상태

- 목적: 다음 세션이 완료된 저장소 역할 분리를 재개하지 않고 Creator의 첫 미완료 작업부터 시작하게 한다.
- 읽는 시점: `core/PROJECT_RULES.md`, `PROJECT_RULES.md` 뒤.
- 책임: 작업 에이전트가 현재 Creator 작업과 승인 경계를 유지하고 사용자가 영상 결과와 외부 효과를 소유한다.
- 상태: Creator main의 Extension 제작 워크플로 보강 및 검증 완료.
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
- Creator 활성 구현 단계: 없음. 승인된 Extension 개선을 main 작업 트리에 적용하고 검증 완료.
- Core 공통 대화 해석·승인 의미 규칙의 변경 후보는 보류. Extension에 공통 정책을 복제하지 않음.

## 구현·검증 상태

- Creator는 Host 소비 계약과 읽기 전용 Core 경계를 유지한다.
- Agent Core Maintainer는 별도 로컬 저장소와 원격을 사용하는 독립 Maintainer로 분리됐다.
- Creator와 Maintainer의 최종 로컬 폴더 이름 전환이 완료됐다.
- 사용자 확인에 따라 Maintainer 관련 작업은 종료됐다.
- 완료된 역할 분리 설계·단계 문서는 휴지통으로 이동했고 Git 이력을 복구 경계로 유지한다.
- `video-to-srt`는 정상 UI 다운로드를 우선하고 미등록 우회 경로를 임의로 사용하지 않으며, 특정 경로 실패를 전체 획득 불가로 확대하지 않는다.
- 새 제목·썸네일은 자막 근거·승인 원문·검수 이미지 해시를 기록하고 `--require-editorial`로 검증한다. 기존 패키지는 읽기 호환을 유지한다.
- 수정 도우미는 제목·문구·이미지의 영향 범위에 맞춰 상태를 무효화한다. 수동 패키지 완료 도우미는 archive 적용 후 재검증까지 수행한다.
- 새 작업의 프로필 결정은 기본 설정 파일 부재를 허용하고 명시 입력을 병합한 뒤 누락 필드만 반환한다.

## 직전 게이트

- `scripts/verify.py`의 Creator 전체 164개 테스트, 소비 통합 gate, Node·Python Runtime 검사, 산출물 계약 검사가 통과했다.
- 승인 문구 축약·자막/이미지 변경·기본값 부재·수정 범위 보존·완료 후 retention 재검증을 합성 자료로 확인했다.
- 스킬 frontmatter·이름·로컬 링크의 표준 라이브러리 검사와 `git diff --check`가 통과했다.
- 실제 NotebookLM·Chrome·이미지 생성 및 채널 성과 검증은 이번 유지보수에서 `not_run`이다.

## 승인 상태

- 승인됨: main의 Extension 개선 구현·로컬 검증 및 해당 변경의 stage·commit·origin/main push.
- 보류: Core 직접 변경. 미승인: 보호 영상 데이터 변경, 추가 외부 쓰기, 후속 변경의 commit·push.

## 차단

- 없음.

## 알려진 위험

- 실제 영상 사용성은 자동 검사로 판정하지 않으며 사용자가 운영 중 확인한다.
- `skill-creator` 공식 `quick_validate.py`는 기본·번들 Python 둘 다 `PyYAML` 부재로 실행 불가했다. 이 세션에서는 동일 구조 항목을 설치 없이 별도 검사했고 전체 Creator gate로 보강했다.

## 중요 산출물

- `.agents/skills/video-to-srt/SKILL.md`: 활성 영상 획득·자막 절차 정본.
- `SESSION_HANDOFF.md`: 활성 현재 상태 정본.

## 첫 다음 행동

1. 변경 검토 요청이면 main의 Extension 워크플로 보강 커밋과 검증 근거를 확인한다. 후속 stage·commit·push는 해당 지시가 있을 때만 수행한다.
2. 새 제작 요청이면 `coordinate-video-production`으로 지정 worktree를 활성화하고 기존 job·프로필부터 확인한다. main 유지보수 변경이 제작 worktree에 적용됐는지 확인한다.
3. 새 제목·썸네일에 근거 계약을 작성하고 `--require-approved --require-editorial` 검증 후 수동 패키지 완료 도우미를 실행한다.

## 다음 세션 시작 prompt

시작 3문서만 먼저 읽고 완료된 저장소 역할 분리와 제안서 검토를 재개하지 않는다. 보호 경로에 접근하지 말고, 실제 영상 제작 요청에서만 해당 workflow skill을 선택한다.
