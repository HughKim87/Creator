# 영상 편집 workflow 계약

- 목적: 원본 영상에서 재현 가능한 실제 컷을 설계하고, 의미 검수와 구조 검수를 통과한 Premiere XML을 최소 산출물로 만든다.
- 읽는 시점: 게임플레이·YouTube 영상의 분석, 컷 설계, 사용자 수정본 반영, Premiere XML 생성 작업을 시작할 때.
- 책임: 에이전트는 승인 범위의 분석·편집 판단·검증·복구를 수행하고, 사용자는 창작 방향·보호 데이터 접근·결과 승인을 소유한다.
- 상태: 활성 영상 편집 운영 계약.
- 관련 권위: 루트 `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, `extension/README.md`.

## 1. 범위와 완료 정의

이 계약은 촬영이 끝난 원본 영상의 내용 분석부터 Premiere XML 전달까지를 다룬다. 촬영 전 근거 패키지는 `YOUTUBE_EVIDENCE_PACK_CONTRACT.md`가 별도로 소유한다.

편집 완료는 다음 조건을 모두 만족한 상태다.

1. 선택한 방향과 스파인 기능이 완성 타임라인에서 이해된다.
2. 후보 범위 내부의 2차 편집이 끝났다.
3. 발화·인과·상태·공간·반복을 검수했다.
4. timeline 구조 검증이 통과했다.
5. XML이 원본 미디어만 참조한다.
6. 사용자가 요청한 산출물 외 미디어를 만들지 않았다.

기술적으로 열리는 XML, 목표 길이에 맞는 영상, 자막 cue를 보존한 영상만으로는 완료가 아니다.

## 2. 시작 계약과 보호 경계

보호 데이터에 접근하기 전 다음을 확정한다.

- exact 원본 영상과 선택 자막
- 이번 단계의 목적
- 허용된 산출물 종류와 exact 대상
- 원본은 읽기 전용이며 덮어쓰지 않는다는 조건
- 이번 단계의 종료 조건과 사용자 소유 승인 gate

한 단계의 계획을 이미 승인받았으면 같은 범위에서 반복 확인하지 않는다. 실제 `inputs/`·`outputs/`의 새 항목, 외부 효과, 삭제·이동, 결과를 바꾸는 충돌이 생길 때만 다시 확인한다.

## 3. 네 작업 층

| 층 | 질문 | 주요 결과 | 종료 조건 |
|---|---|---|---|
| 1차 내용 분석 | 원본에 어떤 사건·반응·변화가 있는가 | 방향을 고정하지 않은 내용 지도 | 구성 가능한 근거와 공백을 설명 가능 |
| 2차 상세 분석 | 선택 방향에 무엇을 쓸 것인가 | 후보 범위·스파인 기능·예상 위험 | 각 후보의 유지·축소·제외 이유가 있음 |
| 1차 구성 편집 | 사건 블록을 어떤 순서로 놓을 것인가 | 블록 순서와 대략 범위 | 도입·전개·회수의 인과가 연결됨 |
| 2차 편집 | 후보 내부를 어디서 실제로 자를 것인가 | frame 단위 video/audio timeline | 모든 블록이 microbeat 검수 완료 |

XML은 2차 편집의 전달 형식이다. 후보 범위나 이야기 블록을 clip 하나로 배치한 것은 1차 구성 편집이며, 완성 편집으로 승인할 수 없다.

## 4. 기본 workflow

1. exact 입력·목적·산출물 계약
2. 원본 기술 상태와 자막 신뢰도 확인
3. 방향을 고정하지 않은 1차 내용 분석
4. 촬영본이 뒷받침하는 구성안 최대 3개와 권장안 제시
5. 사용자 방향 확정
6. 선택 방향의 2차 상세 분석
7. 메시지·편집 스파인 확정
8. 1차 구성 편집
9. 후보 범위 내부 2차 편집
10. 의미 gate
11. timeline 구조 gate
12. Premiere XML 생성·구조 대조
13. 사용자 재생 검수와 수정 범위 반영
14. 승인 범위의 최종 산출물 전달

구성 근거가 부족하면 세 안을 억지로 채우지 않는다. 사용자가 계획 승인 뒤 자동 진행을 지시했다면 사용자 소유 창작 방향과 최종 결과를 제외한 내부 단계는 성공 gate에 따라 연속 진행한다.

## 5. 조건부 운영 규칙

`extension/README.md`가 유일한 extension rule router다. 이 계약을 읽은 뒤 현재 행동과 일치하는 rule owner만 읽는다.

| 책임 | 단일 owner | 규칙 |
|---|---|---|
| 입력 범위와 지시 해석 | `rules/video-editing-intake-and-instructions.md` | R01~R03 |
| 원본 계보와 산출물 예산 | `rules/video-editing-artifact-lineage.md` | R04 |
| 스토리·구성·실제 컷 설계 | `rules/video-editing-story-and-cut-design.md` | R05~R07, R09 |
| 발화·화면·전환 경계 | `rules/video-editing-boundary-quality.md` | R08, R10 |
| current revision과 승인 범위 | `rules/video-editing-state-and-approval.md` | R11, R13~R14 |
| 검증 단계와 전달 주장 | `rules/video-editing-validation-and-delivery.md` | R12, R15~R16 |

운영 규칙은 `조건 / 행동 / 예외 / 검증`을 가져야 한다. 작업 버전·프레임 번호·과거 발언·세션 원문·보고서 경로는 규칙에 넣지 않는다. 새 실패가 기존 조건과 겹치면 규칙을 추가하지 않고 기존 owner의 조건·예외·재현 사례를 보강한다.

## 6. 의미 gate와 구조 gate

XML 생성 전에 완성 타임라인 순서로 다음을 검수한다.

- 스파인 기능과 원인·시도·결과가 남아 있는가
- 상태·공간 이동과 행동의 최소 연결이 있는가
- 후보 내부 2차 편집과 긴 clip의 유지 근거가 있는가
- 말 조각·미완성 생각·진행 없는 반복이 남지 않았는가
- 화면 점프·밝기 전환·동작 불연속을 확인했는가

의미 gate는 AI 사전감사다. 사용자가 완성본의 첫 결함 탐지자가 되도록 넘기지 않는다.

구조 validator는 frame 범위, 길이 식, track 연속성, audio gap, A/V 총길이, 원본 범위, 명시적 시간 역전, source lineage만 판정한다. 스파인 적절성, 발화 자연스러움, 공간 연결, 리듬, 밝기·RMS 합격값은 자동 승인하지 않는다.

## 7. 도구와 XML 경계

- SRT 검증·정리는 strict UTF-8, cue 순서·겹침·미디어 범위를 확인하고 명시된 timestamp 보정·제외만 새 파일에 적용한다. 원본 hash와 cue 본문은 바꾸지 않는다.
- legacy CSV importer는 9열 frame·gap·순서를 그대로 이관하고 의미 역할을 추론하지 않는다. 결과는 `unclassified`와 `semantic_gate: pending`이므로 별도 의미 검수 전 XML을 만들 수 없다.
- timeline 오류는 가능한 범위에서 모두 수집하며, 각 issue는 `code / message / track / clip_id / index`를 가진다.
- XML adapter는 원본 source reference 하나, 결정론적 clip·link 구조, frame·gap·예외, 비덮어쓰기, XML 단일 산출물을 지킨다.

| profile | 용도 | 상태 경계 |
|---|---|---|
| `sequence-v5` | 기존 경량 sequence XML, 기본값 | 기존 byte 호환 유지 |
| `premiere-cs6-v4` | project·bin·masterclip을 포함한 CS6용 FCP XML v4 | 구조 검증이며 실제 Premiere import·재생 검수는 별도 |

## 8. 상태·승인·산출물 수명

- current artifact와 source fingerprint는 하나의 owner가 소유한다.
- 사용자 승인은 결과와 exact 범위에 붙으며 source·사용자 수정·인접 경계 변경 시 해당 범위만 무효화한다.
- 기술 통과는 창작 방향 승인, 앱 import 검수, 사용자 재생 승인을 대체하지 않는다.

| 종류 | 기본 수명 | 원칙 |
|---|---|---|
| 운영 계약·rule·schema·검증 코드 | 유지 | 유일 owner와 회귀가 있어야 함 |
| 현재 작업 brief·handoff | 현재 상태 동안 유지 | 완료 이력과 원문을 복제하지 않음 |
| timeline·XML·사용자 deliverable | 보호 파생물 | exact 항목·목적 승인, Git 제외 |
| 분석 cache·RMS 배열·임시 frame·재전사 | disposable runtime | 재생성 가능, 기본 비추적 |
| 세션 원문·버전별 중복 보고 | 운영 비의존 | 외부 백업 또는 Git 이력, 활성 owner에서 제외 |

규칙으로 승격하지 않은 수치·자동화·skill 후보는 `docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md`만 소유하며 일반 편집의 기본 읽기 대상이 아니다.

### 과거 영상 자료의 domain 지식 환류

과거 영상 spine·방향안·검수 문서·분석 파생물을 추출하거나 정리할 때 범용 절차는 상위 router가 선택한 foundation owner가 담당한다. 이 계약은 추출 결과 중 영상 편집 domain의 배치만 소유한다.

| 추출 내용 | 영상 domain owner |
|---|---|
| 독립 영상에서 반복되고 일반화된 편집 조건 | R01~R16의 가장 좁은 기존 rule owner |
| 한 영상에서만 확인된 판단·수치·자동화·skill 가능성 | `VIDEO_EDITING_RULE_CANDIDATES.md`의 기존 후보 또는 task evidence |
| exact frame·파일명·해시·길이·영상별 사용자 승인 | 원래 검수·보호 자료 또는 현재 영상 task owner |
| 현재 revision·승인 범위·source fingerprint | 상태·승인 rule이 선택한 current owner |
| 세션 원문·버전별 중복 보고·완료 명령 | active owner로 승격하지 않고 Git 이력 또는 사용자 요청 보고서 |

같은 영상 spine의 직접 연결 자료만 목적 범위에서 다루며 sibling 자료를 넓게 열거하지 않는다. 단일 영상 사실을 전역 규칙으로 승격하거나, 범용 파일 절차를 extension 규칙으로 복제하지 않는다.

## 9. 실행점

보호 데이터가 없는 기본 구조 검증:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = ((Resolve-Path 'core/src').Path, (Resolve-Path 'extension/src').Path -join ';')
python -m video_editing validate `
  --timeline-json extension/examples/video-edit-timeline-v1.json
```

자막 검증·정리, legacy CSV 이관, XML 생성:

```powershell
python -m video_editing subtitle-validate --source <승인된-source.srt>
python -m video_editing subtitle-clean `
  --source <승인된-source.srt> `
  --destination <승인된-cleaned.srt> `
  --media-end-ms <정수> `
  --start <cue=ms> `
  --end <cue=ms> `
  --exclude <cue>
python -m video_editing import-csv `
  --video-csv <승인된-video.csv> `
  --audio-csv <승인된-audio.csv> `
  --output <승인된-timeline.json> `
  <source와 sequence metadata>
python -m video_editing premiere-xml `
  --timeline-json <승인된-timeline.json> `
  --output <승인된-output.xml> `
  --profile premiere-cs6-v4
```

실제 `inputs/`·`outputs/`를 사용하는 명령은 사용자가 exact 항목과 목적을 승인한 작업에서만 실행한다.

## 10. Acceptance

1. `extension/README.md`가 모든 활성 `extension/rules/*.md`를 정확히 한 번 라우팅한다.
2. 운영 규칙 R01~R16과 재현 사례 TC01~TC16은 각 rule owner에 정확히 한 번 존재한다.
3. 기존 TC01~TC12의 기대 판정이 이관 전과 동일하다.
4. TC13~TC16이 current revision 동결, 상태 충돌 중단, 검증 주장 제한, validator 계층 분리를 재현한다.
5. 정상 timeline은 결정론적 진단을 반환한다.
6. 의미 gate 미통과 또는 구조 오류는 XML을 만들지 않는다.
7. 정상 timeline은 원본 reference 하나를 가진 XML 하나만 만든다.
8. XML의 clip 수·frame 범위·audio gap이 timeline과 일치한다.
9. SRT·CSV 원본 hash가 유지되고 실패 시 부분 출력이 없다.
10. legacy import는 의미 gate를 통과시키지 않는다.
11. `sequence-v5` byte 회귀와 `premiere-cs6-v4` 구조 회귀가 함께 통과한다.
12. Core와 Extension 전체 회귀가 통과한다.
