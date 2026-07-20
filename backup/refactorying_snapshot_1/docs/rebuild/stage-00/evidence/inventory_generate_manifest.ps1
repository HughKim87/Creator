$ErrorActionPreference = 'Stop'

$root = (Get-Location).Path
$safeRoot = $root.Replace('\', '/')
$backup = (Resolve-Path -LiteralPath 'backup').Path
$stage = Join-Path $root 'docs/rebuild/stage-00'
$evidence = Join-Path $stage 'evidence'
$utf8 = [System.Text.UTF8Encoding]::new($false)

function Write-Utf8Lf([string]$Path, [string]$Text) {
    [System.IO.File]::WriteAllText($Path, ($Text -replace "`r`n", "`n"), $utf8)
}

function Get-Sha256([string]$Path) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        return [System.BitConverter]::ToString(
            $sha.ComputeHash($stream)
        ).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $stream.Dispose()
        $sha.Dispose()
    }
}

function Get-TextSha256([string]$Text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $utf8.GetBytes(($Text -replace "`r`n", "`n"))
        return [System.BitConverter]::ToString(
            $sha.ComputeHash($bytes)
        ).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Test-ForbiddenPath([string]$Rel) {
    $segments = $Rel.ToLowerInvariant().Split('/')
    return ($segments -contains 'inputs' -or $segments -contains 'outputs')
}

function Test-SensitivePath([string]$Rel) {
    $p = $Rel.ToLowerInvariant()
    return (
        $p -match '(^|/)\.env($|[./])' -or
        $p -match '\.(pem|key|p12|pfx)$' -or
        $p -match '(^|/)(id_rsa|id_dsa|id_ecdsa|id_ed25519)(\.|$)' -or
        $p -match '(^|/)(credentials?|secrets?|tokens?|cookies?)(/|$)'
    )
}

function Get-FileType([string]$Rel) {
    $name = [System.IO.Path]::GetFileName($Rel).ToLowerInvariant()
    $ext = [System.IO.Path]::GetExtension($Rel).ToLowerInvariant()
    if ($name -eq 'license') { return 'license' }
    if (-not $ext) { return 'no_extension' }
    return $ext.TrimStart('.')
}

function Get-Role([string]$Rel) {
    $p = $Rel.ToLowerInvariant()
    $name = [System.IO.Path]::GetFileName($p)
    $ext = [System.IO.Path]::GetExtension($p)
    if ($p -match '(^|/)tests?/' -or $name -match '^test_.*\.py$') { return 'test' }
    if (
        $p -match '(^|/)(agents|project_bootstrap|project_rules|skill_contract)\.md$' -or
        $p.EndsWith('/skill.md') -or
        $p -match '(contract|schema)\.(json|md)$' -or
        $p -match '^tools/guard/.*\.(toml|json)$' -or
        $p -match '^\.claude/settings\.json$' -or
        $p -match '^\.(gitignore|geminiignore|gitattributes)$' -or
        $p -match '^\.github/' -or
        $p -match '^\.githooks/'
    ) { return 'contract' }
    if ($ext -in @('.py', '.bat', '.ps1', '.sh', '.exe')) { return 'code' }
    return 'doc'
}

function Invoke-Git([string[]]$Arguments) {
    $result = & git -c 'core.quotepath=false' -c "safe.directory=$safeRoot" @Arguments
    if ($LASTEXITCODE -ne 0) { throw "git command failed with $LASTEXITCODE" }
    return @($result)
}

$trackedRaw = Invoke-Git @('ls-files', '--', 'backup')
$trackedRel = @(
    $trackedRaw |
        Where-Object { $_ } |
        ForEach-Object { ($_ -replace '^backup[/\\]', '').Replace('\', '/') } |
        Sort-Object -Unique
)

if (@($trackedRel | Where-Object { Test-ForbiddenPath $_ }).Count -gt 0) {
    throw 'Forbidden user-data path is tracked; path details intentionally suppressed.'
}
if (@($trackedRel | Where-Object { Test-SensitivePath $_ }).Count -gt 0) {
    throw 'Sensitive path is tracked; path details intentionally suppressed.'
}

function New-Manifest {
    $records = foreach ($rel in $trackedRel) {
        $full = Join-Path $backup ($rel.Replace('/', '\'))
        if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
            throw 'Tracked framework file is missing; path details intentionally suppressed.'
        }
        $item = Get-Item -LiteralPath $full
        [pscustomobject][ordered]@{
            path = $rel
            file_type = Get-FileType $rel
            bytes = [int64]$item.Length
            sha256 = Get-Sha256 $full
            role = Get-Role $rel
        }
    }
    $orderedRecords = @($records | Sort-Object path)
    $roleCounts = [ordered]@{}
    foreach ($role in @('code', 'test', 'contract', 'doc')) {
        $roleCounts[$role] = @($orderedRecords | Where-Object { $_.role -eq $role }).Count
    }
    return [pscustomobject][ordered]@{
        schema_version = 2
        root = 'backup/'
        selection = [pscustomobject][ordered]@{
            source = 'git ls-files -- backup'
            allowed_roles = @('code', 'test', 'contract', 'doc')
            forbidden_path_segments = @('inputs', 'outputs')
            recursive_filesystem_discovery = $false
            ignored_and_untracked_files_collected = $false
        }
        hash_algorithm = 'SHA-256'
        summary = [pscustomobject][ordered]@{
            total_framework_files = $orderedRecords.Count
            hashed_framework_files = $orderedRecords.Count
            role_counts = [pscustomobject]$roleCounts
        }
        files = $orderedRecords
    }
}

function Get-GitState {
    $branch = (Invoke-Git @('branch', '--show-current')) -join ''
    $head = (Invoke-Git @('rev-parse', 'HEAD')) -join ''
    $worktree = @(Invoke-Git @('diff', '--name-only', '--', 'backup/'))
    $index = @(Invoke-Git @('diff', '--cached', '--name-only', '--', 'backup/'))
    return @(
        "branch=$branch"
        "head=$head"
        "backup_worktree_diff_entries=$($worktree.Count)"
        "backup_index_diff_entries=$($index.Count)"
    ) -join "`n"
}

Write-Utf8Lf (Join-Path $evidence 'inventory_pre_git_state.txt') ((Get-GitState) + "`n")

$timer = [System.Diagnostics.Stopwatch]::StartNew()
$manifest1 = New-Manifest
$pass1Seconds = $timer.Elapsed.TotalSeconds
$timer.Restart()
$manifest2 = New-Manifest
$pass2Seconds = $timer.Elapsed.TotalSeconds

$json1 = ($manifest1 | ConvertTo-Json -Depth 8) + "`n"
$json2 = ($manifest2 | ConvertTo-Json -Depth 8) + "`n"
$same = $json1 -ceq $json2

$hash1 = Get-TextSha256 $json1
$hash2 = Get-TextSha256 $json2
if (-not $same) { throw 'Manifest passes differ.' }

Write-Utf8Lf (Join-Path $stage 'BACKUP_MANIFEST.json') $json2
Write-Utf8Lf (Join-Path $evidence 'inventory_manifest_determinism.txt') ((@(
    'scope=git_tracked_framework_only'
    "pass1_seconds=$([Math]::Round($pass1Seconds, 3))"
    "pass2_seconds=$([Math]::Round($pass2Seconds, 3))"
    "full_json_sha256_pass1=$hash1"
    "full_json_sha256_pass2=$hash2"
    "deterministic_fields_match=$same"
    "framework_files=$($manifest2.summary.total_framework_files)"
) -join "`n") + "`n")

Write-Utf8Lf (Join-Path $evidence 'inventory_post_git_state.txt') ((Get-GitState) + "`n")

Write-Output "deterministic=$same framework_files=$($manifest2.summary.total_framework_files) sha256=$hash1"
