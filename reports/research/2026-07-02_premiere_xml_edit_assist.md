# Premiere XML 편집 준비 패키지 리서치 보고

- 작성일: 2026-07-02
- 주제: 크레이지아케이드 플레이 영상 컷편집 자동화 대안
- 결론: 최종 컷편집 영상을 자동 완성하기보다, Premiere에서 바로 다듬을 수 있는 `원본 + 후보클립 + 연결 시퀀스` 패키지를 자동 생성하는 방식이 적합하다.

## 핵심 결론

- 사용자가 기억한 “가져오기만 하면 원본, 후보 클립, 연결된 시퀀스가 들어오는 파일”은 EDL보다는 Final Cut Pro 7 XML(`xmeml`) 계열일 가능성이 높다.
- EDL은 단순 컷 시퀀스 교환에는 쓸 수 있지만, 후보 클립/빈/구조화된 편집 재료를 담기에는 제한적이다.
- XML은 완성본 자동화가 아니라 “편집자 검토용 프로젝트 구조”를 만드는 데 더 맞다.
- 따라서 자동화 목표는 `AI가 최종본 생성`이 아니라 `AI가 Premiere에서 빠르게 고칠 수 있는 편집 초안 구조 생성`으로 잡는 것이 안전하다.

## 적용한 워크플로우

1. 자막/음성/화면 검증으로 컷 후보를 만든다.
2. 컷리스트 CSV를 확정한다.
3. `make_premiere_xml.py`로 Premiere XML을 생성한다.
4. Premiere에서 XML을 가져온다.
5. `00_원본`, `01_후보클립`, `02_시퀀스`를 확인한다.
6. 컷 경계, 재미 포인트, 라운드 결과 보존 여부를 사람이 다듬는다.

## 이번 산출물

- XML 생성 도구: `skills/premiere-editing-export/scripts/make_premiere_xml.py`
- 1컷 테스트 XML: `workspace/outputs/크레이지아케이드_영상/크아_컷편집_러프/premiere_export/CRA_PLAY_EDIT_ASSIST_3P_TEST.xml`
- 13컷 전체 XML: `workspace/outputs/크레이지아케이드_영상/크아_컷편집_러프/premiere_export/CRA_PLAY_EDIT_ASSIST_V1.xml`
- 사용 방법: `workspace/outputs/크레이지아케이드_영상/크아_컷편집_러프/premiere_export/CRA_PLAY_EDIT_ASSIST_V1_사용방법.md`

## 리서치 근거

- Adobe Premiere는 Final Cut Pro XML 내보내기/가져오기 흐름을 지원한다.
  - https://helpx.adobe.com/premiere/desktop/render-and-export/export-files/export-a-project-as-a-final-cut-pro-xml-file.html
- FCPX의 `.fcpxml`은 Premiere가 직접 읽는 표준 XML과 달라 변환이 필요하다. 이번 도구는 `.fcpxml`이 아니라 Premiere 호환을 목표로 한 `xmeml` 구조다.
  - https://helpx.adobe.com/premiere/desktop/organize-media/import-files/migrate-from-final-cut-pro-x.html
- Adobe는 EDL을 단순 프로젝트에 적합한 방식으로 설명한다. 후보 클립/빈/복수 구조를 담는 목적에는 XML이 더 적합하다.
  - https://helpx.adobe.com/premiere/desktop/render-and-export/export-files/export-a-project-as-an-edl-file.html
- Premiere 스크립팅 API에도 파일 가져오기, 클립 기반 시퀀스 생성 기능이 있으나, 사용자가 “가져오기” 방식으로 쓰길 원하므로 JSX는 1차 방식에서 제외했다.
  - https://ppro-scripting.docsforadobe.dev/general/project/

## 레드팀

- XML 문법 검사는 통과했지만, 실제 Premiere 가져오기 성공은 아직 사용자의 Premiere 환경에서 검증해야 한다.
- MKV는 Premiere 환경에 따라 연결이 불안정할 수 있다. 실패하면 원본을 ProRes/DNxHR 같은 편집용 중간 파일로 별도 변환하고 XML을 다시 만드는 편이 낫다.
- XML은 컷 순서와 원본 참조를 만드는 도구다. 화면 의미 판단, 재미 포인트 판단, 라운드 결과 보존 여부는 여전히 화면 검증과 사람 검수가 필요하다.
- 자동 컷 경계가 너무 타이트하면 반응/결과가 잘릴 수 있으므로, 후보 XML은 “조금 넉넉한 러프컷”으로 만들고 Premiere에서 줄이는 방향이 안전하다.

## 다음 권장 작업

- Premiere에서 `CRA_PLAY_EDIT_ASSIST_3P_TEST.xml`을 먼저 가져와 구조와 미디어 연결을 검증한다.
- 1컷 테스트가 성공하면 `CRA_PLAY_EDIT_ASSIST_V1.xml`을 가져와 13컷 전체 타임라인을 다듬는다.
- Premiere가 XML을 거부하거나 미디어 연결이 불안정하면, 기존 EDL 경로 또는 편집용 중간 파일 변환 경로로 전환한다.
