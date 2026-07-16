import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "build_subtitle_review.py"
SPEC = importlib.util.spec_from_file_location("build_subtitle_review", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class SubtitleReviewTests(unittest.TestCase):
    def test_repeated_source_use_is_counted_as_union(self):
        data = [{"i": 1, "s": 10.0, "e": 20.0, "sec": "B08"}]
        cuts = [
            {"start": 11.0, "end": 16.0, "label": "HOOK"},
            {"start": 13.0, "end": 18.0, "label": "B08"},
        ]
        row = MODULE.apply_cuts(data, cuts)[0]
        self.assertEqual(row["ov"], [{"a": 11.0, "b": 18.0}])
        self.assertEqual(row["used"], 7.0)
        self.assertEqual(row["st"], "sel")
        self.assertEqual(row["clip"], "HOOK · B08")

    def test_unselected_story_cue_remains_review_zone(self):
        row = MODULE.apply_cuts(
            [{"i": 1, "s": 10.0, "e": 20.0, "sec": "B03"}],
            [],
        )[0]
        self.assertEqual(row["st"], "zone")
        self.assertEqual(row["used"], 0)

    def test_cutlist_requires_all_18_beats(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "cuts.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["order", "cut_id", "start", "end", "label", "role"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "order": 1,
                        "cut_id": "B01_01",
                        "start": 0,
                        "end": 1,
                        "label": "one",
                        "role": "test",
                    }
                )
            with self.assertRaisesRegex(ValueError, "빠진 비트"):
                MODULE.load_cuts(path)

    def test_build_replaces_existing_cuts_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template = root / "template.html"
            cutlist = root / "cuts.csv"
            output = root / "output.html"
            beats = [
                {"id": f"B{index:02d}", "at": index, "sum": "test", "mode": "", "repr": ""}
                for index in range(1, 19)
            ]
            assessment_beats = [
                {
                    "id": f"B{index:02d}",
                    "score": 80 + index % 10,
                    "verdict": "재설계" if index == 2 else "개선",
                    "summary": "AI 요약",
                    "strengths": ["강점"],
                    "add": ["추가"],
                    "improve": ["개선"],
                    "remove": ["제거"],
                    "decision": "AI 제안",
                }
                for index in range(1, 19)
            ]
            assessment = {
                "overall_score": 84,
                "overall_judgment": "전체 판단",
                "thesis": "테스트 기획 한 줄",
                "ui": {
                    "review_title": "v7 적용 후 AI 재평가",
                    "detail_heading": "비트별 적용 결과와 남은 검증",
                    "decision_label": "AI 판정",
                },
                "planning_intent": {
                    "viewer_promise": "시청자 약속",
                    "story_question": "영상 질문",
                    "character_arc": ["허세", "붕괴", "적응", "퇴장"],
                    "must_prove": ["증명"],
                    "not_this": ["공략 영상"],
                },
                "editing_intent": {
                    "selection_priority": ["선택"],
                    "rhythm": ["리듬"],
                    "audio_visual": ["화면"],
                    "remove_default": ["제거 기본값"],
                },
                "rubric": [{"name": "기획 기여", "weight": 30, "description": "설명"}],
                "priorities": [{"rank": 1, "beats": ["B02"], "action": "재설계"}],
                "beats": assessment_beats,
            }
            template.write_text(
                "<html><head><title>old</title><style></style></head><body><h1>old</h1>\n"
                '<div class="card"><h2 style="margin-top:0">기획·편집 의도</h2>\n'
                '<p class="idea">테스트 기획 한 줄</p>\n'
                '<p>3막 <b>허세 → 붕괴</b> · 편집 문법. 전체 v3: 오래된 설명</p></div>\n'
                '<div class="card">\n<h2 style="margin-top:0">승인된 이야기 스파인 18비트</h2>\n'
                '<table id="spine"><tr><th>비트</th></tr></table>\n'
                '<p class="note">행을 클릭하면 이동합니다. ✅ = 전체 편집 v3에 포함됨.</p></div>\n'
                '<div class="bar"></div><div id="list"></div><script>\n'
                'const DATA=[{"i":1,"s":1,"e":2,"st":"out","clip":"","ov":[],"used":0,"sec":"B01"}];\n'
                f"const BEATS={MODULE.json.dumps(beats, ensure_ascii=False, separators=(',', ':'))};\n"
                'const CUTS=[{"order":999,"cut_id":"OLD","start":0,"end":1,"label":"old","role":"old"}];\n'
                "DATA.forEach(r=>r.cur=(r.st==='sel'));\n"
                "const list=document.getElementById('list');\n"
                "function fmt(s){return String(s)}\n"
                "function rowHtml(r){const cls='';return '<div class=\"row '+cls+'\" id=\"r'+r.i+'\">x</div>'}\n"
                "function summary(){return {base:'full_18beat_v3',cuts:CUTS,added:[],removed:[]};}\n"
                "function buildSpine(){} function render(){}\n"
                "const heading='## 자막 검토 결과 (전체 v3 기준)';\n"
                "const download='subtitle_review_result_full_v3.json';\n"
                "buildSpine();render();\n"
                "</script></body></html>",
                encoding="utf-8",
            )
            with cutlist.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["order", "cut_id", "start", "end", "label", "role"],
                )
                writer.writeheader()
                for index in range(1, 19):
                    writer.writerow(
                        {
                            "order": index,
                            "cut_id": f"B{index:02d}_01",
                            "start": index,
                            "end": index + 0.5,
                            "label": "test",
                            "role": "test",
                        }
                    )

            stats = MODULE.build(
                template,
                cutlist,
                output,
                page_name="전체 18비트",
                version_label="v6",
                source_duration_label="82분 04초",
                media_src="../../inputs/source video.mp4",
                assessment=assessment,
            )
            rendered = output.read_text(encoding="utf-8")
            self.assertEqual(stats["cuts"], 18)
            self.assertEqual(rendered.count("const CUTS="), 1)
            self.assertEqual(len(MODULE.extract_const(rendered, "CUTS")), 18)
            self.assertIn("전체 18비트 검증 v6", rendered)
            self.assertIn("현재 v6: 원본 82분 04초", rendered)
            self.assertNotIn("전체 v3", rendered)
            self.assertIn('<video id="sourceVideo"', rendered)
            self.assertIn('src="../../inputs/source video.mp4"', rendered)
            self.assertIn(".player-card{position:static;", rendered)
            self.assertNotIn(".player-card{position:sticky", rendered)
            self.assertNotIn(".player-card{position:fixed", rendered)
            self.assertIn("전체 순서 재생", rendered)
            self.assertIn("data-seek=", rendered)
            self.assertIn("base:'full_18beat_v6',cuts:CUTS", rendered)
            self.assertIn("subtitle_review_result_full_v6.json", rendered)
            self.assertEqual(stats["assessment_beats"], 18)
            self.assertEqual(rendered.count("테스트 기획 한 줄"), 1)
            self.assertIn("v7 적용 후 AI 재평가", rendered)
            self.assertIn("const ASSESSMENT=", rendered)
            self.assertIn("비트별 적용 결과와 남은 검증", rendered)
            self.assertIn('"decision_label":"AI 판정"', rendered)


if __name__ == "__main__":
    unittest.main()
