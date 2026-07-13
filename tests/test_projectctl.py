import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "projectctl.py"
SPEC = importlib.util.spec_from_file_location("projectctl", MODULE_PATH)
PROJECTCTL = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = PROJECTCTL
SPEC.loader.exec_module(PROJECTCTL)


class ProjectControlTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "outputs").mkdir()
        (self.root / "outputs" / "SESSION_HANDOFF.md").write_text(
            "source_id: `sample_source`\nPRIVATE TASK DETAIL\n", encoding="utf-8"
        )

    def test_missing_state_is_read_only_and_routes_to_handoff(self):
        data = PROJECTCTL.snapshot(self.root)
        self.assertFalse(data["state_exists"])
        self.assertIsNone(data["active_task"])
        self.assertEqual(data["handoff"]["source_id"], "sample_source")
        self.assertFalse((self.root / PROJECTCTL.STATE_RELATIVE).exists())
        context = PROJECTCTL.render_context(data)
        self.assertIn("outputs/SESSION_HANDOFF.md", context)
        self.assertNotIn("PRIVATE TASK DETAIL", context)

    def test_start_is_idempotent_for_same_owner_and_rejects_conflict(self):
        state, created = PROJECTCTL.start_task(
            self.root, "shared-control", "Shared control", "codex", "session-a"
        )
        self.assertTrue(created)
        self.assertEqual(state["active_task"]["id"], "shared-control")

        same_state, created_again = PROJECTCTL.start_task(
            self.root, "shared-control", "Shared control", "codex", "session-a"
        )
        self.assertFalse(created_again)
        self.assertEqual(same_state["active_task"], state["active_task"])

        with self.assertRaises(PROJECTCTL.ProjectCtlError):
            PROJECTCTL.start_task(self.root, "other-task", "Other", "claude")

    def test_failed_verification_keeps_task_active(self):
        PROJECTCTL.start_task(self.root, "verify-gate", "Verify gate", "codex")

        def failed(_root):
            return {
                "ok": False,
                "checked_at": "2026-07-14T00:00:00+09:00",
                "checks": [{"name": "unit_tests", "ok": False}],
            }

        state, verification = PROJECTCTL.finish_task(
            self.root, "verify-gate", "should not finish", verify=failed
        )
        self.assertIsNone(state)
        self.assertFalse(verification["ok"])
        persisted, _ = PROJECTCTL.load_state(self.root)
        self.assertEqual(persisted["active_task"]["id"], "verify-gate")
        self.assertIsNone(persisted["last_completed"])

    def test_successful_verification_writes_compact_receipt(self):
        PROJECTCTL.start_task(self.root, "verified-task", "Verified task", "gemini")

        def passed(_root):
            return {
                "ok": True,
                "checked_at": "2026-07-14T00:00:00+09:00",
                "checks": [
                    {"name": "doccheck", "ok": True, "detail": "large output is not persisted"},
                    {"name": "unit_tests", "ok": True},
                ],
            }

        state, verification = PROJECTCTL.finish_task(
            self.root, "verified-task", "done", verify=passed
        )
        self.assertTrue(verification["ok"])
        self.assertIsNone(state["active_task"])
        self.assertEqual(state["last_completed"]["summary"], "done")
        self.assertEqual(
            state["last_completed"]["verification"]["checks"],
            ["doccheck", "unit_tests"],
        )
        raw = (self.root / PROJECTCTL.STATE_RELATIVE).read_text(encoding="utf-8")
        self.assertNotIn("large output is not persisted", raw)

    def test_schema_covers_default_state(self):
        schema = json.loads((ROOT / "tools" / "projectctl.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], PROJECTCTL.SCHEMA_VERSION)
        self.assertEqual(set(schema["required"]), set(PROJECTCTL.default_state()))

    def test_decodes_windows_localized_subprocess_output(self):
        self.assertEqual(PROJECTCTL._decode_output("문서 검사 통과".encode("cp949")), "문서 검사 통과")

    def test_corrupt_state_is_not_silently_replaced(self):
        (self.root / PROJECTCTL.STATE_RELATIVE).write_text("{broken", encoding="utf-8")
        with self.assertRaises(PROJECTCTL.ProjectCtlError):
            PROJECTCTL.load_state(self.root)
        self.assertEqual(
            (self.root / PROJECTCTL.STATE_RELATIVE).read_text(encoding="utf-8"),
            "{broken",
        )


if __name__ == "__main__":
    unittest.main()
