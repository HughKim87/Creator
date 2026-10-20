using System;using System.Collections.Generic;using System.Linq;using System.Text.RegularExpressions;using System.Threading;using System.Threading.Tasks;using ReplierDesktop;
namespace ReplierDesktop {
 public sealed class ScenePolisher {
  readonly LocalModel model;readonly Func<object,CancellationToken,Task<string>> chat;
  public ScenePolisher(LocalModel m,Func<object,CancellationToken,Task<string>> sender=null){model=m;chat=sender??m.Chat;}
  public async Task Apply(IList<CommentSuggestion> comments,CancellationToken token){
   var json=new System.Web.Script.Serialization.JavaScriptSerializer();var pending=new List<Tuple<CommentSuggestion,string>>();
   foreach(var row in comments.Where(c=>!c.SurfaceReviewed)){
    var schema=new{type="object",properties=new{comments=new{type="array",minItems=1,maxItems=1,items=new{type="string",maxLength=75}}},required=new[]{"comments"},additionalProperties=false};
    string raw=await chat(new{model=model.Name,stream=false,think=false,format=schema,keep_alive="30s",options=new{temperature=0.0,num_ctx=8192,num_predict=170},messages=new[]{
     new{role="system",content="한국어 댓글 한 문장의 문법과 말투를 최소한으로 다듬습니다. 원래 의미와 감정, 시청자 시점을 유지하면서 조사·어미·어색한 단어 연결만 자연스럽게 고치세요. 일상 댓글의 짧은 구어체를 유지하세요. ~네, ~임, ㅋㅋ 같은 자연스러운 말끝을 완전한 존댓말 감상문으로 바꾸지 마세요. 칭찬이나 감탄을 추가하지 마세요. 설명이나 사건을 덧붙이거나 문장을 길게 만들지 마세요. 이미 자연스러우면 그대로 두세요. 고친 문장 하나를 comments JSON으로 반환하세요."},
     new{role="user",content=json.Serialize(new{text=row.Text})}}},token).ConfigureAwait(false);
    string text=Regex.Replace(FastComments.Drafts(raw,1)[0],@"\s+"," ").Trim();
    // Mechanical checks only; both independent judges reassess the edited meaning next.
    if(text.Length<8||text.Length>100||!Regex.IsMatch(text,@"[가-힣]")||Regex.IsMatch(text,@"[\u3400-\u9fff]|https?://|www\."))text=row.Text;
    if(SceneMaterial.IsScene(row.Material)&&CommentPipeline.WritingQuote(text,row.Material)!=text)text=row.Text;
    pending.Add(Tuple.Create(row,text));
   }
   token.ThrowIfCancellationRequested();foreach(var change in pending){var row=change.Item1;row.DraftText=row.Text;row.Text=change.Item2;row.SurfaceReviewed=true;row.FitEligible=false;row.FitScore=row.GemmaFitScore=row.QwenFitScore=null;row.FitContextKey=null;row.FitReason=null;row.TiePreference=0;row.TieReason=null;}
  }
 }
}
