# 2026-07-24 Claude Stage 11 커밋 전후 변경 분석 보고서

- 문서 유형: 시점 증거 보고서 (point-in-time evidence)
- 작성자: Claude
- 분석 범위: 작업 전 커밋 `2aec62d` (docs: Stage 10 공식 종료) → 작업 후 커밋 `846b31f` (docs: Stage 11 실행 교훈 규칙 반영)
- 분석 방법: `git log`, `git diff --stat/--numstat`, 주요 파일 전체 diff 검토, Stage 11 owner 문서 대조
- 정본 owner: [Stage 11 운영 마찰·인지 복잡성 축소](../docs/build/stage-11-operating-friction-reduction.md) — 본 보고서는 요약·검증 시점 기록이며 규칙·상태를 소유하지 않는다.

## 1. 요약

두 커밋 사이 구간은 Stage 11 "운영 마찰·인지 복잡성 축소" 전체에 해당하며, 5개 커밋으로 31개 파일에서 771줄 추가·1,105줄 삭제(순감 334줄)를 수행했다. 실제 도메인 기능 변경 없이 제어 문서·규칙·상태 표면을 경량화한 작업으로, 세션 시작 필수 문서를 412줄에서 151줄로, `SESSION_HANDOFF.md`를 302줄에서 49줄로 줄이고 `quick / standard / controlled` 작업 등급 체계를 도입했다. 보호 경로(`inputs/`, `outputs/`, `backup/`)와 legacy 데이터는 접근·변경되지 않았고, 삭제는 계획에 명시된 Obsidian 과거 stage view 11개에 한정됐다.

## 2. 커밋 구성

| 커밋 | 제목 | 규모 | 역할 |
|---|---|---|---|
| `5c322cd` | docs: Stage 11 운영 단순화 계획 수립 | 5 files, +276/-256 | 11A: 진단·계획 owner 신설, handoff 역사 제거 |
| `153758f` | refactor: Stage 11 작업 규칙과 게이트 경량화 | 10 files, +259/-347 | 11B: 상시 규칙·작업 규칙·마스터 게이트 축약 |
| `fef880d` | refactor: Stage 11 활성 문서 표면 축소 | 23 files, +235/-598 | 11C: Obsidian stage view 11개 삭제, failure 정본 축약 |
| `1ff23dd` | docs: Stage 11 최종 보고와 자체 평가 | 2 files, +88/-9 | 11D: 최종 보고·자체 96점 기록 |
| `846b31f` | docs: Stage 11 실행 교훈 규칙 반영 | 4 files, +31/-13 | 11E: 실행 교훈 2건을 기존 규칙 owner에 반영 |

## 3. 변경 내용 분석

### 3.1 세션 시작 표면 경량화 (AGENTS.md, PROJECT_RULES.md, SESSION_HANDOFF.md)

- `SESSION_HANDOFF.md` +28/-281: 완료된 Stage 10의 체크포인트·실패·교차검증 역사를 제거하고 현재 work·blocker·검증 상태·첫 다음 행동만 남겼다. 상세 역사는 Stage 10 owner와 Git 이력이 이미 소유하므로 정보 손실 없는 중복 제거다.
- `PROJECT_RULES.md` +38/-56: 8개 절을 6개 절로 재편. 우선순위에 `user outcome`을 명시적으로 추가(security > protected-data safety > accuracy > user outcome > efficiency)하고, "Process is a safety tool, not a deliverable by itself" 등 자율성 우선 원칙을 상시 정책으로 승격했다. 보호 데이터·비밀정보·backup 불변 경계는 문구만 압축되고 실질 완화는 없다.
- `AGENTS.md` +28/-18: `quick / standard / controlled` 작업 등급 분류를 신설하고, `quick`·`standard` 작업에는 번호 stage·마스터 계획·점수표·서브에이전트·별도 보고서·경계 커밋을 요구하지 않음을 명시했다.

### 3.2 작업 규칙 4종 경량화 (rules/)

- `stage-work.md` +13/-18: 단계 작업 시 마스터·현재 owner 외 완독 요구 제거, 통합 완료 체크포인트 1회로 축소, 채점·독립 검증·별도 보고서·경계 커밋을 "명시적으로 요구될 때만"으로 전환. 검증자 요구를 과거 단계에서 유추하는 것을 금지.
- `version-control.md` +11/-14: Stage 03 이후의 단계별 경계 커밋 상설 정책 서술을 제거하고 "커밋은 사용자 또는 활성 controlled 계획이 경계를 정의할 때만 필요, quick 작업에 micro-commit 금지"로 대체. 승인·보호 경로·검증 경계는 유지.
- `failure-records.md` +20/-20: 실패 승격 기준을 상향 — 재발성·안전/정확성 영향·비자명한 해결·실질 차단을 넘는 실패만 정본화하고, 교정된 일회성 명령·인용·경로 실수는 transient으로 분류.
- `document-work.md` +11/-14: logical batch checkpoint 검증, 최소 직접 검사 원칙으로 정리.

### 3.3 마스터 계획·문서 표면 축소

- `MASTER_BUILD_PLAN.md` +72/-190 (bytes -56.1%): 완료 단계 상세와 공통 게이트 절차를 축약하고 단계 owner 링크 표 중심으로 재편.
- `docs/obsidian/stages/stage-00.md`~`stage-09.md` 11개 파일 삭제(-167줄): 완료 단계의 수동 Obsidian view. 정본인 `docs/build/stage-*.md`와 Git 이력은 보존되며 `fef880d`에서 복구 가능하다.
- `README.md`, `START_HERE.md`, `DOCUMENT_MAP.md`, `OBSIDIAN_REVIEW_CONTRACT.md`: current 진입 경로와 역사 문서를 분리하는 방향으로 축약(합계 약 -177/+131줄).
- `failures/windows-validation-command-assumptions.md` +26/-100 (bytes -83.4%): 재시도 이력 나열을 공통 원인·해결·예방 중심으로 병합.
- `reports/2026-07-22_프로젝트_의도_통합_요구사항_기준서.md` +17/-8: 새 작업 등급 체계와의 정합성 갱신.

### 3.4 코드 변경 (유일한 src 변경)

`src/file_data/maintenance.py` +3/-2: 생성 inventory 문서의 헤더 문구 변경 — "활성 문서 inventory"를 "전체 추적 문서 inventory"로 바꾸고, 완료 stage·시점 보고서를 포함하므로 active owner 목록이 아니며 현재 진입은 `START_HERE.md`를 사용한다는 사용 경계 1줄을 추가. 로직 변경 없음, 생성 문자열만 수정.

### 3.5 신설 문서

`docs/build/stage-11-operating-friction-reduction.md` (+353줄, 유일한 신설 유지 문서): 진단(원인 C1~C6)·계획·단계별 실행 기록(11A~11E)·최종 보고·자체 점수를 단일 owner로 통합. 별도 진단 보고서나 단계별 보고서를 만들지 않는 원칙을 스스로 적용했다.

## 4. 전후 지표 (Stage 11 owner 11D 기록 기준)

| 지표 | 이전 (`2aec62d`) | 이후 (`846b31f`) |
|---|---:|---:|
| startup 3문서 | 38,739 bytes·412줄 | 10,221 bytes·151줄 |
| `SESSION_HANDOFF.md` | 28,258 bytes·302줄 | 2,918 bytes·49줄 |
| 규칙 문서(AGENTS+PROJECT_RULES+rules 6) | 24,697 bytes | 16,186 bytes (-34.5%) |
| `MASTER_BUILD_PLAN.md` | 20,438 bytes·255줄 | 8,968 bytes·137줄 |
| 유지 Markdown | 89개 | 79개 |
| 수동 과거 stage view | 11개 | 0개 |

## 5. 안전 경계 준수 확인

- 삭제는 계획 §5에 exact 명시된 Obsidian stage view 11개뿐이며 Git에서 복구 가능하다.
- `inputs/`, `outputs/`, `backup/` 접근 0건, legacy records·event bytes 불변.
- branch·push·외부 게시 없음. 5개 커밋 모두 사용자 지시의 단계별 경계 커밋 승인 범위 내.
- 규칙 경량화는 절차 강도만 낮추고 보호 데이터·외부 행위·비가역 행위·비밀정보 경계는 어느 파일에서도 완화되지 않았다 (diff 대조로 확인).
- 11D에서 전체 120 tests 회귀 통과, 자체 96점 (차단 결함 0) 기록.

## 6. 평가와 잔여 위험

이 구간은 "문서·규칙이 실제 작업보다 커진" 운영 마찰을 원인 단위로 진단하고, 삭제 대신 중복 제거·등급화·비례 검증으로 해소한 일관된 리팩터링이다. 커밋 분할이 단계(계획→규칙→표면→보고→교훈)와 정확히 대응해 추적성이 좋다.

잔여 위험은 Stage 11 owner §10.5와 동일하다: 완료 역사 문서 79개와 read-only legacy가 남아 있고, 작업 등급 분류가 에이전트 판단에 의존하며, Obsidian UI 직접 확인은 수행되지 않았다. 본 분석에서 추가로 발견된 경계 위반이나 미보고 변경은 없다.

## 7. 제거 내용 손실 감사 (2026-07-24 추가)

제거·축약된 각 항목에 대해 "다른 활성 정본이 같은 사실을 소유하는가"를 diff와 현재 파일 대조로 확인했다. 모든 제거 내용은 Git(`2aec62d`)에서 복구 가능하다.

### 손실 없음 확인

- Obsidian stage view 11개: 전부 링크 색인만 담은 파일로 고유 사실 0건. 정본 `docs/build/stage-*.md` 모두 보존 확인.
- `SESSION_HANDOFF.md`의 Stage 10 역사(-281줄): 실행 기록·검증 결과·finding의 실질 내용은 Stage 10 owner(137KB, 보존 확인)가 소유. 단 체크포인트별 ISO 타임스탬프 10건은 owner에 개별 재현되지 않고 Git 이력에만 남음 — 규칙상 transient 관찰로 허용 범위.
- 요구사항 기준서·failures 탐색 라우팅: 구 handoff의 "주요 owner" 링크는 `DOCUMENT_MAP.md`·`AGENTS.md` 라우팅으로 대체 확인.
- 채점 rubric: 마스터 계획 §6.4에 5개 항목×20점 기본값으로 축약 보존.

### 유의 항목 (활성 표면에서 사라짐, Git으로만 복구 가능)

1. **독립(blind) 검증자 계약 상세** — 구 `PROJECT_RULES.md`·`stage-work.md`가 소유하던 구체 계약(신규 read-only 검증자 1인, 대화 문맥·과거 finding·수정 이력·원하는 판정 비제공, 결과 변경 시 검증자 재사용 금지)이 전부 제거됨. 현행 §6.3은 "필요 시 현재 stage owner가 정의한다"로 위임만 하고 참조 템플릿이 없다. 향후 독립 검증이 필요한 controlled stage는 이 검증 격리 노하우를 Git 이력에서 재발굴해야 한다. **가장 실질적인 지식 손실 후보.**
2. **Windows 검증 실패 사례 30건의 개별 해결책** — 일반화된 원인·예방 규칙은 보존됐으나, 구체 우회법 일부(예: PowerShell 5.1의 `foreach | pipe` 파서 오류 회피, 구형 .NET의 `Path.GetRelativePath` 부재 대응, `rg -g` 패턴 분리)는 일반 원칙("shell·runtime을 추측하지 말 것")으로만 남음. 재발 시 같은 시행착오를 짧게 반복할 수 있으나 정본 취지(원인·예방 중심)에는 부합.
3. **단계 경계 커밋 상설 승인(Stage 03+)** — `version-control.md`에서 제거되고 "사용자·활성 계획이 경계를 정의할 때만 커밋"으로 대체. 손실이 아니라 의도된 정책 전환이지만, 향후 controlled stage는 커밋 권한을 매번 명시적으로 받아야 함을 의미.
4. **승인 재확인 조항** — "대상·범위·위험이 실질 변경되거나 원 승인을 추적할 수 없으면 재확인" 문구가 축약되어 "scope·exclusions·gates 불변 시 상설 승인 유효"라는 간접 표현만 남음. 의미는 대체로 유지되나 명시성이 낮아짐.

### 판정

계획이 명시한 "정보 손실 없는 중복 제거" 원칙은 대체로 지켜졌다. 즉시 조치가 필요한 손실은 없으며, 유일하게 검토할 가치가 있는 것은 유의 항목 1(검증자 계약)로, 향후 독립 검증을 다시 쓸 계획이 있다면 계약 요지를 `rules/` 또는 마스터 계획 §6.3에 3~4줄로 복원하는 것을 권장한다.
