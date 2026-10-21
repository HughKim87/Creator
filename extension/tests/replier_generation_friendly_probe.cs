using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Threading;using System.Diagnostics;using System.Web.Script.Serialization;using ReplierDesktop;
public static class GenerationResumeProbe{
 public static int Main(string[] args){try{
 var root=Path.GetFullPath(args[0]);var json=new JavaScriptSerializer{MaxJsonLength=8*1024*1024};string dir=Path.Combine(root,"extension/data/replier-prompt-probe");var saved=SceneMaterial.Json(File.ReadAllText(Path.Combine(dir,"generation-only-v4.json")));var messages=new List<object>{new{role="system",content=(string)CaptionService.Get(saved,"system_prompt")}};messages.AddRange((object[])CaptionService.Get(saved,"examples"));messages.Add(new{role="user",content=(string)CaptionService.Get(saved,"input")});
 messages=new List<object>{
new{role="system",content="게임 영상을 함께 구경하는 사람이 남길 한국어 댓글 초안 2개를 씁니다. 장면의 앞뒤 흐름을 이해하고, 거기서 눈에 들어온 행동이나 공감되는 점에 한마디 보태세요. 친구와 영상을 보며 함께 웃는 친근한 말투가 좋습니다. 대단한 장면이 아니면 소소한 맞장구도 충분합니다. 댓글마다 다른 농담이나 질문을 억지로 만들 필요는 없습니다. 아래 예시의 말의 호흡을 참고하되 실제 내용은 마지막 장면에서 찾으세요. 설명이나 평가 없이 comments 배열에 2개를 반환합니다."},
new{role="user",content="장면: 친구 둘이 같이 출발하려는데 서로 다른 방에 들어가 서로를 찾는다. 댓글 한 개."},
new{role="assistant",content="{\"comments\":[\"출발은 같이했는데 만나질 못하네ㅋㅋ\"]}"},
new{role="user",content="장면: 설명을 들을 때는 고개를 끄덕이다가 시작하자마자 뭐부터 하는 거였지라고 묻는다. 댓글 한 개."},
new{role="assistant",content="{\"comments\":[\"들을 땐 알겠는데 시작하면 모르겠는 거 공감ㅋㅋ\"]}"},
new{role="user",content="장면: 게임 채팅을 보냈는데 영어로 쳐져서 한영키를 바꾸고 다시 보낸다. 댓글 한 개."},
new{role="assistant",content="{\"comments\":[\"채팅 치기 전에 한영키부터 확인ㅋㅋ\"]}"},
new{role="user",content=((string)CaptionService.Get(saved,"input")).Replace("초안 3개","초안 2개")}
};
var reports=new List<object>();var runtime=Path.Combine(root,"extension/.runtime/replier-llm");
 foreach(string name in new[]{"gemma4:e2b-it-qat","gemma4:e2b-it-qat"}){
 object body=new{model=name,stream=false,think=false,keep_alive="60s",format=new{type="object",properties=new{comments=new{type="array",minItems=2,maxItems=2,items=new{type="string"}}},required=new[]{"comments"},additionalProperties=false},options=new{num_ctx=2048,num_batch=128,num_predict=300,temperature=0.45,top_p=0.9,seed=20261020+reports.Count},messages=messages};
 string raw=null,error=null;var watch=Stopwatch.StartNew();using(var model=new LocalModel(runtime,name))using(var limit=new CancellationTokenSource(TimeSpan.FromSeconds(180))){try{model.EnsureReady(limit.Token).GetAwaiter().GetResult();raw=model.Chat(body,limit.Token).GetAwaiter().GetResult();}catch(Exception ex){error=ex.GetType().Name+": "+ex.Message;}finally{if(error==null)try{model.Unload().GetAwaiter().GetResult();}catch{}}}
 var row=new{model=name,seconds=Math.Round(watch.Elapsed.TotalSeconds,3),raw=raw,error=error};reports.Add(row);File.WriteAllText(Path.Combine(dir,"generation-only-v7.json"),json.Serialize(new{video=CaptionService.Get(saved,"video"),messages_sent=messages,request_count=reports.Count,polishing=false,model_evaluation=false,runs=reports}));Console.WriteLine(json.Serialize(row));
 if(error!=null)break;
 }
 return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}



