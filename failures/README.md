# 실패 지식

- 목적: 작업과 단계에서 발생해 원인·해결·검증이 확인된 실패를 다음 작업에서도 재사용할 수 있는 장기 지식으로 보존한다.
- 읽는 시점: 유사 실패를 진단·해결할 때, 실패 기록을 갱신할 때, 각 단계의 완료 게이트에서 누락과 재발을 확인할 때.
- 소유 범위: 이 폴더의 각 사례 문서가 해당 실패 원인과 해결 지식의 정본이다. 발생 단계는 출처일 뿐 소유자가 아니다.
- 활성 상태 경계: 현재 미해결 시도, 연속 실패 횟수, 즉시 차단과 재개 조건은 `SESSION_HANDOFF.md`가 소유한다.
- 기록 규칙: [Failure-Record Work Rules](../rules/failure-records.md)

## 기록 원칙

- 원인이 같은 실패는 새 문서를 만들지 않고 기존 사례의 재발 이력과 검증 근거를 갱신한다.
- 원인과 해결이 성공 검증으로 확인된 경우에만 `해결`로 기록한다.
- 증상, 확인된 원인, 실패 시도, 해결, 검증, 재발 방지 조건을 구분한다.
- 단계 문서나 핸드오프에 사례 본문을 복사하지 않고 이 정본을 연결한다.
- 아직 원인을 확인하지 못했거나 해결 검증이 끝나지 않은 실패는 이 폴더로 승격하지 않는다.
- 이 Markdown 구조가 사례 본문의 정본이다. Stage 05의 `failure_knowledge` record는 정본 경로·hash가 일치할 때만 유효한 기계 판독 projection이며 자동 수집·검색 인덱스는 아니다.
- 구조화 관계와 stale 판정은 [지식 유형 계약](../docs/KNOWLEDGE_TYPES_CONTRACT.md), 개정·대체는 [지식 수명주기 계약](../docs/KNOWLEDGE_LIFECYCLE_CONTRACT.md)을 따른다.

## 사례 목록

아래 목록은 탐색용 링크만 제공한다. 각 사례의 상태, 시점, 원인, 해결과 검증 근거는 연결된 문서만 소유한다.

- [프로젝트 목적의 과대 해석](project-purpose-overreach.md)
- [역사 지식 범위의 무제한 확대](historical-scope-expansion.md)
- [미래 단계 기능의 조기 구현](premature-future-stage-implementation.md)
- [영향을 설명하지 않는 형식적 승인](approval-without-impact-context.md)
- [오래된 핸드오프 상태와 죽은 경로](stale-handoff-state.md)
- [후행 공백 정규식의 탭 오해석](trailing-whitespace-regex.md)
- [`apply_patch`와 Markdown 목록 기호 충돌](apply-patch-markdown-prefix.md)
- [Windows 문서 검증 명령의 환경·문구 가정](windows-validation-command-assumptions.md)
- [권위 역할과 문서 유형의 혼합](authority-role-type-conflation.md)
- [활성 문서의 끊어진 로컬 링크](active-document-link-rot.md)
- [Obsidian 보호 경로 링크 노출](obsidian-protected-path-link-leakage.md)
- [시스템 Python 실행 경로 가정](runtime-discovery-system-python.md)
- [기록 ID와 저장 주소의 분리로 생기는 중복](record-id-address-ambiguity.md)
- [Windows CLI 표준 입출력 인코딩 불일치](windows-cli-utf8-stdio.md)
- [쓰기 후 검증의 잠금 해제 경쟁 구간](post-write-verification-lock-window.md)
- [저장된 기록 유형의 승인 우회](stored-type-approval-bypass.md)
- [구현 폴더와 정보 구조 계약의 드리프트](structure-contract-folder-drift.md)
- [작업 event 시각의 snapshot 역행](work-event-time-regression.md)
- [PowerShell 외부 프로세스 JSON 인수의 따옴표 손실](powershell-native-json-argument-quoting.md)
- [진행 중 작업의 체크포인트 전이 부재](in-progress-checkpoint-transition-gap.md)
- [변경된 로컬 출처 한 건의 전체 목록 실패 전파](mutable-local-source-list-fanout.md)
- [테스트 fixture의 payload 계약 구조 가정](test-fixture-contract-shape-assumption.md)
- [Windows 텍스트 줄바꿈 변환과 실제 크기 측정 불일치](windows-text-newline-size-measurement.md)
- [기존 Python bytecode 캐시와 청결 게이트 불일치](python-bytecode-cache-cleanliness.md)
- [완료 작업에 다음 행동을 함께 남기는 상태 충돌](completed-work-next-action-conflict.md)
