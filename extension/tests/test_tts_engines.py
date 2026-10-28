import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sovits_local import select_sovits_reference, SovitsVoice
from tts_engines import EngineManager
import sovits_local


def prepare_catalog(root):
    import shutil
    target = root / 'extension/config/workspace-runtime.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).resolve().parents[1] / 'config/workspace-runtime.json', target)


class References(unittest.TestCase):
    def test_first_pipeline_load_creates_config_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'new-job/work/tts/gpt-sovits'
            config = Mock()
            def initialize(config):
                path = Path(config.configs_path)
                self.assertEqual(path, state / 'tts-infer.yaml')
                path.write_text('custom: {}', encoding='utf-8')
                return 'pipeline'
            jieba = Mock()
            modules = {'jieba': jieba, 'jieba.posseg': jieba.posseg,
                       'g2pk2': Mock(), 'mecab': Mock(), 'tools': Mock(),
                       'TTS_infer_pack': Mock(),
                       'TTS_infer_pack.TTS': Mock(TTS=Mock(side_effect=initialize),
                                                 TTS_Config=Mock(return_value=config))}
            with patch.object(sovits_local, 'STATE', state), patch.object(sovits_local, 'configure_language_detector') as detector, patch.dict(sys.modules, modules), patch('os.chdir'), patch('shutil.which', return_value='tool.exe'), patch.object(sys, 'path', list(sys.path)):
                self.assertEqual(sovits_local.load_pipeline(), 'pipeline')
                detector.assert_called_once()
            self.assertTrue((state / 'tts-infer.yaml').is_file())

    def test_long_srt_uses_matching_complete_words(self):
        srt = '1\n00:00:00,000 --> 00:00:02,840\n첫 문장\n\n2\n00:00:02,840 --> 00:00:06,440\n둘째 문장'
        self.assertEqual(select_sovits_reference(100, srt), (0, 6.44, '첫 문장 둘째 문장'))

    def test_plain_long_recording_cannot_be_blindly_trimmed(self):
        with self.assertRaises(ValueError):
            select_sovits_reference(30, '어떤 구간인지 알 수 없는 전사')

    def test_out_of_range_srt_rejected(self):
        with self.assertRaises(ValueError):
            select_sovits_reference(4, '1\n00:00:00,000 --> 00:00:06,440\n문장')

    def test_voice_reuse_after_restart_does_not_need_source(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / 'voice.wav').write_bytes(b'fixture')
            record = {'audio': 'voice.wav', 'text': '목소리', 'start': 0, 'end': 4}
            (directory / 'active.json').write_text(json.dumps(record), encoding='utf-8')
            self.assertEqual(SovitsVoice(directory).register(None, '')[0], record)


class LanguageDetector(unittest.TestCase):
    def check_local_model(self, have_full):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            package = root / 'site-packages/fast_langdetect'
            bundled = package / 'resources/lid.176.ftz'
            bundled.parent.mkdir(parents=True)
            bundled.write_bytes(b'bundled-fixture')
            full = root / 'repo/GPT_SoVITS/pretrained_models/fast_langdetect/lid.176.bin'
            if have_full:
                full.parent.mkdir(parents=True)
                full.write_bytes(b'full-fixture')
            library = Mock(__file__=str(package / '__init__.py'))
            upstream_detector = Mock()
            def upstream_import(name):
                self.assertEqual(name, 'text.LangSegmenter')
                library.infer._default_detector = upstream_detector
            with patch.dict(sys.modules, {'fast_langdetect': library}), patch('importlib.import_module', side_effect=upstream_import):
                detector = sovits_local.configure_language_detector(root / 'repo')
            library.LangDetectConfig.assert_called_once_with(custom_model_path=str(full if have_full else bundled))
            self.assertIs(library.infer._default_detector, detector)
            self.assertIsNot(detector, upstream_detector)

    def test_absent_cache_uses_bundled_model_without_downloading(self):
        self.check_local_model(False)

    def test_existing_full_model_is_preserved_and_reused(self):
        self.check_local_model(True)

    def test_missing_both_local_models_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            library = Mock(__file__=str(root / '__init__.py'))
            with patch.dict(sys.modules, {'fast_langdetect': library}), patch('importlib.import_module'):
                with self.assertRaisesRegex(ValueError, '언어 감지 모델'):
                    sovits_local.configure_language_detector(root / 'repo')
            library.LangDetector.assert_not_called()


class Workers(unittest.TestCase):
    def test_switch_waits_for_old_process_before_new_start(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            prepare_catalog(root)
            python = root / 'extension/.runtime/gpt-sovits/venv/Scripts/python.exe'
            python.parent.mkdir(parents=True)
            python.touch()
            manager = EngineManager(root)
            old = Mock()
            old.pid = 1234
            old.poll.return_value = None
            child = Mock()
            manager.process, manager.engine = old, 'Qwen'
            def launch(*args, **kwargs):
                old.terminate.assert_called_once()
                old.wait.assert_called_once()
                child.terminate.assert_called_once()
                return Mock()
            with patch('tts_engines.psutil.Process') as process_info, patch('tts_engines.psutil.wait_procs', return_value=([], [])), patch('tts_engines.subprocess.Popen', side_effect=launch), patch.object(manager, '_wait', return_value={'ok': True}):
                process_info.return_value.children.return_value = [child]
                manager._start('GPT-SoVITS')
            self.assertEqual(manager.engine, 'GPT-SoVITS')
            manager.stop()

    def test_cancel_terminates_worker_and_preserves_voice_data(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = EngineManager(folder)
            manager.process = Mock()
            manager.process.poll.return_value = None
            worker = manager.process
            manager.cancel()
            worker.terminate.assert_called_once()
            self.assertTrue(manager.cancelled.is_set())
            self.assertIsNone(manager.process)

    def test_timeout_terminates_owned_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = EngineManager(folder)
            worker = Mock()
            worker.poll.return_value = None
            manager.process = worker
            with self.assertRaisesRegex(ValueError, '3분'):
                manager._wait(Path(folder) / 'absent.json', -1)
            worker.terminate.assert_called_once()


if __name__ == '__main__':
    unittest.main()
