"""Candidate mechanics and source/continuity failure injection, not semantic QA."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'extension/src'))
sys.path.insert(0, str(ROOT / 'extension/tests'))
from editorial_test_support import synthetic_state
from test_video_editing_review_proxy import candidate

SCRIPT = ROOT / '.agents/skills/edit-gameplay-video/scripts/render_candidate.py'
module_spec = importlib.util.spec_from_file_location('gameplay_candidate', SCRIPT)
renderer = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(renderer)


class CandidateChecks(unittest.TestCase):
    def setUp(self):
        self.value = candidate()
        self.state = synthetic_state(self.value)

    def test_independent_audio_edges_are_preserved_without_approval(self):
        original = deepcopy(self.value)
        timeline, rate, spf, frames, evidence = renderer.checked_spec(self.value, self.state)
        self.assertEqual((int(rate), spf, frames), (60, 800, 240))
        self.assertEqual(timeline['sequence']['audio_clips'][1]['source_in'], 298)
        self.assertEqual(evidence['semantic_status'], 'not_run')
        self.assertEqual(self.value, original)

    def test_required_cause_cannot_be_removed(self):
        self.state['scenes'][0]['anchors'].append(dict(id='missing-cause', source_in=200, source_out=210,
                                                     media_scope='video', observation='Synthetic causal action'))
        from editorial_test_support import refresh_review
        refresh_review(self.value, self.state)
        with self.assertRaisesRegex(ValueError, 'required anchor missing'):
            renderer.checked_spec(self.value, self.state)

    def test_unknown_omission_cannot_be_treated_as_redundant(self):
        self.state['reviews'][0]['omissions'][0]['certainty'] = 'uncertain'
        with self.assertRaisesRegex(ValueError, 'uncertain omission'):
            renderer.checked_spec(self.value, self.state)

    def test_known_failed_boundary_blocks_candidate(self):
        self.value['editorial_evidence']['microbeats'][0]['boundary_review'] = 'failed'
        with self.assertRaisesRegex(ValueError, 'failed boundary'):
            renderer.checked_spec(self.value, self.state)

    def test_word_interior_edge_is_a_hint_not_a_pass(self):
        raw = {'segments': [{'words': [{'start': 1.9, 'end': 2.1, 'word': 'unfinished'}]}]}
        findings = renderer.speech_findings(self.value, raw)
        self.assertTrue(findings)
        self.assertTrue(all(f['status'] == 'needs_observation' for f in findings))
        self.assertEqual(self.value['validation']['semantic_status'], 'not_run')

    def test_noninteger_audio_boundary_is_not_silently_resampled(self):
        self.value['source_manifest']['audio']['sample_rate'] = 44101
        self.state = synthetic_state(self.value)
        with self.assertRaisesRegex(ValueError, 'Fractional'):
            renderer.checked_spec(self.value, self.state)


@unittest.skipUnless(os.name == 'nt', 'Mandatory immutable source handle is Windows-only')
class RealCandidateRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from creator_workspace import runtime_path
        tools = runtime_path('ffmpeg', ROOT) / 'bin'
        cls.ffmpeg, cls.ffprobe = tools / 'ffmpeg.exe', tools / 'ffprobe.exe'
        if not cls.ffmpeg.is_file() or not cls.ffprobe.is_file():
            raise unittest.SkipTest('Managed FFmpeg unavailable; render not_run')

    def setUp(self):
        test_root = ROOT / 'extension/.runtime/gameplay-skill-tests'
        test_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='fixture-', dir=test_root)
        self.addCleanup(self.temp.cleanup)
        self.scratch = Path(self.temp.name).resolve()
        self.source = self.scratch / 'original.mkv'
        renderer.run([self.ffmpeg, '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
                      'testsrc2=size=160x90:rate=60:duration=20', '-f', 'lavfi', '-i',
                      'sine=frequency=440:sample_rate=48000:duration=20', '-ac', '2',
                      '-c:v', 'ffv1', '-c:a', 'pcm_s16le', '-n', self.source], self.scratch)
        self.value = candidate()
        self.value['source_manifest'].update(path=str(self.source), byte_size=self.source.stat().st_size,
            content_sha256='sha256:' + hashlib.sha256(self.source.read_bytes()).hexdigest(),
            video={'width': 160, 'height': 90})
        # Non-integer seconds exercise accurate seek, rather than only 5.0s.
        self.value['sequence']['video_clips'][1].update(source_in=301, source_out=421)
        self.value['editorial_evidence']['events'][1]['source_out'] = 421
        self.value['editorial_evidence']['microbeats'][1]['source_out'] = 421
        self.state = synthetic_state(self.value)
        self.output = self.scratch / 'candidate.mp4'

    def render(self):
        return renderer.render(self.value, self.state, work=self.scratch, output=self.output,
                               ffmpeg=self.ffmpeg, ffprobe=self.ffprobe)

    def test_render_source_binding_pixels_audio_and_no_approval(self):
        import array
        before = deepcopy(self.value)
        digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        result = self.render()
        self.assertEqual(result['frames'], 240)
        self.assertEqual(result['technical_status'], 'passed')
        for key in ('semantic_status', 'direct_listening', 'user_approval'):
            self.assertEqual(result[key], 'not_run')
        self.assertEqual(self.value, before)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), digest)
        self.assertEqual(hashlib.sha256(self.output.read_bytes()).hexdigest(), result['video_sha256'][7:])
        self.assertEqual({p.name for p in self.scratch.iterdir()}, {'original.mkv', 'candidate.mp4'})
        # Pixel content at both sides of the source jump, allowing H.264 loss.
        def image(path, frame):
            return renderer.run([self.ffmpeg, '-nostdin', '-v', 'error', '-i', path, '-vf',
                f'select=eq(n\\,{frame})', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'], self.scratch)
        for actual_frame, source_frame in ((0, 0), (120, 301), (239, 420)):
            actual, expected = image(self.output, actual_frame), image(self.source, source_frame)
            self.assertEqual(len(actual), len(expected))
            self.assertLess(sum(abs(a-b) for a,b in zip(actual, expected))/len(expected), 6)
        # Independent audio plan includes the two-frame J-cut at source frame298.
        expected_bytes = renderer.run([self.ffmpeg, '-nostdin', '-v', 'error', '-i', self.source,
            '-filter_complex', '[0:a]atrim=start_sample=0:end_sample=94400,asetpts=PTS-STARTPTS[a];'
            '[0:a]atrim=start_sample=238400:end_sample=336000,asetpts=PTS-STARTPTS[b];'
            '[a][b]concat=n=2:v=0:a=1[out]', '-map', '[out]', '-f', 'f32le', 'pipe:1'], self.scratch)
        actual_bytes = renderer.run([self.ffmpeg, '-nostdin', '-v', 'error', '-i', self.output,
                                    '-map', '0:a:0', '-f', 'f32le', 'pipe:1'], self.scratch)
        expected, actual = array.array('f'), array.array('f')
        expected.frombytes(expected_bytes); actual.frombytes(actual_bytes)
        self.assertLess(abs(len(actual)-len(expected)), 2048)
        x, y = expected[2000:-2000:10], actual[2000:len(expected)-2000:10]
        correlation = sum(a*b for a,b in zip(x,y)) / (sum(a*a for a in x)*sum(b*b for b in y))**0.5
        self.assertGreater(correlation, 0.99)

    def test_existing_output_is_not_replaced(self):
        self.output.write_bytes(b'previous result')
        with self.assertRaisesRegex(ValueError, 'non-colliding'):
            self.render()
        self.assertEqual(self.output.read_bytes(), b'previous result')

    def test_source_drift_does_not_publish(self):
        with self.source.open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'hash/size mismatch'):
            self.render()
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
