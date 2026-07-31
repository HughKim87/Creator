# W4 runtime 보존·output 지식 통합·승인 정리

- 문서 분류: `phase-design`
- phase ID: `W4`
- lifecycle: `passed`
- 결과: runtime 67개와 current output 4개를 보존하고 재사용 지식은 기존 owner에 병합했으며, 승인된 300개·488,962,975 bytes와 Git garbage 6,998,265,971 bytes를 무결성 손실 없이 정리했다.
- 독자: W4 실행 agent, 보호 output·Core·삭제·Git maintenance 승인자
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- optional evidence owner: `extension/work/repository-consolidation/W3_DISPOSITION_MANIFEST.md` — startup-required 아님, W3 수치의 역사 근거이며 현재 runtime·input 판정 권위가 아님
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; 사용자는 `e705f71` 보존, 아래 exact Core 보강, 300개·6디렉터리 처분, Git object 위생과 단계 commit을 현재 대화에서 승인했다. push·publish는 제외한다.
- 첫 다음 행동: W5에서 규칙별 원문→추출→owner 계보를 최종 보고하고 initiative 문서를 self-clean한다.

## Entry gate

- W3 commit `73d66e4`와 clean status가 확인됐다.
- 현재 분석 범위는 `extension/outputs/**`, `extension/.runtime/**`, 처분 후보 tracked·cache·local state, `.git` 위생이다.
- `extension/inputs/**` 전체는 수치·순위·보존 적합성·처분 분석에서 제외하고 보호 원본으로 그대로 둔다.
- runtime은 67개·816,338,813 bytes, outputs는 201개·604,959,116 bytes다.
- pre-delete snapshot `e705f71`은 실제 파일 272개를 추가했고, 기존 tracked 28개와 합쳐 300개·488,962,975 bytes를 복구한다.

## 불변 경계

- `e705f71`은 사용자가 명시한 삭제 전 일회성 복구 commit으로 기록한다. 이후 보호 input·output의 추가 stage·commit은 0이어야 하며 push하지 않는다.
- runtime binary·model은 ignored 상태를 유지하고 Git에 넣지 않는다.
- 현재 `video-to-srt`의 faster-whisper primary 계약을 whisper.cpp로 암묵 교체하지 않는다.
- media content 재생·전사·이미지 분석은 metadata·sidecar로 판정할 수 없고 사용자가 exact 항목·목적을 승인한 경우에만 한다.
- Git garbage 정리는 branch·tag·stash·reflog와 현재 reachable commit을 보존하는 별도 destructive gate다.

## Slice gate

각 slice는 입력 집합·owner·변경·검증·복구·잔여 위험을 기록하고 목표와 실제 결과를 0~5점으로 채점한 뒤 다음 slice로 전환한다.

## W4-S1 — runtime을 관리되는 local capability로 전환

현재 runtime을 두 component로 고정한다.

| component | 역할 | 상태 |
|---|---|---|
| FFmpeg 8.1.2 | 공용 영상 probe·변환·audio fixture 생성 | retained shared tool |
| whisper.cpp v1.8.6 + `ggml-small.bin` | 선택적 offline transcription backend | retained optional; faster-whisper 대체 아님 |

최소 tracked owner를 다음처럼 설계한다.

- `extension/config/local-runtime-v1.json`: component version·role·relative root·file count·bytes·tree digest·critical entrypoint hash·license·source/reinstall metadata
- `extension/schemas/local-runtime-v1.schema.json`: status와 필수 필드 계약
- `extension/src/local_runtime.py`: absent/ready/drift를 구분하는 read-only verifier
- `extension/tests/test_local_runtime.py`: synthetic tree·clean-clone absent·hash drift 회귀
- `extension/README.md`: owner route, primary/optional backend 구분, 검증 명령

### W4-S1 gate

- 67/67 파일, 816,338,813 bytes, reparse 0과 tree digest 일치
- FFmpeg·FFprobe version probe 성공, synthetic audio 생성·probe 성공
- whisper CLI·DLL·model hash 일치와 보호자료 없는 짧은 model-load smoke test 성공
- source·license·reinstall 경로가 검증되거나 `reinstall-unverified` 위험이 명시됨
- runtime staged 0, clean clone에서는 `absent/optional`로 정상 판정
- W4-S1 전용 commit 후 status clean

### W4-S1 실제 결과 — passed, 4.8/5

- commit `0ec2960`; runtime 67/67·816,338,813 bytes와 5개 actual probe, 14개 focused test가 통과했고 ignored/stage 경계를 유지했다.
- 구성·실행·역할/clone은 각 5/5, 출처·복구는 외부 reinstall 미실행으로 4/5다.

## W4-S2 — outputs 201개의 lineage와 재사용 가치 확정

보존 allowlist 4개·117,222,243 bytes는 content 변경 없이 existence·size·hash만 확인한다. 나머지 197개·487,736,873 bytes를 두 queue로 나눈다.

| queue | 파일 수 | 용량 | 기본 판정 |
|---|---:|---:|---|
| MP4·WAV·PNG media | 113 | 475,943,400 bytes | raw Git archive 금지, lineage 확인 후 처분 |
| XML·JSON·TXT·MD·SRT structure/text | 84 | 11,793,473 bytes | 재사용 지식 추출 후보 |

structure/text 84개는 exact 보호 열람 승인 뒤 normalized hash·version lineage·current owner·재현 가능성을 대조한다. W1의 10개 opaque group과 84/84를 교차검증하고 각 항목을 `absorbed / current-deliverable / regenerable / unique-evidence / unresolved` 중 하나로 판정한다.

media 113개는 sidecar·hash·버전명으로 먼저 판정하고, content 검수 없이 current 결과와 중복·이전 revision임이 입증되지 않는 항목만 exception queue로 남긴다.

### W4-S2 gate

- inputs 접근 0, outputs 201/201 분류, keep 4와 candidate 197의 겹침 0
- structure/text 84/84 owner mapping과 media 113/113 lineage 판정
- protected 원문·exact 이름의 tracked evidence·stage 0
- unresolved는 exact 이유·다음 확인·삭제 제외 조건을 가짐

### W4-S2 실제 결과 — passed, 5/5

- 승인 structure/text 84/84·11,793,473 bytes는 UTF-8이며 JSON 22/22, XML 17/17, SRT 15/15가 parse됐다. MD 14는 기존 owner에 흡수된 지식, 나머지 70은 재생성 파생물이다.
- media 113/113·475,943,400 bytes는 내용·신규 hash 없이 metadata와 sidecar로 계보를 확인했다. 103개는 직접 참조, 10개는 같은 evidence group의 sibling이다.
- 전체 201개 판정은 `current-deliverable 4 / absorbed 14 / regenerable 183 / unique-evidence 0 / unresolved 0`이며 candidate 197의 W3 path+size digest가 일치한다.
- W1과 JSON 23·XML 18·SRT 16 총계와 XML clip 7,452를 재현했다. MD line 차이 14는 trailing newline 계수 방식 차이다.

## W4-S3 — 재사용 지식 흡수와 보존 방식 결정

재사용 단위는 영상별 수치·문구가 아니라 반복 가능한 조건·행동·예외·검증·실패 예방으로만 추출한다. owner 우선순위는 `VIDEO_EDITING_WORKFLOW_CONTRACT.md` → `video-editing-artifact-lineage.md` → 기존 schema/test → 필요한 경우에만 최소 새 owner다.

사용자 정정에 따라 이번 candidate 197개는 `.gitignore`의 일회성 예외로 pre-delete commit에 직접 보존한다. keep 4·inputs·runtime은 계속 ignored이며 삭제 commit에서 예외를 원복한다.

### W4-S3 gate

- 추출 단위 100%가 source opaque ID·evidence·owner·검증과 연결
- 새 file·rule·schema·test 증가는 기존 owner로 표현할 수 없는 책임만 허용
- runtime·startup이 과거 output이나 보고서를 active authority로 참조하지 않음
- 흡수 commit에는 보호·runtime·Core 경로 0, 전체 gate 통과

### W4-S3 실제 결과 — passed, 5/5

- MD 14개는 분석·spine 5→계약/R05~R09, evidence·anchor 4→R04, 검증 4→R10~R15, 통합 revision 1→기존 규칙·candidate로 14/14 mapping됐다.
- 새 재사용 trigger·owner gap이 없어 canonical owner·rule·schema·test delta는 0이고 보호 원문 복제도 0이다.

## W4-S4 — exact 승인 처분과 reference release

처분 기준은 tracked history 28개·319,521 bytes, cache/local 75개·906,581 bytes, output candidate 197개·487,736,873 bytes다. 합계 300개·488,962,975 bytes이며 runtime 67개·inputs·output keep 4개는 제외한다.

`e705f71`의 272개 raw blob·worktree hash는 272/272 일치했고 삭제 집합 300개는 누락 0으로 현재 존재한다. Core는 `test_rule_routing.py`의 역사 fixture 전환, `maintenance.py`의 tracked protected 검사, `test_maintenance.py` 회귀와 cache 25개·빈 `core/docs/domain/` 처분만 허용한다. 300개와 빈 디렉터리 6개를 child-before-parent로 제거하고 ignore·attributes 임시 설정을 원복한다.

### W4-S4 gate

- pre-delete commit tree가 300개 삭제 대상을 복구하고 keep·runtime·inputs 포함이 0; raw blob mismatch 0
- 승인된 Core·삭제 범위와 실행 집합의 path·count·bytes·digest 100% 일치
- 삭제 후 tracked·ignored·filesystem 예상치와 실제치 일치
- 보호 keep 4, runtime 67, inputs 전체의 mutation·stage 0
- ignore·attributes 예외 원복, tracked output·cache·local-state 0, Core·Extension·maintenance·route·clean-clone 통과 후 별도 처분 commit
### W4-S4 실제 결과 — passed, 5/5
- 승인 집합 그대로 300개·488,962,975 bytes와 빈 디렉터리 26개를 제거했고 staged tree는 삭제 300·변경 7·추가 0, untracked 0이다. keep output 4·117,222,243 bytes와 runtime 67·816,338,813 bytes는 ignored·실재·stage 0이다.
- Core 140·Extension 138·maintenance 71문서/85링크·clean-clone 3종·runtime actual probe·`git diff --check`가 통과했고 tracked input·output·cache는 0이다.

## W4-S5 실제 결과 — passed, 5/5

- 전: `.git` 7,359,690,190 bytes, loose 3,709·648.26 MiB, pack 2·3.32 GiB, garbage 38·2.89 GiB, `fsck` exit 0.
- reflog 만료를 `never`로 고정한 Git-native GC 후 `.git`은 361,424,219 bytes, pack 1·344.50 MiB, loose·garbage 0이 됐다. 회수량은 6,998,265,971 bytes(95.1%)다.
- refs 11·stash 2·reflog 393·reachable 4,640·graph 224의 count/SHA-256이 전후 동일하고 `e705f71` commit/tree도 동일하다. post `fsck` 출력 0, status clean이다.

## Exit·commit·transition 실제 결과

- W4-S1~S5가 모두 passed이고 inputs 밖 잔여 파일은 canonical tracked 193, 보호 output 4, managed runtime 67로 설명된다.
- 처분·보호 게이트는 `53607e9`; Core 140·Extension 138·maintenance·runtime probe·clean-clone 3종이 통과했다.
- W5만 활성화해 규칙별 계보 최종 보고, initiative self-clean, idle handoff와 final clean commit을 수행한다.

## 단계·슬라이스 교차검증 점수

| 슬라이스 | 점수 | 이유 |
|---|---:|---|
| W4-S1 runtime | 4.8/5 | 67/67 파일·digest·실행 probe를 통과했고 source 재설치 자동화만 미구현이다. |
| W4-S2 output | 5/5 | 201/201을 keep 4·candidate 197로 완전 분류했다. |
| W4-S3 흡수 | 5/5 | MD 14/14를 기존 규칙·계약 owner와 대조해 신규 중복 owner 0을 확인했다. |
| W4-S4 처분 | 5/5 | 승인 300개와 실제 삭제의 path·count·bytes가 일치하고 보호 overlap 0이다. |
| W4-S5 Git | 5/5 | 보존 해시 불변, fsck 정상, 6.998 GB 회수와 garbage 0을 입증했다. |
| W4 전체 | 4.96/5 | 모든 성공 gate가 통과했고 감점은 runtime 재설치 자동화 부재뿐이다. |
