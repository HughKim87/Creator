import csv
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "outputs" / "07_edit_export" / "support" / "build_v7_cutlists.py"
BASELINE = ROOT / "outputs" / "07_edit_export" / "cutlist_full_18beat_v6.csv"
spec = importlib.util.spec_from_file_location("build_v7_cutlists", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class BuildV7CutlistsTests(unittest.TestCase):
    def setUp(self):
        with BASELINE.open(encoding="utf-8-sig", newline="") as handle:
            self.baseline = list(csv.DictReader(handle))
        self.content = module.transform(self.baseline)

    def test_expected_count_duration_and_beats(self):
        self.assertEqual(len(self.content), 88)
        duration = sum(float(row["end"]) - float(row["start"]) for row in self.content)
        self.assertAlmostEqual(duration, 578.28, places=2)
        beat_ids = {module.beat_id(row["cut_id"]) for row in self.content}
        self.assertTrue({f"B{i:02d}" for i in range(1, 19)} <= beat_ids)

    def test_priority_changes_are_applied(self):
        rows = {row["cut_id"]: row for row in self.content}
        self.assertNotIn("B07_11", rows)
        self.assertNotIn("B15_05", rows)
        self.assertEqual(rows["B10_02"]["start"], "2917.19")
        self.assertEqual(rows["B11_03"]["role"], "훅사건_콜백")
        self.assertEqual(rows["B14_05"]["label"], "B14_규칙활용_달리기성공")
        self.assertEqual(rows["B17_02"]["end"], "4513.94")

    def test_multisequence_contract(self):
        rows = module.build_multisequence(self.content)
        self.assertEqual(len(rows), 176)
        self.assertEqual(len({row["cut_id"] for row in rows}), 176)
        self.assertEqual(len({row["sequence"] for row in rows}), 20)


if __name__ == "__main__":
    unittest.main()
