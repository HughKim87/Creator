using System;using System.Linq;using System.Collections.Generic;using System.Threading;using System.Threading.Tasks;using System.Web.Script.Serialization;using ReplierDesktop;
public static class WritingContextChecks {
 static readonly JavaScriptSerializer J=new JavaScriptSerializer();
 static void Check(bool b,string s){if(!b)throw new Exception(s);Console.WriteLine("PASS "+s);}
 static object Req(object body){return SceneMaterial.Json(J.Serialize(body));}
 static object Last(object req){return SceneMaterial.Json((string)CaptionService.Get(((object[])CaptionService.Get(req,"messages")).Last(),"content"));}
 public static int Main(){try{
 var video=new Video{Id="V0000000001",Title="클럽에서 인사하기"};
 var cues=new Dictionary<string,CaptionCue>{{"c0",new CaptionCue{Text="인사를 했는데 대답이 없어요.",StartMs=1000}},{"c1",new CaptionCue{Text="여기는 춤추는 게 끝이에요.",StartMs=9000}}};
 var scene=new SceneReading{EvidenceIds=cues.Keys.ToArray(),Angles=new string[0]};
 var materials=cues.ToDictionary(e=>e.Key,e=>J.Serialize(new{context_version=2,scene=scene,title=video.Title,caption=e.Value.Text,writing_quote=e.Value.Text,writing_fact=e.Key=="c0"?"인사를 해도 대답이 없다":"여기는 춤만 추는 곳이다",raw_sources=new[]{new{cue_id="c9",text="제공하지 않은 보스가 등장한다"}}}));
 var content=new VideoContent{Version=1,VideoId=video.Id,Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=cues.Values.Concat(new[]{new CaptionCue{Text="제공하지 않은 보스가 등장한다",StartMs=30000}}).ToList()};
 string actual=null;object[] whole=null;int writes=0;CommentSuggestion row;
 var drafts=new[]{"춤만 추는 곳이면 말 걸기 더 어렵겠네ㅋㅋ","대답 없는데 인사는 포기 안 하네ㅋㅋ","들어가자마자 어색한 공기 느껴짐ㅋㅋ","채팅부터 꺼내면 눈치 보이겠다ㅋㅋ","서로 말없이 춤추는 것도 웃기네ㅋㅋ"};
 using(var m=new LocalModel("unused")){
 var writer=new SceneWriter(m,(b,t)=>{var input=Last(Req(b));if(writes==0){actual=(string)CaptionService.Get(input,"actual_context");whole=(object[])CaptionService.Get(input,"whole_context");}Check(!J.Serialize(input).Contains("보스"),"unselected raw source is not writing evidence");return Task.FromResult(J.Serialize(new{comments=new[]{drafts[writes++]}}));});
 var generated=writer.Generate(cues,materials,new string[0],CancellationToken.None,(text,id,k)=>new CommentSuggestion{Text=text,CueId=id,StartMs=cues[id].StartMs,Evidence=cues[id].Text},3).GetAwaiter().GetResult();row=generated.Comments[0];
 Check(writes==5&&generated.Comments.Count==5,"no new writing calls or candidates");var saved=WritingContext.Read(row.Material);
 Check(J.Serialize(whole)==J.Serialize(WritingContext.Request(saved))&&actual==saved.First(e=>e.Cue==row.CueId).Fact,"stored context exactly matches the actual writing request");
 Check(saved[1].Cue=="c1"&&saved[1].Quote=="여기는 춤추는 게 끝이에요."&&saved[1].StartMs==9000,"secondary source keeps its exact original quote and timestamp");
 var before=row.Material;new ScenePolisher(m,(b,t)=>Task.FromResult(J.Serialize(new{comments=new[]{row.Text}}))).Apply(new[]{row},CancellationToken.None).GetAwaiter().GetResult();Check(row.Material==before,"surface editing retains writing context");
 }
 cues["c1"].Text="나중에 바뀐 입력";materials["c1"]="{}";
 var calls=new Dictionary<string,int>();
 Func<string,Func<object,CancellationToken,Task<string>>> sender=name=>(body,t)=>{
 t.ThrowIfCancellationRequested();if(!calls.ContainsKey(name))calls[name]=0;calls[name]++;
 var req=Req(body);var props=CaptionService.Get(CaptionService.Get(req,"format"),"properties");
 if(CaptionService.Get(props,"voices")!=null)return Task.FromResult("{\"voices\":[{\"id\":0,\"voice\":\"viewer\"}]}");
 if(CaptionService.Get(props,"added_fact")!=null){var input=Last(req);Check((string)CaptionService.Get(input,"comment")==row.Text,"judge receives the exact candidate");Check((string)CaptionService.Get(input,"fact")==actual&&J.Serialize(CaptionService.Get(input,"whole_context"))==J.Serialize(whole),name+" receives primary AND secondary facts supplied to writer");return Task.FromResult("{\"added_fact\":\"\",\"meaning_clear\":true,\"reason\":\"춤추는 장소에 대한 반응\"}");}
 var msgs=(object[])CaptionService.Get(req,"messages");var text=(string)CaptionService.Get(msgs[msgs.Length-3],"content");var input2=SceneMaterial.Json(text.Substring("영상 참고자료: ".Length));var transcript=(object[])CaptionService.Get(input2,"transcript");
 Check(transcript.Length==2&&(string)CaptionService.Get(transcript[1],"text")=="여기는 춤추는 게 끝이에요."&&!text.Contains("보스")&&!text.Contains("나중에"),name+" relation evidence uses the frozen quotes, not unseen video context");
 return Task.FromResult(J.Serialize(new{evaluated_comment=row.Text,focus="클럽에서 인사",evidence=1,source_role="central_event",conflicts=false,explanation="작성에 제공한 두 번째 구간에 대한 반응"}));};
 using(var g=new LocalModel("unused",DualCommentService.Models[0]))using(var q=new LocalModel("unused",DualCommentService.Models[1])){
 var combined=new CombinedFitScoring(new FitScoring(g,sender(g.Name)),new FitScoring(q,sender(q.Name)),()=>Task.FromResult(0));combined.Evaluate(video,content,new[]{row},CancellationToken.None).GetAwaiter().GetResult();
 if(row.FitEligible!=true)Console.WriteLine(row.FitError+"\n"+row.FitReason);Check(row.FitEligible==true&&calls[g.Name]==3&&calls[q.Name]==3,"both judges retain the existing three calls, without extra inspections");Check(row.FitReason.Contains("여기는 춤추는 게 끝이에요."),"debug preserves the secondary real quote");
 var bad=new CommentSuggestion{Text="보스가 갑자기 튀어나오네ㅋㅋ",CueId=row.CueId,Material=row.Material,GroundingQuote=row.GroundingQuote};int badCalls=0;
 var review=new FitScoring(g,(b,t)=>{badCalls++;var req=Req(b);var props=CaptionService.Get(CaptionService.Get(req,"format"),"properties");if(CaptionService.Get(props,"voices")!=null)return Task.FromResult("{\"voices\":[{\"id\":0,\"voice\":\"viewer\"}]}");Check(!J.Serialize(CaptionService.Get(Last(req),"whole_context")).Contains("보스"),"unseen event cannot be borrowed from the rest of the video");return Task.FromResult("{\"added_fact\":\"보스가 등장함\",\"meaning_clear\":true,\"reason\":\"작성에 없는 사건\"}");}).Assess(video,content,new[]{bad},CancellationToken.None).GetAwaiter().GetResult();Check(!review[0].Eligible&&badCalls==2,"unsupported response still rejects before relation scoring");
 var legacy=new CommentSuggestion{Text="대답 없어서 더 어색하네ㅋㅋ",CueId="c0",GroundingQuote="인사를 했는데 대답이 없어요.",Material=J.Serialize(new{context_version=2,writing_fact="인사를 해도 대답이 없다",writing_quote="인사를 했는데 대답이 없어요."})};
 new FitScoring(g,(b,t)=>{var req=Req(b);var props=CaptionService.Get(CaptionService.Get(req,"format"),"properties");if(CaptionService.Get(props,"voices")!=null)return Task.FromResult("{\"voices\":[{\"id\":0,\"voice\":\"viewer\"}]}");var input=Last(req);Check(CaptionService.Get(input,"whole_context")==null&&(string)CaptionService.Get(input,"fact")=="인사를 해도 대답이 없다","legacy candidates keep their original single-fact boundary");return Task.FromResult("{\"added_fact\":\"\",\"meaning_clear\":false,\"reason\":\"검사용 판정\"}");}).Assess(video,content,new[]{legacy},CancellationToken.None).GetAwaiter().GetResult();
 bool canceled=false;try{combined.Evaluate(video,content,new[]{row},new CancellationToken(true)).GetAwaiter().GetResult();}catch(OperationCanceledException){canceled=true;}Check(canceled,"cancellation is not swallowed");
 }
 return 0;}catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}
