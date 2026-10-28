import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from video_scene_cache import render_cached_scene


class SceneCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = self.root / 'extension/jobs/example/work/cache'
        self.media = self.root / 'image.png'
        self.overlay = self.root / 'overlay.png'
        self.renderer = self.root / 'renderer.py'
        for p in (self.media, self.overlay, self.renderer):
            p.write_bytes(b'original')
        self.calls = 0

    def run_scene(self, scene='one', settings=None, render=None, validate=None):
        def default_render(path):
            self.calls += 1
            path.write_bytes(b'rendered-fixture')
        def default_validate(path):
            self.assertEqual(path.read_bytes(), b'rendered-fixture')
        return render_cached_scene(self.root, self.cache, scene,
            inputs={'image': self.media, 'overlay': self.overlay},
            settings=settings or {'frames': 60, 'effect': 'none'},
            renderer_inputs={'renderer': self.renderer},
            render=render or default_render, validate=validate or default_validate)

    def test_same_inputs_reuse_but_changed_scene_does_not_replace_other(self):
        first, reused = self.run_scene()
        self.assertFalse(reused)
        self.assertTrue(self.run_scene()[1])
        other, _ = self.run_scene('two')
        old = other.read_bytes()
        changed, reused = self.run_scene(settings={'frames': 60, 'effect': 'pop'})
        self.assertFalse(reused)
        self.assertNotEqual(first, changed)
        self.assertEqual(other.read_bytes(), old)
        self.assertEqual(self.calls, 3)

    def test_media_overlay_and_renderer_changes_invalidate(self):
        before, _ = self.run_scene()
        for path in (self.media, self.overlay, self.renderer):
            path.write_bytes(b'changed')
            after, reused = self.run_scene()
            self.assertFalse(reused)
            self.assertNotEqual(before, after)
            before = after

    def test_corrupt_cache_rejected(self):
        target, _ = self.run_scene()
        target.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'Damaged'):
            self.run_scene()

    def test_missing_input_rejected_before_render(self):
        self.overlay.unlink()
        with self.assertRaises(FileNotFoundError):
            self.run_scene()
        self.assertEqual(self.calls, 0)

    def test_input_drift_during_render_does_not_publish(self):
        def render(path):
            path.write_bytes(b'rendered-fixture')
            self.media.write_bytes(b'changed during render')
        with self.assertRaisesRegex(ValueError, 'changed during'):
            self.run_scene(render=render)
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_validation_failure_does_not_publish(self):
        def validate(path):
            raise ValueError('bad frame count')
        with self.assertRaisesRegex(ValueError, 'frame count'):
            self.run_scene(validate=validate)
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_outside_job_rejected(self):
        self.cache = self.root / 'core/cache'
        with self.assertRaisesRegex(ValueError, 'inside a Consumer job'):
            self.run_scene()
        self.assertFalse(self.cache.exists())


if __name__ == '__main__':
    unittest.main()
