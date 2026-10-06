# 백룸 Premiere import probe v2 보고서

- 목적: 실패한 전체 편집 XML과 편집 내용 변수를 분리하고, v18 계열 구조 자체를 Premiere가 받아들이는지 최소 단위로 확인한다.
- 상태: `app-import: passed`, `playback/meaning/approval: not_run`
- 결과: `outputs/07_edit_export/backrooms_premiere_import_probe_v2.xml`
- SHA-256: `034caee3b9b0465431943179672b5c2276aab7a9e4d307bab1882081ecb0e6b1`

## 제작 방식

새 generator 출력을 사용하지 않았다. `inputs/2026-06-30 00-23-03.full-edit-v18.xml`의 project, master clip, file metadata, sequence, track, clipitem, link 구조를 그대로 복제한 뒤 다음 변경만 적용했다.

- 첫 video clip 하나와 정확히 연결된 stereo audio clip 두 개만 유지
- sequence 이름과 UUID를 새 fixture용 값으로 변경
- sequence duration을 첫 clip의 2,369 frames로 축소
- source `pathurl`을 현재 worktree의 승인된 MP4로 변경
- XML 선언과 `<!DOCTYPE xmeml>`을 v18과 동일하게 유지

편집 후보가 아니므로 서사·리듬·완성도 판단에는 사용하지 않는다.

## 로컬 검증

| 항목 | 결과 |
|---|---|
| XML header | `<?xml version="1.0" encoding="UTF-8"?>`, `<!DOCTYPE xmeml>` |
| XMEML | version 4, sequence 1 |
| clips | video 1, audio track 2, audio clip 2 |
| timeline | 0–2,369 frames |
| source | 19,495–21,864 frames |
| file definition | 1, 현재 MP4 경로 존재 |
| links | 누락 target 0 |
| v18 schema drift | v18에 없는 element path 0 |
| audio metadata | `file/media/audio/channelcount` 1, 잘못 중첩된 channelcount 0 |
| timecode reel | 1 |
| 직렬화 | 258 lines, 최대 128자 |

로컬 검증 뒤 사용자가 `호환돼`라고 확인해 Premiere import는 통과로 기록한다. 이 확인은 가져오기 호환성만 증명하며, 정상 재생·편집 의미·완성도·최종 승인을 뜻하지 않는다.

## v1 중단 사유

`backrooms_premiere_import_probe_v1.xml`은 앱에 전달하기 전 로컬 preflight에서 DOCTYPE이 `<!DOCTYPE xmeml []>`로 직렬화된 것을 발견했다. 직접 원인으로 확정한 것은 아니지만 v18과 구조를 완전히 맞추려는 시험 목적에 어긋나므로 중단했다. v2는 이를 바로잡은 새 파일이다.

## 다음 게이트

1. v2 구조를 생성기 회귀 기준으로 구현한다. 완료.
2. 생성기가 만든 별도 1-clip fixture도 Premiere import를 통과해야 한다.
3. 그 뒤에만 전체 단일 sequence의 새 revision을 만든다.

현재 fixture에는 `current`, 편집 방향 `approved`, `final` 지위가 없다.
