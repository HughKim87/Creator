# 세션 핸드오프

- 갱신일: 2026-07-29
- 역할: ainotebook 이외 worktree의 현재 work·blocker·검증 상태·첫 다음 행동 단일 owner
- 현재 작업: 재현 가능한 프로젝트 기반 M2 설계·실행 계약 (in_progress)
- 상태: M0-S1~S3·M0-X1~X4와 M1-S1~S5·M1-X1~X5 통과, M1 커밋과 M2 전환을 함께 수행 중
- 활성 전체 설계: `extension/work/PROJECT_FOUNDATION_DESIGN.md`
- 활성 단계 설계: `extension/work/project-foundation/M2_DESIGN_EXECUTION_CONTRACT.md`
- 선택 근거: `extension/reports/codex_2026-07-28_재현가능한_프로젝트_기반_방향분석과_개선계획.md`
- 읽기 순서: `PROJECT_RULES.md` → 이 문서 → 활성 전체 설계 → 활성 단계 설계 → 다음 행동에 matching된 규칙

## 검증된 현재 상태

### main

- 현재 branch는 `main`, HEAD는 `a1977a5`이며 범용 파일 추출·정리 규칙은 Core owner로 교정됐다.
- 현재 dirty 범위는 설계 규칙·라우팅·Core 회귀 4개, Extension 보고서·회귀·전체 설계 3개, M0~M6 단계 설계 7개와 이 핸드오프뿐이며 다른 변경은 없다.
- 승인된 Core gate에서 Core 131개·Extension 119개와 maintenance 문서 81개·링크 109개가 통과했다.
- 현재 workspace 재측정: Core 131개와 Extension 119개 회귀는 통과했지만, `maintenance-verify`는 기존 미승인 `core/rules/document-work.md`, `core/rules/staged-work-design.md`, `core/tests/test_rule_routing.py` 때문에 `core_change_required`로 실패했다.
- HEAD `07a26a3`를 한글·공백 포함 임의 경로에 `--no-hardlinks --no-local` clean clone해 재측정한 결과, Core 129개 중 `test_test_write_capability_rejects_active_project_root` 1개가 source-root 판정으로 실패했고 Extension 114개와 `maintenance-verify`(문서 71·링크 80·Python 22·schema 14)는 통과했다.
- 같은 clone의 `python -S -B -m unittest extension/tests/test_manual_upload_package.py -q`는 `PIL`/Pillow가 선언된 환경 계약 없이 host package에 의존해 import 단계에서 실패했다.
- M0-S1-G: 통과. 각 결과에 환경·명령·pass/fail·확인 원인을 남겼고, 미실행 검사를 pass로 기록하지 않았다.
- M0-S2-G: 최신 사용자 지시의 권장안 자동선택으로 Q0~Q5·재현성 정의를 승인 기준으로 확정했다.
- M0-S3-G: runtime·dependency·bootstrap·namespace·storage·artifact registry·clone·CI 경계와 각 exact 후보 범위를 M0 phase design 결정표에 기록했다.
- M0-X1~X4: 통과. baseline, 승인 기준, M1 입력, required-read 문서 예산과 reference-evidence 분리가 확인됐다.
- M1-S1~S5-G: runtime preflight, source-root/storage, neutral namespace, one-way artifact registry, ASCII·한글·공백 clean clone conformance가 통과했다.
- M1-X1~X5: bootstrap·Q0~Q3 전건, Core project/YouTube identity 0, Core artifact direct enumeration 0, Extension 121개 회귀, protected/external gate 분리가 확인됐다.
- M1 transition evidence: 3개 clone path, 약 95초 conformance, 자동 실행 사용자 행동 0, root script 4개·manifest 2개·registry/test 추가, 잔여 domain leakage 0.
- 전체 설계는 이 gap과 Core의 project URN·YouTube artifact 역의존을 M0 이후 M1에서 설계하도록 제한한다.
- 보호 `inputs/`·`outputs/` 접근·변경은 0건이고 설치·CI·commit·push는 수행하지 않았다.

### ainotebook

- 전용 상태 owner commit은 `19049ba`, main 병합 commit은 `762e650`이다.
- G2 병합 직후 Core 116개, Extension 113개, maintenance 68문서·78링크가 통과했다.
- ainotebook의 현재 작업·승인 gate는 `extension/work/AINOTEBOOK_WORKTREE_STATE.md`만 소유한다.
- `SESSION_HANDOFF.md` local diff는 0건이며 이 문서는 ainotebook에서 선택되지 않는다.

## 결정과 복구

- `AGENTS.md`와 `CLAUDE.md`는 `PROJECT_RULES.md`만 가리킨다.
- `PROJECT_RULES.md`가 startup·작업 분류·worktree 상태 선택·조건부 rule routing을 단독 소유한다.
- 사용자 교정은 기존 plan과 대기 mutation을 무효화하며, 다른 세션의 미커밋 변경은 exact target·diff·recovery·사용자 승인 없이 restore하지 않는다.
- ainotebook 상태 이전 전 저장소 밖 recovery copy 2개의 SHA-256 일치를 확인했다. 프로젝트 문서는 실제 destination을 링크하거나 의존하지 않는다.
- 이전에 restore된 6개 파일의 정확한 byte diff는 Git backup이 없어 복구할 수 없으며, 재구성 자료를 backup으로 부르지 않는다.

## 실패 ledger

| objective | attempt·result | 확인 원인 | 연속 횟수 | 다음 조건 |
|---|---|---|---:|---|
| arbitrary-path clean clone Core | `07a26a3` temp clone에서 1 failure | repository root를 isolated temp fixture로 오인하는 source-root 판정 | 1 | M0-S1에서 현재 revision 재측정 |
| package 차단 upload test | `07a26a3`의 `python -S`에서 import failure | Pillow가 선언된 환경 계약 없이 host package에 의존 | 1 | M0-S1에서 현재 revision 재측정 |
| M1 Core purity mutation | `20260728T183445Z` 자동 실행에서 차단 | exact Core 경로·이유에 대한 현재 대화의 명시적 승인 부재 | 1 | 사용자 승인 확인됨; M1-S1 재검증 |

## blocker·남은 gate

- M1 exit·transition gate는 통과했고 M2 entry gate가 활성화됐다. M1 변경과 이 전환을 지정 범위로 커밋한다.
- dependency 설치, CI·hook, 삭제·이동은 별도 승인 전 실행하지 않는다.
- M0 exit gate는 종료됐고, M1은 exact Core 범위 산출·승인 전 상태다.
- ainotebook의 별도 영상 작업은 전용 상태 문서에 기록된 사용자 승인 gate를 유지한다.

## 중요 문서

| 경로 | 상태 | 역할 |
|---|---|---|
| `extension/work/PROJECT_FOUNDATION_DESIGN.md` | active overall-design | 장기 목표·불변식·M0~M6 단계 지도 |
| `extension/work/project-foundation/M0_BASELINE_AND_SUCCESS_GATES.md` | passed phase-design | M0 exact 범위·slice·entry/exit/transition gate |
| `extension/work/project-foundation/M1_FRESH_CLONE_AND_CORE_PURITY.md` | passed phase-design | M1 exact 범위·slice·entry/exit/transition gate |
| `extension/work/project-foundation/M2_DESIGN_EXECUTION_CONTRACT.md` | active phase-design·in_progress | M2 exact 범위·slice·entry/exit/transition gate |
| `extension/work/CORE_CHANGE_FAILURES.md` | active failure owner | 자동 Core 변경 차단 기록 |
| `extension/reports/codex_2026-07-28_재현가능한_프로젝트_기반_방향분석과_개선계획.md` | reference-evidence | 선택적 방향 분석·측정·대안 근거 |
| ainotebook `extension/work/AINOTEBOOK_WORKTREE_STATE.md` | active | ainotebook 현재 상태 단일 owner |

## 첫 다음 행동

1. M1 변경과 M2 전환을 지정 범위만 stage·commit하고 M2-S1 phase 계약을 실행한다.

> M0은 통과했고 M0 설계 커밋은 `a1977a5`다. M1 Core 변경 승인이 확인됐으며, dependency 설치·CI·보호 데이터 접근은 정의된 별도 경계를 유지한다.
