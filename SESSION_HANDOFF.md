# 세션 핸드오프

- 갱신일: 2026-07-31
- 역할: ainotebook 이외 worktree의 현재 상태·blocker·검증·첫 다음 행동 단일 owner
- 현재 작업: 프로젝트 전역 지식 선별·구조 통합·workspace 정리 W5 전역 회귀·규칙 계보 보고·clean closeout
- 상태: W4-S1~S5 passed. 처분 commit `53607e9`와 Git GC 무결성 대조를 완료했고 W5 규칙별 최종 보고·initiative self-clean만 남았다.
- 활성 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 활성 단계 설계: `extension/work/repository-consolidation/W5_GLOBAL_REGRESSION_RULE_LINEAGE_AND_CLEAN_CLOSEOUT.md`
- handoff mode: `same-workspace`; `uncommitted` ignored runtime·보호 keep output이 후속 gate 입력이다.
- 읽기 순서: `PROJECT_RULES.md` → 이 문서 → 전체 설계 → W4 단계 설계 → 첫 행동에 matching된 규칙

## 현재 목표·불변 경계

- `inputs/**`를 분석·처분에서 제외하고 tracked·untracked·ignored·백룸·개선 산출물을 동일한 기준으로 정리한다.
- 재사용 가치가 검증된 지식만 기존 canonical owner에 흡수하고, 재생성·중복·역할 종료 항목은 복구·참조·승인 후 정리한다.
- FFmpeg·whisper.cpp runtime 67개, current output 4개, inputs 전체는 유지한다.
- `e705f71`은 사용자 명시에 따른 삭제 전 일회성 Git 복구점이다. push하지 않고, 이후 보호 경로를 추가 stage하지 않는다.

## resume checkpoint

- branch `main`, HEAD `53607e9`, status clean.
- snapshot 신규 272개·488,643,454 bytes는 filesystem·HEAD blob 272/272 byte-identical이다.
- exact 처분 집합은 300개·488,962,975 bytes: 역사 문서 28, output 197, Python cache 71, Obsidian local state 4. 누락·untracked 0.
- 처분 후 inputs 제외 inventory는 tracked 193, untracked 0, ignored 71, filesystem 264이며 tracked input·output·cache는 0이다.
- Core cache 처분은 `core/src/file_data/__pycache__/` 13개·273,629 bytes와 `core/tests/__pycache__/` 12개·228,750 bytes다.
- 빈 디렉터리 6개는 다시 확인했고 parent 1개는 empty child 1개만 가진다.

## 승인된 exact 변경

- Core maintained: `core/tests/test_rule_routing.py`, `core/src/file_data/maintenance.py`, `core/tests/test_maintenance.py`.
- Core cleanup: 위 cache 25개와 빈 `core/docs/domain/`.
- disposition: W3 manifest의 tracked 28, `e705f71`의 output 197·cache 71·Obsidian 4, 빈 디렉터리 6.
- controls: `.gitignore`·`.gitattributes` 일회성 예외 원복.
- Git maintenance: refs·stash 2개·reflog·reachable object와 `e705f71` 보존 후 prune/repack. push·publish·history rewrite는 포함하지 않는다.

## 현재 검증

- 2026-07-31 staged-tree 전체 gate: Core 140, Extension 138, maintenance 71문서·85링크, errors·drift·duplicates 0, clean-clone ASCII·한글·공백 3종 통과.
- local runtime actual probe: FFmpeg 45개·318,594,126 bytes, whisper.cpp 22개·497,744,687 bytes, 모두 `ready`.
- Git GC 후 `.git` 361,424,219 bytes; 6,998,265,971 bytes(95.1%) 회수, garbage 0, stash 2 보존.
- maintenance의 clean-commit protected-path 사각지대는 Core 회귀 38건과 전체 gate로 닫혔다.

## 실패 ledger

| objective | attempt | result / cause | count | next condition |
|---|---|---|---:|---|
| 프로젝트 전역 정리 | 이전 M0~M4 | 규칙·문서 slice를 전체 목표로 축소 | 1 | W0~W5 전역 설계로 교체 |
| W4-S4 삭제 복구 | 첫 해석 | ignore 변경 후 실제 파일 commit 지시를 tracked checkpoint로 축소 | 1 | `e705f71` raw blob 272/272 일치로 해결 |
| protected clean gate | `e705f71` 후 | maintenance가 tracked output 197개를 감지하지 못함 | 1 | Core maintenance 회귀·final tracked protected 0 |

## 중요 artifact

| 경로 | 상태 | 역할 |
|---|---|---|
| `PROJECT_DIRECTION.md` | active reference-evidence | 장기 사용자 결과 |
| `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md` | active overall-design | W0~W5 단계·최종 gate |
| `extension/work/repository-consolidation/W5_GLOBAL_REGRESSION_RULE_LINEAGE_AND_CLEAN_CLOSEOUT.md` | in_progress phase-design | 현재 W5 실행 계약 |
| `extension/work/repository-consolidation/W3_DISPOSITION_MANIFEST.md` | partially superseded evidence | exact 28개·6디렉터리·W5 self-clean queue |
| `extension/reports/2026-07-31_규칙_무손실_통합_M0_작업_보고.md` | historical partial evidence | W5에서 전역 최종 보고로 전면 갱신 |

## 첫 다음 행동

1. 삭제 자료와 현재 owner를 다시 읽어 모든 작업 규칙의 원문→추출→흡수·신설 위치 matrix를 만든다.
2. 최종 보고서를 실제 W0~W5·M0~M4 커밋·수치·점수와 일치시킨다.
3. initiative 문서 10개를 self-clean하고 전체 gate 후 final clean commit으로 마감한다.

## 다음 session 시작 prompt

`PROJECT_RULES.md → SESSION_HANDOFF.md → overall → W5`를 읽고 규칙 계보 matrix 작성부터 재개한다. keep output 4·runtime 67·inputs는 유지하고 push하지 않는다.
