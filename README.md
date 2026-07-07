# 김실버 유튜브 작업 폴더

> **프로젝트 계층**: 이 프로젝트는 상위 프로젝트 **Building WorkFlow**의 하위 프로젝트다.
> 위치: `Building WorkFlow/Workspace/김실버유튜브/`
> 상위 프로젝트의 공통 규칙(보안 > 정확성 > 비용, 수정 전 백업)이 이 폴더의 모든 작업에 적용되며,
> 충돌 시 상위 규칙이 우선한다. 이 폴더의 `00_공통_작업원칙.md`는 그 아래 단계의 원칙이다.

- 재구성일: 2026-07-02
- 원본 출처: `C:\Codex\Backup\김실버 유튜브\` (Codex CLI 시절 백업 → 이 폴더로 이관, 원본 폴더는 삭제 예정)
- 채널: 신입 아재 유튜버, 김실버😎 (https://youtube.com/channel/UCp9Pn5dAUByhBDkH1K59HiQ)
- 이관 시점 기준: 구독자 611명, 영상 245개, 총 조회수 약 142만

## 폴더 구성

| 위치 | 내용 |
|---|---|
| `PROJECT_RULES.md` | 이 프로젝트의 전역 지침 원본 (유일한 수정 지점) |
| `문서_인덱스.md` | 현재 기준/현재 작업/참고/대체 문서를 구분하는 단일 진입점 |
| `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` | 플랫폼별 포인터 — `PROJECT_RULES.md`를 가리키기만 함 |
| `00_공통_작업원칙.md` | 원본 보호, 파일 생성/삭제, 의도 확인 규칙 (모든 작업의 최상위 안전장치) |
| `01_유튜브_제작_워크플로우.md` | 제작 7단계: 소재조사 → 기획 → 대본 → 자막 → 영상분석 → 편집자료 → 검수 |
| `skills/` | 작업용 스킬 5종. 구버전 .skill 백업은 `temp/archive/2026-07-08/skills/temp_backup/`로 이동 |
| `tools/` | 프로젝트 내부 휴대용 도구. 현재 FFmpeg 8.1.2 essentials 설치됨 (`tools/README.md` 참고) |
| `workspace/` | Git에 올리지 않는 로컬 작업 공간. 원본은 `workspace/inputs/`, 현재 기준 산출물은 `workspace/outputs/`에 둠 |
| `기획_리서치/` | 현재 기준 기획 규격과 운영 진단만 유지. 구 리서치는 `temp/archive/2026-07-08/기획_리서치/`에 보관 |
| `temp/archive/2026-07-08/` | 2026-07-08 정리로 이동한 구 리서치, 구 출력물, 캐시, 구 스킬 백업, FFmpeg 부속 문서 |

원본 백업에서 제외한 것: 구 `.tools/`(ffmpeg 실행파일 — 현재 `tools/ffmpeg/`에 재설치됨),
`subtitle_recovery_work/pydeps*`, `hf_cache`(파이썬 패키지·Whisper 모델 캐시 — 재설치 가능),
`.git`, `.codex`, `.agents`(빈 폴더 또는 Codex 환경 잔재). 스크립트와 로그는 보존함.

## 채널 방향 (확정된 결론)

> 김실버는 게임을 리뷰하는 사람이 아니라,
> 게임이 유저의 기대를 어떻게 배신하는지 해부하는 사람.

- 잘 되는 것: 게임사 운영 논란·배신감 해부형 (리니지 자동사냥 3.2만, 솔 인챈트 2.6만, NC 신뢰 붕괴 2.1만)
- 안 되는 것: 맥락 없는 플레이 일지형 (100~300회)
- 시청자가 김실버에게 기대하는 것: "같이 상처받은 사람"의 시선, 빠른 렉카가 아닌 "겪어본 유저의 구조 해설"

## 현재 상태

- 진행 중인 작업: 백룸 영상 5단계 기획서 확인. 현재 기준 산출물은 `workspace/outputs/analysis/08_백룸_기획서_대사스파인_2026-07-07.md`.
- 다음 단일 작업: 기획서가 원본 대사 기반 메시지로 적절한지 확인한 뒤, 승인되면 6단계 화면 검증으로 이동.
- 구 러프컷 v12 XML/컷리스트는 `temp/archive/2026-07-08/workspace/outputs/`에 보관된 참조용이며 Premiere 미검증. 기획서 승인 전 편집 재개 금지.
- 작업용 스킬 5종: `game-trend-research`, `youtube-channel-planning`, `gameplay-video-analysis`, `video-watch`, `premiere-editing-export` (상세는 `skills/README.md`).
- 새 영상은 원본을 `workspace/inputs/`에 넣고 워크플로우 1단계(촬영본이면 5단계)부터 시작.

## 작업 시 규칙

- 이 폴더의 `00_공통_작업원칙.md`가 최우선. 특히: 원본(mkv, srt, 사용자 작성 파일) 절대 덮어쓰지 않기, 산출물은 새 파일로.
- 상위 프로젝트(Building WorkFlow) 공통 규칙도 적용됨: 보안 > 정확성 > 비용, 수정 전 백업.
