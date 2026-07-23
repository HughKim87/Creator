from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from file_data import ExpectationMismatchError
from file_data.knowledge import KnowledgeService
from file_data.lifecycle import InvalidLifecycleTransition, LifecycleError, LifecycleService
from test_support import TEST_WRITE_CAPABILITY


FAILURE_TEXT = """# 검증 실패 사례

- 상태: 해결·회귀 검증 완료
- 적용 범위: 테스트

## 증상

검증이 중단됐다.

## 확인된 원인

- 원인 A

## 실패·해결 이력

| 시점 | 시도 | 최고 연속 횟수 | 해결 |
|---|---|---:|---|
| 테스트 | 실패 | 1 | 수정 후 성공 |

## 해결과 검증

- 원인을 수정했다.
- 전체 검증이 성공했다.

## 재사용 규칙

- 같은 원인을 먼저 확인한다.

## 근거

- 안전한 테스트 fixture
"""


class LifecycleTests(unittest.TestCase):
    def _root(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(prefix="stage06-lifecycle-")

    def _services(self, raw_root: str) -> tuple[KnowledgeService, LifecycleService]:
        knowledge = KnowledgeService(
            raw_root,
            _write_capability=TEST_WRITE_CAPABILITY,
        )
        knowledge.initialize()
        return (
            knowledge,
            LifecycleService(
                raw_root,
                _write_capability=TEST_WRITE_CAPABILITY,
            ),
        )

    def _statement_source(self, knowledge: KnowledgeService, *, status: str = "verified") -> dict:
        return knowledge.create_source(
            source_kind="user_statement",
            locator="user://stage06/approval",
            evidence_role="primary",
            verification_status=status,
            record_id=str(uuid4()),
        )

    def test_current_registration_requires_user_or_standing_policy(self) -> None:
        with self._root() as raw_root:
            knowledge, lifecycle = self._services(raw_root)
            source = self._statement_source(knowledge)
            with self.assertRaises(InvalidLifecycleTransition):
                lifecycle.register(
                    source["id"],
                    initial_state="current",
                    actor="agent:test",
                    approval_kind="agent_in_scope",
                    reason="승인 없는 현재 채택 시도",
                )
            state = lifecycle.register(
                source["id"],
                initial_state="current",
                actor="agent:test",
                approval_kind="standing_policy",
                reason="테스트 상시 정책",
            )
            self.assertEqual(state["payload"]["state"], "current")

    def test_review_and_approval_preserve_append_only_history(self) -> None:
        with self._root() as raw_root:
            knowledge, lifecycle = self._services(raw_root)
            source = self._statement_source(knowledge, status="observed")
            candidate = lifecycle.register(
                source["id"],
                initial_state="candidate",
                actor="agent:test",
                approval_kind="agent_in_scope",
                reason="미검증 후보 등록",
            )
            review = lifecycle.transition(
                source["id"],
                expected_state_hash=candidate["content_hash"],
                action="request_review",
                actor="agent:test",
                approval_kind="agent_in_scope",
                reason="출처 확인 필요",
            )
            with self.assertRaises(InvalidLifecycleTransition):
                lifecycle.transition(
                    source["id"],
                    expected_state_hash=review["content_hash"],
                    action="approve_current",
                    actor="agent:test",
                    approval_kind="agent_in_scope",
                    reason="무권한 승인",
                )
            current = lifecycle.transition(
                source["id"],
                expected_state_hash=review["content_hash"],
                action="approve_current",
                actor="user:test",
                approval_kind="user",
                reason="사용자 검토 완료",
            )
            self.assertEqual(current["payload"]["revision"], 3)
            self.assertEqual([item["payload"]["action"] for item in lifecycle.history(source["id"])], [
                "register", "request_review", "approve_current"
            ])
            self.assertEqual(lifecycle.rebuild_snapshot(source["id"]), current)

    def test_expected_hash_and_terminal_state_are_enforced(self) -> None:
        with self._root() as raw_root:
            knowledge, lifecycle = self._services(raw_root)
            source = self._statement_source(knowledge)
            state = lifecycle.register(
                source["id"], initial_state="current", actor="agent:test",
                approval_kind="standing_policy", reason="현재 등록"
            )
            with self.assertRaises(ExpectationMismatchError):
                lifecycle.transition(
                    source["id"], expected_state_hash="sha256:" + "0" * 64,
                    action="retire", actor="user:test", approval_kind="user", reason="오래됨"
                )
            retired = lifecycle.transition(
                source["id"], expected_state_hash=state["content_hash"],
                action="retire", actor="user:test", approval_kind="user", reason="사용 종료"
            )
            with self.assertRaises(InvalidLifecycleTransition):
                lifecycle.transition(
                    source["id"], expected_state_hash=retired["content_hash"],
                    action="request_review", actor="agent:test", approval_kind="agent_in_scope",
                    reason="terminal 복귀 시도"
                )

    def test_event_time_cannot_regress_and_replacement_cannot_be_self(self) -> None:
        with self._root() as raw_root:
            knowledge, lifecycle = self._services(raw_root)
            source = self._statement_source(knowledge)
            now = datetime.now(UTC).replace(microsecond=0)
            state = lifecycle.register(
                source["id"], initial_state="current", actor="agent:test",
                approval_kind="standing_policy", reason="현재 등록", timestamp=now
            )
            with self.assertRaises(InvalidLifecycleTransition):
                lifecycle.transition(
                    source["id"], expected_state_hash=state["content_hash"], action="request_review",
                    actor="agent:test", approval_kind="agent_in_scope", reason="과거 event",
                    timestamp=now - timedelta(seconds=1)
                )
            with self.assertRaises(InvalidLifecycleTransition):
                lifecycle.transition(
                    source["id"], expected_state_hash=state["content_hash"], action="supersede",
                    actor="user:test", approval_kind="user", reason="자기 자신 대체",
                    replacement_id=source["id"], timestamp=now
                )
            self.assertEqual(lifecycle.get_state(source["id"]), state)

    def test_lifecycle_event_can_reference_an_approved_decision(self) -> None:
        with self._root() as raw_root:
            knowledge, lifecycle = self._services(raw_root)
            source = self._statement_source(knowledge)
            decision = knowledge.create_decision(
                {
                    "problem": "현재 지식 재검토 여부",
                    "requirements": ["원본 보존"],
                    "options": [
                        {"label": "review", "impact": "검토 필요로 전환"},
                        {"label": "keep", "impact": "현재 유지"},
                    ],
                    "selected_option": "review",
                    "rationale": "출처가 변경됨",
                    "impacts": ["검토 전 기본 결과 제외"],
                    "source_ids": [source["id"]],
                    "requires_user_approval": True,
                    "approval_kind": "standing_policy",
                    "approved_by": "user:standing-policy",
                    "decided_at": datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
                record_id=str(uuid4()),
            )
            lifecycle.register_existing(actor="agent:test", approval_kind="standing_policy")
            state = lifecycle.get_state(source["id"])
            updated = lifecycle.transition(
                source["id"], expected_state_hash=state["content_hash"], action="request_review",
                actor="agent:test", approval_kind="agent_in_scope", reason="승인된 결정 적용",
                decision_id=decision["id"]
            )
            self.assertEqual(updated["payload"]["last_decision_id"], decision["id"])

    def test_supersede_keeps_old_record_and_selects_replacement(self) -> None:
        with self._root() as raw_root:
            knowledge, lifecycle = self._services(raw_root)
            old = self._statement_source(knowledge)
            replacement = knowledge.create_source(
                source_kind="user_statement", locator="user://stage06/revised",
                evidence_role="primary", verification_status="verified", record_id=str(uuid4())
            )
            old_state = lifecycle.register(
                old["id"], initial_state="current", actor="agent:test",
                approval_kind="standing_policy", reason="기존 현재 기록"
            )
            lifecycle.register(
                replacement["id"], initial_state="current", actor="agent:test",
                approval_kind="standing_policy", reason="검증된 개정 기록"
            )
            superseded = lifecycle.transition(
                old["id"], expected_state_hash=old_state["content_hash"], action="supersede",
                actor="user:test", approval_kind="user", reason="새 출처로 대체",
                replacement_id=replacement["id"]
            )
            self.assertEqual(superseded["payload"]["superseded_by"], replacement["id"])
            self.assertEqual(lifecycle.store.get_record(old["id"]), old)
            self.assertEqual([item["id"] for item in lifecycle.current_records(target_type="source")], [
                replacement["id"]
            ])

    def test_conflict_marks_both_records_for_review_without_merging(self) -> None:
        with self._root() as raw_root:
            knowledge, lifecycle = self._services(raw_root)
            source = self._statement_source(knowledge)
            first = knowledge.create_knowledge(
                statement="규칙 A가 현재다", classification="fact", scope="test",
                source_ids=[source["id"]], verification_status="verified",
                verified_by="user:test", record_id=str(uuid4())
            )
            second = knowledge.create_knowledge(
                statement="규칙 B가 현재다", classification="fact", scope="test",
                source_ids=[source["id"]], verification_status="verified",
                verified_by="user:test", record_id=str(uuid4())
            )
            lifecycle.register_existing(actor="agent:test", approval_kind="standing_policy")
            first_state = lifecycle.get_state(first["id"])
            lifecycle.transition(
                first["id"], expected_state_hash=first_state["content_hash"],
                action="declare_conflict", actor="agent:test", approval_kind="agent_in_scope",
                reason="서로 양립할 수 없는 현재 주장", related_target_ids=[second["id"]]
            )
            for target, other in ((first, second), (second, first)):
                state = lifecycle.get_state(target["id"])
                self.assertEqual(state["payload"]["state"], "review_required")
                self.assertIn(other["id"], state["payload"]["conflict_ids"])
                self.assertEqual(lifecycle.store.get_record(target["id"]), target)
            first_review = lifecycle.get_state(first["id"])
            lifecycle.transition(
                first["id"], expected_state_hash=first_review["content_hash"],
                action="approve_current", actor="user:test", approval_kind="user",
                reason="사용자가 첫 주장을 현재로 채택"
            )
            second_review = lifecycle.get_state(second["id"])
            lifecycle.transition(
                second["id"], expected_state_hash=second_review["content_hash"],
                action="reject", actor="user:test", approval_kind="user",
                reason="상충하는 둘째 주장은 채택하지 않음"
            )
            self.assertEqual(
                [item["id"] for item in lifecycle.current_records(target_type="knowledge")], [first["id"]]
            )

    def test_actual_source_drift_triggers_source_and_dependent_review(self) -> None:
        with self._root() as raw_root:
            root = Path(raw_root)
            (root / "docs").mkdir()
            target = root / "docs" / "source.md"
            target.write_text("version one\n", encoding="utf-8")
            knowledge, lifecycle = self._services(raw_root)
            source = knowledge.create_source(
                source_kind="local_document", locator="docs/source.md", evidence_role="primary",
                record_id=str(uuid4())
            )
            claim = knowledge.create_knowledge(
                statement="출처는 version one이다", classification="fact", scope="test",
                source_ids=[source["id"]], verification_status="verified",
                verified_by="agent:test", record_id=str(uuid4())
            )
            lifecycle.register_existing(actor="agent:test", approval_kind="standing_policy")
            target.write_text("version two\n", encoding="utf-8")
            findings = lifecycle.audit(actor="agent:audit")
            self.assertEqual({item["target_id"] for item in findings}, {source["id"], claim["id"]})
            self.assertEqual(lifecycle.get_state(source["id"])["payload"]["state"], "review_required")
            self.assertEqual(lifecycle.get_state(claim["id"])["payload"]["state"], "review_required")
            history_lengths = {
                source["id"]: len(lifecycle.history(source["id"])),
                claim["id"]: len(lifecycle.history(claim["id"])),
            }
            lifecycle.audit(actor="agent:audit")
            self.assertEqual(len(lifecycle.history(source["id"])), history_lengths[source["id"]])
            self.assertEqual(len(lifecycle.history(claim["id"])), history_lengths[claim["id"]])

    def test_legacy_failure_refresh_validates_canonical_document_without_fanout(self) -> None:
        with self._root() as raw_root:
            root = Path(raw_root)
            (root / "failures").mkdir()
            failure_doc = root / "failures" / "case.md"
            failure_doc.write_text(FAILURE_TEXT, encoding="utf-8")
            knowledge, lifecycle = self._services(raw_root)
            imported = knowledge._import_legacy_failure_knowledge(
                "failures/case.md", projected_by="agent:test", record_id=str(uuid4()), source_id=str(uuid4())
            )
            old_failure = imported["failure_knowledge"]
            old_source = imported["source"]
            lifecycle.register_existing(actor="agent:test", approval_kind="standing_policy")
            before_records = {
                path.name for path in (root / "data" / "records").glob("*.json")
            }
            before_events = (root / "data" / "events" / "lifecycle_events.jsonl").read_bytes()
            before_failure_state = lifecycle.get_state(old_failure["id"])
            before_source_state = lifecycle.get_state(old_source["id"])
            failure_doc.write_text(FAILURE_TEXT.replace("원인 A", "원인 A의 확정된 개정"), encoding="utf-8")
            validated = lifecycle.refresh_failure_projection(
                old_failure["id"], actor="agent:test", approval_kind="standing_policy",
                reason="정본 실패 문서 개정 반영"
            )
            self.assertEqual(
                validated["failure_document"]["confirmed_cause"],
                "- 원인 A의 확정된 개정",
            )
            self.assertFalse(validated["stored"])
            self.assertEqual(
                {path.name for path in (root / "data" / "records").glob("*.json")},
                before_records,
            )
            self.assertEqual(
                (root / "data" / "events" / "lifecycle_events.jsonl").read_bytes(),
                before_events,
            )
            self.assertEqual(lifecycle.get_state(old_failure["id"]), before_failure_state)
            self.assertEqual(lifecycle.get_state(old_source["id"]), before_source_state)

    def test_register_existing_preserves_stage05_candidate_status(self) -> None:
        with self._root() as raw_root:
            knowledge, lifecycle = self._services(raw_root)
            observed = self._statement_source(knowledge, status="observed")
            verified = knowledge.create_source(
                source_kind="user_statement", locator="user://stage06/verified",
                evidence_role="supporting", verification_status="verified", record_id=str(uuid4())
            )
            states = lifecycle.register_existing(actor="agent:test", approval_kind="standing_policy")
            self.assertEqual(len(states), 2)
            self.assertEqual(lifecycle.get_state(observed["id"])["payload"]["state"], "candidate")
            self.assertEqual(lifecycle.get_state(verified["id"])["payload"]["state"], "current")
            self.assertEqual(lifecycle.register_existing(actor="agent:test", approval_kind="standing_policy"), [])

    def test_conflict_requires_same_record_type_and_registered_target(self) -> None:
        with self._root() as raw_root:
            knowledge, lifecycle = self._services(raw_root)
            source = self._statement_source(knowledge)
            knowledge_record = knowledge.create_knowledge(
                statement="테스트 주장", classification="fact", scope="test",
                source_ids=[source["id"]], verification_status="verified",
                verified_by="agent:test", record_id=str(uuid4())
            )
            lifecycle.register_existing(actor="agent:test", approval_kind="standing_policy")
            state = lifecycle.get_state(knowledge_record["id"])
            with self.assertRaises(LifecycleError):
                lifecycle.transition(
                    knowledge_record["id"], expected_state_hash=state["content_hash"],
                    action="declare_conflict", actor="agent:test", approval_kind="agent_in_scope",
                    reason="잘못된 유형 연결", related_target_ids=[source["id"]]
                )
            self.assertEqual(lifecycle.get_state(knowledge_record["id"]), state)

    def test_cli_register_show_and_list(self) -> None:
        with self._root() as raw_root:
            knowledge, _ = self._services(raw_root)
            source = self._statement_source(knowledge)
            env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src"), "PYTHONUTF8": "1"}
            command = [
                sys.executable,
                str(Path(__file__).parents[1] / "tests" / "test_cli_entry.py"),
                "--root",
                raw_root,
                "lifecycle-register", "--id", source["id"], "--state", "current",
                "--actor", "agent:test", "--approval-kind", "standing_policy", "--reason", "CLI 검증",
            ]
            created = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", env=env, check=False)
            self.assertEqual(created.returncode, 0, created.stderr)
            listed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).parents[1] / "tests" / "test_cli_entry.py"),
                    "--root",
                    raw_root,
                    "--legacy-read",
                    "lifecycle-list",
                    "--state",
                    "current",
                ],
                capture_output=True, text=True, encoding="utf-8", env=env, check=False,
            )
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(json.loads(listed.stdout)["result"]["count"], 1)

    def test_schema_fields_and_enums_match_runtime_contract(self) -> None:
        root = Path(__file__).parents[1]
        event_schema = json.loads(
            (root / "schemas" / "lifecycle-event-payload-v1.schema.json").read_text(encoding="utf-8")
        )
        state_schema = json.loads(
            (root / "schemas" / "lifecycle-state-payload-v1.schema.json").read_text(encoding="utf-8")
        )
        from file_data.lifecycle import (
            ACTIONS, APPROVAL_KINDS, EVENT_FIELDS, LIFECYCLE_STATES, STATE_FIELDS, TARGET_TYPES
        )
        self.assertEqual(set(event_schema["properties"]), set(EVENT_FIELDS))
        self.assertEqual(set(state_schema["properties"]), set(STATE_FIELDS))
        self.assertEqual(set(event_schema["properties"]["action"]["enum"]), set(ACTIONS))
        self.assertEqual(set(event_schema["properties"]["approval_kind"]["enum"]), set(APPROVAL_KINDS))
        self.assertEqual(set(event_schema["properties"]["target_type"]["enum"]), set(TARGET_TYPES))
        self.assertEqual(set(state_schema["properties"]["state"]["enum"]), set(LIFECYCLE_STATES))


if __name__ == "__main__":
    unittest.main()
