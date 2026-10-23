"""Synthetic calculation/CLI checks; no channel data or external writes."""
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'extension/src'))
from youtube_analysis import (chapter_candidates, lint_pair, read_retention, read_srt,
                              retention_report, validate_chapters)

COMPARE_PATH = ROOT / '.agents/skills/game-trend-brief/scripts/compare_views.py'
spec = importlib.util.spec_from_file_location('compare_views', COMPARE_PATH)
COMPARE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(COMPARE)


class YouTubeToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'extension/work', prefix='youtube-tools-')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def write(self, name, text):
        p = self.folder / name
        p.write_text(text, encoding='utf-8-sig')
        return p

    def rows(self):
        return [dict(url=f'https://example.invalid/{i}', title=f'한국어 리뷰 {i}', channel='합성채널',
                     views=views, format='롱폼', cohort='한국어 리뷰 / 게시 48~72시간',
                     checked_at='2026-10-23T12:00:00+09:00')
                for i, views in enumerate([1000, 2000, 2000, 20000])]

    def test_comparable_cohorts_and_median(self):
        rows = self.rows()
        rows += [dict(rows[0], url='https://example.invalid/short', format='쇼츠', views=999999)]
        result = COMPARE.compare(rows)
        self.assertEqual(result['videos'][0]['multiple'], 10)
        self.assertEqual(result['videos'][0]['median'], 2000)
        self.assertEqual(result['skipped'][0]['format'], '쇼츠')
        self.assertEqual(len(result['videos']), 4)

    def test_insufficient_zero_and_invalid_views(self):
        self.assertEqual(COMPARE.compare(self.rows()[:3])['videos'], [])
        self.assertEqual(COMPARE.compare([dict(r, views=0) for r in self.rows()])['videos'], [])
        for views in [None, True, -1, math.nan, math.inf, '2만']:
            with self.subTest(views=views), self.assertRaises(ValueError):
                COMPARE.compare([dict(self.rows()[0], views=views)])
        with self.assertRaises(ValueError):
            COMPARE.compare(self.rows() + [self.rows()[0]])

    def test_short_seconds_axis_is_not_guessed_as_percent(self):
        path = self.write('유지율.csv', '초,유지율\n0,100\n10,90\n20,80\n40,70\n')
        points = read_retention(path, position_column='초', retention_column='유지율', axis='seconds', unit='percent', duration=40)
        result = retention_report(points, 40)
        self.assertEqual(result['coverage_seconds'], [0, 40])
        self.assertEqual(result['opening_drop_pp'], 25)
        self.assertEqual(result['middle_net_drop_pp_per_second'], .5)

    def test_percent_and_ratio_are_equivalent_and_allow_rewatch(self):
        percent = self.write('percent.csv', '위치,유지\n0%,120%\n50%,90%\n100%,80%\n')
        ratio = self.write('ratio.csv', '위치,유지\n0,1.2\n0.5,0.9\n1,0.8\n')
        def load(p, axis, unit):
            return read_retention(p, position_column='위치', retention_column='유지', axis=axis, unit=unit, duration=60)
        self.assertEqual(load(percent, 'percent', 'percent'), load(ratio, 'ratio', 'ratio'))
        with self.assertRaises(ValueError):
            load(percent, 'ratio', 'ratio')

    def test_invalid_missing_unordered_or_out_of_bounds_csv(self):
        for row in ['10,\n', '10,nan\n', '0,90\n', '61,90\n', '-1,90\n']:
            with self.subTest(row=row), self.assertRaises(ValueError):
                p = self.write('bad.csv', '초,유지\n0,100\n' + row)
                read_retention(p, position_column='초', retention_column='유지', axis='seconds', unit='percent', duration=60)

    def test_srt_binding_and_no_extrapolation(self):
        path = self.write('자막.srt', '1\n00:00:10,000 --> 00:00:15,000\n비교 조건을 확인합니다.\n\n2\n00:00:20,000 --> 00:00:25,000\n선택 기준입니다.\n')
        cues = read_srt(path)
        result = retention_report([(5, 100), (15, 70), (30, 75)], 40, cues)
        self.assertIsNone(result['opening_drop_pp'])
        self.assertEqual(result['drop_candidates'][0]['transcript'][0]['text'], '비교 조건을 확인합니다.')
        self.assertEqual(len(result['drop_candidates']), 1)
        with self.assertRaises(ValueError):
            retention_report([(0, 100), (10, 50)], 10, cues)

    def test_weighted_slide_does_not_depend_on_sampling_density(self):
        sparse = retention_report([(0, 100), (30, 90), (40, 80), (100, 68)], 100)
        dense = retention_report([(0, 100), (30, 90), (40, 80), (60, 76), (100, 68)], 100)
        self.assertEqual(sparse['middle_net_drop_pp_per_second'], dense['middle_net_drop_pp_per_second'])

    def test_korean_shared_words_are_advisory_not_rejection(self):
        result = lint_pair('아이온2 지금 시작할까?', '아이온2 먼저 확인할 것')
        self.assertIn('아이온2', result['shared_tokens'])
        self.assertEqual(result['errors'], [])
        self.assertTrue(result['warnings'])
        self.assertEqual(lint_pair('갈아탈까?', '먼저 확인하세요')['errors'], [])
        self.assertTrue(lint_pair('가' * 101, '짧은 문구')['errors'])
        self.assertTrue(lint_pair('제목\n다음 줄', '문구')['errors'])

    def test_chapter_final_interval_order_and_short_videos(self):
        rows = [{'start': 0, 'title': '첫 질문'}, {'start': 20, 'title': '실제 비교'}, {'start': 40, 'title': '선택 기준'}]
        self.assertTrue(validate_chapters(rows, 60)['valid'])
        self.assertTrue(validate_chapters(rows, 60)['block'].startswith('00:00 첫 질문'))
        self.assertFalse(validate_chapters(rows, 45)['valid'])
        self.assertFalse(validate_chapters(list(reversed(rows)), 60)['valid'])
        self.assertFalse(validate_chapters(rows[:2], 25)['valid'])
        with self.assertRaises(ValueError):
            validate_chapters([{'start': 0, 'title': '제목\n줄'}], 60)

    def test_korean_boundary_candidates_preserve_evidence(self):
        cues = [{'start': i * 12, 'end': i * 12 + 5, 'text': text}
                for i, text in enumerate(['신작 출시 소개', '직업 선택 방법', '전투 실제 비교', '과금 조건 확인', '선택 기준 정리'])]
        result = chapter_candidates(cues, 60, target=3)
        self.assertEqual(len(result['candidates']), 3)
        self.assertEqual(result['candidates'][0]['start'], 0)
        self.assertIn('신작 출시 소개', result['candidates'][0]['evidence'])
        self.assertNotIn('valid', result)

    def cli(self, relative, *args):
        return subprocess.run([sys.executable, '-B', str(ROOT / relative), *map(str, args)],
                              cwd=ROOT, env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1'},
                              capture_output=True, text=True, encoding='utf-8')

    def test_all_cli_entrypoints(self):
        observed = self.write('관측.json', json.dumps(self.rows(), ensure_ascii=False))
        csv_path = self.write('유지.csv', '영상 위치,유지율\n0,100\n30,75\n60,60\n')
        srt = self.write('최종.srt', '1\n00:00:00,000 --> 00:00:05,000\n첫 질문\n\n2\n00:00:20,000 --> 00:00:25,000\n실제 비교\n\n3\n00:00:40,000 --> 00:00:45,000\n선택 기준\n')
        chapters = self.write('챕터.json', json.dumps([{'start': i * 20, 'title': t} for i, t in enumerate(['질문', '비교', '결론'])], ensure_ascii=False))
        calls = [
            ('.agents/skills/game-trend-brief/scripts/compare_views.py', observed),
            ('.agents/skills/youtube-title-thumbnail/scripts/analyze_retention.py', csv_path, '--position-column', '영상 위치', '--retention-column', '유지율', '--axis', 'seconds', '--unit', 'percent', '--duration', 60, '--srt', srt),
            ('.agents/skills/youtube-title-thumbnail/scripts/lint_pair.py', '--title', '신작 살까?', '--thumbnail', '구매 전 확인'),
            ('.agents/skills/prepare-youtube-upload/scripts/chapters.py', 'suggest', srt, '--duration', 60),
            ('.agents/skills/prepare-youtube-upload/scripts/chapters.py', 'validate', chapters, '--duration', 60),
        ]
        for relative, *args in calls:
            with self.subTest(relative=relative, args=args):
                run = self.cli(relative, *args)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertIsInstance(json.loads(run.stdout), dict)
        run = self.cli('.agents/skills/prepare-youtube-upload/scripts/chapters.py', 'validate', chapters, '--duration', 45)
        self.assertEqual(run.returncode, 1)
        self.assertFalse(json.loads(run.stdout)['valid'])


if __name__ == '__main__':
    unittest.main()
