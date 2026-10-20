using System;using System.IO;using System.Collections.Generic;using System.Linq;using System.Threading;using System.Web.Script.Serialization;using ReplierDesktop;
public class QualityActualChecks {
 class Sample {public string Title,Caption,Text;public bool Good;}
 public static int Main(string[] a){try{
 string root=a[0];var json=new JavaScriptSerializer();var samples=new[]{
 new Sample{Title="무료 게임 추천",Caption="스팀 여름 세일이 끝났습니다. 그래서 무료로 즐길 게임들을 추천합니다.",Text="게임 끝났는데도 계속 만들어져서 재밌네요 ㅋㅋ"},
 new Sample{Title="보호막 패치",Caption="이번 패치로 보호막의 체력 계수가 올랐습니다. 체력 자체는 그대로입니다.",Text="체력이 늘어나서 이제 든든하네요"},
 new Sample{Title="게임 할인 추천",Caption="목숨값이 천 원이면 거저죠. 현실적인 바이크 시뮬레이션 게임인데요.",Text="이 정도면 목숨값도 이 정도는 이해할 만하죠"},
 new Sample{Title="무료 게임 추천",Caption="유료보다 재밌는 스팀 무료 게임들을 소개합니다.",Text="유료보다 재밌는 무료 게임 찾는 게 핵심이군요"},
 new Sample{Title="직접 정비하는 운전 게임",Caption="이 게임은 바이크를 운전하면서 정비도 직접 해야 합니다.",Text="운전만 하면 되는 줄 알았는데 정비까지 해야 하네요 ㅋㅋ",Good=true},
 new Sample{Title="보호막 패치",Caption="이번 패치로 보호막의 체력 계수가 올랐습니다.",Text="보호막 버프는 반갑네요. 좀 더 든든하겠어요",Good=true}
 };
 var results=new List<FitAssessment[]>();foreach(string name in DualCommentService.Models)using(var model=new LocalModel(Path.Combine(root,"extension/.runtime/replier-llm"),name)){
 var scorer=new FitScoring(model);var list=new List<FitAssessment>();foreach(var s in samples){var content=new VideoContent{Version=1,VideoId="V0000000001",Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=new List<CaptionCue>{new CaptionCue{Text=s.Caption}}};var c=new CommentSuggestion{Text=s.Text,CueId="c0",GroundingQuote=s.Caption};var r=scorer.Assess(new Video{Id=content.VideoId,Title=s.Title},content,new[]{c},CancellationToken.None).GetAwaiter().GetResult()[0];if(ViewerQuality.Problem(s.Text)!=null)r.Eligible=false;list.Add(r);Console.WriteLine(name+" | "+r.Eligible+" | "+s.Text+" | "+r.Reason);}
 results.Add(list.ToArray());model.Unload().GetAwaiter().GetResult();
 }
 var records=samples.Select((s,i)=>new{s.Title,s.Caption,s.Text,s.Good,gemma=results[0][i],qwen=results[1][i],approved=results.All(r=>r[i].Eligible)}).ToArray();string dir=Path.Combine(root,"extension/data/replier-grounded-checks");Directory.CreateDirectory(dir);File.WriteAllText(Path.Combine(dir,"quality-challenges.json"),json.Serialize(records));
 if(records.Any(r=>r.approved!=r.Good))throw new Exception("actual quality decision did not match reviewed expectation");Console.WriteLine("PASS four reviewed bad comments rejected and two grounded natural reactions accepted by both actual models");return 0;
 }catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}
