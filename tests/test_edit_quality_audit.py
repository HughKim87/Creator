import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "edit_quality_audit.py"
SPEC = importlib.util.spec_from_file_location("edit_quality_audit", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def cut(cut_id, start, end):
    return MODULE.Cut(
        cut_id=cut_id,
        section=MODULE.section_from_cut_id(cut_id),
        start=start,
        end=end,
        label=cut_id,
    )


def profile(section, mode, waive=(), justification=""):
    return MODULE.Profile(section, mode, frozenset(waive), justification)


class EditQualityAuditTests(unittest.TestCase):
    def test_long_single_compress_block_requires_review(self):
        cuts = [cut("B01_01", 0, 13)]
        profiles = {"B01": profile("B01", "compress")}
        _, findings = MODULE.audit(cuts, profiles)
        codes = {(finding.code, finding.status) for finding in findings}
        self.assertIn(("AVG_LONG", "REVIEW"), codes)
        self.assertIn(("MAX_LONG", "REVIEW"), codes)
        self.assertIn(("SINGLE_BLOCK", "REVIEW"), codes)

    def test_evidenced_waiver_remains_visible(self):
        cuts = [cut("B03_01", 0, 20)]
        profiles = {
            "B03": profile(
                "B03",
                "radio",
                {"AVG_LONG", "MAX_LONG", "SINGLE_BLOCK"},
                "연결 문장과 사건 화면을 함께 보존",
            )
        }
        _, findings = MODULE.audit(cuts, profiles)
        self.assertTrue(findings)
        self.assertTrue(all(finding.status == "WAIVED" for finding in findings))

    def test_late_density_cliff_is_reported(self):
        cuts = [
            cut("B01_01", 0, 2),
            cut("B01_02", 3, 5),
            cut("B13_01", 10, 20),
            cut("B13_02", 21, 31),
        ]
        profiles = {
            "B01": profile("B01", "compress"),
            "B13": profile("B13", "breath"),
            "GLOBAL": profile("GLOBAL", "global"),
        }
        _, findings = MODULE.audit(cuts, profiles)
        self.assertTrue(
            any(
                finding.code == "LATE_DENSITY_CLIFF"
                and finding.status == "REVIEW"
                for finding in findings
            )
        )

    def test_waiver_requires_justification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "profile.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["section", "mode", "waive", "justification"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "section": "B01",
                        "mode": "compress",
                        "waive": "AVG_LONG",
                        "justification": "",
                    }
                )
            with self.assertRaisesRegex(ValueError, "justification"):
                MODULE.load_profiles(path)


if __name__ == "__main__":
    unittest.main()
