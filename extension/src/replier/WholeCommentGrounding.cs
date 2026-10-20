using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

namespace ReplierDesktop {
 public sealed class GroundingReview {
  public bool Supported;
  public string Reason;
  public int[] SourceIndexes;
 }
 public sealed class WholeCommentGrounding {
  readonly LocalModel model;
  readonly Func<object,CancellationToken,Task<string>> chat;
  public WholeCommentGrounding(LocalModel runtime,Func<object,CancellationToken,Task<string>> sender=null){model=runtime;chat=sender??runtime.Chat;}

  public static string[] Clauses(string comment){
   // Program-owned coverage: the judge cannot silently omit a sentence after a compliment.
   return Regex.Split(comment??"",@"(?<=[.!?。！？])\s+|(?=\b(?:다만|하지만|근데|그런데|반면|대신)\b)")
    .Select(s=>s.Trim()).Where(s=>s.Length>0&&!Regex.IsMatch(s,@"\A[ㅋㅎ\s\p{P}]+\z")).ToArray();
  }
  public static GroundingReview Parse(string raw,string clause,Video video,KeyValuePair<string,CaptionCue>[] evidence){
   var root=SceneMaterial.Json(raw);var supported=CaptionService.Get(root,"supported");var source=CaptionService.Get(root,"source");
   if(!(supported is bool)||!(source is int))throw new InvalidDataException("댓글 부분별 근거 응답 형식을 확인하지 못했습니다.");
   int index=(int)source;string original=index==-1?video.Title:index>=0&&index<evidence.Length?evidence[index].Value.Text:null;
   string quote=CaptionService.Get(root,"quote") as string;
   bool exact=ContextGuidance.HasQuote(original,quote);
   bool ok=(bool)supported&&exact;
   string label=index==-1?"제목":index>=0&&index<evidence.Length?evidence[index].Key+" · "+CaptionService.Timestamp(evidence[index].Value.StartMs):"미확인 구간";
   return new GroundingReview{Supported=ok,SourceIndexes=ok&&index>=0?new[]{index}:new int[0],Reason="부분 ‘"+clause+"’: "+(ok?"근거 연결 판정 · "+label+" ‘"+quote+"’ · "+(CaptionService.Get(root,"rationale") as string ?? ""):(bool)supported?"선택 구간에서 실제 근거 구절을 확인하지 못함":"제목·자막에서 이 부분의 전제·평가 근거 미확인 · "+(CaptionService.Get(root,"rationale") as string ?? ""))};
  }
  public async Task<GroundingReview> Assess(Video video,KeyValuePair<string,CaptionCue>[] evidence,string comment,CancellationToken token,KeyValuePair<string,CaptionCue>[] wholeContext=null){
   evidence=ContextGuidance.Units(evidence);var clauses=Clauses(comment);if(clauses.Length==0)throw new InvalidDataException("평가할 댓글 내용이 없습니다.");
   var references=await new ReferenceGrounding(model,chat).Assess(video,evidence,comment,token).ConfigureAwait(false);
   if(!references.Supported)return new GroundingReview{Supported=false,Reason="댓글 전체 근거 검사: 원문에 없는 대상 참조 → 추천 제외\n"+references.Reason};
   var json=new JavaScriptSerializer();var reviews=new List<GroundingReview>();

   foreach(string clause in clauses){
    token.ThrowIfCancellationRequested();
   var schema=new{type="object",properties=new{evaluated_comment=new{type="string",@enum=new[]{clause}},premise=new{type="string",maxLength=100},source=new{type="integer",minimum=-1,maximum=evidence.Length-1},supported=new{type="boolean"},context_clear=new{type="boolean"},added_claim=new{type="boolean"},asserts_event_result=new{type="boolean"},source_kind=new{type="string",@enum=new[]{"actual_event","conditional_or_rule","unclear","no_event"}},comment_outcome=new{type="string",@enum=new[]{"none","success","failure"}},context_outcome=new{type="string",@enum=new[]{"undetermined","success","failure"}},rationale=new{type="string",maxLength=160}},required=new[]{"evaluated_comment","premise","source","supported","context_clear","added_claim","asserts_event_result","source_kind","comment_outcome","context_outcome","rationale"},additionalProperties=false};
    string raw=await chat(new{model=model.Name,stream=false,think=false,format=schema,keep_alive="30s",options=new{temperature=0.0,num_ctx=8192,num_predict=650},messages=new[]{
     new{role="system",content=ContextGuidance.Reaction+"평가 대상은 마지막 user 입력의 candidate_comment입니다. 영상 요약을 쓰는 일이 아닙니다. evaluated_comment에 그 댓글을 그대로 복사하세요. 그 댓글이 실제로 말하는 사실 전제만 premise에 쓰세요. 댓글에 없는 주어·사건·평가를 넣지 않습니다. 그 전제를 확인할 실제 구절의 index만 source에 씁니다(-1은 제목). 원문 구절은 프로그램이 번호에 연결하므로 새로 쓰지 않습니다. 그 구절이 전제의 대상·주체·사건·조건·시점을 뒷받침하면 supported=true, 다른 내용을 보태거나 바꾸면 false입니다. 주제 단어가 같다는 것만으로 충분하지 않습니다. 원문을 설명하려고 댓글에 없는 주장을 끼워 넣지 마세요. 감상 자체의 옳고 그름, 영상의 핵심과 얼마나 가까운지는 이 단계의 탈락 기준이 아닙니다. 영상과의 관계는 다음 단계에서 따로 평가합니다. whole_context는 주체·조건·결과를 혼동하지 않도록 읽는 주변 원문이며 source 번호의 근거를 대신하지 않습니다. comment_outcome은 댓글이 현재 영상 속 대상의 성공·완료·승리(success) 또는 실패·패배·못 끝냄(failure)을 말하는지, 그런 결과 주장이 없는지(none)입니다. 못 깬 것 같아처럼 추측형이어도 현재 대상의 실패를 추정하면 failure입니다. 내 감상·기대나 나였으면 어렵겠다는 반응은 영상 속 결과 주장이 아니므로 none입니다. context_outcome은 같은 대상·같은 구간에 대해 앞뒤 원문에서 확인된 결과입니다. 예: 제한 시간이 있어 빨리 해야 한다고 한 뒤 이겼다고 확인했다면 context_outcome=success이고, 못 깬 것 같다는 댓글은 comment_outcome=failure여서 통과하지 않습니다. 제목에서 실패한 다른 사람과 영상에서 성공한 사람을 혼동하지 마세요. 결과를 알 수 없으면 undetermined입니다. asserts_event_result는 댓글이 성공·실패·죽음·파손·완료 등 사건이 실제 발생했다고 말하는지입니다. 질문형으로 왜 죽었냐고 해도 실제 죽음이 전제이므로 true입니다. source_kind는 실제 근거 문장이 일어난 사건(actual_event)인지 조건·가능성·설명(conditional_or_rule)인지 구분합니다. 맞으면 죽는다는 말은 실제 맞아 죽었다는 뜻이 아닙니다. 댓글이 사건 발생을 주장하면 원문에도 같은 실제 발생이 확인되어야 합니다. context_clear는 앞뒤 원문을 함께 읽었을 때 대상과 행동의 뜻이 명확한지입니다. 자동 자막의 깨진 단어 조각만 맞거나 대상·행동의 뜻이 모호하면 false입니다. added_claim은 댓글이 원문에 없는 성공/실패, 공략의 핵심, 원인·결과, 횟수·수치, 대상을 추가했는지입니다. 예: 재료가 남았다는 대사만으로 남은 재료를 찾는 것이 성공 비결이라고 하면 added_claim=true입니다. 질문형·감탄형이어도 담긴 사실 전제는 같은 기준으로 봅니다. 기대·기쁨 같은 감정 자체는 추가 사실이 아닙니다. 한 줄의 같은 단어가 아니라 해당 구간과 주변 맥락이 댓글 전체 전제를 뒷받침해야 합니다. rationale에 각 사실 전제가 원문에서 어떻게 확인되는지 또는 무엇이 불명확한지 적습니다."},
     new{role="user",content="{\"title\":\"연기 끝에 개봉 확정\",\"transcript\":[{\"index\":0,\"text\":\"오랫동안 기다렸는데 개봉일이 다음 달로 확정됐습니다.\"}],\"candidate_comment\":\"드디어 영화 볼 수 있다니 기쁘네요\"}"},new{role="assistant",content="{\"evaluated_comment\":\"드디어 영화 볼 수 있다니 기쁘네요\",\"premise\":\"영화 개봉일이 확정됐다\",\"quote\":\"개봉일이 다음 달로 확정됐습니다.\",\"source\":0,\"supported\":true,\"context_clear\":true,\"added_claim\":false,\"asserts_event_result\":false,\"source_kind\":\"actual_event\",\"comment_outcome\":\"none\",\"context_outcome\":\"undetermined\",\"rationale\":\"확정 소식에 대한 시청자의 기쁨이며 이미 개봉했다는 뜻은 아님\"}"},
     new{role="user",content="{\"title\":\"색상 구경\",\"transcript\":[{\"index\":0,\"text\":\"파란색과 초록색 두 가지입니다.\"}],\"candidate_comment\":\"무게가 가벼워서 좋네요\"}"},new{role="assistant",content="{\"evaluated_comment\":\"무게가 가벼워서 좋네요\",\"premise\":\"무게가 가볍다\",\"quote\":\"\",\"source\":0,\"supported\":false,\"context_clear\":true,\"added_claim\":true,\"asserts_event_result\":false,\"source_kind\":\"no_event\",\"comment_outcome\":\"none\",\"context_outcome\":\"undetermined\",\"rationale\":\"색상 설명만 있어 무게를 알 수 없음\"}"},
     new{role="user",content=json.Serialize(new{title=video.Title,transcript=evidence.Select((e,i)=>new{index=i,text=e.Value.Text}).ToArray(),candidate_comment=clause,whole_context=(wholeContext??evidence).Select(e=>e.Value.Text).ToArray()})}}},token).ConfigureAwait(false);
    if((CaptionService.Get(SceneMaterial.Json(raw),"evaluated_comment") as string)!=clause)throw new InvalidDataException("근거 검사 대상 댓글이 일치하지 않습니다.");
    var parsed=SceneMaterial.Json(raw);var claimed=CaptionService.Get(parsed,"comment_outcome") as string;var observed=CaptionService.Get(parsed,"context_outcome") as string;if(!new[]{"none","success","failure"}.Contains(claimed)||!new[]{"undetermined","success","failure"}.Contains(observed))throw new InvalidDataException("댓글과 실제 결과의 일치 여부를 확인하지 못했습니다.");var eventResult=CaptionService.Get(parsed,"asserts_event_result");var sourceKind=CaptionService.Get(parsed,"source_kind") as string;if(!(eventResult is bool)||!new[]{"actual_event","conditional_or_rule","unclear","no_event"}.Contains(sourceKind))throw new InvalidDataException("실제 발생과 조건 설명을 구분하지 못했습니다.");
    var clear=CaptionService.Get(parsed,"context_clear");var added=CaptionService.Get(parsed,"added_claim");if(!(clear is bool)||!(added is bool))throw new InvalidDataException("근거의 명확성과 추가 사실 여부를 확인하지 못했습니다.");
    var source=CaptionService.Get(parsed,"source");if(!(source is int)||(int)source < -1||(int)source>=evidence.Length)throw new InvalidDataException("실제 구절 번호가 필요합니다.");
    string original=(int)source==-1?video.Title:evidence[(int)source].Value.Text;
    reviews.Add(Parse(json.Serialize(new{supported=object.Equals(CaptionService.Get(parsed,"supported"),true)&&(bool)clear&&!(bool)added&&(!(bool)eventResult||sourceKind=="actual_event")&&(claimed=="none"||claimed==observed),source=(int)source,quote=original,rationale=Convert.ToString(CaptionService.Get(parsed,"rationale"))+" · 원문 의미 명확: "+clear+" · 추가 사실: "+added+" · 사건 발생 주장: "+eventResult+" · 원문 유형: "+sourceKind+" · 댓글 결과: "+claimed+" · 같은 대상의 원문 결과: "+observed}),clause,video,evidence));
   }
   token.ThrowIfCancellationRequested();
   return new GroundingReview{Supported=reviews.All(r=>r.Supported),SourceIndexes=reviews.Where(r=>r.Supported).SelectMany(r=>r.SourceIndexes??new int[0]).Distinct().ToArray(),Reason="댓글 전체 근거 검사: "+(reviews.All(r=>r.Supported)?"모든 부분 확인":"일부 근거 미확인 → 추천 제외")+"\n"+references.Reason+"\n"+string.Join("\n",reviews.Select(r=>r.Reason))};
  }
 }
}
