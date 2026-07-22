# 선택적 읽기·컨텍스트 패키지 계약

- 목적: 현재 작업에 필요한 활성 문서와 current 지식 record만 직접 선택·필터·단순 문자열 후보로 구성하고 선택·제외 이유와 크기를 함께 보여준다.
- 읽는 시점: 전체 문서 읽기 없이 작업 컨텍스트를 만들거나 대표 선택 평가를 실행할 때.
- 책임: `ContextService`가 선택·검증·크기 제한·fingerprint를, 원 문서와 Stage 05 record가 내용 정본을, lifecycle이 현재 사용 가능 상태를 소유한다.
- 상태: Stage 07 활성 계약.
- 선행 계약: [지식 수명주기](KNOWLEDGE_LIFECYCLE_CONTRACT.md), [정보·문서 책임 구조](INFORMATION_ARCHITECTURE.md).

## 선택 우선순위

1. 사용자가 지정한 정확한 record ID와 명시 문서 경로
2. 실제 payload에 있는 record type·lifecycle state·knowledge scope·source evidence role 필터
3. 위 방법이 부족할 때 current record의 승인 필드만 대상으로 하는 대소문자 비구분 단순 부분 문자열 후보

단순 문자열 결과는 후보일 뿐 실행 권위가 아니다. package에 들어가기 전에 lifecycle current 여부, source 참조, 범위, 크기 제한을 다시 확인한다. FTS·SQLite·벡터·그래프·관련성 점수는 사용하지 않는다.

## 직접 문서와 record

- 문서는 프로젝트 상대 경로로만 지정하고 strict UTF-8·NUL 부재·실제 파일 여부를 확인한다.
- `backup`, `inputs`, `outputs`, `.git`, `.obsidian` segment는 경로 해석 전에 거부한다.
- record는 lifecycle에 등록된 source·knowledge·decision·failure_knowledge만 선택한다.
- 직접 지정한 record가 candidate·review_required·superseded·rejected·retired이면 내용에 포함하지 않고 상태와 제외 이유를 남긴다.
- current record가 참조하는 source ID, evidence role, source lifecycle 상태를 함께 표시한다.

## 구조화 필터와 단순 검색

허용 필터는 실제 Stage 05~06 필드 네 개뿐이다.

| 필터 | 값·동작 |
|---|---|
| `record_type` | source, knowledge, decision, failure_knowledge |
| `state` | lifecycle 여섯 상태. 생략 시 current |
| `scope` | knowledge payload의 exact scope만 비교 |
| `evidence_role` | 참조 source의 primary, supporting, contextual |

검색 필드는 source locator, knowledge statement·scope·classification, decision problem·rationale·selected option, failure title·symptom·confirmed cause·prevention이다. 검색은 항상 current record로 다시 제한한다. 검색 자체가 정상 실행돼 match가 0건인 결과와 입력·I/O·검증 실패는 CLI 성공·오류 상태로 구분한다.

## 비영구 context package

package v1은 다음을 포함한다.

- 작업 목적과 선택 설정
- 선택된 문서 ref 또는 record ID·유형·상태
- 항목별 선택 이유와 source 상태
- 최대 20개의 결정론적 제외 상세와 사유별 전체 개수
- 선택 content의 Unicode 문자 수·UTF-8 byte 수
- 전체 읽기 기준선 문자 수와 절감률
- 모든 필드의 canonical JSON에서 계산한 SHA-256 fingerprint

package에는 생성 시각과 무작위 ID를 넣지 않는다. 같은 정본·요청·설정은 byte로 같은 논리 package와 fingerprint를 만든다. package는 반환만 하고 `data/`에 저장하지 않으므로 새 정본이 아니다.

## 크기와 기준선

- 기본·대표 평가 최대 크기는 선택 content 12,000 Unicode 문자다.
- 목표는 보호·역사 경계를 제외한 전체 활성 Markdown 문자 기준선보다 85% 이상 작게 구성하는 것이다.
- 모델별 tokenizer를 새 의존성으로 고정하지 않는다. Unicode 문자 수를 기본 비용 지표, UTF-8 byte를 보조 지표로 사용한다.
- 직접 지정한 필수 항목만으로 한도를 넘으면 자르지 않고 `context limit` 실패를 반환한다.
- 검색 후보가 한도를 넘으면 해당 후보를 제외하고 `size_limit` 이유를 남긴다.

## 대표 평가 계약

| 평가 | 직접·검색 입력 | 필수 결과 | 금지 결과 |
|---|---|---|---|
| 기존 지식 읽기 | 기존 current knowledge ID | 정확한 knowledge 1건과 source 상태 | 대체된 옛 knowledge, 무관 record |
| 새 지식 다시 읽기 | Stage 07에서 만든 current knowledge의 고유 문구 | 새 knowledge 1건 | candidate·superseded·보호 경로 |
| 실패 경험 재사용 | 해결된 Windows UTF-8 pipe 실패의 고유 문구 | current failure_knowledge와 prevention | stale 옛 projection, 무관 실패 |

세 평가 모두 필수 누락 0, 금지 결과 0이어야 한다. 직접 선택의 무관 결과 허용은 0, 단순 검색 후보는 최대 1건이다. 실패하면 단순 검색 필드·질의를 먼저 보정하고, 그것으로 해결되지 않는 증거가 있을 때만 다음 검색 기술을 제안한다.

## 승인된 진입점

- Library: `file_data.ContextService`
- CLI: `context-build`, `context-search`, `context-filter`, `context-baseline`
- 구조 계약: `schemas/context-package-v1.schema.json`

CLI build는 PowerShell에서 UTF-8 stdin과 `--request-stdin`을 사용한다. 직접 문서 목록은 호출자가 현재 작업 라우팅에 따라 명시하며 서비스가 저장소 전체를 자동 로딩하지 않는다.

## 제외와 후속

- 컨텍스트 package 저장·자동 지식 승격·보호 데이터 색인·보고서 기본 로딩은 금지한다.
- 최신성·중복·재생성·비용 관측과 검증된 반복 실행은 [Stage 08 유지보수 계약](MAINTENANCE_AUTOMATION_CONTRACT.md)이 소유한다.
- 도메인 태그·추천·영상 제작 입력은 Stage 09 범위다.
