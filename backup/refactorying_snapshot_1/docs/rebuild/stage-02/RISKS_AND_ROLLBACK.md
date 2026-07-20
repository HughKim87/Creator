# Stage 02 위험과 롤백

## 미해결 위험

1. **BACKUP_MANIFEST.json 휴대성 결함 (Stage 00 산물, 신규 발견)**
   매니페스트 해시가 Windows worktree 바이트(CRLF) 기준이라 `.gitattributes`
   정규화(eol=lf)가 적용되는 fresh clone에서 `backup_baseline`이 71건 불일치로
   실패한다. 콘텐츠는 git blob 수준에서 동일함을 확인했다. 이대로면 후속
   clean-clone 게이트가 통과할 수 없다. 처리 방안(예: git blob OID 기준 재작성
   또는 정규화 해시)은 Stage 00 기준선 정책 변경이므로 사용자 결정 항목이다.
2. **사용자 의미 승인 미완료**: 지시서 10절 게이트. `CONTRACT_MAPPING.md` 11절의
   7개 항목이 미승인 상태다. 이 승인 없이 Stage 03을 시작하지 않는다.
3. **독립 QA 미실행**: 구현·자가검증만 완료. 계획 4절에 따라 별도 검증/레드팀
   역할의 재실행이 남아 있다.
4. **provenance의 구조적 한계**: 도메인은 HUMAN 승인의 provenance 필드
   존재를 강제할 뿐 암호학적 신원 증명은 하지 않는다. 세션 검증은 응용/저장
   계층(Stage 03+) 책임으로 명시했다.
5. **검증 환경 차이**: 이번 검증은 Linux 샌드박스 clone에서 수행했다(Python
   3.12.3). Windows 실제 환경 재실행은 다음 Windows 세션에서 확인할 것.

## 롤백 지점과 절차

- 롤백 지점: 커밋 `d5f5fb5` (`feature/refactoring`, Stage 01 완료 체크포인트).
- Stage 02 산출물은 전부 신규 미추적 파일이므로 롤백은 다음 삭제로 충분하다:
  `src/video_workflow/domain/`, `tests/unit/domain/`, `tests/contract/domain/`,
  `tests/property/`, `tests/support/`, `docs/rebuild/stage-02/`의 신규 문서·증거.
- 기존 추적 파일 수정이 0건이므로 `git checkout`/`reset`은 필요 없다.
- 저장 DB가 없으므로 데이터 마이그레이션 롤백은 발생하지 않는다.

## 실패 증거 보존

- 게이트·검증 JSON과 SHA-256: `evidence/` 참조
  (`gate_doctor_clean_clone.json` d53d0781…, `gate_check_full_baseline_clean_clone.json`
  d291008a…, `check_full_after_stage02_clean_clone.json` 45b70627…).
