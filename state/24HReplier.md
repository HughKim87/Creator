# 24HReplier 작업 상태

- 목적: 공개 YouTube 영상의 제목·자막·기존 댓글을 참고해 자연스러운 댓글을 제안하고, 사용자가 검토한 문구를 수동 게시하는 Windows 앱.
- 읽는 순서: core/PROJECT_RULES.md → PROJECT_RULES.md → SESSION_HANDOFF.md → 이 문서.
- 상태 정본: codex/24HReplier의 이 문서 하나. SESSION_HANDOFF.md는 공통 안내판이므로 수정하지 않는다.
- 워크트리: D:/AI Agent/GitHub/Creator-24HReplier. 현재 셸의 Creator main과 혼동하지 않는다.
- handoff mode: same-workspace. 소스 보존 커밋과 별개로 로컬 모델·Git 제외 실험 데이터에 의존한다.
- 갱신일: 2026-10-20. 생성 전용 입력·프롬프트 분석과 짧은 실험 결과를 반영했다. 앱 적용 전이며 품질은 미해결이다.

## 현재 단계

### 세션 종료 개선 진행

필수안 E1·E2 구현과 단계별 커밋을 승인받았다. E3은 보류한다. 활성 설계: extension/work/24hreplier-session-close-design.md. E1 실제 예시 포함·기록/전송 일치의 모의 경계 검사를 통과했으며 현재 활성 단계는 E2다. 실제 모델 생성·추가 평가 호출·삭제·초기화·push는 제외한다. 이전 생성 전용 범위보다 E2의 승인된 근거 공유 수정만 확대됐으며 앱의 자연스러운 최종 품질은 미해결이다.

### 현재 목표와 작업 경계

핵심 미해결 사항은 댓글 초안의 품질이다. 영상에 실제 나온 내용을 이해하고 구경한 사람이 짧게 반응하는 문장이 필요하다. 자막 바꿔쓰기, 근거 없는 사건·인물·감정 추측, 반복되는 칭찬이나 억지 비판은 원하는 결과가 아니다. 아재개그·아재 말투는 필수가 아니다. 특정 단어를 계속 금지하거나 평가 호출을 늘리는 방식보다 작은 모델이 이해하기 쉬운 입력과 생성 지침을 먼저 개선한다.

현재 작업 범위는 **같은 영상의 생성 프롬프트·입력 구성만 별도로 시험하는 것**이다. 앱·평가 로직 적용 전 초안 자체를 보여주는 단계다. 최신 실험도 품질 해결이나 사용자 승인을 얻은 상태가 아니다. 다음 세션은 기존 결과를 먼저 분석해야 하며 자동으로 장시간 재시험하거나 앱을 재빌드하지 않는다. 저장장치·하드웨어 설명이나 추가 검사 로직으로 논점을 옮기지 않는다.

### 최신 생성 전용 확인점 — v10/v11

- 사용자 지시에 따라 기존 실제 입력·출력을 먼저 분석하고, 같은 영상의 생성 부분만 시험했다. 앱·평가 로직·운영 실행 파일은 수정하지 않았다. 금지 단어·검사를 추가하지 않았고 파일 삭제·이동을 하지 않았으며 해당 실험 당시 commit/push도 하지 않았다.
- v8/v9 입력은 채팅을 해도 되는지 묻고 춤추는 곳이라는 말을 듣는 중간 흐름을 생략했다. 다른 상황의 예시 3쌍은 난처함·공감 반응에 치우쳐 있어 일반적인 ‘대화가 막막함’으로 수렴하는 데 영향을 줬을 가능성이 있다. 예시 영향은 별도 대조로 입증하지 않았다.
- 운영 SceneWriter의 rawSources는 메시지에 쓰이지 않는다. whole_context는 선택된 writing_fact/writing_quote들의 배열이며 전체 연속 자막이 아니다. ClearReactionPoints는 종결형 문장 선택과 일부 일반 조건 치환을 하므로 발화의 연결이 빠질 수 있다. FocusedGrounding은 전달된 fact만 보도록 지시한다. 이번에는 해당 소스를 읽기만 했다.
- v10: 편향된 예시를 제거하고, 발언→다음 발언·행동의 흐름을 읽고 친구와 같이 보는 시청자처럼 한 대목에 반응하도록 안내했다. 제목은 표제로 구분하고 연속 자막 233239~262560ms를 보존했다. 동일 프롬프트·seed·생성 설정으로 자막만/사람의 문맥 설명 추가를 각 1회 비교했다. 기존 v8/v9 대비 여러 요소가 함께 달라져 요소별 효과는 분리할 수 없다.
- v10 자막만 원문: `와, 갑자기 분위기 확 바뀌네. 춤추는 거 말고 다른 거 시도해봐!` (55.415초).
- v10 사람 문맥+동일 자막 원문: `와, 갑자기 분위기 확 바뀌는데 춤추는 거 추천! ㅋㅋㅋ` (0.225초).
- 두 결과 모두 장면 반응보다 조언·추천에 가깝다. 사람 문맥 추가만으로 품질이 나아졌다고 판단하지 않았다. 시간은 준비를 포함한 도구 기록이며 두 번째 수치를 앱 속도나 반복 가능한 성능으로 해석하지 않는다.
- v11: 자막 시작을 243159ms로 좁히고 사람이 고른 ‘인사→대화 방법 질문→다시 인사’ 반응 지점을 명시했다. 60초 제한으로 취소되어 raw는 null이며 새 초안은 없다. 이 가이드의 효과는 미검증이다. 추가 반복은 하지 않았다.
- 실제 입력·요청: extension/data/replier-prompt-probe/generation-context-v10-requests.json, generation-context-v11-requests.json. 해당 파일에 전송한 messages와 설정이 있다. 실제 응답·시간·오류: 같은 폴더의 generation-context-v10-results.json, generation-context-v11-results.json. 후편집·모델 평가 없음.
- 생성 도구: extension/tests/replier_generation_context_v10_probe.cs, extension/tests/replier_generation_focus_v11_probe.cs. 기존 Comments.TestOnly.cs와 별도 포트 11440·소유 Windows Job을 사용했다. 운영 앱을 재빌드하지 않고 별도 probe 실행 파일만 컴파일했다.
- 검증: generation-context-v10-v11-verification.json. 운영 소스 32개와 앱 exe의 전후 SHA256 동일, 실험 포트 종료 확인. 자동 장면 추출·다른 영상·앱 적용·자연스러운 최종 품질은 검증하지 않았다.

### 이전 생성 전용 실험의 실제 체크포인트 — v8/v9

- 대상: vDWt01ul5F0, 「잼민이 기강 잡기」, 김재원의 즐거운 세상.
- 입력 정본: extension/data/replier/content/vDWt01ul5F0.json.
- 현재 실험 도구: extension/tests/replier_generation_single_draft_probe.cs, extension/tests/replier_generation_single_repeat_probe.cs.
- 실제 요청·출력: extension/data/replier-prompt-probe/generation-only-v8.json, extension/data/replier-prompt-probe/generation-only-v9.json. messages_sent를 확인할 수 있다.
- Gemma만 사용한다. system + 다른 상황의 예시 3쌍 + 현재 입력, 총 8메시지. 댓글 1개 요청, 후편집·모델 평가 없음. 컨텍스트 2048, batch 128, predict 120, temperature 0.2. Qwen의 품질 비교 결과는 확보하지 못했다.
- 작성 입력은 실제 자막을 사람이 대조해 정리한 클럽 인사 장면이다. 인사를 해도 대답이 없다고 말하고, 대화 방법을 물은 뒤 마이크 이야기를 듣고 다시 인사하는 흐름과 해당 실제 대사를 준다. 자동으로 장면을 정확히 요약한 성과가 아니다. 제목은 결과 메타데이터에 있으나 이 최종 작성 요청에는 넣지 않았다.

저장된 원문은 다음과 같다. 수정·선별한 문장으로 대체하지 않는다.

| 자료 | 초안 원문 | 도구 기록 시간 |
|---|---|---|
| v8 | 저 상황에서 어떻게 대화 시작해야 할지 막막함 ㅋㅋㅋㅋ | 10.848초 |
| v9 | 저 상황에서 어떻게 대화를 시작해야 할지 막막함ㅋㅋ | 109.868초 |
| v9 | 저 상황에서 어떻게 대화를 이어가야 할지 고민되네요ㅋㅋ | 12.114초 |

세 문장은 비슷하고 두루뭉술하다. 장면과 느슨하게 연결됐다는 것만으로 자연스러운 최종 품질을 입증하지 못한다. 시간은 도구 실행 기록이며 앱 전체 시간이나 순수 토큰 생성 시간으로 바꾸어 보고하지 않는다. 5~10초 목표를 달성하지 못했다.

실험은 extension/.runtime/replier-checks/generation-probe/Comments.TestOnly.cs라는 파생 사본과 별도 포트 11440을 사용한다. 운영 Comments.cs와 앱 실행 파일은 이 실험으로 변경하지 않았다. 소유 Windows Job으로 테스트 서버·runner를 정리하는 도구다. 이전 PowerShell v3/v4 결과는 당시 예시를 저장만 하고 실제 요청에 보내지 않았으므로 few-shot 효과의 비교 근거로 사용하지 않는다. 해당 스크립트는 E1에서 실제 요청 조립·사전 기록을 공유하도록 수정했으며 재실행 출력은 repaired 파일로 분리한다. 그 외 이전 probe는 과거 비교 자료이며 현재의 권장 실행 절차가 아니다.

### 운영 앱과 실험의 차이

운영 경로는 Evidence → Qwen ScenePlanner → ClearReactionPoints → 모델별 SceneWriter → Gemma ScenePolisher → 두 모델의 말투·근거·관계 평가 → Qwen 최종 말투 선택이다. 각 모델 최대 5개를 목표로 작성하고 최종 1개를 표시한다. 최근 생성 전용 프롬프트는 이 경로에 반영되지 않았다.

현재 원인 분석에서 이어갈 부분:

- SceneWriter는 질문·관찰·대조·공감·응수 등의 고정 슬롯과 짧은 길이 지시로 여러 후보를 각각 요청한다. 해당 장면에 필요 없는 질문·대조를 만들 가능성이 있다.
- 운영 작성의 실제 전달 입력은 선택 사실·인용과 가린 제목 중심이다. rawSources 변수를 가져온 것과 실제 모델 메시지에 전체 자막이 포함되는 것은 다르다. 이전 상태의 ‘전체 발췌를 작성 모델에 제공한다’는 설명을 그대로 믿지 말고 메시지 조립 코드를 기준으로 판단한다.
- 기존 댓글은 주로 말투 정보로 축소돼 전달된다. 사람들의 실제 반응 소재가 작성에 충분히 연결되지 않으며, 반대로 원문 댓글 전체를 넣으면 다른 시점·인물·사연이 섞일 수 있다. 기존 댓글은 영상 사실의 근거가 아니다.
- 작성 때 받은 복수 사실 중 하나를 사용했더라도 FocusedGrounding이 후보에 배정된 한 사실만 대조하면 생성·평가의 근거 범위가 어긋난다.
- ScenePolisher는 영상 없이 문장만 따로 편집한다. 의미 보존과 자연스러움을 보장하지 않는다.
- 짧은 초안보다 후보별 검사·재요청·후편집·최종 선택에 많은 호출이 필요하다. 합산 평가가 끝나야 화면에 보여 오래 빈 화면으로 보일 수 있다. 추가 평가를 붙여 초안 결함을 해결하려 하지 않는다.
- ScenePlanner의 분류와 ClearReactionPoints의 완결형 문장 추출은 실제 장면 이해와 다르다. 자동 자막의 종결형이나 단어만으로 명확한 사실이라고 간주하면 잘못된 해석이 전파된다.

### 기존 앱 기능과 실행 위치

- 실행 파일: extension/.runtime/replier-desktop/24HReplier.exe.
- 시작: scripts/Start-24HReplier.cmd. 빌드: scripts/Build-24HReplier.ps1.
- .NET Framework C#5 WinForms. 직접 컴파일하는 검사에는 System.Security.dll 참조가 필요하다.
- 로컬 모델: 기존 Ollama v0.40.4, gemma4:e2b-it-qat, qwen3.5:4b. 런타임 extension/.runtime/replier-llm, 프로필 extension/config/replier-llm-local.json.
- 앱 전용 서버는 localhost:11439. 앱 시작 시 Gemma→Qwen을 준비하고 실행 중 keep_alive=-1로 유지하는 구현이 남아 있다. 종료 시 소유 Windows Job을 닫고 타 프로세스 소유 서버는 종료하지 않는다. 이번 실험에서 상주 기능을 제거하지 않았다.
- 준비 완료를 기다린 뒤 생성 타이머·180초 제한을 시작한다. 준비 시간은 별도 표시하며 취소 시 재시도 버튼을 복구한다. 호출당 60초·모델 작성 75초 제한도 남아 있다.
- 같은 영상·제목·자막의 세션 캐시를 사용한다. 평가만 실패하면 기존 후보 재평가가 가능하다. 실패·취소 시 기존 검증 댓글이 있으면 유지하며 미검증 새 결과를 정상 최종 댓글로 표시하지 않는다. 이전 작업의 늦은 응답은 취소·버전으로 차단한다.
- 검색 방식: 직접 검색 / 실제 YouTube 자동완성에서 검색어 하나 무작위 선택 / 채널의 실제 제목·태그에서 게임을 추려 하나 무작위 선택 / 한국 게임 인급동. 공통 목록을 사용한다.
- 카테고리·기간·추천 종류를 로컬에 복원한다. 직접 입력 검색어·채널 링크는 저장하지 않는다. 기간은 24시간/1주/1개월/전체, 초기 기본 1주. 게임(20)이 기본이고 인급동은 게임만 지원한다.
- 한국어 제목·자막·원어 근거, 카테고리·기간을 확인한다. 제작자 국적 판정은 아니다. 후보 최대 30개 중 자막 확보 최대 10개를 최종 댓글 수 내림차순으로 표시한다. 수집 단계의 조회수 우선 탐색과 최종 표시 정렬은 다르다.
- 영상 목록: 제목/채널/길이/조회수/업로드/댓글 수. 숫자 열 정렬, 두 목록 독립 스크롤·분할선, 영상 열기, 경과 시간, 댓글 재생성·재평가, 디버깅 복사를 구현했다.
- 영상 중복 제외는 모든 수집 경로에서 제거했다. 기존 이력 파일은 보존하며 자동 검색어 이력·자막 캐시·후보 문장 중복 검사와 구분한다.
- 적합도는 Gemma 50 + Qwen 50의 합계다. 사실 정확도 확률이 아니며 고점이 자연스러움을 보증하지 않는다. 운영 캐시 식별자는 scene-reaction-v13-added-fact. FocusedGrounding은 added_fact와 meaning_clear를 사용한다. 구형 파서는 호환 검사에 남는다.
- 디버깅 복사는 영상·자막·최종 댓글·전체 후보·모델별 판단과 실패 상태를 구분해 클립보드로 보낸다. 생성/평가 중에는 비활성이다. 진단 extension/data/replier/llm-diagnostics.jsonl에는 단계 시간·오류를 기록하며 프롬프트·댓글 본문은 기록하지 않는다.
- 메뉴 연결·시작 자동 복원·수동 댓글 게시 구현은 존재한다. 계정/토큰 파일을 에이전트가 읽거나 실제 게시로 시험하지 않는다. 게시 결과가 불명확하면 자동 재전송하지 않는다.

## 직전 게이트

생성 전용 v10 요청·원문 결과와 v11 시간 제한 종료를 확보했다. 품질 게이트는 미달이다. v10 두 초안은 조언·추천으로 흘렀고, 사람이 반응 지점을 고른 v11은 초안이 없어 효과를 판단할 수 없다. 운영 소스 32개·앱 exe 전후 SHA256 동일과 테스트 포트 종료를 확인했다. 앱·평가 변경, 후편집, 다른 영상 시험은 하지 않았다.

## 승인 상태

- 현재 승인 범위: 같은 영상의 생성 프롬프트·입력 구성 분석·제한된 별도 시험과 실제 초안 보고. 앱 적용·평가 로직 수정·장시간 반복은 제외한다.
- 과거 앱 구현 권한을 현재의 ‘앱 적용 전 생성만 확인’ 경계보다 넓게 해석하지 않는다. 검사 추가·운영 경로 변경·재빌드는 현재 단계에서 수행하지 않는다.
- 기존 두 모델 설치 승인은 있었으나 추가 설치·의존성·비용·환경 변경을 허용하는 것은 아니다.
- 삭제 요청은 없다. 프로젝트·실험·모델·이력·앱을 삭제/이동하지 않는다. 기존 변경의 별도 로컬 보존 커밋만 승인됐다. push·실제 게시·24시간 자동 댓글 실행은 위임되지 않았다.
- OAuth 설정 선택·브라우저 동의·게시 최종 클릭은 사용자가 앱에서 수행한다. 비밀·토큰은 읽지 않는다.

## 차단

핵심 품질이 미해결이다. 짧은 수동 장면 요약에서도 일반적인 문장으로 수렴하며, 자동 자막에서 신뢰할 수 있는 장면 맥락을 만드는 방법은 아직 입증되지 않았다. 초안 성공과 앱 전체 성공을 구분해야 한다. 재개 시 먼저 저장된 입력·출력과 운영 입력 손실 지점을 설명하고, 필요한 최소 생성 실험만 정의한다. 앱 반영은 현재 범위를 넘어 별도 지시가 필요하다. 인증/게시 검증은 이 품질 문제의 선행 조건이 아니다.

## 알려진 위험

- 제목·자막·공개 댓글만 사용한다. 화면·음성까지 실제로 이해한 시스템이 아니다. 서로 다른 발췌·발화자·시간대의 내용을 한 사건으로 합치면 추측이 생긴다.
- 앱의 기존 복잡한 평가 경로는 오판·응답 지연·형식 오류·전부 탈락을 여전히 만들 수 있다. 점수를 높이거나 단어 차단을 늘려 품질 개선으로 보고하지 않는다.
- 과거 운영 측정 extension/data/replier-grounded-checks/residency-benchmark-timeout-recovery-final-latest.json은 생성·평가 51.504초, 후보 9개, 통과 5개, 성공 모델 호출 76개였다. 최종 ‘진짜 잼민이라 놀랐네 ㅋㅋ’도 품질 해결의 근거가 아니다. 이는 생성 전용 v8/v9와 다른 경로다.
- 상주 전후 다른 실행의 전체 시간은 후보 수와 호출 수가 달라 단축을 입증하지 못했다. 사용자 목표 5~10초와 현 상태의 차이는 남아 있다. 로딩 절약을 전체 시간 해결로 보고하지 않는다.
- 공개 YouTube 구조 변경·접근 제한과 자막 오류로 추천 수 부족·실패가 생길 수 있다. 기존 댓글이 없으면 제목·자막 경로로 돌아가며 디버그에 구분한다.
- 실험 원문/실행 의존성이 Git 제외 로컬 경로에 있으므로 다른 checkout만으로 재개할 수 없다. 테스트 사본의 설정을 운영 설정으로 오인하지 않는다.
- private 연결 파일은 에이전트 열람 대상이 아니다. 인증·실제 게시·공개 상태의 종단 검증을 이번 품질 실험이나 인계의 완료로 주장하지 않는다.

## 첫 다음 행동

1. 최신 v10-requests/results JSON과 v11-requests/results JSON을 읽어 실제 입력·원문 출력·시간 제한 종료를 구분한다. v8/v9보다 좋아졌다고 전제하지 않는다.
2. 사용자에게 v10 원문 두 개와 미충족 이유를 보고한 상태에서 다음 지시를 따른다. 앱 적용·재빌드·평가 추가·다른 영상 확대를 자동 진행하지 않는다.
3. 추가 생성 시험 지시가 있으면 장면 사실과 반응 목적을 짧게 분리한 입력을 검토한다. v11의 수동 반응 지점은 생성 성공과 품질이 미검증이다. 단어 금지나 후보 검사 강화로 대체하지 않는다.
## 재개에 필요한 파일

모든 상대경로는 위 24HReplier 워크트리 기준이다. 아래 코드는 운영 구현이며 현재 품질의 보증이 아니다.

- 생성·모델 생명주기: extension/src/replier/SceneReaction.cs, extension/src/replier/Comments.cs, extension/src/replier/DualComments.cs, extension/src/replier/ClearReactionPoints.cs.
- 후편집·평가·선택: extension/src/replier/ScenePolisher.cs, extension/src/replier/FocusedGrounding.cs, extension/src/replier/FitScoring.cs, extension/src/replier/ConnectionRubric.cs, extension/src/replier/SceneTieBreaker.cs.
- 공통 맥락·구형 근거 경로: extension/src/replier/ContextGuidance.cs, extension/src/replier/ReferenceGrounding.cs, extension/src/replier/WholeCommentGrounding.cs. 구형 작성 ReactionWriter/FastComments 경로와 운영 SceneWriter를 혼동하지 않는다.
- 화면·디버그: extension/src/replier/Desktop.cs, extension/src/replier/CommentDebugReport.cs.
- 수집·기존 댓글: extension/src/replier/VideoBatch.cs, extension/src/replier/VideoSearch.cs, extension/src/replier/TrendingSearch.cs, extension/src/replier/ChannelSearch.cs, extension/src/replier/AudienceComments.cs.
- 연결·게시 UI: extension/src/replier/YoutubeConnectionDialog.cs, extension/src/replier/YoutubePosting.cs, extension/src/replier/YoutubePostDialog.cs. 실제 연결 데이터는 읽지 않는다.
- 기존 회귀(필요할 때만): extension/tests/replier_grounded_spoken_checks.cs, extension/tests/replier_residency_lifecycle_checks.cs, extension/tests/replier_comment_debug_checks.cs. 합성 검사 통과를 자연스러운 댓글 품질 입증으로 사용하지 않는다.
- 문서 구조 검사: extension/tests/test_worktree_state_files.py. 현재 인계 검증용이며 모델을 실행하지 않는다.

## 다음 세션 시작 prompt

시작 규칙과 이 상태 문서를 읽고 최신 v10/v11 실제 요청·결과부터 확인하라. v10 초안은 조언으로 흘러 품질 미달이며 v11은 시간 제한으로 초안이 없다. 앱·평가 로직·실행 파일은 그대로다. 사용자 지시 없이 반복 실험이나 앱 적용을 하지 말고, 삭제·설치·게시·commit/push를 하지 마라.
