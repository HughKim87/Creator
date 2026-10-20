# 24HReplier 작업 상태

- 목적: 공개 YouTube 제목·자막·기존 댓글을 참고해 자연스러운 댓글을 제안하고 사용자가 수동 게시하는 Windows 앱의 재개 상태.
- 읽는 순서: core/PROJECT_RULES.md → PROJECT_RULES.md → SESSION_HANDOFF.md → 이 문서.
- 책임: codex/24HReplier 작업 에이전트. 사용자 승인·실제 게시 결정은 사용자가 소유한다.
- 관련 권위: PROJECT_RULES.md, 직접 호출한 session-close 스킬, 승인된 필수안 E1·E2.
- 워크트리: D:/AI Agent/GitHub/Creator-24HReplier, codex/24HReplier. Creator main에서 앱 작업하지 않는다.
- handoff mode: same-workspace. 소스가 커밋돼도 모델·실험 원문·연결 정보는 Git 제외 로컬 경로에 의존한다.
- 갱신일: 2026-10-20.

## 현재 단계

승인된 E1·E2의 소스 수정·모의 검증·단계 커밋·종료 보고를 완료했다. 보고서는 D:/AI Agent/GitHub/24HReplier-session-close-report.md에 있다. extension/work/24hreplier-session-close-design.md는 삭제 금지 지시에 따라 비활성 완료 설계로 보존한다. Core·gitlink·정책은 변경하지 않는다.

**실제 댓글 품질과 5~10초 목표는 여전히 미해결이다.** 이번 수정은 실험 입력의 진실성과 작성·평가 근거 일치를 고친 것이다. 실제 모델 생성, 앱 UI 실행, OAuth·게시를 시험하지 않았다. 사용자용 운영 exe는 덮어쓰지 않았다. 별도 컴파일 출력은 extension/.runtime/replier-checks/session-close-e1-e2/에 있다. 따라서 현재 실행 파일을 켜면 새 소스가 아직 반영되지 않는다.

### 현재 소스 동작

- E1: extension/tests/replier_probe_request.ps1에서 system→실제 예시→현재 입력의 요청을 한 번 직렬화한다. replier_generation_context_probe.ps1과 replier_generation_grounded_input_probe.ps1은 같은 JSON을 기록·전송한다. request_sent를 전송 직전에도 저장하고 실패 시에도 남긴다. 재실행 결과는 generation-only-v3-repaired.json / generation-only-v4-repaired.json으로 분리한다. 과거 v3/v4 결과는 예시가 실제 전송된 성과가 아니다.
- E2: WritingContext.cs가 작성에 실제 제공한 구간 ID·사실·원문·시각을 후보 Material의 writing_context에 보존한다. SceneWriter와 FocusedGrounding이 같은 사실 배열을 공유하며 관계 평가도 보존한 실제 인용을 사용한다. 나중에 다른 자막에서 근거를 빌리지 않는다. 제목은 배경이며 제목만으로 사건·결과를 추가하지 않도록 구분한다.
- 스냅샷 없는 기존 후보는 기존 단일 근거 경계를 유지한다. 후편집은 스냅샷을 유지한다. 캐시 버전은 scene-reaction-v14-shared-writing-context다. 생성·평가 호출과 점수 기준을 추가하거나 상향하지 않았다.
- 운영 파이프라인 자체는 Evidence → Qwen ScenePlanner → ClearReactionPoints → 모델별 SceneWriter → Gemma ScenePolisher → 두 모델의 말투·근거·관계 평가 → Qwen 선택이다. 모델당 최대 5개 목표, 최종 1개 표시. 이 많은 호출을 줄이거나 자연스러운 초안을 보장한 변경은 아니다.

### 생성 품질 작업의 남은 맥락

- 핵심 대상: vDWt01ul5F0, 「잼민이 기강 잡기」, 김재원의 즐거운 세상. 저장 자막은 extension/data/replier/content/vDWt01ul5F0.json.
- 실제 최신 생성 전용 입력·결과: extension/data/replier-prompt-probe/generation-context-v10-requests.json, generation-context-v10-results.json, generation-context-v11-requests.json, generation-context-v11-results.json. 기존 검증 자료 generation-context-v10-v11-verification.json. 이번 종료 작업에서 새 생성은 하지 않았다.
- 기존 v10 초안은 조언·추천으로 흘렀고 v11은 제한 시간 내 초안이 없었다. 품질 개선 성공으로 사용하지 않는다. 사람이 설명한 장면과 자동 연속 자막 입력은 구분해야 한다.
- 이전 비교 원문: extension/data/replier-prompt-probe/generation-only-v8.json, generation-only-v9.json. ‘대화 시작이 막막함/이어가기 고민’으로 수렴하는 일반적·반복적 문장이며 수동 장면 요약에 한정됐다. 자연스러운 최종 품질·다른 영상 일반화·앱 속도를 입증하지 않는다.
- 생성 전용 도구: extension/tests/replier_generation_context_v10_probe.cs, replier_generation_focus_v11_probe.cs, replier_generation_single_draft_probe.cs, replier_generation_single_repeat_probe.cs. 일부는 별도 포트 11440의 Comments.TestOnly.cs 파생 사본을 전제로 한다. 운영 모델 서버와 혼동하거나 바로 실행하지 않는다.
- 생성 입력은 아직 종결형 구절 선택·일반 사실 치환·고정 반응 슬롯에 의존한다. 연속 대화의 발화자·조건·시점이 빠지거나 별도 장면을 합치면 부자연스러운 반응이 생긴다. 기존 댓글의 말투만 남겨 실제 반응 소재가 약해지는 문제도 남아 있다. 새 단어 금지나 평가 호출을 더 붙여 해결된 것으로 보고하지 않는다.

### 실행·기존 기능

- 운영 exe: extension/.runtime/replier-desktop/24HReplier.exe. 시작 scripts/Start-24HReplier.cmd, 빌드 scripts/Build-24HReplier.ps1. .NET Framework C#5 WinForms, System.Security.dll 등 기존 참조 사용.
- 기존 Ollama v0.40.4, Gemma gemma4:e2b-it-qat, Qwen qwen3.5:4b. 런타임 extension/.runtime/replier-llm, 프로필 extension/config/replier-llm-local.json.
- 운영 서버 localhost:11439. 앱 시작 시 Gemma→Qwen 준비, keep_alive=-1, 종료 시 자기 Windows Job만 정리한다. 모델 상주 설정은 유지됐다. 준비 완료 후 생성 타이머/180초 제한 시작, 호출당 60초·모델 작성 75초 제한이 남는다.
- 검색어 / 실제 자동완성 검색어 하나 무작위 / 채널 제목·태그에서 게임 하나 무작위 / 한국 게임 인급동. 카테고리·기간·종류 복원, 직접 입력 문자열은 저장하지 않는다. 한국어 제목·원어 자막·카테고리·기간 필터와 최대 10개 표시, 최종 댓글 수 내림차순이다. 게임 인급동은 게임 카테고리 전용이다.
- 영상 중복 제외는 제거됐다. 자막 캐시·자동 검색어 이력·댓글 문장 중복 검사와 구분한다. 기존 이력 파일은 보존한다.
- 숫자 정렬, 독립 목록 스크롤, 영상 열기, 경과 시간, 재생성·재평가·디버깅 복사, 메뉴 계정 연결·복원·수동 게시 구현이 존재한다. 기존 평가 실패 시 이전 검증 댓글 유지·후보별 오류 격리는 유지됐다.
- 연결 파일 extension/data/replier/youtube-private/connection.bin은 읽지 않는다. 토큰·설정 원문을 로그·fixture·커밋으로 복제하지 않는다. 실제 게시 최종 클릭은 사용자 소유다.

## 직전 게이트

E2 모의 경계 검사와 별도 전체 C# 컴파일 pass. 실제 작성 요청과 저장 근거·Gemma/Qwen 평가 요청의 일치, 두 번째 구간 유지, 미제공 구간 제외, 원문·시각 보존, 후편집 보존, 기존 후보 호환, 취소를 확인했다. 모의 평가 호출은 모델당 기존 3회 그대로였다. 기존 DualChecks·CandidateIsolationChecks·GroundedSpokenChecks와 E1 요청 검사도 pass. 이는 구조 검증이며 실제 모델의 의미 판단·품질·속도 검증은 not_run이다.

## 승인 상태

- 승인: 기존 변경 별도 보존 커밋, 필수안 E1·E2의 제한된 소스 수정·회귀 검증·단계별 커밋·종료 보고. E3 빈 줄 정리는 보류.
- 사용자 지시: 삭제·초기화 금지. 기존 파일·실험 데이터·이번 생성물도 보존한다. 완료 설계는 비활성으로 남긴다.
- 미위임: 추가 모델 설치·비용·환경 변경·push·실제 게시·상시 자동 댓글 실행·Core 변경. 이번 설계는 운영 exe 덮어쓰기·실제 모델 생성도 제외했다.

## 차단

E1·E2 구조 개선의 검증 차단은 없다. 앱의 자연스러운 댓글 품질은 별도 미해결 작업이다. 소스를 적용하려면 운영 빌드가 필요하고, 자연스러움은 같은 영상의 실제 초안으로 검증해야 한다. 구조 검사 pass를 그 성과로 확대하지 않는다.

## 알려진 위험

- 실제 화면·음성을 이해하지 않으며 자동 자막·다른 시점 댓글은 잘못 해석될 수 있다. 사실 근거 공유는 모델의 의미 판정 정확도를 보장하지 않는다.
- 호출 수·후편집·긴 평가 응답이 남아 있으므로 5~10초를 보장하지 않는다. 하드웨어 설명으로 생성 로직 분석을 대신하지 않는다.
- 새 공유 근거는 작은 모델에 더 많은 사실을 제공한다. 서로 다른 구간을 합치는 오판이 실제로 줄었는지는 미검증이다. 관계 점수는 정확도 확률이 아니다.
- 운영 exe가 아직 이전 소스이므로 소스 변경과 실제 실행 결과를 혼동하지 않는다. 빌드·실제 품질 검증을 수행한 뒤에만 앱 반영과 사용자 승인 상태를 갱신한다.
- 모델·계정·실험 데이터는 Git 제외 상태다. 다른 checkout만으로 실험을 재현할 수 없다. 공개 YouTube 구조 변경·접근 제한도 남는다.

## 첫 다음 행동

1. 세션 종료 보고와 단계 커밋을 확인하고 작업 지시를 따른다. E1·E2를 댓글 품질 해결로 전제하지 않는다.
2. 앱에 반영해 확인하라는 지시가 있으면 scripts/Build-24HReplier.ps1로 빌드한 뒤 사용자용 exe와 소스 일치를 확인한다. 설치·실제 게시로 확대하지 않는다.
3. 생성 개선을 재개하면 최신 v10/v11의 실제 요청·원문 결과부터 읽는다. 제목은 전체 화제, 연속 자막은 장면 사실, 기존 댓글은 반응 소재·말투라는 역할을 분리한다. 같은 영상의 생성 초안만 짧게 시험하고 실제 메시지·편집 전 원문·시간·한계를 보고한다.
4. 단어 금지·평가 추가·점수 상향으로 초안 결함을 덮지 않는다. 다른 영상 확대·장시간 반복은 새 근거나 해당 지시가 있을 때만 수행한다.

## 다음 세션 시작 prompt

D:/AI Agent/GitHub/Creator-24HReplier의 시작 규칙과 state/24HReplier.md를 읽어라. E1·E2는 소스와 모의 검증까지 완료됐지만 운영 exe에는 미반영이며, 실제 댓글 품질·5~10초 목표는 미해결이다. 최신 생성 입력·출력부터 확인하고 사용자가 지시한 범위에서 다음 작업을 수행하라. 삭제·초기화·추가 설치·실제 게시·push는 하지 마라.
