# 다음 영상의 약속 이행·실적 진단 개선 설계

- 목적: 승인된 E1·E2를 기존 영상 workflow owner에 반영하고 검증·로컬 커밋한다.
- 읽는 시점: 이번 개선 실행·검증·정리 전.
- 책임: 에이전트가 승인 범위를 구현·검증하고 사용자가 범위와 외부 효과를 소유한다.
- 상태: 승인 범위 안의 임시 설계. 정리 커밋에서 제거하고 Git 이력으로 보존한다.
- 관련 권위: PROJECT_RULES.md, session-close 스킬과 적용된 Core 작업·단계·버전 관리·거버넌스 규칙.

## 작업 계약과 소유권

대상은 D:/AI Agent/GitHub/Creator의 main, host 역할이다. 시작 HEAD는 5cb73e9140b230e1e5f8d5229461b438f9f10e81이며 부모와 Core의 Git 상태는 clean으로 직접 확인했다. Core는 읽기 전용이고 gitlink·다른 worktree·게시 영상·보호 입력과 산출물·전역/플러그인 스킬·원격에는 쓰지 않는다. 기존 ignored extension/data는 이번 자원이 아니므로 정리하지 않는다.

분석 원본은 현재 세션이다. 공개 metadata만으로 실적 진단을 끝낸 뒤 실제 Studio를 확인한 과정, 유지율 그래프·자막의 대조를 근거로 한다. 저조한 클릭률/유지율의 존재와 특정 창작 요소의 인과 효과는 다르다. 이번 개선은 진단과 검수 절차이며 성과 개선이 입증됐다는 결론이 아니다. 영상별 지표·계정 정보·원문 대화·이미지는 main 문서와 합성 검사에 복제하지 않는다.

E1은 기존 R06 스파인·인과 연결의 보강이다. 새 편집 또는 약속·순서가 바뀌는 작업에서 도입 질문, 본편 첫 진행 시점, 회수 시점과 대기 구간의 기능을 대조한다. 의도된 지연·분위기 체험은 설명 가능한 예외이며 국소 수정·형식 재생성에는 전체 재설계를 강제하지 않는다. 특정 초 수나 영상 길이를 보편 기준으로 만들지 않는다.

E2는 youtube-title-thumbnail의 게시된 영상 성과 점검 모드다. Studio 연결·채널/영상 확인, 유입 경로별 지표, 유지율과 내용의 대조, 관측/가설/미검증의 구분과 다음 영상 적용을 소유한다. 단순 문구 수정·새 제목 제작에는 실적 진단을 강제하지 않는다. 채널 전체 진단과 업로드/수정 권한을 확대하지 않는다. 세부 절차는 조건부 reference 하나에만 둔다.

모두 YouTube 도메인에 종속된 Extension 개선이다. Core 일반화·Core 의미 변경과 규칙 route 변경은 없다. E3(참고 이미지·썸네일 시각 검수 보강)는 보류한다.

## 단계와 조건 대응

| 단계 | goal·변경 표면 | 성공·검증·커밋 조건 |
|---|---|---|
| 0 | 이 설계를 정확한 단일 경로로 커밋 | 승인 E1·E2, 제외 E3, 경로·검증·정리 범위 대조. 실제 commit snapshot 내용 확인 |
| 1 | E1·E2가 이어지는 다음 영상 개선 workflow 완성 | 아래 경로만 수정. 기존 관련 합성 회귀·bundle·링크·UTF-8·diff 검사 pass와 8개 수동 문맥 시나리오 판단. state/main.md 현재 상태 갱신 후 개선 커밋; 실제 snapshot 경로와 내용 대조 |
| 정리 | 활성 설계 제거·최종 보고·clean 상태 | 0/1 commit 보존, 설계의 고유 내용이 Git에 있고 활성 참조가 없음을 확인 후 이 파일만 삭제·정리 커밋. Core 불변·최종 Git 상태·보고 일치 확인 |

1단계 정확한 변경 표면:
- extension/rules/video-editing-story-and-cut-design.md: R06에 약속의 진행·회수·중간 지연 검수와 검증 기준 보강.
- .agents/skills/youtube-title-thumbnail/SKILL.md: E1 제목/도입 대조와 E2 조건부 실적 모드 발견·진입 안내.
- .agents/skills/youtube-title-thumbnail/references/performance-review.md: E2의 mode-specific 절차. 다른 정본을 복제하지 않는 새 하위 reference.
- .agents/skills/coordinate-video-production/references/skill-bundle.json: 위 스킬 파일의 무결성 metadata만 갱신.
- state/main.md: 이번 활성 상태와 종료 뒤 재개 정보만 갱신. 다른 작업의 상태는 유지.

필수 명령: Python -B unittest discover로 test_extension_rule_routing.py, test_title_thumbnail_package.py, test_video_session_improvements.py, test_worktree_state_files.py를 각각 실행; check_skill_bundle.py; git diff --check. 스킬 quick_validate는 기존 Python에서 PyYAML이 있으면 실행하며 없으면 설치하지 않고 한계로 기록한다. 스크립트·schema 변경이 없으므로 성과·의미 판단을 문자열 테스트로 대신하지 않는다.

수동 문맥 검토 8개: (1) 하이라이트 뒤 곁가지로 지연 (2) 사건의 원인인 준비 과정 (3) 의도된 장기 회수/분위기 (4) 국소 형식 수정 (5) Studio 연결 가능 (6) Studio 접근 불가 (7) 추천 중심 저CTR와 작은 검색 표본 (8) 유지율 하락 및 제목 버전 누적/다음 영상만 요청. 실제 공개/Studio 조작은 재실행하지 않고 지침의 선택과 결과 범위를 검토하며 독립 Agent 재현으로 주장하지 않는다.

모든 필수 gate와 단계 goal 및 commit snapshot 확인 뒤 전환한다. 무관한 local change가 생기면 정지하고 사용자 결정을 받는다. 실패하면 영향받은 gate만 원인을 해소해 재검증하며 승인 밖 범위로 확대하지 않는다. 복구 기준은 마지막 검증 commit이고 reset·stash·기존 파일 처분은 자동 수행하지 않는다.

## 자원 수명과 보고

이번 임시 추적 자원은 이 설계 파일 하나다. 종료 시 정확히 이 파일만 삭제하는 범위는 승인된 설계·개선·정리 로컬 커밋 범위에 속한다. 합성 테스트가 자기 호출에서 만든 임시 fixture만 정리한다. 기존 자료·생성 이미지·runtime은 정리하지 않는다.

최종 보고 보존 경로: C:/Users/Hugh/.codex/visualizations/2026/10/11/01a129ec-9f0c-7dd2-bb7b-bdc26cadf686/session-close-e1-e2-20261016.md. 보고에는 개선 전후·승인/보류·정확한 로컬 commit·실행 검사·미실행/효과 한계·정리와 Git 상태를 담는다. 새 영상 제작과 실제 CTR/유지율 상승 검증은 이번 범위가 아니다.
