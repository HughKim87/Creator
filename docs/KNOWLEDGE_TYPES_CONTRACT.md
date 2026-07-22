# 지식 유형 계약과 사용법

- 목적: 작업 기록과 분리된 장기 재사용 데이터를 출처, 단일 지식 주장, 결정, 실패 지식 projection으로 명시적으로 생성·검증한다.
- 읽는 시점: source·knowledge·decision·failure_knowledge record를 생성·조회·검증하거나 유형 간 책임을 판단할 때.
- 책임: `src/file_data/knowledge.py`가 의미 검증과 참조 무결성, `schemas/*-payload-v1.schema.json`이 필드 구조, `failures/*.md`가 실패 사례 본문 정본을 소유한다.
- 상태: Stage 05 활성 계약.
- 선행 계약: [공통 기록 I/O](RECORD_IO_CONTRACT.md), [작업 기록·현재 상태](WORK_STATE_CONTRACT.md).

## 유형과 정본 책임

| record type | 소유 정보 | 소유하지 않는 정보 |
|---|---|---|
| `source` | 출처 종류·위치·관찰 시각·확인 상태·증거 역할·버전 또는 hash | 원문 전체, 보호 데이터 사본, 신뢰 점수 |
| `knowledge` | 한 줄의 주요 주장 하나·분류·적용 범위·source 참조·검증 상태와 주체 | 작업 전문, 복수 주장, 태그·검색 점수·검토 일정 |
| `decision` | 문제·요구조건·검토 선택지·선택·이유·영향·source·승인·결정 시각 | 현재 실행 상태, 승인되지 않은 대리 결정 |
| `failure_knowledge` | `failures/*.md` 정본을 구조적으로 읽은 hash 고정 projection | 실패 사례 본문의 정본, 원인 미확인·임시 우회 사례 |

작업 요청·event·snapshot은 장기 지식 record로 복제하지 않는다. 지식은 명시적 create/import 명령에서만 생성되며 자동 추출·승격은 없다.

## 05A 출처 기록

허용 종류는 `local_document`, `local_data`, `command_result`, `web_page`, `user_statement`다. 증거 역할은 `primary`, `supporting`, `contextual`, 확인 상태는 `observed`, `verified`, `unavailable`이다.

- 로컬 출처는 정규화된 프로젝트 상대 경로만 허용하고 `backup`, `inputs`, `outputs`, `.git`, `.obsidian`을 거부한다.
- 로컬 파일 생성 시 실제 bytes의 SHA-256을 계산해 `verified`로 저장한다.
- `source-show`와 `source-list`는 당시 관찰 record를 읽는다. `source-verify`는 현재 bytes를 다시 계산하며 저장 hash와 다르면 `source_integrity`로 실패한다.
- web source는 `http` 또는 `https` locator만 기록한다. Stage 05는 외부 내용을 가져오거나 권위를 자동 판정하지 않는다.
- user statement는 원문을 복사하지 않고 승인된 `request://...` 참조만 기록할 수 있다.

## 05B 지식 항목

분류는 `fact`, `inference`, `procedure`, `constraint`, 상태는 `candidate`, `verified`다.

- `statement`는 줄바꿈 없는 500자 이하 문자열 하나다. 의미상 복수 주장은 사용자 검토에서 분리한다.
- source ID는 최소 한 개이며 모두 존재하는 `source` record여야 한다.
- `unavailable` source는 지식 생성에 사용할 수 없다.
- `candidate`는 `verified_by`를 가질 수 없고 `verified`는 검증 주체가 필수다.
- 참조한 로컬 source가 바뀌어도 당시 지식 record 조회는 보존되지만 `source-verify`는 실패한다. 현재도 유효한지의 갱신·대체 판정은 Stage 06이 소유한다.

## 05C 결정 기록

결정은 최소 두 선택지를 검토하고 `selected_option`이 그 label 중 하나여야 한다. 요구조건·영향·source가 각각 최소 하나 필요하다.

- 승인 종류는 `user`, `standing_policy`, `agent_in_scope`다.
- `requires_user_approval=true`이면 `user` 또는 `standing_policy`만 허용한다.
- `approved_by`와 `decided_at`을 항상 기록한다.
- 결정 시각은 record 생성 시각보다 미래일 수 없다.
- 설치·외부 게시·보호 데이터·삭제·이동·비용·실질적 범위 확대는 기존 상시 안전 경계를 그대로 따른다.

## 05D 실패 지식 projection

사용자 요구에 따라 `failures/*.md`가 해결된 실패 사례 본문의 정본으로 계속 남는다. `failure_knowledge`는 이를 대체하지 않고 다음 필드를 구조화한 파생 record다.

- 제목, 정본 문서 경로와 SHA-256
- 증상, 적용 범위, 확인된 원인
- 해결, 검증, 재사용 규칙
- source ID, projection 주체·시각·`resolved` 상태

import는 `failures/README.md`를 제외하고 상태에 `해결`이 있으며 `증상`, `확인된 원인`, `해결과 검증`, `재사용 규칙` 절이 모두 있는 사례만 받는다. `해결과 검증` 절의 첫 목록 항목을 해결, 나머지를 검증 근거로 projection한다. 읽을 때 정본 bytes hash, source record, 구조화 필드를 모두 다시 대조하며 하나라도 다르면 사용을 거부한다.

정본 Markdown이 갱신되면 기존 projection은 즉시 stale이다. Stage 05 record 자체는 수정하지 않으며 [Stage 06 수명주기](KNOWLEDGE_LIFECYCLE_CONTRACT.md)가 새 source·projection을 만들고 옛 record를 `superseded`로 보존한다.

## 승인된 진입점

- Library: `file_data.KnowledgeService`
- Source CLI: `source-create`, `source-show`, `source-list`, `source-verify`
- Knowledge CLI: `knowledge-create`, `knowledge-show`, `knowledge-list`
- Decision CLI: `decision-create`, `decision-show`, `decision-list`
- Failure CLI: `failure-import`, `failure-show`, `failure-list`

복합 decision payload는 PowerShell에서 UTF-8 stdin과 `--payload-stdin`을 사용한다. 모든 record는 common-record v1 외피와 `data/records/<id>.json` 단일 주소를 재사용한다.

## 구조 계약

- `schemas/source-payload-v1.schema.json`
- `schemas/knowledge-payload-v1.schema.json`
- `schemas/decision-payload-v1.schema.json`
- `schemas/failure-knowledge-payload-v1.schema.json`

Python 검증기가 구조 스키마보다 강한 교차 필드·참조·hash 검증을 수행한다. 테스트는 두 필드 집합과 enum이 일치하는지 확인한다.

Stage 05 완료 시 검증된 실제 예시는 source 23건, knowledge 1건, decision 1건, failure_knowledge 21건이다. 이 개수는 완료 시점 근거이며 동적 현재 상태의 정본은 아니다.

## Stage 05 제외와 후속

- record 검토·대체·폐기·충돌·사건 기반 검토 트리거는 [Stage 06 수명주기](KNOWLEDGE_LIFECYCLE_CONTRACT.md)가 소유한다.
- 검색·순위·관계 탐색·컨텍스트 조립은 Stage 07 범위다.
- stale projection 재생성·일괄 유지보수는 Stage 08 범위다.
- 도메인 전용 필드와 영상 제작 연결은 Stage 09 전까지 도입하지 않는다.
