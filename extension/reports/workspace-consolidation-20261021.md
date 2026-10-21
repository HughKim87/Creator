# Creator 통합·정리 판정

- 목적: 제거될 브랜치에 재사용 개선이 남지 않도록 출처별 흡수 판정과 자료 처분 대상을 기록한다.
- 읽는 시점: 단일 workspace 전환 검토와 기존 자료·worktree 처분 승인 시.
- 책임: main 유지보수 세션이 실제 파일·검사를 갱신하고 사용자가 자료 처분을 승인한다.
- 상태: 개선 통합 진행. 기존 자료 이동·삭제와 worktree 제거 미실행.
- 관련 권위: `../docs/WORKSPACE.md`, 루트 `PROJECT_RULES.md`.

## 개선사항 출처 대조

태그는 원래 Git 이력을 고정한다. 아래 판정은 현재 main의 기능 소유자를 기준으로 하며 과거 브랜치 전체를 덮어쓰지 않는다. 개인 설정·원본·출력은 공통 코드에 포함하지 않는다.

| 출처 | 확인 범위와 판정 | main 소유자 |
|---|---|---|
| `before-codex-wardogs` | 공통 조상 이후 공통 코드·규칙 변경 없음. 썸네일 제작 자료는 영상별 데이터이며 원위치 보존 | 공통 기능 추가 불필요; 자료 이전 승인 대상으로 분리 |
| `before-codex-ainotebook` | merge-base 이후 최종 차이는 handoff·전용 상태뿐. `7c331a9`의 연속 제작·브라우저 실행·내용 검수 개선은 main에 반영돼 있으며 job validator는 bytes 동일 | `.agents/skills/`의 제작 7종·browser launcher·job validator·session 개선 검사 |
| `before-codex-backroom-video` | merge-base 이후 차이는 상태 정책의 과거 수정·영상별 계획. `84adf0a`, `9f79ca3`, `fbfb8f3`, `eb08649`의 편집·검수 개선은 `9d23fd1` 등에서 흡수됐고 video_editing 구현은 bytes 동일 | `extension/src/video_editing/`, 편집 규칙과 workflow 계약. 최신 main 정책을 유지 |
| `before-claude-dokkaebi` | 시청자 질문·분석, 재전사·말실수, 무음 판단, 효과 검증, 후편집 자막·밈, 후속 정정 보존은 main의 R03/R04/R05/R07/R09/R19/R21 및 TC34~TC40에 반영. TC 번호는 main 정본 유지 | `extension/rules/` 및 관련 회귀 |
| 같은 도깨비 출처의 잔여 개선 | CS6 효과 호환 관측과 상세 스타일 선택이 main에 빠져 있어 흡수. 관측 사실과 새 검증을 구분하고 단일 영상 선택을 새 영상의 강제값으로 일반화하지 않음 | `PREMIERE_CS6_XML_COMPAT.md`, `VIDEO_EDITING_PROFILES.md`의 선택적 변형 및 CAND08 링크 |
| `before-codex-TRYALLGAME` | 공통 변경은 작업 폴더 ignore. 특정 영상 이름을 추가하는 방식 대신 새 jobs 전체를 Git 제외하는 구조로 대체 | `.gitignore`, `creator_workspace.py` |
| `before-codex-24HReplier` | 앱 전체·생성/판정 근거 일치 개선과 검사·probe 구현을 흡수. `e9587cc`, `cdc3ae7`, `d649c9d`의 코드를 후속 tip `6764ae7`에서 가져옴. 실서비스 실험은 자동 실행하지 않음 | `extension/src/replier/`, `extension/tests/replier_*`, `test_replier.py`, Build/Install/Start 스크립트와 model manifest |

도깨비의 옛 workflow 문구를 통째로 가져오면 main의 국소 보정 위임·시청자 분석 범위가 되돌아간다. 백룸·ainotebook의 옛 파일로 덮어쓰면 최신 TTS·제목·공개 시간·Claude 개선이 삭제된다. 이들 차이는 개선 누락이 아닌 main 후속 발전으로 판정하고 보존한다.

## 검증

- 24HReplier Python 합성 API 12개 pass. 로컬 loopback만 사용했고 실제 서비스 호출 없음.
- Windows C# 앱 빌드 pass. writing-context / pipeline / candidate-isolation / recovery 합성 검사 프로그램 네 개 pass.
- 편집 rule routing 구조 검사 13개 pass.
- CS6 앱 import·게시·실모델 생성 성과는 이번 통합에서 not_run. 브랜치에 기록된 과거 검증을 신규 실측으로 보고하지 않음.

## 복구 범위

`before`와 `before-*` 태그를 유지한다. 현재 작업은 원래 worktree와 ignored 자료를 변경하지 않는다. 로컬 metadata inventory는 `extension/data/consolidation/baseline.json`이며 inputs·비밀·브라우저 프로필·링크 경계는 제외됐다. 이 목록은 파일 내용 백업이 아니다. ignored 자료를 처분하기 전에는 별도 복구본 또는 검증된 재생성 조건을 확보해야 한다.

## 자료 정리 승인

기존 자료·worktree는 아직 이동·삭제하지 않았다. 최종 XML이 참조하는 원본·PNG·WAV를 포함한 종속 자산은 단순 중간본으로 처분하지 않는다. 해당 작업의 최종 승인 근거와 dependency를 대조한 뒤 정확한 유지·보관·삭제 목록을 제시한다. 사용자 확인 전에는 이 절을 실행 승인으로 해석하지 않는다.
