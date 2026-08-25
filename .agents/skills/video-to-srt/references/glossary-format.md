# 전사 Glossary 형식

UTF-8 JSON 파일을 사용한다.

```json
{
  "terms": [
    "GPT-5.6",
    "Sol",
    "Terra",
    "Luna",
    "ChatGPT",
    "Codex"
  ],
  "replacements": [
    {
      "from": "채치피티",
      "to": "ChatGPT"
    },
    {
      "from": "출원 강도",
      "to": "추론 강도"
    }
  ]
}
```

## 규칙

- `terms`는 Whisper 초기 프롬프트에 넣을 정확한 표기다.
- `replacements`는 음성과 문맥으로 오인식이 명백할 때만 추가한다.
- 일반적인 문장 다듬기, 주장 변경, 번역에는 사용하지 않는다.
- 원본 JSON은 수정하지 않고 정제된 SRT에만 교정을 적용한다.
- 같은 영상을 다시 전사하지 않고 용어만 고칠 때는 `--postprocess-only`를 사용한다.
- 영상별 glossary는 `extension/work/<job-id>/`의 task scratch에 둔다. 이 `references/` 디렉터리에는 실제 영상·주제별 JSON을 보존하지 않는다.
- 작업 종료 시 고유 용어와 치환 목록 자체는 일반 규칙으로 승격하지 않는다. 반복 사용이 입증된 작성·검증 원칙만 이 문서에 흡수하고 task glossary는 후속 소비자가 없으면 제거한다.
