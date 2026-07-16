import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "outputs" / "07_edit_export" / "support" / "build_v8_cutlists.py"
spec = importlib.util.spec_from_file_location("build_v8_cutlists", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class BuildV8CutlistsTests(unittest.TestCase):
    def setUp(self):
        self.content = module.build_content()

    def test_expected_count_duration_and_sections(self):
        self.assertEqual(len(self.content), 58)
        duration = sum(float(row["end"]) - float(row["start"]) for row in self.content)
        self.assertAlmostEqual(duration, 665.586, places=3)
        sections = {module.beat_id(row["cut_id"]) for row in self.content}
        self.assertEqual(sections, {"HOOK"} | {f"B{i:02d}" for i in range(1, 19)})

    def test_backrooms_liminal_spine_is_present(self):
        rows = {row["cut_id"]: row for row in self.content}
        self.assertEqual(rows["B02_02"]["role"], "리미널_시청자약속")
        self.assertEqual(rows["B09_01"]["role"], "공간분석")
        self.assertEqual(rows["B13_03"]["role"], "광원작동_전후결과")
        self.assertEqual(rows["B16_02"]["role"], "구현비평_공간반례")
        self.assertEqual(rows["B17_05"]["role"], "소리재해석_이해")
        self.assertNotIn("HOOK_인간형조우_비명_붙잡힘_사망", {row["label"] for row in self.content})

    def test_hook_sources_are_not_reused_in_body(self):
        hook_ranges = [
            (float(row["start"]), float(row["end"]))
            for row in self.content
            if module.beat_id(row["cut_id"]) == "HOOK"
        ]
        body_ranges = [
            (float(row["start"]), float(row["end"]))
            for row in self.content
            if module.beat_id(row["cut_id"]) != "HOOK"
        ]
        for hook_start, hook_end in hook_ranges:
            for body_start, body_end in body_ranges:
                self.assertTrue(body_end <= hook_start or body_start >= hook_end)

    def test_multisequence_contract(self):
        rows = module.build_multisequence(self.content)
        self.assertEqual(len(rows), 116)
        self.assertEqual(len({row["cut_id"] for row in rows}), 116)
        self.assertEqual(len({row["sequence"] for row in rows}), 20)

    def test_dialogue_edges_do_not_split_srt_cues(self):
        srt_path = ROOT / "inputs" / "2026-06-30 00-23-03.srt"
        text = srt_path.read_text(encoding="utf-8-sig")

        def seconds(value):
            hour, minute, rest = value.split(":")
            second, millisecond = rest.split(",")
            return int(hour) * 3600 + int(minute) * 60 + int(second) + int(millisecond) / 1000

        cues = []
        for block in re.split(r"\n\s*\n", text.strip()):
            lines = block.splitlines()
            if len(lines) >= 2 and "-->" in lines[1]:
                start, end = (part.strip() for part in lines[1].split("-->", 1))
                cues.append((seconds(start), seconds(end)))

        risks = []
        for row in self.content:
            for edge_name in ("start", "end"):
                edge = float(row[edge_name])
                if any(start + 0.05 < edge < end - 0.05 for start, end in cues):
                    risks.append((row["cut_id"], edge_name, edge))
        self.assertEqual(risks, [])


if __name__ == "__main__":
    unittest.main()
