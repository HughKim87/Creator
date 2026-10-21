param([ValidateSet('qwen3.5:4b','gemma4:e2b-it-qat')][string]$ReplierModel = 'qwen3.5:4b')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'Shared-Runtime.ps1')
$taskRuntimeLease = Enter-CreatorRuntimeLease -Root $taskRoot -Name 'install-replier-llm'
try {
$taskInstallGpuLease = Enter-CreatorRuntimeLease -Root $taskRoot -Name 'gpu'
try {
$taskRuntime = & python -B (Join-Path $taskRoot 'scripts/creator_job.py') --root $taskRoot runtime --component replier-llm
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve shared runtime' }
$taskOllama = Join-Path $taskRuntime 'ollama'
$taskArchive = Join-Path $taskRuntime 'ollama-windows-amd64-v0.40.4.zip'
$taskUrl = 'https://github.com/ollama/ollama/releases/download/v0.40.4/ollama-windows-amd64.zip'
$taskDigest = '7485a1172f8527db4342a63521b9342fc466185ff0855da378cc864ecf6354cf'
$taskExe = Join-Path $taskOllama 'ollama.exe'
$taskMarker = Join-Path $taskOllama '.24hreplier-complete'
[System.IO.Directory]::CreateDirectory($taskRuntime) | Out-Null
if (-not (Test-Path -LiteralPath $taskMarker)) {
    if (-not (Test-Path -LiteralPath $taskArchive)) {
        Write-Output 'Downloading official Ollama Windows package (about 1.47 GB)...'
        $taskDownload = New-Object System.Net.WebClient
        try { $taskDownload.DownloadFile($taskUrl, $taskArchive) } finally { $taskDownload.Dispose() }
    }
    if ((Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskDigest) { throw 'Official package checksum mismatch.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Directory]::CreateDirectory($taskOllama) | Out-Null
    $taskZip = [System.IO.Compression.ZipFile]::OpenRead($taskArchive)
    try {
        $taskPrefix = [System.IO.Path]::GetFullPath($taskOllama) + [System.IO.Path]::DirectorySeparatorChar
        foreach ($taskEntry in $taskZip.Entries) {
            $taskTarget = [System.IO.Path]::GetFullPath((Join-Path $taskOllama $taskEntry.FullName))
            if (-not $taskTarget.StartsWith($taskPrefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe archive entry.' }
            if ([string]::IsNullOrEmpty($taskEntry.Name)) { [System.IO.Directory]::CreateDirectory($taskTarget) | Out-Null; continue }
            [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($taskTarget)) | Out-Null
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($taskEntry, $taskTarget, $true)
        }
    } finally { $taskZip.Dispose() }
    [System.IO.File]::WriteAllText($taskMarker, $taskDigest)
}
$taskStarted = $null
try {
    $taskReady = $false
    try { $taskVersion = Invoke-RestMethod -Uri 'http://127.0.0.1:11439/api/version' -TimeoutSec 2; $taskReady = [bool]$taskVersion.version } catch {}
    if (-not $taskReady) {
        $taskInfo = New-Object System.Diagnostics.ProcessStartInfo
        $taskInfo.FileName = $taskExe
        $taskInfo.Arguments = 'serve'
        $taskInfo.WorkingDirectory = $taskOllama
        $taskInfo.UseShellExecute = $false
        $taskInfo.CreateNoWindow = $true
        $taskInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $taskHome = Join-Path $taskRuntime 'home'
        $taskModels = Join-Path $taskRuntime 'models'
        [System.IO.Directory]::CreateDirectory($taskHome) | Out-Null
        [System.IO.Directory]::CreateDirectory($taskModels) | Out-Null
        $taskInfo.EnvironmentVariables['USERPROFILE'] = $taskHome
        $taskInfo.EnvironmentVariables['OLLAMA_HOST'] = '127.0.0.1:11439'
        $taskInfo.EnvironmentVariables['OLLAMA_MODELS'] = $taskModels
        $taskInfo.EnvironmentVariables['OLLAMA_NO_CLOUD'] = '1'
        $taskStarted = [System.Diagnostics.Process]::Start($taskInfo)
        for ($taskTry = 0; $taskTry -lt 40; $taskTry++) {
            try { $taskVersion = Invoke-RestMethod -Uri 'http://127.0.0.1:11439/api/version' -TimeoutSec 2; $taskReady = [bool]$taskVersion.version } catch {}
            if ($taskReady) { break }
            Start-Sleep -Milliseconds 300
        }
        if (-not $taskReady) { throw 'Local model runtime did not start.' }
    }
    $taskTags = Invoke-RestMethod -Uri 'http://127.0.0.1:11439/api/tags' -TimeoutSec 10
    if (-not ($taskTags.models | Where-Object { $_.name -eq $ReplierModel })) {
        Write-Output ('Downloading local model: ' + $ReplierModel)
        Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:11439/api/pull' -ContentType 'application/json' -Body (@{model=$ReplierModel; stream=$false} | ConvertTo-Json -Compress) -TimeoutSec 3600 | Out-Null
        $taskTags = Invoke-RestMethod -Uri 'http://127.0.0.1:11439/api/tags' -TimeoutSec 10
    }
    if (-not ($taskTags.models | Where-Object { $_.name -eq $ReplierModel })) { throw 'Requested model was not installed.' }
    $taskSelectedModel = $ReplierModel
    $taskConfigPath = Join-Path $taskRoot 'extension/config/replier-llm-local.json'
    if (Test-Path -LiteralPath $taskConfigPath) {
        try {
            $taskPriorModel = (Get-Content -Raw -LiteralPath $taskConfigPath | ConvertFrom-Json).model
            if ($taskPriorModel -in @('qwen3.5:4b','gemma4:e2b-it-qat') -and ($taskTags.models | Where-Object { $_.name -eq $taskPriorModel })) { $taskSelectedModel = $taskPriorModel }
        } catch {}
    }
    $taskRecord = @{
        component = 'ollama'; version = 'v0.40.4'; source = $taskUrl; sha256 = $taskDigest
        model = $taskSelectedModel; modelRebuild = ('scripts/Install-24HReplierLLM.ps1 -ReplierModel ' + $taskSelectedModel); root = 'extension/.runtime/replier-llm'; rebuild = 'scripts/Install-24HReplierLLM.ps1'
        commentModels = @('gemma4:e2b-it-qat','qwen3.5:4b')
        commentRebuild = @('scripts/Install-24HReplierLLM.ps1 -ReplierModel gemma4:e2b-it-qat','scripts/Install-24HReplierLLM.ps1 -ReplierModel qwen3.5:4b')
        models = @($taskTags.models | ForEach-Object { @{name=$_.name; digest=$_.digest; size=$_.size; source=('https://ollama.com/library/'+$_.name)} })
    }
    $taskJson = $taskRecord | ConvertTo-Json -Depth 6
    [System.IO.File]::WriteAllText((Join-Path $taskRoot 'extension/config/replier-llm-local.json'), $taskJson, [System.Text.UTF8Encoding]::new($false))
    Write-Output '24HReplier local AI is ready.'
} finally {
    if ($taskStarted -and -not $taskStarted.HasExited) { $taskStarted.Kill(); $taskStarted.WaitForExit() }
}
} finally { $taskInstallGpuLease.Dispose() }
} finally { $taskRuntimeLease.Dispose() }
