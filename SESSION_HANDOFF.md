# SESSION_HANDOFF.md — 작업 재개 안내

- 역할: 공용 진입점. 특정 영상의 상태나 식별자를 기록하지 않는다.
- 사용자 제공 자료는 `inputs/`에서 읽는다.
- 입력 자료를 바탕으로 만든 현재 작업 상태는 `outputs/SESSION_HANDOFF.md`에서 읽는다.
- `outputs/SESSION_HANDOFF.md`가 없으면 진행 중인 영상 작업이 없는 것으로 본다.
