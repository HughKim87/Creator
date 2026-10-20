using System;using System.Diagnostics;using System.IO;using System.Linq;using System.Threading;using System.Threading.Tasks;using System.Web.Script.Serialization;using ReplierDesktop;
public static class LatencyChecks{
 sealed class Progress:IProgress<DualCommentResult>{public Action<DualCommentResult> Changed;public void Report(DualCommentResult r){Changed(r);}}
 public static int Main(string[] args){try{
 string root=Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"..",".."));string id="oqKGRWJ9TaM";
 var content=new ContentStore(Path.Combine(root,"data","replier","content")).Load(id);if(content==null)throw new Exception("Cached source missing");
 var timer=Stopwatch.StartNew();double five=-1,ten=-1;var progress=new Progress{Changed=r=>{if(r.Count>=5 && five<0)five=timer.Elapsed.TotalSeconds;if(r.Count==10 && ten<0)ten=timer.Elapsed.TotalSeconds;}};
 using(var service=new DualCommentService(Path.Combine(root,".runtime","replier-llm"))){
 double warmSeconds=0;if(args[1].Contains("prepared")){service.PrepareFirst(CancellationToken.None).GetAwaiter().GetResult();warmSeconds=timer.Elapsed.TotalSeconds;timer.Restart();}
 var result=service.Generate(new Video{Id=id,Title="게임 영상"},content,CancellationToken.None,false,progress).GetAwaiter().GetResult();
 timer.Stop();foreach(var batch in result.Batches)Console.WriteLine(batch.Label+" "+batch.Error);
 if(result.Count!=10 || result.Cancelled || result.ScoreError!="")throw new Exception("incomplete comments or scores");
 var measured=new{sample=args[1],video=id,warmup=Math.Round(warmSeconds,2),firstFive=Math.Round(five,2),allTen=Math.Round(ten,2),completed=Math.Round(timer.Elapsed.TotalSeconds,2)};
 string json=new JavaScriptSerializer().Serialize(measured);Console.WriteLine(json);Directory.CreateDirectory(args[0]);File.WriteAllText(Path.Combine(args[0],args[1]+".json"),json);
 }return 0;}catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}}
