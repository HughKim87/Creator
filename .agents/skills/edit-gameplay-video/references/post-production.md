# 후편집 실행

정책은 기존 R04·R19–R22가 소유한다. 여기서는 실행 순서와 도구 입력만 정의한다. 특정 영상의 글자 크기·밈 개수·폴더·시각은 일반 기본값으로 승격하지 않는다.

## 시작과 설계

여러 작업 자료와 해설 음성을 조합하는 작업은 [목적별 경로](../../../../extension/docs/domain/youtube/VIDEO_PURPOSE_WORKFLOWS.md)로 입력·지원 범위를 먼저 구분한다. 연출 선택은 Agent의 판단으로 두되 무엇을 설명하는지, 읽는 시간과 고정해야 할 요소를 큐시트에 연결한다. 새 효과·배치의 샘플은 등장 중/정착 후/읽는 동안을 실제로 확인한다. 작은 글씨를 포함한 캡처 전체의 지속 확대 대신 필요한 패널이나 별도 큰 설명을 선택할 수 있다. 모든 자료를 움직이거나 모든 확대를 금지하는 고정값은 만들지 않는다. 검증된 스타일과 유효한 샘플 근거는 재사용한다.

1. 현재 job의 최신 v2·editorial-state·source manifest·편집본 SRT와 프로필을 확인한다. 영상명이나 파일 수정일만으로 기준본을 고르지 않는다. 기존 컷과 사용자가 만족한 구간을 보존한다. 최신 전사에 미확인 단어가 있으면 별도 확인한다.
2. 프로필의 일반/화자별 색·강조 크기·줄 수·화면 여백·음량을 상속하고 차이의 이유를 job 기록에 둔다. 큐시트에는 레이어의 기능, 편집본 프레임 구간, 대응 원본 anchor/발화 끝, 출처와 hash, 이미지 대상·종료 지점, 가림 판단을 기록한다. anchor 문자열 자체가 실제 관찰의 증거가 되지는 않는다.
3. 밈은 사용자 지정 폴더에서 읽고 실제 이미지와 앞뒤 장면을 확인한다. 기존 승인 경로는 job 입력으로 재사용한다. 자막의 원문·시각을 유지하면서 화자/강조는 해당 cue의 스타일을 바꾼다. 강조와 일반 자막을 두 번 얹지 않는다. 효과음·음악·카드 등 현재 adapter 밖 연출은 지원 도구와 검증을 먼저 확보한다.
4. 모든 사용 레이어와 핵심 위험이 드러나는 최소 연속 샘플을 만든다. 샘플용 컷도 원본/v2에서 유도하고 전체 큐를 샘플의 새 프레임 원점에 맞춘다. 샘플을 앱에서 재생 가능하게 보여주고 R20의 사용자 확인 또는 이미 받은 위임에 따라 전체로 확장한다. 샘플·위임·관찰 결과를 꾸며 쓰지 않는다.

## 도구 계약

`scripts/postprocess.py`는 Windows mandatory read lock·hash/size 결속·비덮어쓰기 게시를 재사용한다. layers는 최신 v2/editorial 검사를 통과한 **원본**에서 컷 stage를 만든다. 전달 MP4를 layers 입력으로 받지 않는다. stage와 효과 chunk는 job/work/post-cache에만 두며 timeline/renderer/ASS/asset/zoom hash로 재사용한다. 변경 cue가 걸친 chunk만 다시 렌더하고 기존 chunk hash를 확인한다. 손상 cache는 실패하며 사용자 기존 자료를 자동 정리하지 않는다. cache는 R04의 임시 수명에 속한다.

지원 범위: 단일 원본, 한 영상·한 음성, 정수 CFR 1–120fps, 프레임당 정수 audio sample, 정상 속도, mono/stereo, 짝수 해상도, 식별된 BT.709·정사각 픽셀. layers는 libass 자막(최대 2줄·10ms 시각 정밀도), cue별 색/강조, 정지 이미지와 점진 확대, 전체 음량 마감을 지원한다. VFR·다중 원본·효과음/음악 합성·별도 카드·HDR/색공간 변환은 지원하지 않는다. 임의 변환으로 숨기지 않는다.

layers JSON의 모든 프레임 구간은 컷 timeline의 `[start_frame,end_frame)`이다. 아래 수치는 형식을 보이는 예시이며 실제 프로필을 대신하지 않는다. `{path,sha256,bytes}`는 절대 canonical 경로와 `sha256:` 접두 해시·정수 파일 크기를 뜻한다.

```json
{
  "version": 1,
  "operation": "layers",
  "editorial_fingerprint": "<기존 함수가 계산한 최신 v2 fingerprint>",
  "srt": {"path": "D:/.../body.srt", "sha256": "sha256:<64hex>", "bytes": 1000},
  "captions": {"font": "Malgun Gothic", "size": 64, "emphasis_size": 88, "outline": 3, "margin": 48},
  "caption_overrides": [{"cue": 3, "style": "emphasis", "color": "FFFF00"}],
  "images": [{"start_frame": 600, "end_frame": 720, "anchor": "<원본 사건/발화 근거 위치>", "rect": [100, 100, 320, 240], "asset": {"path": "D:/.../meme.png", "sha256": "sha256:<64hex>", "bytes": 1000}}],
  "protected_rects": [[1400, 700, 500, 300]],
  "zooms": [{"start_frame": 800, "end_frame": 860, "anchor": "<관찰 근거>", "factor": 1.15, "x": 0.5, "y": 0.5}],
  "audio": {"integrated_lufs": -14, "true_peak_dbtp": -1, "tolerance_lu": 0.8},
  "chunk_frames": 1800
}
```

도구는 실제 libass glyph raster 폭, 중복 강조, 선언된 보호 사각형과 이미지의 교차를 검사한다. 색별 화자 식별·글꼴 fallback·화면 모든 HUD·이미지 대상 적합성·레이어 간 실제 가림은 샘플/전편 화면 검수가 판단한다. 선언한 사각형 검사만으로 전체 가림 검수 pass를 기록하지 않는다. 더 큰 글자가 넘치면 글자를 줄이기 전에 발화·줄바꿈·cue 분할을 재검토한다.

```powershell
python -B scripts/creator_job.py run --job <job-id> -- python -B .agents/skills/edit-gameplay-video/scripts/postprocess.py --plan '<job/work/post-plan.json>' --timeline-json '<최신-v2>' --editorial-state-json '<최신-state>' --output '<job/outputs/새-post.mp4>'
```

기준본 참조는 render_candidate.py와 동일한 --calibration-timeline-json / --baseline-timeline-json / 반복 --reference-timeline-json으로 전달한다. 도구 결과 JSON을 job/logs에 보존하고 현재 revision과 연결한다. 기존 runner의 dirty/provenance/lock gate를 우회하거나 자동 커밋하지 않는다.

## 지정 아웃트로와 전체 SRT

사용자가 exact 완성본 뒤에 exact 아웃트로를 추가하라고 지정했을 때만 `operation=append`를 쓴다. 본편에 새 레이어를 입히는 권한으로 이 모드를 선택하지 않는다.

```json
{"version":1,"operation":"append","body":{"path":"D:/.../body.mp4","sha256":"sha256:<64hex>","bytes":1000},"outro":{"path":"D:/.../outro.mp4","sha256":"sha256:<64hex>","bytes":1000},"audio":{"integrated_lufs":-14,"true_peak_dbtp":-1}}
```

append는 본편 H.264·B-frame 없음·BT.709·정사각 픽셀, 같은 해상도·audio sample rate/채널을 요구한다. 식별된 BT.709/BT.601 SDR 아웃트로를 본편 fps로 변환하고 출력 프레임 수가 정수일 때만 처리한다. 본편 coded video packet hash 전체를 최종 prefix와 비교한다. 타임베이스를 통일하고 음성은 본편/아웃트로의 정확한 sample 경계로 합친 뒤 **전체를 재인코딩·음량 마감**한다. 본편 음성 바이트 보존은 약속하지 않는다. 예상 총 길이와 각 구간 frame/sample 수를 조립 계획에 남긴다.

실행은 위 명령에서 --plan과 --output만 사용한다. 본편 packet 보존이 지원되지 않으면 원본 기반 별도 adapter가 필요하다고 보고한다.

아웃트로 자막은 해당 음성에서 별도 전사·청취/교차확인하고 본편 cue는 텍스트·시간을 보존한다. SRT 결합 도구는 전사하거나 빠진 대사를 채우지 않는다. 아래 offset은 정확한 본편 길이, total은 결합 후 길이를 ms로 명시한다. ms로 정확히 표현되지 않는 경계는 영상 대비 반올림 오차도 기록한다.

```powershell
python -B scripts/creator_job.py run --job <job-id> -- python -B .agents/skills/edit-gameplay-video/scripts/postprocess.py --body-srt '<body.srt>' --outro-srt '<outro.srt>' --offset-ms <본편길이> --total-ms <총길이> --output '<job/outputs/새-final.srt>'
```

## 최종 검사와 전달

도구는 최종 frame count·CFR·PTS 연속·영상/음성 길이·전체 decode·입력 hash·출력 loudness/true peak를 검사하고 통과 뒤 새 파일을 게시한다. AAC 인코딩 여유를 두어도 **최종 파일 재측정**이 목표를 넘으면 게시하지 않는다. append에서 본편 pass를 최종 pass로 상속하지 않는다.

추가로 에이전트가 레이어 없는 원본 구간과 합성본 색/화면, 밈의 삽입/직후/종료, 강조 대체와 화자 색, 컷 접합, 본편↔아웃트로 경계, SRT 최종 cue를 확인한다. 도구의 colour_fidelity/not_run 및 semantic_status/not_run을 실제 관찰 없이 pass로 바꾸지 않는다. 전체 정상속도 A/V 미검수는 명시한다.

최신 MP4/SRT를 절대 경로 Markdown 미디어 임베드와 파일 링크로 바로 보여준다. 이전 revision과 혼동시키지 않는다. 내부 plan/cache/log는 job 내부에 둔다. 제목·썸네일·설명·게시 자료는 요청했을 때만 기존 전문 스킬로 연결한다.

## 회귀 실행

`python -B -m unittest discover -s extension/tests -p test_gameplay_postproduction.py -v`

실제 FFmpeg 합성 fixture로 스타일 대체·이미지 합성·확대·부분 cache·원본/자막 불변·fps/timebase 조립·본편 packet 동일성·전체 음량·실패 시 미게시를 검사한다. 기존 컷/editorial/검토 전달 검사도 유지한다. Windows sandbox가 os.link 검사를 막으면 테스트 범위의 실행 권한을 요청하며 원자적 게시 구현을 약화하지 않는다. 합성 검사 통과는 실제 게임 영상의 자연스러움 검수가 아니다.
