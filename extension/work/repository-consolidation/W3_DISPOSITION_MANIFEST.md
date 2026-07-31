# W3 처분 매니페스트

- 문서 분류: `reference-evidence`
- 기준 checkpoint: `5ed6bb6`
- 기준일: 2026-07-31
- 목적: W4가 다시 판단하지 않고도 승인 범위, 보존 범위, 참조 해제, 복구 경계를 검증할 수 있게 한다.
- 보호 경계: 보호 입력·출력의 자식 이름과 내용은 기록하지 않고 opaque ID·개수·용량·집계 해시만 기록한다.
- 실행 경계: 이 문서는 dry-run 명세이며 삭제·이동·Core 변경을 승인하지 않는다.

## 결론

현재 filesystem과 Git union은 같은 560개 파일을 설명한다. W4 권장안은 367개 파일과 빈 디렉터리 6개를 제거하고, Core 회귀 테스트 1개 파일의 역사 문서 의존성을 현재 규칙 owner로 전환하는 것이다. 보호 입력 2개와 현재 재사용 가치가 확인된 보호 출력 4개는 보존한다.

W5가 현재 initiative 문서 9개를 self-clean하고 handoff와 최종 보고서를 갱신하면 최종 상태는 tracked 180개, reviewed ignored 6개, untracked 0개, filesystem 186개로 예상한다.

## 1. 기준 inventory

| 구분 | 파일 수 | 비고 |
|---|---:|---|
| tracked | 214 | W3 phase-design 포함 |
| untracked | 1 | 이 매니페스트 생성 전 W3 phase-design |
| ignored | 345 | 보호 자료·cache·local state·runtime |
| Git union | 560 | tracked + untracked + ignored |
| filesystem | 560 | Git union과 차이 0 |
| 전체 용량 | 5,223,599,780 bytes | 파일 합계 |

검증 결과:

- Git union에만 있거나 filesystem에만 있는 파일: 0
- 중복 분류·enumeration error·reparse point: 0
- 모든 처분 대상은 workspace 내부에 있다.

## 2. 최종 보존 allowlist

### 2.1 tracked allowlist

- 예상 최종 tracked 파일: 180
- path-list SHA-256: `9dfb565db0f84176b6dbee6cf7e6e8c9dcf6df05f24e6eb5242c1ec900d71f4f`

| root | 파일 수 |
|---|---:|
| `.agents` | 37 |
| `core` | 70 |
| `extension` | 57 |
| repository root | 16 |
| 합계 | 180 |

이 allowlist는 canonical startup·rule·contract·code·test·schema·skill·사용자 source, 갱신된 current-state, 최종 보고서만 남기는 W5 완료 상태를 기준으로 한다.

### 2.2 보호 자료 allowlist

보호 자식 이름은 Git 문서에 남기지 않는다.

| opaque ID | 구분 | 파일 수 | 용량 | 판정 |
|---|---|---:|---:|---|
| `IN-b2c049ea49` | 사용자 입력 source | 2 | 3,799,860,960 bytes | 보존 |
| `KEEP-e8556bad28` | 현재 자막 derivative | 1 | 64,099 bytes | 보존 |
| `KEEP-548004f0e5` | 현재 편집 interchange | 1 | 746,529 bytes | 보존 |
| `KEEP-49b619b626` | 사용자 승인 review media | 1 | 116,400,513 bytes | 보존 |
| `KEEP-6a8afdf0ca` | review manifest | 1 | 11,102 bytes | 보존 |

- 보호 출력 보존 집합: 4개, 117,222,243 bytes
- 보호 출력 보존 집합 path+size SHA-256: `fb1e0fe64828a7ad31e6f8d0e8760fc65407d1cc69cc50ec28f784c4d990e910`
- 최종 reviewed ignored allowlist: 보호 입력 2개 + 보호 출력 4개 = 6개
- 최종 reviewed ignored 용량: 3,917,083,203 bytes

## 3. W4 exact tracked 처분 후보

아래 28개 파일은 역할이 끝난 역사 보고서·계획·phase evidence다. 재사용 가능한 내용은 W1에서 검토했고 K01~K04는 W2에서 현재 owner에 흡수했다. 모든 파일은 Git checkpoint `5ed6bb6`에서 복구할 수 있다.

1. `docs.md`
2. `extension/reports/2026-07-24_프로젝트_구조_및_목표_달성도_진단.md`
3. `extension/reports/claude_2026-07-29_규칙_손실_이력분석과_재발방지_개선계획.md`
4. `extension/reports/codex_2026-07-27_e4161fd_장점선별_개선적용_최종보고.md`
5. `extension/reports/codex_2026-07-27_e4161fd_장점선별_현재버전_개선적용계획.md`
6. `extension/reports/codex_2026-07-27_영상편집_프로젝트근간_개선_최종보고.md`
7. `extension/reports/codex_2026-07-27_전체세션자료_재분석_최종개선계획.md`
8. `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G0-G1_기준고정과_상태라우팅.md`
9. `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G2_ainotebook_상태이전.md`
10. `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G3-G4_지시준수_규칙과_회귀검증.md`
11. `extension/reports/codex_2026-07-28_문서기반_개선_plan/codex_G5_통합검증과_최종보고.md`
12. `extension/reports/codex_2026-07-28_문서기반_지시준수_개선_최종보고.md`
13. `extension/reports/codex_2026-07-28_문서기반_지시준수와_워크트리상태관리_개선안.md`
14. `extension/reports/codex_2026-07-28_재현가능한_프로젝트_기반_방향분석과_개선계획.md`
15. `extension/work/PROJECT_FOUNDATION_DESIGN.md`
16. `extension/work/project-foundation/M0_BASELINE_AND_SUCCESS_GATES.md`
17. `extension/work/project-foundation/M1_FRESH_CLONE_AND_CORE_PURITY.md`
18. `extension/work/project-foundation/M2_DESIGN_EXECUTION_CONTRACT.md`
19. `extension/work/project-foundation/M3_SINGLE_QUALITY_GATE.md`
20. `extension/work/project-foundation/M4_VIDEO_WORKFLOW_ENGINE.md`
21. `extension/work/project-foundation/M5_LEARNING_AND_COMPLEXITY_AUDIT.md`
22. `extension/work/project-foundation/M6_CORE_EXPORT_GAME_PILOT.md`
23. `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md`
24. `extension/work/rule-preservation/M0_RULE_LINEAGE_AND_LOSS_AUDIT.md`
25. `extension/work/rule-preservation/M1_PRESERVATION_VALIDATION_AND_MINIMAL_CHANGE.md`
26. `extension/work/rule-preservation/M2_RESTORE_INTEGRATE_AND_SINGLE_GATE.md`
27. `extension/work/rule-preservation/M3_STARTUP_ROUTE_REGRESSION_AND_DISPOSITION.md`
28. `extension/work/rule-preservation/M4_EXACT_DISPOSITION_AND_FINAL_REPORT.md`

- 파일 수: 28
- 용량: 319,521 bytes
- path+size SHA-256: `fb881b3bcf05b290338116a0d0488dca673522ad4296e456911a0ab6ee8a8ea1`
- 복구 경계: Git 복구 가능

## 4. W4 ignored 처분 후보

### 4.1 비보호 ignored

| 집합 | 파일 수 | 용량 | 근거 |
|---|---:|---:|---|
| Python `__pycache__` 8개 디렉터리 | 71 | 898,379 bytes | 테스트·실행으로 재생성 가능 |
| Obsidian local state | 4 | 8,202 bytes | 사용자별 UI 상태, canonical content 아님 |
| `extension/.runtime/` | 67 | 816,338,813 bytes | active exact reference 0, 현재 workflow owner와 불일치하는 inactive cache |
| 합계 | 142 | 817,245,394 bytes |  |

- path+size SHA-256: `ee3a0dc1acc0c85e02ca6e1b60c793b6a66cd627282bce045e4727cd54fbd5cb`
- Python cache exact directories:
  - `core/src/file_data/__pycache__`
  - `core/tests/__pycache__`
  - `extension/src/__pycache__`
  - `extension/src/learning/__pycache__`
  - `extension/src/video_editing/__pycache__`
  - `extension/src/video_workflow/__pycache__`
  - `extension/src/youtube_domain/__pycache__`
  - `extension/tests/__pycache__`
- Obsidian local-state exact files:
  - `.obsidian/appearance.json`
  - `.obsidian/core-plugins.json`
  - `.obsidian/graph.json`
  - `.obsidian/workspace.json`
- runtime exact root: `extension/.runtime/`

runtime은 byte-identical Git 복구가 불가능하다. 향후 기능이 필요하면 당시의 active workflow owner를 기준으로 현재 지원 도구를 재설치해야 한다. 현재 디렉터리를 설치 기준으로 승격하지 않는다.

### 4.2 보호 출력 처분 후보

- 대상 root: 보호 출력 root
- 제거 후보: 197개, 487,736,873 bytes
- 제거 후보 path+size SHA-256: `8f2790624d2964a234b9ed0dd4b5dc308934b2c61f93f9aeb3d1aba710d37573`
- 선택식: 보호 출력 root의 현재 201개 중 2.2절 opaque 보존 집합 4개를 제외한 전부
- 근거: 중간 분석·이전 revision·재생성 산출물이며 W1에서 일반화 가능한 지식은 현재 owner로 흡수했다.
- 복구 경계: Git 및 byte-identical 복구 불가. 사용자 source는 보존되지만 같은 산출물을 그대로 재현한다고 보장할 수 없다.

보호 경계 때문에 exact 자식 이름은 이 Git 문서에 기록하지 않는다. W4 승인 요청은 현재 사용자 대화 안에서 보존 4개 exact 이름과 “root minus 보존 4개” 선택식을 함께 제시해야 한다.

## 5. 빈 디렉터리 처분 후보

1. `.codex-upload-staging`
2. `.skill-staging`
3. `core/docs/domain`
4. `extension/skills`
5. `extension/work/2026-06-30-00-23-03/xml_build`
6. `extension/work/2026-06-30-00-23-03`

- 디렉터리 path-list SHA-256: `e73435f72cfe130afd6e02f6dda6fc4b6c4505da78d5092520ab000ed168f116`
- 6번은 5번을 제거한 뒤 비게 되므로 child-before-parent 순서로 처리한다.
- workspace containment와 reparse 검사는 W4 실행 직전에 다시 수행한다.

## 6. Core 회귀 fixture 전환

### 현재 blocker

`core/tests/test_rule_routing.py`가 3절 13번의 역사 보고서를 회귀 fixture로 직접 읽는다. 보고서를 제거하면서 테스트를 그대로 두면 Core gate가 깨진다.

### 권장 변경

정확한 변경 대상은 `core/tests/test_rule_routing.py` 한 파일이다.

- 사용자 정정이 controlled plan을 무효화하는 의미 검증은 현재 canonical owner인 `core/rules/staged-work-design.md`를 읽도록 전환한다.
- 완료된 과거 G0~G5 표에 의존한 fixture는 제거한다.
- `SESSION_HANDOFF.md`의 selected-state·status·first-action 검증은 현재 상태 계약으로 유지한다.

이는 Core 규칙의 의미 변경이 아니라 회귀 fixture routing을 현재 owner로 맞추는 변경이다. 규칙상 W4 전에 exact Core 승인이 필요하다.

### 비권장 대안

역사 보고서 한 개를 테스트만 위해 영구 보존할 수 있으나, active authority와 history를 다시 결합해 이번 정리 목적을 훼손하므로 권장하지 않는다.

## 7. active reference release

W4는 처분과 같은 commit에서 다음 참조를 해제한다.

- `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
  - prior M0 map 링크 제거
  - 역사 M4를 active route로 해석할 여지 제거
- `SESSION_HANDOFF.md`
  - M0 map·역사 M4 artifact row 제거
  - W4 실제 결과와 남은 allowlist로 current-state 갱신
- `core/tests/test_rule_routing.py`
  - 6절의 역사 보고서 fixture를 current canonical owner로 전환

W0·W1 evidence에 남은 처분 후보 literal path는 runtime dependency가 아니며 W5 self-clean 대상이다. 최종 보고서는 역사 문서를 startup/current authority로 링크하지 않는다.

## 8. W5 self-clean queue

W4가 보존하고 W5 종료 commit에서 제거할 현재 initiative 문서는 9개다.

1. `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
2. `extension/work/repository-consolidation/W0_REPOSITORY_WIDE_INVENTORY_AND_CLASSIFICATION.md`
3. `extension/work/repository-consolidation/W0_FILE_CLASSIFICATION.md`
4. `extension/work/repository-consolidation/W1_REUSABLE_KNOWLEDGE_EXTRACTION_AND_OWNER_MAPPING.md`
5. `extension/work/repository-consolidation/W1_REUSABLE_KNOWLEDGE_MAP.md`
6. `extension/work/repository-consolidation/W2_SELECTIVE_ABSORPTION_AND_FOUNDATION_STRENGTHENING.md`
7. `extension/work/repository-consolidation/W3_DEPENDENCY_RELEASE_AND_EXACT_DISPOSITION_MANIFEST.md`
8. `extension/work/repository-consolidation/W3_DISPOSITION_MANIFEST.md`
9. W4 phase-design

W5 phase-design은 final commit 전에 자체 제거할 수 있는 임시 실행 문서로 운용한다. `SESSION_HANDOFF.md`는 clean idle/current truth로 갱신해 보존하고, 최종 보고서는 `extension/reports/2026-07-31_규칙_무손실_통합_M0_작업_보고.md`를 실제 전역 작업 보고서로 다시 작성해 보존한다.

## 9. W4 dry-run 합계

| 처분 집합 | 파일 수 | 용량 |
|---|---:|---:|
| tracked history·phase | 28 | 319,521 bytes |
| 보호 출력의 이전·중간 산출물 | 197 | 487,736,873 bytes |
| 비보호 ignored cache·local state·runtime | 142 | 817,245,394 bytes |
| 합계 | 367 | 1,305,301,788 bytes |

추가로 빈 디렉터리 6개를 제거한다.

예상 상태:

| 시점 | tracked | untracked | ignored | filesystem |
|---|---:|---:|---:|---:|
| W4 phase-design 반영 후 | 189 | 0 | 6 | 195 |
| W5 self-clean 완료 후 | 180 | 0 | 6 | 186 |

## 10. 실행 전 재검증 계약

W4는 mutation 전에 다음 조건을 모두 다시 검증해야 한다.

1. 기준 checkpoint와 현재 승인 대상의 path·개수·용량·집계 해시가 일치한다.
2. workspace 밖 경로, reparse point, duplicate, tracked/ignored overlap이 0이다.
3. 빈 디렉터리는 실제로 비어 있고 child-before-parent 순서를 지킨다.
4. 보호 보존 집합 4개와 입력 2개는 삭제·stage·commit 대상이 아니다.
5. Core exact 승인과 삭제 exact 승인이 현재 대화에 모두 존재한다.
6. 승인 이후 대상이 달라졌으면 실행하지 않고 inventory와 승인을 갱신한다.

실행 후에는 Core·Extension·maintenance·route·strict UTF-8·NUL·trailing whitespace·link·`git diff --check`를 모두 통과시키고, 보호 staged count 0과 실제/예상 inventory 일치를 확인한다.
