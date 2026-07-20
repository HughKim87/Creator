"""Synchronization checks for the formal state schema and runtime validator."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
SCHEMA_PATH = ROOT / "docs/agent/state/schemas/video_task_state.schema.json"
sys.path.insert(0, str(TOOLS_DIR))

import state_io  # noqa: E402


class StateSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_schema_declares_current_draft_version_and_scope(self) -> None:
        self.assertEqual(
            self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        self.assertEqual(self.schema["$id"], "urn:kimsilver:video-task-state:v3")
        self.assertIn("Purpose:", self.schema["$comment"])
        self.assertIn("Scope:", self.schema["$comment"])
        self.assertEqual(
            self.schema["properties"]["schema_version"]["const"],
            state_io.SCHEMA_VERSION,
        )

    def test_required_fields_match_runtime_exact_key_sets(self) -> None:
        self.assertEqual(set(self.schema["required"]), set(state_io._STATE_KEYS))
        self.assertEqual(
            set(self.schema["properties"]["reference_input"]["required"]),
            set(state_io._REFERENCE_KEYS),
        )
        self.assertEqual(
            set(self.schema["$defs"]["integrity"]["required"]),
            set(state_io._FINGERPRINT_KEYS),
        )
        self.assertEqual(
            set(self.schema["$defs"]["output"]["required"]),
            set(state_io._OUTPUT_KEYS),
        )

    def test_runtime_enums_match_schema_enums(self) -> None:
        output = self.schema["$defs"]["output"]["properties"]
        self.assertEqual(set(output["status"]["enum"]), set(state_io.OUTPUT_STATUSES))
        self.assertEqual(
            set(output["approval_state"]["enum"]), set(state_io.APPROVAL_STATES)
        )
        self.assertEqual(
            set(output["approval_scope"]["enum"]), set(state_io.APPROVAL_SCOPES)
        )
        self.assertEqual(
            set(output["next_use"]["enum"]), set(state_io.NEXT_USE_STATES)
        )
        self.assertEqual(
            set(self.schema["$defs"]["validation_level"]["enum"]),
            set(state_io.VALIDATION_LEVELS),
        )


if __name__ == "__main__":
    unittest.main()
