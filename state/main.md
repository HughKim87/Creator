# Creator main 공통 개발 상태

- 목적: 단일 workspace와 공통 구현 유지보수의 현재 상태를 소유한다.
- 읽는 시점: 시작 문서 뒤.
- 책임: main 유지보수 세션과 사용자.
- 상태: 공용 runtime과 job 분리 구조 운영. 개별 작업은 해당 job의 상태를 따른다.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md, extension/docs/WORKSPACE.md.

## 현재 단계

승인된 E2·E3의 원본 발췌·MP4/XML 검수 보고 절차를 반영하고 검증했다. 이번 전용 임시 설계를 종료했으며 활성 설계는 없다. Core 구현은 제외하며 저장 원칙 제안서와 개선 보고서를 내부 보존하는 단계다.

공용 도구는 extension/.runtime에서 재사용하며 운영 안내는 extension/docs/WORKSPACE.md가 소유한다. 프로젝트별 자료와 상태는 extension/jobs/<job-id>/에 둔다. 공통 유지보수와 개별 영상 제작의 상태를 분리하며, 새 작업 시작 시 실제 Git 상태를 확인한다.

## 직전 게이트

E3: 검수 후보 전달 회귀 7개, ASR recorded 허용·speech passed 승격 거부·semantic not_run 보존 대조를 통과했다. 자동 사전검수·실제 청취·기술 검사 요청 문맥을 대조했다. 실제 영상 직접 청취·연속 재생과 독립 Agent 재현은 not_run이다.

상태 안내를 실제 Git 상태와 대조하고, 이미 정리된 미커밋 삭제·문서 수정이 남아 있다는 안내를 제거했다. 이는 실제 영상 제작·모델 추론 검증이 아니다.

## 승인 상태

이번 세션의 E2·E3 Extension 개선, 기존 관련 검사, 단계별 로컬 커밋과 이번 전용 임시 설계 정리 및 프로젝트 내부 보고가 승인됐다. Core 변경·gitlink 갱신·실제 영상 재편집·직접 청취 통과 선언·설치·외부 게시·push는 제외한다.

E1의 현재 상태 안내 정정과 단계별 로컬 커밋·임시 설계 정리·저장소 밖 종료 보고가 승인됐다. 영상 제작·자료 처분·설치·push·외부 게시·Core 변경은 이 승인에 포함하지 않는다.

## 차단

확인된 공통 유지보수 차단은 없다. 새 변경이나 job별 자료·도구의 미충족 여부는 해당 작업 시작 시 다시 확인한다.

## 알려진 위험

새 제작 전체 실행·실모델 추론·Premiere 재생·로그인은 not_run이다. 두 TTS 가상환경의 기반 Python은 Creator 밖의 Codex 기본 runtime을 사용한다. 공용 코드·도구가 있다는 사실만으로 개별 job의 원본·제작 기록·실행 준비가 완전하다고 판단하지 않는다. 전용 앱의 실행·설정 참조 정리는 이 상태 문서 정정의 검증 범위가 아니다.

## 첫 다음 행동

1. extension/docs/reports/에 Core 저장 원칙 제안서와 E2·E3 개선 보고서를 작성하고 문서·링크·Core 불변·최종 Git 상태를 대조한다.

1. git status --short --ignore-submodules=all로 현재 변경을 확인하고, 공통 코드 변경이 있으면 해당 변경의 소유자와 처리 범위를 먼저 확정한다.
2. 도구는 scripts/creator_job.py runtime --component <component-id>로 현재 경로를 조회한다.
3. 기존 작업은 extension/jobs/<job-id>/state.md와 실제 자료를 대조한다. 새 job 생성이 필요할 때만 scripts/creator_job.py init --job <job-id>를 사용하며, 제작은 해당 작업의 지시와 범위가 확정된 뒤 job runner 안에서 실행한다.
