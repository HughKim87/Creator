from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4

from file_data.context import ContextError, ContextLimitError, ContextService
from file_data.knowledge import KnowledgeService
from file_data.lifecycle import LifecycleService


class ContextServiceTests(unittest.TestCase):
    def _fixture(self, raw_root: str) -> tuple[ContextService, dict, dict]:
        root = Path(raw_root)
        (root / "docs").mkdir()
        (root / "docs" / "route.md").write_text("# 직접 라우팅\n\n필수 계약만 읽는다.\n", encoding="utf-8")
        knowledge = KnowledgeService(root)
        knowledge.initialize()
        source = knowledge.create_source(
            source_kind="local_document",
            locator="docs/route.md",
            evidence_role="primary",
            record_id=str(uuid4()),
        )
        claim = knowledge.create_knowledge(
            statement="직접 선택은 전체 읽기보다 먼저 수행한다",
            classification="procedure",
            scope="project-foundation",
            source_ids=[source["id"]],
            verification_status="verified",
            verified_by="agent:test",
            record_id=str(uuid4()),
        )
        LifecycleService(root).register_existing(actor="agent:test", approval_kind="standing_policy")
        return ContextService(root), source, claim

    def _root(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(prefix="stage07-context-")

    def test_direct_document_and_current_record_build_deterministic_package(self) -> None:
        with self._root() as raw_root:
            context, _, claim = self._fixture(raw_root)
            request = {
                "purpose": "직접 선택 평가",
                "documents": [
                    {"ref": "docs/route.md", "reason": "필수 계약"},
                    {"ref": "docs/route.md", "reason": "중복 직접 경로"},
                ],
                "records": [
                    {"id": claim["id"], "reason": "현재 절차"},
                    {"id": claim["id"], "reason": "중복 직접 ID"},
                ],
                "char_limit": 12000,
                "baseline_characters": 1000,
            }
            first = context.build_package(request)
            second = context.build_package(request)
            self.assertEqual(first, second)
            self.assertEqual(first["metrics"]["selected_items"], 2)
            self.assertEqual({item["kind"] for item in first["selected"]}, {"document", "record"})
            self.assertTrue(first["fingerprint"].startswith("sha256:"))

    def test_noncurrent_direct_record_is_excluded_with_reason(self) -> None:
        with self._root() as raw_root:
            context, source, old = self._fixture(raw_root)
            knowledge = KnowledgeService(raw_root)
            replacement = knowledge.create_knowledge(
                statement="직접 선택은 current 상태를 먼저 확인한다",
                classification="procedure", scope="project-foundation",
                source_ids=[source["id"]], verification_status="verified",
                verified_by="agent:test", record_id=str(uuid4())
            )
            lifecycle = LifecycleService(raw_root)
            lifecycle.register(
                replacement["id"], initial_state="current", actor="agent:test",
                approval_kind="standing_policy", reason="개정 절차"
            )
            old_state = lifecycle.get_state(old["id"])
            lifecycle.transition(
                old["id"], expected_state_hash=old_state["content_hash"], action="supersede",
                actor="agent:test", approval_kind="standing_policy", reason="개정",
                replacement_id=replacement["id"]
            )
            package = context.build_package({
                "purpose": "과거 record 제외",
                "records": [{"id": old["id"], "reason": "명시했지만 과거 상태"}],
            })
            self.assertEqual(package["selected"], [])
            self.assertEqual(package["excluded"]["counts_by_reason"], {"noncurrent:superseded": 1})

    def test_structured_filter_uses_type_state_scope_and_source_role(self) -> None:
        with self._root() as raw_root:
            context, _, claim = self._fixture(raw_root)
            matches = context.filter_records({
                "record_type": "knowledge", "state": "current",
                "scope": "project-foundation", "evidence_role": "primary",
            })
            self.assertEqual([item["id"] for item in matches], [claim["id"]])
            self.assertEqual(context.filter_records({"scope": "other"}), [])
            package = context.build_package({
                "purpose": "필터 단독 선택",
                "filters": {
                    "record_type": "knowledge", "scope": "project-foundation",
                    "evidence_role": "primary",
                },
            })
            self.assertEqual(
                [item["id"] for item in package["selected"] if item["kind"] == "record"], [claim["id"]]
            )
            with self.assertRaises(ContextError):
                context.build_package({"purpose": "과거 상태 package 금지", "filters": {"state": "superseded"}})

    def test_plain_search_returns_current_candidates_and_distinguishes_no_result(self) -> None:
        with self._root() as raw_root:
            context, _, claim = self._fixture(raw_root)
            matches = context.search("전체 읽기", {"record_type": "knowledge"})
            self.assertEqual([item["id"] for item in matches], [claim["id"]])
            self.assertEqual(matches[0]["matched_fields"], ["statement"])
            self.assertEqual(context.search("존재하지 않는 문자열"), [])

    def test_search_never_returns_superseded_match(self) -> None:
        with self._root() as raw_root:
            context, source, old = self._fixture(raw_root)
            knowledge = KnowledgeService(raw_root)
            replacement = knowledge.create_knowledge(
                statement="전체 읽기 대신 current 선택을 사용한다", classification="procedure",
                scope="project-foundation", source_ids=[source["id"]],
                verification_status="verified", verified_by="agent:test", record_id=str(uuid4())
            )
            lifecycle = LifecycleService(raw_root)
            lifecycle.register(
                replacement["id"], initial_state="current", actor="agent:test",
                approval_kind="standing_policy", reason="새 절차"
            )
            state = lifecycle.get_state(old["id"])
            lifecycle.transition(
                old["id"], expected_state_hash=state["content_hash"], action="supersede",
                actor="agent:test", approval_kind="standing_policy", reason="새 절차로 대체",
                replacement_id=replacement["id"]
            )
            self.assertEqual([item["id"] for item in context.search("전체 읽기")], [replacement["id"]])

    def test_protected_document_is_rejected_before_read(self) -> None:
        with self._root() as raw_root:
            context, _, _ = self._fixture(raw_root)
            with self.assertRaises(ContextError):
                context.build_package({
                    "purpose": "보호 경계",
                    "documents": [{"ref": "inputs/private.md", "reason": "금지 대상"}],
                })

    def test_required_context_over_limit_fails_without_truncation(self) -> None:
        with self._root() as raw_root:
            context, _, _ = self._fixture(raw_root)
            with self.assertRaises(ContextLimitError):
                context.build_package({
                    "purpose": "크기 제한",
                    "documents": [{"ref": "docs/route.md", "reason": "필수 계약"}],
                    "char_limit": 1,
                })

    def test_optional_search_candidate_is_excluded_at_size_limit(self) -> None:
        with self._root() as raw_root:
            context, _, _ = self._fixture(raw_root)
            document_chars = context.measure_documents(["docs/route.md"])["characters"]
            package = context.build_package({
                "purpose": "선택 후보 크기 제한",
                "documents": [{"ref": "docs/route.md", "reason": "필수 계약"}],
                "search": "전체 읽기",
                "char_limit": document_chars,
            })
            self.assertEqual(package["metrics"]["selected_items"], 1)
            self.assertEqual(package["excluded"]["counts_by_reason"], {"size_limit": 1})

    def test_baseline_counts_exact_unique_documents(self) -> None:
        with self._root() as raw_root:
            context, _, _ = self._fixture(raw_root)
            measured = context.measure_documents(["docs/route.md", "docs/route.md"])
            raw = (Path(raw_root) / "docs" / "route.md").read_bytes()
            content = raw.decode("utf-8", "strict")
            self.assertEqual(measured, {
                "documents": 1,
                "characters": len(content),
                "utf8_bytes": len(raw),
            })

    def test_cli_build_and_empty_search_are_successful(self) -> None:
        with self._root() as raw_root:
            _, _, claim = self._fixture(raw_root)
            env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src"), "PYTHONUTF8": "1"}
            request = json.dumps({
                "purpose": "CLI 직접 선택",
                "records": [{"id": claim["id"], "reason": "현재 절차"}],
            }, ensure_ascii=False)
            built = subprocess.run(
                [sys.executable, "-m", "file_data", "--root", raw_root, "context-build", "--request-stdin"],
                input=request, capture_output=True, text=True, encoding="utf-8", env=env, check=False,
            )
            self.assertEqual(built.returncode, 0, built.stderr)
            self.assertEqual(json.loads(built.stdout)["result"]["package"]["metrics"]["selected_items"], 1)
            empty = subprocess.run(
                [sys.executable, "-m", "file_data", "--root", raw_root, "context-search", "--text", "없음"],
                capture_output=True, text=True, encoding="utf-8", env=env, check=False,
            )
            self.assertEqual(empty.returncode, 0, empty.stderr)
            self.assertEqual(json.loads(empty.stdout)["result"]["count"], 0)

    def test_package_schema_has_runtime_top_level_fields(self) -> None:
        schema = json.loads(
            (Path(__file__).parents[1] / "schemas" / "context-package-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(set(schema["required"]), {
            "package_version", "purpose", "settings", "selected", "excluded", "metrics", "fingerprint"
        })


if __name__ == "__main__":
    unittest.main()
