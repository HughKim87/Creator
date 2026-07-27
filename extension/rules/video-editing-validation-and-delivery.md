# 영상 편집 검증·전달 규칙

- Purpose: 구조·미디어·앱·사용자 검증을 구분하고 실제로 확인한 수준보다 결과를 높여 보고하지 않는다.
- Read when: validator를 설계·실행하거나 timeline·XML·검토본의 성공과 전달 상태를 보고할 때.
- Authority: 영상 편집 workflow 계약의 완료 정의와 `PROJECT_RULES.md`의 검증·보호 데이터 경계가 상위 권위다.

### R12 — 기술 gate와 의미 gate 분리

- 조건: 새 timeline, XML 또는 검토본을 성공으로 보고하려 한다.
- 행동: 구조·디코딩·길이·링크 검증과 발화·인과·상태·공간·반복 검수를 별도 결과로 기록한다.
- 예외: 해당 산출물에 적용되지 않는 검사는 `해당 없음`으로 남기며 통과로 계산하지 않는다.
- 검증: 두 gate가 모두 필요한 작업은 둘 다 통과하기 전 `편집 완료`나 `사용자 승인 후보`라고 보고하지 않는다.

### R15 — 검증 단계별 주장 제한

- 조건: XML 생성, import, 재생, 사용자 검토 결과를 상태로 기록하거나 보고한다.
- 행동: `semantic_gate: passed → structure-validated → media-validated → app-validated → user-approved` 중 증거가 있는 단계만 기록하고, 다음 단계가 자동으로 충족됐다고 추론하지 않는다.
- 예외: 적용되지 않는 단계는 `not-applicable`로 기록할 수 있지만 더 높은 단계를 통과한 것으로 계산하지 않는다.
- 검증: 각 상태에 실행 시점, 대상 artifact, 검사 방법, 결과 owner가 있고 보고 문구가 최고 검증 단계보다 높지 않은지 확인한다.

### R16 — validator 계층 분리

- 조건: 새 validator를 추가하거나 여러 검사를 하나의 합격 결과로 묶으려 한다.
- 행동: 검사를 `비보호 구조 / 선언 metadata / 보호 미디어 / 의미 검수`로 분류하고 각 결과를 독립적으로 반환한다.
- 예외: 하나의 명령이 여러 계층을 실행할 수 있지만 계층별 결과와 미실행 상태를 합치지 않는다.
- 검증: 보호 미디어 검사는 exact 승인 없이는 실행되지 않고, 구조 통과가 media·app·user 통과를 만들지 않는지 확인한다.

## 상태 증거

| 상태 | 최소 증거 |
|---|---|
| `semantic_gate: passed` | 완성 timeline 순차 의미 검수와 reviewer |
| `structure-validated` | frame·gap·track·source lineage·XML 구조 검사 |
| `media-validated` | exact 승인 원본의 decode·프레임·오디오 확인 |
| `app-validated` | 대상 Premiere profile의 실제 import·offline media·재생 확인 |
| `user-approved` | exact artifact에 대한 사용자 결과 승인 |

## 재현 사례

| ID | 상황 | 기대 판정 |
|---|---|---|
| TC12 | XML 구조 검사는 통과했지만 인과 누락이 남음 | 기술 통과·의미 실패로 기록하고 완료 보고를 차단한다 |
| TC15 | 합성 XML 구조 테스트만 통과함 | `structure-validated`까지만 보고하고 Premiere 호환·사용자 승인을 주장하지 않는다 |
| TC16 | exact 원본 승인 없이 RMS·밝기 검사를 실행하려 함 | 보호 미디어 검사를 미실행으로 두고 구조 결과와 분리한다 |
