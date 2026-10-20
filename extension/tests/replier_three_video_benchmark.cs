using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Diagnostics;using System.Threading;using System.Web.Script.Serialization;using ReplierDesktop;
public static class ThreeVideoBenchmark {
 sealed class Progress:IProgress<DualCommentResult>{
  public string Current;readonly Stopwatch watch;double last;public List<object> Phases=new List<object>();
  public Progress(Stopwatch w){watch=w;}
  public void Report(DualCommentResult r){if(r.ActiveModel==Current)return;double now=watch.Elapsed.TotalSeconds;if(Current!=null)Phases.Add(new{phase=Current,seconds=Math.Round(now-last,3)});Current=r.ActiveModel;last=now;Console.WriteLine("PHASE "+Current+" elapsed="+now.ToString("F1")+" candidates="+r.Count);}
 }
 public static int Main(string[] args){try{
 string root=Path.GetFullPath(args[0]),dir=Path.Combine(root,"extension/data/replier-grounded-checks"),runtime=Path.Combine(root,"extension/.runtime/replier-llm"),log=Path.Combine(root,"extension/data/replier/llm-diagnostics.jsonl");var j=new JavaScriptSerializer{MaxJsonLength=16*1024*1024};var reports=new List<object>();
 string[] ids={"dXWu3pyxmSU","CFYOk550ckc","e7QJZTlIUbI"};
 using(var service=new DualCommentService(runtime,false)){
 foreach(string id in ids){
 var fixture=SceneMaterial.Json(File.ReadAllText(Path.Combine(dir,"scene-final-"+id+".json")));var video=j.Deserialize<Video>(j.Serialize(CaptionService.Get(fixture,"video")));var started=DateTime.UtcNow;var watch=Stopwatch.StartNew();var progress=new Progress(watch);DualCommentResult result=null;string error=null;
 Console.WriteLine("START "+id+" "+video.Title);
 using(var limit=new CancellationTokenSource(TimeSpan.FromSeconds(180)))try{
 var content=new ContentStore(Path.Combine(root,"extension/data/replier/content")).Load(id);if(content==null)throw new Exception("Saved public captions missing");
 result=service.Generate(video,content,limit.Token,true,progress).GetAwaiter().GetResult();
 }catch(Exception ex){error=ex.GetType().Name+": "+ex.Message;}
 watch.Stop();var rows=result==null?new CommentSuggestion[0]:result.Batches.Where(b=>b.Result!=null).SelectMany(b=>b.Result.Comments).ToArray();var best=rows.Where(c=>c.FitEligible==true).OrderByDescending(c=>c.TiePreference).ThenByDescending(c=>c.FitScore).FirstOrDefault();
 var diagnostics=new List<object>();foreach(var line in File.ReadAllLines(log)){try{var item=SceneMaterial.Json(line);DateTime at;if(DateTime.TryParse(CaptionService.Get(item,"at") as string,null,System.Globalization.DateTimeStyles.RoundtripKind,out at)&&at.ToUniversalTime()>=started)diagnostics.Add(item);}catch(ArgumentException){}}
 double model=diagnostics.Sum(d=>Number(d,"seconds")),load=diagnostics.Sum(d=>Number(d,"loadSeconds")),prompt=diagnostics.Sum(d=>Number(d,"promptSeconds")),generation=diagnostics.Sum(d=>Number(d,"generationSeconds"));
 bool completed=result!=null&&result.Complete&&!result.Cancelled&&string.IsNullOrEmpty(result.ScoreError)&&result.Batches.Count==2&&result.Batches.All(b=>b.Result!=null&&string.IsNullOrEmpty(b.Error))&&best!=null;
 var record=new{video=video,seconds=Math.Round(watch.Elapsed.TotalSeconds,3),completed=completed,error=error,result=result,best=best,cached_captions=true,fresh_generation=true,phases=progress.Phases,metrics=new{calls=diagnostics.Count,model_seconds=model,load_seconds=load,prompt_seconds=prompt,output_seconds=generation},diagnostics=diagnostics};
 reports.Add(record);File.WriteAllText(Path.Combine(dir,"three-video-benchmark-"+id+".json"),j.Serialize(record));File.WriteAllText(Path.Combine(dir,"three-video-benchmark-"+id+"-debug.txt"),CommentDebugReport.Format(video,result,best,"실제 전체 생성·평가 측정",error??""));File.WriteAllText(Path.Combine(dir,"three-video-benchmark-latest.json"),j.Serialize(new{runs=reports}));
 Console.WriteLine("FINAL "+id+" seconds="+watch.Elapsed.TotalSeconds.ToString("F1")+" completed="+completed+" candidates="+rows.Length+" eligible="+rows.Count(c=>c.FitEligible==true)+" calls="+diagnostics.Count+" load="+load.ToString("F1")+" prompt="+prompt.ToString("F1")+" output="+generation.ToString("F1"));
 Console.WriteLine("BEST "+(best==null?"NONE":best.Text));if(best!=null){Console.WriteLine("FACT "+CaptionService.Get(SceneMaterial.Json(best.Material),"writing_fact"));Console.WriteLine("QUOTE "+best.GroundingQuote);Console.WriteLine("REASON "+best.FitReason);}
 if(result!=null)foreach(var b in result.Batches)Console.WriteLine("MODEL "+b.Label+" error="+b.Error);Console.WriteLine("ERROR "+(error??(result==null?"":result.ScoreError)));
 }
 }
 return 0;
 }catch(Exception e){Console.WriteLine(e);return 1;}}
 static double Number(object item,string key){double d;return double.TryParse(Convert.ToString(CaptionService.Get(item,key)),out d)?d:0;}
}