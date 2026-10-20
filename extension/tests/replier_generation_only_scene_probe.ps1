$ErrorActionPreference='Stop'
$root='D:\AI Agent\GitHub\Creator-24HReplier'
$runtime=Join-Path $root 'extension\.runtime\replier-llm'
$out=Join-Path $root 'extension\data\replier-prompt-probe'
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
foreach($pair in @{OLLAMA_HOST='127.0.0.1:11440';OLLAMA_MODELS=(Join-Path $runtime 'models');OLLAMA_NO_CLOUD='1';USERPROFILE=(Join-Path $runtime 'home');OLLAMA_MAX_LOADED_MODELS='1';OLLAMA_NUM_PARALLEL='1'}.GetEnumerator()){$info.EnvironmentVariables[$pair.Key]=$pair.Value}
$source=(Get-Content -LiteralPath (Join-Path $root 'extension\data\replier-grounded-checks\residency-benchmark-timeout-recovery-final-latest.json') -Raw|ConvertFrom-Json).runs[0]
$material=$source.result.Batches[0].Result.Comments[0].Material|ConvertFrom-Json
$content=Get-Content -LiteralPath (Join-Path $root 'extension/data/replier/content/vDWt01ul5F0.json') -Raw|ConvertFrom-Json
$scene=@($content.Cues|Where-Object {$_.StartMs -ge 233000 -and $_.StartMs -le 279000})
$dialogue=($scene|ForEach-Object {$span=[TimeSpan]::FromMilliseconds($_.StartMs);'['+$span.ToString('mm\:ss')+'] '+$_.Text}) -join "`n"
$reference=@($source.result.Batches[0].Result.ReferenceComments|Where-Object {$_ -match '3:5[2-9]|4:[0-3][0-9]'})
$inputData="영상 제목: "+$source.video.Title+"`n`n한 장면의 앞뒤 대화:`n"+$dialogue+"`n`n이 장면 부근에 달린 기존 댓글(반응 지점과 말투 참고):`n"+($reference -join "`n")
$prompt='한국어 유튜브 영상을 본 시청자가 남길 법한 댓글 초안 3개를 씁니다.
아래는 한 장면의 앞뒤가 이어지는 실제 자막입니다. 말 한 조각을 복원하려 하지 말고, 대화를 주고받으며 무엇을 하려다가 어떤 반응을 얻는지 흐름을 읽으세요. 그 장면을 구경한 사람의 생각이나 웃음이 드러나는 한마디를 자기 말로 쓰세요. 설명문이나 출연자의 다음 대사를 쓰는 작업이 아닙니다.
기존 댓글은 사람들이 관심을 보인 대목과 말의 호흡을 참고합니다. 거기에만 나오는 사연이나 이름은 새 사실의 근거가 아닙니다. 사실은 자막에서 이해되는 행동과 대화로 잡고, 장면 설명을 반복하기보다 자기 반응을 보태세요.
예를 들어 약속한 시간보다 한참 늦게 도착한 장면이라면 시청자가 그 기다림에 반응할 수 있습니다. 이런 식으로 앞뒤 상황을 읽되, 예시 장면이 실제 자료에 없으면 사용하지 않습니다.
길이를 억지로 줄이거나 후보마다 질문·칭찬·농담을 배정하지 않습니다. 평소 말하는 한 문장 정도면 됩니다. 기존 댓글을 베끼지 말고 설명·분석·점수 없이 comments 배열로 초안 3개만 반환하세요.'
function Post($path,$data){Invoke-RestMethod -Uri ($uri+$path) -Method Post -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes(($data|ConvertTo-Json -Depth 16 -Compress))) -TimeoutSec 70}
$models=@('qwen3.5:4b','gemma4:e2b-it-qat')
$report=[ordered]@{video=$source.video;system_prompt=$prompt;input=$inputData;request_count=0;polishing=$false;model_evaluation=$false;runs=@()}
$p=$null
try{
 $p=[Diagnostics.Process]::Start($info)
 $ready=$false
 for($i=0;$i -lt 40;$i++){try{$null=Invoke-RestMethod "$uri/api/version" -TimeoutSec 1;$ready=$true;break}catch{Start-Sleep -Milliseconds 300}}
 if(-not $ready){throw 'Server did not start'}
 foreach($name in $models){
  $data=@{model=$name;stream=$false;think=$false;keep_alive=0;format=@{type='object';properties=@{comments=@{type='array';minItems=3;maxItems=3;items=@{type='string'}}};required=@('comments');additionalProperties=$false};options=@{num_ctx=8192;num_batch=128;num_predict=420;temperature=0.65;top_p=0.9;seed=20261020};messages=@(@{role='system';content=$prompt},@{role='user';content=$inputData})}
  $watch=[Diagnostics.Stopwatch]::StartNew();$report.request_count++
  try{$r=Post '/api/chat' $data;$row=[ordered]@{model=$name;seconds=[Math]::Round($watch.Elapsed.TotalSeconds,3);load_seconds=[Math]::Round($r.load_duration/1e9,3);prompt_seconds=[Math]::Round($r.prompt_eval_duration/1e9,3);generation_seconds=[Math]::Round($r.eval_duration/1e9,3);done=$r.done;done_reason=$r.done_reason;raw=$r.message.content}}
  catch{$row=[ordered]@{model=$name;seconds=[Math]::Round($watch.Elapsed.TotalSeconds,3);error=$_.Exception.Message}}
  $report.runs+= $row
  $report|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $out 'generation-only-v2.json') -Encoding UTF8
  $row|ConvertTo-Json -Depth 7 -Compress|Write-Output
 }
}finally{
 if($p -and -not $p.HasExited){& taskkill.exe /PID $p.Id /T /F|Out-Null}
 $report.cleanup_port_open=[bool](Get-NetTCPConnection -State Listen -LocalPort 11440 -ErrorAction SilentlyContinue)
 $report|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $out 'generation-only-v2.json') -Encoding UTF8
}

