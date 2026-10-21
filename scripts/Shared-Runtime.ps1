# Resolve a catalog-owned component and hold an install/build lease for one call.
function Enter-CreatorRuntimeLease {
    param([string]$Root, [string]$Name)
    if ($Name -notmatch '^[a-z0-9-]+$') { throw 'Invalid runtime lease name' }
    $taskLockRoot = Join-Path $Root 'extension/.runtime/locks'
    foreach ($taskCheck in @((Join-Path $Root 'extension'), (Join-Path $Root 'extension/.runtime'), $taskLockRoot)) {
        if ((Test-Path -LiteralPath $taskCheck) -and ((Get-Item -LiteralPath $taskCheck).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Unsafe runtime lock path' }
    }
    [IO.Directory]::CreateDirectory($taskLockRoot) | Out-Null
    try {
        return [IO.File]::Open((Join-Path $taskLockRoot ($Name + '.lock')), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    } catch { throw "Another process owns runtime resource $Name" }
}
