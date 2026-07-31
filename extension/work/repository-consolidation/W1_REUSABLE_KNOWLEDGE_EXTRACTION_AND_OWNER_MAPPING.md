# W1 재사용 지식 추출·owner mapping

- 문서 분류: `phase-design`
- phase ID: `W1`
- lifecycle: `passed`
- 결과: W0가 지정한 report·plan·prior evidence·보호 outputs 후보에서 이후 workflow에 재사용할 수 있는 의미만 추출하고, 기존 canonical owner·보강 필요·미흡수 이유를 evidence와 연결한다.
- 독자: W1 실행 agent와 W2 변경 범위를 검토하는 사용자
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- optional evidence owner: `extension/work/repository-consolidation/W1_REUSABLE_KNOWLEDGE_MAP.md` — startup-required 아님, 보호 exact 이름·원문·task fact 금지, W4까지 유지 후 W5 정리 후보
- W0 evidence: `extension/work/repository-consolidation/W0_FILE_CLASSIFICATION.md`
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; W1은 owner mapping만 수행하며 Core·Extension owner mutation, 삭제·이동, 보호 stage·commit을 승인하지 않는다.
- 첫 다음 행동: W1 task-owned 5경로만 stage해 단계 checkpoint를 commit하고, commit 검증 뒤 W2 phase를 활성화한다.

## Entry gate

- W0-S1~S4와 exit/commit/transition이 passed이고 checkpoint는 `16f87cc`다.
- entry 작업트리는 clean이며 W1은 이 commit을 baseline으로 사용한다.
- W0 queue는 이전 report·plan·foundation 21개, prior evidence 7개, output opaque group의 MD·JSON·TXT·SRT·XML이다.
- `docs.md`, Python cache, Obsidian local state, MP4·PNG·WAV binary content, local runtime binary/model은 reusable content queue에서 제외한다.

## 포함·제외 범위

포함:

- tracked nonprotected 21개 report·plan·foundation 문서의 재사용 가능한 조건·행동·예외·검증
- prior evidence 7개의 현재 전역 목표 대비 미흡수 delta
- 보호 outputs의 MD·JSON·TXT·SRT·XML에서 반복 workflow·검증·실패 예방을 판단하는 최소 구조·내용
- 현재 owner·route·test와의 직접 대조

제외:

- 단일 영상의 제목·대본·자막 본문·프레임·파일명·해시·사용자 승인·개별 결과
- 보호 media binary의 재생·전사·이미지 내용 분석
- 모든 과거 문구의 자동 흡수
- W1에서의 owner 본문 수정, 새 rule·schema·tool 생성, Core mutation, 삭제·이동

보호 산출물은 W0 opaque group으로만 evidence에 기록한다. 원문·exact filename·task fact는 persistent 문서나 Git에 복제하지 않는다.

## 판정 체계

각 의미 후보는 다음 중 하나로 판정한다.

- `already-canonical`: 현재 owner가 trigger·action·exception·verification을 충분히 보존
- `strengthen-existing-owner`: 반복 workflow 가치가 있고 현재 owner에 행동 공백이 있음
- `domain-candidate`: 한 작업 이상의 근거가 필요하거나 YouTube/video 조건에 종속
- `task-specific`: 단일 작업 사실·수치·선호·산출물
- `superseded-or-unsafe`: 현재 정책·workflow와 충돌하거나 위험
- `unresolved`: source·적용 범위·반복 근거가 부족

## Slice gate

W1-S1~S4는 source·evidence label·현재 owner·판정·미흡수 이유를 W1 evidence에 기록하고, 보호 원문이 남지 않았음을 확인한 뒤 다음 slice로 전환한다.

## W1-S1 — 이전 report·plan·foundation 21개

문서를 source family별로 읽고 제목·결론 복사가 아니라 의미 단위로 대조한다.

1. project-foundation 8개
2. 2026-07-24 진단 1개
3. 2026-07-27 report·plan 4개
4. 2026-07-28 report·plan 8개

### W1-S1 gate

- 21/21 문서가 exact source family와 extraction 상태를 가진다.
- 재사용 후보는 현재 owner와 direct evidence를 가지며 중복 보고는 evidence 수를 늘리지 않는다.
- 이미 M0~M2에서 반영된 규칙 의미를 새 후보로 중복 계산하지 않는다.

## W1-S2 — prior evidence 7개 delta

M0 map·M0~M4 phase·이전 partial report를 새 전역 목표와 대조한다. 완료 기록은 Git에 두고, W2 행동을 바꾸는 미흡수 의미만 남긴다.

### W1-S2 gate

- previous rule/document slice의 유효 결과와 전역 범위 공백이 분리된다.
- active overall·W0 evidence와 중복되는 설명은 W1 candidate로 만들지 않는다.

## W1-S3 — 보호 outputs의 text·structure 후보

W0 opaque group별로 확장자·schema key·heading·validator 상태를 먼저 보고, 재사용 판단에 필요한 exact text fragment만 현재 메모리에서 검토한다.

- MD·TXT: 반복 절차·검증·실패 예방만 추출
- JSON: key/schema/state 구조만 우선하고 task value는 복제하지 않음
- SRT: cue 구조·검증 문제만 판단하고 본문은 추출하지 않음
- XML: profile·source/link/clip 구조만 판단하고 media path는 복제하지 않음

### W1-S3 gate

- opaque output 10그룹의 text/structure 후보가 모두 검토 또는 미검토 사유를 가진다.
- 보호 exact 이름·본문·media path·사용자 사실이 evidence에 0건이다.
- code·test·contract에서 이미 생성·검증 가능한 구조는 산출물 자체에서 중복 승격하지 않는다.

## W1-S4 — owner matrix·W2 exact 입력

후보를 기존 owner별로 합치고 신규 owner 필요성을 별도 판정한다. W2에는 `strengthen-existing-owner`만 exact path·이유·최소 delta·검증과 함께 넘긴다. Core 후보는 extension-only 대안과 현재 대화 exact 승인 필요성을 표시한다.

### W1-S4 gate

- 모든 후보가 판정 1개와 evidence·owner·미흡수 이유를 가진다.
- existing owner 우선이며 신규 owner는 trigger·reader·responsibility가 실제로 구분될 때만 후보가 된다.
- 보호 자료를 근거로 foundation rule을 자동 승격하지 않는다.
- W2 exact path set, Core 승인 경계, Extension-only 대안, 예상 복잡성 delta가 있다.

## Exit·commit·transition gate

- W1-S1~S4가 passed이고 source coverage·보호 경계·owner uniqueness가 검증된다.
- Core·Extension 회귀, maintenance, design budget, strict UTF-8·NUL·후행 공백·links·diff check가 통과한다.
- task-owned W1 phase/evidence·overall·handoff만 단계 commit하며 보호 path·raw extraction·unrelated file은 stage하지 않는다.
- commit 검증 뒤 W2가 여전히 필요한지 재판정하고, 필요한 exact Core 변경은 W2 mutation 전에 사용자 승인을 확인한다.

## 복구·중단 조건

- 보호 원문·exact filename·task fact가 persistent evidence에 들어가면 해당 evidence를 성공으로 보고하지 않고 제거·재작성한다.
- source 내용과 현재 owner가 충돌하면 자동 흡수하지 않고 `superseded-or-unsafe` 또는 `unresolved`로 남긴다.
- W2 후보가 owner 신설·Core 변경을 요구하면 이유·대안을 기록하고 W1에서는 구현하지 않는다.

## Gate evidence

- source coverage: 과거 문서 21/21, 선행 evidence 7/7, 보호 opaque output 10/10
- 재사용 결과: K01~K04, 기존 owner 3개, 신규 owner·Core 후보 0
- Core·Extension: 139·132 tests passed
- Node runtime: v20.11.1 ready
- maintenance: 95 documents, 122 links, errors·drift·duplicates 0
- clean clone: ASCII·한글+공백·공백 경로 3/3 bootstrap와 inner verify passed
- 설계 예산: overall 90줄·5,024자, W1 phase 136줄·5,306자
- 보호 exact persistent 기록·Core diff·삭제·이동: 0

## Closeout record

- W1-S1: `passed` — 21/21 source family·의미·현재 owner 대조
- W1-S2: `passed` — 선행 evidence 7/7의 유효 결과와 전역 delta 분리
- W1-S3: `passed` — 보호 output 10/10 구조 검토, exact persistent 기록 0
- W1-S4: `passed` — K01~K04를 기존 owner 3개와 W2 exact path로 고정
- W1 exit: `passed`
- W2 transition: `ready-after-commit` — Core 변경 없이 root·Extension owner 3개만 보강
