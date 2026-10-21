using System;using System.Collections.Generic;using System.IO;using System.Linq;using System.Threading;using System.Web.Script.Serialization;using ReplierDesktop;
public static class GroundedActualChecks
{
 public static int Main(string[] args){try{
 string extension=Path.GetFullPath(Path.Combine(args[0],"..",".."));
 var real=new ContentStore(Path.Combine(extension,"data","replier","content")).Load("oqKGRWJ9TaM");
 if(real==null)throw new Exception("saved public caption fixture missing");
 using(var service=new DualCommentService(args[0])){
  var watch=System.Diagnostics.Stopwatch.StartNew();
  var result=service.Generate(new Video{Id=real.VideoId,Title="다이애나는 더이상 암살자가 아닙니다. W체력 계수 버프로 AP크산테가 되어버린 몸짱 강심 다이애나 전략"},real,CancellationToken.None).GetAwaiter().GetResult();
  foreach(var batch in result.Batches){Console.WriteLine(batch.Label+" error="+batch.Error);if(batch.Result!=null)foreach(var c in batch.Result.Comments)Console.WriteLine(batch.Label+" | "+c.Text+" | "+c.FitScore+" | "+c.FitReason);}
  watch.Stop();Console.WriteLine("SCORE_ERROR="+result.ScoreError+" ACCEPTED="+result.Count+" SECONDS="+watch.Elapsed.TotalSeconds.ToString("F1"));
  Directory.CreateDirectory(args[1]);File.WriteAllText(Path.Combine(args[1],"grounded-actual.json"),new JavaScriptSerializer().Serialize(result));
  foreach(var c in result.Batches.Where(b=>b.Result!=null).SelectMany(b=>b.Result.Comments)){
   CommentPipeline.ValidateReaction(c.Text,c.Material);
   if(!FastComments.HasGrounding(c.Text,c.Material) || !c.FitScore.HasValue)throw new Exception("unvalidated candidate escaped");
  }

  if(result.Count<1 || result.Count>10 || !result.Complete || result.ScoreError.Length>0 || result.Batches.Any(b=>b.Error.Length>0))throw new Exception("actual title-caption generation/grading incomplete");
 }
 return 0;}catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
