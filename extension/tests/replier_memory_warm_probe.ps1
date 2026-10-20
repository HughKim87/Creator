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
 $report|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $out 'warm-verification.json') -Encoding UTF8
 Write-Output ($entry|ConvertTo-Json -Depth 8 -Compress)
}
function Probe($name,$label){
 $watch=[Diagnostics.Stopwatch]::StartNew()
 $response=Post '/api/chat' @{model=$name;messages=@(@{role='user';content=("게임 영상을 본 시청자처럼 짧고 자연스러운 한국어 반응 세 개를 작성하세요. 영상 내용: 아이템 강화 비용이 한 번에 10만원이고 좋은 결과가 나와도 원하던 능력치가 아니어서 아쉬워합니다. 이번 요청 번호: "+$label)});stream=$false;think=$false;keep_alive=-1;options=@{num_ctx=8192;num_predict=96;temperature=0}}
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
 Probe $models[1] 'gemma_first'
 Probe $models[0] 'qwen_second'
 Probe $models[1] 'gemma_warm'
 Probe $models[0] 'qwen_warm'
 Probe $models[1] 'gemma_warm_again'
}catch{$report.error=$_.Exception.Message;Write-Output ('ERROR '+$report.error)}finally{
 foreach($name in $models){try{$null=Post '/api/generate' @{model=$name;keep_alive=0}}catch{}}
 if($p -and -not $p.HasExited){& taskkill.exe /PID $p.Id /T /F | Out-Null}
 Start-Sleep -Seconds 2
 $report.cleanup_gpu=(& nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader)
 $report.cleanup_port_open=[bool](Get-NetTCPConnection -State Listen -LocalPort 11440 -ErrorAction SilentlyContinue)
 $report|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $out 'warm-verification.json') -Encoding UTF8
 Write-Output ('CLEANUP '+$report.cleanup_gpu+' port_open='+$report.cleanup_port_open)
}

