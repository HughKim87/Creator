import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "source_frame_assets.py"
SPEC = importlib.util.spec_from_file_location("source_frame_assets", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class SourceFrameAssetTests(unittest.TestCase):
    def test_parse_time_and_even_sampling(self):
        self.assertEqual(MODULE.parse_time("01:02:03.5"), 3723.5)
        self.assertEqual(MODULE.parse_time("02:03.5"), 123.5)
        self.assertEqual(MODULE.sample_times(10, 20, 3), [10.0, 15.0, 20.0])

    def test_canonical_name_uses_source_time_and_frame(self):
        self.assertEqual(
            MODULE.canonical_name(34.3, 2058, 1024),
            "src_t0000034300_f000002058_w1024.jpg",
        )

    def test_higher_resolution_existing_frame_is_reused(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            frame = root / "assets" / "frame.jpg"
            frame.parent.mkdir(parents=True)
            frame.write_bytes(b"jpeg")
            original_root = MODULE.ROOT
            MODULE.ROOT = root
            try:
                row = {field: "" for field in MODULE.FIELDS}
                row.update(
                    {
                        "asset_id": "source_t0000034300_w1024",
                        "source_id": "source",
                        "source_size": "100",
                        "source_mtime_ns": "200",
                        "source_time_seconds": "34.300",
                        "source_frame": "2058",
                        "width": "1024",
                        "kind": "source_frame",
                        "path": "assets/frame.jpg",
                        "status": "current",
                    }
                )
                found = MODULE.find_reusable(
                    [row],
                    source_id="source",
                    source_size=100,
                    source_mtime_ns=200,
                    source_time=34.3,
                    width=512,
                )
                self.assertEqual(found, row)
            finally:
                MODULE.ROOT = original_root

    def test_temporary_and_backup_output_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            original_root = MODULE.ROOT
            MODULE.ROOT = root
            try:
                with self.assertRaisesRegex(ValueError, "temporary or backup"):
                    MODULE.resolve_project_path("temp/frames", "asset root")
                with self.assertRaisesRegex(ValueError, "temporary or backup"):
                    MODULE.resolve_project_path("backups/frames", "asset root")
            finally:
                MODULE.ROOT = original_root

    def test_same_fingerprint_cannot_use_a_new_source_id(self):
        rows = [
            {
                "source_id": "source_a",
                "source_size": "100",
                "source_mtime_ns": "200",
                "status": "current",
            }
        ]
        with self.assertRaisesRegex(ValueError, "already registered as source_a"):
            MODULE.validate_source_identity(
                rows,
                source_id="source_b",
                source_size=100,
                source_mtime_ns=200,
            )

    def test_source_id_cannot_mix_a_changed_fingerprint(self):
        rows = [
            {
                "source_id": "source_a",
                "source_size": "100",
                "source_mtime_ns": "200",
                "status": "current",
            }
        ]
        with self.assertRaisesRegex(ValueError, "different source fingerprint"):
            MODULE.validate_source_identity(
                rows,
                source_id="source_a",
                source_size=101,
                source_mtime_ns=201,
            )

    def test_matching_source_identity_is_allowed(self):
        rows = [
            {
                "source_id": "source_a",
                "source_size": "100",
                "source_mtime_ns": "200",
                "status": "current",
            }
        ]
        MODULE.validate_source_identity(
            rows,
            source_id="source_a",
            source_size=100,
            source_mtime_ns=200,
        )


if __name__ == "__main__":
    unittest.main()
