using System;using System.Collections.Generic;using System.Linq;using System.Threading;using System.Threading.Tasks;using ReplierDesktop;
public static class DualChecks
{
 static void Check(bool ok,string name){if(!ok)throw new Exception(name);Console.WriteLine("PASS "+name);}
 static CommentResult Five(string model){return new CommentResult{Comments=Enumerable.Range(0,5).Select(i=>new CommentSuggestion{Text=model+" "+i}).ToList()};}
 public static int Main(){try{
  var events=new List<string>();
  using(var service=new DualCommentService((name,v,c,t,r)=>{events.Add(name+":"+r);return Task.FromResult(Five(name));},name=>{events.Add("unload:"+name);return Task.FromResult(0);})){
   var result=service.Generate(new Video(),new VideoContent(),CancellationToken.None,true).GetAwaiter().GetResult();
   Check(result.Count==10 && result.Batches.Count==2 && result.Batches.All(b=>b.Result.Comments.Count==5),"two model outputs retain five candidates each");
   Check(result.Batches.Select(b=>b.Label).SequenceEqual(new[]{"Gemma","Qwen"}),"source labels stay associated with model results");
   Check(events.SequenceEqual(new[]{"gemma4:e2b-it-qat:True","unload:gemma4:e2b-it-qat","qwen3.5:4b:True","unload:qwen3.5:4b"}),"refresh reaches both models and unload precedes next model");
  }
  using(var service=new DualCommentService((name,v,c,t,r)=>{if(name.StartsWith("qwen"))throw new InvalidOperationException("test failure");return Task.FromResult(Five(name));})){
   var result=service.Generate(new Video(),new VideoContent(),CancellationToken.None).GetAwaiter().GetResult();
   Check(result.Count==5 && result.Batches[1].Error=="test failure" && result.Batches[1].Result==null,"one model failure retains successful five without inventing ten");
  }
  var stop=new CancellationTokenSource();
  using(var service=new DualCommentService((name,v,c,t,r)=>{if(name.StartsWith("qwen")){stop.Cancel();t.ThrowIfCancellationRequested();}return Task.FromResult(Five(name));})){
   var result=service.Generate(new Video(),new VideoContent(),stop.Token).GetAwaiter().GetResult();
   Check(result.Cancelled && result.Count==5 && result.Batches.Count==1,"cancelling second model preserves already completed first model");
  }
  return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex.Message);return 1;}}
}