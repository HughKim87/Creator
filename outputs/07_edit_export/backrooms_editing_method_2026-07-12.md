# 백룸 영상 편집 개선 및 실행 명세

- 상태: `approved_for_next_stage`
- 작성일: 2026-07-12
- 역할: 다음 에이전트가 7단계 편집 문법·문서·XML 도구를 개선할 때 사용하는 구현 기준.
- 읽는 시점: `SESSION_HANDOFF.md`를 읽은 직후, 7단계 파일을 수정하기 전.
- 보존 기준: 개선 적용·검증·사용자 승인까지 유지하고, 적용 완료 후 정리 여부를 판단한다.
- 주의: 이 문서는 최종 컷 흐름 승인이 아니다. 캘리브레이션 XML 승인 전 전체 XML을 만들지 않는다.

## 1. 사용자 의도

사용자는 수동 편집본을 정답으로 복제하라는 것이 아니다. 원하는 감각은 다음과 같다.

- 설명·설정·반복·이동은 작은 단위로 나눠 빠르게 전진한다.
- 공포의 원인, 실제 행동, 살아 있는 리액션과 웃음은 충분히 전달한다.
- 길이를 줄이는 것보다 매 순간 이야기·정보·감정이 움직이는지가 중요하다.
- 편집 결과는 Premiere Pro CS6용 XML로만 제공한다.
- 전체 러프컷을 반복 수정하는 방식은 중단하고, 편집 감각을 작은 대표 구간에서 먼저 확정한다.

이 명세의 권장 모델은 **정보 밀도 기반 탄력 편집**이다. 수동본의 높은 정보 밀도는 채택하되, 모든 구간을 2초 단위로 자르지 않고 각성도·이해 부담·사건 경계에 따라 호흡을 바꾼다.

## 2. 기준 입력과 사용 금지 파일

기준 입력:

- 원본: `inputs/2026-06-30 00-23-03.mp4`
- 자막: `inputs/2026-06-30 00-23-03.srt`
- 승인 기획: `outputs/05_planning/video_plan_backrooms_2026-07-11.md`
- 화면 검증: `outputs/06_analysis/backrooms_6단계_화면검증_후보지도_2026-07-11.md`
- 수동 리듬 표본: `C:\Users\Hugh\Desktop\backroom.xml`의 `0:00~0:54.5667`만
- 현재 작업 상태: `SESSION_HANDOFF.md`

실패 분석용으로만 보존하고 새 기준으로 사용하지 않는 파일:

- `outputs/07_edit_export/backrooms_edit_v1.xml`
- `outputs/07_edit_export/cutlist_draft_v1.csv`

## 3. 실패 진단

기존 XML은 19:32.5에 영상 32클립뿐이며 평균 36.64초, 중앙값 30초다. 첫 60초는 4클립·3전환이고 C09는 3:22 연속 클립이다.

원인은 다음과 같다.

1. 5단계 이야기 비트와 6단계 후보범위를 실제 편집 컷으로 오인했다.
2. 후보의 핵심을 채굴하지 않고 후보 외피를 거의 그대로 보존했다.
3. `사건→반응→결과` 보존을 인과관계 보존이 아니라 시간 연속성 보존으로 해석했다.
4. CSV 한 행을 XML 한 클립으로 변환해 후보 내부의 침묵·반복·이동을 제거하지 않았다.
5. 서사 커버리지 승인과 편집 호흡 승인을 같은 것으로 취급했다.

따라서 문제는 XML 형식이나 Premiere 가져오기가 아니라 **후보범위와 실제 컷 사이에 microbeat 설계가 없었던 것**이다.

## 4. 수동본에서 채택할 것과 채택하지 않을 것

확인된 수동 표본:

- 첫 60초 19구간·18전환·중앙값 2.18초.
- 훅 뒤 `15.45~54.5667`은 17클립·평균 2.30초·중앙값 1.82초.
- 원본 `00:34.3~04:50.7`을 39.117초로 압축했다.
- 같은 기능 안 군더더기 18.083초, 기능 사이 중복 199.217초를 제거했다.
- 전환·속도변경·영상필터 없이 하드 점프컷만 사용했다.

채택:

- `새 정보 한 절 / 행동 한 박자 / 리액션 한 타격점`을 실제 컷 단위로 사용.
- 의미 중복 설명은 삭제하고 감정이 상승하는 반복은 보존.
- 훅은 강한 장면 나열보다 이해 가능한 미니 사건 하나로 설계.
- 속도감은 효과보다 선택·삭제·배치로 만든다.

채택하지 않음:

- 중앙값 2초대를 모든 구간의 합격선으로 사용.
- 수동본의 C11 훅을 자동 재채택.
- 하드 점프컷만 유일한 편집법으로 고정.
- 수동본 첫 55초를 전체 영상의 리듬 표본으로 확대 해석.

## 5. 편집 판단 모델

각 후보범위 안에서 먼저 아래 질문에 답한다.

1. 이 순간이 새 정보나 상태 변화를 주는가?
2. 감정·긴장·웃음을 상승시키거나 해소하는가?
3. 다음 장면의 원인·공간·행동을 이해하는 데 필요한가?
4. 내용은 반복돼도 퍼포먼스가 더 강해지는가?

네 항목이 모두 아니면 기본값은 제거다. 유지한다면 반드시 `기능`과 `유지 이유`를 기록한다. 긴 연속 컷은 `긴 호흡 이유`가 있어야 한다.

정보량과 각성도를 함께 판단한다.

| 구분 | 기본 처리 |
|---|---|
| 저정보·저각성 | 삭제 또는 강한 압축 |
| 고정보·저각성 | 절·UI 동작 단위 microcut |
| 저정보·고각성 | 긴장 누적·여운 기능이 있으면 유지, 아니면 축소 |
| 고정보·고각성 | 컷 수를 줄이고 원인→인지→행동→반응→결과를 보존 |

## 6. 콘텐츠 유형별 편집 방법

아래 길이는 수동본과 연구를 바탕으로 한 **시작 휴리스틱**이며 게이트가 아니다.

| 유형 | 방법 | 참고 호흡 | 반드시 보존 | 기본 삭제 |
|---|---|---:|---|---|
| 훅 | 한 개의 미니 사건으로 약속 | 약 10~16초 | 위기·변화·작은 결말 | 맥락 없는 최고 장면 나열 |
| 설명·동기 | 한 절마다 새 정보 | 약 0.7~3초 | 게임 선택 이유·개인 조건 | 자기정정·진행어·반복 부연 |
| UI·설정 | 선택→결과만 빠르게 | 약 0.5~1.5초 | 이해에 필요한 상태 | 대기·커서 이동·중복 확인 |
| 탐색·이동 | 위치 변화→단서→결과 | 약 1~5초 | 공간 방향·새 위험 | 목적 없는 이동·같은 복도 |
| 공포 예열 | 새로운 소리·시각 단서가 생길 때만 유지 | 약 3~12초 | 원인 단서·인지 순간 | 변화 없는 정적 |
| 조우·비명 | 원인→인지→반응→결과 | 필요만큼 | 괴물·피격·비명·사망 관계 | 같은 반응의 반복 |
| 추격 | 발견·회피·막힘·탄원·생존의 milestone로 분할 | microbeat 약 2~8초 | 공간 변화·최고 반응·결과 | 반복 달리기·동일 실패 |
| 코미디 | setup→반응→punchline | 필요만큼 | 타격점과 짧은 여운 | punchline 뒤 긴 설명 |
| 반성·엔딩 | 변화와 아이러니를 문장 단위 보존 | 필요만큼 | “무서운 채 적응”의 반례·결말 | 같은 결론 재진술 |

빠른 편집은 초단컷의 총량이 아니라 **새 정보·상태 변화의 빈도**로 판단한다. 공포가 실제로 상승하는 동안 긴 컷은 실패가 아니다.

## 7. 실제 편집 순서

### 7A — 후보범위 해석

- 6단계 후보는 탐색 범위이며 컷이 아니다.
- 각 후보에 이야기 역할, 반드시 보존할 지점, 압축 가능 범위, 제거 가능 범위를 기록한다.
- 본편 기능 중복과 훅 적합성을 따로 평가한다.

### 7B — microbeat 설계

1. 후보범위의 오디오를 먼저 듣고 radio edit를 만든다.
2. 새 정보·행동·리액션·전환 단위로 microbeat를 나눈다.
3. 유지·압축·제거를 모두 결정표에 남긴다.
4. 화면으로 원인·공간·결과를 보강한다.
5. 기본 이야기 구간의 원본 시간 순서와 V2 인서트의 출처 시간을 감사한다.
6. J/L 컷, match-on-action, sound bridge와 원본 인서트를 검토한다.
7. 마지막에 VAD·파형으로 말·비명·웃음·호흡 경계를 검증한다.

명시적인 콜드오픈만 미래 사건 선공개를 허용한다. 콜드오픈이 끝나 본편으로 리셋된 뒤에는 미래 플레이를 설명용 B-roll로 섞지 않는다. 회고·평가 발화의 컷어웨이는 그 발화 시점보다 앞에서 이미 본 화면을 우선하며, 미래 화면이 꼭 필요하면 선공개 이유와 표시 방식을 별도로 승인받는다.

`synccheck`는 경계 위험만 제안한다. microbeat 기능, 유지·제거, 편집 템포를 결정하지 않는다.

### 7C — 캘리브레이션 XML

전체 편집 전에 한 XML에 다음 세 시퀀스만 만든다.

| 시퀀스 | 범위 | 검증할 편집 감각 |
|---|---|---|
| `CAL_A_INFO_UI` | 원본 `00:34.3~04:50.7` | 설명·UI 압축, 수동본보다 나은 오디오 연결 |
| `CAL_B_HORROR_REACTION` | C13 `50:15~51:10` | 인간형 발견→비명→사망의 이해와 여백 |
| `CAL_C_CHASE_COMEDY` | C09 `34:40~37:44` | 3:22 추격을 milestone로 압축하면서 웃음 보존 |

사용자 승인 항목:

- 빠르지만 의미가 따라오는가?
- 공포의 원인과 리액션이 모두 보이는가?
- 점프컷 오디오가 거슬리지 않는가?
- 긴 컷은 의도적으로 느껴지는가?
- 농담과 비명의 타격이 약해지지 않았는가?
- 수동본 복제가 아니라 더 나은 결과라고 느껴지는가?

사용자에게 보여주기 전 AI 선검증 항목:

- 훅을 제외한 기본 이야기 컷의 원본 시간이 의도한 방향으로 진행하는가?
- V2·J/L 인서트가 미래 플레이를 앞에 섞거나 거짓 인과를 만들지 않는가?
- 화면과 발화의 의미가 맞는가?
- 반복·저정보 구간과 명백한 리듬 결함을 AI가 먼저 제거했는가?
- 대표 프레임·SRT 경계·XML 구조 검사를 통과했는가?

사용자 승인은 기본 결함 탐지 단계가 아니다. AI 선검증을 통과한 뒤 취향·메시지·최종 리듬 판단만 요청한다.

기술적으로 열렸다는 사실과 편집 감각 승인은 별도다. Premiere에서 열려도 사용자 감각 승인이 없으면 `needs_user_decision`이다.

### 7D — 전체 확장

- 승인된 편집 문법을 모든 후보범위에 적용한다.
- 전체 microbeat 컷리스트와 새 XML을 생성한다.
- 전체 컷 흐름 승인 후에만 8단계로 전달한다.

## 8. 필수 산출물과 스키마

판단 근거와 XML 입력을 분리한다.

1. `microbeat_decisions.csv`: 유지·압축·제거 전체 판단.
2. `calibration_cutlist.csv`: 세 대표 시퀀스의 실제 XML 입력.
3. `editing_grammar.md`: 사용자 승인·거절을 실행 규칙으로 기록.
4. `full_cutlist.csv`: 승인 문법을 전체에 적용한 XML 입력.
5. 캘리브레이션 XML과 전체 XML: 서로 다른 새 파일명 사용.

`microbeat_decisions.csv` 최소 필드:

```text
order,candidate_id,micro_id,source_in,source_out,content_type,role,
viewer_delta,arousal,processing_load,silence_role,decision,
join_mode,boundary_basis,long_take_reason,reason_risk,status
```

- `viewer_delta`: 이 구간 뒤 시청자가 새로 알거나 느끼는 것.
- `decision`: `keep`, `compress`, `remove`.
- `join_mode`: `hard`, `J`, `L`, `sound_bridge`, `cutaway`.
- `boundary_basis`: `speech`, `action`, `sound`, `visual`, `event` 중 실제 근거.
- `long_take_reason`: 긴 컷일 때만 필수. 고정 초과 기준이 아니라 의도 기록용.

XML 확장 입력의 선택 필드:

```text
sequence,order,cut_id,start,end,label,note,source,
video_track,timeline_start,audio_mode,audio_start,audio_end
```

기존 `start,end,label` CSV는 계속 지원해야 한다.

## 9. 문서 개선 범위

다음 에이전트는 먼저 문서 계약을 수정한다.

필수:

1. `01_youtube_production_workflow.md`
   - 7A 후보범위 해석, 7B microbeat, 7C 캘리브레이션, 7D 전체 확장으로 변경.
   - 캘리브레이션 승인 전 전체 XML 생성 금지.
2. `skills/premiere-editing-export/SKILL.md`
   - 후보범위는 컷이 아님을 명시.
   - 새 입력·출력·게이트·중단 조건·다음 단계 전달물을 추가.
   - 실제 스크립트에 없는 `--guide` 예시 옵션을 제거.
   - CS6 예시는 MKV가 아니라 remux MP4를 사용.
3. `tools/README.md`
   - `synccheck`는 경계 보조 도구이며 편집 판단 도구가 아님을 한 줄 추가.

수정하지 않음:

- `PROJECT_RULES.md`, `PROJECT_BOOTSTRAP.md`, `AGENTS.md`, `CLAUDE.md`.
- `skills/SKILL_CONTRACT.md`: 현재 공통 계약으로 충분하며 단계 7 내용을 넣지 않는다.

## 10. XML 도구 개선 범위

대상: `skills/premiere-editing-export/scripts/make_premiere_xml.py`.

### 우선순위 P0 — 현재 실패 재발 방지

- microbeat CSV 한 행을 실제 컷 한 개로 변환.
- `sequence` 컬럼으로 한 XML 안 여러 시퀀스 생성.
- 기존 CLI와 기존 CSV 형식의 backward compatibility 유지.
- 전역 `_FILES_WRITTEN`을 빌드 컨텍스트로 옮겨 반복 build 누락 방지.
- source `out-in`과 timeline `end-start`를 같은 프레임 길이로 계산해 1프레임 불일치를 막는다.
- CS6 직접 export fixture에 맞춰 timeline clipitem의 `duration`은 원본 전체 프레임으로 기록하고, 실제 배치는 `start/end/in/out`으로 검증한다.
- 0프레임 컷, 소스 범위 밖, 중복 `cut_id`, 혼합 FPS/채널을 조용히 보정하지 말고 실패시킨다.

### 우선순위 P1 — 캘리브레이션 품질

- V1 기본 연결 시퀀스와 V2 cutaway/insert를 지원.
- `audio_start/end`로 영상과 다른 오디오 경계를 표현.
- J/L 오디오 겹침은 A1/A2, A3/A4처럼 stereo lane pair를 분리 배치.
- cutaway는 기본 `audio_mode=none`; 실제 시간과 인과를 바꾸는 인서트 금지.
- 시퀀스 duration은 모든 트랙의 최대 end로 계산.
- V2·추가 오디오 lane의 link는 실제 trackindex와 트랙별 clipindex를 기록한다. `sourcetrack.trackindex`는 원본 L/R 채널 번호와 혼동하지 않는다.

### 우선순위 P2 — 전체 확장

- 승인된 `editing_grammar.md`와 full cutlist를 기준으로 전체 XML 생성.
- `make_roughcut.py`는 확장 CSV·멀티트랙을 지원하지 않으므로 이번 작업에서 사용하지 않는다.

구조 성공은 CS6 import 성공을 증명하지 않는다. 캘리브레이션 XML을 실제 CS6에서 열기 전에는 `App-validated`로 쓰지 않는다.

## 11. 테스트와 완료 판정

새 테스트 권장: `tests/test_make_premiere_xml.py`(stdlib `unittest` 가능).

필수 자동 검증:

- 기존 headerless/headed CSV가 기존 1시퀀스·V1+A1/A2 구조를 유지한다.
- 세 calibration 그룹이 각각 타임라인 0에서 시작하는 세 시퀀스로 생성된다.
- 모든 clipitem ID·sequence ID가 유일하고 link target이 존재한다.
- 모든 컷에서 `out-in == end-start` 프레임이 성립하고 clipitem `duration`은 CS6 fixture의 source-duration 의미와 일치한다.
- J/L 오디오는 겹치지 않는 stereo lane pair에 배치된다.
- V2 cutaway가 정확한 timeline 위치에 있고 오디오가 비활성이다.
- source/timeline bounds, 혼합 FPS·채널, 중복 ID, 0프레임 컷은 명시 실패한다.
- xmeml v4, 원본 pathurl, masterclip, L/R 링크 구조를 검사한다.

완료 판정:

1. 문서·스킬·도구 변경 후 `tools\run_doccheck.bat` 통과.
2. 새·기존 XML 테스트 통과와 `git diff --check` 통과.
3. 캘리브레이션 XML `Parsed`·`Structure-validated`.
4. 사용자가 CS6에서 열어 `App-validated` 여부를 알려준다.
5. 사용자가 세 리듬 유형의 감각을 승인해야 7D로 진입한다.

## 12. 다음 에이전트 실행 순서

1. `SESSION_HANDOFF.md`와 이 문서를 끝까지 읽는다.
2. 현행 generator의 legacy 동작을 고정하는 회귀 테스트부터 작성한다.
3. 워크플로·스킬·tools README의 단계 계약을 수정하고 doccheck를 통과시킨다.
4. P0 기능과 테스트를 구현한다.
5. 세 구간의 `microbeat_decisions.csv`를 작성한다.
6. 필요할 때만 P1의 J/L·V2 기능을 구현한다. 효과를 위해 기능을 억지로 사용하지 않는다.
7. 새 파일명으로 캘리브레이션 XML을 생성·구조 검증한다.
8. 세 시퀀스의 시간 순서·화면 인과·경계를 AI가 먼저 자체 검수한다.
9. 전체 XML을 만들지 말고 사용자에게 자체검수 통과본의 감각 승인만 요청한다.
10. 승인 결과를 `editing_grammar.md`와 `SESSION_HANDOFF.md`에 기록한다.

## 13. Red-team — 실패 방지

- 2초 컷을 목표값으로 강제해 공포·추격을 과절단하지 않는다.
- 자동 무음 제거로 긴장·웃음·비명 뒤 여운을 지우지 않는다.
- J/L 컷과 인서트로 다른 시간의 화면을 덮어 거짓 인과를 만들지 않는다.
- 명시적 콜드오픈 뒤 본편 셋업에 미래 플레이 B-roll을 섞지 않는다.
- 사용자를 첫 번째 품질검사자로 사용하지 않는다. 시간 순서와 화면 인과는 AI가 먼저 전수 감사한다.
- 채팅 재구성 자막에 실제로 없던 문장을 창작하지 않는다.
- 수동 C11 훅이 기존 C09/C13 판정을 자동 대체한다고 해석하지 않는다.
- 캘리브레이션 가져오기 성공을 편집 감각 승인으로 말하지 않는다.
- 문제가 생겼을 때 실제 시퀀스 대신 프레임워크 개선으로 다시 도피하지 않는다.
- 같은 방향이 두 번 거절되면 `PROJECT_RULES.md`의 중단 규칙을 따른다.

## 14. 연구 근거

- YouTube 첫 30초·dips·spikes·top moments: https://support.google.com/youtube/answer/9314415?hl=ko
- YouTube는 보편적인 이상 길이보다 군더더기 제거와 유지율 검증을 권장: https://support.google.com/youtube/answer/16559651
- 빠른 편집과 고각성 콘텐츠의 결합은 처리 과부하 위험: https://doi.org/10.1080/08838159909364504
- 빠른 컷은 조건에 따라 주의·기억을 높일 수 있음: https://doi.org/10.1207/s15506878jobem4401_7
- 컷보다 의미 있는 행동 경계가 사건 분절에 중요: https://doi.org/10.3758/BF03213801
- 같은 사건 안의 연속성 편집이 이해를 도움: https://pmc.ncbi.nlm.nih.gov/articles/PMC3208769/
- Premiere J/L 컷: https://helpx.adobe.com/ca/premiere/desktop/edit-projects/trim-clips/perform-j-cuts-and-l-cuts.html
- Premiere CS6 공식 매뉴얼: https://helpx.adobe.com/pdf/cs6/premiere_pro_reference.pdf
