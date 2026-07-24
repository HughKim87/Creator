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
