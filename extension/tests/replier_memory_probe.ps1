$ErrorActionPreference='Stop'
$root='D:\AI Agent\GitHub\Creator-24HReplier'
$runtime=Join-Path $root 'extension\.runtime\replier-llm'
$out=Join-Path $root 'extension\data\replier-memory-checks'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$uri='http://127.0.0.1:11440'
if(Get-NetTCPConnection -State Listen -LocalPort 11440 -ErrorAction SilentlyContinue){throw 'Test port occupied'}
$info=New-Object System.Diagnostics.ProcessStartInfo
$info.FileName=Join-Path $runtime 'ollama\ollama.exe'
$info.Arguments='serve'
$info.WorkingDirectory=Join-Path $runtime 'ollama'
$info.UseShellExecute=$false
$info.CreateNoWindow=$true
$info.WindowStyle=[System.Diagnostics.ProcessWindowStyle]::Hidden
foreach($pair in @{OLLAMA_HOST='127.0.0.1:11440';OLLAMA_MODELS=(Join-Path $runtime 'models');OLLAMA_NO_CLOUD='1';USERPROFILE=(Join-Path $runtime 'home');OLLAMA_MAX_LOADED_MODELS='2';OLLAMA_NUM_PARALLEL='1'}.GetEnumerator()){$info.EnvironmentVariables[$pair.Key]=$pair.Value}
$models=@('qwen3.5:4b','gemma4:e2b-it-qat')
$report=[ordered]@{at=(Get-Date).ToString('o');context=8192;parallel=1;max_loaded=2;baseline_gpu=(& nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader);steps=@()}
function Post($path,$body){Invoke-RestMethod -Uri ($uri+$path) -Method Post -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes(($body|ConvertTo-Json -Depth 12 -Compress))) -TimeoutSec 90}
function Snapshot($label,$response,$elapsed){
 $ps=Invoke-RestMethod -Uri "$uri/api/ps" -TimeoutSec 5
 $entry=[ordered]@{label=$label;elapsed_s=$elapsed;load_s=($response.load_duration/1e9);total_s=($response.total_duration/1e9);eval_count=$response.eval_count;models=$ps.models;gpu=(& nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader)}
 $script:report.steps+= $entry
 $report|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $out 'latest.json') -Encoding UTF8
 Write-Output ($entry|ConvertTo-Json -Depth 8 -Compress)
}
function Probe($name,$label){
 $watch=[Diagnostics.Stopwatch]::StartNew()
 $response=Post '/api/chat' @{model=$name;messages=@(@{role='user';content='짧게 확인이라고만 답해주세요.'});stream=$false;think=$false;keep_alive=-1;options=@{num_ctx=8192;num_predict=12;temperature=0}}
 Snapshot $label $response ([Math]::Round($watch.Elapsed.TotalSeconds,3))
}
$p=$null
try{
 $p=[Diagnostics.Process]::Start($info)
 $ready=$false
 for($i=0;$i -lt 40;$i++){try{$report.version=Invoke-RestMethod -Uri "$uri/api/version" -TimeoutSec 1;$ready=$true;break}catch{Start-Sleep -Milliseconds 300}}
 if(-not $ready){throw 'Server readiness failed'}
 $report.tags=(Invoke-RestMethod -Uri "$uri/api/tags").models|Select-Object name,size,details
 $report.show=@()
 foreach($name in $models){$show=Post '/api/show' @{model=$name};$report.show+=@{name=$name;details=$show.details;model_info=$show.model_info;projector_info=$show.projector_info}}
 Write-Output ('METADATA '+($report|ConvertTo-Json -Depth 12 -Compress))
 Probe $models[0] 'qwen_alone'
 $null=Post '/api/generate' @{model=$models[0];keep_alive=0}
 Probe $models[1] 'gemma_alone'
 $null=Post '/api/generate' @{model=$models[1];keep_alive=0}
 Probe $models[0] 'both_A_qwen'
 Probe $models[1] 'both_B_gemma'
 Probe $models[0] 'both_A2_qwen'
 Probe $models[1] 'both_B2_gemma'
}catch{$report.error=$_.Exception.Message;Write-Output ('ERROR '+$report.error)}finally{
 foreach($name in $models){try{$null=Post '/api/generate' @{model=$name;keep_alive=0}}catch{}}
 if($p -and -not $p.HasExited){& taskkill.exe /PID $p.Id /T /F | Out-Null}
 Start-Sleep -Seconds 2
 $report.cleanup_gpu=(& nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader)
 $report.cleanup_port_open=[bool](Get-NetTCPConnection -State Listen -LocalPort 11440 -ErrorAction SilentlyContinue)
 $report|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $out 'latest.json') -Encoding UTF8
 Write-Output ('CLEANUP '+$report.cleanup_gpu+' port_open='+$report.cleanup_port_open)
}
