# Creator 단일 작업 공간

- 목적: main 하나에서 영상별 데이터와 공용 실행 자원을 분리하고 기존 worktree를 안전하게 통합한다.
- 읽는 시점: 새 영상 생성·재개, 공용 도구 설치, 저장소 정리·복구 시.
- 책임: 공통 코드는 main 유지보수 세션, 영상 데이터는 명시된 job ID의 작업 세션, 기존 자료 처분은 사용자.
- 상태: 단일 workspace 코드 구현 완료. 기존 자료 이전·삭제와 worktree 제거는 미승인.
- 관련 권위: 루트 PROJECT_RULES.md, core/PROJECT_RULES.md.

## 작업 계약과 단계

요청 결과는 브랜치별 재사용 개선을 main에 보존하고, 영상별 데이터가 섞이지 않는 작업 경로와 공용 도구 경로를 제공하며, main의 Git 상태를 깨끗하게 만드는 것이다. 기존 파일·worktree는 유지하고 외부 게시·push·Core 수정·자동 설치는 제외한다.

1. 복구 지점: `before`는 승인된 main 시작 커밋을 가리킨다. 다른 로컬 브랜치는 `before-<branch의 /를 -로 치환>` 태그로 고정한다. 태그와 원본 브랜치가 같은 커밋을 가리키는지 검사한다. Git 제외 데이터는 태그의 복구 범위가 아니므로 원래 위치에서 보존한다.
2. 개선 통합: 각 브랜치의 공통 조상 이후 변경을 현재 main과 비교한다. 이미 반영된 내용은 중복 적용하지 않고, 고유 공통 구현은 원본 SHA와 경로를 연결해 반영한다. 영상 자료·실서비스 실험은 코드와 분리한다. 관련 검사·앱 빌드를 통과한 뒤 독립 커밋으로 남긴다.
3. 구조 구현: 아래 작업 경로·공용 runtime·프로세스 잠금·제작 진입점을 적용한다. 서로 다른 두 합성 job의 병행 실행, 같은 job 중복 실행 차단, GPU 잠금, 실패·취소·재개, 경로 이탈 방지와 기존 계약 회귀를 확인한다. 필요한 코드만 커밋한다.
4. 정리 준비: 기존 작업별 최종 결과물·종속 자산·복구 근거·삭제 후보를 분리해 정확한 경로와 용량을 사용자에게 제시한다. 이동·삭제·worktree 제거는 별도 승인 후 진행한다. 최종 XML이 외부 PNG/WAV/원본을 참조하면 그 의존 파일도 최종 패키지의 일부다.

실패 시 해당 단계에서 멈추고 직전 커밋의 변경을 되돌리는 커밋으로 복구한다. `git reset --hard`와 `git clean -fdx`는 데이터 복구 수단이 아니다. `before`를 별도 경로에 checkout하면 공통 코드를 조사할 수 있지만 ignored 데이터는 원본 위치에서 별도로 복구해야 한다. 기존 worktree를 제거하기 전에는 미커밋·미추적·ignored 자료와 submodule의 독립 복구 수단을 확인한다. 현재 Git 복구 bundle과 검증 receipt는 Git 제외 `extension/data/consolidation/recovery/`에 있으며, 코드 복구는 이 bundle만으로 독립 검증했다. 미디어는 포함하지 않는다.

## 경로와 실행

`extension/jobs/<job-id>/`는 Git 제외 작업 루트다. job ID는 ASCII 소문자·숫자·하이픈으로 만든다. `job.json`, `state.md`, `inputs/`, `work/`, `outputs/`, `logs/`를 작업별로 소유한다. 다른 영상의 경로를 상대 참조하지 않는다. 작업 상태와 프로필은 전역 현재 작업 변수로 선택하지 않는다.

```powershell
python -B scripts/creator_job.py init --job 2026-10-21-example
python -B scripts/creator_job.py inspect --job 2026-10-21-example
python -B scripts/creator_job.py run --job 2026-10-21-example -- python -B <script.py>
python -B scripts/creator_job.py run --job 2026-10-21-example --gpu -- python -B <gpu-script.py>
```

run은 job 잠금을 잡고 root에서 자식 명령을 실행한다. `CREATOR_JOB_ID`, `CREATOR_JOB_ROOT`, `CREATOR_WORK_DIR`, `CREATOR_OUTPUT_DIR`, `CREATOR_LOG_DIR`, `TMP`/`TEMP`/`TMPDIR`을 전달한다. 하위 스크립트는 출력 옵션에 이 경로를 사용한다. 임의의 외부 프로그램 쓰기까지 OS sandbox로 격리하는 기능은 아니다. 실패·중단 시 작업 데이터는 남기고 잠금만 해제한다. GPU 작업은 `--gpu` 또는 공용 GPU lease를 사용한다.

공용 코드를 수정할 때 다른 세션의 실행을 중지하고 한 유지보수 세션만 Git을 변경한다. 처리 중인 job은 시작 시 코드 커밋과 runtime catalog digest를 기록하며, 다른 코드로 재개하려면 명시적으로 `--accept-code-change`를 사용한다. 단순 inspect는 파일을 만들거나 상태를 변경하지 않는다.

## 공용 runtime

정본 catalog는 `extension/config/workspace-runtime.json`이다. 기본 위치는 `extension/.runtime/{tools,models,environments,cache}`이며 버전별로 분리한다. 기존 설치가 있으면 catalog의 exact legacy 위치를 재사용한다. 기존 설치를 이동하거나 새 복사본을 자동 다운로드하지 않는다. 도구별 가상환경은 서로 합치지 않는다.

`python -B scripts/creator_job.py runtime --component qwen-tts`처럼 실행 경로를 조회한다. 경로만 확인하는 것은 설치·모델 로딩 성공 증거가 아니다. Windows venv는 이동 가능하다고 가정하지 않는다. 기존 모델의 bytes와 환경 호환성을 확인한 뒤 이전하거나 재구축한다. 설치 스크립트는 구성요소별 install lease와 GPU lease를 잡아 동시 설치·사용을 차단한다. 사용자 음성·토큰·브라우저 설정은 공용 모델 cache와 별개이며 자동 복사·공유하지 않는다.

## 최종 결과물과 Git

최종 결과물은 job의 `outputs/`에 둔다. NotebookLM 수동 업로드는 MP4·썸네일·SRT·수동 가이드 네 파일, Premiere는 최종 XML과 그것이 실제 참조하는 자산을 보존한다. 중간본을 확장자나 수정 시각만으로 자동 삭제하지 않는다. 판단 근거·승인·재현에 꼭 필요한 metadata는 사용자용 결과물과 구분하되 정리 전 복구 가능해야 한다.

`git status`가 깨끗한 상태와 디스크에서 ignored 자료를 제거한 상태는 별개다. `extension/jobs/`와 `.runtime/`는 Git 제외이고, 보호 원본·결과물은 커밋하지 않는다. 이전에 추적된 영상별 파일은 ignore 추가로 추적 해제되지 않는다. 해당 파일의 처분은 승인된 정리 단계에서만 한다.

로컬 음성 UI는 `scripts/Start-QwenTTS.cmd <job-id>`, Replier는 `scripts/Start-24HReplier.cmd <job-id>`로 연다. launcher는 기존 환경을 선택하며 모델을 자동 다운로드하지 않는다. 새 job의 음성 상태는 기존 개인 목소리를 자동 복사하지 않으므로 해당 작업에서 등록한다. 기존 개인 음성 저장소는 이전 승인 전 그대로 보존한다.

GPU UI launcher는 앱이 종료될 때까지 GPU lease를 유지한다. 다른 GPU 작업을 시작하려면 해당 UI를 종료한다. CPU 작업과 서로 다른 job의 데이터 처리는 병행할 수 있다.
