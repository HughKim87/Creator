using System;using System.Collections.Generic;using System.IO;using System.Linq;using System.Threading;using System.Threading.Tasks;using ReplierDesktop;using System.Web.Script.Serialization;
public static class RecoveryChecks
{
 static void Check(bool ok,string label){if(!ok)throw new Exception(label);Console.WriteLine("PASS "+label);}
 static CommentResult Five(){return new CommentResult{Comments=Enumerable.Range(0,5).Select(i=>new CommentSuggestion{Text="구경하는 재미가 있네요 "+i}).ToList()};}
 public static int Main(){try{
 var video=new Video{Id="HPUpsEzL1ps",Title="게임 플레이"};var content=new VideoContent{Version=1,VideoId=video.Id,Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=Enumerable.Range(0,10).Select(i=>new CaptionCue{StartMs=i*1000,Text="게임 분위기와 체력 관리 이야기"}).ToList()};
 var evidence=CommentService.Evidence(content);var id=evidence.Keys.First();
 var normal=new[]{"게임 속 체력 관리가 중요해 보이네요.","가볍게 구경하는 재미가 있네요.","분위기가 꽤 인상적으로 느껴지네요.","시간 가는 줄 모르고 보게 되네요.","이런 스타일도 재미있어 보이네요."};
 Check(CommentService.ParsePlain(string.Join("\n",normal),evidence,id,content.Cues.Count).Comments.Count==5,"game health is not automatically mistaken for personal stamina self-deprecation");
 int writers=0;bool broken=false;
 using(var model=new LocalModel("unused")){
 var service=new CommentService(model,(body,t)=>{
  var serializer=new JavaScriptSerializer();var root=serializer.DeserializeObject(serializer.Serialize(body));
  if(CaptionService.Get(root,"format")!=null)return Task.FromResult("{\"kind\":\"게임 플레이\",\"mood\":\"가벼움\"}");
  writers++;if(broken)return Task.FromResult("제 손이 느려서 따라가기 힘드네요ㅋㅋ");
  if(writers<=2)return Task.FromResult("나이가 들수록 체력이 떨어지네요ㅋㅋ");
  return Task.FromResult("이런 분위기를 구경하는 재미가 있네요 "+new string('가',writers));
 },usePlanning:false);
 var result=service.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();
 Check(result.Comments.Count==5 && writers==7,"two rejected drafts repaired on third attempt without losing other candidates");
 broken=true;int before=writers;bool rejected=false;
 try{service.Generate(video,content,CancellationToken.None,true).GetAwaiter().GetResult();}catch(InvalidDataException){rejected=true;}
 Check(rejected && writers-before==3,"persistent invalid output stops at bounded retry limit");
 Check(object.ReferenceEquals(service.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult(),result),"failed refresh preserves previous validated model cache");
 }
 var events=new List<string>();
 using(var service=new DualCommentService((m,v,c,t,r)=>{events.Add("generate:"+m);return Task.FromResult(Five());},m=>{events.Add("unload:"+m);return Task.FromResult(0);},(v,c,rows,t)=>{events.Add("score");return Task.FromResult(0);})){
 var result=service.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();
 Check(result.Count==10 && events.SequenceEqual(new[]{"generate:gemma4:e2b-it-qat","unload:gemma4:e2b-it-qat","generate:qwen3.5:4b","score","unload:gemma4:e2b-it-qat","unload:qwen3.5:4b"}),"last successful generator remains loaded until scoring then both are released");
 }
 return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}}
}
