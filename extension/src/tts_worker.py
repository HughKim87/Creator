"""One GPU engine per process. IPC stays in private local runtime files."""
import contextlib
import json
import os
import sys
import time
import traceback
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
engine, ready = sys.argv[1:3]
runtime = ROOT / 'extension/.runtime' / ('qwen-tts' if engine == 'Qwen' else 'gpt-sovits')
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_IMPLICIT_TOKEN='1',
                  HF_HUB_DISABLE_TELEMETRY='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                  NLTK_DATA=str(ROOT / 'extension/.runtime/gpt-sovits/nltk-data'),
                  NUMBA_CACHE_DIR=str(runtime / 'numba-cache'))

def watch_parent():
    import psutil
    parent = psutil.Process(int(os.environ.get('TTS_OWNER_PID', os.getppid())))
    while parent.is_running():
        time.sleep(1)
    os._exit(0)

threading.Thread(target=watch_parent, daemon=True).start()

def publish(path, value):
    path = Path(path)
    temporary = path.with_suffix('.pending')
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)

try:
    if engine == 'Qwen':
        import qwen_tts_local as backend
        model = backend.load_model()
    else:
        import sovits_local as backend
        model = backend.load_pipeline()
        voices = backend.SovitsVoice()
    publish(ready, {'ok': True, 'pid': os.getpid()})
except Exception as exc:
    traceback.print_exc()
    publish(ready, {'ok': False, 'error': f'{type(exc).__name__}: {exc}'})
    sys.exit(1)

import numpy as np
import soundfile as sf
for line in sys.stdin:
    job = json.loads(line)
    started = time.perf_counter()
    try:
        # Upstream prints scripts during synthesis; avoid retaining them in logs.
        with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            if engine == 'Qwen':
                if job['action'] == 'register':
                    _, notice, hit, seconds = backend.register_voice(model, job.get('reference'), job.get('transcript'))
                    result = {'notice': notice, 'cache': hit, 'preparation_seconds': seconds}
                else:
                    sr, wave = backend.clone(model, job.get('reference'), job.get('transcript'), job['script'])
                    sf.write(job['audio'], wave, sr)
                    result = dict(backend.LAST_METRICS, audio=job['audio'])
            else:
                record, notice = voices.register(job.get('reference'), job.get('transcript'))
                path = str(voices.directory / record['audio'])
                preparation = time.perf_counter() - started
                if job['action'] == 'register':
                    model.set_ref_audio(path)
                    result = {'notice': notice, 'preparation_seconds': time.perf_counter()-started}
                else:
                    generated = time.perf_counter()
                    pieces = list(model.run({'text': job['script'], 'text_lang': 'all_ko',
                        'ref_audio_path': path, 'prompt_text': record['text'], 'prompt_lang': 'all_ko',
                        'text_split_method': 'cut5', 'batch_size': 1, 'parallel_infer': False,
                        'streaming_mode': False, 'seed': 42, 'use_cuda_graph': False}))
                    if not pieces:
                        raise ValueError('음성이 생성되지 않았습니다.')
                    sr = pieces[0][0]
                    wave = np.concatenate([p[1] for p in pieces])
                    if not wave.size or not np.isfinite(wave).all():
                        raise ValueError('유효한 음성이 생성되지 않았습니다.')
                    sf.write(job['audio'], wave, sr)
                    result = {'audio': job['audio'], 'notice': notice, 'preparation_seconds': preparation,
                              'generation_seconds': time.perf_counter()-generated}
        publish(job['response'], {'ok': True, **result})
    except Exception as exc:
        publish(job['response'], {'ok': False, 'error': f'{type(exc).__name__}: {exc}'})
