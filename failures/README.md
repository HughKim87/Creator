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
- 이 구조는 사람이 읽는 최소 Markdown 기록이다. 기계 스키마, 자동 수집, 검색 인덱스는 후속 단계의 별도 승인 전까지 도입하지 않는다.

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
