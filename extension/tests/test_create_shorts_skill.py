"""Synthetic helper tests; do not claim real speech/editorial quality from these."""
import copy
import functools
import hashlib
import http.server
import importlib.util
import json
import subprocess
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SKILL = BASE.parent / '.agents/skills/create-shorts'
WORK = None
spec = importlib.util.spec_from_file_location('shorts_review', SKILL / 'scripts/shorts_review.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class ShortsSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global WORK
        scratch = BASE / 'data'
        scratch.mkdir(parents=True, exist_ok=True)
        cls.scratch = tempfile.TemporaryDirectory(prefix='shorts-skill-test-', dir=scratch)
        cls.addClassCleanup(cls.scratch.cleanup)
        WORK = Path(cls.scratch.name).resolve()
        cls.source = WORK / '합성 원본 fixture.mp4'
        if not cls.source.exists():
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=30',
                            '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '8',
                            '-c:v', 'libx264', '-preset', 'ultrafast', '-threads', '2', '-c:a', 'aac',
                            '-shortest', '-n', str(cls.source)], check=True)
        cls.original_sha = hashlib.sha256(cls.source.read_bytes()).hexdigest()
        cls.data = {'job_id': 'synthetic-shorts-test', 'source': str(cls.source),
                    'source_label': '합성 영상 · 실제 전사 아님', 'source_duration': 8,
                    'actual_listening': 'not_run', 'clips': [
                        {'id': '001', 'revision': 'r1', 'title': '설명 후보', 'category': '설명',
                         'reason': '합성 도구 검증용', 'parts': [{'start': 0, 'end': 2}, {'start': 5, 'end': 7}],
                         'file': 'videos/001-r1.mp4', 'caption_status': 'aligned',
                         'caption_method': '합성 fixture · 음성 전사 아님',
                         'captions': [{'start': .2, 'end': 1.5, 'text': '합성 자막'}],
                         'uncertain': [{'id': 'word-1', 'start': .2, 'end': 1.5, 'text': '현재 표현',
                                        'alternatives': ['대안 표현'], 'reason': '확인 게이트 시험'}]},
                        {'id': '007', 'revision': 'r1', 'title': '다른 후보', 'category': '반전',
                         'reason': '번호와 선택 보존 시험', 'parts': [{'start': 2, 'end': 4}],
                         'file': 'videos/007-r1.mp4', 'caption_status': 'unverified',
                         'captions': [{'start': 0, 'end': 1, 'text': '표시하면 안 되는 미검증 자막'}],
                         'uncertain': []}]}
        cls.root = WORK / 'fixture-review'
        helper.previews(cls.data, cls.root)
        helper.gallery(cls.data, cls.root)
        (WORK / 'fixture-manifest.json').write_text(json.dumps(cls.data, ensure_ascii=False, indent=2), encoding='utf-8')

    def load(self, data):
        p = WORK / 'validation-case.json'
        p.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        return helper.read_manifest(p)

    def selection(self):
        c = self.data['clips'][0]
        return {'job_id': self.data['job_id'], 'selection_only': True,
                'clips': [{'id': c['id'], 'revision': c['revision'], 'parts': c['parts'],
                           'selected': True, 'note': '합성 확인', 'confirmations': []}]}

    def test_valid_manifest_and_source_unchanged(self):
        self.assertEqual(len(self.load(self.data)['clips']), 2)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.original_sha)

    def test_invalid_time_and_outside_source(self):
        for value in [float('nan'), float('inf'), True, -1, 20]:
            d = copy.deepcopy(self.data)
            d['clips'][0]['parts'][0]['start'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.load(d)

    def test_caption_overlap_rejected(self):
        d = copy.deepcopy(self.data)
        d['clips'][0]['captions'].append({'start': 1, 'end': 2, 'text': 'overlap'})
        with self.assertRaises(ValueError):
            self.load(d)

    def test_unconfirmed_caption_blocks_final(self):
        with self.assertRaisesRegex(ValueError, 'confirmation'):
            helper.final_gate(self.data, self.selection())

    def test_user_correction_allows_selected_clip(self):
        s = self.selection()
        s['clips'][0]['confirmations'] = [{**self.data['clips'][0]['uncertain'][0],
                                          'confirmed': True, 'replacement': '확인한 표현'}]
        self.assertEqual(helper.final_gate(self.data, s), ['001'])
        s['clips'][0]['confirmations'][0]['replacement'] = '[자막 생략]'
        self.assertEqual(helper.final_gate(self.data, s), ['001'])

    def test_stale_time_revision_and_parts_rejected(self):
        s = self.selection()
        s['clips'][0]['confirmations'] = [{**self.data['clips'][0]['uncertain'][0],
                                          'confirmed': True, 'replacement': '확인한 표현'}]
        for change in ['time', 'revision', 'parts']:
            old = copy.deepcopy(s)
            if change == 'time':
                old['clips'][0]['confirmations'][0]['end'] = 1.4
            elif change == 'revision':
                old['clips'][0]['revision'] = 'r0'
            else:
                old['clips'][0]['parts'] = [{'start': 1, 'end': 3}, {'start': 5, 'end': 7}]
            with self.subTest(change=change), self.assertRaises(ValueError):
                helper.final_gate(self.data, old)

    def test_unverified_and_wrong_job_rejected(self):
        s = self.selection()
        s['job_id'] = 'another-job'
        with self.assertRaises(ValueError):
            helper.final_gate(self.data, s)
        s = self.selection()
        s['clips'] = [{'id': '007', 'revision': 'r1', 'parts': self.data['clips'][1]['parts'], 'selected': True}]
        with self.assertRaises(ValueError):
            helper.final_gate(self.data, s)

    def test_preview_concat_length_pixels_and_decode(self):
        p = self.root / 'videos/001-r1.mp4'
        info = helper.probe(p)
        self.assertAlmostEqual(float(info['format']['duration']), 4, delta=.1)
        video = next(s for s in info['streams'] if s['codec_type'] == 'video')
        self.assertEqual(video['width'], 640)
        self.assertEqual(video['sample_aspect_ratio'], '1:1')
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'null', '-'], check=True)

    def test_changed_parts_cannot_reuse_same_preview(self):
        d = copy.deepcopy(self.data)
        d['clips'][0]['parts'] = [{'start': 1, 'end': 3}, {'start': 5, 'end': 7}]
        with self.assertRaisesRegex(ValueError, 'changed existing preview'):
            helper.previews(d, self.root)

    def test_gallery_data_escape_and_no_absolute_source(self):
        d = copy.deepcopy(self.data)
        d['clips'][0]['title'] = '</script><script>alert(1)</script>'
        root = WORK / 'escape-review'
        root.mkdir(exist_ok=True)
        for c in d['clips']:
            p = root / c['file']
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists():
                p.write_bytes((self.root / c['file']).read_bytes())
        helper.gallery(d, root)
        html = (root / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn(d['source'], html)
        self.assertNotIn('</script><script>alert(1)</script>', html)
        self.assertIn('\\u003c/script\\u003e', html)
        other = copy.deepcopy(d)
        other['job_id'] = 'unrelated-job'
        with self.assertRaises(ValueError):
            helper.gallery(other, root)

    def test_http_ranges_head_and_traversal(self):
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(helper.RangeHandler, root=self.root))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        payload = (self.root / 'videos/001-r1.mp4').read_bytes()
        try:
            for value, expected in [('bytes=0-31', payload[:32]), ('bytes=-8', payload[-8:]), ('bytes=32-', payload[32:])]:
                req = urllib.request.Request(base + '/videos/001-r1.mp4', headers={'Range': value})
                with urllib.request.urlopen(req) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.read(), expected)
            with urllib.request.urlopen(urllib.request.Request(base + '/videos/001-r1.mp4', method='HEAD')) as response:
                self.assertEqual(int(response.headers['Content-Length']), len(payload))
                self.assertEqual(response.read(), b'')
            for path, status in [('/%2e%2e/fixture-manifest.json', 403), ('/videos/', 404)]:
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    urllib.request.urlopen(base + path)
                self.assertEqual(raised.exception.code, status)
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(urllib.request.Request(base + '/videos/001-r1.mp4', headers={'Range': 'bytes=999999999-'}))
            self.assertEqual(raised.exception.code, 416)
        finally:
            server.shutdown()
            thread.join(timeout=3)
            server.server_close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
