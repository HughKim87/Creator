# Generation probes record and send the same serialized request.
function New-ReplierProbeRequest {
    param(
        [string]$Model,
        [string]$Prompt,
        [string]$InputText,
        [AllowEmptyCollection()][object[]]$Examples = @(),
        [object]$Format,
        [object]$Options
    )
    $messages = @(@{role='system';content=$Prompt}) + @($Examples) + @(@{role='user';content=$InputText})
    $request = [ordered]@{model=$Model;stream=$false;think=$false;keep_alive=0;format=$Format;options=$Options;messages=$messages}
    return ($request | ConvertTo-Json -Depth 20 -Compress)
}
