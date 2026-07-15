param(
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$RequiredFiles = @(
    'PROJECT_BOOTSTRAP.md',
    'docs/INDEX.md',
    'PROJECT_RULES.md',
    'docs/WORKFLOW_CONTRACT.json',
    'tools/projectctl.bat',
    'tools/run_python.bat',
    'tools/git_project.bat'
)
$CandidateScanRoots = @(
    'docs',
    'inputs',
    'outputs',
    'planning_research',
    'skills',
    'tests',
    'tools'
)

$MissingRequired = @(
    $RequiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $Root $_)) }
)
$ExistingScanRoots = @(
    $CandidateScanRoots | Where-Object { Test-Path -LiteralPath (Join-Path $Root $_) }
)
$SkippedScanRoots = @(
    $CandidateScanRoots | Where-Object { -not (Test-Path -LiteralPath (Join-Path $Root $_)) }
)

$PythonExecutable = & (Join-Path $PSScriptRoot 'run_python.bat') -c "import pathlib,sys; print(pathlib.Path(sys.executable).as_posix())"
if ($LASTEXITCODE -ne 0) {
    throw 'Python resolver failed.'
}

$GitRoot = & (Join-Path $PSScriptRoot 'git_project.bat') rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) {
    throw 'Git safe-directory wrapper failed.'
}

$ControlContext = @(& (Join-Path $PSScriptRoot 'projectctl.bat') context)
if ($LASTEXITCODE -ne 0) {
    throw 'projectctl context failed.'
}

$Result = [ordered]@{
    ok = ($MissingRequired.Count -eq 0)
    root = $Root
    missing_required = $MissingRequired
    scan_roots = $ExistingScanRoots
    skipped_scan_roots = $SkippedScanRoots
    python_executable = ($PythonExecutable | Select-Object -First 1)
    git_root = ($GitRoot | Select-Object -First 1)
    control_context = $ControlContext
}

if ($Json) {
    $Result | ConvertTo-Json -Depth 4
}
else {
    'PROJECT PREFLIGHT'
    "- ok: $($Result.ok)"
    "- root: $($Result.root)"
    "- scan roots: $($Result.scan_roots -join ', ')"
    "- skipped scan roots: $($Result.skipped_scan_roots -join ', ')"
    "- python: $($Result.python_executable)"
    "- git root: $($Result.git_root)"
    if ($Result.missing_required.Count) {
        "- missing required: $($Result.missing_required -join ', ')"
    }
    $Result.control_context
}

if (-not $Result.ok) {
    exit 1
}
