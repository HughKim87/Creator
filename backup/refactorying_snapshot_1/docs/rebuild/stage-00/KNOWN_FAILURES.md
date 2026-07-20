# Stage 00 알려진 결함과 미검증 위험

## 1. 해석 규칙

- `STATIC_CONFIRMED`: 소스에 해당 분기나 누락이 직접 보인다.
- `STATIC_INFERENCE`: 운영 결과는 아직 재현하지 않았지만 코드 흐름상 위험이 있다.
- `OBSERVED`: 격리 실행에서 실제 종료 코드나 결과를 재현했다.
- `UNAVAILABLE_POLICY_BOUNDARY`: 실행 자체가 사용자 데이터 경계를 침범해 중단했다.

## 2. 결함 원장

| ID | 영역 | 정적 사실과 예상 영향 | 수준 | 후속 단계 |
|---|---|---|---|---|
| KF-00-01 | 실행 증거 | 74개 중 안전한 45개는 직접 실행 통과, 29개는 fixture/도구가 금지 경로를 생성·조회해 실행 불가 | `OBSERVED` / `UNAVAILABLE_POLICY_BOUNDARY` | Stage 01에서 데이터 비의존 fixture로 재설계 |
| KF-00-02 | remux | `remux_mkv_to_mp4.bat`는 개별 FFmpeg 오류를 출력하지만 실패를 누적하거나 마지막에 `exit /b 1` 하지 않음. `[ALL DONE]` 뒤 성공처럼 보일 수 있음 | `STATIC_INFERENCE` | Stage 01/04에서 fail-closed 래퍼와 회귀 테스트 |
| KF-00-03 | Premiere XML | ffprobe가 없거나 실패하면 `make_premiere_xml.py`가 30fps/1920x1080/48kHz/2ch 기본값으로 계속 생성 | `STATIC_CONFIRMED`; 잘못된 XML 결과는 미실행 | Stage 04에서 probe 실패 차단 또는 명시적 승인 fallback |
| KF-00-04 | source identity | 원본 지문이 파일 크기와 mtime에 의존하며 원본 콘텐츠 해시는 매니페스트 필드에 없음 | `STATIC_CONFIRMED` | Stage 02/04에서 immutable source hash 계약 |
| KF-00-05 | 자산 원자성 | 프레임 파일을 먼저 만들고 여러 처리 후 매니페스트를 append하므로 중단 시 미등록 파일이 남을 수 있음 | `STATIC_INFERENCE` | Stage 03/04에서 staging+승격·복구 테스트 |
| KF-00-06 | 승인 신뢰 경계 | revision 상태 `approved`, baseline pointer, workflow 승인 boolean을 이벤트/JSON 작성자가 설정할 수 있고 사람 승인 provenance 검증이 없음 | `STATIC_CONFIRMED` | Stage 02/03의 사람 승인 provenance 계약 |
| KF-00-07 | A/V 승인 | edit memory에서 실제 A/V 관찰 누락은 검증 오류가 아니라 경고이며, 사용자/에이전트 문자열 값의 권한 검증도 없음 | `STATIC_CONFIRMED` | Stage 03/05에서 final 승격 하드 게이트와 실제 사용자 승인 |
| KF-00-08 | `default_deny` | 계약 JSON에는 `default_deny=true`가 있으나 workflow gate가 이 필드를 직접 확인하는 코드와 회귀 테스트를 찾지 못함 | `STATIC_CONFIRMED` | Stage 02 특성 테스트 후 이식 |
| KF-00-09 | 품질 감사 종료 코드 | `REVIEW` findings가 있어도 `edit_quality_audit.py`는 보고서만 출력하고 정상 종료하므로 자동 게이트가 종료 코드만 보면 승인으로 오해할 수 있음 | `STATIC_INFERENCE` | Stage 04에서 보고용/게이트용 모드 분리 |
| KF-00-10 | sync 의존성 | synccheck는 전용 테스트가 없고 일부 도구는 `numpy`, `webrtcvad`, 시스템 PATH의 `ffmpeg`에 의존함. README 예시는 bundled FFmpeg를 명시하지 않음 | `STATIC_CONFIRMED`; 환경 실패 미실행 | Stage 01 잠금 의존성, Stage 04 합성 fixture |
| KF-00-11 | sync 판정 | VAD 경고는 제안 출력이며 위험을 발견해도 정상 종료하는 구조라 자동 차단 명령으로 사용할 수 없음 | `STATIC_CONFIRMED`; 의도된 advisory인지 사용자 의미 확인 필요 | Stage 02/04에서 advisory와 gate 계약 분리 |
| KF-00-12 | 래퍼 자식 코드 | 자식 `7`이 래퍼 최종 `0`으로 바뀌었다. 괄호 블록의 `%ERRORLEVEL%` 선확장으로 거짓 성공 발생 | `OBSERVED` | Stage 01 fail-closed 래퍼와 회귀 테스트 |
| KF-00-13 | 중첩 루트 결합 | legacy 도구는 자신의 상위 폴더를 프로젝트 루트로 계산한다. `backup/`에서 Git을 호출하면 계산 루트는 `backup/`, 실제 Git 루트는 부모라 safe.directory·상태 범위가 어긋날 수 있음 | `STATIC_INFERENCE`; 실행 금지로 미재현 | legacy SHA 별도 worktree에서만 직접 실행 |
| KF-00-14 | Windows 한정 래퍼 | `test_tool_wrappers.py` 래퍼 클래스는 Windows가 아니면 skip됨 | `STATIC_CONFIRMED` | Windows와 CI 플랫폼을 분리 검증 |
| KF-00-15 | guard fail-open | `agent_guard.py`는 malformed input, Git/doccheck 실행 예외, 검사기 결손을 성공으로 허용하도록 명시됨 | `STATIC_CONFIRMED` | Stage 01 fail-closed 기반으로 교체 |
| KF-00-16 | 현재 루트 훅/CI | 현재 루트 pre-commit은 검사기 결손/Python 결손을 성공 처리하며, CI는 현재 없는 루트 `tools/`, `tests/`를 참조 | `STATIC_CONFIRMED`; 원격 CI 미확인 | Stage 01 |
| KF-00-17 | Premiere 앱 검증 | XML 테스트는 ElementTree 구조만 검사하고 실제 Premiere import, 렌더, 연속 A/V를 확인하지 않음 | `STATIC_CONFIRMED` | Stage 04 구조 비교, Stage 05 앱·사람 A/V |
| KF-00-18 | remux 보존 검증 | remux에 입력/출력 stream·duration·timestamp 동등성 검사와 전용 테스트가 없음 | `STATIC_CONFIRMED` | Stage 04 합성 MKV fixture와 ffprobe 비교 |

## 3. 실행 경계

격리 worktree에서 안전한 코드·테스트만 실행했다. doccheck, preflight, workflow gate,
projectctl verify와 29개 테스트는 금지 경로를 실제로 생성·조회하도록 설계되어 실행하지
않았다. 미디어·Premiere·원격 CI도 검증하지 않았다. 상세 근거는
`evidence/behavior_execution_results.txt`에 있다.

## 4. 다음 단계로 넘기면 안 되는 해석

- 정적 테스트가 존재한다는 사실은 통과 증거가 아니다.
- XML 생성은 Premiere import 또는 영상·음성 품질 승인이 아니다.
- `actual_av_observed=true` 문자열/boolean은 사람의 실제 승인 provenance가 아니다.
- 품질 보고서 생성 성공은 `REVIEW` 해소가 아니다.
- synccheck의 정상 종료는 발화 경계가 안전하다는 뜻이 아니다.
- `[ALL DONE]` 문구는 remux 자식 작업이 모두 성공했다는 증거가 아니다.
