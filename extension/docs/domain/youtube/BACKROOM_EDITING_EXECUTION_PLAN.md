# 백룸 영상 편집 실행 계획

- 목적: 사용자가 반복해서 교정한 방향을 실제 편집 순서와 중단 게이트로 고정해, 전체 백룸 영상을 한 편의 자연스러운 Premiere sequence로 완성한다.
- 읽는 시점: 백룸 원본 분석, calibration, 전체 편집, XML 생성, Premiere 검수에 들어가기 전.
- 책임: 작업 에이전트가 사건·microbeat·경계·검증 근거를 유지하고, 사용자가 편집 문법과 최종 revision을 승인한다.
- 상태: **active 전체 설계**. 현재 활성 단계와 첫 다음 행동은 루트 `SESSION_HANDOFF.md`만 소유한다.
- 문서 분류: `overall-design`
- 관련 권위: `core/PROJECT_RULES.md`, `PROJECT_RULES.md`, `extension/rules/video-editing-*.md`, 사용자의 최신 교정.
- 대체 관계: `extension/reports/2026-08-26_BACKROOM_EDITING_RESUME_PLAN.md`은 historical 참고 자료이며 이 문서의 실행 지시를 대체하지 않는다.
- 종료 조건: 사용자 승인 revision이 `current` 또는 `approved`로 확정되고, 전체 재생·Premiere import·source lineage가 검증되면 completed 설계로 전환한다.

## 0. 사용자가 원하는 편집 방식

> 빠르지만 급하지 않고, 자연스럽지만 루즈하지 않으며, 촘촘하지만 과삭제하지 않는다. 시청자는 항상 왜 움직이는지, 어디로 이동했는지, 무엇이 달라졌는지 이해한다. 대사는 완결되고 화면을 인지할 여유 뒤에 들리며, 공포와 코미디의 타격에는 필요한 호흡을 남긴다.

이 작업의 핵심은 목표 길이에 맞춰 원본을 줄이는 것이 아니다. **사건의 인과와 감정 흐름을 먼저 잠근 뒤, 각 장면 안의 반복·맥락 없는 혼잣말·죽은 움직임만 microbeat 단위로 정리하는 자연스러운 서사형 microcut 편집**이다.

### 편집 판단 우선순위

1. 인과·공간·행동 anchor
2. 캐릭터의 첫 반응, 새 정보, 새 실패·학습, 공포·코미디 payoff
3. 기능 있는 정적·환경음과 화면 인지 시간
4. 반복 제거와 템포
5. 자연스러운 A/V 경계와 강조 기법
6. 기술 XML

충돌할 때는 하위 목적 때문에 상위 목적을 훼손하지 않는다. 특히 템포를 높인다는 이유로 원인·발견·접근·진입·결과를 삭제하지 않는다. 먼저 줄일 것은 중복 혼잣말, 같은 의미의 반복, 상태 변화 없는 이동·대기다.

### 촘촘함과 자연스러움의 뜻

- microcut은 모든 컷을 짧게 만드는 것이 아니라 **원본의 모든 microbeat를 촘촘히 판단하는 것**이다.
- 탐색·반복·설명은 조밀하게 압축하고, 발견·위협 인지·행동 전환·방 진입·규칙 확인·첫 반응은 의도적으로 필요한 호흡을 둔다.
- 컷 수를 늘리는 데서 멈추지 않는다. reveal timing, anticipation과 정적, reaction hold, action·movement·eyeline match, source-native J/L cut, cutaway, 제한적 reframing을 실제 결함에 맞게 선택한다.
- 기법의 개수는 품질 지표가 아니다. 각 기법은 해결한 결함과 제거했을 때 다시 생기는 문제를 설명할 수 있어야 한다.
- 사용자는 기본 연결 결함을 찾아내는 첫 검수자가 아니다. 에이전트가 전체를 먼저 검수하고 사용자는 분위기·캐릭터·연출의 창작 방향과 최종 revision을 판단한다.

### 이 작업이 아닌 것

- 목표 시간·압축률에 맞춘 속도전
- 사건 block을 통째로 들어내는 하이라이트 요약
- hard cut만 많이 배치한 기술적으로 짧은 결과
- 긴 rough block을 그대로 이어 붙인 통편집
- J/L cut이나 효과를 개수 채우기식으로 넣는 기법 시연
- XML import 성공을 편집 완성도나 사용자 승인으로 바꿔 부르는 것

추가 BGM·효과음·자막 그래픽·밈 연출의 종류와 강도는 아직 확정된 요구가 아니다. “컷편집만 하지 말라”는 교정은 우선 삭제 외의 리듬·반응·화면·음성 연결까지 설계하라는 뜻으로 적용하고, 비원본 창작 layer는 필요성과 득실을 제시한 뒤 별도 결정한다.

## 1. 결과 계약

### 원하는 결과

- 백룸 원본의 시작부터 결말까지 처음 보는 사람이 사건과 공간을 이해할 수 있는 **한 편의 연속 영상**을 만든다.
- Premiere에서 한 번에 가져오고 이어서 볼 수 있는 **단일 sequence XML 하나**를 전달한다.
- 원본에서 실제 확인된 공간 경험·규칙 학습·반응 변화가 하나의 이야기로 이어져야 한다.
- 결과 길이는 내용 판단의 결과다. 목표 시간, 평균 컷 길이, 사용 비율을 먼저 정하지 않는다.

### 허용 범위

- 승인된 원본 MP4·SRT·v18 XML을 목적에 맞게 읽고 분석한다.
- v18은 장면 위치와 전체 이야기 지도만 참고한다. 컷 경계와 승인 상태는 승계하지 않는다.
- 새 revision과 XML은 기존 결과를 덮어쓰지 않는 새 이름으로 만든다.
- 임시 frame·contact sheet·audio 분석·v2 payload·정상 속도 검수용 review proxy는 Git 제외 scratch에서만 사용하고 작업 종료 시 제거한다.

### 제외 범위

- 반려되거나 `use_prohibited`인 XML을 편집 source 또는 baseline으로 사용하지 않는다.
- 여러 독립 sequence, 장면별 XML 묶음, 전달용 timeline JSON을 만들지 않는다.
- 목표 시간을 맞추기 위한 일괄 축약, 고정 길이 microcut, 자막 cue만 보고 자르는 편집을 하지 않는다.
- 사용자 승인 없이 음악·효과음·자막 그래픽으로 원본에 없는 공포·추격·감정을 만들지 않는다.
- 기술 검증을 의미 검수·Premiere 검수·사용자 승인으로 높여 보고하지 않는다.

### 승인된 입력과 보호 경계

- `inputs/2026-06-30 00-23-03.mp4`: 원본 화면·음성.
- `inputs/2026-06-30 00-23-03.srt`: 발화 탐색 보조.
- `inputs/2026-06-30 00-23-03.full-edit-v18.xml`: source 위치와 CS6 구조 참고.
- 그 밖의 `inputs`, `outputs`, `extension/inputs`, `extension/outputs`는 exact 경로와 목적 승인 없이 열거하거나 읽지 않는다.

## 2. 편집 문법

### 2.1 작업 단위와 근거

- 작업 계층은 `source → chapter → scene → event → microbeat → clip`이다. scene은 연속된 공간·시간·목표 상태, event는 상태를 바꾸는 원인→행동→결과, microbeat는 한 가지 정보·행동·반응·화면 상태·발화 절, clip은 이를 구현한 실제 video/audio source 범위다. rough block은 clip이 아니다.
- scene/event 지도에는 `source in/out, 위치, 입구·출구 상태(goal/space/direction/threat/knowledge/emotion), 원인, 행동, 결과, visual/audio anchor, 선행 의존, must-keep, 위험, 확실성, 검수 상태`를 둔다.
- microbeat에는 `event, video/audio in/out, 기능, 상태 변화, keep/trim/remove/split 결정과 이유, 앞뒤 의존, 사용 가능한 source handle, 경계 위험, clip owner, 검수 상태`를 둔다.
- 관측 사실·해석·편집 결정을 분리하고 근거 채널을 `video_seen / audio_heard / srt_hint / v18_locator`로 기록한다. SRT·v18·contact sheet만으로 사건이나 대사를 confirmed로 올리지 않는다.
- 전체 source 범위는 `functional / repetition-idle / uncertain / technical` 중 하나로 coverage한다. `uncertain`은 정상 속도 A/V 재확인 전 편집하지 않는다.

### 2.2 한 편의 영상과 시간 해석

- 본편은 원본 시간 순서를 따른다. 콜드 오픈을 쓰더라도 훅으로 명시하고 본편의 인과 순서를 바꾸지 않는다.
- 과거 교정된 `9초 42 부근`을 `9분 42초`로 해석하지 않는다. 모든 시간 지시는 `source/timeline`, `시:분:초.밀리초 또는 프레임`, `점/범위`를 먼저 기록한다.
- 머리를 잘라낸 뒤 시작하는 오프닝 장면은 자연스러운 타격점이나 완료 지점까지 보여준다. 새 timeline 약 13초에서 오프닝을 강제로 끊지 않는다.
- calibration이나 대표 구간을 전체 편집 결과처럼 보고하지 않는다.

### 2.3 사건·공간·대사의 인과

각 컷 전후에는 다음 상태를 확인한다.

`공간 / 진행 방향 / 현재 목표 / 위협 인지 / 현재 행동 / 새로 안 정보 / 감정 / 발화가 전제하는 사실`

값이 바뀌면 변화의 원인, 실제 행동, 이동 경로, 관객이 먼저 알아야 할 정보를 source 화면에서 찾는다. 하나라도 설명할 수 없으면 컷을 더 줄이지 않고 원인·이동·행동 anchor를 복원한다.

모든 사건은 다음 다섯 항목을 source anchor로 가진다.

1. 상황
2. 원인 또는 발견
3. 행동 또는 시도
4. 결과와 반응
5. 다음 상태

다음 기능은 대사가 없어도 삭제하지 않는다.

- 괴물을 처음 화면으로 인지하는 순간
- 위험을 확인하고 몸을 돌려 달아나는 행동
- 다음 stage·방·출구를 발견하고 접근하는 과정
- 문을 열고 들어가거나 나오는 행동
- 괴물이 아직 가까이 있음을 다시 확인하는 장면
- 방으로 퇴각하고 문을 닫아 차단하는 행동
- 차단 결과를 보고 규칙을 이해하는 순간

`도망간다`, `망했다`, `괴물을 만났다`, `문을 닫으면 못 들어온다` 같은 반응과 결론은 그 원인 화면보다 먼저 나오거나 원인 없이 단독으로 남을 수 없다.

### 2.4 템포와 microcut

긴 후보 구간은 `정보 / 행동 / 반응 / 화면 상태 / 자연스러운 발화 절`로 다시 나눈 뒤 다음 네 가지 중 하나로 판정한다.

| 판정 | 적용 조건 |
|---|---|
| 유지 | 발견·인지·방향 전환·접근·진입·시도 결과·새 규칙·첫 반응·감정 변화·공포/코미디 타격처럼 이후 이해에 필요한 기능이 있다. 무음이어도 유지한다. |
| 축소 | 기능은 있지만 같은 이동·설명·반응이 길게 반복된다. 첫 인지→실질 변화→결과를 남기고 내부 반복만 microcut한다. |
| 제거 | 새 정보·상태 변화·후속 반응의 원인·감정 누적·회수가 모두 없고, 삭제 전후의 행동 방향과 발화가 자연스럽다. |
| 분할 | 한 source 구간 안에 보존할 기능과 반복이 섞여 있다. 긴 구간을 통째 유지하거나 삭제하지 않고 내부 microbeat를 나눈다. |

앞뒤 맥락과 무관한 혼잣말, 같은 의미의 반복, 진행 없는 이동·대기부터 강하게 줄인다. 반대로 공간 파악, 위협 확인, 문 조작, 긴장 누적, 회복에 기능이 있는 무음은 필요한 만큼 유지한다. 길다는 이유만으로 자르지 않고, 짧다는 이유만으로 살리지 않는다.

### 2.5 발화와 화면 경계

- 말을 시작하는 장면은 화면 변화와 첫 음절을 같은 frame에 붙이지 않는다. 원본의 숨·환경음·게임음으로 장면 인지 여유를 확보한다.
- 음절·단어·조사·미완성 생각을 남기지 않는다. SRT는 위치 탐색용이며 최종 경계는 실제 청취로 결정한다.
- 같은 공간에서 화면이 탁탁 튀면 split edit부터 넣지 않는다. 먼저 동작·이동 방향·시선·밝기·공간 위치를 확인한다.
- 화면 점프는 source가 제공하는 action match, movement match, eyeline match, cutaway, 연결 동작, 더 긴 원테이크 중 가장 작은 수단으로 해결한다.
- J-cut은 다음 발화·환경음을 먼저 들려 장면 진입을 준비할 때, L-cut은 이전 반응·환경음을 다음 화면까지 이어 의미와 공간을 연결할 때만 사용한다.
- split edit의 개수나 비율을 목표로 삼지 않는다. 문제를 해결하지 못하는 기법은 사용하지 않는다.

### 2.6 컷 편집 이후의 연출

컷 수를 늘리는 것만 편집으로 보지 않는다. 인과가 확정된 뒤 다음을 장면별로 비교한다.

- 반응을 살리는 hold와 타격 직후의 짧은 여운
- 긴장 누적을 위한 의도적 정적과 환경음
- 같은 행동을 잇는 movement/action match
- 정보 화면과 반응 음성을 엇갈리게 배치하는 J/L cut
- 원본 안의 시선 전환·밝기 변화·문·복도·계단을 연결 재료로 사용하는 cutaway
- 실제로 의미를 강조하고 Premiere CS6 XML로 재현 가능한 경우에만 제한적인 punch-in 또는 reframing

추가 음악·효과음·그래픽은 별도 창작 layer다. 필요한 장면, 목적, 원본 사실과의 차이를 제시하고 사용자 결정 뒤 적용한다.

## 3. 이야기 스파인 설계 원칙

전편 근거를 확보하기 전에는 이야기 스파인을 확정하지 않는다. 현재의 `진입→탐색→위협과 실패→규칙 학습→적응` 구상은 탐색 가설일 뿐이다. 단계 1의 전편 로컬 index·가속 discovery와 위험 기반 정상 속도 A/V 검수, 사건 지도를 근거로 실제 변화가 있는 장만 골라 단계 2에서 구성안을 제시하며, 근거가 없는 장은 폐기한다.

## 4. 단계별 실행 계획

한 번에 활성 단계는 하나다. 각 단계의 필수 게이트가 `pass`가 아니면 다음 단계로 넘어가지 않는다.

### 단계 0 — 미학 계약과 검수 능력

- 결과 형식·편집 미학·금지 사항만 확정한다. 원본 확인 전 이야기 스파인은 승인받지 않는다.
- `재생기 / v2-equivalent proxy renderer / 실제 A/V reviewer / proxy-editorial fingerprint 결속 / Premiere operator·profile` 다섯 능력을 각각 판정한다.
- 비보호 A/V fixture로 proxy의 clip range·split A/V·source handle 재현을 확인하고, 실제 reviewer가 metadata 도움 없이 원인 누락·동작 jump·발화 절단 결함을 정상 속도에서 찾는지 시험한다.
- 정지 frame·SRT·ASR·RMS·decode·ffplay 종료 코드는 실제 보고 들은 검수의 대체 증거가 아니다.

**통과:** 사용자 교정 반영, 다섯 능력 pass, reviewer·method·evidence 기록. 하나라도 `not_run`이면 편집을 시작하지 않는다.

### 단계 1 — 전편 로컬 인덱싱과 위험 기반 분석

- 먼저 exact source의 hash·duration·실측 fps/timebase·audio track/sample rate를 기록하고 source 좌표와 timeline 좌표를 분리한다.
- FFprobe, SRT·v18 locator, scene·motion·luma, silence·RMS로 전편 time-coded index를 만들고 가속 discovery sweep으로 모든 source interval을 coverage한다. 자동 index는 위치·위험 후보일 뿐 의미 확인이 아니다.
- `채택 후보+양쪽 handle / 원인·행동·결과와 공간 bridge / 발화 경계 / 동일 공간 jump 위험 / index 충돌·불확실 구간`만 실제 A/V를 1배속으로 확인한다.
- 자동 근거가 충돌하거나 상태 변화·원인을 설명하지 못하면 `uncertain`으로 올려 1배속 확인하고, SRT·v18은 위치 보조로만 사용해 scene/event 지도와 `상황→원인→행동→결과→다음 상태`를 source 좌표에 묶는다.
- 결과·반응마다 실제 선행 원인과 장면 간 entry/exit bridge를 연결한다. 정상 속도로 보지 않은 저위험 제외 구간은 semantic-confirmed라고 부르지 않는다.

**통과:** 모든 source interval의 index coverage, review set의 실제 A/V 확인, 미해결 `uncertain` 0, 모든 결과·반응의 선행 원인과 장면 인접 상태 설명 가능.

### 단계 2 — 구성·보존 anchor·대표 장

- 원본 근거로 이야기 스파인, 장별 기능, 필수 anchor, 제거할 반복을 제안한다. 목표 길이와 컷 수는 예산으로 두지 않는다.
- `오프닝 / 동일 공간 jump / 공간 전환 / 위협 인과 / 혼잣말 / 발화 lead / 규칙 학습` 위험표로 대표 calibration 장을 고른다. `36:22.380~38:23.500`은 후보일 뿐이다.

**통과:** 구성의 인과와 대표 장의 위험 커버리지를 설명하고, 실제 창작 갈림길만 사용자에게 판단받는다.

### 단계 3 — 편집 문법 증명

- 대표 연속 장에서 anchor를 먼저 잠그고 반복만 microcut한 exact review proxy를 1배속 A/B 검수한다.
- 부족한 위험은 내부 boundary probe로 보완하되 여러 전달 sequence/XML로 만들지 않는다.
- proxy가 v2의 clip range·A/V 경계·J/L handle·지원 연출을 동일하게 재현하고 같은 editorial fingerprint에 결속되는지 확인한다. 재현하지 못하는 기법은 사용 전에 차단한다.
- calibration은 전체 결과·source·baseline이 아니다. 전체 편집은 원본과 전편 지도에서 새로 만든다.

**통과:** 의미 검수, Premiere import·재생, 사용자 방향 승인을 각각 증명한다. 미승인이면 확장하지 않는다.

### 단계 4 — 단일 sequence 전체 편집

1. **causal skeleton:** 필수 원인·행동·결과와 공간 bridge를 잠근다.
2. **local density:** 모든 장면을 microbeat로 나누고 반복·무관 혼잣말·진행 없는 이동만 줄인다.
3. **boundary continuity:** 발화 lead/tail, 동작·시선·방향·밝기, split A/V와 source handle을 검수한다.
4. **dramatic rhythm:** anticipation→reveal→reaction→payoff와 공포→안도→코미디→재긴장의 호흡을 조정한다.
5. **global redundancy:** 전편의 중복 탐색·설명·반응을 줄이고 escalation과 회수를 확인한다.

각 chapter 조립 직후 장면 내부와 양쪽 인접 경계를 A/B 검수하고, 전편 조립 뒤 chapter 전환을 별도로 본다. 뒤 pass가 앞 pass의 anchor·positive lock을 깨면 즉시 실패다.

**통과:** 원인 없는 반응, 공간 순간이동, 긴 통편집, 발화 파편, 동일 공간 화면 튐이 0개다.

### 단계 5 — 에이전트 QA·XML·승인

- 같은 A/V-capable reviewer가 최신 exact timeline을 처음부터 끝까지 건너뛰지 않고 1배속으로 한 번 재생하며 `causal_space / tempo_repetition / av_boundary`를 각각 기록한다. 세 관점은 별도 evidence record이며 별도 전편 재생이 아니다.
- 새로 만들거나 바꾼 모든 cut boundary는 정상 속도 전후 문맥 A/B로 검수한다. 바뀌지 않은 경계 근거는 source 범위·A/V edge·인접 상태가 동일하다는 결정론적 diff가 있을 때만 승계한다.
- 각 결함은 `source anchor + event/microbeat + boundary ID + 증상 + 원인 + severity`로 기록한다. 경계 수정은 해당 window와 양쪽 인접 문맥, scene 수정은 scene과 인접 전환, chapter 수정은 chapter와 인접 전환, 사건 순서·스파인·전역 리듬 수정은 전편을 재검수한다.
- 한 frame/sample이라도 editorial 내용이 바뀌면 기존 canonical 의미 pass와 revision 승인은 무효이며 영향 범위 검수는 중간 QA로만 기록한다. 편집이 안정된 최신 fingerprint에서 최종 전편 1배속 재생과 세 관점 기록을 다시 결속하며, 첫 QA 뒤 mutation이 없으면 그 재생이 최종 재생을 겸한다. pending P0/P1 결함이 하나라도 있으면 사용자에게 넘기지 않는다.
- proxy→v2 timeline→XML→Premiere sequence의 clip mapping과 editorial identity가 같은지 확인한다.
- 최신 전체 재생과 세 관점 통과 뒤 단일 XML을 만들고 구조·media·lineage를 검증한 다음 Premiere import·single sequence·online media·track/link·duration·gap·전체 재생을 확인한다.
- 사용자에게 추천 revision 하나를 제시하고, 승인된 exact revision만 `current` 또는 `approved`로 승격한다.

**통과:** 실제 A/V reviewer, 기술 검증, Premiere 검수, 사용자 전체 승인이 같은 revision에 결속된다.

## 5. 기법 선택표

| 관측된 문제 | 우선 수단 | 금지되는 오용 |
|---|---|---|
| 새 화면과 첫 음절이 동시에 튐 | source-native lead, 필요 시 J-cut | 임의 무음 gap, 고정 pre-roll |
| 이전 대사가 화면 전환 뒤까지 의미가 있음 | L-cut | 모든 컷에 일괄 적용 |
| 같은 공간에서 화면이 튐 | action/movement/eyeline match, cutaway, 연결 동작, 더 긴 take | split edit만 넣고 화면 문제를 해결했다고 주장 |
| 다음 stage·방으로 순간이동 | 발견·접근·진입·도착 anchor 복원 | 설명 대사만 추가 |
| 반복 혼잣말로 늘어짐 | 완결된 절 단위 microcut, 첫 반응과 결과 보존 | 자막 cue 전체 삭제, 목표 길이 맞추기 |
| 추격이 너무 길거나 너무 짧음 | 새 위험·경로 변화·스태미나·도착 기능별 재분할 | 무음·이동을 일괄 삭제 또는 통째 유지 |
| 공포가 단조로움 | 정적·안도·코미디 hold·재긴장 순서 조정 | 원본에 없는 효과로 감정 조작 |

## 6. 사용자 교정 회귀 목록

아래 과거 timeline 시각은 결함 유형의 근거이지 새 revision의 직접 컷 지시가 아니다. 새 편집에서는 원본 source anchor로 다시 찾아 결속한다.
각 항목은 `resolved / approved_defer / unreproduced` 중 하나로 닫고 pending을 0으로 만든다. 뒤 두 상태는 `approved_by=user`가 필수다.

다음 항목은 새 revision마다 source anchor 기준으로 확인한다.

- 오프닝이 타격점 전에 끊기지 않는다.
- 괴물을 보여주기 전에 도망가거나 `망했다`는 반응이 나오지 않는다.
- 직전 장면과 같은 괴물을 다시 처음 만나는 것처럼 중복 연결하지 않는다.
- 다음 stage로 바뀌기 전에 전환 원인과 도착을 보여준다.
- 출구방·안전방은 발견하고 들어가는 과정이 남아 있다.
- 괴물을 아직 보지 않았는데 이미 만난 것처럼 말하지 않는다.
- 문을 열고 나가려 함→가까운 괴물 확인→방으로 후퇴→문 차단→규칙 이해가 순서대로 남아 있다.
- 말 시작을 너무 타이트하게 자르지 않고 장면 인지와 첫 음절에 source-native 여유가 있다.
- 노란 벽 등 같은 공간의 연속 컷에서 이동 방향·시선·밝기가 튀지 않는다.
- 흐름을 빠르게 만든다는 이유로 사건·대사·공간 정보를 마구 삭제하지 않는다.
- 자연스러운 편집이라는 positive lock을 유지하면서 반복과 죽은 구간만 줄인다.

## 7. revision과 산출물 상태

- revision 상태는 `working_candidate / current / approved / use_prohibited / historical`만 사용한다. 현재 대상과 반려 목록은 handoff가 소유한다.
- `current`는 사용자가 exact entire revision을 후속 delta의 활성 baseline으로 채택한 상태, `approved`는 사용자가 exact entire revision을 편집 완료본으로 확정한 상태다.
- `final`은 revision 상태가 아니라 approved revision의 semantic·technical·Premiere·delivery gate가 끝난 완료 milestone이다.
- 반려 revision은 `use_prohibited`, 대체 revision은 `historical`로 동결하고 새 편집 source로 쓰지 않는다.
- calibration XML은 이름과 보고에서 전체 편집 결과와 명확히 구분한다.
- XML 생성은 `generated/parsed/structure-validated/tool-validated/media-validated/semantic/app/user` 상태를 각각 기록한다.
- 정상 속도 의미 검수 전에는 편집 품질 점수를 매기지 않는다.
- 최종 전달 폴더에는 사용자가 요청한 XML만 남기고 내부 v2 JSON·contact sheet·WAV·보고서를 추가하지 않는다.

## 8. 중단 조건과 사용자 판단 요청

무관 혼잣말 제거, 최소 causal bridge 복원, source-native handle 선택, action/movement/eyeline match와 cutaway 비교는 에이전트가 책임지고 A/B 검증한다. 사용자가 기본 결함을 하나씩 찾아 지시하게 만들지 않는다.

다음 조건에서는 추측으로 진행하지 않는다.

- 시간값의 좌표계·단위 해석이 결과를 크게 바꾼다.
- 원인 anchor와 템포 압축 중 어느 쪽을 택해도 중요한 기능이 사라진다.
- 원본만으로 화면 점프를 해결할 연결 재료가 없다.
- 추가 음악·효과음·그래픽·reframing이 필요하지만 창작 범위가 정해지지 않았다.
- 실제 A/V 정상 속도 검수가 불가능하다.
- review proxy가 v2 또는 Premiere sequence와 동등하지 않다.
- Premiere import 또는 전체 재생이 실패한다.
- calibration 문법이 사용자 승인을 받지 못했다.

질문은 두 선택 모두 중요한 기능을 잃는 실제 창작 갈림길, 비원본 음악·효과·그래픽, 결과를 바꾸는 시간 지시 모호성, 실제 A/V 정상 속도 검수 불가에 한정한다. 사용자에게 요청할 때는 `정확한 source 구간 / 확인된 문제 / 선택지별 얻는 것과 잃는 것 / 권장안`을 함께 제시한다.

## 9. 완료 정의

다음이 모두 충족돼야 백룸 편집 완료다.

1. 한 편의 단일 sequence XML이다.
2. 전체 원본의 이야기와 공간 흐름이 연결된다.
3. 사용자 교정 회귀 목록을 모두 통과한다.
4. 정상 속도 전체 A/V 의미 검수를 통과한다.
5. Premiere import와 전체 재생을 통과한다.
6. exact revision 전체를 사용자가 승인한다.
7. source lineage와 승인 상태가 보존된다.

그 전에는 `working_candidate`이며, 기술 검증 성공만으로 완성본·추천본·승인본이라고 보고하지 않는다.
