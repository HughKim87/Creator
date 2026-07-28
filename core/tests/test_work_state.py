from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "src"))

from file_data import (  # noqa: E402
    EVENT_FIELDS,
    EVENT_OUTCOMES,
    ExpectationMismatchError,
    InputContractError,
    InvalidTransitionError,
    ProjectionPendingError,
    RecordValidationError,
    REQUEST_FIELDS,
    OPTIONAL_REQUEST_FIELDS,
    WorkStateService,
)
from test_support import TEST_WRITE_CAPABILITY  # noqa: E402


WORK_ID = "123e4567-e89b-42d3-a456-426614174020"


def request_payload() -> dict[str, object]:
    return {
        "desired_outcome": "중립 작업의 완료 상태를 검증한다",
        "authorized_actions": ["임시 프로젝트 안에서 기록 생성과 검증"],
        "excluded_scope": ["보호 데이터", "장기 지식 승격"],
        "input_refs": ["fixture://neutral"],
        "protection_boundaries": ["inputs", "outputs"],
        "required_decisions": [],
        "verification_levels": ["tool", "structure"],
    }


class WorkStateServiceTests(unittest.TestCase):
    def make_service(self, root: Path) -> WorkStateService:
        service = WorkStateService(
            str(root),
            _write_capability=TEST_WRITE_CAPABILITY,
        )
        service.initialize()
        return service

    def create(self, service: WorkStateService) -> dict[str, object]:
        return service.create_work(
            request_payload(),
            actor="user",
            next_action="작업 시작",
            work_id=WORK_ID,
            timestamp=datetime(2026, 7, 23, 3, 0, tzinfo=UTC),
        )

    def test_work_state_schema_matches_projected_payload(self) -> None:
        schema = json.loads((ROOT / "core" / "schemas" / "work-state-payload-v1.schema.json").read_text(encoding="utf-8"))
        expected = {
            "work_id", "request", "status", "completed_items", "blockers", "next_action",
            "related_record_ids", "evidence_refs", "last_event_id",
        }
        self.assertEqual(set(schema["required"]), expected)
        self.assertEqual(set(schema["properties"]), expected)

    def test_request_and_event_schemas_match_runtime_fields(self) -> None:
        request_schema = json.loads(
            (ROOT / "core" / "schemas" / "work-request-payload-v1.schema.json").read_text(encoding="utf-8")
        )
        event_schema = json.loads(
            (ROOT / "core" / "schemas" / "work-event-payload-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(request_schema["required"]), REQUEST_FIELDS)
        self.assertEqual(set(request_schema["properties"]), REQUEST_FIELDS | OPTIONAL_REQUEST_FIELDS)
        self.assertEqual(set(event_schema["required"]), EVENT_FIELDS)
        self.assertEqual(set(event_schema["properties"]), EVENT_FIELDS)
        self.assertEqual(set(event_schema["properties"]["outcome"]["enum"]), EVENT_OUTCOMES)

    def test_request_and_full_transition_sequence_replay(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage04-flow-") as raw_root:
            service = self.make_service(Path(raw_root))
            requested = self.create(service)
            self.assertEqual(requested["payload"]["status"], "requested")
            started = service.transition(
                WORK_ID,
                expected_state_hash=requested["content_hash"],
                actor="agent",
                action="start",
                outcome="success",
                to_status="in_progress",
                next_action="대표 흐름 검증",
                timestamp=datetime(2026, 7, 23, 3, 1, tzinfo=UTC),
            )
            failed = service.transition(
                WORK_ID,
                expected_state_hash=started["content_hash"],
                actor="agent",
                action="validate",
                outcome="failure",
                to_status="failed",
                completed_items=["입력 검증"],
                next_action="원인 보정 후 재개",
                evidence_refs=["failure://example"],
                timestamp=datetime(2026, 7, 23, 3, 2, tzinfo=UTC),
            )
            resumed = service.transition(
                WORK_ID,
                expected_state_hash=failed["content_hash"],
                actor="agent",
                action="resume",
                outcome="success",
                to_status="in_progress",
                next_action="전체 재검증",
                timestamp=datetime(2026, 7, 23, 3, 3, tzinfo=UTC),
            )
            completed = service.transition(
                WORK_ID,
                expected_state_hash=resumed["content_hash"],
                actor="agent",
                action="complete",
                outcome="success",
                to_status="completed",
                completed_items=["전체 재검증"],
                next_action=None,
                evidence_refs=["test://pass"],
                timestamp=datetime(2026, 7, 23, 3, 4, tzinfo=UTC),
            )
            self.assertEqual(completed["payload"]["status"], "completed")
            self.assertEqual(completed["payload"]["completed_items"], ["입력 검증", "전체 재검증"])
            self.assertEqual(completed["payload"]["evidence_refs"], ["failure://example", "test://pass"])
            self.assertIsNone(completed["payload"]["next_action"])
            rebuilt = service.rebuild_snapshot(WORK_ID)
            self.assertEqual(rebuilt["payload"], completed["payload"])

    def test_in_progress_checkpoint_updates_progress_without_closing_work(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage04-progress-") as raw_root:
            service = self.make_service(Path(raw_root))
            requested = self.create(service)
            started = service.transition(
                WORK_ID,
                expected_state_hash=requested["content_hash"],
                actor="agent",
                action="start",
                outcome="success",
                to_status="in_progress",
                next_action="첫 소단계",
                timestamp=datetime(2026, 7, 23, 3, 1, tzinfo=UTC),
            )
            checkpoint = service.transition(
                WORK_ID,
                expected_state_hash=started["content_hash"],
                actor="agent",
                action="substage checkpoint",
                outcome="success",
                to_status="in_progress",
                completed_items=["첫 소단계"],
                next_action="다음 소단계",
                evidence_refs=["test://substage"],
                timestamp=datetime(2026, 7, 23, 3, 2, tzinfo=UTC),
            )
            self.assertEqual(checkpoint["payload"]["status"], "in_progress")
            self.assertEqual(checkpoint["payload"]["completed_items"], ["첫 소단계"])
            self.assertEqual(checkpoint["payload"]["next_action"], "다음 소단계")
            self.assertEqual(service.rebuild_snapshot(WORK_ID)["payload"], checkpoint["payload"])

    def test_blocked_state_requires_blocker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage04-blocked-") as raw_root:
            service = self.make_service(Path(raw_root))
            requested = self.create(service)
            with self.assertRaises(InvalidTransitionError):
                service.transition(
                    WORK_ID,
                    expected_state_hash=requested["content_hash"],
                    actor="agent",
                    action="block",
                    outcome="blocked",
                    to_status="blocked",
                    blockers=[],
                    next_action="사용자 입력 대기",
                )
            blocked = service.transition(
                WORK_ID,
                expected_state_hash=requested["content_hash"],
                actor="agent",
                action="block",
                outcome="blocked",
                to_status="blocked",
                blockers=["사용자 결정 필요"],
                next_action="사용자 입력 대기",
                timestamp=datetime(2026, 7, 23, 3, 1, tzinfo=UTC),
            )
            self.assertEqual(blocked["payload"]["status"], "blocked")
            self.assertEqual(blocked["payload"]["blockers"], ["사용자 결정 필요"])

    def test_expectation_and_invalid_transition_do_not_append(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage04-conflict-") as raw_root:
            service = self.make_service(Path(raw_root))
            requested = self.create(service)
            before, _ = service.store.list_events("work_events")
            with self.assertRaises(ExpectationMismatchError):
                service.transition(
                    WORK_ID,
                    expected_state_hash="sha256:" + "0" * 64,
                    actor="agent",
                    action="start",
                    outcome="success",
                    to_status="in_progress",
                    next_action="검증",
                )
            with self.assertRaises(InvalidTransitionError):
                service.transition(
                    WORK_ID,
                    expected_state_hash=requested["content_hash"],
                    actor="agent",
                    action="skip",
                    outcome="success",
                    to_status="completed",
                    next_action=None,
                )
            with self.assertRaisesRegex(InvalidTransitionError, "Outcome"):
                service.transition(
                    WORK_ID,
                    expected_state_hash=requested["content_hash"],
                    actor="agent",
                    action="mismatched outcome",
                    outcome="failure",
                    to_status="in_progress",
                    next_action="검증",
                    timestamp=datetime(2026, 7, 23, 3, 1, tzinfo=UTC),
                )
            with self.assertRaisesRegex(InputContractError, "evidence_refs"):
                service.transition(
                    WORK_ID,
                    expected_state_hash=requested["content_hash"],
                    actor="agent",
                    action="invalid evidence",
                    outcome="rejected",
                    to_status=None,
                    evidence_refs=[""],
                    timestamp=datetime(2026, 7, 23, 3, 1, tzinfo=UTC),
                )
            after, _ = service.store.list_events("work_events")
            self.assertEqual(after, before)

    def test_replay_rejects_malformed_work_event_payload(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage04-event-schema-") as raw_root:
            service = self.make_service(Path(raw_root))
            requested = self.create(service)
            events, stream_hash = service.store.list_events("work_events")
            malformed = dict(events[0]["payload"])
            malformed["request"] = None
            malformed["from_status"] = "requested"
            malformed["to_status"] = None
            malformed["outcome"] = "rejected"
            malformed["action"] = "malformed"
            malformed.pop("evidence_refs")
            service.store.append_event("work_events", malformed, expected_stream_hash=stream_hash)
            with self.assertRaises(RecordValidationError) as caught:
                service.rebuild_snapshot(WORK_ID)
            self.assertEqual(caught.exception.code, "work_event_payload")
            self.assertEqual(service.get_state(WORK_ID)["content_hash"], requested["content_hash"])

    def test_rejected_event_records_fact_without_mutating_snapshot_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage04-rejected-") as raw_root:
            service = self.make_service(Path(raw_root))
            requested = self.create(service)
            rejected = service.transition(
                WORK_ID,
                expected_state_hash=requested["content_hash"],
                actor="agent",
                action="deny out-of-scope action",
                outcome="rejected",
                to_status=None,
                completed_items=["변경하면 안 되는 완료 항목"],
                blockers=["변경하면 안 되는 차단 항목"],
                next_action="변경하면 안 되는 다음 행동",
                related_record_ids=["변경하면 안 되는 관련 ID"],
                evidence_refs=["변경하면 안 되는 근거"],
                timestamp=datetime(2026, 7, 23, 3, 1, tzinfo=UTC),
            )
            self.assertEqual(rejected["payload"]["status"], "requested")
            for field in (
                "completed_items", "blockers", "related_record_ids", "evidence_refs"
            ):
                self.assertEqual(rejected["payload"][field], requested["payload"][field])
            self.assertEqual(rejected["payload"]["next_action"], requested["payload"]["next_action"])
            events, _ = service.store.list_events("work_events")
            self.assertEqual(len(events), 2)
            self.assertEqual(events[-1]["payload"]["outcome"], "rejected")

    def test_projection_failure_preserves_event_and_rebuild_recovers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage04-rebuild-") as raw_root:
            service = self.make_service(Path(raw_root))
            with patch.object(service.store, "create_record", side_effect=OSError("snapshot failure")):
                with self.assertRaises(ProjectionPendingError):
                    self.create(service)
            events, _ = service.store.list_events("work_events")
            self.assertEqual(len(events), 1)
            recovered = service.rebuild_snapshot(WORK_ID)
            self.assertEqual(recovered["payload"]["status"], "requested")

    def test_request_is_immutable_after_first_event(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage04-request-") as raw_root:
            service = self.make_service(Path(raw_root))
            requested = self.create(service)
            events, stream_hash = service.store.list_events("work_events")
            bad = dict(events[0]["payload"])
            bad["from_status"] = "requested"
            bad["to_status"] = "in_progress"
            bad["action"] = "mutate-request"
            service.store.append_event("work_events", bad, expected_stream_hash=stream_hash)
            with self.assertRaises(RecordValidationError) as caught:
                service.rebuild_snapshot(WORK_ID)
            self.assertIn(caught.exception.code, {"work_request_mutation", "work_event_order"})
            self.assertEqual(service.get_state(WORK_ID)["content_hash"], requested["content_hash"])


class WorkStateCliTests(unittest.TestCase):
    def run_cli(
        self, root: Path, *arguments: str, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "core" / "src")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        prepared = list(arguments)
        if prepared and prepared[0] == "work-show":
            prepared.insert(0, "--legacy-read")
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "core" / "tests" / "test_cli_entry.py"),
                "--root",
                str(root),
                *prepared,
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            encoding="utf-8",
            input=input_text,
            capture_output=True,
            check=False,
        )

    def test_cli_create_show_and_transition(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage04-cli-") as raw_root:
            root = Path(raw_root)
            self.assertEqual(self.run_cli(root, "init").returncode, 0)
            created = self.run_cli(
                root,
                "work-create",
                "--id",
                WORK_ID,
                "--actor",
                "user",
                "--next-action",
                "작업 시작",
                "--request-stdin",
                input_text=json.dumps(request_payload(), ensure_ascii=False),
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            state = json.loads(created.stdout)["result"]["state"]
            shown = self.run_cli(root, "work-show", "--id", WORK_ID)
            self.assertEqual(json.loads(shown.stdout)["result"]["state"], state)
            transitioned = self.run_cli(
                root,
                "work-transition",
                "--id",
                WORK_ID,
                "--expected-hash",
                state["content_hash"],
                "--actor",
                "agent",
                "--action",
                "start",
                "--outcome",
                "success",
                "--to-status",
                "in_progress",
                "--next-action",
                "검증",
            )
            self.assertEqual(transitioned.returncode, 0, transitioned.stderr)
            self.assertEqual(json.loads(transitioned.stdout)["result"]["state"]["payload"]["status"], "in_progress")


if __name__ == "__main__":
    unittest.main()
