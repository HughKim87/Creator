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

다운로드가 필요하면 대상 아티팩트의 제목과 길이를 확인한 뒤 한 번만 다운로드한다. 원본 다운로드 파일을 이동하거나 삭제하지 말고 Git에서 제외된 `extension/outputs/<job-id>/`에 복사해 사용한다.

## 환경 점검

1. 영상 크기가 0보다 크고 비디오·오디오 스트림과 총 길이가 있는지 PyAV로 확인한다.
2. 먼저 공용 Git 제외 런타임을 확인한다. Python 의존성은 `extension/.runtime/python-deps/`, Whisper 모델 캐시는 `extension/.runtime/models/whisper/`를 기본 경로로 재사용한다.
3. `faster-whisper`가 공용 런타임에 없으면 사용자 승인 없이 설치하지 않는다. 한 번 승인·설치한 뒤에는 영상별 `work/<job-id>/`에 다시 설치하지 않는다.

   `python -m pip install --target <runtime-deps> faster-whisper`

4. 기본 모델은 다국어 정확도와 속도의 균형이 좋은 `large-v3-turbo`다. `transcribe_to_srt.py`는 별도 `--model-dir`가 없으면 공용 모델 캐시를 자동으로 사용한다.
5. 모델 캐시와 Python 의존성을 `extension/work/<job-id>/`에 복사하거나 커밋하지 않는다. 작업 폴더에는 영상별 SRT·원본 전사·용어 사전만 둔다.
6. Windows에서는 CUDA 장치가 보여도 실제 추론 시 `cublas64_12.dll` 또는 cuDNN이 없을 수 있다. CUDA를 쓰려면 라이브러리까지 확인한다. 확실하지 않으면 `cpu/int8`을 기본값으로 사용한다.

## 전사 실행

`scripts/transcribe_to_srt.py`를 사용한다.

```powershell
python scripts/transcribe_to_srt.py <video.mp4> `
  --output <captions.srt> `
  --raw-json <transcript.json> `
  --model large-v3-turbo `
  --model-dir extension/.runtime/models/whisper `
  --language ko `
  --device cpu `
  --glossary <glossary.json>
```

실행 규칙:

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

## 품질 검증

`scripts/validate_srt.py <captions.srt> --video <video.mp4>`를 실행하고 다음을 모두 확인한다.

- UTF-8 디코딩 성공, NUL과 `U+FFFD` 없음
- SRT 번호가 1부터 연속
- `HH:MM:SS,mmm --> HH:MM:SS,mmm` 형식
- 종료 시간이 시작 시간보다 큼
- 큐가 겹치거나 역전되지 않음
- 최소 표시 시간 0.35초 이상
- 마지막 큐가 영상 길이를 넘지 않음
- 지나치게 긴 큐와 긴 텍스트는 경고로 검토

내용은 최소한 시작부, 핵심 전문 용어가 많은 중간 구간, 숫자·가격 구간, 결론부를 직접 읽어 확인한다. 깨진 문자와 glossary 용어를 검색한다. 영상 자체가 필요한 내용을 빠뜨렸다면 자막에 내용을 만들어 넣지 말고 영상 내용 공백으로 보고한다.

## 반환 결과

- 원본 영상 경로와 영상 길이
- SRT 경로, 크기, SHA-256
- 원본 전사 JSON 경로
- 모델·장치·처리 시간
- 큐 수, 첫 시작, 마지막 종료
- 자동 교정과 수동 확인 내용
- 남아 있는 불확실한 구간

## 정지 조건

검증된 SRT와 원본 전사 JSON을 만든 뒤 멈춘다. 제목·썸네일 제작과 수동 업로드 자료 준비는 후속 스킬의 책임이며, 실제 YouTube 업로드는 사용자가 직접 수행한다.
