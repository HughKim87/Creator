# 도구 연결과 지원 범위

Creator root 기준 경로다. 정책·스키마·완료 조건은 기존 owner가 소유하며 아래는 실행 안내다.

| 기능 | 재사용할 도구 | 확인한 경계 |
|---|---|---|
| job·runtime·GPU lease | scripts/creator_job.py, extension/docs/WORKSPACE.md | main의 job별 실행, dirty checkout/코드 변경을 차단할 수 있음 |
| 로컬 전사 | .agents/skills/video-to-srt/scripts/transcribe_to_srt.py | raw 단어/세그먼트 JSON와 정제 SRT, 청취 대체 아님 |
| SRT 검사 | 같은 스킬의 validate_srt.py, review_srt.py | 구조·문자열·저확률 조사 |
| 편집 구조 | extension/src/video_editing/timeline_v2.py | 사건·microbeat·clip·feedback·revision 기존 계약 |
| 개연성 근거 검사 | video_editing editorial-check / record-feedback | anchor·생략 coverage·누적 feedback, 관찰 내용의 진실은 판별 불가 |
| XML | video_editing premiere-review-xml / premiere-xml | 기존 참조·승인·검수 gate 유지 |
| 기존 렌더 테스트 | video_editing.review_proxy.render_fixture_proxy | 합성 fixture 전용, 실제 영상 경로 우회 금지 |
| MP4 후보 출력 | 이 스킬의 scripts/render_candidate.py | 단일 CFR 원본·정상 속도·독립 A/V 컷, 의미 승인 없음 |
| 컷 이후 후편집·지정 결합 | 이 스킬의 scripts/postprocess.py, [후편집 실행](post-production.md) | 원본 기반 레이어/cache, exact 완성본 append, 전체 loudness/길이 재검사 |

## 준비와 실행

```powershell
python -B scripts/creator_job.py runtime --component ffmpeg
python -B scripts/creator_job.py runtime --component python-deps
python -B scripts/creator_job.py runtime --component whisper-models
python -B scripts/creator_job.py inspect --job <job-id>
# 새 작업일 때만
python -B scripts/creator_job.py init --job <job-id>
```

미디어 실행은 `creator_job.py run --job <job-id> -- <자식 명령>` 안에서 한다. GPU는 --gpu를 사용한다. dirty 코드나 provenance 변경으로 runner가 차단하면 자동 커밋·우회하지 말고 재개 조건을 보고한다. 원본은 지정 위치를 참조하고 무조건 복사하지 않는다.

ffmpeg/ffprobe는 조회 경로의 bin에서 재사용한다. 기존 모델 snapshot을 확인하고 HF_HUB_OFFLINE=1을 자식 환경에 설정한다. 전사에는 --model-dir로 실제 기존 snapshot을 지정해 의도하지 않은 다운로드를 막는다. 모델/패키지를 못 찾으면 설치된 것처럼 진행하지 않는다.

## 내용 탐색

FFprobe의 -show_streams -show_format -of json으로 영상·음성·자막 트랙을 구분한다. 별도 자막 트랙은 그 트랙을 추출하고 화면 자막은 필요한 구간에서 따로 관찰한다. 음성 인식 두 번을 서로 다른 자막 추출이라고 부르지 않는다.

video-to-srt의 **로컬 전사 절만** 재사용한다. NotebookLM 다운로드·클라우드 실행·후속 업로드는 이 범위가 아니다.

```powershell
# job runner 안의 자식 명령. 결과는 해당 job/work의 새 절대 경로.
python -B .agents/skills/video-to-srt/scripts/transcribe_to_srt.py '<원본>' --output '<원본.srt>' --raw-json '<raw.json>' --model-dir '<기존-snapshot>' --language ko --device cpu
```

주 언어는 실제 음성으로 선택한다. 다국어·동시 발화·저확률은 source 범위를 발췌해 해당 언어로 별도 확인한다. 같은 모델의 재전사는 독립 증거가 아니다. raw의 segments[].words[]를 보존한다. 기존 전사 스크립트는 문장을 비례 시간으로 나누고 인접 반복을 정제하므로, 정제 SRT를 강제 정렬 결과나 실제 반복이 없는 증거로 쓰지 않는다.

프레임·음성·silence 탐색은 FFmpeg의 아래 형태를 인수 배열로 실행한다. 시각·검출값은 소스별로 정하고 보편적인 컷 기준으로 만들지 않는다.

```text
ffmpeg -nostdin -n -ss <시작초> -i <원본> -t <범위초> -vf fps=<탐색빈도>,scale=<폭>:-2 <새프레임패턴.jpg>
ffmpeg -nostdin -n -i <원본> -ss <시작초> -t <범위초> -map 0:a:<확인한트랙> -c:a pcm_s16le <새검토.wav>
ffmpeg -nostdin -i <원본> -map 0:a:<트랙> -af silencedetect=noise=<해당기준>:d=<해당기준> -f null -
```

거친 전 구간 색인은 구조 탐색일 뿐 상세 검수가 아니다. 채택/삭제 후보와 양쪽 handle을 촘촘히 보고 게임음·몸짓을 확인한다. 실제 컷은 프레임·샘플로 정한다. 직접 청취 기록은 실제 가능한 도구로 수행했을 때만 남긴다.

## 편집 근거와 검사

extension/examples/video-edit-timeline-v2.json 및 editorial-state-v1.json은 필드 예시다. 합성 예시의 approved/passed·관찰 문자열을 실제 작업으로 복사하지 않는다. spine·프로필·관찰 방법은 job 기록, 컷은 v2, 원본 scene·anchor·생략·feedback은 editorial-state에 둔다. 스키마 밖 임의 필드를 덧붙이지 않는다.

scenes[].show에 원본 상황, viewer_learns에 시청자가 아는 사실, next_action_reason에 다음 행동 이유를 기록한다. 위치·생존·동료·목표 변화 근거를 관찰에 포함한다. depends_on은 실제 선행 원인을 가리킨다. derive_omissions로 실제 A/V 생략을 얻은 뒤 범위별로 관찰한다.

```powershell
# extension/src만 PYTHONPATH에 추가한다. Core import는 필요 없다.
python -B -m video_editing editorial-check --timeline-json '<v2>' --editorial-state-json '<최신-state>'
python -B -m video_editing record-feedback --timeline-json '<v2>' --editorial-state-json '<최신-state>' --feedback-id '<id>' --symptom '<증상>' --reported-by user --output '<새-state>'
```

## MP4 후보

```powershell
python -B scripts/creator_job.py run --job <job-id> -- python -B .agents/skills/edit-gameplay-video/scripts/render_candidate.py --timeline-json '<v2-절대경로>' --editorial-state-json '<최신-state-절대경로>' --output '<job/outputs/새-candidate.mp4>'
# 미디어 접근 없는 기존 구조/근거 검사와 선택적 raw 단어 내부 경계 힌트
python -B .agents/skills/edit-gameplay-video/scripts/render_candidate.py --timeline-json '<v2>' --editorial-state-json '<state>' --check-only --raw-json '<원본-raw>'
```

원본 하나를 참조하는 v2 working_candidate·semantic not_run만 받는다. 기존 구조·anchor·생략·feedback 검사를 재사용하고 failed 경계를 거부한다. source hash/size와 Windows mandatory read-lock을 유지하며 원본을 직접 읽는다. stage나 전달 MP4를 원본으로 바꾸지 않는다. XML writer나 calibration gate를 우회하는 용도가 아니다. 작업의 후보 생성 권한과 상위 승인 경계는 에이전트가 먼저 확인한다.

참조가 있는 v2에는 기존 CLI와 같은 --calibration-timeline-json / --baseline-timeline-json / 반복 --reference-timeline-json을 전달한다. authoritative 최신 bundle의 완전성은 호출자 책임이다.

지원: Windows, 한 video/한 audio, CFR, 정상 속도, 프레임당 정수 audio samples, mono/stereo, 짝수 해상도. 독립 A/V 컷으로 J/L cut을 보존한다. 다중 원본·비정수 샘플 경계(예: 29.97fps/48kHz)·VFR·트랙 합성·효과는 별도 검증 adapter가 필요하다. 자동 리사이즈/트랙 버림/정규화로 숨기지 않는다.

영상은 정확한 input seek 뒤 필요한 프레임만 H.264 stage로 만든다. 음성은 원본을 한 번 float32 PCM으로 디코딩한 뒤 바이트 offset으로 정확한 sample 범위만 연결하여 컨테이너 seek의 음성 시각 오차를 피한다. 모두 job/work의 이번 전용 임시이며 긴 filter graph의 메모리 누적을 피한다. 전체 원본 PCM 공간(초×sample rate×채널×4bytes)과 영상 stage 비용을 준비 단계에 확인한다. source와 결과 전체 timestamp·frame/sample을 검사한다. 출력은 자막 미합성 MP4이고 편집본 전사/SRT는 다음 단계다. 원본색 완전 일치나 대사 자연스러움을 이 도구가 검증하지는 않는다.

반환 JSON은 지정 job/logs에 보존하고 현재 후보에 연결한다. full decode/rate/count 연속성의 technical pass와 semantic/user/direct_listening not_run을 구분한다. AAC 끝 padding은 1024 sample 미만만 허용하고 실제 값을 기록한다. raw 단어 내부 경계 힌트는 실제 절단 판정이나 청취 pass가 아니다.

재생 파일은 앱의 로컬 미디어 임베드로 먼저 보여준다. HTML 선택 페이지는 사용자가 요청하거나 여러 후보 비교가 필요할 때 생성하되 현재 revision과 source anchor를 결속하고, 오래된 페이지의 timeline을 현재 시각으로 재사용하지 않는다.
