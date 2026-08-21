from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4

from core_clients import CoreClientError, SharedDataClient
from youtube_domain import (
    REQUEST_FIELDS,
    VIDEO_FIELDS,
    YouTubeDomainError,
    YouTubeEvidenceError,
    YouTubeEvidenceService,
    validate_request,
)


class YouTubeEvidenceServiceTests(unittest.TestCase):
    def _root(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(prefix="stage09-youtube-domain-")

    def _fixture(self, raw_root: str) -> tuple[dict, dict]:
        root = Path(raw_root)
        (root / "core" / "docs").mkdir(parents=True)
        (root / "core" / "docs" / "evidence.md").write_text(
            """# 영상 근거

현재 근거만 선택한다.

<!-- project-data:v1 kind=knowledge key=test-youtube-evidence -->
```json
{
  "key": "test-youtube-evidence",
  "kind": "knowledge",
  "payload": {
    "statement": "영상 근거 패키지는 current 근거만 선택한다",
    "classification": "procedure",
    "scope": "youtube:evidence-pack",
    "verification_status": "verified",
    "verified_by": "agent:test",
    "replaces_legacy_ids": ["123e4567-e89b-42d3-a456-426614174000"]
  },
  "source_refs": ["core/docs/evidence.md"],
  "status": "current"
}
```
<!-- /project-data -->
""",
            encoding="utf-8",
        )
        shared = SharedDataClient(root)
        shared.invoke("initialize", {}, write=True)
        source = shared.invoke(
            "source.create",
            {
                "source_kind": "local_document",
                "locator": "core/docs/evidence.md",
                "evidence_role": "primary",
                "record_id": str(uuid4()),
            },
            write=True,
        )
        claim = shared.invoke(
            "knowledge.create",
            {
                "statement": "영상 근거 패키지는 current 근거만 선택한다",
                "classification": "procedure",
                "scope": "youtube:evidence-pack",
                "source_ids": [source["id"]],
                "verification_status": "verified",
                "verified_by": "agent:test",
                "record_id": str(uuid4()),
            },
            write=True,
        )
        shared.invoke(
            "lifecycle.register_existing",
            {"actor": "agent:test", "approval_kind": "standing_policy"},
            write=True,
        )
        return source, claim

    def _request(self, claim_id: str) -> dict:
        return {
            "video": {
                "id": "test-video",
                "working_title": "현재 근거로 영상 준비하기",
                "audience": "반복 제작자",
                "goal": "선택한 근거를 촬영 전 검토한다.",
            },
            "documents": [{"ref": "core/docs/evidence.md", "reason": "도메인 근거"}],
            "records": [{"id": claim_id, "reason": "current 절차"}],
            "search": None,
            "char_limit": 12000,
            "baseline_characters": 1000,
        }

    def _document_request(self) -> dict:
        request = self._request(str(uuid4()))
        request["documents"] = [
            {
                "ref": "core/docs/evidence.md",
                "data_key": "test-youtube-evidence",
                "reason": "문서 정본 근거",
            }
        ]
        request["records"] = []
        return request

    def test_builds_from_document_data_key_without_record_storage(self) -> None:
        with self._root() as raw_root:
            self._fixture(raw_root)
            pack = YouTubeEvidenceService(raw_root).build_pack(self._document_request())
            selected = pack["context_package"]["selected"]
            self.assertEqual(len(selected), 1)
            self.assertEqual(selected[0]["data_key"], "test-youtube-evidence")
            self.assertEqual(selected[0]["kind"], "document_data")

    def test_builds_deterministic_nonpersistent_pack_with_user_gate(self) -> None:
        with self._root() as raw_root:
            source, claim = self._fixture(raw_root)
            service = YouTubeEvidenceService(raw_root)
            before = sorted(path.relative_to(raw_root).as_posix() for path in Path(raw_root).rglob("*"))
            first = service.build_pack(self._request(claim["id"]))
            second = service.build_pack(self._request(claim["id"]))
            after = sorted(path.relative_to(raw_root).as_posix() for path in Path(raw_root).rglob("*"))
            self.assertEqual(first, second)
            self.assertEqual(before, after)
            self.assertEqual(first["approval_gate"]["status"], "review_required")
            self.assertEqual(first["approval_gate"]["owner"], "user")
            self.assertTrue(first["fingerprint"].startswith("sha256:"))
            records = [
                item for item in first["context_package"]["selected"] if item["kind"] == "record"
            ]
            self.assertEqual([item["record_id"] for item in records], [claim["id"]])
            self.assertEqual(records[0]["data"]["payload"]["source_ids"], [source["id"]])
            self.assertEqual(first["selection_metrics"]["baseline_characters"], 1000)

    def test_noncurrent_requested_record_fails_instead_of_partial_success(self) -> None:
        with self._root() as raw_root:
            source, old = self._fixture(raw_root)
            shared = SharedDataClient(raw_root)
            replacement = shared.invoke(
                "knowledge.create",
                {
                    "statement": "개정된 current 영상 근거 절차",
                    "classification": "procedure",
                    "scope": "youtube:evidence-pack",
                    "source_ids": [source["id"]],
                    "verification_status": "verified",
                    "verified_by": "agent:test",
                    "record_id": str(uuid4()),
                },
                write=True,
            )
            shared.invoke(
                "lifecycle.register",
                {
                    "target_id": replacement["id"],
                    "initial_state": "current",
                    "actor": "agent:test",
                    "approval_kind": "standing_policy",
                    "reason": "개정 절차",
                },
                write=True,
            )
            state = shared.invoke("lifecycle.get", {"target_id": old["id"]})["lifecycle"]
            shared.invoke(
                "lifecycle.transition",
                {
                    "target_id": old["id"],
                    "expected_state_hash": state["content_hash"],
                    "action": "supersede",
                    "actor": "agent:test",
                    "approval_kind": "standing_policy",
                    "reason": "개정",
                    "replacement_id": replacement["id"],
                },
                write=True,
            )
            with self.assertRaises(YouTubeEvidenceError):
                YouTubeEvidenceService(raw_root).build_pack(self._request(old["id"]))

    def test_protected_document_is_rejected_by_common_context_boundary(self) -> None:
        with self._root() as raw_root:
            _, claim = self._fixture(raw_root)
            request = self._request(claim["id"])
            request["documents"] = [{"ref": "sealed-material/private.md", "reason": "금지 원본"}]
            with self.assertRaises(CoreClientError):
                YouTubeEvidenceService(
                    raw_root, protected_paths=("sealed-material",)
                ).build_pack(request)

    def test_current_record_selection_needs_no_legacy_mode(self) -> None:
        normalized = validate_request(self._request(str(uuid4())))
        self.assertEqual(len(normalized["records"]), 1)

    def test_request_rejects_unknown_fields_duplicates_empty_evidence_and_large_limit(self) -> None:
        request = self._request(str(uuid4()))
        request["unknown"] = True
        with self.assertRaises(YouTubeDomainError):
            validate_request(request)
        request = self._request(str(uuid4()))
        request["documents"] *= 2
        with self.assertRaises(YouTubeDomainError):
            validate_request(request)
        request = self._request(str(uuid4()))
        request.update({"documents": [], "records": [], "search": None})
        with self.assertRaises(YouTubeDomainError):
            validate_request(request)
        request = self._request(str(uuid4()))
        request["char_limit"] = 12001
        with self.assertRaises(YouTubeDomainError):
            validate_request(request)

    def test_runtime_and_json_schema_top_level_fields_match(self) -> None:
        root = Path(__file__).resolve().parents[2]
        request_schema = json.loads(
            (
                root
                / "extension"
                / "schemas"
                / "youtube-evidence-request-v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        pack_schema = json.loads(
            (
                root
                / "extension"
                / "schemas"
                / "youtube-evidence-pack-v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(set(request_schema["required"]), set(REQUEST_FIELDS))
        self.assertEqual(set(request_schema["properties"]["video"]["required"]), set(VIDEO_FIELDS))
        self.assertEqual(
            set(request_schema["properties"]["documents"]["items"]["required"]), {"ref", "reason"}
        )
        self.assertEqual(
            set(request_schema["properties"]["records"]["items"]["required"]), {"id", "reason"}
        )
        self.assertEqual(
            set(pack_schema["required"]),
            {"pack_version", "domain", "task", "video", "approval_gate", "context_package", "selection_metrics", "fingerprint"},
        )
        self.assertEqual(set(pack_schema["properties"]["video"]["required"]), set(VIDEO_FIELDS))

    def test_cli_accepts_utf8_stdin_and_returns_structured_error(self) -> None:
        with self._root() as raw_root:
            _, claim = self._fixture(raw_root)
            root = Path(__file__).resolve().parents[2]
            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.pathsep.join(
                [
                    str(root / "core" / "src"),
                    str(root / "core"),
                    str(root / "extension" / "src"),
                ]
            )
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONUTF8"] = "1"
            command = [
                sys.executable, "-m", "youtube_domain", "--root", raw_root,
                "evidence-pack", "--request-stdin",
            ]
            success = subprocess.run(
                command,
                input=json.dumps(self._request(claim["id"]), ensure_ascii=False),
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertEqual(json.loads(success.stdout)["result"]["pack"]["domain"], "youtube")
            invalid = self._request(claim["id"])
            invalid["video"]["id"] = "잘못된 ID"
            failure = subprocess.run(
                command,
                input=json.dumps(invalid, ensure_ascii=False),
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(failure.returncode, 2)
            self.assertEqual(json.loads(failure.stderr)["error"]["kind"], "input_error")


if __name__ == "__main__":
    unittest.main()
