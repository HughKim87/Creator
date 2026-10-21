using System;using System.Collections.Generic;using System.IO;using System.Linq;using System.Threading;using System.Threading.Tasks;using System.Web.Script.Serialization;using ReplierDesktop;
public static class FitChecks
{
 static readonly JavaScriptSerializer Json=new JavaScriptSerializer();
 static void Check(bool ok,string text){if(!ok)throw new Exception(text);Console.WriteLine("PASS "+text);}
 static object Row(int id,string text,string kind,int score,string term="",string source="",string quote=""){return new{issue="none",id=id,text=text,kind=kind,match=kind=="linked" || kind=="conflict" ? 0 : -1,topic=Math.Min(score,20),tone=Math.Min(Math.Max(score-20,0),10),care=Math.Min(Math.Max(score-30,0),5),link=Math.Max(score-35,0),term=term,source=source,quote=quote};}
 static string Ratings(params object[] rows){return Json.Serialize(new{ratings=rows});}
 static bool Reject(string raw,IList<CommentSuggestion> rows,IDictionary<string,string> sources){try{FitScoring.Parse(raw,rows,sources);return false;}catch(InvalidDataException){return true;}}
 static object Input(object body){var parsed=Json.DeserializeObject(Json.Serialize(body));return Json.DeserializeObject((string)CaptionService.Get(((object[])CaptionService.Get(parsed,"messages"))[1],"content"));}
 static string Reply(object body,int start){var rows=(object[])CaptionService.Get(Input(body),"comments");Check(rows.Length==1,"each grading request contains only one original comment");var r=rows[0];return Json.Serialize(new{rating=Row(999,"모델이 잘못 복사한 다른 문장","general",start+(int)CaptionService.Get(r,"id"))});}

 public static int Main(){try{
 var comments=new List<CommentSuggestion>{new CommentSuggestion{Text="다음 영상도 궁금해요",CueId="c0"},new CommentSuggestion{Text="확률을 보니 쉽게 결정하기 어렵네요",CueId="c0"}};
 var sources=new Dictionary<string,string>{{"title","신화확률을 확인합니다"},{"c0","신화확률이 낮아서 선택을 고민합니다"}};
 Check(Reject(Ratings(Row(0,comments[0].Text,"linked",50,"신화확률","c0",sources["c0"]),Row(1,comments[1].Text,"general",20)),comments,sources),"user regression: caption-only mythic probability cannot earn credit for next-video comment");
 var valid=FitScoring.Parse(Ratings(Row(1,comments[1].Text,"linked",48,"확률","c0",sources["c0"]),Row(0,comments[0].Text,"general",50)),comments,sources);
 Check(valid[0].Score==48 && valid[1].Score==35 && !valid[1].Reason.Contains("신화") && valid[1].Reason.Contains(comments[0].Text) && valid[1].Reason.Contains("주제 어울림 20/20") && valid[1].Reason.Contains("내용 연결 0/15"),"verified content credit retained while generic expectation is capped without invented rationale");
 Check(FitScoring.Parse(Ratings(Row(0,comments[0].Text,"general",20),Row(1,comments[1].Text,"linked",50,"확률","title",sources["title"])),comments,sources)[1].Reason.Contains("제목"),"title-only textual connection uses verified title quote");
 Check(Reject(Ratings(Row(0,comments[1].Text,"general",30),Row(1,comments[0].Text,"general",30)),comments,sources),"swapped comment texts rejected even when IDs look valid");
 Check(Reject(Ratings(Row(0,comments[0].Text,"general",30),Row(1,comments[1].Text,"linked",45,"확률","c0","확률이 매우 높습니다")),comments,sources),"fabricated caption quote rejected");
 Check(!FitScoring.Parse(Ratings(Row(0,comments[0].Text,"general",50,"신화확률","c0",sources["c0"]),Row(1,comments[1].Text,"general",30)),comments,sources)[0].Reason.Contains("신화"),"generic assessment discards unrelated evidence and cannot smuggle in rationale");
 Check(Reject(Ratings(Row(0,comments[0].Text,"general",51),Row(1,comments[1].Text,"general",30)),comments,sources),"out-of-range score rejected");
 Check(Reject(Ratings(Row(0,comments[0].Text,"general",30),Row(0,comments[0].Text,"general",30)),comments,sources) && Reject("oops",comments,sources),"duplicate IDs and malformed response rejected");
 var visual=new[]{new CommentSuggestion{Text="편집이 깔끔하네요"}};
 Check(FitScoring.Parse(Ratings(Row(0,visual[0].Text,"unsupported",50,"편집")),visual,sources)[0].Score==15,"unobservable visual claim cannot receive high score");
 var linkSources=new Dictionary<string,string>{{"title","체력 계수 버프"},{"c0","이번 패치로 보호막의 체력 계수가 버프를 받았습니다."}};
 var detailed=FitScoring.FindLinks("체력 계수 버프라니, 이거 꽤 괜찮은 변화네요.",linkSources);
 Check(detailed.Count>0 && detailed.Any(m=>m.Term.Contains("체력 계수 버프")) && detailed.All(m=>linkSources[m.Source].Contains(m.Quote) && m.Quote.Contains(m.Term)),"short subjective reaction retains verified concrete title/caption connections");
 Check(FitScoring.FindLinks("다음 영상도 궁금해요",sources).Count==0,"unrelated mythic probability cannot become a matching phrase for generic expectation");
 var mereOverlap=new[]{new CommentSuggestion{Text="체력 버프로 외형도 바뀌었네요"}};
 Check(FitScoring.Parse(Ratings(Row(0,mereOverlap[0].Text,"unsupported",50,"외형")),mereOverlap,linkSources)[0].Link==0,"lexical overlap cannot automatically earn factual connection points");
 var linkedReaction=new[]{new CommentSuggestion{Text="체력 계수 버프라니, 괜찮은 변화네요"}};
 var linkedScore=FitScoring.Parse(Ratings(Row(0,linkedReaction[0].Text,"linked",44,"체력 계수 버프","title","체력 계수 버프")),linkedReaction,linkSources)[0];
 Check(linkedScore.Link==9 && linkedScore.Score==44 && linkedScore.Reason.Contains("체력 계수 버프"),"grounded casual reaction receives explicit connection points without a generic-category cap");
 var negativeSources=new Dictionary<string,string>{{"title","보호막 체력 계수 버프"},{"c0","보호막 체력 계수가 올랐습니다. 외형은 바뀌지 않았습니다."}};
 var contradictionRows=new[]{new CommentSuggestion{Text="이번 버프로 외형까지 바뀌었네요"}};
 var guarded=FitScoring.Parse(Ratings(Row(0,contradictionRows[0].Text,"linked",50,"외형","c0","외형은 바뀌지 않았습니다")),contradictionRows,negativeSources)[0];
 Check(guarded.Link==0 && guarded.Score<=10 && guarded.Reason.Contains("원문 부정"),"shared noun cannot override an explicitly negated identical predicate");
 Check(!FitScoring.DeniesSamePredicate("외형은 바뀌지 않았지만 보호막은 좋아졌네요","외형","외형은 바뀌지 않았습니다"),"matching negative reaction is not misread as a contradiction");
 Check(!FitScoring.DeniesSamePredicate("보호막이 좋아졌네요","보호막","외형은 바뀌지 않았습니다. 보호막은 좋아졌습니다"),"unrelated negative clause cannot reduce a supported reaction");
 var video=new Video{Id="V0000000001",Title="검사용 게임 제목"};
 var content=new VideoContent{Version=1,VideoId=video.Id,Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=new List<CaptionCue>{new CaptionCue{Text=sources["c0"]}}};
 int calls=0;var inputs=new List<string>();var events=new List<string>();
 using(var g=new LocalModel("unused","gemma4:e2b-it-qat"))using(var q=new LocalModel("unused","qwen3.5:4b")){
 Func<string,int,Func<object,CancellationToken,Task<string>>> sender=(name,start)=>(body,t)=>{calls++;events.Add(name);inputs.Add(Json.Serialize(Input(body)));return Task.FromResult(Reply(body,start));};
 var first=new FitScoring(g,sender("g",10),false);var second=new FitScoring(q,sender("q",20),false);
 var combined=new CombinedFitScoring(first,second,()=>{events.Add("unload");return Task.FromResult(0);});
 combined.Evaluate(video,content,comments,CancellationToken.None).GetAwaiter().GetResult();
 Check(events.SequenceEqual(new[]{"g","g","unload","q","q"}) && inputs[0]==inputs[2] && inputs[1]==inputs[3],"independent judges receive same anonymous exact comments title and captions");
 Check(comments[0].FitScore==0 && comments[1].FitScore==0 && comments.All(c=>c.FitEligible==false),"single-request responses bind to original comments despite mutated model echo");
 combined.Evaluate(video,content,comments,CancellationToken.None).GetAwaiter().GetResult();Check(calls==4,"unchanged validated context reuses both scores");
 comments[0].Text="또 보고 싶은 영상이네요";
 combined.Evaluate(video,content,comments,CancellationToken.None).GetAwaiter().GetResult();Check(calls==8,"changed comment invalidates cached scores");
 video.Title="바뀐 제목";combined.Evaluate(video,content,comments,CancellationToken.None).GetAwaiter().GetResult();Check(calls==12,"changed title invalidates cached scores");
 var fresh=new[]{new CommentSuggestion{Text="다음 영상도 궁금해요",CueId="c0"}};
 var broken=new CombinedFitScoring(first,new FitScoring(q,(b,t)=>Task.FromResult("{\"ratings\":[]}"),false),()=>Task.FromResult(0));
 try{broken.Evaluate(video,content,fresh,CancellationToken.None).GetAwaiter().GetResult();}catch(InvalidDataException){}
 Check(!fresh[0].FitScore.HasValue && !fresh[0].GemmaFitScore.HasValue,"invalid second judge cannot publish partial total");
 var stop=new CancellationTokenSource();var cancelled=new CombinedFitScoring(first,second,()=>{stop.Cancel();return Task.FromResult(0);});
 try{cancelled.Evaluate(video,content,fresh,stop.Token).GetAwaiter().GetResult();}catch(OperationCanceledException){}Check(!fresh[0].FitScore.HasValue,"cancellation cannot publish partial total");
 }
 using(var m=new LocalModel("unused")){
 int repairs=0;var one=new[]{new CommentSuggestion{Text="확률을 보고 나니 쉽게 고르기 어렵네요"}};
 var corrected=new FitScoring(m,(b,t)=>{repairs++;return Task.FromResult(repairs==1 ? "{\"ratings\":[]}" : Json.Serialize(new{rating=Row(0,one[0].Text,"general",25)}));},false);
 var c=new VideoContent{Version=1,VideoId="V0000000003",Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=new List<CaptionCue>{new CaptionCue{Text="확률을 보고 선택합니다"}}};
 Check(corrected.Assess(new Video{Id=c.VideoId,Title="확률 확인"},c,one,CancellationToken.None).GetAwaiter().GetResult().Count==1 && repairs==2,"invalid grading format gets exactly one validated repair");
 int failedCalls=0;var bad=new FitScoring(m,(b,t)=>{failedCalls++;return Task.FromResult("{\"ratings\":[]}");},false);bool rejected=false;
 try{bad.Assess(new Video{Id=c.VideoId,Title="확률 확인"},c,one,CancellationToken.None).GetAwaiter().GetResult();}catch(InvalidDataException){rejected=true;}
 Check(rejected && failedCalls==2,"repeated invalid grading stops without a fabricated fallback score");
 }
 return 0;}catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
