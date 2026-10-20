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
$scene=@($content.Cues|Where-Object {$_.StartMs -ge 243000 -and $_.StartMs -le 263000})
$dialogue=($scene|ForEach-Object {$_.Text}) -join " "
$inputData='영상 제목: 잼민이 기강 잡기
댓글을 달 장면: 게임 속 클럽에서 인사하고 대화를 시도하는 부분.
원문에서 확인되는 흐름:
1. 놀아보겠다며 안녕이라고 인사를 한다.
2. 대답이 없자 왜 대답을 안 해 주느냐고 말한다.
3. 대화를 어떻게 하는지 묻고, 마이크를 켠다는 이야기가 나온 뒤 다시 안녕이라고 인사한다.
원문 근거:
- 좀 이제 놀아야 되는 거죠, 여기서. 안녕.
- 왜? 대답 안 해 주는데.
- 대화를 어떻게 해요?
- 마이크 키고 한다고. 안녕. 안녕.
이 장면에 대한 시청자의 댓글 초안 3개.'
$prompt='Write three natural Korean YouTube comments reacting to the supplied game scene. The scene notes are grounded in the quoted transcript; use those facts. Write as a viewer, not as the player continuing the dialogue. Add a personal reaction to the situation instead of describing or paraphrasing it. Casual, everyday Korean is best. A small observation or playful response is enough; no mandatory question, praise, criticism, or joke. Do not invent events or causes. Use the examples only for conversational style, not their content. Return only a comments array with three drafts.'
$examples=@(
 @{role='user';content="대화 원문: 한참 밀어서 여기까지 왔는데 다시 보니까 처음 그 자리네. 뭐야 한 바퀴 돈 거였어?`n댓글 한 개"},
 @{role='assistant';content='{"comments":["열심히 돌아서 제자리ㅋㅋ"]}'},
 @{role='user';content="대화 원문: 연습할 때는 다 맞았는데 시작 누르니까 또 틀리네. 방금까지 됐잖아.`n댓글 한 개"},
 @{role='assistant';content='{"comments":["연습할 땐 잘되는 게 더 약오름ㅋㅋ"]}'}
)
function Post($path,$data){Invoke-RestMethod -Uri ($uri+$path) -Method Post -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes(($data|ConvertTo-Json -Depth 16 -Compress))) -TimeoutSec 70}
$models=@('qwen3.5:4b','gemma4:e2b-it-qat')
$report=[ordered]@{video=$source.video;system_prompt=$prompt;input=$inputData;examples=$examples;request_count=0;polishing=$false;model_evaluation=$false;runs=@()}
$p=$null
try{
 $p=[Diagnostics.Process]::Start($info)
 $ready=$false
 for($i=0;$i -lt 40;$i++){try{$null=Invoke-RestMethod "$uri/api/version" -TimeoutSec 1;$ready=$true;break}catch{Start-Sleep -Milliseconds 300}}
 if(-not $ready){throw 'Server did not start'}
 foreach($name in $models){
  $data=@{model=$name;stream=$false;think=$false;keep_alive=0;format=@{type='object';properties=@{comments=@{type='array';minItems=3;maxItems=3;items=@{type='string'}}};required=@('comments');additionalProperties=$false};options=@{num_ctx=8192;num_batch=128;num_predict=420;temperature=0.45;top_p=0.9;seed=20261020};messages=@(@{role='system';content=$prompt},@{role='user';content=$inputData})}
  $watch=[Diagnostics.Stopwatch]::StartNew();$report.request_count++
  try{$r=Post '/api/chat' $data;$row=[ordered]@{model=$name;seconds=[Math]::Round($watch.Elapsed.TotalSeconds,3);load_seconds=[Math]::Round($r.load_duration/1e9,3);prompt_seconds=[Math]::Round($r.prompt_eval_duration/1e9,3);generation_seconds=[Math]::Round($r.eval_duration/1e9,3);done=$r.done;done_reason=$r.done_reason;raw=$r.message.content}}
  catch{$row=[ordered]@{model=$name;seconds=[Math]::Round($watch.Elapsed.TotalSeconds,3);error=$_.Exception.Message}}
  $report.runs+= $row
  $report|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $out 'generation-only-v4.json') -Encoding UTF8
  $row|ConvertTo-Json -Depth 7 -Compress|Write-Output
 }
}finally{
 if($p -and -not $p.HasExited){& taskkill.exe /PID $p.Id /T /F|Out-Null}
 $report.cleanup_port_open=[bool](Get-NetTCPConnection -State Listen -LocalPort 11440 -ErrorAction SilentlyContinue)
 $report|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $out 'generation-only-v4.json') -Encoding UTF8
}



