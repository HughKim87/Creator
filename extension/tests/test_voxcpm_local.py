import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, create_autospec

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import voxcpm_local as backend
from tts_engines import EngineManager
from test_tts_engines import prepare_catalog


class VoxCPMReferences(unittest.TestCase):
    def test_optional_transcript_and_short_clip(self):
        self.assertEqual(backend.select_voxcpm_reference(12, ''), (0, 12, ''))
        self.assertEqual(backend.select_voxcpm_reference(12, '실제 발화문'), (0, 12, '실제 발화문'))

    def test_long_audio_requires_matching_srt(self):
        with self.assertRaises(ValueError):
            backend.select_voxcpm_reference(31, '전체 녹음 발화문')
        srt = '1\n00:00:02,000 --> 00:00:06,000\n첫 문장\n\n2\n00:00:07,000 --> 00:00:12,000\n다음 문장'
        self.assertEqual(backend.select_voxcpm_reference(100, srt), (2, 6, '첫 문장'))

    def test_invalid_durations_and_mismatched_srt_rejected(self):
        for duration in (0, 2, float('nan'), float('inf')):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                backend.select_voxcpm_reference(duration, '')
        with self.assertRaises(ValueError):
            backend.select_voxcpm_reference(4, '1\n00:00:00,000 --> 00:00:12,000\n문장')

    def test_registration_persists_a_16khz_copy_and_survives_source_removal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.wav'
            source.write_bytes(b'fixture')
            voices = backend.VoxCPMVoice(root / 'voices')
            def run(command, **kwargs):
                if command[0] == 'ffprobe':
                    return Mock(stdout=b'{"format":{"duration":"5"}}')
                self.assertEqual(command[command.index('-ar')+1], '16000')
                Path(command[-1]).write_bytes(b'converted-fixture')
            with patch.object(backend.subprocess, 'run', side_effect=run):
                record, _ = voices.register(source, '문장')
            source.unlink()
            self.assertEqual(backend.VoxCPMVoice(voices.directory).register(None, '')[0], record)
            self.assertTrue((voices.directory / record['audio']).is_file())

    def test_failed_conversion_keeps_existing_voice(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.wav'
            source.write_bytes(b'fixture')
            voices = backend.VoxCPMVoice(root / 'voices')
            active = voices.directory / 'active.json'
            active.write_text('{"previous": true}')
            with patch.object(backend.subprocess, 'run', side_effect=[
                    Mock(stdout=b'{"format":{"duration":"5"}}'), RuntimeError('decode failed')]):
                with self.assertRaises(RuntimeError):
                    voices.register(source, '')
            self.assertEqual(active.read_text(), '{"previous": true}')

    def test_model_call_keeps_reference_and_transcript_paired(self):
        model = Mock()
        model.tts_model.sample_rate = 48000
        # Installed 2.0.3 has no seed keyword (newer upstream main does).
        def generate(*, text, reference_wav_path, cfg_value, inference_timesteps,
                     normalize, denoise, retry_badcase, max_len,
                     prompt_wav_path=None, prompt_text=None):
            pass
        model.generate = create_autospec(generate, return_value=[0, .1, -.1])
        voices = Mock(directory=Path('voices'))
        with patch.object(backend, 'ensure_context_capacity'):
            sr, _ = backend.synthesize(model, voices, {'audio': 'ref.wav', 'text': '참고 문장'}, '새 문장')
        self.assertEqual(sr, 48000)
        options = model.generate.call_args.kwargs
        self.assertEqual(options['prompt_wav_path'], options['reference_wav_path'])
        self.assertEqual(options['prompt_text'], '참고 문장')
        self.assertFalse(options['normalize'])
        self.assertFalse(options['denoise'])
        self.assertFalse(options['retry_badcase'])
        with patch.object(backend, 'ensure_context_capacity'):
            backend.synthesize(model, voices, {'audio': 'ref.wav', 'text': ''}, '새 문장')
        self.assertNotIn('prompt_text', model.generate.call_args.kwargs)
        model.generate.return_value = [float('nan')]
        with patch.object(backend, 'ensure_context_capacity'), self.assertRaises(ValueError):
            backend.synthesize(model, voices, {'audio': 'ref.wav', 'text': ''}, '새 문장')

    def test_687_token_prefill_expands_both_512_caches_with_generation_room(self):
        from types import SimpleNamespace
        def language_model():
            cache = SimpleNamespace(max_length=512)
            def setup(batch, capacity, device, dtype):
                cache.max_length = capacity
            return SimpleNamespace(kv_cache=cache, setup_cache=Mock(side_effect=setup),
                                   parameters=lambda: iter([SimpleNamespace(dtype='bf16')]))
        pipeline = SimpleNamespace(text_tokenizer=lambda text: list(text),
            audio_vae=SimpleNamespace(sample_rate=16000), patch_size=4, chunk_size=640,
            device='cuda', base_lm=language_model(), residual_lm=language_model())
        model = SimpleNamespace(tts_model=pipeline)
        with patch('soundfile.info', return_value=SimpleNamespace(frames=480000, samplerate=16000)):
            prefix, required = backend.ensure_context_capacity(model, 'ref.wav', '가'*200, '나'*108)
            self.assertEqual(prefix, 687)
            self.assertGreater(required, prefix)
            for lm in (pipeline.base_lm, pipeline.residual_lm):
                lm.setup_cache.assert_called_once_with(1, 2048, 'cuda', 'bf16')
            backend.ensure_context_capacity(model, 'ref.wav', '가'*200, '나'*108)
            self.assertEqual(pipeline.base_lm.setup_cache.call_count, 1)
            with self.assertRaisesRegex(ValueError, '처리 범위'):
                backend.ensure_context_capacity(model, 'ref.wav', '가'*9000, '나')


class VoxCPMInstallation(unittest.TestCase):
    def test_external_installation_is_used_for_worker_with_local_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'creator'
            prepare_catalog(root)
            runtime = backend.runtime_path('voxcpm2', root)
            runtime.mkdir(parents=True)
            external = Path(folder) / 'external'
            external.mkdir()
            python, model = external / 'python.exe', external / 'model'
            python.touch()
            model.mkdir()
            (model / 'config.json').write_text('{"architecture":"voxcpm2"}')
            (runtime / 'installation.json').write_text(json.dumps({
                'schema_version': 'creator-voxcpm2-installation-v1',
                'python': str(python), 'model': str(model)}))
            self.assertEqual(backend.configured_paths(root), (python, model))
            manager = EngineManager(root)
            with patch('tts_engines.subprocess.Popen') as launch, patch.object(manager, '_wait') as wait:
                manager._start('VoxCPM2')
                self.assertEqual(wait.call_args.args[1], 600)
                command = launch.call_args.args[0]
                self.assertEqual(command[0], str(python))
                self.assertEqual(command[-2], 'VoxCPM2')
                environment = launch.call_args.kwargs['env']
                self.assertEqual(environment['HF_HUB_OFFLINE'], '1')
                self.assertEqual(environment['HF_HOME'], str(runtime / 'hf-cache'))
            manager.stop()
            python.unlink()
            with self.assertRaisesRegex(ValueError, 'Python'):
                backend.configured_paths(root)

    def test_missing_connection_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            prepare_catalog(root)
            with self.assertRaisesRegex(ValueError, '연결 설정'):
                backend.configured_paths(root)

    def test_pipeline_is_local_cuda_and_has_no_denoiser_or_compilation(self):
        with tempfile.TemporaryDirectory() as folder:
            model = Path(folder)
            (model / 'config.json').write_text('{"architecture":"voxcpm2"}')
            torch, voxcpm = Mock(), Mock()
            with patch.object(backend, 'configured_paths', return_value=(Path('python'), model)), patch.dict(sys.modules, {'torch': torch, 'voxcpm': voxcpm}):
                backend.load_pipeline()
                voxcpm.VoxCPM.from_pretrained.assert_called_once_with(str(model), local_files_only=True,
                    load_denoiser=False, optimize=False, device='cuda')


if __name__ == '__main__':
    unittest.main()
