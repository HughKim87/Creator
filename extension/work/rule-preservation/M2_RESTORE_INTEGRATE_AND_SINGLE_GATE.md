# M2 복원·통합 단일 체크포인트

- 문서 분류: `phase-design`
- phase ID: `M2`
- lifecycle: `in_progress`
- 결과: M1에서 검증한 손실 의미만 기존 owner에 최소 delta로 복원하고, 중복 owner·새 active rule 없이 Core/Extension 단일 회귀 gate를 통과한다.
- 독자: M2 실행 agent와 승인자
- 전체 설계: `extension/work/RULE_PRESERVATION_AND_SIMPLIFICATION_DESIGN.md`
- 상태 owner: `SESSION_HANDOFF.md`
- evidence owner: `extension/work/rule-preservation/M0_RULE_CONSERVATION_MAP.md`
- 권위: 최신 사용자 지시와 `PROJECT_RULES.md`; 이 문서는 Core 정책을 독자적으로 승인하지 않는다.
- 첫 다음 행동: 아래 exact 경로를 다시 확인하고 최소 delta를 적용한 뒤 Core·Extension·maintenance 통합 gate를 실행한다.

## Entry gate

- M1 `M1-S1~S4`와 exit gate가 passed다.
- 사용자의 현재 “설계된 모든 단계” 지시를 M2 실행 승인으로 적용한다. exact Core scope는 아래 5개 경로로 제한하며, M0·M1에서 고정한 이유와 extension-only 대안을 벗어나지 않는다.
- 삭제·이동·보호 데이터 접근·외부 상태 변경·dependency 설치·push는 M2 범위가 아니다.
- working tree는 M1 checkpoint 이후 clean이어야 한다.

## Exact change contract

| exact path | 의미·이유 | 최소 delta | extension-only 판단 |
|---|---|---|---|
| `PROJECT_RULES.md` | L01 외부 입력 권위 경계, L02 최소 데이터·권한 | always-on 정책 bullet 2개 | 범용 보안·권한이므로 대체 불가 |
| `core/rules/boundary-routing-and-dependency.md` | L03 새 tool/API/agent/MCP route 검증 | BND05 절 1개 | 범용 boundary owner |
| `core/rules/cross-validation.md` | L04 1차 출처·변동 주장·약한 출처 | 교차검증 규칙 1개 | 범용 evidence owner |
| `core/rules/document-work.md` | L05 조건부 red-team, L10 write-success와 내용 검증 분리 | 일반 문서 규칙 2개 | 범용 document owner |
| `core/rules/file-extraction.md` | L08 historical evidence의 exact-read와 authority 분리 | FEX02 절 1개 | 범용 extraction owner |
| `extension/rules/video-editing-validation-and-delivery.md` | L09 영상 검증 사다리의 generated/parsed/tool 단계 | R15·상태표 최소 확장 | 영상 artifact 전용이므로 Core에 승격하지 않음 |

L06·L11은 복원하지 않는다. L07은 이미 보존됐다. L12는 report-only·미검증 표본이므로 규칙 변경 대상이 아니다. 신규 rule file과 literal-only test는 만들지 않는다.

## Slices

### M2-S1 — Core 정책·procedure delta

정확히 위 5개 Core 경로만 수정한다. 역사 문장의 그대로 복사나 작업명·일회성 수치를 넣지 않고 `조건 / 행동 / 예외 / 검증`으로 압축한다. 기존 규칙과 겹치는 승인·보호·검증 문장은 중복하지 않고 delta만 추가한다.

### M2-S2 — Extension domain delta

영상 owner의 기존 R12/R15/R16과 상태 증거표를 유지하면서 `generated`, `parsed`, `tool-validated`를 추가한다. 기술·의미·미디어·앱·사용자 gate는 독립 상태로 남기고, 낮은 단계 성공을 높은 단계 성공으로 추론하지 않는다.

### M2-S3 — 의미·route 교차검증

L01~L05·L08~L10마다 최종 owner가 정확히 하나인지 확인한다. Core/Extension direct link와 route를 검사하고, 각 delta가 historical source의 행동·경계·검증을 재현하는지 직접 대조한다. L06·L11·L12는 비복원 근거가 남아 있는지 확인한다.

### M2-S4 — 통합 성공게이트

다음 명령을 모두 실행한다.

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH=((Resolve-Path 'core/src').Path, (Resolve-Path 'extension/src').Path, (Resolve-Path 'core/tests').Path -join ';')
python -m unittest discover -s core/tests -q
python -m unittest discover -s extension/tests -q
python -m file_data --root . maintenance-verify --allow-core-changes
```

추가로 변경 6개 파일의 strict UTF-8·NUL 0·후행 공백·관련 링크·`git diff --check`·scoped diff를 확인한다. Core/Extension 테스트와 maintenance 중 하나라도 실패하면 passed로 기록하지 않는다.

## Slice gate

M2-S1~M2-S4의 각 slice는 exact scope와 실제 검증 결과를 기록한 뒤 다음 slice로 전환한다.

## Exit gate

- L01~L05·L08~L10의 보존 의미가 각 exact owner에 하나씩 존재하고 중복 owner가 없다.
- L09의 domain ladder는 Core에 역의존하지 않고 기존 상위 router를 유지한다.
- L06·L11·L12는 복원되지 않았고 근거·evidence label이 보존된다.
- Core·Extension·maintenance·문서 무결성·scoped diff가 모두 통과하고 보호 경로 staged count가 0이다.
- 실패 시 변경을 성공으로 보고하지 않고, 해당 단계에서 마지막 정상 Git 버전과 scoped diff를 대조해 복구한다. 같은 gate 목적이 세 번 실패하면 원인·위험·다음 조사 방법을 handoff에 기록한다.

## 복구·전환 gate

실패 시 변경을 성공으로 보고하지 않고, 해당 단계에서 마지막 정상 Git 버전과 scoped diff를 대조해 복구한다. 통과 뒤 lifecycle을 `passed`로 바꾸고 M3 phase-design을 활성화한다. M2 변경만 별도 단계 커밋으로 stage·commit한다. 삭제·이동 후보는 M3까지 목록으로만 유지한다.

## Closeout record

- M2-S1: `passed` — exact Core 5경로에 범용 delta 적용
- M2-S2: `passed` — 영상 Extension 검증 사다리 delta 적용
- M2-S3: `passed` — one-owner·route·historical meaning 대조 완료
- M2-S4: `passed` — Core 139·Extension 132·maintenance pass·diff check 통과
- M2 exit: `passed`
- M3 transition: `pending`
