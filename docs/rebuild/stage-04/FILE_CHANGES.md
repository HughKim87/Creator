# Stage 04 변경 파일 (미커밋)

## 신규

| 파일 | 의도 |
|---|---|
| `src/video_workflow/adapters/media_probe.py` | 동결 `MediaProbe` 포트 + `FfprobeMediaProbe`(fail-closed) + `StaticMediaProbe` |
| `src/video_workflow/adapters/premiere_xml.py` | 레거시 make_premiere_xml 알고리즘 이식(FCP7 XML), uuid 주입 지원 |
| `src/video_workflow/adapters/sync_check.py` | synccheck 순수 계산 이식(numpy 제거) + ffmpeg PCM 추출 어댑터 |
| `src/video_workflow/services/source_registration.py` | 지문·프로브·재지문·등록 단일 논리 작업, 금지 경로 차단 |
| `src/video_workflow/services/artifact_service.py` | staging→ready 승격 프로토콜 + reconcile(자동 삭제 없음) |
| `src/video_workflow/adapters/__init__.py` | 패키지 |
| `tests/contract/adapters/test_premiere_xml_characterization.py` | 레거시 특성 테스트 1:1 동결 + byte-identical 결정성 |
| `tests/unit/adapters/test_sync_check_and_probe.py` | 순수 계산·프로브 fail-closed 테스트 |
| `tests/integration/state/test_vertical_slice.py` | 등록 부정 매트릭스, 승격 실패 주입, reconcile 탐지, 수직 스모크 3회, CLI |
| `tests/{contract,unit}/adapters/__init__.py` | 패키지 |

## 수정

| 파일 | 내용 |
|---|---|
| `docs/rebuild/stage-00/BACKUP_MANIFEST.json` | schema v3 재작성(git blob 콘텐츠 sha256, 사용자 승인) |
| `src/video_workflow/checks/baseline.py` | blob 기준 해시 검사(`git cat-file`), schema v3 |
| `src/video_workflow/storage/sqlite_store.py` | artifact lifecycle 메서드 추가(`artifact_row`/`list_artifact_rows`/`set_artifact_lifecycle`) |
| `src/video_workflow/cli.py` | `workflow artifact reconcile` 추가 |
| `tests/unit/checks/test_baseline.py` | schema v3 반영 |

`backup/` 변경 0. 의존성·uv.lock 변경 0. 사용자 데이터 접근 0.
