from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "extension" / "src"))

from local_runtime import (  # noqa: E402
    DEFAULT_MANIFEST,
    RuntimeManifestError,
    load_manifest,
    tree_record,
    verify_runtime,
)


def fixture_manifest(component_root: Path) -> dict[str, object]:
    record = tree_record(component_root)
    payload = component_root / "tool.bin"
    import hashlib

    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    return {
        "$schema": "../schemas/local-runtime-v1.schema.json",
        "schema_version": "local-runtime-v1",
        "runtime_root": "extension/.runtime",
        "retention": "gitignored-local-capability",
        "tree_digest": "sha256(sorted-posix-path-ordinal|bytes|sha256-with-lf)",
        "verified_on": "2026-07-31",
        "components": [
            {
                "id": "fixture-tool",
                "status": "retained-shared-tool",
                "role": "synthetic fixture",
                "version": "1.0",
                "platform": "windows-x86_64",
                "relative_root": "fixture",
                **record,
                "critical_files": [
                    {
                        "role": "tool",
                        "path": "tool.bin",
                        "bytes": payload.stat().st_size,
                        "sha256": digest,
                    }
                ],
                "probe": {"kind": "none"},
                "source": {
                    "project_url": "https://example.com/project",
                    "distribution_url": "https://example.com/releases/1.0",
                    "release_label": "fixture 1.0",
                    "source_commit": "1234567",
                    "license": "MIT",
                    "license_path": None,
                    "reinstall": "Restore the synthetic fixture.",
                },
            }
        ],
    }


class LocalRuntimeTests(unittest.TestCase):
    def test_schema_and_tracked_manifest_field_sets_match(self) -> None:
        manifest = load_manifest(DEFAULT_MANIFEST)
        schema = json.loads(
            (
                ROOT
                / "extension"
                / "schemas"
                / "local-runtime-v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(set(schema["required"]), set(manifest))
        component_schema = schema["$defs"]["component"]
        for component in manifest["components"]:
            self.assertEqual(set(component_schema["required"]), set(component))
        source_schema = schema["$defs"]["source"]
        for component in manifest["components"]:
            self.assertTrue(
                set(source_schema["required"]).issubset(component["source"])
            )

    def test_tracked_manifest_keeps_primary_and_optional_backends_distinct(self) -> None:
        manifest = load_manifest(DEFAULT_MANIFEST)
        self.assertEqual(len(manifest["components"]), 2)
        statuses = {component["status"] for component in manifest["components"]}
        self.assertEqual(
            statuses,
            {"retained-shared-tool", "retained-optional-backend"},
        )
        whisper = next(
            component
            for component in manifest["components"]
            if component["status"] == "retained-optional-backend"
        )
        self.assertIn("not the faster-whisper primary backend", whisper["role"])

    def test_clean_clone_absence_is_optional_but_require_present_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="local-runtime-absent-") as temp:
            root = Path(temp) / "missing"
            optional = verify_runtime(DEFAULT_MANIFEST, runtime_root=root)
            self.assertTrue(optional["ok"])
            self.assertEqual(optional["status"], "absent")
            required = verify_runtime(
                DEFAULT_MANIFEST,
                runtime_root=root,
                require_present=True,
            )
            self.assertFalse(required["ok"])
            self.assertEqual(required["status"], "absent")

    def test_fixture_tree_is_ready_and_hash_drift_is_detected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="local-runtime-fixture-") as temp:
            root = Path(temp)
            component = root / "fixture"
            component.mkdir()
            payload = component / "tool.bin"
            payload.write_bytes(b"verified-runtime")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(fixture_manifest(component)),
                encoding="utf-8",
            )
            ready = verify_runtime(
                manifest_path,
                runtime_root=root,
                require_present=True,
            )
            self.assertTrue(ready["ok"])
            self.assertEqual(ready["status"], "ready")
            payload.write_bytes(b"drifted-runtime")
            drift = verify_runtime(
                manifest_path,
                runtime_root=root,
                require_present=True,
            )
            self.assertFalse(drift["ok"])
            self.assertEqual(drift["status"], "drift")

    def test_manifest_rejects_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="local-runtime-unsafe-") as temp:
            root = Path(temp)
            component = root / "fixture"
            component.mkdir()
            (component / "tool.bin").write_bytes(b"fixture")
            value = fixture_manifest(component)
            value["components"][0]["relative_root"] = "../outside"  # type: ignore[index]
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(RuntimeManifestError):
                load_manifest(manifest_path)

    def test_manifest_rejects_incomplete_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="local-runtime-source-") as temp:
            root = Path(temp)
            component = root / "fixture"
            component.mkdir()
            (component / "tool.bin").write_bytes(b"fixture")
            value = fixture_manifest(component)
            del value["components"][0]["source"]["license"]  # type: ignore[index]
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(RuntimeManifestError):
                load_manifest(manifest_path)


if __name__ == "__main__":
    unittest.main()
