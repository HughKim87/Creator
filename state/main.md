# Creator main 공통 개발 상태

- 목적: 단일 workspace와 공통 구현 유지보수의 현재 상태를 소유한다.
- 읽는 시점: 시작 문서 뒤.
- 책임: main 유지보수 세션과 사용자.
- 상태: 공용 runtime과 job 분리 구조 운영. 개별 작업은 해당 job의 상태를 따른다.
- handoff mode: same-workspace.
- 관련 권위: PROJECT_RULES.md, extension/docs/WORKSPACE.md.

## 현재 단계

게임플레이영상제작 스킬 `.agents/skills/edit-gameplay-video/`의 기존 컷 workflow에 후편집 모드를 추가했다. references/post-production.md가 기준본·프로필·큐시트→최소 샘플→전체 레이어→선택적 아웃트로·전체 SRT→검수 실행을 설명한다. scripts/postprocess.py가 원본 기반 자막/강조·정지 이미지·확대·음량 마감, hash 기반 부분 cache, exact 지정 완성본의 packet 보존 결합과 SRT 결합을 구현한다. 실제 워독스 미디어는 읽거나 재편집하지 않았다. 스킬·도구·규칙·검사 변경을 사용자 승인에 따라 로컬 커밋으로 보존하며 push는 범위에 포함하지 않는다.

기존 R19–R21은 중복하지 않고 실행 절차에서 재사용했다. R04에 사용자 지정 완성본의 단순 아웃트로 결합 예외만, R22에 조립 계획과 결합 후 전체 길이·음량·true peak 재측정만 보강했다. 새 규칙·route·Core 변경은 없다. 기존 후편집 사례 TC37/TC38이 다른 owner와 중복된 것을 TC45/TC46으로 정리하고 신규 TC43/TC44를 추가했다. 구조 검사 ID 집합도 갱신했다.

기존 E2·E3 보고는 extension/docs/reports/SESSION_CLOSE_EXTENSION_2026-10-22.md, 미구현 Core 제안은 extension/docs/reports/CORE_ARTIFACT_STORAGE_PROPOSAL_2026-10-22.md가 소유하는 이전 작업 근거다. 활성 설계는 없다.

공용 도구는 extension/.runtime에서 재사용하며 운영 안내는 extension/docs/WORKSPACE.md가 소유한다. 프로젝트별 자료와 상태는 extension/jobs/<job-id>/에 둔다. 공통 유지보수와 개별 영상 제작의 상태를 분리하며, 새 작업 시작 시 실제 Git 상태를 확인한다.

## 직전 게이트

2026-10-22 검증: 신규 후편집 12개, 기존 컷 9개, editorial-state·검토 전달 26개 pass(47개). 규칙 route·중복·형태 구조 검사 13개도 pass, 총 60개. 합성 영상에서 libass 강조 대체·실제 폭·이미지 등장/종료·확대 화면·레이어 없는 프레임 오차·chunk 재사용과 부분 변경·원본/SRT 불변·손상 cache 및 source drift 차단·30→60fps/타임베이스 결합·본편 coded packet 동일성·전체 loudness/true peak·피크 실패 시 미게시·SRT CLI offset/비덮어쓰기·job context 경계를 확인했다. Windows sandbox의 hardlink 차단은 테스트 명령의 승인된 확장 실행으로 검증했으며 구현을 약화하지 않았다.

quick_validate는 기존 python-deps의 PyYAML을 재사용해 pass. strict UTF-8·로컬 Markdown 참조·Python 구문·diff whitespace 검사 pass. 실제 게임 영상 재미·연속 A/V·청취·색 품질의 의미 검수 및 실제 job runner 전체 실행은 not_run이다. 도구 반환은 semantic/direct_listening not_run, user_approval pending으로 유지한다.

상태 안내를 실제 Git 상태와 대조하고, 이미 정리된 미커밋 삭제·문서 수정이 남아 있다는 안내를 제거했다. 이는 실제 영상 제작·모델 추론 검증이 아니다.

## 승인 상태

현재 요청은 검증된 후편집 스킬·실행 도구·회귀 검사·규칙 보강 변경의 로컬 stage/commit이다. 변경은 스킬·검사·R04/R22와 이 상태 문서에 한정했다. Core·워독스 미디어·모델은 변경하지 않았다. 실제 영상 제작·새 설치·외부 전송·push는 이 승인에 포함하지 않는다. 앞선 session-close 개선 실행은 사용자 직접 정리 후 재개 결정에 따라 별도 보류 상태다.

E1의 현재 상태 안내 정정과 단계별 로컬 커밋·임시 설계 정리·저장소 밖 종료 보고가 승인됐다. 영상 제작·자료 처분·설치·push·외부 게시·Core 변경은 이 승인에 포함하지 않는다.

## 차단

확인된 공통 유지보수 차단은 없다. 새 변경이나 job별 자료·도구의 미충족 여부는 해당 작업 시작 시 다시 확인한다.

## 알려진 위험

새 제작 전체 실행·실모델 추론·Premiere 재생·로그인은 not_run이다. 두 TTS 가상환경의 기반 Python은 Creator 밖의 Codex 기본 runtime을 사용한다. 공용 코드·도구가 있다는 사실만으로 개별 job의 원본·제작 기록·실행 준비가 완전하다고 판단하지 않는다. 전용 앱의 실행·설정 참조 정리는 이 상태 문서 정정의 검증 범위가 아니다.

신규 스킬의 실제 게임 영상 전체 실행·다른 게임의 일반화 평가는 not_run이다. 후편집은 Windows mandatory lock, 단일 정수 CFR·정수 샘플 경계·mono/stereo·식별된 SDR BT.709와 정사각 픽셀에 한정한다. append는 본편 H.264 B-frame 없음·동일 geometry/audio format을 요구하며 본편 음성은 재인코딩한다. 다중 원본/VFR/HDR·효과음/음악 믹스·카드에는 별도 검증 adapter가 필요하다. 선언된 HUD 보호 사각형 검사만으로 전체 가림 검수를 통과시키지 않는다. job runner는 dirty 공통 코드를 거부하므로 실제 job 실행 전 기존 Git 정책에 따라 변경을 정리해야 하며 스킬이 자동 커밋·우회하지 않는다. 상위 계약의 필수 방향/calibration 승인은 자동 추천으로 대체하지 않는다.

## 첫 다음 행동

1. git log -1 --stat와 git status --short --ignore-submodules=all로 후편집 변경의 로컬 복구 지점과 이후 변경을 확인한다. 원격 push는 별도 승인 전 수행하지 않는다.
2. 다음 게임 편집 요청에서는 `.agents/skills/edit-gameplay-video/SKILL.md`의 준비 단계부터 실행한다. 실제 원본·출력·프로필·가능한 A/V 검수 방법을 확인한 뒤 기존 job 또는 새 명시 job을 선택한다.
3. 도구는 scripts/creator_job.py runtime --component <component-id>로 조회하고 코드 상태·잠금 조건을 충족한 job runner에서 실행한다. 원본 관찰·이야기 설계의 실제 품질을 평가하고 자동 검사와 의미 검수 결과를 분리한다.
