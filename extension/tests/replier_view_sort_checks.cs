using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using ReplierDesktop;
public static class ViewSortChecks
{
 static void Check(bool ok,string name){if(!ok)throw new Exception(name);Console.WriteLine("PASS "+name);}
 public static int Main(string[] args){try{
  Check(ViewCounts.Parse("조회수 139,047회")==139047,"full Korean count");
  Check(ViewCounts.Parse("조회수 1.2만회")==12000 && ViewCounts.Parse("2.3억회")==230000000,"Korean abbreviated counts");
  Check(ViewCounts.Parse("1.5천회")==1500 && ViewCounts.Parse("2.4M views")==2400000 && ViewCounts.Parse("1.1K views")==1100,"thousands and English abbreviations");
  Check(ViewCounts.Parse("조회수 없음")==0 && ViewCounts.Parse("No views")==0,"explicit zero counts");
  Check(ViewCounts.Parse(null)==-1 && ViewCounts.Parse("미제공")==-1 && ViewCounts.Parse("시청 중 123명")==-1,"unknown counts and live viewers are not treated as views");
  Check(ViewCounts.Parse("99999999999999999999999999999999999억회")==-1,"overflow rejected");
  string run=Path.Combine(Path.GetFullPath(args[0]),"run-"+Guid.NewGuid().ToString("N"));
  Directory.CreateDirectory(run);
  var raw=Enumerable.Range(0,15).Select(i=>new Video{Id="S"+i.ToString("D10"),Title="순서 검사 "+i,ViewCountText=i==14?"미제공":"조회수 "+(i*1000)+"회"}).ToList();
  var result=VideoBatch.Collect("검사",new VideoLedger(Path.Combine(run,"history.jsonl")),new ContentStore(Path.Combine(run,"content")),CancellationToken.None,
   search:(q,t)=>Task.FromResult(raw),captions:(v,t)=>{
    if(v.Id==raw[13].Id)throw new ContentUnavailable("검사용 자막 없음");
    return Task.FromResult(new VideoContent{Version=1,VideoId=v.Id,Language="ko",IsAuto=true,Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=new List<CaptionCue>{new CaptionCue{StartMs=0,DurationMs=1000,Text="검사 대사"}}});
   }).GetAwaiter().GetResult();
  Check(result.Videos.Count==10 && result.Videos.Select(v=>v.Id).SequenceEqual(raw.Skip(3).Take(10).Reverse().Select(v=>v.Id)),"higher-view candidates selected first with caption failures skipped and descending display order");
  var equal=VideoBatch.Collect("동률",new VideoLedger(Path.Combine(run,"equal.jsonl")),new ContentStore(Path.Combine(run,"equal-content")),CancellationToken.None,
   search:(q,t)=>Task.FromResult(new List<Video>{raw[14],new Video{Id="S9999999999",Title="동률",ViewCountText="조회수 0회"},raw[0]}),
   captions:(v,t)=>Task.FromResult(new VideoContent{Version=1,VideoId=v.Id,Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=new List<CaptionCue>{new CaptionCue{Text="검사 대사"}}})).GetAwaiter().GetResult();
  Check(equal.Videos[0].Id=="S9999999999" && equal.Videos[1].Id==raw[0].Id && equal.Videos[2].Id==raw[14].Id,"ties keep source order and missing counts sort last");
  return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}}
}
