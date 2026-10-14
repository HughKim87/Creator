import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import torch
from qwen_voice_cache import VoicePromptCache, VoiceClonePromptItem


class VoiceCacheTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / ".runtime/qwen-tts/verification"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.root = Path(self.temporary.name)
        self.reference = self.root / "sample.wav"
        self.reference.write_bytes(b"voice one")
        self.directory = self.root / "voice-cache"
        self.calls = 0

    def tearDown(self):
        self.temporary.cleanup()

    def build(self):
        self.calls += 1
        item = VoiceClonePromptItem(torch.tensor([[1, 2], [3, 4]]),
                                   torch.tensor([0.3, 0.7], dtype=torch.bfloat16),
                                   False, True, "실제 발화문")
        return [item], "참고 구간"

    def test_memory_and_disk_reuse_preserve_features(self):
        cache = VoicePromptCache(self.directory, "model-v1")
        original, _, _ = cache.acquire(self.reference, "입력문", self.build)
        _, _, mode = cache.acquire(self.reference, "입력문", self.build)
        self.assertEqual(mode, "memory")
        loaded, _, mode = VoicePromptCache(self.directory, "model-v1").acquire(None, "", self.build)
        self.assertEqual(mode, "disk")
        self.assertEqual(self.calls, 1)
        self.assertTrue(torch.equal(original[0].ref_code, loaded[0].ref_code))
        self.assertTrue(torch.equal(original[0].ref_spk_embedding, loaded[0].ref_spk_embedding))
        self.assertEqual(loaded[0].ref_text, "실제 발화문")

    def test_changed_transcript_or_audio_requires_new_features(self):
        cache = VoicePromptCache(self.directory, "model-v1")
        cache.acquire(self.reference, "입력문", self.build)
        cache.acquire(self.reference, "바꾼 입력문", self.build)
        self.reference.write_bytes(b"another voice recording")
        cache.acquire(self.reference, "바꾼 입력문", self.build)
        self.assertEqual(self.calls, 3)

    def test_changed_model_cannot_silently_reuse_previous_voice(self):
        VoicePromptCache(self.directory, "model-v1").acquire(self.reference, "입력문", self.build)
        with self.assertRaises(ValueError):
            VoicePromptCache(self.directory, "model-v2").acquire(None, "", self.build)


if __name__ == "__main__":
    unittest.main()
