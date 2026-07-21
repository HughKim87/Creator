$PythonArguments = @($args)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-PythonCandidate {
    param(
        [string] $Command,
        [string[]] $PrefixArguments,
        [string] $Source
    )

    [pscustomobject]@{
        Command = $Command
        PrefixArguments = @($PrefixArguments)
        Source = $Source
    }
}

function Test-PythonCandidate {
    param([pscustomobject] $Candidate)

    $probeArguments = @($Candidate.PrefixArguments) + @(
        "-c",
        "import sys, tomllib; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
    )
    try {
        & $Candidate.Command @probeArguments *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

if (-not $PythonArguments -or $PythonArguments.Count -eq 0) {
    [Console]::Error.WriteLine("No Python arguments were supplied. Example: & tools/runtime/run_python.ps1 --version")
    exit 2
}

$selected = $null
if (-not [string]::IsNullOrWhiteSpace($env:PROJECT_PYTHON)) {
    $override = New-PythonCandidate -Command $env:PROJECT_PYTHON -PrefixArguments @() -Source "PROJECT_PYTHON"
    if (-not (Test-Path -LiteralPath $override.Command -PathType Leaf) -or -not (Test-PythonCandidate $override)) {
        [Console]::Error.WriteLine("PROJECT_PYTHON does not point to a working Python executable with Python 3.11+ and tomllib: $($override.Command)")
        exit 2
    }
    $selected = $override
}
else {
    $candidates = @()
    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    foreach ($relativePath in @(".venv\Scripts\python.exe", ".venv/bin/python3", ".venv/bin/python")) {
        $candidatePath = Join-Path $repoRoot $relativePath
        if (Test-Path -LiteralPath $candidatePath -PathType Leaf) {
            $candidates += New-PythonCandidate -Command $candidatePath -PrefixArguments @() -Source "project-venv"
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($HOME)) {
        $codexRoot = Join-Path $HOME ".cache/codex-runtimes"
        $primaryRoot = Join-Path $codexRoot "codex-primary-runtime/dependencies/python"
        foreach ($candidatePath in @(
            (Join-Path $primaryRoot "python.exe"),
            (Join-Path $primaryRoot "bin/python3"),
            (Join-Path $primaryRoot "bin/python")
        )) {
            if (Test-Path -LiteralPath $candidatePath -PathType Leaf) {
                $candidates += New-PythonCandidate -Command $candidatePath -PrefixArguments @() -Source "codex-primary-runtime"
            }
        }

        if (Test-Path -LiteralPath $codexRoot -PathType Container) {
            foreach ($runtime in (Get-ChildItem -LiteralPath $codexRoot -Directory -ErrorAction SilentlyContinue | Sort-Object FullName)) {
                foreach ($suffix in @("dependencies/python/python.exe", "dependencies/python/bin/python3", "dependencies/python/bin/python")) {
                    $candidatePath = Join-Path $runtime.FullName $suffix
                    if (Test-Path -LiteralPath $candidatePath -PathType Leaf) {
                        $candidates += New-PythonCandidate -Command $candidatePath -PrefixArguments @() -Source "codex-runtime"
                    }
                }
            }
        }
    }

    foreach ($commandSpec in @(
        [pscustomobject]@{ Name = "py"; PrefixArguments = @("-3") },
        [pscustomobject]@{ Name = "python3"; PrefixArguments = @() },
        [pscustomobject]@{ Name = "python"; PrefixArguments = @() }
    )) {
        $command = Get-Command -Name $commandSpec.Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($command) {
            $candidates += New-PythonCandidate -Command $command.Source -PrefixArguments $commandSpec.PrefixArguments -Source "PATH:$($commandSpec.Name)"
        }
    }

    $seen = @{}
    foreach ($candidate in $candidates) {
        $key = "$($candidate.Command)|$($candidate.PrefixArguments -join ' ')"
        if ($seen.ContainsKey($key)) {
            continue
        }
        $seen[$key] = $true
        if (Test-PythonCandidate $candidate) {
            $selected = $candidate
            break
        }
    }
}

if (-not $selected) {
    [Console]::Error.WriteLine("No working Python 3.11+ runtime with tomllib was found. Set PROJECT_PYTHON to an exact executable, create .venv, or load the Codex workspace dependency runtime.")
    exit 2
}

$invocationArguments = @($selected.PrefixArguments) + @($PythonArguments)
& $selected.Command @invocationArguments
exit [int]$LASTEXITCODE
