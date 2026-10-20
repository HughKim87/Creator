using System;using System.Diagnostics;using System.IO;using System.Threading;using ReplierDesktop;
public static class PipelinePerformance
{
 public static int Main(string[] args){try{
 string extension=Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"..",".."));
 string id=args.Length>0?args[0]:"oqKGRWJ9TaM";
 var content=new ContentStore(Path.Combine(extension,"data","replier","content")).Load(id);
 if(content==null)throw new Exception("Cached captions missing");
 var video=new Video{Id=id,Title="게임 플레이 영상"};
 var stop=new CancellationTokenSource(TimeSpan.FromSeconds(150));var watch=Stopwatch.StartNew();
 using(var service=new DualCommentService(Path.Combine(extension,".runtime","replier-llm"))){
 var result=service.Generate(video,content,stop.Token).GetAwaiter().GetResult();
 foreach(var batch in result.Batches)Console.WriteLine("MODEL "+batch.Label+" COUNT "+(batch.Result==null?0:batch.Result.Comments.Count)+" ERROR "+batch.Error);
 Console.WriteLine("TOTAL "+result.Count+" CANCELLED "+result.Cancelled+" SCORE_ERROR "+result.ScoreError+" SECONDS "+watch.Elapsed.TotalSeconds.ToString("F1"));
 return result.Cancelled?2:0;
 }
 }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}}
}
