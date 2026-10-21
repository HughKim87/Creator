# Creator 단일 작업 공간

- 목적: main 하나에서 영상별 데이터와 공용 실행 자원을 분리하고 기존 worktree를 안전하게 통합한다.
- 읽는 시점: 새 영상 생성·재개, 공용 도구 설치, 저장소 정리·복구 시.
- 책임: 공통 코드는 main 유지보수 세션, 영상 데이터는 명시된 job ID의 작업 세션, 기존 자료 처분은 사용자.
- 상태: 단일 workspace 코드 구현 완료. 기존 작업·설치 도구·캐시까지 main 밖으로 보관하는 실제 cleanup 완료.
- 관련 권위: 루트 PROJECT_RULES.md, core/PROJECT_RULES.md.

## 작업 계약과 단계

요청 결과는 브랜치별 재사용 개선을 main에 보존하고, 영상별 데이터가 섞이지 않는 작업 경로와 공용 도구 경로를 제공하며, main의 Git 상태를 깨끗하게 만드는 것이다. 기존 자료는 독립 archive에 보존하고 검증 뒤 기존 worktree를 퇴역시킨다. 외부 게시·push·Core 수정·자동 설치는 제외한다.

1. 복구 지점: `before`는 승인된 main 시작 커밋을 가리킨다. 다른 로컬 브랜치는 `before-<branch의 /를 -로 치환>` 태그로 고정한다. 태그와 원본 브랜치가 같은 커밋을 가리키는지 검사한다. Git 제외 데이터는 태그의 복구 범위가 아니므로 별도 archive와 파일별 복구 ledger로 보존한다.
2. 개선 통합: 각 브랜치의 공통 조상 이후 변경을 현재 main과 비교한다. 이미 반영된 내용은 중복 적용하지 않고, 고유 공통 구현은 원본 SHA와 경로를 연결해 반영한다. 영상 자료·실서비스 실험은 코드와 분리한다. 관련 검사·앱 빌드를 통과한 뒤 독립 커밋으로 남긴다.
3. 구조 구현: 아래 작업 경로·공용 runtime·프로세스 잠금·제작 진입점을 적용한다. 서로 다른 두 합성 job의 병행 실행, 같은 job 중복 실행 차단, GPU 잠금, 실패·취소·재개, 경로 이탈 방지와 기존 계약 회귀를 확인한다. 필요한 코드만 커밋한다.
4. 정리 준비: 기존 작업별 최종 결과물·종속 자산·복구 근거·삭제 후보를 분리해 정확한 경로와 용량을 사용자에게 제시한다. 이동·삭제·worktree 제거는 별도 승인 후 진행한다. 최종 XML이 외부 PNG/WAV/원본을 참조하면 그 의존 파일도 최종 패키지의 일부다.

실패 시 해당 단계에서 멈추고 직전 커밋의 변경을 되돌리는 커밋으로 복구한다. `git reset --hard`와 `git clean -fdx`는 데이터 복구 수단이 아니다. `before`를 별도 경로에 checkout하면 공통 코드를 조사할 수 있지만 ignored 데이터는 아래 archive 복구 절차로 별도로 복구해야 한다. 기존 worktree를 제거하기 전에는 미커밋·미추적·ignored 자료와 submodule의 독립 복구 수단을 확인한다. Git 복구 bundle과 검증 receipt는 외부 `D:/AI Agent/Creator-Archive/2026-10-21/recovery/`에 있다. 코드 복구는 이 bundle만으로 독립 검증했다. bundle에는 미디어를 포함하지 않는다.

## 경로와 실행

현재 main에는 기존 job·설치 runtime·data·Python cache가 없다. 아래 경로는 앞으로 생성할 작업의 구조다. 기존 작업이나 도구가 필요하면 먼저 아래 cleanup snapshot에서 해당 경로를 복원한다. runtime catalog 조회만으로 도구가 설치되지는 않는다.

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

`git status`가 깨끗한 상태와 디스크에서 ignored 자료를 제거한 상태는 별개다. `extension/jobs/`와 `.runtime/`는 Git 제외이고, 보호 원본·결과물은 커밋하지 않는다. 이전에 추적된 영상별 파일은 ignore 추가로 추적 해제되지 않는다. 해당 파일의 처분은 승인된 정리 단계에서만 한다.

로컬 음성 UI는 `scripts/Start-QwenTTS.cmd <job-id>`, Replier는 `scripts/Start-24HReplier.cmd <job-id>`로 연다. launcher는 기존 환경을 선택하며 모델을 자동 다운로드하지 않는다. 새 job의 음성 상태는 기존 개인 목소리를 자동 복사하지 않으므로 해당 작업에서 등록한다. 기존 개인 음성 저장소는 archive에서 복원할 수 있다.

GPU UI launcher는 앱이 종료될 때까지 GPU lease를 유지한다. 다른 GPU 작업을 시작하려면 해당 UI를 종료한다. CPU 작업과 서로 다른 job의 데이터 처리는 병행할 수 있다.

## 승인된 자료 이전 단계 (2026-10-21)

사용자가 보고서의 최종본·필수 자산·공용 도구 이전, 나머지 archive 보관, 원본·개인설정 복구 검증 뒤 기존 worktree 4개 제거와 main clean 마감을 승인했다. 영구적인 데이터 폐기는 제외한다.

- 원본 경계: main의 기존 data surfaces 및 wardogs·24HReplier·ainotebook·dokkaebi 네 등록 checkout. 원본 입력·개인설정은 값이나 비밀을 로그에 출력하지 않고 파일 단위로 보존한다.
- 4A: 전체 metadata inventory와 Git registration/Core bundle을 보존한다. D:의 checkout은 archive/worktrees/<이름>으로 파일 identity를 유지해 옮기고 C:의 wardogs는 copy+SHA-256 검증 후 원본을 마지막 gate까지 유지한다. 중첩 Core checkout과 별도 Git registration은 각각 archive와 bundle에서 복구되도록 보존하며 main/core는 변경하지 않는다.
- 4B: 승인된 최종 파일과 XML의 실제 참조 자산을 job으로 옮긴다. XML 원본은 archive에 유지하고 새 사본의 참조만 새 경로로 바꾼다. 실제 존재하지 않던 원본은 missing으로 명시하고 만들어내거나 대체하지 않는다. 공용 도구는 이전 후 import·실행 probe를 확인한다.
- 4C: 모든 원본 파일이 독립 archive의 ledger 위치에서 동일 bytes로 복원되는지 확인한다. 개인설정은 내용 비공개 copy/hash/restore probe로 검증한다. 검증한 cross-volume move의 원래 사본만 정리하고, Git registration을 해제해 main만 활성 worktree로 남긴다. before 태그·Git bundle·archive는 유지한다.
- 작업 경로: main의 extension/data/consolidation 및 D:/AI Agent/Creator-Archive/2026-10-21. 생성한 합성 restore probe는 정확한 소유 임시 경로만 종료 정리한다.
- gate: 원본 metadata drift 없음, copied bytes hash 동일, rename identity 동일, 전체 파일별 recovery ledger 완결, XML 참조 검증(기존 missing 구분), tool probes, 4개 source checkout 퇴역 및 main Git clean.


## 복구 절차

### 실제 cleanup 직전 상태

`D:/AI Agent/Creator-Archive/2026-10-21/main-cleanup-20261021-220805/`에 정리 직전 main의 모든 ignored·미추적 폴더를 보관했다. `tree/` 아래의 상대경로가 원래 main 상대경로이며 `receipt.json`과 `inventory-*.json`이 이동 전후 파일 identity·크기·수정 시각·속성 대조를 소유한다. 기존 job의 최종본·참조 자산·개인설정, 공용 도구와 모델, data의 이전 검증 자료도 이 snapshot에 포함된다. 동일 D: 볼륨 rename으로 파일 자체를 이동했고 중첩 저장소·링크도 그대로 보존한다.

복원은 필요한 `tree/<상대경로>`를 원래 main의 동일 상대경로로 옮기는 방식이다. 대상 경로가 없을 때만 수행하고 기존 파일에 덮어쓰지 않는다. 도구만 필요하면 `tree/extension/.runtime`, 특정 영상만 필요하면 `tree/extension/jobs/<job-id>`를 선택한다. XML의 main 절대경로와 Windows 환경은 원래 위치로 복원한 뒤 사용한다. archive 내부에서 실행하는 것은 보장하지 않는다. 이전 전 원본 복원은 다음 별도 절차를 사용한다.

### 통합 이전 원본

복구 소유자는 `D:/AI Agent/Creator-Archive/2026-10-21/`다. `original-inventory.json`은 이전 전 파일 목록, `recovery-ledger.jsonl`은 원래 경로·독립 보관 위치·SHA-256, `migration-state.json`은 최종 검증 receipt를 소유한다. main에 옮긴 자료도 archive/snapshots에 독립 복사한다. archive 내부에서만 같은 원본 inode의 파일을 hardlink로 공유하며 main과 archive가 같은 파일 inode를 공유하지 않는다. 따라서 main의 후속 편집은 복구본을 바꾸지 않는다.

이전 전 파일 트리를 새 빈 폴더로 복원하려면 다음 명령으로 계획을 확인한 뒤 `--materialize`를 붙인다. 복원 도구와 windows_reparse_snapshot.py 보조 코드는 archive/recovery에도 보존한다. 원래 위치나 기존 폴더에 덮어쓰지 않으며 원본별 SHA-256을 다시 대조한다. `--root`는 main, wardogs, replier, ainotebook, dokkaebi 중 하나다. main snapshot은 기존 데이터 경로만 포함하며 코드는 Git bundle이 소유한다.

```powershell
python -B "D:/AI Agent/Creator-Archive/2026-10-21/recovery/restore_workspace_snapshot.py" --archive "D:/AI Agent/Creator-Archive/2026-10-21" --root wardogs --destination "D:/AI Agent/Creator-Restore/wardogs"
```

복원 폴더의 `.git` pointer는 역사적 원본 바이트다. 이 파일만으로 활성 checkout이 되지 않는다. 원래 코드가 필요하면 archive/recovery/creator-before.bundle을 별도 빈 경로에 clone하고 `before` 또는 해당 `before-*` 태그를 새 복구 브랜치로 checkout한다. Core는 대응하는 core-main/wardogs/replier/ainotebook/dokkaebi.bundle을 core 경로에 clone한 뒤 부모 커밋의 `core` gitlink SHA로 checkout한다. 미디어와 개인설정은 위 snapshot을 별도 복원한 뒤 필요한 데이터 경로만 새 checkout에 복사한다. archive/git-metadata의 원래 registration·Core Git metadata도 보존하지만 현재 main의 `.git` 위에 덮어쓰지 않는다.

private 설정의 복구 검증은 파일 바이트·복원 해시를 의미한다. 암호화된 설정의 복호화, OAuth 로그인, 서비스 연결은 이번 정리 검증 범위가 아니다. 다른 Windows 사용자·PC에서는 OS 자격 증명이 추가로 필요할 수 있다. Zeus의 기존 누락 원본 `2026-10-05 01-56-11.mp4`는 사용자가 제외했으며 복구본이 있다고 주장하지 않는다.

archive는 이번 정리의 독립 로컬 복구본이며 별도 물리 디스크 백업은 아니다. `before` 태그·브랜치·bundle·archive를 유지하고, 더 이상 필요하지 않은 archive의 영구 삭제는 별도 사용자 판단으로 남긴다.


초기 Whisper cache에는 과거 Linux 세션으로 향하는 Windows LX reparse point가 하나 있었다. 실제 모델 파일은 main에 유지하고 이 사용 불가능한 포인터는 archive/special-entries에 원래 형태로 보존했다. 원시 reparse buffer는 archive/reparse-blobs에 따로 보존한다. 복원 도구는 대상을 따라가지 않고 Windows API로 링크 buffer와 원래 수정 시각을 복원·대조한다. 과거 클라우드 세션의 외부 경로를 다시 생성하거나 존재한다고 주장하지 않는다. 이 항목의 복원에는 Windows가 필요하다.
