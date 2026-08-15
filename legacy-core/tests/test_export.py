from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "src"))

from file_data import (  # noqa: E402
    ExportContractError,
    get_export_manifest,
    validate_export_manifest,
)


class ExportContractTests(unittest.TestCase):
    def test_manifest_is_domain_neutral_and_copyable(self) -> None:
        manifest = get_export_manifest()
        self.assertEqual(manifest["manifest_version"], 1)
        self.assertEqual(manifest["compatibility"]["record_schema"], 1)
        self.assertTrue(manifest["compatibility"]["read_legacy_records"])
        self.assertNotIn("youtube", repr(manifest).casefold())
        self.assertNotIn("game", repr(manifest).casefold())
        manifest["exports"].append("mutated")
        self.assertNotIn("mutated", get_export_manifest()["exports"])

    def test_manifest_rejects_unknown_fields_and_bad_revision(self) -> None:
        manifest = get_export_manifest()
        manifest["unexpected"] = True
        with self.assertRaises(ExportContractError):
            validate_export_manifest(manifest)
        manifest = get_export_manifest()
        manifest["manifest_version"] = 2
        with self.assertRaises(ExportContractError):
            validate_export_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
