from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from fractions import Fraction

from video_editing.review_proxy import (
    ReviewProxyError, render_fixture_proxy, render_spec, toolchain,
    verify_fixture_binding, _check_timestamps,
)
from video_editing.timeline_v2 import TimelineV2Error


ROOT = Path(__file__).resolve().parents[2]


def candidate() -> dict:
    value = json.loads((ROOT / "extension/examples/video-edit-timeline-v2.json").read_text("utf-8"))
    value["validation"] = {
        "reviewed_editorial_fingerprint": None, "reviewer": None,
        "semantic_status": "not_run",
        "passes": {name: dict(status="not_run", method=None, reviewer=None, checked_at=None, evidence=None)
                   for name in ("causal_space", "tempo_repetition", "av_boundary")},
    }
    # A two-frame J-cut: source audio begins before the second video shot.
    audio = value["sequence"]["audio_clips"][1]
    audio.update(source_in=298, frames=122, timeline_start=118, gap_before=0)
    value["editorial_evidence"]["events"][1]["source_in"] = 298
    value["editorial_evidence"]["microbeats"][1]["source_in"] = 298
    for beat in value["editorial_evidence"]["microbeats"]:
        beat["boundary_review"] = "pending"
    return value


class RenderSpecTests(unittest.TestCase):
    def test_unreviewed_candidate_and_independent_audio_are_supported(self):
        value = candidate()
        before = deepcopy(value)
        spec = render_spec(value)
        self.assertEqual(spec["frames"], 240)
        self.assertEqual(spec["samples"], 192000)
        self.assertIn("trim=start_frame=300:end_frame=420", spec["graph"])
        self.assertIn("atrim=start_sample=238400:end_sample=336000", spec["graph"])
        self.assertNotIn("apad", spec["graph"])
        self.assertEqual(value, before)

    def test_audio_hole_cannot_be_replaced_with_silence(self):
        value = candidate()
        value["sequence"]["audio_clips"][1].update(source_in=300, frames=120, timeline_start=120, gap_before=2)
        value["editorial_evidence"]["events"][1]["source_in"] = 300
        value["editorial_evidence"]["microbeats"][1]["source_in"] = 300
        with self.assertRaisesRegex(ReviewProxyError, "holes"):
            render_spec(value)

    def test_fractional_sample_boundaries_are_explicitly_unsupported(self):
        value = candidate()
        value["source_manifest"]["audio"]["sample_rate"] = 44101
        with self.assertRaisesRegex(ReviewProxyError, "fractional"):
            render_spec(value)

    def test_unknown_effect_is_not_silently_dropped(self):
        value = candidate()
        value["sequence"]["video_clips"][0]["speed"] = 2
        with self.assertRaises(TimelineV2Error):
            render_spec(value)

    def test_source_bounds_fail_before_render(self):
        value = candidate()
        value["source_manifest"]["total_frames"] = 400
        with self.assertRaises(TimelineV2Error):
            render_spec(value)

    def test_declared_cfr_does_not_hide_discontinuous_timestamps(self):
        observed = {"video": {"time_base": "1/1000"}, "audio": {"time_base": "1/48000", "sample_rate": "48000"}}
        payload = {"frames": [{"best_effort_timestamp_time": "0"}, {"best_effort_timestamp_time": "0.05"}]}
        with patch("video_editing.review_proxy._run", return_value=json.dumps(payload).encode()):
            with self.assertRaisesRegex(ReviewProxyError, "cadence"):
                _check_timestamps(Path("unused"), Path("unused"), ROOT, observed, Fraction(60))


@unittest.skipUnless(os.name == "nt", "mandatory source lock requires Windows")
class RealFfmpegFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        expected = ROOT / "extension/.runtime/ffmpeg/ffmpeg-8.1.2-essentials_build/bin/ffmpeg.exe"
        if not expected.is_file():
            raise unittest.SkipTest("managed FFmpeg absent; real rendering not_run")
        cls.binaries = toolchain(ROOT)
        cls.data_root = ROOT / "extension/data"
        cls.data_root.mkdir(exist_ok=True)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="proxy-test-", dir=self.data_root)
        self.addCleanup(self.temporary.cleanup)
        self.scratch = Path(self.temporary.name).resolve()
        self.source = self.scratch / "source.mkv"
        result = subprocess.run([
            str(self.binaries["ffmpeg"]), "-nostdin", "-v", "error", "-xerror",
            "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=60:duration=20",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=20",
            "-ac", "2", "-c:v", "ffv1", "-c:a", "pcm_s16le", "-n", str(self.source),
        ], cwd=self.scratch, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.value = candidate()
        self.value["source_manifest"].update(
            path=str(self.source), content_sha256="sha256:" + hashlib.sha256(self.source.read_bytes()).hexdigest(),
            byte_size=self.source.stat().st_size, video={"width": 160, "height": 90},
        )
        self.target = self.scratch / "review.mkv"
        self.cached_tools = patch("video_editing.review_proxy.toolchain", return_value=self.binaries)
        self.cached_tools.start()
        self.addCleanup(self.cached_tools.stop)

    def render(self):
        return render_fixture_proxy(self.value, consumer_root=ROOT, scratch_root=self.scratch, output_path=self.target)

    def test_real_short_proxy_and_binding_never_grant_approval(self):
        before = deepcopy(self.value)
        evidence = self.render()
        self.assertEqual(evidence["frames"], 240)  # source is 1200 frames
        self.assertEqual(evidence["audio_samples"], 192000)
        self.assertEqual(evidence["semantic_status"], "not_run")
        checked = verify_fixture_binding(self.value, evidence, scratch_root=self.scratch)
        self.assertEqual(checked, dict(binding_status="passed", semantic_status="not_run", app_status="not_run", user_status="not_run"))
        self.assertEqual(before, self.value)
        self.assertEqual({p.name for p in self.scratch.iterdir()}, {"source.mkv", "review.mkv"})

    def test_rendered_pixels_and_audio_equal_independent_source_ranges(self):
        self.render()
        def decode(media, options):
            result = subprocess.run([
                str(self.binaries["ffmpeg"]), "-nostdin", "-v", "error", "-i", str(media), *options, "pipe:1",
            ], capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
            return result.stdout
        raw_video = decode(self.source, ["-map", "0:v:0", "-pix_fmt", "yuv420p", "-f", "rawvideo"])
        proxy_video = decode(self.target, ["-map", "0:v:0", "-pix_fmt", "yuv420p", "-f", "rawvideo"])
        frame_bytes = 160 * 90 * 3 // 2
        expected_video = raw_video[:120 * frame_bytes] + raw_video[300 * frame_bytes:420 * frame_bytes]
        self.assertEqual(proxy_video, expected_video)
        raw_audio = decode(self.source, ["-map", "0:a:0", "-c:a", "pcm_s16le", "-f", "s16le"])
        proxy_audio = decode(self.target, ["-map", "0:a:0", "-c:a", "pcm_s16le", "-f", "s16le"])
        bytes_per_frame = 800 * 2 * 2
        expected_audio = raw_audio[:118 * bytes_per_frame] + raw_audio[298 * bytes_per_frame:420 * bytes_per_frame]
        self.assertEqual(proxy_audio, expected_audio)

    def test_wrong_declared_source_hash_leaves_no_render(self):
        self.value["source_manifest"]["content_sha256"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ReviewProxyError, "source bytes"):
            self.render()
        self.assertEqual([p.name for p in self.scratch.iterdir()], ["source.mkv"])

    def test_protected_source_is_rejected_without_reading_it(self):
        self.value["source_manifest"]["path"] = str(ROOT / "inputs/never-open-this.mkv")
        with self.assertRaisesRegex(ReviewProxyError, "protected"):
            self.render()
        self.assertFalse(self.target.exists())

    def test_existing_output_preserved(self):
        self.target.write_bytes(b"existing result")
        with self.assertRaisesRegex(ReviewProxyError, "new non-colliding"):
            self.render()
        self.assertEqual(self.target.read_bytes(), b"existing result")

    def test_changed_proxy_and_editorial_identity_are_rejected(self):
        evidence = self.render()
        changed = deepcopy(self.value)
        changed["sequence"]["video_clips"][0]["edit_reason"] = "changed editorial reasoning"
        with self.assertRaisesRegex(ReviewProxyError, "stale"):
            verify_fixture_binding(changed, evidence, scratch_root=self.scratch)
        with self.target.open("ab") as handle:
            handle.write(b"drift")
        with self.assertRaisesRegex(ReviewProxyError, "bytes changed"):
            verify_fixture_binding(self.value, evidence, scratch_root=self.scratch)

    def test_technical_record_cannot_claim_semantic_approval(self):
        evidence = self.render()
        evidence["semantic_status"] = "passed"
        with self.assertRaisesRegex(ReviewProxyError, "overstated"):
            verify_fixture_binding(self.value, evidence, scratch_root=self.scratch)

    def test_current_source_bytes_are_rechecked_during_binding(self):
        evidence = self.render()
        with self.source.open("ab") as handle:
            handle.write(b"changed source")
        with self.assertRaisesRegex(ReviewProxyError, "source bytes changed"):
            verify_fixture_binding(self.value, evidence, scratch_root=self.scratch)

    def test_output_outside_scratch_is_rejected(self):
        with self.assertRaisesRegex(ReviewProxyError, "inside the exact scratch"):
            render_fixture_proxy(self.value, consumer_root=ROOT, scratch_root=self.scratch,
                                 output_path=ROOT / "extension/work/never-created.mkv")

    def test_failed_render_cleans_only_its_temporary_files(self):
        from video_editing import review_proxy
        real_run = review_proxy._run
        def failing_run(args, **kwargs):
            if "-filter_complex" in args:
                raise ReviewProxyError("injected encoder failure")
            return real_run(args, **kwargs)
        with patch("video_editing.review_proxy._run", side_effect=failing_run):
            with self.assertRaisesRegex(ReviewProxyError, "injected"):
                self.render()
        self.assertEqual({p.name for p in self.scratch.iterdir()}, {"source.mkv"})

    def test_atomic_publication_does_not_clobber_concurrent_output(self):
        from video_editing import review_proxy
        real_link = os.link
        def race(source, target):
            Path(target).write_bytes(b"concurrent output")
            return real_link(source, target)
        with patch.object(review_proxy.os, "link", side_effect=race):
            with self.assertRaises(FileExistsError):
                self.render()
        self.assertEqual(self.target.read_bytes(), b"concurrent output")
        self.assertEqual({p.name for p in self.scratch.iterdir()}, {"source.mkv", "review.mkv"})


if __name__ == "__main__":
    unittest.main()
