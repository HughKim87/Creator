$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'replier_probe_request.ps1')
function Check($ok,$label){if(-not $ok){throw $label}; Write-Output ('PASS '+$label)}
$prompt='한국어 장면 반응'
$inputData='인사를 다시 건넵니다.'
$examples=@(@{role='user';content='예시 장면'},@{role='assistant';content='{"comments":["예시 반응ㅋㅋ"]}'})
$name='mock-model'
$uri='http://not-a-real-server.invalid'
$script:sent=$null
function Invoke-RestMethod {
    param($Uri,$Method,$ContentType,$Body,$TimeoutSec)
    $script:sent=[Text.Encoding]::UTF8.GetString($Body)
    return @{done=$true;message=@{content='{"comments":["검사용"]}'}}
}
foreach($file in @('replier_generation_context_probe.ps1','replier_generation_grounded_input_probe.ps1')){
    $path=Join-Path $PSScriptRoot $file
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
    Check ($errors.Count -eq 0) ($file+' parses')
    $post=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Post'},$true)
    . ([scriptblock]::Create($post.Extent.Text))
    $assignment=$ast.Find({param($node) $node -is [Management.Automation.Language.AssignmentStatementAst] -and $node.Left.Extent.Text -eq '$requestJson'},$true)
    . ([scriptblock]::Create($assignment.Extent.Text))
    $recorded=$requestJson|ConvertFrom-Json
    Check ($recorded.messages.Count -eq 4 -and $recorded.messages[1].content -eq $examples[0].content -and $recorded.messages[2].content -eq $examples[1].content) ($file+' sends actual examples between system and current input')
    $null=Post '/api/chat' $requestJson
    Check ($script:sent -ceq $requestJson) ($file+' mocked HTTP receives exactly the recorded JSON UTF8 bytes')
    Check (($script:sent|ConvertFrom-Json).messages[3].content -eq $inputData) ($file+' preserves Korean current input')
    $text=[IO.File]::ReadAllText($path)
    $recordAt=$text.IndexOf('request_sent=($requestJson|ConvertFrom-Json)')
    # Inspect literal boundaries without executing the process-starting probe.
    $sendAt=$text.IndexOf('try{$r=Post')
    Check ($recordAt -ge 0 -and $recordAt -lt $sendAt -and $text.Substring($recordAt,$sendAt-$recordAt).Contains('Set-Content')) ($file+' records request before dispatch, including timeout cases')
    Check ($text.Contains('-repaired.json')) ($file+' keeps historical result files intact')
}
$empty=New-ReplierProbeRequest -Model $name -Prompt $prompt -InputText $inputData -Examples @() -Format @{} -Options @{}
Check (($empty|ConvertFrom-Json).messages.Count -eq 2) 'intentional no-example experiments remain valid'
