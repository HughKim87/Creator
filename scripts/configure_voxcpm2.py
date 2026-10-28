"""Connect an existing VoxCPM2 installation; never install or download anything."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extension/src'))
from creator_workspace import Lease, atomic_json, runtime_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    args = parser.parse_args()
    python, model = args.python.resolve(), args.model.resolve()
    if not python.is_file():
        parser.error('Python executable not found')
    for name in ('config.json', 'model.safetensors', 'audiovae.pth', 'tokenizer.json'):
        if not (model / name).is_file():
            parser.error('Missing VoxCPM2 model file: ' + name)
    if json.loads((model / 'config.json').read_text(encoding='utf-8')).get('architecture') != 'voxcpm2':
        parser.error('The selected model is not VoxCPM2')
    # Only read distribution metadata from the supplied interpreter.
    version = subprocess.check_output([str(python), '-B', '-c',
        'import importlib.metadata; print(importlib.metadata.version("voxcpm"))'],
        text=True, encoding='utf-8', timeout=30).strip()
    if version != '2.0.3':
        parser.error('This adapter targets voxcpm==2.0.3; found ' + version)
    runtime = runtime_path('voxcpm2', ROOT)
    with Lease('install-voxcpm2', ROOT), Lease('gpu', ROOT):
        runtime.mkdir(parents=True, exist_ok=True)
        atomic_json(runtime / 'installation.json', {
            'schema_version': 'creator-voxcpm2-installation-v1',
            'python': str(python), 'model': str(model), 'voxcpm_version': version})
    print('Connected existing VoxCPM2 installation. No packages or model files changed.')


if __name__ == '__main__':
    main()
