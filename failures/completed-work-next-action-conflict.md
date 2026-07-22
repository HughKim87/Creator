# 완료 작업에 다음 행동을 함께 남기는 상태 충돌

- 상태: 해결·회귀 검증 완료
- 최초 확인: 2026-07-23 Stage 08 work 완료 전이
- 마지막 검증: 2026-07-23
- 적용 범위: `WorkStateService`, `work-transition`, terminal work snapshot

## 증상

Stage 08 성공 게이트 뒤 work를 `completed`로 닫는 전이가 `Completed work cannot keep a next action.` 입력 계약 오류로 거부됐다.

## 확인된 원인

- 완료 snapshot은 현재 work 안의 후속 행동이 없어야 하므로 `next_action`이 반드시 `null`이어야 한다.
- 다음 단계의 첫 행동을 핸드오프에 기록하는 것과 완료된 현재 work의 `next_action`을 같은 위치에 기록하려 했다.
- 전이 검증은 event append 전에 실행되어 실패 시 event와 snapshot이 모두 보존됐다.

## 실패·해결 이력

| 시점·문맥 | 시도·결과 | 최고 연속 횟수 | 해결·검증 |
|---|---|---:|---|
| Stage 08 work 완료 전이 | `--to-status completed`와 `--next-action 'Stage 08 경계 커밋…'`을 함께 전달해 명시적 거부 | 1 | 같은 expected hash에서 `--next-action`만 제거해 재실행하고 status `completed`, `next_action: null`, 새 snapshot hash를 확인 |

## 해결과 검증

- 거부 뒤 work snapshot hash가 기존 값과 같아 부분 event나 부분 snapshot이 없음을 확인했다.
- 완료 전이에는 완료 항목·관련 ID·근거만 기록하고 `next_action`은 전달하지 않았다.
- 다음 단계의 시작 행동은 완료 work가 아니라 `SESSION_HANDOFF.md`의 정확한 재개 체크포인트가 소유한다.
- 보정된 전이 결과는 work `3c6681e5-2595-47a1-9d47-f056c4218031`, status `completed`, `next_action: null`, snapshot hash `sha256:efd51ef93859942a538314b126cccc0f8e71318c5493465c079371d1ec5ed1f7`다.

## 재사용 규칙

- `completed`·`failed` 같은 terminal work 전이에는 현재 work의 `next_action`을 함께 보내지 않는다.
- 후속 단계 행동은 새 work request나 핸드오프 체크포인트에 기록하고 완료 work의 잔여 작업처럼 표현하지 않는다.
- 전이가 입력 계약으로 거부되면 snapshot hash와 event 수 불변을 확인한 뒤 같은 expected hash에서 최소 인자만 보정한다.

## 근거

- [작업 기록·현재 상태 계약](../docs/WORK_STATE_CONTRACT.md)
- [세션 핸드오프](../SESSION_HANDOFF.md)
- [Stage 08 계획](../docs/build/stage-08-maintenance-automation.md)
