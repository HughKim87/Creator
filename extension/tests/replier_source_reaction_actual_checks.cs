using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Threading;using System.Diagnostics;using System.Web.Script.Serialization;using ReplierDesktop;
public static class SourceReactionActualChecks {
 public static int Main(string[] args){try{
 var root=Path.GetFullPath(args[0]);var json=new JavaScriptSerializer{MaxJsonLength=8*1024*1024};
 var videos=File.ReadLines(Path.Combine(root,"extension/data/replier/videos.jsonl")).Select(s=>json.Deserialize<Video>(s)).GroupBy(v=>v.Id).ToDictionary(g=>g.Key,g=>g.First());
 videos["oqKGRWJ9TaM"]=new Video{Id="oqKGRWJ9TaM",Title="다이애나는 더이상 암살자가 아닙니다. W체력 계수 버프로 AP크산테가 되어버린 몸짱 강심 다이애나 전략"};
 videos["CFYOk550ckc"]=new Video{Id="CFYOk550ckc",Title="역대급 눈물겨운 120만원 배틀그라운드‘한정판 벤틀리 스킨’ㅋㅋ 이쁜데요?!",Channel="김블루"};
 videos["HPUpsEzL1ps"]=new Video{Id="HPUpsEzL1ps",Title="스팀평가 매우긍정적 이상! 꿀잼 인디게임 추천 14종"};
 var store=new ContentStore(Path.Combine(root,"extension/data/replier/content"));var records=new List<object>();
 string dir=Path.Combine(root,"extension/data/replier-grounded-checks");Directory.CreateDirectory(dir);
 using(var service=new DualCommentService(Path.Combine(root,"extension/.runtime/replier-llm"))){foreach(string id in (args.Length>1 ? args.Skip(1).ToArray() : new[]{"oqKGRWJ9TaM","e7QJZTlIUbI","a6gmZ8duxLE","M4QmBRPnoKc"})){
 var video=videos[id];var content=store.Load(id);if(content==null)throw new Exception("missing saved public caption "+id);
 Console.WriteLine("START "+id+" "+video.Title);var watch=Stopwatch.StartNew();
 var result=service.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();
 foreach(var batch in result.Batches){Console.WriteLine("BATCH "+batch.Label+" "+batch.Error);if(batch.Result!=null)foreach(var c in batch.Result.Comments){if(string.IsNullOrEmpty(c.GroundingQuote)||!c.Evidence.Contains(c.GroundingQuote))throw new Exception("literal quote lost");Console.WriteLine(batch.Label+" | "+c.FitScore+" | "+c.Text+" | "+c.GroundingQuote);}}
 var eligible=result.Batches.Where(b=>b.Result!=null).SelectMany(b=>b.Result.Comments).Where(c=>c.FitEligible==true).OrderByDescending(c=>c.FitScore).ToList();
 Console.WriteLine("BEST "+(eligible.Count==0?"NONE":eligible[0].Text));
 records.Add(new{video=video,seconds=watch.Elapsed.TotalSeconds,best=eligible.FirstOrDefault(),result=result});File.WriteAllText(Path.Combine(dir,args.Length>1 ? "quality-target-"+args[1]+".json" : "quality-actual-videos.json"),json.Serialize(records));
 if(!result.Complete || eligible.Count==0 || !string.IsNullOrEmpty(result.ScoreError) || result.Batches.Any(b=>!string.IsNullOrEmpty(b.Error)))throw new Exception("generation/scoring failure: "+result.ScoreError);
 Console.WriteLine("PASS "+id+" count="+result.Count+" seconds="+watch.Elapsed.TotalSeconds.ToString("F1"));
 }}return 0;}catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
