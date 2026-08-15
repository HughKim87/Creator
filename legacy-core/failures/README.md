# 실패 지식

- 목적: 다시 발생할 가능성이 있고 해결 방법이 비자명한 실패만 원인별로 보존한다.
- 현재 미해결 blocker는 `SESSION_HANDOFF.md`가 소유한다.
- 기록 규칙: [Failure-Record Work Rules](../rules/failure-records.md)

## 기록 원칙

- 같은 원인의 증상은 기존 사례에 합친다.
- 일회성 명령·인용·경로 실수는 별도 사례로 만들지 않는다.
- 원인과 해결이 검증된 경우에만 `해결` 상태로 기록한다.
- 상세 실행 로그와 과거 단계 서사는 Git 이력에 맡긴다.

## 사례 목록

- [범위·권한·목적 경계](scope-and-authority-boundaries.md)
- [정본·문서·현재 상태 드리프트](canonical-owner-and-document-drift.md)
- [Windows 런타임·명령·텍스트 경계](windows-runtime-and-text-boundaries.md)
- [원자 쓰기·기록·상태 무결성](atomic-state-and-storage-integrity.md)
- [보호 경로의 간접 노출](protected-path-visibility.md)
- [검증 fixture·패치·캐시 위생](validation-fixture-and-cache-hygiene.md)
