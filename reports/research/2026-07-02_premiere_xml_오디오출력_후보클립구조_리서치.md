# Premiere XML 오디오 출력 꺼짐 + 후보클립 중복 문제 리서치 보고서

작성: 2026-07-02 | 배경: `CRA_PLAY_EDIT_ASSIST_3P_TEST_MP4.xml` Premiere 가져오기 성공, A/V 싱크 정상.
남은 문제 2건: (1) 오디오 트랙의 출력(스피커) 토글이 꺼진 상태로 들어옴, (2) `00_원본`과 `01_후보클립`이 같은 전체 영상으로 보임.

## 문제 1 — 오디오 트랙 출력(스피커 아이콘) 꺼짐

### 원인 (확정적)

Premiere가 직접 내보내는 FCP7 XML(xmeml)을 확인한 결과, 시퀀스의 각 오디오 트랙에는
클립 외에 **트랙 상태 요소**가 반드시 포함된다:

```xml
<track ...>
  <clipitem>...</clipitem>
  <enabled>TRUE</enabled>          <!-- 트랙 활성화 -->
  <locked>FALSE</locked>
  <outputchannelindex>1</outputchannelindex>  <!-- 출력 채널 라우팅 (L=1, R=2) -->
</track>
```

또한 시퀀스 `<audio>` 아래에 출력 채널 정의(`<outputs>`)가 있다:

```xml
<audio>
  <numOutputChannels>2</numOutputChannels>
  <format>...</format>
  <outputs>
    <group><index>1</index><numchannels>1</numchannels><downmix>0</downmix><channel><index>1</index></channel></group>
    <group><index>2</index><numchannels>1</numchannels><downmix>0</downmix><channel><index>2</index></channel></group>
  </outputs>
  ...
```

현재 `make_premiere_xml.py`가 만드는 XML에는 **트랙 수준의 `enabled`/`locked`/`outputchannelindex`와
`outputs` 정의가 모두 빠져 있다.** Premiere는 명시되지 않은 트랙 출력 상태를 꺼짐으로 처리해
스피커 아이콘이 비활성으로 들어온 것이다. 클립 자체는 정상이므로 싱크는 맞았다.

### 해결

- 단기(지금 당장): 타임라인에서 빈 스피커 칸을 클릭해 켜면 됨. 데이터 손상 아님.
- 근본(스크립트 수정): `add_sequence()`에 위 요소들을 추가 —
  각 오디오 트랙에 `enabled TRUE / locked FALSE / outputchannelindex 1·2`,
  시퀀스 audio에 `numOutputChannels`(이미 있음) + `outputs` 그룹 2개,
  비디오 트랙에도 `enabled/locked` 추가.

## 문제 2 — 원본과 후보클립이 같은 전체 영상으로 보임

### 원인 (확정적)

현재 스크립트는 후보클립을 **in/out이 지정된 bin 수준 `<clip>`**으로 만든다.
그러나 Premiere의 FCP7 XML 가져오기는 이 방식과 맞지 않는다:

1. Premiere는 bin의 `<clip>`을 가져올 때 in/out(가상 경계)을 **서브클립으로 인식하지 못하거나 무시**하고,
   같은 원본 파일을 가리키는 또 하나의 마스터 클립으로 만든다. → 후보클립이 원본과 똑같은 전체 영상으로 보임.
2. FCP7→Premiere 서브클립 변환은 알려진 버그가 많다: In점은 맞지만 Out점이 부모 클립의 Out점이 되고,
   미디어 메타데이터(길이/시작점)도 부모 기준으로 잘못 들어온다 (Creative COW 보고, CS6 기준).

### 해결 — 후보클립을 "컷별 미니 시퀀스"로 재구성 (사용자 제안과 일치)

전문 변환 도구(XtoCC 등)도 같은 원리를 쓴다: **선택 구간은 클립이 아니라 시퀀스로 번역**하고,
Premiere가 가져오기 시 필요한 마스터 클립을 자동 생성하게 한다.

목표 구조 v2:

```text
00_원본        → 마스터 클립 1개 (전체 영상, 파일 리소스 등록용) — 그대로
01_후보클립    → 컷마다 독립 미니 시퀀스 1개 (해당 구간만 타임라인에 배치)
02_시퀀스      → 전체 러프컷 시퀀스 (13컷 연결) — 그대로
```

- 시퀀스의 in/out은 Premiere가 정확히 해석하므로 구간 경계가 확실히 보존된다.
- 편집 시 후보 구간을 더블클릭하면 해당 구간만 타임라인으로 열림 → 원하는 부분을 러프컷 시퀀스로 복사/조정.
- 원본 파일 리소스 등록은 `00_원본` 마스터 클립 1개로 유지 (사용자 의도와 동일).

## 적용 계획

1. `make_premiere_xml.py` 수정 전 `temp/backups/2026-07-02/`에 백업.
2. 수정 v2: 트랙 상태 요소 추가 + 후보클립을 컷별 미니 시퀀스로 변경.
3. 1컷 테스트 XML(`_MP4_V2`) 재생성 → 구조 파싱 검증(Syntax-validated).
4. Premiere 가져오기 재검증: 스피커 토글 켜짐, 후보클립이 구간 시퀀스로 들어오는지 (App-validated).
5. 통과 시 13컷 전체 XML 재생성 (기준 컷리스트 1번 컷 02:15:23-02:17:42 갱신 포함).

## 출처

- [Premiere 실제 내보내기 xmeml 전문 예시 (track enabled/outputchannelindex/outputs 구조)](https://gist.github.com/boredstiff/63c9d4f8f7bca48c3e5441326ae8ce69)
- [Apple FCP7 XML Interchange Format 공식 문서](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/FinalCutPro_XML/Elements/Elements.html)
- [Creative COW — FCP7 to Premiere CS6 XML 서브클립 Out점/메타데이터 버그](https://creativecow.net/forums/thread/fcp7-to-premiere-cs6-via-xml-strange-subclip-behav/)
- [XtoCC — 선택 구간을 시퀀스로 번역, Premiere가 가져오기 시 클립 자동 생성](https://www.intelligentassistance.com/xtocc-help/)
