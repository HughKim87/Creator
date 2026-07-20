# Stage 03 위험과 롤백

## 미해결 위험

1. Stage 02에서 이월: BACKUP_MANIFEST 줄바꿈 휴대성 결함(사용자 결정 대기),
   독립 QA/레드팀 미실행, Git 커밋 미실행(index.lock 잔존 포함).
2. Windows 실제 환경 재검증 미실행: 이번 통합 검증은 Linux clone 기준.
   경로 처리(한글·공백)는 테스트했으나 Windows 고유 동작(파일 잠금, os.replace
   원자성)은 다음 Windows 세션에서 통합 1회로 확인 필요.
3. 사람 승인 provenance는 TTY+challenge 기반: 플랫폼 검증 가능 사용자 이벤트
   어댑터가 생기면 교체·강화 예정. 현 방식은 로컬 위협 모델에서만 유효.
4. `retry` 실패 카운터(동일 objective 3회 중단)는 도메인 실패 원장 조회로 구현
   가능하나 자동 강제는 미구현 — Stage 04에서 실행 계층과 함께.
5. 동시성 테스트는 순차 시뮬레이션(같은 버전 로드 후 순차 커밋) 기준. 실제
   병렬 프로세스 경합은 busy_timeout 경로까지 포함해 Stage 05 파일럿에서 관찰.

## 롤백

- 롤백 지점: `d5f5fb5`. 코드 롤백 절차는 STAGE_REPORT 참조.
- 작업 DB 롤백: 해당 없음(실제 사용자 DB 미생성).
- 마이그레이션 백업 규약: `workflow.sqlite.bak-v<N>` 생성 후 적용, 실패 시 자동
  복원(단위 테스트 보장).

## 증거

- `evidence/check_full_after_stage03_clean_clone.json`
  (SHA-256 96ba9cdb6b7bd1a8b7bca1af2861c5781c71270ab06c6adea9256c676891c52c)
