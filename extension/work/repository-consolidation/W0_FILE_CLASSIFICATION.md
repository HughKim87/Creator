# W0 프로젝트 전역 file classification

- 문서 분류: `reference-evidence`
- startup-required: 아니오
- owner: `extension/work/repository-consolidation/W0_REPOSITORY_WIDE_INVENTORY_AND_CLASSIFICATION.md`
- 독자: W0 검토자와 W1~W4 실행 agent
- 역할: 전 작업트리 inventory의 재현 기준·그룹 분류·보호 aggregate·후속 queue 보존
- 보존: W4 처분 검증까지; W5에서 Git history 복구 가능성을 확인한 뒤 정리 후보
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; 이 문서는 삭제·이동·Core·보호 content 접근 승인이 아니다.
- 측정 시점: 2026-07-31 14:14 KST, branch `main`, HEAD `11a6031`
- evidence label: 별도 표시가 없으면 `direct remeasurement`

## 사용자 의도 적용

이 inventory는 ignored 파일을 추적하기 위한 목록이 아니다. tracked·untracked·ignored·filesystem 항목을 같은 기준으로 대조하고, 백룸·개선 과정의 결과 중 이후 workflow에 재사용할 가치가 있는 내용만 W1로 넘기기 위한 1차 분류다. content 존재 자체는 재사용 판정이 아니며, 보호 이름·내용과 secrets는 이 문서에 복제하지 않는다.

## W0-S1 재현 기준과 일치성

| inventory | 재현 기준 | 파일 |
|---|---|---:|
| tracked | `git ls-files` | 209 |
| untracked | `git ls-files --others --exclude-standard` | 1 |
| ignored | `git ls-files --others --ignored --exclude-standard` | 345 |
| Git union | 세 집합의 unique union | 555 |
| filesystem | root recursive file metadata − `.git/**` | 555 |

- Git union과 filesystem 차이: 양방향 0
- Git state 중복: 0
- filesystem total: 5,223,547,559 bytes
- enumeration error·reparse point: 0·0
- `extension/data/`: 0 files / 0 bytes
- 보호 경로: 203 files / 4,404,820,076 bytes
- entry dirty 10경로 composite SHA-256: `0e8d0667a56ef976250234e233f6b2f29b4cdd93c6f900b54024bebe133159ad`

entry dirty exact paths:

- `PROJECT_DIRECTION.md`
- `SESSION_HANDOFF.md`
- `extension/reports/2026-07-31_규칙_무손실_통합_M0_작업_보고.md`
- `extension/tests/test_staged_design_routing.py`
- `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- `extension/work/repository-consolidation/W0_REPOSITORY_WIDE_INVENTORY_AND_CLASSIFICATION.md`
- `extension/work/rule-preservation/M1_PRESERVATION_VALIDATION_AND_MINIMAL_CHANGE.md`
- `extension/work/rule-preservation/M2_RESTORE_INTEGRATE_AND_SINGLE_GATE.md`
- `extension/work/rule-preservation/M3_STARTUP_ROUTE_REGRESSION_AND_DISPOSITION.md`
- `extension/work/rule-preservation/M4_EXACT_DISPOSITION_AND_FINAL_REPORT.md`

이 anchor는 W0 실행 시작 상태다. 이후 이 evidence와 handoff 변경은 task-owned delta로 별도 비교한다.

## W0-S2~S4 전체 분류

아래 18개 행은 상호 배타적이며 555개 파일을 전부 덮는다.

| Git state | group | files | bytes | provenance / role | owner·rebuild/recovery | reuse / safety |
|---|---|---:|---:|---|---|---|
| tracked | domain code·tests | 45 | 253,629 | canonical / code·test·schema·example | `extension/README.md`; Git | `canonical-retain / normal` |
| tracked | domain docs·rules | 10 | 53,054 | canonical / contract·rule | `extension/README.md`; Git | `canonical-retain / normal` |
| tracked | shared Obsidian config | 1 | 173 | canonical / editor safety config | `.gitignore`; Git | `canonical-retain / normal` |
| tracked | foundation code·tests | 41 | 416,312 | canonical / code·test·schema | `PROJECT_RULES.md`; Git | `canonical-retain / normal` |
| tracked | foundation docs·rules | 29 | 131,691 | canonical / policy·contract·failure | `PROJECT_RULES.md`; Git | `canonical-retain / normal` |
| tracked | project tools | 5 | 13,717 | canonical / bootstrap·verify tool | root scripts; Git | `canonical-retain / normal` |
| tracked | root controls excluding `docs.md` | 10 | 27,603 | canonical / route·config·state | root owner별; Git | `canonical-retain / normal` |
| tracked | `docs.md` | 1 | 0 | historical / empty document | owner 없음; Git | `disposition-candidate / normal` |
| tracked | skill sources | 37 | 228,588 | canonical / repeatable workflow | `.agents/skills/`; Git | `canonical-retain / normal` |
| tracked | active work controls | 2 | 10,582 | current / failure state·overall | handoff route; Git | `canonical-retain / normal` |
| tracked | prior rule/document evidence | 7 | 107,119 | improvement / map·phase·partial report | current overall; Git | `historical-git / normal` |
| tracked | prior M4 file candidates | 21 | 230,792 | backroom·improvement / report·plan | invalidated M4 exact list; Git | `disposition-candidate / normal` |
| untracked | W0 phase design | 1 | 8,962 | current improvement / phase | active overall; phase exit commit | `canonical-retain / normal` |
| ignored | Obsidian local state | 4 | 8,202 | runtime / editor UI state | Obsidian 재생성; active exact ref 0 | `regenerable-disposable / normal` |
| ignored | protected inputs | 2 | 3,799,860,960 | user-source / media·subtitle | 사용자 원본; Git 복구 없음 | `protected-user-artifact / protected-metadata` |
| ignored | protected outputs | 201 | 604,959,116 | user-deliverable·derivative / mixed | 영상 workflow owners; Git 복구 없음 | `unresolved / protected-metadata` |
| ignored | Python caches | 71 | 898,246 | generated / bytecode cache | import·tests로 재생성; `.gitignore` | `regenerable-disposable / normal` |
| ignored | local runtime dependencies | 67 | 816,338,813 | runtime / ffmpeg·whisper tool/model | `extension/README.md` generic owner; exact rebuild 미확인 | `unresolved / external-recovery-required` |

분류 합계:

- `canonical-retain`: 181
- `historical-git`: 7
- `disposition-candidate`: 22
- `regenerable-disposable`: 75
- `protected-user-artifact`: 2
- `unresolved`: 268
- total: 555

`unresolved`는 자동 처분 실패가 아니라 다음 확인 조건이 있는 안전한 보류다. protected outputs 201개는 exact lineage·현재 deliverable·재생성 여부 확인이 필요하고, runtime 67개는 설치 source·version·rebuild 검증이 필요하다.

## 보호 aggregate

exact filename과 content를 보존하지 않고 parent path를 SHA-256으로 opaque ID화했다.

### Inputs

| opaque group | files | bytes | type summary | W0 판정 |
|---|---:|---:|---|---|
| `IN-b2c049ea49` | 2 | 3,799,860,960 | MP4 1, SRT 1 | 사용자 원본·선택 자막으로 보존 |

### Outputs

| opaque group | files | bytes | type summary | W0 판정 |
|---|---:|---:|---|---|
| `OUT-3537c733f2` | 15 | 28,563,640 | PNG 15 | review derivative; exact lineage 확인 |
| `OUT-4f577374b7` | 13 | 13,162,355 | JSON 1, MD 1, PNG 10, WAV 1 | mixed analysis derivative; W1 후보 |
| `OUT-52b4eba74b` | 17 | 15,869,397 | MD 1, PNG 15, TXT 1 | mixed review derivative; W1 후보 |
| `OUT-736a78dfc7` | 15 | 67,649,170 | WAV 15 | audio derivative; rebuild 확인 |
| `OUT-74185d747c` | 17 | 22,089,253 | JSON 1, MD 1, PNG 12, WAV 3 | mixed analysis derivative; W1 후보 |
| `OUT-7cfbf66621` | 7 | 14,486,007 | JSON 2, PNG 2, WAV 3 | mixed analysis derivative; W1 후보 |
| `OUT-b1781b1e40` | 41 | 438,647,615 | JSON 4, MD 10, MP4 4, PNG 4, SRT 1, XML 18 | deliverable·timeline mixed; current/obsolete 분리 필요 |
| `OUT-b9616a9104` | 30 | 4,252,707 | PNG 30 | review derivative; exact lineage 확인 |
| `OUT-ee118bab0c` | 45 | 228,545 | JSON 15, SRT 15, TXT 15 | transcription·validation mixed; W1 후보 |
| `OUT-f7969614e6` | 1 | 10,427 | MD 1 | task report; W1 후보 |

보호 outputs의 확장자 합계는 PNG 88, JSON 23, WAV 22, XML 18, TXT 16, SRT 16, MD 14, MP4 4이며 201개와 일치한다.

## Reference·rebuild·recovery 판정

- canonical tracked groups는 현재 router·contract·test에 연결되고 Git으로 복구 가능하다.
- 이전 22개 disposition 후보는 Git tracked이며, exact 목록은 invalidated M4에 있다. W1 지식 추출과 W3 새 manifest 전에는 삭제하지 않는다.
- Python cache는 `.gitignore` owner와 import/test rebuild가 있고 active runtime dependency가 아니다.
- ignored Obsidian local state의 exact active reference는 0이며 `.obsidian/app.json`만 shared config로 tracked다.
- `extension/.runtime/ffmpeg`와 `extension/.runtime/whisper.cpp` exact tracked reference는 각각 0이다. generic `.runtime` owner는 있으나 설치 source·rebuild command가 없어 W3 처분 판정을 보류한다.
- 보호 inputs·outputs는 Git 복구가 없고 사용자 원본·파생물 계약을 따른다. output의 재사용 판단은 text/JSON/MD/SRT/XML과 media metadata를 exact 목적에 필요한 최소 범위로 검토해야 한다.

## W1·W3 queue

### W1 reusable extraction queue

1. 이전 M4의 21개 report·plan·foundation 문서: 과거 extraction이 프로젝트 전역 목표를 다루지 않았으므로 재사용 지식을 다시 선별
2. output opaque groups의 MD·JSON·TXT·SRT·XML: 반복 workflow·검증·실패 예방 후보만 추출하고 task 사실은 승격하지 않음
3. prior rule/document evidence 7개: 이미 canonical owner에 반영된 의미와 새 전역 목표에서 필요한 delta만 확인

`docs.md`, Python cache, Obsidian local state, 바이너리 runtime은 reusable content queue에서 제외한다.

### W3 disposition/recovery queue

- 기존 M4 후보 22개
- Python cache 71개
- Obsidian local state 4개
- runtime dependency 67개 — rebuild 미확인 blocker
- protected outputs 201개 — exact lineage·current deliverable·외부 복구/사용자 승인 필요

## W0 slice 판정

| slice | 결과 | 점수 | 이유 |
|---|---|---:|---|
| W0-S1 | Git·filesystem 555/555, 차이·중복·오류·reparse 0 | 5/5 | 세 inventory가 독립적으로 일치 |
| W0-S2 | 18개 상호 배타 그룹으로 provenance·role·safety 100% 분류 | 5/5 | ignored/tracked 상태를 가치 판정으로 사용하지 않음 |
| W0-S3 | owner·reference·rebuild/recovery 연결 | 4/5 | runtime 67과 protected outputs 201은 안전하게 unresolved |
| W0-S4 | reuse/disposition 합계 555, 후속 queue 분리 | 5/5 | 미해결 항목에 exact 다음 조건이 있음 |
| W0 전체 | 전역 inventory·1차 분류 완료 | 4.75/5 | 실제 흡수·처분은 의도대로 후속 단계에 남김 |
