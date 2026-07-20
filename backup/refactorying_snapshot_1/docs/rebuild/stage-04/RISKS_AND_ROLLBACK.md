# Stage 04 위험과 롤백

## 미해결 위험

1. **실제 미디어 미검증**: 특성 테스트는 레거시 테스트 기대값 기준. 실제 영상
   파일(ffprobe/ffmpeg 실행 포함)과 Premiere 가져오기 검증은 Stage 05 파일럿
   범위. `FfprobeMediaProbe`·`extract_pcm`은 스텁 없이 실기기 검증 필요.
2. **독립 QA·레드팀 미실행** (Stage 02~04 공통, 사용자 결정 대기).
3. **원격 CI 미실행**: 커밋·푸시 승인 대기에 종속.
4. **Windows 실제 환경 재검증 대기**: Linux clone 기준 통과. 특히 os.replace
   원자성, 한글 경로, git cat-file 동작을 Windows에서 1회 확인할 것.
5. 매니페스트 v3는 git 저장소 존재를 전제(비-git 배포 검증은 범위 밖).
6. 레거시 대비 의도 변경 5건은 STAGE_REPORT에 기록 — 의미 승인은 사용자 지시
   ("매니페스트 재작성하고 Stage 04 진행해")로 갈음하되 이의 시 재조정.

## 롤백

- 지점 `d5f5fb5`. 절차는 STAGE_REPORT 롤백 절 참조.
- 실제 작업 DB·미디어 미사용이므로 데이터 롤백 없음.

## 증거

- `evidence/clean_clone_gate_full_check.json` (be0aeac1…) — 매니페스트 재작성 후
  clean-clone 게이트 full check rc=0.
- `evidence/check_full_after_stage04_clean_clone.json` (01d486df…) — Stage 04
  구현 후 스테이지 말 통합 full check rc=0 (159 passed, 1 skipped).
