# Legacy Core 종료 후보 원본

- 목적: 새 Agent Core로 흡수된 이전 구현의 source lineage를 삭제 승인 전까지 보존한다.
- 읽는 시점: `legacy-core/` 전체의 정확한 삭제 여부를 결정하거나 과거 구현 근거를 추적할 때만 읽는다.
- 책임: 활성 기능·정책은 `core/`와 Maintainer가 소유하며 이 디렉터리는 새 변경을 받지 않는다.
- 상태: 동결된 종료 후보. 활성 route·import·Runtime 소유권 없음.
- 관련 권위: 루트 `PROJECT_RULES.md`, `core/rules/file-cleanup.md`, `SESSION_HANDOFF.md`.

## 7H 흡수·대체 판정

| 이전 영역 | 현재 소유자 | 판정 |
|---|---|---|
| `rules/` | `core/rules/`와 Core route·회귀 테스트 | 일반화 흡수 완료 |
| record·store·knowledge·lifecycle·context·work·execution | `core/experimental/shared_data/`와 공개 `shared_data` v1 CLI | 일반화 흡수 완료 |
| `document_data`의 직접 문서 선택 | `shared_data`의 Evidence Context | 흡수 완료 |
| `document_data`의 artifact 의미 일치 | `extension/src/artifact_conformance.py`와 Extension registry | 소비자 소유로 대체 완료 |
| export manifest | 공개 `core_check verify`와 `shared_data info` | 공개 경계로 대체 완료 |
| maintenance 검증 | `core_check gate`, `scripts/verify.py`, Extension artifact 검사 | 분리 대체 완료 |
| `.obsidian/app.json` 정본 | 루트 `README.md`와 Extension registry | 소유권 이전 완료 |
| 실패 사례 문서 | 현재 Core 규칙과 결함 주입·회귀 테스트 | 예방책 흡수 완료, 별도 사례 복사 안 함 |
| failure knowledge projection·schema | `core/rules/failure-records.md` | 저장 projection을 의도적으로 종료 |
| 이전 계약·schema·fixture·테스트 | 현재 구현·계약·테스트와 Git 이력 | 활성 소유권 없음, source lineage만 보존 |

## 종료 경계

- 활성 코드와 검증 스크립트는 `legacy-core/src`를 import path로 사용하지 않는다.
- 이 디렉터리의 CLI·테스트·문서는 활성 진입점이나 검증 정본으로 사용하지 않는다.
- 원본의 복구와 상세 비교는 저장소 Git 이력이 소유한다.
- 이 판정은 삭제 실행 승인이 아니다. `legacy-core/` 전체 삭제는 정확한 대상에 대한 사용자의 별도 승인 뒤에만 수행한다.
