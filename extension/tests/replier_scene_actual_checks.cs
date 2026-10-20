using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Threading;using System.Diagnostics;using System.Web.Script.Serialization;using ReplierDesktop;
public static class SceneActualChecks {
 public static int Main(string[] args){try{
 string root=Path.GetFullPath(args[0]),id=args.Length>1?args[1]:"dXWu3pyxmSU";int count=args.Length>2?int.Parse(args[2]):5;string prefix=args.Length>3?args[3]:"scene-trials-";var json=new JavaScriptSerializer{MaxJsonLength=16*1024*1024};
 var titles=new Dictionary<string,string>{{"dXWu3pyxmSU","200렙 찍자마자 750만원 혼줌작 때려서 만든 미친매물 ㅋㅋㅋㅋㅋㅋㅋ"},{"e7QJZTlIUbI","99% 압도적으로 긍정적? 유료보다 재밌는 무료 스팀게임 추천 모음집"},{"CFYOk550ckc","역대급 눈물겨운 120만원 배틀그라운드‘한정판 벤틀리 스킨’ㅋㅋ 이쁜데요?!"}};
 var video=new Video{Id=id,Title=titles[id]};var content=new ContentStore(Path.Combine(root,"extension/data/replier/content")).Load(id);if(content==null)throw new Exception("Missing saved public captions");var records=new List<object>();bool passed=true;
 DualCommentService service=null;try{for(int run=0;run<count;run++){
 if(run==0 || run==3){if(service!=null)service.Dispose();service=new DualCommentService(Path.Combine(root,"extension/.runtime/replier-llm"));}
 Console.WriteLine("START "+id+" run="+(run+1));var watch=Stopwatch.StartNew();var result=service.Generate(video,content,CancellationToken.None,run>0).GetAwaiter().GetResult();
 var rows=result.Batches.Where(b=>b.Result!=null).SelectMany(b=>b.Result.Comments).ToArray();var best=rows.Where(c=>c.FitEligible==true).OrderByDescending(c=>c.FitScore).ThenByDescending(c=>c.TiePreference).FirstOrDefault();
 foreach(var batch in result.Batches){Console.WriteLine(batch.Label+" error="+batch.Error);if(batch.Result!=null){Console.WriteLine(batch.Result.ContextSummary);foreach(var row in batch.Result.Comments)Console.WriteLine(batch.Label+" | "+row.FitScore+" | "+row.Text);}}
 Console.WriteLine("BEST "+(best==null?"NONE":best.Text)+" seconds="+watch.Elapsed.TotalSeconds.ToString("F1")+" error="+result.ScoreError);
 bool ok=result.Complete&&!result.Cancelled&&string.IsNullOrEmpty(result.ScoreError)&&result.Batches.All(b=>string.IsNullOrEmpty(b.Error))&&best!=null;passed&=ok;
 records.Add(new{run=run+1,seconds=watch.Elapsed.TotalSeconds,pass=ok,best=best,result=result});string dir=Path.Combine(root,"extension/data/replier-grounded-checks");Directory.CreateDirectory(dir);File.WriteAllText(Path.Combine(dir,prefix+id+".json"),json.Serialize(new{video=video,runs=records}));
 }}finally{if(service!=null)service.Dispose();}Console.WriteLine((passed?"PASS":"FAIL")+" "+count+" fresh generations; semantic quality requires review of every saved winner");return passed?0:1;
 }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
