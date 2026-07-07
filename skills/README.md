# Skills Index

이 폴더는 김실버 유튜브 작업에 사용하는 독립 스킬을 관리한다.

## 운영 기준 스킬

| 스킬 | 역할 |
|---|---|
| `game-trend-research` | 게임 트렌드, 랭킹, 유튜브 수요, 커뮤니티 이슈 조사 |
| `youtube-channel-planning` | 김실버 채널에 맞는 영상 콘셉트와 기획 구성 |
| `gameplay-video-analysis` | 긴 게임 플레이 영상을 저토큰 방식으로 분석해 후보 구간, 화면 검증, 라운드맵, 편집 컷리스트 생성 |
| `video-watch` | Claude가 영상을 직접 보게 하는 도구 (프레임 추출 + 전사). 로컬 mkv 화면 검증, 타 채널 벤치마킹에 사용. 원본: bradautomates/claude-video (MIT) |
| `premiere-editing-export` | 컷리스트를 Premiere용 XML 편집 패키지(원본/후보클립/시퀀스)와 보조 CSV/EDL/러프컷으로 변환 |

## 기존 스킬 백업

구버전 .skill 5종은 `temp/archive/2026-07-08/skills/temp_backup/`에 보관한다.

| 기존 스킬 파일 | 정리 방향 |
|---|---|
| `game-ranking-kr.skill` | `game-trend-research`로 통합 예정 |
| `korean-game-research.skill` | `game-trend-research`로 통합 예정 |
| `youtube-channel-coach.skill` | `youtube-channel-planning`으로 핵심 내용 이전 예정 |
| `youtube-game-review.skill` | `youtube-channel-planning`으로 통합 검토 |
| `youtube-timestamp-hashtag.skill` | 신규 스킬에 대응 없음. 업로드 단계가 필요해질 때 신규화 검토 |

기존 스킬은 기본 로드하지 않는다. 필요할 때만 아카이브에서 확인한다.
