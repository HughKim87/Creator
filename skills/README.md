# Skills Index

이 폴더는 반복 영상 제작 작업에 사용하는 독립 스킬을 관리한다.

스킬을 만들거나 고칠 때는 `skills/SKILL_CONTRACT.md`를 먼저 읽고,
`skills/*/SKILL.md`에는 단계별 차이만 남긴다.

## 현재 운영 스킬과 보조 스킬

| 스킬 | 단계 | 역할 | 상태 |
|---|---:|---|---|
| `game-trend-research` | 1 | 소재 조사 | 1차 보강 완료 |
| `youtube-channel-planning` | 2 | 채널 기획 | 1차 보강 완료 |
| `youtube-script-planning` | 3 | 대본 구조, 주장 흐름, 장면 목적 | 1차 신설 완료 |
| `subtitle-cleanup` | 4 | 자막 생성/정리, 원문 보존, 타임코드 신뢰도 표시 | source_id 인계 반영 |
| `dialogue-based-planning` | 5 | 원본 대사 기반 컨트롤링 아이디어, 대사 스파인, 6단계 브리프 | source_id 인계 반영 |
| `gameplay-video-analysis` | 6 | 화면 검증, 후보 지도, 7단계 인계 브리프 | 원본 시간 자산 재사용 반영 |
| `video-watch` | 보조 | 영상 프레임 추출과 전사 보조 | 안정 경로·기존 결과 재사용 반영 |
| `premiere-editing-export` | 7 | 컷리스트를 Premiere용 XML/EDL/CSV/러프컷으로 변환 | 증분 검증·CURRENT 반영 |
| `final-video-review` | 8 | 최종 검수표, 수정 필요 목록, 업로드 전 확인 | 원본·렌더 증거 분리 반영 |
| `korean-game-research` | 보조 | 신작 게임 출시·업데이트·사전예약 리서치 → 구글 캘린더 등록(승인 후) | 복원 + SKILL_CONTRACT 정리 완료 |
| `youtube-timestamp-hashtag` | 보조 | YouTube Studio 설명란 타임스탬프/해시태그 자동화 (Chrome MCP) | 복원 + SKILL_CONTRACT 정리 + 저장 DOM 실측 검증(5~7단계) |

## 현재 상태

현재 1~8단계의 1차 스킬은 모두 존재한다.
공통 항목은 `skills/SKILL_CONTRACT.md`로 관리하고, 스킬 파일에는 해당
단계에서 달라지는 입력, 출력, 게이트만 둔다.

## 삭제된 구 자료

과거 구버전 `.skill` 파일은 현재 파일시스템에 남아 있지 않다. 삭제된 구 스킬 폴더도 기준 자료로 사용하지 않는다.
