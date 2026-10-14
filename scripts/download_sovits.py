"""Download only official GPT-SoVITS inference weights; no user audio upload."""
import json
import os
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'extension/.runtime/gpt-sovits'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['HF_HOME'] = str(RUNTIME / 'hf-cache')
api = HfApi(token=False)
repo = 'lj1995/GPT-SoVITS'
revision = '8f8857563c040d542de108a2c18b0425abd6c9c5'
files = api.list_repo_files(repo, revision=revision)
selected = [p for p in files if p in {
    's1v3.ckpt', 'gsv-v5-pretrained/s2Gv5turbo.pth', 'gsv-v5-pretrained/vocoder.pth',
} or (p.startswith(('chinese-hubert-base/', 'chinese-roberta-wwm-ext-large/'))
      and Path(p).name in {'config.json', 'pytorch_model.bin', 'model.safetensors',
                          'preprocessor_config.json', 'tokenizer_config.json',
                          'tokenizer.json', 'vocab.txt', 'special_tokens_map.json'})]
print(json.dumps({'revision': revision, 'files': selected}), flush=True)
for name in selected:
    print('Downloading ' + name, flush=True)
    hf_hub_download(repo, name, revision=revision, token=False,
                    local_dir=RUNTIME / 'repo/GPT_SoVITS/pretrained_models')
(RUNTIME / 'model-revision.json').write_text(json.dumps({'repo': repo, 'revision': revision, 'files': selected}, indent=2), encoding='utf-8')
