using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Threading;using System.Threading.Tasks;using System.Web.Script.Serialization;using ReplierDesktop;
public static class SceneReplayChecks {
 public sealed class Trial {public int run;public double seconds;public bool pass;public CommentSuggestion best;public DualCommentResult result;}
 public sealed class Document {public Video video;public List<Trial> runs;}
 public static int Main(string[] args){try{string root=args[0];var json=new JavaScriptSerializer{MaxJsonLength=16*1024*1024};var runtimes=DualCommentService.Models.ToDictionary(n=>n,n=>new LocalModel(Path.Combine(root,"extension/.runtime/replier-llm"),n));try{
 var chooser=new SceneTieBreaker((n,b,t)=>runtimes[n].Chat(b,t),n=>runtimes[n].Unload());foreach(string id in args.Skip(1)){
 var document=json.Deserialize<Document>(File.ReadAllText(Path.Combine(root,"extension/data/replier-grounded-checks/scene-trials-"+id+".json")));foreach(var trial in document.runs){var rows=trial.result.Batches.Where(b=>b.Result!=null).SelectMany(b=>b.Result.Comments).ToArray();string previous=trial.best==null?"NONE":trial.best.Text;awaited(chooser.Apply(document.video,rows,CancellationToken.None));trial.best=rows.Where(c=>c.FitEligible==true).OrderByDescending(c=>c.FitScore).ThenByDescending(c=>c.TiePreference).FirstOrDefault();Console.WriteLine(id+" run="+trial.run+" BEFORE "+previous+" AFTER "+(trial.best==null?"NONE":trial.best.Text));}
 File.WriteAllText(Path.Combine(root,"extension/data/replier-grounded-checks/scene-ranked-"+id+".json"),json.Serialize(new{video=document.video,runs=document.runs,ranking_replayed=true}));
 }}finally{foreach(var runtime in runtimes.Values.Reverse())runtime.Dispose();}return 0;}catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
 static void awaited(Task task){task.GetAwaiter().GetResult();}
}
