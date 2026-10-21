using System;using System.Collections.Generic;using System.Linq;using System.Threading;using System.Threading.Tasks;using System.Web.Script.Serialization;using ReplierDesktop;
public class QualityGateChecks {
 static void Check(bool b,string s){if(!b)throw new Exception(s);Console.WriteLine("PASS "+s);}
 public static int Main(){try{
 var json=new JavaScriptSerializer();var content=new VideoContent{Version=1,VideoId="V0000000001",Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=new List<CaptionCue>{new CaptionCue{Text="보호막의 체력 계수가 올랐습니다."}}};var video=new Video{Id=content.VideoId,Title="보호막 체력 계수 버프"};
 using(var plannerModel=new LocalModel("unused","gemma4:e2b-it-qat")){
 string expectedTitle=video.Title;
 var planner=new ReactionPlanner(plannerModel,(body,t)=>{var root=json.DeserializeObject(json.Serialize(body));var messages=(object[])CaptionService.Get(root,"messages");Check(((string)CaptionService.Get(messages.Last(),"content")).Contains(expectedTitle),"selector receives whole title and source context");return Task.FromResult("{\"source\":0,\"fact\":\"모델이 잘못 만든 체력 증가 사실\"}");});
 var plan=planner.Prepare(video,content,CancellationToken.None).GetAwaiter().GetResult();var material=json.DeserializeObject(plan.Values.First());string selected=(string)CaptionService.Get(material,"selected"),fact=(string)CaptionService.Get(material,"fact");
 Check(content.Cues[0].Text.Contains(selected) && fact==selected && !fact.Contains("잘못 만든"),"program attaches selected original speech and ignores any model-written replacement fact");
 var continuous=new VideoContent{Version=1,VideoId=content.VideoId,Language="ko",Source="YouTube 공개 자막",AcquiredAt=content.AcquiredAt,Cues=new List<CaptionCue>{new CaptionCue{Text="이 게임의 전투는 캐릭터를 교체하며 콤보를"},new CaptionCue{StartMs=2000,Text="이어가는 논타겟 액션을 중심으로 전개됩니다."}}};
 var complete=planner.Prepare(video,continuous,CancellationToken.None).GetAwaiter().GetResult();string completeQuote=(string)CaptionService.Get(json.DeserializeObject(complete.Values.First()),"selected");
 Check(completeQuote.Contains("교체") && completeQuote.Contains("이어가는"),"sentence spanning caption cues is kept whole instead of starting at a dangling verb");
 var priced=new VideoContent{Version=1,VideoId=content.VideoId,Language="ko",Source="YouTube 공개 자막",AcquiredAt=content.AcquiredAt,Cues=new List<CaptionCue>{new CaptionCue{Text="이 게임은 이제 큰 폭의 60% 할인을 시작했네요."}}};
 var discount=planner.Prepare(video,priced,CancellationToken.None).GetAwaiter().GetResult();string discountQuote=(string)CaptionService.Get(json.DeserializeObject(discount.Values.First()),"selected");
 Check(discountQuote=="할인을 시작했네요." && priced.Cues[0].Text.Contains(discountQuote),"numeric qualifier is omitted by selecting a real contiguous discount predicate, not by inventing a summary");
 var semanticReject=new ReactionPlanner(plannerModel,(body,t)=>Task.FromResult("{\"source\":-1}"));
 bool praiseRejected=false;try{semanticReject.Prepare(video,new VideoContent{Version=1,VideoId=content.VideoId,Language="ko",Source="YouTube 공개 자막",AcquiredAt=content.AcquiredAt,Cues=new List<CaptionCue>{new CaptionCue{Text="제가 추천하는 필살기 무료 게임은 순수 재미 고트입니다."}}},CancellationToken.None).GetAwaiter().GetResult();}catch(System.IO.InvalidDataException){praiseRejected=true;}Check(praiseRejected,"promotional praise without a concrete feature cannot become a literal skill fact");
 var plain=new VideoContent{Version=1,VideoId=content.VideoId,Language="ko",Source="YouTube 공개 자막",AcquiredAt=content.AcquiredAt,Cues=new List<CaptionCue>{new CaptionCue{Text="열심히 상자를 열었는데 안에 아무것도 없네요."}}};
 var ordinary=planner.Prepare(video,plain,CancellationToken.None).GetAwaiter().GetResult();string ordinaryQuote=(string)CaptionService.Get(json.DeserializeObject(ordinary.Values.First()),"selected");
 Check(ordinaryQuote==plain.Cues[0].Text,"ordinary gameplay reaches source selection without a hardcoded technical keyword");
 var questionAndFact=new VideoContent{Version=1,VideoId=content.VideoId,Language="ko",Source="YouTube 공개 자막",AcquiredAt=content.AcquiredAt,Cues=new List<CaptionCue>{new CaptionCue{Text="이번 스킨 받았냐고요? 토큰으로 원하는 스킨을 선택할 수 있습니다."}}};
 var factual=planner.Prepare(video,questionAndFact,CancellationToken.None).GetAwaiter().GetResult();string factualQuote=(string)CaptionService.Get(json.DeserializeObject(factual.Values.First()),"selected");Check(factualQuote.Contains("토큰")&&!factualQuote.Contains("받았냐고요"),"a question does not become factual evidence merely because its name matches the title");
 var loose=new VideoContent{Version=1,VideoId=content.VideoId,Language="ko",Source="YouTube 공개 자막",AcquiredAt=content.AcquiredAt,Cues=new List<CaptionCue>{new CaptionCue{Text="이 게임은 무료로 즐길 수 있는데 아쉬운 점은 본편에"},new CaptionCue{StartMs=2000,Text="아직 한글이 없다는 거 빨리 지원해줬으면 좋겠다 다음게임"}}};
 expectedTitle="무료 게임 추천";
 var language=planner.Prepare(new Video{Id=video.Id,Title=expectedTitle},loose,CancellationToken.None).GetAwaiter().GetResult();string languageQuote=(string)CaptionService.Get(json.DeserializeObject(language.Values.First()),"selected");
 Check(languageQuote.Contains("한글") && !languageQuote.Contains("다음게임"),"specific support detail outranks generic free introduction and stops before the next subject");

 }
 Check(!FastComments.HasGrounding("새로 나온 거 있으면 도움 될 거예요.",json.Serialize(new{caption="스킨을 구매하시면 도움이 되실 거예요."})),"reported abstract winner cannot claim concrete connection from help alone");
 Check(!FastComments.HasGrounding("오 그래도 예쁘네요.",json.Serialize(new{caption="어 그래도 이쁜데요."})),"bare admiration without its subject is not counted as concrete content");
 Check(ViewerQuality.Problem("스킨 없는 분들에게 큰 도움이 되겠네요")!=null,"purchase usefulness guidance is distinguished from viewer reaction");
 Check(ViewerQuality.SourceProblem("벤틀리 줬냐고요?","이번 벤틀리 줬냐고요?")!=null && ViewerQuality.SourceProblem("토큰으로 스킨 고를 수 있는 건 좋네요.","토큰으로 원하는 스킨을 선택할 수 있습니다.")==null,"copied dialogue is not a viewer reaction while a fact-based response remains allowed");
 bool typoRejected=false;try{CommentPipeline.ValidateReaction("스킨 있으면 굳이 틀릴 필요 없죠.",json.Serialize(new{caption="스킨이 있다 하시는 분들은 굳이 뽑을 필요는 없다고 생각해요."}));}catch(System.IO.InvalidDataException){typoRejected=true;}Check(typoRejected,"reported ASR mistake cannot change drawing a skin into being wrong");
 using(var m=new LocalModel("unused","gemma4:e2b-it-qat")){
 var diverse=new VideoContent{Version=1,VideoId=content.VideoId,Language="ko",Source="YouTube 공개 자막",AcquiredAt=content.AcquiredAt,Cues=Enumerable.Range(0,35).Select(i=>new CaptionCue{StartMs=i*1000,Text="스킨의 "+new[]{"분홍색 시트가 예쁘네요.","토큰을 모아서 고를 수 있네요.","검은색도 함께 있네요.","초록색 차량도 보이네요.","광택이 은은하네요."}[i/7]}).ToList()};
 var selector=new ReactionPlanner(m,(body,t)=>{var req=json.DeserializeObject(json.Serialize(body));var messages=(object[])CaptionService.Get(req,"messages");var input=json.DeserializeObject((string)CaptionService.Get(messages.Last(),"content"));var options=((object[])CaptionService.Get(input,"sources")).GroupBy(x=>(int)CaptionService.Get(x,"window")).Select(g=>g.First()).Take(3).ToArray();return Task.FromResult(json.Serialize(new{source=CaptionService.Get(options[0],"index"),alternatives=new int[0]}));});
 var prepared=selector.Prepare(new Video{Id=video.Id,Title="새 스킨 구경"},diverse,CancellationToken.None).GetAwaiter().GetResult();Check(prepared.Count==3,"central-topic windows are distributed even if the selector omits optional alternatives");
 var windows=CommentService.Evidence(diverse,"새 스킨 구경");Check(prepared.All(p=>windows[p.Key].Text.Contains((string)CaptionService.Get(json.DeserializeObject(p.Value),"selected"))),"diverse source selections still attach literal original quotations");
 }
 using(var g=new LocalModel("unused","gemma4:e2b-it-qat"))using(var q=new LocalModel("unused")){
 for(int phase=0;phase<3;phase++){
 int numerical=0;int current=phase;var item=new[]{new CommentSuggestion{Text="보호막 버프는 반갑네요",CueId="c0"}};
 var audited=new FitScoring(g,(body,t)=>{var request=json.DeserializeObject(json.Serialize(body));var props=CaptionService.Get(CaptionService.Get(request,"format"),"properties");var messages=(object[])CaptionService.Get(request,"messages");var input=json.DeserializeObject((string)CaptionService.Get(messages.Last(),"content"));
 if(CaptionService.Get(props,"natural")!=null){Check(CaptionService.Get(input,"caption")==null && CaptionService.Get(input,"title")==null,"style-only audit receives no video evidence to bias its language judgment");return Task.FromResult(json.Serialize(new{natural=current!=0}));}
 if(CaptionService.Get(props,"grounded")!=null)return Task.FromResult(json.Serialize(new{grounded=current!=1}));
 numerical++;return Task.FromResult(json.Serialize(new{rating=new{issue="none",kind="linked",match=0,topic=20,tone=10,care=5,link=15}}));});
 var rating=audited.Assess(video,content,item,CancellationToken.None).GetAwaiter().GetResult()[0];
 Check(current==2 ? rating.Eligible && numerical==1 : !rating.Eligible && numerical==0,"style and meaning audits must pass before weighted scoring, phase "+current);
 }
 string veto="none";Func<string,Func<object,CancellationToken,Task<string>>> send=judge=>(body,t)=>Task.FromResult(json.Serialize(new{rating=new{issue=judge=="q"?veto:"none",kind="linked",match=0,topic=20,tone=10,care=5,link=15}}));
 foreach(string issue in new[]{"awkward","meaning","explanation","unsupported"}){
 veto=issue;var c=new[]{new CommentSuggestion{Text="보호막 버프는 반갑네요",CueId="c0"}};new CombinedFitScoring(new FitScoring(g,send("g"),false),new FitScoring(q,send("q"),false),()=>Task.FromResult(0)).Evaluate(video,content,c,CancellationToken.None).GetAwaiter().GetResult();
 Check(c[0].FitEligible==false && c[0].FitScore==0 && c[0].GemmaFitScore+c[0].QwenFitScore==0,"one judge veto overrides all maximum numerical scores: "+issue);
 }
 veto="none";var good=new[]{new CommentSuggestion{Text="보호막 버프는 반갑네요",CueId="c0"}};new CombinedFitScoring(new FitScoring(g,send("g"),false),new FitScoring(q,send("q"),false),()=>Task.FromResult(0)).Evaluate(video,content,good,CancellationToken.None).GetAwaiter().GetResult();Check(good[0].FitEligible==true && good[0].FitScore==100,"both judges must approve before numerical ranking");
 var dangling=new[]{new CommentSuggestion{Text="그게 보호막에 체력 계수 버프 먹었대 ㅋㅋ",CueId="c0"}};new CombinedFitScoring(new FitScoring(g,send("g"),false),new FitScoring(q,send("q"),false),()=>Task.FromResult(0)).Evaluate(video,content,dangling,CancellationToken.None).GetAwaiter().GetResult();Check(dangling[0].FitEligible==false && dangling[0].FitScore==0,"unbound conversational continuation cannot win even when both judges give full marks");
 var helpSource=new VideoContent{Version=1,VideoId=content.VideoId,Language="ko",Source="YouTube 공개 자막",AcquiredAt=content.AcquiredAt,Cues=new List<CaptionCue>{new CaptionCue{Text="기존에 스킨 없던 분들이 구매하시면 생활에 도움이 되실 거고 이미 스킨이 있으면 굳이 뽑을 필요는 없어요."}}};
 var help=new[]{new CommentSuggestion{Text="새로 나온 거 있으면 도움 될 거예요.",CueId="c0"}};new CombinedFitScoring(new FitScoring(g,send("g"),false),new FitScoring(q,send("q"),false),()=>Task.FromResult(0)).Evaluate(new Video{Id=video.Id,Title="새 스킨 구경"},helpSource,help,CancellationToken.None).GetAwaiter().GetResult();Check(help[0].FitEligible==false && help[0].FitScore==0,"both judges giving maximum scores cannot rescue the reported abstract help comment");
 var repeated=new[]{new CommentSuggestion{Text="이 정도면 보호막도 이 정도는 이해할 만하죠",CueId="c0"}};new CombinedFitScoring(new FitScoring(g,send("g"),false),new FitScoring(q,send("q"),false),()=>Task.FromResult(0)).Evaluate(video,content,repeated,CancellationToken.None).GetAwaiter().GetResult();Check(repeated[0].FitEligible==false && repeated[0].FitScore==0,"repeated phrase veto remains effective even if both judges give full marks");
 }
 int evaluation=0;var refreshes=new List<bool>();
 using(var repair=new DualCommentService((name,v,c,t,refresh)=>{refreshes.Add(refresh);return Task.FromResult(new CommentResult{Comments=Enumerable.Range(0,5).Select(i=>new CommentSuggestion{Text="검사 후보",FitEligible=false}).ToList()});},evaluator:(v,c,rows,t)=>{evaluation++;foreach(var row in rows){row.FitEligible=evaluation==2;row.FitScore=evaluation==2?80:0;}return Task.FromResult(0);},retryRejected:true)){
 var repaired=repair.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();Check(evaluation==2 && refreshes.SequenceEqual(new[]{false,false,true,true}) && repaired.Batches.SelectMany(b=>b.Result.Comments).All(c=>c.FitEligible==true),"all-rejected result triggers one fresh rewrite and repeats identical quality checks");
 }
 evaluation=0;using(var reject=new DualCommentService((name,v,c,t,refresh)=>Task.FromResult(new CommentResult{Comments=new List<CommentSuggestion>{new CommentSuggestion{Text="불합격 후보",FitEligible=false}},QualityFiltered=true}),evaluator:(v,c,rows,t)=>{evaluation++;foreach(var row in rows)row.FitScore=0;return Task.FromResult(0);},retryRejected:true)){
 var rejected=reject.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();Check(evaluation==2 && rejected.Complete && rejected.Batches.SelectMany(b=>b.Result.Comments).All(c=>c.FitEligible==false),"automatic quality rewrite stops after two passes without inventing an approved candidate");
 }
 return 0;}catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}

