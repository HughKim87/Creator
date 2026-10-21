$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'Shared-Runtime.ps1')
$taskRuntimeLease = Enter-CreatorRuntimeLease -Root $taskRoot -Name 'build-replier-desktop'
try {
$taskCompiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
$taskOutputDir = & python -B (Join-Path $taskRoot 'scripts/creator_job.py') --root $taskRoot runtime --component replier-desktop
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve shared runtime' }
$taskSource = @(Get-ChildItem -LiteralPath (Join-Path $taskRoot 'extension/src/replier') -Filter '*.cs' -File | ForEach-Object { $_.FullName })
$taskOutput = Join-Path $taskOutputDir '24HReplier.exe'
if (-not (Test-Path -LiteralPath $taskCompiler)) { throw 'Windows .NET Framework C# compiler was not found.' }
[System.IO.Directory]::CreateDirectory($taskOutputDir) | Out-Null
& $taskCompiler /nologo /target:winexe /platform:anycpu /optimize+ /codepage:65001 "/out:$taskOutput" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Net.Http.dll /reference:System.Web.Extensions.dll /reference:System.Web.dll /reference:System.Security.dll $taskSource
if ($LASTEXITCODE -ne 0) { throw '24HReplier build failed.' }
Write-Output $taskOutput

} finally { $taskRuntimeLease.Dispose() }
