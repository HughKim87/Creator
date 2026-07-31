# W4 runtime 보존·output 지식 통합·승인 정리

- 문서 분류: `phase-design`
- phase ID: `W4`
- lifecycle: `ready`
- 결과: `inputs/**`를 분석에서 제외하고, runtime 67개를 검증 가능한 선택적 capability로 보존하며, outputs 197개에서 재사용 지식만 canonical owner에 흡수한 뒤 승인된 잔여물과 Git garbage를 정리한다.
- 독자: W4 실행 agent, 보호 output·Core·삭제·Git maintenance 승인자
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- optional evidence owner: `extension/work/repository-consolidation/W3_DISPOSITION_MANIFEST.md` — startup-required 아님, W3 수치의 역사 근거이며 현재 runtime·input 판정 권위가 아님
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; 이 문서는 설계만 승인하며 보호자료 열람·Core 변경·삭제·Git object prune를 승인하지 않는다.
- 첫 다음 행동: W4-S1에서 runtime 67개를 content 변경 없이 tree hash·version·entrypoint·license·source 기준으로 재측정한다.

## Entry gate

- W3 commit `73d66e4`와 clean status가 확인됐다.
- 현재 분석 범위는 `extension/outputs/**`, `extension/.runtime/**`, 처분 후보 tracked·cache·local state, `.git` 위생이다.
- `extension/inputs/**` 전체는 수치·순위·보존 적합성·처분 분석에서 제외하고 보호 원본으로 그대로 둔다.
- runtime은 67개·816,338,813 bytes, outputs는 201개·604,959,116 bytes다.
- 삭제·Core·Git prune는 exact 승인을 받기 전 0이어야 한다.

## 불변 경계

- 보호 input·output을 stage·commit하거나 exact 이름·원문을 tracked evidence에 복제하지 않는다.
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

## W4-S3 — 재사용 지식 흡수와 보존 방식 결정

재사용 단위는 영상별 수치·문구가 아니라 반복 가능한 조건·행동·예외·검증·실패 예방으로만 추출한다. owner 우선순위는 `VIDEO_EDITING_WORKFLOW_CONTRACT.md` → `video-editing-artifact-lineage.md` → 기존 schema/test → 필요한 경우에만 최소 새 owner다.

raw 보호 output은 현재 규칙상 `git add -f` 보존 대상이 아니다. 권장 보존은 보호 원문을 복사하지 않은 canonical 문서·schema·test diff다. raw structure archive가 꼭 필요하면 permanent Git 노출과 history 증가를 명시한 별도 exact 보호정책 승인을 받기 전에는 실행하지 않는다.

### W4-S3 gate

- 추출 단위 100%가 source opaque ID·evidence·owner·검증과 연결
- 새 file·rule·schema·test 증가는 기존 owner로 표현할 수 없는 책임만 허용
- runtime·startup이 과거 output이나 보고서를 active authority로 참조하지 않음
- 흡수 commit에는 보호·runtime·Core 경로 0, 전체 gate 통과

## W4-S4 — exact 승인 처분과 reference release

권장 처분 기준은 tracked history 28개·319,521 bytes, cache/local state 75개·906,581 bytes, output candidate 197개·487,736,873 bytes다. 합계는 300개·488,962,975 bytes이며 runtime 67개와 input 2개는 제외한다.

역사 보고서를 읽는 `core/tests/test_rule_routing.py`는 exact Core 승인 뒤 현재 `staged-work-design.md` fixture로 전환한다. 빈 디렉터리 6개는 child-before-parent로 제거한다. 승인 직전 count·bytes·digest·containment·reparse·allowlist overlap을 재검증한다.

### W4-S4 gate

- exact Core 승인·exact delete 승인·보호 structure 열람 승인이 서로 구분됨
- 승인 집합과 실행 집합의 path·count·bytes·digest 100% 일치
- 삭제 후 tracked·ignored·filesystem 예상치와 실제치 일치
- 보호 keep 4, runtime 67, inputs 전체의 mutation·stage 0
- Core·Extension·maintenance·route·clean-clone 통과 후 W4 처분 commit

## W4-S5 — Git object 위생

artifact 분석과 분리해 `.git` 6.428 GiB를 감사한다. 현재 확인된 3.284 GiB unreachable pack과 2.895 GiB temporary garbage는 백업으로 간주하지 않는다. `main`, 모든 branch·tag, stash 2개, reflog와 HEAD의 reachable objects를 보존하고 exact Git maintenance 승인 뒤 Git-native prune/repack을 수행한다.

### W4-S5 gate

- prune 전후 `fsck`, refs·stash 목록, HEAD·commit graph·bundle 또는 동등한 reachable recovery 검증
- 제거 대상은 unreachable/temporary object로만 한정
- 예상 최대 회수 약 6.18 GiB와 실제 회수량 보고
- 작업트리·index·commit 내용 불변, `git status` clean

## Exit·commit·transition gate

- W4-S1~S5가 passed이고 inputs 밖 모든 잔여 파일이 canonical tracked, 보호 current output, managed runtime 중 하나로 설명된다.
- strict UTF-8·NUL·후행 공백·link·`git diff --check`, Core 139+·Extension 132+, clean-clone 3종이 통과한다.
- W4 점수는 S1 runtime readiness, S2 coverage, S3 absorption, S4 disposition, S5 Git integrity를 각 5점으로 교차검증한다.
- W5는 initiative 문서를 self-clean하고 handoff를 idle truth로 갱신하며 단일 최종 보고서와 final clean commit을 만든다.

## 설계 교차검증 점수

| 설계 슬라이스 | 점수 | 이유 |
|---|---:|---|
| 범위·수치 | 5/5 | inputs를 제외하고 runtime·outputs·처분 합계를 실제 filesystem과 대조했다. |
| runtime 관리 | 4/5 | primary/optional 역할과 owner·smoke gate는 명확하지만 source·reinstall은 실행 단계에서 검증해야 한다. |
| output 선별 | 5/5 | 201개를 keep 4·media 113·structure 84로 완전 분할하고 raw Git 보존 경계를 분리했다. |
| 승인·복구 | 4/5 | 보호 열람·Core·삭제·Git prune를 분리했지만 실제 승인은 아직 없고 Git recovery 구현도 남았다. |
| 설계 전체 | 4.5/5 | 실행 가능한 순서와 정량 gate가 완결됐으며 감점은 의도적으로 실행 단계에 남긴 외부 검증·승인이다. |

## 복구·중단 조건

- runtime smoke test나 source 검증이 실패해도 파일을 삭제하지 않고 `retained-unverified`로 격리한다.
- structure/text 84개 중 unique evidence가 있으면 해당 항목을 삭제 집합에서 제외한다.
- 승인 뒤 digest가 달라지거나 새 output이 생기면 mutation을 중단하고 manifest를 갱신한다.
- Git fsck·refs·stash·recovery 검증 중 하나라도 실패하면 object cleanup을 수행하지 않는다.
