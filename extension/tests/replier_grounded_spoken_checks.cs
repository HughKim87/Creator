using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Threading;using System.Threading.Tasks;using System.Web.Script.Serialization;using ReplierDesktop;
public static class GroundedSpokenChecks {
 static void Check(bool b,string s){if(!b)throw new Exception(s);Console.WriteLine("PASS "+s);}
 public static int Main(){try{var j=new JavaScriptSerializer();var video=new Video{Id="V0000000001",Title="조립 마무리"};var evidence=new[]{new KeyValuePair<string,CaptionCue>("c0",new CaptionCue{Text="나사 하나가 남았습니다. 어디에 쓰는 것인지는 모르겠어요."})};
 using(var m=new LocalModel("unused")){foreach(var pair in new[]{new[]{false,false,false,false},new[]{true,true,false,false},new[]{true,false,false,false},new[]{true,false,true,false},new[]{true,false,true,true}}){
 var engine=new WholeCommentGrounding(m,(body,t)=>{var req=SceneMaterial.Json(j.Serialize(body));var props=CaptionService.Get(CaptionService.Get(req,"format"),"properties");if(CaptionService.Get(props,"references")!=null)return Task.FromResult("{\"references\":[]}");
 var msgs=(object[])CaptionService.Get(req,"messages");var input=SceneMaterial.Json((string)CaptionService.Get(msgs.Last(),"content"));return Task.FromResult(j.Serialize(new{evaluated_comment=(string)CaptionService.Get(input,"candidate_comment"),premise="나사가 남음",source=0,supported=true,context_clear=pair[0],added_claim=pair[1],asserts_event_result=pair[2],source_kind=pair[3]?"actual_event":"conditional_or_rule",comment_outcome="none",context_outcome="undetermined",rationale="검사용 판단"}));});
 var review=engine.Assess(video,evidence,"나사 하나 남는 게 신경 쓰이네요",CancellationToken.None).GetAwaiter().GetResult();
 Check(review.Supported==(pair[0]&&!pair[1]&&(!pair[2]||pair[3])),"positive support alone cannot bypass unclear context or added claims or treating conditions as events "+string.Join("/",pair));}}
 var tieRows=new[]{new CommentSuggestion{Text="복잡한 작업도 차근차근 하니까 되는군요",FitEligible=true,FitScore=90},new CommentSuggestion{Text="이걸 동시에 챙기네ㅋㅋ",FitEligible=true,FitScore=81},new CommentSuggestion{Text="없는 사건",FitEligible=false,FitScore=100}};
 int choices=0;var tie=new SceneTieBreaker((model,body,token)=>{choices++;Check(model==DualCommentService.Models[1],"style comparison reuses the final loaded evaluator");return Task.FromResult("{\"choice\":1}");},model=>{throw new Exception("should not reload model");},true);
 tie.Apply(video,tieRows,CancellationToken.None).GetAwaiter().GetResult();
 Check(tieRows[1].TiePreference==2&&tieRows[0].TiePreference==0&&tieRows[2].TiePreference==0&&tieRows[1].FitScore==81&&choices==1,"style choice considers only independently grounded finalists without changing scores or reloading models");
 string diagnosticRoot=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"diagnostic-fixture"),diagnosticRuntime=Path.Combine(diagnosticRoot,".runtime","replier-llm"),diagnosticFile=Path.Combine(diagnosticRoot,"data","replier","llm-diagnostics.jsonl");Directory.CreateDirectory(Path.GetDirectoryName(diagnosticFile));File.WriteAllLines(diagnosticFile,Enumerable.Repeat("{\"at\":\"fixture\",\"padding\":\""+new string('x',1000)+"\"}",2200));ModelDiagnostics.Record(diagnosticRuntime,new{at="fresh",phase="bounded-log-check"});
 Check(new FileInfo(diagnosticFile).Length<2*1024*1024&&File.ReadLines(diagnosticFile).Last().Contains("bounded-log-check"),"full diagnostics keeps recent records instead of silently stopping forever");
 using(var model=new LocalModel("unused")){
 var scene=new SceneReading{EvidenceIds=new[]{"c0"},Angles=new string[0]};var material=new Dictionary<string,string>{{"c0",j.Serialize(new{context_version=2,scene=scene,title="제한 시간 도전",raw_sources=new object[0]})}};
 var cues=new Dictionary<string,CaptionCue>{{"c0",new CaptionCue{Text="제한 시간이 있기 때문에 빨리 해야 돼요. 다음 대사는 이름을 알아듣기 어렵습니다."}}};
 var points=ClearReactionPoints.Select(model,material,cues,CancellationToken.None).GetAwaiter().GetResult();var point=SceneMaterial.Json(points["c0"]);
 Check((string)CaptionService.Get(point,"writing_fact")=="시간 제한이 있다"&&ContextGuidance.HasQuote(cues["c0"].Text,(string)CaptionService.Get(point,"writing_quote")),"literal clear condition preserves the real quote and avoids guessing ASR terminology before writing");
 }
 using(var model=new LocalModel("unused")){
 var contradictory=new WholeCommentGrounding(model,(body,t)=>{var req=SceneMaterial.Json(j.Serialize(body));var props=CaptionService.Get(CaptionService.Get(req,"format"),"properties");if(CaptionService.Get(props,"references")!=null)return Task.FromResult("{\"references\":[]}");var messages=(object[])CaptionService.Get(req,"messages");var input=SceneMaterial.Json((string)CaptionService.Get(messages.Last(),"content"));return Task.FromResult(j.Serialize(new{evaluated_comment=(string)CaptionService.Get(input,"candidate_comment"),source=0,supported=true,context_clear=true,added_claim=false,asserts_event_result=true,source_kind="actual_event",comment_outcome="failure",context_outcome="success",rationale="단어 연결만 본 잘못된 긍정 판정"}));});
 var outcome=contradictory.Assess(video,evidence,"못 끝낸 것 같네",CancellationToken.None).GetAwaiter().GetResult();
 Check(!outcome.Supported&&outcome.Reason.Contains("댓글 결과: failure")&&outcome.Reason.Contains("원문 결과: success"),"a positive support verdict cannot override a contrary observed success or failure");
 }
 using(var model=new LocalModel("unused")){
 string seenFact=null;
 var focused=FocusedGrounding.Assess(model,(body,t)=>{var req=SceneMaterial.Json(j.Serialize(body));var messages=(object[])CaptionService.Get(req,"messages");var input=SceneMaterial.Json((string)CaptionService.Get(messages.Last(),"content"));seenFact=(string)CaptionService.Get(input,"fact");Check(CaptionService.Get(input,"title")==null&&CaptionService.Get(input,"whole_context")==null,"factual verification receives only the selected fact rather than borrowing claims from a title or unrelated ASR");return Task.FromResult("{\"verdict\":\"unsupported\",\"reason\":\"없는 결과를 추가함\"}");},"시간 제한이 있다","못 끝냈다는 거야ㅋㅋ",evidence,CancellationToken.None).GetAwaiter().GetResult();
 Check(!focused.Supported&&seenFact=="시간 제한이 있다","a focused unsupported verdict vetoes a candidate before numeric relevance grading");
 var relaxed=FocusedGrounding.Assess(model,(body,t)=>Task.FromResult("{\"verdict\":\"supported\",\"reason\":\"조건에 대한 개인 감상\"}"),"시간 제한이 있다","더 긴장되겠다ㅋㅋ",evidence,CancellationToken.None).GetAwaiter().GetResult();
 Check(relaxed.Supported&&relaxed.SourceIndexes.SequenceEqual(new[]{0}),"an ordinary personal response can pass without copying words or inventing a result");
 }
 using(var model=new LocalModel("unused")){
 var scene=new SceneReading{EvidenceIds=new[]{"c0"},Angles=new string[0]};var materials=new Dictionary<string,string>{{"c0",j.Serialize(new{context_version=2,scene=scene,title="도전",caption="뜻 모를 도입부",raw_sources=new object[0]})}};
 var cues=new Dictionary<string,CaptionCue>{{"c0",new CaptionCue{Text="뜻 모를 도입부에서 어떻게 하는 거야?"}},{"c9",new CaptionCue{Text="제한 시간이 있어서 순서대로 해야 합니다."}}};
 var points=ClearReactionPoints.Select(model,materials,cues,CancellationToken.None).GetAwaiter().GetResult();var point=SceneMaterial.Json(points["c9"]);
 Check(points.ContainsKey("c9")&&!points.ContainsKey("c0")&&(string)CaptionService.Get(point,"caption")==cues["c9"].Text&&ContextGuidance.HasQuote(cues["c9"].Text,(string)CaptionService.Get(point,"writing_quote")),"clear source can come from outside the planner's initial window without fabricating or mismatching its quote");
 }
 using(var model=new LocalModel("unused")){
 foreach(var sample in new[]{new{added="",clear=true,want=true},new{added="실제로 실패함",clear=true,want=false},new{added="",clear=false,want=false}}){
 var assessment=FocusedGrounding.Assess(model,(b,t)=>Task.FromResult(j.Serialize(new{added_fact=sample.added,meaning_clear=sample.clear,reason="검사용 사실 대조"})),"답하지 않았습니다","답 안 해줘서 웃기네",evidence,CancellationToken.None).GetAwaiter().GetResult();
 Check(assessment.Supported==sample.want,"fact verification distinguishes a personal response from an added event and unclear source "+sample.added+"/"+sample.clear);
 }
 }
 int calls=0;
 using(var svc=new DualCommentService(async(name,v,c,t,refresh)=>{calls++;if(calls==1)await Task.Delay(1000,t);return new CommentResult{Comments=new List<CommentSuggestion>(),QualityFiltered=true};},generationTimeout:TimeSpan.FromMilliseconds(20))){
 var result=svc.Generate(video,new VideoContent(),CancellationToken.None).GetAwaiter().GetResult();
 Check(result.Complete&&!result.Cancelled&&calls==2&&result.Batches[0].Result==null&&result.Batches[0].Error.Contains("중단"),"stalled writer exits its deadline and completes without retrying it indefinitely");
 }
 var cancel=new CancellationTokenSource();cancel.Cancel();using(var svc=new DualCommentService((name,v,c,t,r)=>{throw new Exception("should not run");})){bool stopped=false;try{svc.Generate(video,new VideoContent(),cancel.Token).GetAwaiter().GetResult();}catch(OperationCanceledException){stopped=true;}Check(stopped,"explicit user cancellation remains cancellation");}
 return 0;}catch(Exception e){Console.WriteLine(e);return 1;}}
}

