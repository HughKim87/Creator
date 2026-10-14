$ErrorActionPreference = 'Stop'
$qwenRoot = Split-Path -Parent $PSScriptRoot
$qwenRuntime = Join-Path $qwenRoot 'extension\.runtime\qwen-tts'
$qwenPython = Join-Path $qwenRuntime 'venv\Scripts\python.exe'
$env:UV_CACHE_DIR = Join-Path $qwenRuntime 'uv-cache'
$env:HF_HOME = Join-Path $qwenRuntime 'hf-cache'
$env:HF_HUB_DISABLE_IMPLICIT_TOKEN = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:GRADIO_ANALYTICS_ENABLED = 'False'
$env:PYTHONDONTWRITEBYTECODE = '1'
New-Item -ItemType Directory -Path $qwenRuntime -Force | Out-Null
if (-not (Test-Path -LiteralPath $qwenPython)) {
    uv venv --python (Get-Command python).Source --no-managed-python (Join-Path $qwenRuntime 'venv')
    if ($LASTEXITCODE -ne 0) { throw 'venv creation failed' }
}
uv pip install --python $qwenPython --index-url https://download.pytorch.org/whl/cu128 'torch==2.8.0' 'torchaudio==2.8.0'
if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed' }
uv pip install --python $qwenPython 'qwen-tts==0.1.1' 'gradio==6.13.0'
if ($LASTEXITCODE -ne 0) { throw 'Qwen installation failed' }
& $qwenPython -B (Join-Path $PSScriptRoot 'download_qwen_tts.py')
if ($LASTEXITCODE -ne 0) { throw 'Model download failed' }
