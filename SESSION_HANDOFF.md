# SESSION_HANDOFF.md — 김실버유튜브

최종 갱신: 2026-07-05 (Claude Cowork 세션 — srt 반영 → dB·자막·화면 3중 재분석 → 러프컷 기획 v1~v5 → Premiere XML v5 생성 완료. **Premiere 실제 가져오기 미검증**)

규칙 원본:
- Tier-1: `C:\Users\Hugh\Claude\Projects\Building WorkFlow\PROJECT_RULES.md`
- Tier-2: 이 폴더의 `PROJECT_RULES.md` / `00_공통_작업원칙.md` / `01_유튜브_제작_워크플로우.md`
- **이번 세션에 Tier-2에 '영상 길이 원칙' 신설(사용자 확정):** 길이 고정 목표 금지, 재미·퀄리티 기준 컷 선별의 결과로 확정. 문서에 길이는 '참고 측정치'로만 기록.

## 현재 진행 영상

- 원본: `workspace/inputs/2026-06-30 00-23-03.mp4` (82:04 · 1080p60 · 무수정 참조만)
- 자막: `workspace/inputs/2026-06-30 00-23-03.srt` (사용자 PC 생성, 760블록) — **도착·반영 완료. 전사 재생성 금지, 이 파일이 기준.**
- 게임: Escape the Backrooms. **솔로 플레이+시청자 채팅 소통 방송**(졸려님 공략 도움). 이전 핸드오프의 "co-op 2인" 추정은 대사로 오류 확인됨.
- 방향: 공포 리액션 하이라이트 + **영화 백룸 연결이 뼈대** (아래 기획 참조)

## 이번 세션 완료 작업

1. **srt 교차 반영:** `round_map.csv`(기준 컷리스트) 19→26행 정밀화. 모든 하이라이트에 대사 근거 부착.
2. **dB·자막·화면 3중 재분석 신규 발견:**
   - 14:07 = 전체 최대 음량(-7.7dB) 찐텐 비명 — 기존 분석 누락분
   - 29:29 = "열쇠 발견"이 아니라 **엔티티 정면 풀스크린 점프스케어**(-10.5dB, 썸네일 후보 `temp/video-watch/dialog-check/n4_key_2929.jpg`)
   - 43:18~43:54 = 사망 이벤트 확인(43:47 인벤토리 화면)
3. **리서치 2건:** `기획_리서치/백룸_시청자층_리서치_2026-07-05.md`
   - 영화 백룸(A24·케인 파슨스) 5/27 한국 최초 개봉→100만 관객, 6/29 확장판 재개봉 발표. 게임 플레이어 +132%. **지금이 업로드 적기.**
   - 타깃: 2030 영화 유입층+리미널 스페이스 감성층+로어 팬. 2차(5절): 간접 체험·의미 있는 정적·빈 공간 응시가 몰입 핵심.
4. **러프컷 기획 v1→v5:** `workspace/outputs/analysis/02_러프컷_편집기획.md` (v5, 56컷)
   - v2: 영화·로어 연결고리 10비트 승격(인트로 풀버전, 44:25 영화감상 토크 등)
   - v3: 훅 = 비명 3연타 몽타주 약 20초(29:27/43:29/50:23), 사용자 요청 "10초 이상"
   - v4: 1막을 '첫 탐험 몰입 시퀀스'로 재구성 — 7:12 "소름 돋는다, 이 커다란 공간에 아무도 없다" 등 탐험 소감 11컷 복원
   - v5: 토크 구간(01·31·38) 점프컷 분해 — 무음 1.2~4.5초 제거·중복 문장 삭제·잘린 내용 복원("어두운 방에서 혼자", "누가 들어오면 개무섭겠다" 솔로 설정). 기법은 기획서 4b절.
5. **XML 생성:** `workspace/outputs/premiere_export/백룸_러프컷_v1~v5.xml` — **최신 v5(56컷, 약 20:35, 시퀀스 `02_시퀀스_러프컷v5`)**. `skills/premiere-editing-export` 스킬 사용, pathurl Windows 치환·파싱 검증 완료. 안내: 같은 폴더 `백룸_러프컷_사용방법.md`.

## 컷리스트 파일 관계 (헷갈림 방지)

- `workspace/outputs/analysis/round_map.csv` — **분석 기준**(구간·근거·keep/maybe 판단, 26행)
- `workspace/outputs/analysis/roughcut_cutlist.csv` — **XML 생성용 실행 컷리스트**(v5, 56컷, 라벨=XML 클립명)
- 수정 순서: 화면/자막 근거 변경 → round_map 갱신 → roughcut_cutlist 반영 → XML 재생성 (헤더 컷 수·총 길이 검산 후)

## 다음 세션 할 일

1. **사용자 Premiere CS6에서 v5 가져오기 확인** — 확인 전까지 "사용 가능 확정" 표현 금지(Tier-2 App-validated 규칙).
2. 사용자와 ◇ 선택 컷 취사(참고: ◆만 약 12분, 전체 약 20:35). 줄일 때 ◇리액션→◇개그→◇로어 순, **탐험 소감·영화 연결고리는 최후 보존.**
3. 제목·썸네일 확정(방향: 영화 백룸 검색 편승, 리서치 문서 4절. 썸네일 후보 n4 엔티티 정면).
4. 확정 후 필요 시 러프컷 mp4(`make_roughcut.py`) 또는 최종 XML 재생성.

## 환경·도구 주의 (이번 세션 재확인)

- **Windows→샌드박스 동기화 버그 실재:** Write로 만든 round_map.csv가 샌드박스에서 11행으로 깨져 보였으나 Windows 원본은 정상(26행). 샌드박스에서 읽을 파일은 heredoc으로 생성, 검증은 Read 도구(Windows 쪽)로.
- 샌드박스 네트워크: pypi·github만. 전사/모델 다운로드 불가(상세: `reports/whisper_medium_사용법_리서치.md`). srt 도착으로 이번 영상에선 더 이상 불필요.
- XML pathurl 치환 sed: `s|file://localhost//sessions/<세션>/mnt/|file://localhost/C:/Users/Hugh/Claude/Projects/Building%20WorkFlow/Workspace/|`
- 검증 프레임: `temp/video-watch/dialog-check/`(14장 추가: n1~n5·s4~s8·b_*), 기존 overview/·reactions/.
- CS6 오디오 모노 2트랙·`.bat`만 사용 등 편집 환경 전제는 Tier-2 PROJECT_RULES 참조.

## 백업 (temp/backups/2026-07-05/)

round_map.csv(2회)·01_흐름표·02_기획서(2회)·roughcut_cutlist(3회: v2/v3/v4)·영상_1편_제작_템플릿·PROJECT_RULES·SESSION_HANDOFF(금일분).

## 다음 세션 시작 프롬프트

```text
Tier-1/Tier-2 PROJECT_RULES.md와 SESSION_HANDOFF.md를 읽고 이어서 진행.
진행 영상: workspace/inputs/2026-06-30 00-23-03.mp4 (Escape the Backrooms, 82분, 솔로+채팅 방송).
상태: 러프컷 기획 v5 + 백룸_러프컷_v5.xml(56컷) 생성 완료, Premiere 가져오기 확인 대기.
사용자 확인 결과 듣고 → ◇ 컷 취사선택 → 제목·썸네일 → 필요 시 XML/러프컷 mp4 재생성.
길이는 고정 목표 없음(Tier-2 '영상 길이 원칙'). 컷 수정은 round_map → roughcut_cutlist → XML 순서.
```
