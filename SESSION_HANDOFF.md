# 세션 핸드오프

- 갱신일: 2026-07-31
- 역할: ainotebook 이외 worktree의 현재 상태 단일 owner
- 현재 작업: 없음 — 프로젝트 전역 지식 선별·기반 통합·workspace 정리 W0~W5 완료
- 상태: idle; 활성 계획·task-rule·scratch·종료 보고서는 없다.
- branch: `main`
- 활성 전체 설계: 없음
- 활성 단계 설계: 없음
- handoff mode: `same-workspace`; Git checkout은 재현 가능하고 uncommitted ignored runtime·current output은 이 workspace에만 존재한다.
- startup route: `PROJECT_RULES.md` → 이 문서 → 새 사용자 요청에 매칭되는 규칙. 활성 overall/phase 문서는 없다.

## 완료 결과

- inputs는 분석·변경·stage에서 제외했다.
- 삭제 전 복구 commit `e705f71`에 ignored actual 272개·488,643,454 bytes를 byte-identical로 보존했다.
- 처분 commit `53607e9`에서 승인된 300개·488,962,975 bytes를 제거하고 tracked input·output·cache를 0으로 만들었다.
- FFmpeg·whisper.cpp runtime 67개·816,338,813 bytes와 current output 4개·117,222,243 bytes는 ignored 상태로 보존했다.
- Git GC 전후 refs 11·stash 2·reflog 393·reachable object 4,640·graph 224의 count/SHA-256이 같고 `.git`은 7,359,690,190→361,424,219 bytes로 줄었다.
- 삭제 자료의 재사용 지식은 현재 canonical owner에 흡수됐고, 상세 계보·완료 수치·점수는 Git history가 소유한다.

## 최종 검증 기준

- Core 141, Extension 139, bootstrap·Node·maintenance·clean-clone 3종 통과
- runtime actual probe 통과
- inputs 제외 tracked 183, untracked 0, ignored 71, filesystem 254
- ignored 71 = runtime 67 + current output 4
- tracked input·output·cache 0, Git status clean

## 유지 artifact

| 경로 | 역할 |
|---|---|
| `PROJECT_DIRECTION.md` | 장기 사용자 결과·방향 |
| `PROJECT_RULES.md` | startup·권한·보호·Core·검증 정책 |
| `SESSION_HANDOFF.md` | 현재 idle 상태와 로컬 보존 allowlist |
| `extension/config/local-runtime-v1.json` | ignored runtime manifest |

## 잔여 제한

- runtime source 재설치 자동화는 없지만 현재 version·digest·실행 probe는 통과했다.
- browser-user-session은 deterministic clone bootstrap 밖의 의도된 `needs_user`다.

## 첫 다음 행동

1. 새 요청이 오면 `PROJECT_RULES.md`를 읽고 이 idle 상태에서 작업을 새로 분류한다.

완료된 W0~W5 문서를 복구하거나 읽을 필요는 없으며, 역사 확인이 필요할 때만 exact Git commit을 사용한다.

## 다음 session 시작 prompt

`PROJECT_RULES.md`와 `SESSION_HANDOFF.md`를 읽고 새 사용자 요청을 분류한다. 활성 설계는 없고 inputs·runtime·current output 경계를 유지한다.
