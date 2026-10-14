"""Official public reference only; functional Korean synthesis verification."""
import json
import os
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extension/src'))
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
    NLTK_DATA=str(ROOT / 'extension/.runtime/gpt-sovits/nltk-data'),
    NUMBA_CACHE_DIR=str(ROOT / 'extension/.runtime/gpt-sovits/numba-cache'))
from sovits_local import load_pipeline, RUNTIME
import soundfile as sf
import numpy as np
import torch
started = time.perf_counter()
model = load_pipeline()
load_seconds = time.perf_counter()-started
started = time.perf_counter()
parts = list(model.run({'text':'안녕하세요. 지금 이 컴퓨터에서 한국어 음성을 생성하고 있습니다.',
    'text_lang':'all_ko','prompt_lang':'en',
    'ref_audio_path':str(ROOT / 'extension/.runtime/qwen-tts/verification/official-reference.wav'),
    'prompt_text':'Okay. Yeah. I resent you. I love you. I respect you. But you know what? You blew it! And thanks to you.',
    'text_split_method':'cut5','batch_size':1,'parallel_infer':False,'streaming_mode':False,
    'use_cuda_graph':False,'seed':42}))
sr = parts[0][0]
wave = np.concatenate([p[1] for p in parts])
target = RUNTIME / 'verification'
target.mkdir(exist_ok=True)
sf.write(target / 'korean-smoke.wav', wave, sr)
evidence = {'version':'v5turbo','load_seconds':round(load_seconds,2),
    'generation_seconds':round(time.perf_counter()-started,2),
    'sample_rate':sr,'duration_seconds':round(len(wave)/sr,2),
    'finite':bool(np.isfinite(wave).all()),'peak':float(np.max(np.abs(wave))),
    'gpu_peak_allocated_mib':round(torch.cuda.max_memory_allocated()/1024**2,1),
    'scope':'public English reference to Korean functional test; no user voice similarity claim'}
assert evidence['finite'] and evidence['duration_seconds'] > 0 and evidence['peak'] > 0
(target / 'evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(json.dumps(evidence),flush=True)
