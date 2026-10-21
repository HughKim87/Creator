using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Threading;using System.Diagnostics;using System.Web.Script.Serialization;using ReplierDesktop;
public static class GenerationResumeProbe{
 public static int Main(string[] args){try{
 var root=Path.GetFullPath(args[0]);var json=new JavaScriptSerializer{MaxJsonLength=8*1024*1024};string dir=Path.Combine(root,"extension/data/replier-prompt-probe");var saved=SceneMaterial.Json(File.ReadAllText(Path.Combine(dir,"generation-only-v4.json")));var messages=new List<object>{new{role="system",content=(string)CaptionService.Get(saved,"system_prompt")}};messages.AddRange((object[])CaptionService.Get(saved,"examples"));messages.Add(new{role="user",content=(string)CaptionService.Get(saved,"input")});
 var reports=new List<object>();var runtime=Path.Combine(root,"extension/.runtime/replier-llm");
 foreach(string name in new[]{"qwen3.5:4b","gemma4:e2b-it-qat"}){
 object body=new{model=name,stream=false,think=false,keep_alive="60s",format=new{type="object",properties=new{comments=new{type="array",minItems=3,maxItems=3,items=new{type="string"}}},required=new[]{"comments"},additionalProperties=false},options=new{num_ctx=8192,num_batch=128,num_predict=420,temperature=0.45,top_p=0.9,seed=20261020},messages=messages};
 string raw=null,error=null;var watch=Stopwatch.StartNew();using(var model=new LocalModel(runtime,name))using(var limit=new CancellationTokenSource(TimeSpan.FromSeconds(180))){try{model.EnsureReady(limit.Token).GetAwaiter().GetResult();raw=model.Chat(body,limit.Token).GetAwaiter().GetResult();}catch(Exception ex){error=ex.GetType().Name+": "+ex.Message;}finally{if(error==null)try{model.Unload().GetAwaiter().GetResult();}catch{}}}
 var row=new{model=name,seconds=Math.Round(watch.Elapsed.TotalSeconds,3),raw=raw,error=error};reports.Add(row);File.WriteAllText(Path.Combine(dir,"generation-only-v5.json"),json.Serialize(new{video=CaptionService.Get(saved,"video"),messages_sent=messages,request_count=reports.Count,polishing=false,model_evaluation=false,runs=reports}));Console.WriteLine(json.Serialize(row));
 if(error!=null)break;
 }
 return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}

