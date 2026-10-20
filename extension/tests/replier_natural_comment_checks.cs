using System;using System.Collections.Generic;using System.IO;using System.Linq;using System.Net;using System.Threading;using System.Threading.Tasks;using System.Web.Script.Serialization;using ReplierDesktop;
public static class NaturalCommentChecks
{
 static void Check(bool ok,string label){if(!ok)throw new Exception(label);Console.WriteLine("PASS "+label);}
 public static int Main(string[] args){try{
 ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
 var video=new Video{Id="V0000000001",Title="새 전략으로 해보는 게임"};
 var content=new VideoContent{Version=1,VideoId=video.Id,Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=Enumerable.Range(0,10).Select(i=>new CaptionCue{StartMs=i*1000,Text="지금은 긴장되지만 다음 방법을 한번 해보겠습니다."}).ToList()};
 var evidence=CommentService.Evidence(content);string key=evidence.Keys.First();
 foreach(var bad in new[]{"이 공포 게임 분위기가 정말 좋네요.","숨이 막히는 것 같은 느낌이네요.","손에 땀이 날 정도로 긴장되네요.","심장이 두근거려서 못 보겠네요.","압도적인 재미를 선사하는 영상이네요."}){
 bool rejected=false;try{CommentService.ParsePlain(string.Join("\n",new[]{bad,"이번엔 어떻게 될지 궁금하네요","한번 시작하면 계속 하게 되겠네요","보기보다 할 게 많네요","이 방법도 한번 해볼 만하겠네요"}),evidence,key,10);}catch(InvalidDataException){rejected=true;}Check(rejected,"unwanted genre or exaggerated review wording rejected");}
 int calls=0;using(var model=new LocalModel("unused")){
 var service=new CommentService(model,(body,t)=>{
 var s=new JavaScriptSerializer();var root=s.DeserializeObject(s.Serialize(body));
 Check(CaptionService.Get(root,"format")==null,"no speculative mood or genre classification call");
 var messages=(object[])CaptionService.Get(root,"messages");string prompt=(string)CaptionService.Get(messages[1],"content");
 Check(!prompt.Contains("공포 게임을 플레이하는 영상이다"),"tense speech does not become a horror premise");
 if(calls==1)Check(!((string)CaptionService.Get(messages[0],"content")).Contains("말투 참고"),"repair removes examples to prevent repeated copying");
 calls++;return Task.FromResult(calls==1 ? "숨이 막히는 것 같네요." : "이 방법은 한번 해볼 만하겠네요 "+new string('가',calls));
 },usePlanning:false);
 var result=service.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();Check(result.Comments.Count==5 && calls==6,"bad phrase repaired without reducing five comments");}
 if(args.Contains("--synthetic-only"))return 0;
 string extension=Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"..",".."));var store=new ContentStore(Path.Combine(extension,"data","replier","content"));
 string[] ids={"oqKGRWJ9TaM","HPUpsEzL1ps"};var serializer=new JavaScriptSerializer();
 var videos=File.ReadLines(Path.Combine(extension,"data","replier","videos.jsonl")).Select(line=>serializer.Deserialize<Video>(line)).Where(v=>ids.Contains(v.Id)).GroupBy(v=>v.Id).Select(g=>g.First()).ToList();
 if(!videos.Any(v=>v.Id=="HPUpsEzL1ps"))videos.Add(new Video{Id="HPUpsEzL1ps",Title="스팀평가 매우긍정적 이상! 꿀잼 인디게임 추천 14종"});
 Check(videos.Count==2,"two actual source videos available for generation review");var records=new List<object>();
 foreach(string name in new[]{"gemma4:e2b-it-qat","qwen3.5:4b"})using(var model=new LocalModel(Path.Combine(extension,".runtime","replier-llm"),name)){
 var service=new CommentService(model,async (body,t)=>{string raw=await model.Chat(body,t);var request=serializer.DeserializeObject(serializer.Serialize(body));if(CaptionService.Get(request,"format")==null)Console.WriteLine("DRAFT "+raw);else if(CaptionService.Get(CaptionService.Get(CaptionService.Get(request,"format"),"properties"),"decision")!=null)Console.WriteLine("NATURAL "+raw);return raw;});
 foreach(var v in videos){var c=store.Load(v.Id) ?? CaptionService.Fetch(v,CancellationToken.None).GetAwaiter().GetResult();
 var result=service.Generate(v,c,CancellationToken.None).GetAwaiter().GetResult();
 Check(result.Comments.Count==5,"five actual comments from "+name+" for "+v.Id);
 foreach(var row in result.Comments)Console.WriteLine(name+" | "+v.Id+" | "+row.Text);
 records.Add(new{model=name,video=v.Id,title=v.Title,comments=result.Comments.Select(r=>new{r.Text,r.Evidence,r.Material}).ToArray()});
 }model.Unload().GetAwaiter().GetResult();}
 string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);File.WriteAllText(Path.Combine(output,"natural-comments-staged.json"),serializer.Serialize(records));return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
