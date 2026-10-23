# Creator 단일 작업 공간

- 목적: main 하나에서 영상별 데이터와 공용 실행 자원을 분리해 사용한다.
- 읽는 시점: 새 영상 생성·재개, 공용 도구 경로 확인·설치 시.
- 책임: 공통 코드는 main 유지보수 세션, 영상 데이터는 명시된 job ID의 작업 세션, 기존 자료 처분은 사용자.
- 상태: 단일 workspace 운영 구조 적용. 공용 도구는 main의 extension/.runtime에서 재사용한다.
- 관련 권위: 루트 PROJECT_RULES.md, core/PROJECT_RULES.md.

## 경로와 실행

공용 도구는 main의 `extension/.runtime/`에서 재사용한다. 새 영상의 데이터는 아래 job 경로에 생성한다. runtime catalog 조회만으로 도구가 설치되지는 않는다.

영상 작업용 채널 코치·게시 설명·쇼츠의 정본은 `.agents/skills/youtube-channel-coach/`·`.agents/skills/youtube-timestamp-hashtag/`·`.agents/skills/create-shorts/`다. 총괄과 전문 스킬의 프로젝트 상대 링크와 제작 묶음 검사를 사용하며 플러그인·개인 설치 업데이트를 프로젝트 스킬 갱신으로 취급하지 않는다. 설치 사본과 legacy `extension/skills/create-shorts/`는 실행 fallback이 아니다. 쇼츠 테스트도 `.agents/skills/create-shorts/`를 검증한다.

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

정본 catalog는 `extension/config/workspace-runtime.json`이다. 기본 위치는 `extension/.runtime/{tools,models,environments,cache}`이며 버전별로 분리한다. 기존 설치가 있으면 catalog의 exact legacy 위치를 재사용한다. 검증된 기존 설치를 공용 경로로 재사용하며 새 복사본을 자동 다운로드하지 않는다. 도구별 가상환경은 서로 합치지 않는다.

`python -B scripts/creator_job.py runtime --component qwen-tts`처럼 실행 경로를 조회한다. 경로만 확인하는 것은 설치·모델 로딩 성공 증거가 아니다. Windows venv는 이동 가능하다고 가정하지 않는다. 기존 모델의 bytes와 환경 호환성을 확인한 뒤 이전하거나 재구축한다. 설치 스크립트는 구성요소별 install lease와 GPU lease를 잡아 동시 설치·사용을 차단한다. 사용자 음성·토큰·브라우저 설정은 공용 모델 cache와 별개이며 자동 복사·공유하지 않는다.

## 최종 결과물과 Git

최종 결과물은 job의 `outputs/`에 둔다. NotebookLM 수동 업로드는 MP4·썸네일·SRT·수동 가이드 네 파일, Premiere는 최종 XML과 그것이 실제 참조하는 자산을 보존한다. 중간본을 확장자나 수정 시각만으로 자동 삭제하지 않는다. 판단 근거·승인·재현에 꼭 필요한 metadata는 사용자용 결과물과 구분하되 정리 전 복구 가능해야 한다.

동일 job의 롱폼 업로드 자료와 쇼츠 같은 복수 최종 결과는 첫 출력 전에 `outputs/upload/`·`outputs/shorts/`로 분리한다. job의 outputs root는 공통 경계로 유지하고 네 파일 검증·archive는 수동 패키지의 전용 `preparation.output_dir`에만 적용한다. 형제 결과를 정리하지 않으며, 기존 혼합 배치는 별도 확인 없이 이동하지 않는다. 단일 결과는 기존 배치를 유지한다.

`git status`가 깨끗한 상태와 디스크에서 ignored 자료를 제거한 상태는 별개다. `extension/jobs/`와 `.runtime/`는 Git 제외이고, 보호 원본·결과물은 커밋하지 않는다. 이전에 추적된 영상별 파일은 ignore 추가로 추적 해제되지 않는다. 해당 파일의 처분은 승인된 정리 단계에서만 한다.

`git reset --hard`와 `git clean -fdx`는 데이터 복구 수단이 아니다. Git 제외 데이터는 Git 커밋만으로 복구할 수 없다.

로컬 음성 UI는 `scripts/Start-QwenTTS.cmd <job-id>`로 연다. launcher는 기존 환경을 선택하며 모델을 자동 다운로드하지 않는다. 새 job의 음성 상태는 기존 개인 목소리를 자동 복사하지 않으므로 해당 작업에서 등록한다.

GPU UI launcher는 앱이 종료될 때까지 GPU lease를 유지한다. 다른 GPU 작업을 시작하려면 해당 UI를 종료한다. CPU 작업과 서로 다른 job의 데이터 처리는 병행할 수 있다.
