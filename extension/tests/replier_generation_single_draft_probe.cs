using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Threading;using System.Diagnostics;using System.Web.Script.Serialization;using ReplierDesktop;
public static class GenerationResumeProbe{
 public static int Main(string[] args){try{
 var root=Path.GetFullPath(args[0]);var json=new JavaScriptSerializer{MaxJsonLength=8*1024*1024};string dir=Path.Combine(root,"extension/data/replier-prompt-probe");var saved=SceneMaterial.Json(File.ReadAllText(Path.Combine(dir,"generation-only-v4.json")));var messages=new List<object>{
new{role="system",content="게임 영상 댓글 초안 한 개를 씁니다. 마지막 입력의 작은 장면에 대해 구경하는 사람이 편하게 툭 남기는 한 문장이면 됩니다. 아래 예시의 담백한 어순과 길이를 참고하세요. 장면을 소개하거나 인물의 마음을 설명하기보다 그 상황에 자기 반응을 보태세요. 예시의 사건을 현재 장면으로 옮기지 않습니다. comments 배열에 한 문장만 반환하세요."},
new{role="user",content="장면: 문을 잠그고 돌아서다가 다시 손잡이를 당겨 잠겼는지 확인한다."},
new{role="assistant",content="{\"comments\":[\"잠갔는데 괜히 한 번 더 확인하게 됨ㅋㅋ\"]}"},
new{role="user",content="장면: 서로 먼저 지나가라고 양보하다가 둘 다 제자리에 서 있다."},
new{role="assistant",content="{\"comments\":[\"서로 양보하다 출발도 못함ㅋㅋ\"]}"},
new{role="user",content="장면: 설명을 들을 때는 고개를 끄덕이다가 시작하자마자 뭐부터 하는지 다시 묻는다."},
new{role="assistant",content="{\"comments\":[\"들을 땐 알겠는데 시작하면 모르겠는 거 공감ㅋㅋ\"]}"},
new{role="user",content="장면: 게임 속 클럽에서 다른 사람들과 대화해 보려는 부분. 안녕이라고 인사하지만 대답이 없다고 말한다. 대화를 어떻게 하는지 묻고, 마이크를 켠다는 이야기를 듣고 다시 안녕이라고 인사한다.\n실제 대사: 여기서. 안녕. / 왜? 대답 안 해 주는데. / 대화를 어떻게 해요? / 마이크 키고 한다고. 안녕. 안녕.\n이 장면을 구경한 사람의 댓글 한 개."}
};var reports=new List<object>();var runtime=Path.Combine(root,"extension/.runtime/replier-llm");
 foreach(string name in new[]{"gemma4:e2b-it-qat"}){
 object body=new{model=name,stream=false,think=false,keep_alive="60s",format=new{type="object",properties=new{comments=new{type="array",minItems=1,maxItems=1,items=new{type="string"}}},required=new[]{"comments"},additionalProperties=false},options=new{num_ctx=2048,num_batch=128,num_predict=120,temperature=0.2,top_p=0.9,seed=20261020+reports.Count},messages=messages};
 string raw=null,error=null;var watch=Stopwatch.StartNew();using(var model=new LocalModel(runtime,name))using(var limit=new CancellationTokenSource(TimeSpan.FromSeconds(180))){try{model.EnsureReady(limit.Token).GetAwaiter().GetResult();raw=model.Chat(body,limit.Token).GetAwaiter().GetResult();}catch(Exception ex){error=ex.GetType().Name+": "+ex.Message;}finally{if(error==null)try{model.Unload().GetAwaiter().GetResult();}catch{}}}
 var row=new{model=name,seconds=Math.Round(watch.Elapsed.TotalSeconds,3),raw=raw,error=error};reports.Add(row);File.WriteAllText(Path.Combine(dir,"generation-only-v8.json"),json.Serialize(new{video=CaptionService.Get(saved,"video"),messages_sent=messages,request_count=reports.Count,polishing=false,model_evaluation=false,runs=reports}));Console.WriteLine(json.Serialize(row));
 if(error!=null)break;
 }
 return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}




