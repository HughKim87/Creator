"""Identify the local TTS source loaded by a running UI."""
import hashlib
from pathlib import Path


def source_version():
    directory = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for name in ('tts_build.py', 'qwen_tts_local.py', 'tts_engines.py',
                 'tts_worker.py', 'tts_text.py', 'voxcpm_local.py', 'sovits_local.py'):
        digest.update(name.encode('utf-8'))
        digest.update((directory / name).read_bytes().replace(b'\r\n', b'\n'))
    return 'tts-source-' + digest.hexdigest()[:16]


def is_current(config):
    return any(component.get('props', {}).get('elem_id') == 'tts-source-version'
               and component.get('props', {}).get('value') == source_version()
               for component in config.get('components', []))
