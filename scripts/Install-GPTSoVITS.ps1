$ErrorActionPreference = 'Stop'
$sovitsRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'Shared-Runtime.ps1')
$taskRuntimeLease = Enter-CreatorRuntimeLease -Root $sovitsRoot -Name 'install-gpt-sovits'
try {
$taskInstallGpuLease = Enter-CreatorRuntimeLease -Root $sovitsRoot -Name 'gpu'
try {
$sovitsRuntime = & python -B (Join-Path $sovitsRoot 'scripts/creator_job.py') --root $sovitsRoot runtime --component gpt-sovits
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve shared runtime' }
$sovitsRepo = Join-Path $sovitsRuntime 'repo'
$sovitsPython = Join-Path $sovitsRuntime 'venv\Scripts\python.exe'
$env:UV_CACHE_DIR = Join-Path $sovitsRuntime 'uv-cache'
$env:HF_HOME = Join-Path $sovitsRuntime 'hf-cache'
$env:HF_HUB_OFFLINE = '0'
$env:HF_HUB_DISABLE_IMPLICIT_TOKEN = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
if (-not (Test-Path -LiteralPath $sovitsRepo)) {
    git clone https://github.com/RVC-Boss/GPT-SoVITS.git $sovitsRepo
    if ($LASTEXITCODE -ne 0) { throw 'Official source download failed' }
}
git -C $sovitsRepo checkout --detach '1b47ca07ef43a284e0b8bd7f29d3e1e3ff76082a'
if ($LASTEXITCODE -ne 0) { throw 'Source revision unavailable' }
if (-not (Test-Path -LiteralPath $sovitsPython)) {
    uv venv --python (Get-Command python).Source --no-managed-python (Join-Path $sovitsRuntime 'venv')
    if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed' }
}
uv pip install --python $sovitsPython --extra-index-url https://download.pytorch.org/whl/cu128 --index-strategy unsafe-best-match -r (Join-Path $sovitsRoot 'extension\config\sovits-requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependencies installation failed' }
& $sovitsPython -B (Join-Path $PSScriptRoot 'download_sovits.py')
if ($LASTEXITCODE -ne 0) { throw 'Official model download failed' }
& $sovitsPython -B -m nltk.downloader -d (Join-Path $sovitsRuntime 'nltk-data') cmudict averaged_perceptron_tagger averaged_perceptron_tagger_eng
if ($LASTEXITCODE -ne 0) { throw 'Pronunciation dictionary download failed' }
} finally { $taskInstallGpuLease.Dispose() }
} finally { $taskRuntimeLease.Dispose() }
