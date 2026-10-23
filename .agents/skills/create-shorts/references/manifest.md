# 후보 manifest와 helper

helper는 Python 표준 라이브러리와 이미 설치된 ffmpeg를 쓴다. 후보 판단/ASR은 에이전트 책임이다. JSON은 UTF-8, 시간은 초/end exclusive, source는 absolute, file은 review root 내부 상대경로다.

```json
{
  "job_id": "example-job",
  "source": "D:/videos/example.mp4",
  "source_label": "example.mp4",
  "source_duration": 1800.0,
  "actual_listening": "not_run",
  "clips": [{
    "id": "001", "revision": "r1", "title": "한 가지 오해와 답", "category": "설명",
    "reason": "질문과 실제 사례의 답이 함께 있습니다.",
    "parts": [{"start": 40, "end": 45}, {"start": 48, "end": 54}],
    "file": "videos/001-r1.mp4", "active": true,
    "caption_status": "aligned", "caption_method": "ASR word timestamps",
    "captions": [{"start": 0.2, "end": 2.3, "text": "원음에서 확인할 문구"}],
    "uncertain": [{"id": "word-1", "start": 0.2, "end": 2.3, "text": "현재 표현", "alternatives": ["다른 표현"], "reason": "원음과 전사가 다름"}]
  }]
}
```

ID는 숫자 문자열이며 제외 후 재사용하지 않는다. parts 합이 preview 길이다. captions/uncertain 시간은 **합성 clip** 기준이다. parts나 불확실 문구가 달라지면 revision을 갱신한다.

caption_status는 `unverified`, `aligned`, `user_confirmed`. unverified는 동기화 자막을 숨기고 최종 gate는 거부한다. uncertain의 빈 배열은 에이전트가 그 근거를 확보한 경우만 쓴다. helper가 숨은 오인식을 발견하지는 않는다.

active=false는 페이지에서 숨기며 선택 기록/파일은 지우지 않는다. file은 revision별 새 MP4 경로로 지정한다. 원본을 file로 지정하지 않는다. symlink 포함 resolved 경로가 root 밖이면 거부한다.

```text
python scripts/shorts_review.py previews manifest.json --root review-dir
python scripts/shorts_review.py gallery manifest.json --root review-dir
python scripts/shorts_review.py serve --root review-dir --port 0
python scripts/shorts_review.py final-gate manifest.json --selection selection.json
```

previews는 parts trim/concat,640px 폭/30fps/H264/AAC/faststart로 출력한다. `.preview-owner.json`의 job·입력 식별 hash·parts/revision과 길이를 검사한 기존 파일만 재사용한다. 새 파일은 `.partial.mp4` 성공 후 같은 root 안의 최종 이름으로 옮긴다. partial 충돌은 알려 새 revision을 사용하게 하며 임의 삭제하지 않는다.

gallery는 file 존재를 확인해 index.html/manifest.json을 생성한다. 같은 job만 갱신하며 다른 job 파일이 있으면 중단한다. HTML은 CDN 없이 동작한다. gallery root의 index/manifest는 도구 소유 갱신 대상이고 media는 재작성하지 않는다.

serve는 localhost에서 실제 포트를 출력한다. port0은 빈 포트를 골라 기존 작업을 침범하지 않는다. directory listing/root밖 symlink/입력 폴더 공개는 금지한다. 테스트 server/PID만 종료하고 운영 server는 작업별로 관리한다.

## 사용자 선택 JSON

페이지에서 복사/저장하면 selected 항목만 다음 형태로 내보낸다. **대화에서 사용자에게 반환받은 결과**만 권위 있는 입력이다.

```json
{
  "job_id": "example-job", "selection_only": true,
  "clips": [{
    "id": "001", "revision": "r1", "parts": [{"start": 40, "end": 45}, {"start": 48, "end": 54}], "selected": true, "note": "앞 장면부터 보여주세요",
    "confirmations": [{"id": "word-1", "start": 0.2, "end": 2.3, "text": "현재 표현", "confirmed": true, "replacement": "사용자가 들은 표현"}]
  }]
}
```

final-gate는 선택한 active 후보≥1, ID/revision/job/parts 일치, 모든 uncertain에 현재 text/start/end가 같은 확인·교정 또는 `[자막 생략]`을 요구한다. 새 컷에는 새 revision을 써 오래된 확인을 무효화한다. gate 통과는 **확인 기록 구조**만 증명하고 actual listening, 의미 정확도, 최종 제작 요청은 증명하지 않는다. 확인 결과는 원음/시간을 대조해 에이전트가 반영하며 helper가 자막을 자동 수정하지 않는다.
