# Stage 00 골든 픽스처 계획

## 1. 원칙

골든 기준은 **합성 기술 픽스처**와 **외부 실제 파일럿**을 분리한다. 이 문서는 계획만
정의하며 영상·음성·MP4를 생성하지 않았다. 실제 미디어의 경로나 내용은 기록하지
않는다.

- Git 허용: 생성 스크립트, 작은 CSV/JSON/SRT 계약, 기대 메타데이터, 정규화된 텍스트
- Git 금지: 생성된 영상·음성, 실제 파일럿, Premiere 렌더, 사용자 미디어 경로
- 외부 실제 파일럿 기록: 사용자 승인 작업 공간에서만 논리 ID, SHA-256, 길이,
  코덱/컨테이너, 프레임레이트, 오디오 레이아웃, 승인자 provenance를 관리한다. 실제
  값은 이 프레임워크 저장소나 Stage 보고서에 복사하지 않는다.
- 기술 성공과 사람 A/V 승인은 별도 결과로 저장

## 2. 합성 기술 픽스처

| ID | 생성물·입력 | 검증할 보존 계약 | 기대 결과 |
|---|---|---|---|
| TECH-WRAP-EXIT-07 | 종료 코드 `7`만 내는 인라인 자식 | 직접 Python 대 래퍼 종료 코드 | 두 호출 모두 `7`; stdout/stderr와 실제 코드 별도 기록 |
| TECH-SOURCE-ID-A | 결정적 짧은 합성 A/V와 복제·내용변경 변형 | `source_id`, 원본 콘텐츠 지문, 변경 혼합 거부 | 동일 바이트는 동일 ID 재사용, 내용 변경은 크기/mtime과 무관하게 거부 |
| TECH-FRAME-A | 고정 FPS·고정 길이 색상/타임코드 영상 | 절대 source time/frame, 이름, JPEG 완전성, manifest hash, 고해상도 재사용 | 기대 프레임 번호·밀리초·SHA와 일치, 재실행은 새 파일 0 |
| TECH-ASSET-CRASH-A | 프레임 생성/manifest 승격 사이 강제 중단 | 파일-상태 crash consistency | 복구 후 orphan이 current로 승격되지 않고 재실행 가능 |
| TECH-SYNC-A | 결정적 PCM 발화/무음 경계와 SRT·cutlist | VAD/RMS/자막 경계, advisory와 gate 구분 | 미리 지정한 안전/위험 경계와 허용 오차 내 일치 |
| TECH-XML-A | 동일 FPS/채널 두 소스와 multi-sequence/cutaway CSV | source/timeline 프레임, 순서, 트랙, source time | 정규화 XML 구조와 기대 프레임 값 일치 |
| TECH-XML-MISMATCH | FPS·오디오 채널 불일치 소스 | 혼합 미디어 거부, ffprobe 결손 fail-closed | 명시적 비정상 코드이며 XML 미생성 |
| TECH-QUALITY-A | `CLEAR`, `REVIEW`, `WAIVED`, 잘못된 waiver CSV | 편집 품질 findings와 게이트 종료 코드 | 상태·코드·정당화가 기대값과 일치; gate 모드는 REVIEW를 성공 처리하지 않음 |
| TECH-WORKFLOW-A | 닫힌/허용/승인 위조/근거 결손 JSON | `default_deny`, 바로 전 단계, 근거, generation lock | 닫힌 상태 audit은 coherent, 승인 없는 전이는 차단, 위조 provenance는 거부 |
| TECH-MEMORY-A | event batch·중복·실패 edge·승인 이벤트 | 트랜잭션, 멱등성, revision DAG, working/approved baseline | 배치 전체 롤백, 동일 event skip, 승인 provenance 없는 approved 거부 |
| TECH-REMUX-A | 짧은 합성 MKV, 손상 입력, 기존 출력 | stream copy, duration/codec 보존, 실패 집계, overwrite 금지 | 정상 stream 메타데이터 동등; 손상 입력은 최종 비정상 코드 |
| TECH-ROOT-A | 승인된 legacy SHA의 독립 worktree | 래퍼 루트 탐지, Git safe.directory, doccheck/projectctl | 계산 루트와 Git 루트 동일, 중첩 backup 경로 비사용 |

합성 A/V 생성은 향후 승인된 단계에서 FFmpeg 명령을 스크립트로 고정하고 버전,
명령행, seed, 기대 ffprobe JSON을 함께 보존한다. MP4가 필요한 경우 그 실행 요청에서
사용자에게 별도 승인을 받는다.

## 3. 외부 실제 파일럿

실제 파일럿은 Git 밖 사용자 승인 작업 공간에서만 수행한다. 경로·제목·대사·화면
내용은 보고서에 기록하지 않는다.

| 논리 ID | 대표 목적 | 최소 메타데이터 | 승인 게이트 |
|---|---|---|---|
| `PILOT-DIALOGUE-01` | 발화 경계·자막·L/J-cut·연속 음성 | source hash, duration, video/audio codec, fps, channels | 사용자 실제 연속 A/V 승인 |
| `PILOT-GAMEPLAY-01` | 화면-음성 인과, cutaway, 리듬 변화 | source hash, duration, codec, fps, channels | 사용자 메시지·리듬·A/V 승인 |
| `PILOT-LONGFORM-01` | 후반 밀도, 다중 시퀀스, 긴 구간 안정성 | source hash, duration, codec, fps, channels | 품질 감사 해소와 사용자 전체 재생 승인 |

각 파일럿 레코드에는 다음 provenance가 필요하다.

1. 논리 `source_id`와 SHA-256
2. legacy 기준의 커밋/SHA와 실행 모드(`direct_shadow` 또는 승인된 동결 기준)
3. 도구·FFmpeg·Premiere 버전
4. 생성 산출물의 SHA-256과 정규화 메타데이터
5. 자동 검사 결과와 실제 종료 코드
6. agent 사전 A/V 관찰과 사용자 A/V 승인 분리
7. 승인자 식별자, 승인 시각, 승인 범위, 증거 참조
8. 승인되지 않은 차이와 롤백 지점

## 4. 비교 산출물

- 프레임/자산: source time, frame number, width, asset hash, manifest row
- sync: 경계별 safe/risk, 제안 시각, 오차 허용값, 도구 의존성 버전
- Premiere XML: 정규화 XML, sequence/track/clip frame map, ffprobe 입력 메타데이터
- 품질 감사: finding code/status/justification의 정렬된 JSON 또는 Markdown 표
- workflow/memory: 실제 CLI 종료 코드, blockers/errors, revision/baseline/event snapshot
- remux: 입력/출력 ffprobe stream·duration·timestamp 비교와 전체 래퍼 종료 코드
- 사람 승인: 자동 검사와 합치지 않은 별도 불변 레코드

## 5. 실행 순서와 승인 경계

1. Stage 00 실행 보완 승인 후 `TECH-WRAP-EXIT-07`, doccheck, workflow gate, 단위 테스트를
   독립 legacy worktree에서 실행한다.
2. Stage 01~04에서 합성 픽스처 생성기와 fail-closed 계약 테스트를 신규 구조에 이식한다.
3. Stage 04에서 legacy/new의 정규화 기술 산출물을 비교한다.
4. Stage 05에서 외부 실제 파일럿을 병행하고 사용자가 직접 A/V를 승인한다.
5. 파일럿 차이를 설명하지 못하면 승격하지 않고 실패 증거를 동결한다.

현재 상태는 전 항목 `PLANNED_NOT_EXECUTED`다.
