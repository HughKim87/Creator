import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sovits_local import select_sovits_reference, SovitsVoice
from tts_engines import EngineManager


class References(unittest.TestCase):
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


class Workers(unittest.TestCase):
    def test_switch_waits_for_old_process_before_new_start(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
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
