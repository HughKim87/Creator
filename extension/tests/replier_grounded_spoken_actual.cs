using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Threading;using System.Diagnostics;using System.Web.Script.Serialization;using ReplierDesktop;
public static class GroundedSpokenActual {
 public static int Main(string[] args){try{string root=args[0],dir=Path.Combine(root,"extension/data/replier-grounded-checks"),runtime=Path.Combine(root,"extension/.runtime/replier-llm");var json=new JavaScriptSerializer{MaxJsonLength=16*1024*1024};
 var baseline=json.Deserialize<AudienceActualChecks.Baseline>(File.ReadAllText(Path.Combine(dir,"audience-baseline-dIRksYUQz6Y.json")));var content=new ContentStore(Path.Combine(root,"extension/data/replier/content")).Load(baseline.video.Id);
 var snapshot=SceneMaterial.Json(File.ReadAllText(Path.Combine(dir,"audience-condition-grounded-dIRksYUQz6Y.json")));var result=json.Deserialize<DualCommentResult>(json.Serialize(CaptionService.Get(snapshot,"after")));var existing=result.Batches.Where(b=>b.Result!=null).SelectMany(b=>b.Result.Comments).ToArray();var proof=existing.First().Material;
 var regressions=new[]{new CommentSuggestion{Text="피 없는 데가 따로 있다는데 그게 핵심이네",Material=proof},new CommentSuggestion{Text="피 없는 데 찾아서 실수한 건 진짜 위험했네",Material=proof},new CommentSuggestion{Text="피진 마린으로 이겼네, 진짜 놀라워.",Material=proof}};
 var rows=existing.Concat(regressions).ToArray();var watch=Stopwatch.StartNew();
 using(var g=new LocalModel(runtime,DualCommentService.Models[0]))using(var q=new LocalModel(runtime,DualCommentService.Models[1])){
 var scores=new CombinedFitScoring(new FitScoring(g),new FitScoring(q),g.Unload);scores.Evaluate(baseline.video,content,rows,CancellationToken.None).GetAwaiter().GetResult();
 var selector=new SceneTieBreaker((model,body,t)=>q.Chat(body,t),model=>TaskFrom(),true);selector.Apply(baseline.video,existing,CancellationToken.None).GetAwaiter().GetResult();q.Unload().GetAwaiter().GetResult();}
 var best=existing.Where(c=>c.FitEligible==true).OrderByDescending(c=>c.TiePreference).ThenByDescending(c=>c.FitScore).FirstOrDefault();var wrong=existing.First(c=>c.Text=="시간 제한 걸고도 못 깨는 것 같아 ㅋㅋ");
 bool pass=regressions.All(c=>c.FitEligible==false)&&wrong.FitEligible==false&&best!=null&&best.Text.Length<=38;
 File.WriteAllText(Path.Combine(dir,"grounded-spoken-existing-replay-dIRksYUQz6Y.json"),json.Serialize(new{video=baseline.video,result=result,best=best,regressions=regressions,pass=pass,seconds=watch.Elapsed.TotalSeconds,new_comment_generation=false}));
 File.WriteAllText(Path.Combine(dir,"grounded-spoken-final-debug-dIRksYUQz6Y.txt"),CommentDebugReport.Format(baseline.video,result,best,"기존 후보 재평가",""));
 foreach(var row in rows)Console.WriteLine(row.FitScore+" | "+row.FitEligible+" | "+row.Text+" | "+row.FitError);Console.WriteLine("FINAL "+(best==null?"NONE":best.Text)+" seconds="+watch.Elapsed.TotalSeconds.ToString("F1"));Console.WriteLine(pass?"PASS existing misread candidates rejected and final natural comment retained":"FAIL review real judgment");return pass?0:1;
 }catch(Exception e){Console.WriteLine(e);return 1;}}
 static System.Threading.Tasks.Task TaskFrom(){return System.Threading.Tasks.Task.FromResult(0);}
}