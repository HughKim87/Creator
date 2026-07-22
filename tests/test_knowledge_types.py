from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from file_data import (  # noqa: E402
    DECISION_APPROVAL_KINDS,
    DECISION_FIELDS,
    FAILURE_KNOWLEDGE_FIELDS,
    KNOWLEDGE_CLASSES,
    KNOWLEDGE_FIELDS,
    KNOWLEDGE_VERIFICATION_STATUSES,
    SOURCE_EVIDENCE_ROLES,
    SOURCE_FIELDS,
    SOURCE_KINDS,
    SOURCE_VERIFICATION_STATUSES,
    KnowledgeRecordError,
    KnowledgeService,
    SourceIntegrityError,
)


SOURCE_ID = "123e4567-e89b-42d3-a456-426614174050"
KNOWLEDGE_ID = "123e4567-e89b-42d3-a456-426614174052"
DECISION_ID = "123e4567-e89b-42d3-a456-426614174053"
FAILURE_ID = "123e4567-e89b-42d3-a456-426614174054"
FAILURE_SOURCE_ID = "123e4567-e89b-42d3-a456-426614174055"


def failure_document(*, status: str = "해결·회귀 검증 완료", include_prevention: bool = True) -> str:
    prevention = "\n## 재사용 규칙\n\n- 같은 원인을 먼저 검사한다.\n" if include_prevention else ""
    return (
        "# 중립 실패 사례\n\n"
        f"- 상태: {status}\n"
        "- 최초 확인: 중립 테스트\n"
        "- 마지막 검증: 2026-07-23\n"
        "- 적용 범위: 중립 fixture\n\n"
        "## 증상\n\n예상 결과와 실제 결과가 달랐다.\n\n"
        "## 확인된 원인\n\n입력 계약을 먼저 검사하지 않았다.\n\n"
        "## 실패·해결 이력\n\n| 시도 | 결과 |\n|---|---|\n| 첫 시도 | 실패 |\n\n"
        "## 해결과 검증\n\n- 입력 계약을 쓰기 전에 검사했다.\n- 전체 회귀 테스트가 통과했다.\n"
        f"{prevention}\n## 근거\n\n- fixture://neutral\n"
    )


class SourceRecordTests(unittest.TestCase):
    def make_service(self, root: Path) -> KnowledgeService:
        service = KnowledgeService(root)
        service.initialize()
        return service

    def test_source_schema_matches_runtime_contract(self) -> None:
        schema = json.loads((ROOT / "schemas" / "source-payload-v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), SOURCE_FIELDS)
        self.assertEqual(set(schema["properties"]), SOURCE_FIELDS)
        self.assertEqual(set(schema["properties"]["source_kind"]["enum"]), SOURCE_KINDS)
        self.assertEqual(
            set(schema["properties"]["verification_status"]["enum"]), SOURCE_VERIFICATION_STATUSES
        )
        self.assertEqual(set(schema["properties"]["evidence_role"]["enum"]), SOURCE_EVIDENCE_ROLES)

    def test_local_source_create_read_list_and_integrity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05a-local-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            (root / "docs" / "source.md").write_text("검증된 출처\n", encoding="utf-8")
            service = self.make_service(root)
            created = service.create_source(
                source_kind="local_document",
                locator="docs/source.md",
                evidence_role="primary",
                record_id=SOURCE_ID,
                timestamp=datetime(2026, 7, 23, 4, 0, tzinfo=UTC),
            )
            self.assertEqual(created["payload"]["verification_status"], "verified")
            self.assertRegex(created["payload"]["version_or_hash"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(service.get_source(SOURCE_ID), created)
            self.assertEqual(service.list_sources(), [created])
            self.assertEqual(service.verify_source(SOURCE_ID)["integrity"], "match")

    def test_local_source_change_and_protected_path_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05a-drift-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            source = root / "docs" / "source.md"
            source.write_text("첫 내용\n", encoding="utf-8")
            service = self.make_service(root)
            created = service.create_source(
                source_kind="local_document",
                locator="docs/source.md",
                evidence_role="supporting",
                record_id=SOURCE_ID,
            )
            source.write_text("바뀐 내용\n", encoding="utf-8")
            self.assertEqual(service.get_source(created["id"]), created)
            self.assertEqual(service.list_sources(), [created])
            with self.assertRaises(SourceIntegrityError):
                service.verify_source(created["id"])
            with self.assertRaises(Exception):
                service.create_source(
                    source_kind="local_document",
                    locator="inputs/secret.md",
                    evidence_role="primary",
                )

    def test_nonlocal_source_and_malformed_stored_payload(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05a-nonlocal-") as raw_root:
            service = self.make_service(Path(raw_root))
            statement = service.create_source(
                source_kind="user_statement",
                locator="request://stage05-standing-approval",
                evidence_role="primary",
                verification_status="observed",
                record_id=SOURCE_ID,
            )
            self.assertEqual(service.verify_source(statement["id"])["integrity"], "not_applicable")
            malformed = dict(statement["payload"])
            malformed["unexpected"] = True
            other = service.store.create_record(
                "source", malformed, record_id="123e4567-e89b-42d3-a456-426614174051"
            )
            with self.assertRaises(KnowledgeRecordError):
                service.get_source(other["id"])


class KnowledgeRecordTests(unittest.TestCase):
    def source(self, service: KnowledgeService, root: Path) -> dict[str, object]:
        (root / "docs").mkdir(exist_ok=True)
        (root / "docs" / "source.md").write_text("단일 소유자 계약\n", encoding="utf-8")
        return service.create_source(
            source_kind="local_document",
            locator="docs/source.md",
            evidence_role="primary",
            record_id=SOURCE_ID,
        )

    def test_knowledge_schema_matches_runtime_contract(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "knowledge-payload-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(schema["required"]), KNOWLEDGE_FIELDS)
        self.assertEqual(set(schema["properties"]), KNOWLEDGE_FIELDS)
        self.assertEqual(set(schema["properties"]["classification"]["enum"]), KNOWLEDGE_CLASSES)
        self.assertEqual(
            set(schema["properties"]["verification_status"]["enum"]),
            KNOWLEDGE_VERIFICATION_STATUSES,
        )

    def test_verified_knowledge_create_read_and_list(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05b-knowledge-") as raw_root:
            root = Path(raw_root)
            service = KnowledgeService(root)
            service.initialize()
            self.source(service, root)
            created = service.create_knowledge(
                statement="활성 정보마다 단일 소유자를 둔다.",
                classification="constraint",
                scope="프로젝트 정보·문서 책임",
                source_ids=[SOURCE_ID],
                verification_status="verified",
                verified_by="agent:test-gate",
                record_id=KNOWLEDGE_ID,
            )
            self.assertEqual(service.get_knowledge(KNOWLEDGE_ID), created)
            self.assertEqual(service.list_knowledge(), [created])

    def test_knowledge_rejects_multiclaim_shape_missing_source_and_bad_approval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05b-invalid-") as raw_root:
            root = Path(raw_root)
            service = KnowledgeService(root)
            service.initialize()
            self.source(service, root)
            cases = [
                {"statement": "첫 주장\n둘째 주장", "status": "candidate", "verifier": None, "sources": [SOURCE_ID]},
                {"statement": "출처 없음", "status": "candidate", "verifier": None, "sources": []},
                {"statement": "승인 없음", "status": "verified", "verifier": None, "sources": [SOURCE_ID]},
                {"statement": "후보 과승인", "status": "candidate", "verifier": "agent", "sources": [SOURCE_ID]},
            ]
            for case in cases:
                with self.subTest(case=case["statement"]):
                    with self.assertRaises(KnowledgeRecordError):
                        service.create_knowledge(
                            statement=case["statement"],
                            classification="fact",
                            scope="중립 범위",
                            source_ids=case["sources"],
                            verification_status=case["status"],
                            verified_by=case["verifier"],
                        )
            with self.assertRaises(Exception):
                service.create_knowledge(
                    statement="없는 출처 참조",
                    classification="fact",
                    scope="중립 범위",
                    source_ids=["123e4567-e89b-42d3-a456-426614174099"],
                    verification_status="candidate",
                )

    def test_source_drift_preserves_historical_knowledge_but_fails_explicit_verify(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05b-drift-") as raw_root:
            root = Path(raw_root)
            service = KnowledgeService(root)
            service.initialize()
            self.source(service, root)
            created = service.create_knowledge(
                statement="출처 무결성에 의존한다.",
                classification="fact",
                scope="중립 범위",
                source_ids=[SOURCE_ID],
                verification_status="candidate",
                record_id=KNOWLEDGE_ID,
            )
            (root / "docs" / "source.md").write_text("변경됨\n", encoding="utf-8")
            self.assertEqual(service.get_knowledge(created["id"]), created)
            with self.assertRaises(SourceIntegrityError):
                service.verify_source(SOURCE_ID)


class DecisionRecordTests(unittest.TestCase):
    def source(self, service: KnowledgeService) -> None:
        service.create_source(
            source_kind="user_statement",
            locator="request://recommended-choice",
            evidence_role="primary",
            verification_status="observed",
            record_id=SOURCE_ID,
        )

    def payload(self) -> dict[str, object]:
        return {
            "problem": "실패 문서와 구조화 데이터의 정본 관계",
            "requirements": ["기존 문서 보존", "복수 정본 방지"],
            "options": [
                {"label": "data_canonical", "impact": "Markdown을 파생 화면으로 전환"},
                {"label": "markdown_canonical", "impact": "구조화 데이터는 hash 고정 projection"},
            ],
            "selected_option": "markdown_canonical",
            "rationale": "사용자가 요구한 실패 문서를 보존하면서 기계 판독을 제공한다.",
            "impacts": ["문서 hash 불일치 시 projection 사용 거부"],
            "source_ids": [SOURCE_ID],
            "requires_user_approval": True,
            "approval_kind": "standing_policy",
            "approved_by": "user:recommended-auto-selection",
            "decided_at": "2020-01-01T00:00:00Z",
        }

    def test_decision_schema_matches_runtime_contract(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "decision-payload-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(schema["required"]), DECISION_FIELDS)
        self.assertEqual(set(schema["properties"]), DECISION_FIELDS)
        self.assertEqual(set(schema["properties"]["approval_kind"]["enum"]), DECISION_APPROVAL_KINDS)

    def test_decision_create_read_and_list(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05c-decision-") as raw_root:
            service = KnowledgeService(Path(raw_root))
            service.initialize()
            self.source(service)
            created = service.create_decision(self.payload(), record_id=DECISION_ID)
            self.assertEqual(service.get_decision(DECISION_ID), created)
            self.assertEqual(service.list_decisions(), [created])

    def test_decision_rejects_unreviewed_selection_duplicate_option_and_bad_approval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05c-invalid-") as raw_root:
            service = KnowledgeService(Path(raw_root))
            service.initialize()
            self.source(service)
            bad_selected = self.payload()
            bad_selected["selected_option"] = "not_reviewed"
            duplicate = self.payload()
            duplicate["options"] = [duplicate["options"][0], duplicate["options"][0]]
            bad_approval = self.payload()
            bad_approval["approval_kind"] = "agent_in_scope"
            future = self.payload()
            future["decided_at"] = "2099-01-01T00:00:00Z"
            for payload in (bad_selected, duplicate, bad_approval, future):
                with self.subTest(payload=payload):
                    with self.assertRaises(KnowledgeRecordError):
                        service.create_decision(payload)


class FailureKnowledgeTests(unittest.TestCase):
    def test_failure_schema_matches_runtime_contract(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "failure-knowledge-payload-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(schema["required"]), FAILURE_KNOWLEDGE_FIELDS)
        self.assertEqual(set(schema["properties"]), FAILURE_KNOWLEDGE_FIELDS)

    def test_failure_import_read_list_and_source_trace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05d-failure-") as raw_root:
            root = Path(raw_root)
            (root / "failures").mkdir()
            (root / "failures" / "neutral.md").write_text(failure_document(), encoding="utf-8")
            service = KnowledgeService(root)
            service.initialize()
            imported = service.import_failure_knowledge(
                "failures/neutral.md",
                projected_by="agent:test",
                record_id=FAILURE_ID,
                source_id=FAILURE_SOURCE_ID,
            )
            failure = imported["failure_knowledge"]
            self.assertEqual(failure["payload"]["source_id"], imported["source"]["id"])
            self.assertEqual(failure["payload"]["resolution"], ["입력 계약을 쓰기 전에 검사했다."])
            self.assertEqual(failure["payload"]["verification"], ["전체 회귀 테스트가 통과했다."])
            self.assertEqual(service.get_failure_knowledge(FAILURE_ID), failure)
            self.assertEqual(service.list_failure_knowledge(), [failure])

    def test_failure_projection_rejects_unresolved_missing_section_duplicate_and_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05d-invalid-") as raw_root:
            root = Path(raw_root)
            failures = root / "failures"
            failures.mkdir()
            service = KnowledgeService(root)
            service.initialize()
            (failures / "unresolved.md").write_text(
                failure_document(status="원인 조사 중"), encoding="utf-8"
            )
            with self.assertRaises(KnowledgeRecordError):
                service.import_failure_knowledge("failures/unresolved.md", projected_by="agent:test")
            (failures / "missing.md").write_text(
                failure_document(include_prevention=False), encoding="utf-8"
            )
            with self.assertRaises(KnowledgeRecordError):
                service.import_failure_knowledge("failures/missing.md", projected_by="agent:test")
            target = failures / "prevalidation.md"
            target.write_text(failure_document(), encoding="utf-8")
            before = list((root / "data" / "records").glob("*.json"))
            with self.assertRaises(KnowledgeRecordError):
                service.import_failure_knowledge(
                    "failures/prevalidation.md", projected_by="", record_id="not-a-uuid"
                )
            self.assertEqual(list((root / "data" / "records").glob("*.json")), before)
            target = failures / "neutral.md"
            target.write_text(failure_document(), encoding="utf-8")
            service.import_failure_knowledge(
                "failures/neutral.md", projected_by="agent:test", record_id=FAILURE_ID
            )
            with self.assertRaises(KnowledgeRecordError):
                service.import_failure_knowledge("failures/neutral.md", projected_by="agent:test")
            target.write_text(failure_document().replace("예상 결과", "변경된 결과"), encoding="utf-8")
            with self.assertRaises(SourceIntegrityError):
                service.get_failure_knowledge(FAILURE_ID)


class SourceCliTests(unittest.TestCase):
    def run_cli(
        self, root: Path, *arguments: str, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, "-m", "file_data", "--root", str(root), *arguments],
            cwd=ROOT,
            env=environment,
            text=True,
            encoding="utf-8",
            input=input_text,
            capture_output=True,
            check=False,
        )

    def test_source_cli_create_show_list_verify(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05a-cli-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            (root / "docs" / "source.md").write_text("CLI 출처\n", encoding="utf-8")
            self.assertEqual(self.run_cli(root, "init").returncode, 0)
            created = self.run_cli(
                root,
                "source-create",
                "--kind", "local_document",
                "--locator", "docs/source.md",
                "--role", "primary",
                "--id", SOURCE_ID,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            shown = self.run_cli(root, "source-show", "--id", SOURCE_ID)
            self.assertEqual(shown.returncode, 0, shown.stderr)
            self.assertEqual(json.loads(shown.stdout)["result"]["record"]["id"], SOURCE_ID)
            listed = self.run_cli(root, "source-list")
            self.assertEqual(json.loads(listed.stdout)["result"]["count"], 1)
            verified = self.run_cli(root, "source-verify", "--id", SOURCE_ID)
            self.assertEqual(json.loads(verified.stdout)["result"]["integrity"], "match")

    def test_knowledge_cli_create_show_and_list(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05b-cli-") as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            (root / "docs" / "source.md").write_text("CLI 지식 출처\n", encoding="utf-8")
            self.assertEqual(self.run_cli(root, "init").returncode, 0)
            source = self.run_cli(
                root, "source-create", "--kind", "local_document", "--locator", "docs/source.md",
                "--role", "primary", "--id", SOURCE_ID,
            )
            self.assertEqual(source.returncode, 0, source.stderr)
            created = self.run_cli(
                root, "knowledge-create", "--statement", "한 항목에는 한 주장을 둔다.",
                "--classification", "constraint", "--scope", "중립 지식", "--source-id", SOURCE_ID,
                "--verification-status", "verified", "--verified-by", "agent:test", "--id", KNOWLEDGE_ID,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            shown = self.run_cli(root, "knowledge-show", "--id", KNOWLEDGE_ID)
            self.assertEqual(json.loads(shown.stdout)["result"]["record"]["id"], KNOWLEDGE_ID)
            listed = self.run_cli(root, "knowledge-list")
            self.assertEqual(json.loads(listed.stdout)["result"]["count"], 1)

    def test_decision_cli_stdin_create_show_and_list(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05c-cli-") as raw_root:
            root = Path(raw_root)
            self.assertEqual(self.run_cli(root, "init").returncode, 0)
            source = self.run_cli(
                root, "source-create", "--kind", "user_statement",
                "--locator", "request://decision", "--role", "primary",
                "--verification-status", "observed", "--id", SOURCE_ID,
            )
            self.assertEqual(source.returncode, 0, source.stderr)
            payload = DecisionRecordTests().payload()
            created = self.run_cli(
                root, "decision-create", "--payload-stdin", "--id", DECISION_ID,
                input_text=json.dumps(payload, ensure_ascii=False),
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            shown = self.run_cli(root, "decision-show", "--id", DECISION_ID)
            self.assertEqual(json.loads(shown.stdout)["result"]["record"]["id"], DECISION_ID)
            listed = self.run_cli(root, "decision-list")
            self.assertEqual(json.loads(listed.stdout)["result"]["count"], 1)

    def test_failure_cli_import_show_and_list(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage05d-cli-") as raw_root:
            root = Path(raw_root)
            (root / "failures").mkdir()
            (root / "failures" / "neutral.md").write_text(failure_document(), encoding="utf-8")
            self.assertEqual(self.run_cli(root, "init").returncode, 0)
            imported = self.run_cli(
                root, "failure-import", "--doc", "failures/neutral.md",
                "--projected-by", "agent:test", "--id", FAILURE_ID, "--source-id", FAILURE_SOURCE_ID,
            )
            self.assertEqual(imported.returncode, 0, imported.stderr)
            shown = self.run_cli(root, "failure-show", "--id", FAILURE_ID)
            self.assertEqual(json.loads(shown.stdout)["result"]["record"]["id"], FAILURE_ID)
            listed = self.run_cli(root, "failure-list")
            self.assertEqual(json.loads(listed.stdout)["result"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
