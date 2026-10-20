using System;using System.Collections.Generic;using System.IO;using System.Linq;using System.Threading;using System.Threading.Tasks;using System.Web.Script.Serialization;using ReplierDesktop;
public static class PipelineChecks{
 static void Check(bool ok,string label){if(!ok)throw new Exception(label);Console.WriteLine("PASS "+label);}
 public static int Main(){try{
 var evidence=new Dictionary<string,CaptionCue>{{"a",new CaptionCue{Text="게임을 추천합니다"}},{"b",new CaptionCue{Text="다른 방법으로 해봅니다"}},{"c",new CaptionCue{Text="이 전략은 추천하지 않습니다"}},{"d",new CaptionCue{Text="업데이트 후 전략도 바뀌었습니다"}},{"e",new CaptionCue{Text="무슨 내용인지 불확실합니다"}}};
 var local=CommentPipeline.ExtractLocally(evidence);Check(local["a"]==CommentPipeline.Topics[0] && local["b"]==CommentPipeline.Topics[1],"local source keywords select material without model call");Check(local["c"]==CommentPipeline.Topics[4] && local["d"]==CommentPipeline.Topics[4] && local["e"]==CommentPipeline.Topics[4],"negative ambiguous and unknown sources stay neutral");
 foreach(string raw in new[]{"{\"comments\":[]}","{\"comments\":[0]}"}){bool bad=false;try{FastComments.Drafts(raw,1);}catch(InvalidDataException){bad=true;}Check(bad,"wrong draft count or type rejected");}
 foreach(string raw in new[]{"{\"decisions\":[6]}","{\"decisions\":[false]}","{\"decisions\":[0.5]}","{\"decisions\":[]}"}){bool bad=false;try{FastComments.Decisions(raw,1);}catch(InvalidDataException){bad=true;}Check(bad,"wrong style verdict is not acceptance");}
 var content=new VideoContent{Version=1,VideoId="V0000000001",Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=Enumerable.Range(0,10).Select(i=>new CaptionCue{StartMs=i*1000,Text="자동 정리가 되니 손으로 옮길 필요가 없어요. 재료는 따로 보관할 수 있어요."}).ToList()};
 string[] replies={"자동 정리 덕에 일일이 옮기는 수고는 덜겠네요", "재료를 따로 보관하는 건 괜찮네요. 뒤섞이지 않겠어요", "손으로 옮길 필요가 없다는 게 제일 반갑네요", "자동 정리는 이런 데서 편한 게 느껴지죠 ㅋㅋ", "재료 보관도 따로라니 정리하기 편하겠네요", "자동 정리가 되니 짐 옮기는 건 덜 번거롭겠어요"};
 var serializer=new JavaScriptSerializer();int writes=0,judges=0;bool broken=false;
 using(var model=new LocalModel("unused")){
 var service=new CommentService(model,(body,t)=>{
 var request=serializer.DeserializeObject(serializer.Serialize(body));var props=CaptionService.Get(CaptionService.Get(request,"format"),"properties");var messages=(object[])CaptionService.Get(request,"messages");string prompt=(string)CaptionService.Get(messages[messages.Length-1],"content");
 if(CaptionService.Get(props,"topic")!=null){Check(prompt.Contains("검사용 제목"),"title focus extraction receives actual title");return Task.FromResult(serializer.Serialize(new{topic="검사용 제목"}));}
 if(CaptionService.Get(props,"comments")!=null){writes++;Check(prompt.Contains("자동 정리") && prompt.Contains("검사용 제목"),"writer retains actual caption content and title");if(broken)return Task.FromResult("{\"comments\":[]}");var input=serializer.DeserializeObject(prompt);var rows=(object[])CaptionService.Get(input,"requests");Check(rows.Length==1,"each writer sees only one source request");int index=(int)CaptionService.Get(rows[0],"index");if(writes>5)Check(index==0,"repair requests only rejected index");return Task.FromResult(serializer.Serialize(new{evidence=(index==1 || index==4)?1:0,comments=new[]{writes<=5 ? replies[index] : replies[5]}}));}
 if(CaptionService.Get(props,"decisions")!=null){Check(prompt.Contains("검사용 제목"),"quality checker receives specific source excerpts");judges++;return Task.FromResult(serializer.Serialize(new{decisions=judges==1 ? new[]{1,0,0,0,0} : new[]{0}}));}
 throw new Exception("unexpected model call");});
 var result=service.Generate(new Video{Id=content.VideoId,Title="검사용 제목"},content,CancellationToken.None).GetAwaiter().GetResult();Check(result.Comments.Count==5 && writes==6 && judges==2,"isolated drafting and batched checking repair only rejected candidate");
 var actualEvidence=CommentService.Evidence(content,"검사용 제목");Check(result.Comments.Select(c=>c.CueId).SequenceEqual(Enumerable.Range(0,5).Select(i=>actualEvidence.Keys.ElementAt(i%actualEvidence.Count))) && result.Comments.All(c=>c.Evidence==actualEvidence[c.CueId].Text),"batched comments preserve five actual source references");
 broken=true;bool rejected=false;try{service.Generate(new Video{Id=content.VideoId,Title="검사용 제목"},content,CancellationToken.None,true).GetAwaiter().GetResult();}catch(InvalidDataException){rejected=true;}Check(rejected && writes==21,"malformed batch repair stops at three attempts");Check(object.ReferenceEquals(result,service.Generate(new Video{Id=content.VideoId,Title="검사용 제목"},content,CancellationToken.None).GetAwaiter().GetResult()),"failed refresh preserves last validated cache");}
 int qualityWrites=0;using(var model=new LocalModel("unused")){
 var guarded=new CommentService(model,(body,t)=>{
 var request=serializer.DeserializeObject(serializer.Serialize(body));var props=CaptionService.Get(CaptionService.Get(request,"format"),"properties");
 if(CaptionService.Get(props,"topic")!=null)return Task.FromResult(serializer.Serialize(new{topic="검사용 제목"}));
 if(CaptionService.Get(props,"comments")!=null){qualityWrites++;var msgs=(object[])CaptionService.Get(request,"messages");var input=serializer.DeserializeObject((string)CaptionService.Get(msgs[msgs.Length-1],"content"));int index=(int)CaptionService.Get(((object[])CaptionService.Get(input,"requests"))[0],"index");return Task.FromResult(serializer.Serialize(new{evidence=(index==1 || index==4)?1:0,comments=new[]{qualityWrites==1 ? "이런 게임은 처음 해봐요" : qualityWrites==2 ? "자동 정리 된다길래 할인할 때 샀죠 ㅋㅋ" : replies[index]}}));}
 int count=(int)CaptionService.Get(CaptionService.Get(props,"decisions"),"minItems");return Task.FromResult(serializer.Serialize(new{decisions=Enumerable.Repeat(0,count).ToArray()}));});
 var repaired=guarded.Generate(new Video{Id=content.VideoId,Title="검사용 제목"},content,CancellationToken.None).GetAwaiter().GetResult();Check(qualityWrites==7 && repaired.Comments.Count==5 && repaired.Comments.All(c=>!c.Text.Contains("처음 해봐") && !c.Text.Contains("샀죠")),"invented play and purchase experience rejected even when model style checker would accept it");}
 using(var model=new LocalModel("unused")){
 var pipe=new CommentPipeline(model,(body,t)=>{throw new Exception("context must not be speculatively summarized");});
 var source=new Dictionary<string,CaptionCue>{{"x",new CaptionCue{Text="기본 플레이는 무료지만 꾸미기는 따로 구매합니다."}}};
 var context=pipe.AnalyzeContext("신작 무료 게임",source,CancellationToken.None).GetAwaiter().GetResult()["x"];
 Check(context.Contains("신작 무료 게임"),"writer retains full title instead of reducing it to free keyword");
 var surrounding="재료는 모두 무료가 아닙니다. 기본 재료만 무료이고 나머지는 구매합니다.";
 var preserved=pipe.AnalyzeContext("무료 재료 대박",new Dictionary<string,CaptionCue>{{"x",new CaptionCue{Text=surrounding}}},CancellationToken.None).GetAwaiter().GetResult()["x"];
 Check((string)CaptionService.Get(serializer.DeserializeObject(preserved),"caption")==surrounding,"negation and neighboring qualification retained verbatim");
 var quotes=FastComments.FactQuotes("무료 재료 대박",surrounding);
 Check(quotes.All(q=>surrounding.Contains(q)) && quotes.Any(q=>q.Contains("아닙니다")),"source clauses preserve original negation and qualifications");
 Check(FastComments.SelectedQuote("{\"evidence\":0}",quotes)==quotes[0],"selected evidence resolves program-owned actual quote");
 foreach(string raw in new[]{"{}", "{\"evidence\":-1}", "{\"evidence\":8}", "{\"evidence\":\"0\"}"}){
 bool invalid=false;try{FastComments.SelectedQuote(raw,quotes);}catch(InvalidDataException){invalid=true;}Check(invalid,"missing or invalid source index rejected");
 }
 Check(FastComments.FactQuotes("보호막 체력 계수 버프","반갑습니다. 요즘 뭘 해볼까요? 보호막의 체력 계수가 버프를 받았습니다.").All(q=>q.Contains("체력 계수")),"irrelevant greeting cannot replace title-related fact");
 Check(FastComments.FactQuotes("할인 게임 추천","할인코드를 쓰고 골드 회원 가입하세요.").Length==0,"advertising is not offered as a viewer reaction fact");
 var named=pipe.AnalyzeContext("민수 무료 민수",new Dictionary<string,CaptionCue>{{"x",new CaptionCue{Text="민수가 무료로 제공합니다."}}},CancellationToken.None).GetAwaiter().GetResult()["x"];
 Check(!((string)CaptionService.Get(serializer.DeserializeObject(named),"title")).Contains("민수") && !CommentPipeline.WritingQuote("민수가 무료로 제공합니다.",named).Contains("민수"),"name masking also covers full title and new writing evidence input");
 var aliasContext=pipe.AnalyzeContext("다이애나 다이애나",new Dictionary<string,CaptionCue>{{"x",new CaptionCue{Text="다이에나의 보호막 계수가 올랐어요."}}},CancellationToken.None).GetAwaiter().GetResult()["x"];
 bool aliasRejected=false;try{CommentPipeline.ValidateReaction("다이에나 이제 강할 것 같네요",aliasContext);}catch(InvalidDataException){aliasRejected=true;}Check(aliasRejected,"caption spelling variants of an excluded name cannot leak through new writer context");
 var gameContext=pipe.AnalyzeContext("\"드래곤소드\" 소개",new Dictionary<string,CaptionCue>{{"x",new CaptionCue{Text="드래곤 소드의 전투는 자유롭게 캐릭터를 바꿉니다."}}},CancellationToken.None).GetAwaiter().GetResult()["x"];
 Check(CommentPipeline.WritingQuote("드래곤 소드의 전투",gameContext)=="이 게임의 전투","quoted game names and ASR spacing variants are masked as games, not characters");
 var namedGame=pipe.AnalyzeContext("무료 게임 추천",new Dictionary<string,CaptionCue>{{"x",new CaptionCue{Text="페이퍼 릴리라는 제목의 게임도 무료입니다."}}},CancellationToken.None).GetAwaiter().GetResult()["x"];
 Check(CommentPipeline.WritingQuote("페이퍼 릴리라는 제목의 게임",namedGame)=="이 게임이라는 제목의 게임","explicit source game-name markers are masked without breaking the Korean particle");
 Check(CommentPipeline.WritingQuote("페이퍼 릴리는 한글이 없습니다",namedGame)=="이 게임은 한글이 없습니다","name masking preserves subject particles for the neutral game reference");
 bool onlyRejected=false;try{CommentPipeline.ValidateReaction("프롤로그만 무료라니 좋네요",serializer.Serialize(new{caption="프롤로그도 무료이고 본편도 무료입니다."}));}catch(InvalidDataException){onlyRejected=true;}Check(onlyRejected,"only-free restriction cannot be added to source that also supports the main game");
 CommentPipeline.ValidateReaction("하지만 무료로 즐길 수 있는 게 좋네요",serializer.Serialize(new{caption="무료로 즐길 수 있습니다."}));
 Check(context.Contains("꾸미기는 따로 구매"),"caption detail survives without a shared literal title keyword");
 Check(FastComments.HasGrounding("꾸미기는 따로 파는군요. 지갑 조심해야겠네요 ㅋㅋ",context) && !FastComments.HasGrounding("다음 영상도 궁금해요",context),"generic reaction cannot pass as concrete caption connection");
 foreach(string bad in new[]{"캐릭터 잠재력이 어떻게 확장될지 궁금해지네요", "제목의 전환이 독특하네요", "모습이 달라질 것 같네요", "보스를 잡는 게 인상적이네요", "다들 이 조합을 추천하네요"}){
 bool rejected=false;try{CommentPipeline.ValidateReaction(bad,context);}catch(InvalidDataException){rejected=true;}Check(rejected,"reported stiff or invented claim is rejected independently of model verdict");
 }
 string statContext=serializer.Serialize(new{caption="보호막의 체력 계수가 버프를 받았습니다."});
 foreach(string bad in new[]{"보호막 대신 체력 계수가 더해진 거라니 강해졌네요", "보호막이 체력까지 버프라니 좋네요", "보호막이 꽤 체감 되더라고요", "체력 계수가 얼마나 달라지는 건지 궁금하네요", "보호막이 아니라서 당황스럽네요", "보호막 오인했길래 당황스러웠네요", "보호막 버프 먹으니까 든든하네요. 캐릭터 체감 확실하죠"}){
 bool rejected=false;try{CommentPipeline.ValidateReaction(bad,statContext);}catch(InvalidDataException){rejected=true;}Check(rejected,"observed replacement/stat/experience/interview regression rejected");
 }
 CommentPipeline.ValidateReaction("꾸미기는 따로 파는군요. 지갑 조심해야겠네요 ㅋㅋ",context);
 Check(true,"source-grounded casual reaction remains allowed");
 }
 var ranked=new VideoContent{Version=1,VideoId="V0000000002",Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=Enumerable.Range(0,100).Select(i=>new CaptionCue{StartMs=i*1000,Text=i%20==0 ? "보호막 체력 계수가 바뀌어서 보호막이 더 두꺼워집니다." : "안녕하세요. 계속 해보겠습니다."}).ToList()};
 var chosen=CommentService.Evidence(ranked,"보호막 체력 계수 버프");
 Check(chosen.Count==5 && chosen.Values.All(c=>c.Text.Contains("보호막")) && chosen.All(c=>c.Value.StartMs==int.Parse(c.Key.Substring(1))*1000),"title-related actual speech selected across timeline with original cue identity");
 using(var model=new LocalModel("unused")){
 int totalWrites=0;var filtered=new CommentService(model,(body,t)=>{totalWrites++;return Task.FromResult("{\"comments\":[\"다음 영상도 궁금해요\"]}");}).Generate(new Video{Id=content.VideoId,Title="검사용 제목"},content,CancellationToken.None).GetAwaiter().GetResult();
 Check(filtered.QualityFiltered && filtered.Comments.Count==0 && totalWrites==15,"rejected valid-format comments are discarded after bounded retries rather than filled with generic text");
 }
 bool duplicateRejected=false;try{CommentService.ParsePlain(string.Join("\n",new[]{replies[0],replies[0]+" ㅋㅋㅋ",replies[2],replies[3],replies[4]}),evidence,"a",0);}catch(InvalidDataException){duplicateRejected=true;}Check(duplicateRejected,"laughter and punctuation variants cannot bypass duplicate validation");
 var events=new List<string>();var entered=new TaskCompletionSource<int>();var stop=new CancellationTokenSource();
 using(var dual=new DualCommentService((m,v,c,t,r)=>{events.Add("write");return Task.FromResult(new CommentResult{Comments=Enumerable.Range(0,5).Select(i=>new CommentSuggestion()).ToList()});},preparer:async t=>{events.Add("warm");entered.SetResult(0);await Task.Delay(Timeout.Infinite,t);})){var warming=dual.PrepareFirst(stop.Token);entered.Task.GetAwaiter().GetResult();var generation=dual.Generate(new Video(),content,CancellationToken.None);Check(events.SequenceEqual(new[]{"warm"}),"generation does not interleave with active warmup");stop.Cancel();try{warming.GetAwaiter().GetResult();}catch(OperationCanceledException){}Check(generation.GetAwaiter().GetResult().Count==10,"cancelled warmup releases gate for normal generation");}
 return 0;}catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}}
