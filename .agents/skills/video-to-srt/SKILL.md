---
name: video-to-srt
description: NotebookLM 등에서 생성한 동영상의 음성을 로컬 Whisper로 전사하고, 용어 사전·타임코드 보정·중복 제거·구조 검증을 거쳐 YouTube에 사용할 SRT 자막을 만드는 스킬. 사용자가 영상 음성 분석, 한국어 자막 추출, MP4를 SRT로 변환, research-to-video 워크플로의 자막 단계를 요청할 때 사용한다. 원본 전사 근거를 보존하고 제목·썸네일·수동 업로드 자료 준비 전에 멈춘다.
---

# Video to SRT

정확히 지정된 영상에서 음성을 전사하고 검증된 SRT와 원본 전사 JSON을 만든다. 자막은 음성을 옮기는 산출물이며 영상에 없는 정보를 새로 쓰지 않는다.

## 입력과 작업 위치

다음을 확정한다.

- 정확한 영상 파일 또는 NotebookLM 영상 아티팩트
- 음성 언어
- 전문 용어·제품명·인명 표기
- SRT와 원본 JSON을 둘 위치

다운로드가 필요하면 대상 아티팩트의 제목과 길이를 확인한 뒤 화면에 제공된 정상 다운로드 동작을 한 번만 사용한다. 이 동작의 정확한 실패가 확인되기 전에는 미디어 URL 직접 추출, 페이지 자산 수집, 미등록 API를 대체 경로로 사용하지 않는다. 정상 경로나 특정 대체 경로가 실패하면 관측한 경로의 실패만 기록하고, 다른 경로를 확인하지 않은 채 영상 획득 전체가 불가능하다고 보고하지 않는다. 미등록 대체 경로를 임의로 실행하지 않고 확인된 상태와 필요한 다음 결정을 보고한다.

원본 다운로드 파일을 이동하거나 삭제하지 말고 Git에서 제외된 `extension/outputs/<job-id>/`에 복사해 사용한다. 복사본은 아래 환경 점검에서 실제 영상 파일, video·audio stream, 전체 길이를 통과해야 한다.

| 다운로드 판정 사례 | 기대 행동 |
|---|---|
| 화면의 정상 다운로드가 가능한데 미디어 URL을 먼저 추출하려 함 | 우회 추출을 중단하고 정상 다운로드 동작을 사용한다 |
| 하나의 다운로드 경로가 실패했지만 다른 획득 경로는 미확인임 | 해당 경로 실패와 전체 획득 미확인을 구분하고 전체 불가능을 주장하지 않는다 |

## 환경 점검

1. 영상 크기가 0보다 크고 비디오·오디오 스트림과 총 길이가 있는지 PyAV로 확인한다.
2. 먼저 공용 Git 제외 런타임을 확인한다. Python 의존성은 `extension/.runtime/python-deps/`, Whisper 모델 캐시는 `extension/.runtime/models/whisper/`를 기본 경로로 재사용한다.
3. `faster-whisper`가 공용 런타임에 없으면 사용자 승인 없이 설치하지 않는다. 한 번 승인·설치한 뒤에는 영상별 `work/<job-id>/`에 다시 설치하지 않는다.

   `python -m pip install --target <runtime-deps> faster-whisper`

4. 기본 모델은 다국어 정확도와 속도의 균형이 좋은 `large-v3-turbo`다. `transcribe_to_srt.py`는 별도 `--model-dir`가 없으면 공용 모델 캐시를 자동으로 사용한다.
5. 모델 캐시와 Python 의존성을 `extension/work/<job-id>/`에 복사하거나 커밋하지 않는다. 작업 폴더에는 영상별 SRT·원본 전사·용어 사전만 둔다. 영상별 용어 사전은 `.agents/skills/video-to-srt/references/`에 두지 않는다. 이 디렉터리는 재사용 형식과 절차만 소유한다.
6. `transcribe_to_srt.py`와 `validate_srt.py`는 프로젝트의 `extension/.runtime/python-deps`를 자동으로 우선 참조한다. 검증 명령을 위해 별도 `PYTHONPATH`를 만들지 않는다.
7. Windows에서는 CUDA 장치가 보여도 실제 추론 시 `cublas64_12.dll` 또는 cuDNN이 없을 수 있다. CUDA를 쓰려면 라이브러리까지 확인한다. 확실하지 않으면 `cpu/int8`을 기본값으로 사용한다.

## 전사 실행

`scripts/transcribe_to_srt.py`를 사용한다.

```powershell
& python scripts/transcribe_to_srt.py '<video.mp4>' `
  --output <captions.srt> `
  --raw-json <transcript.json> `
  --model large-v3-turbo `
  --model-dir extension/.runtime/models/whisper `
  --language ko `
  --device cpu `
  --glossary <glossary.json>
```

실행 규칙:

- Windows 경로에 공백이나 한글이 있으면 실행 파일과 모든 경로 인수를 작은따옴표로 감싸고 PowerShell 호출 연산자 `&`를 사용한다.
- 백그라운드 실행이 필요하면 인수 배열을 사용한다. 예: `Start-Process -FilePath $python -ArgumentList @($script, $video, '--output', $srt) -WindowStyle Hidden -PassThru`.
- 제품명과 기술 용어를 `initial_prompt`와 glossary `terms`에 넣는다.
- 단어 타임스탬프와 VAD를 사용한다.
- 원본 세그먼트·단어 확률·모델·장치·언어 확률을 JSON으로 보존한다.
- GPU 모델 로딩이 성공해도 첫 추론에서 CUDA DLL 오류가 날 수 있다. 스크립트는 CUDA 실행 전체를 감싸고 실패하면 CPU int8로 한 번 다시 실행한다.
- 장시간 전사는 백그라운드로 실행하고 **5분 간격으로만** 상태를 확인한다.

## SRT 정제

Whisper 결과를 그대로 최종본으로 취급하지 않는다.

1. 단어 타임스탬프가 세그먼트 문장의 72% 미만만 덮으면 단어 배열을 버리고 전체 세그먼트 텍스트를 사용한다.
2. 긴 문장은 문장부호와 절 경계에서 나누고 세그먼트 시간 안에 비례 배치한다.
3. 0.7초 미만의 짧은 큐는 가까운 인접 큐에 합친다.
4. 연속된 같은 문구와 마무리 인사 반복을 제거한다.
5. glossary `replacements`로 확인된 오인식만 교정한다.
6. 번역, 문체 개선, 사실 추가, 영상 내용 수정은 하지 않는다.
7. 용어 사전을 바꿔 다시 정제할 때는 `--postprocess-only`를 사용해 음성을 재전사하지 않는다.

glossary 형식은 `references/glossary-format.md`를 따른다.

영상별 glossary는 현재 `extension/work/<job-id>/`의 task scratch에 둔다. closeout에서는 재사용 가능한 교정 원칙만 이 스킬이나 형식 문서에 흡수하고, 고유 제품명·인명·오인식 치환을 담은 task glossary는 후속 소비자가 명시된 유지 산출물이 아닌 한 scratch와 함께 제거한다.

## 구조 검증

`scripts/validate_srt.py <captions.srt> --video <video.mp4>`를 실행하고 다음을 모두 확인한다.

- UTF-8 디코딩 성공, NUL과 `U+FFFD` 없음
- SRT 번호가 1부터 연속
- `HH:MM:SS,mmm --> HH:MM:SS,mmm` 형식
- 종료 시간이 시작 시간보다 큼
- 큐가 겹치거나 역전되지 않음
- 최소 표시 시간 0.35초 이상
- 마지막 큐가 영상 길이를 넘지 않음
- 지나치게 긴 큐와 긴 텍스트는 경고로 검토

## 의미·맞춤법 검수

구조 검증 통과만으로 자막을 완료 처리하지 않는다. `scripts/review_srt.py`와 원본 전사 JSON을 사용해 다음 순서로 전체 자막을 검수한다.

```powershell
& python scripts/review_srt.py '<captions.srt>' `
  --raw-json '<transcript.json>' `
  --glossary '<glossary.json>' `
  --output '<captions-review.json>'
```

1. 첫 실행의 `low_confidence_words`와 `unresolved_replacement_hits`를 확인한다.
2. 낮은 확률 단어만 보지 말고 SRT의 모든 큐를 처음부터 끝까지 읽어 문맥상 잘못된 단어, 동음이의어, 조사·어미, 전문 용어와 맞춤법을 확인한다.
3. 음성으로 확인된 오인식만 glossary `replacements`에 추가한다. 의미를 새로 만들거나 문체를 윤문하지 않는다.
4. `--postprocess-only`로 SRT를 다시 만든 뒤 구조 검증과 검색을 반복한다.
5. 전체 큐 검수가 끝났을 때만 `--confirm-full-read`를 붙여 최종 검수 기록을 만든다.

```powershell
& python scripts/review_srt.py '<captions.srt>' `
  --raw-json '<transcript.json>' `
  --glossary '<glossary.json>' `
  --output '<captions-review.json>' `
  --confirm-full-read
```

최종 `captions-review.json`의 `status`가 `reviewed`이고 glossary의 교정 전 표현이 최종 SRT에 남지 않아야 한다. 영상 자체가 필요한 내용을 빠뜨렸다면 자막에 내용을 만들어 넣지 말고 영상 내용 공백으로 보고한다.

## 반환 결과

- 원본 영상 경로와 영상 길이
- SRT 경로, 크기, SHA-256
- 원본 전사 JSON 경로
- 모델·장치·처리 시간
- 큐 수, 첫 시작, 마지막 종료
- 전체 의미·맞춤법 검수 기록 경로와 자동 교정·수동 확인 내용
- 남아 있는 불확실한 구간

## 정지 조건

구조 검증을 통과한 SRT, 원본 전사 JSON, `status: reviewed`인 전체 의미·맞춤법 검수 기록을 만든 뒤 멈춘다. 제목·썸네일 제작과 수동 업로드 자료 준비는 후속 스킬의 책임이며, 실제 YouTube 업로드는 사용자가 직접 수행한다.
