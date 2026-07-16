import hashlib
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "register_source_assets.py"
SPEC = importlib.util.spec_from_file_location("register_source_assets", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class RegisterSourceAssetsTests(unittest.TestCase):
    def test_catalog_contract_contains_range_and_traceability_fields(self):
        self.assertIn("source_time_seconds", MODULE.CATALOG_FIELDS)
        self.assertIn("source_end_seconds", MODULE.CATALOG_FIELDS)
        self.assertIn("candidate_ids", MODULE.CATALOG_FIELDS)
        self.assertIn("bit_ids", MODULE.CATALOG_FIELDS)

    def test_hash_asset_matches_file_sha256(self):
        expected = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        self.assertEqual(MODULE.hash_asset(Path(__file__)), expected)


if __name__ == "__main__":
    unittest.main()
