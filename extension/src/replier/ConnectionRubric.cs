using System;using System.Collections.Generic;using System.IO;using System.Linq;using System.Web.Script.Serialization;
namespace ReplierDesktop {
 public static class ConnectionRubric {
  // A single semantic decision owns topic/link/reaction; the model never emits independent numbers.
  public static readonly string[] Levels={"specific_reaction","direct_reaction","partial_reaction","generic_reaction","retelling","unrelated","conflict"};
  public static FitAssessment ParseRelation(string raw,CommentSuggestion comment,KeyValuePair<string,CaptionCue>[] evidence,string voice){
   var root=SceneMaterial.Json(raw);string role=CaptionService.Get(root,"source_role") as string;var conflicts=CaptionService.Get(root,"conflicts");
   if(!new[]{"central_event","supporting_example","background","no_target"}.Contains(role)||!(conflicts is bool))throw new InvalidDataException("원문 역할·모순 여부를 확인하지 못했습니다.");
   // Voice and full factual coverage already have separate owners. Do not ask another judge
   // whether personal happiness counts as a reaction or demand a quotation in the comment.
   string level=(bool)conflicts?"conflict":voice=="retelling"?"retelling":role=="no_target"?"generic_reaction":role=="central_event"?"direct_reaction":"partial_reaction";
   var selected=CaptionService.Get(root,"evidence");if(!(selected is int)||(int)selected<0||(int)selected>=evidence.Length)throw new InvalidDataException("실제 구절 번호가 필요합니다.");
   var adapted=new JavaScriptSerializer().Serialize(new{evaluated_comment=CaptionService.Get(root,"evaluated_comment"),focus=CaptionService.Get(root,"focus"),explanation=CaptionService.Get(root,"explanation"),quote=evidence[(int)selected].Value.Text,connection=level,evidence=CaptionService.Get(root,"evidence")});
   var rating=ParseContext(adapted,comment,evidence,voice);rating.Reason="원문 역할: "+role+"\n"+rating.Reason;return rating;
  }
  public static FitAssessment ParseContext(string raw,CommentSuggestion comment,KeyValuePair<string,CaptionCue>[] evidence,string voice){
   var root=SceneMaterial.Json(raw);if((CaptionService.Get(root,"evaluated_comment") as string)!=comment.Text)throw new InvalidDataException("문맥 평가 대상 댓글이 일치하지 않습니다.");string focus=CaptionService.Get(root,"focus") as string,why=CaptionService.Get(root,"explanation") as string,quote=CaptionService.Get(root,"quote") as string;var source=CaptionService.Get(root,"evidence");
   if(string.IsNullOrWhiteSpace(focus)||string.IsNullOrWhiteSpace(why)||!(source is int)||(int)source<0||(int)source>=evidence.Length||!ContextGuidance.HasQuote(evidence[(int)source].Value.Text,quote))throw new InvalidDataException("핵심 맥락·판단 이유·선택 구간의 실제 인용을 확인해야 합니다.");
   var rating=Parse(new JavaScriptSerializer().Serialize(new{connection=CaptionService.Get(root,"connection"),evidence=(int)source}),comment,evidence,voice);
   rating.Reason="영상 중심 화제: "+focus+"\n반응과 맥락: "+why+"\n대조한 실제 구절: ‘"+quote+"’\n"+rating.Reason;return rating;
  }
  public static FitAssessment Parse(string raw,CommentSuggestion comment,KeyValuePair<string,CaptionCue>[] evidence,string voice){
   var root=SceneMaterial.Json(raw) as Dictionary<string,object>;if(root==null||root.Count!=2||!root.ContainsKey("connection")||!root.ContainsKey("evidence"))throw new InvalidDataException("관계 판정과 실제 근거 번호만 반환해야 합니다. 독립적인 숫자 점수는 사용하지 않습니다.");
   string level=root["connection"] as string;var source=root["evidence"];
   if(!Levels.Contains(level)||!(source is int)||(int)source<0||(int)source>=evidence.Length)throw new InvalidDataException("관계 판정·실제 근거 번호를 확인하지 못했습니다.");
   if(!new[]{"viewer","retelling","awkward"}.Contains(voice))throw new InvalidDataException("말투 판정을 확인하지 못했습니다.");
   int topic,link;string label;
   switch(level){
    case "specific_reaction":topic=20;link=15;label="구체적 상황에 대한 반응";break;
    case "direct_reaction":topic=18;link=12;label="실제 대상·특징에 대한 직접 감상";break;
    case "partial_reaction":topic=14;link=7;label="부분적으로 연결된 반응";break;
    case "generic_reaction":topic=8;link=2;label="구체적 연결이 없는 일반 감상";break;
    case "retelling":topic=14;link=0;label="설명·대사 반복";break;
    case "unrelated":topic=0;link=0;label="주제 무관";break;
    default:topic=0;link=0;label="원문과 모순";break;
   }
   int tone=voice=="viewer"?10:voice=="retelling"?5:0;
   bool reaction=level=="specific_reaction"||level=="direct_reaction"||level=="partial_reaction";
   bool eligible=reaction&&voice=="viewer";
   int care=level=="conflict"||level=="unrelated"?0:5;
   var cue=evidence[(int)source];
   return new FitAssessment{Id=0,Eligible=eligible,Score=eligible?topic+tone+care+link:0,Topic=topic,Tone=tone,Care=care,Link=link,
    Reason="댓글 ‘"+comment.Text+"’ 기준\n관계 판정: "+label+"\n기준표 계산: 주제 "+topic+"/20 · 말투 "+tone+"/10 · 추측 억제 "+care+"/5 · 상황 연결 "+link+"/15\n말투 점수는 별도 말투 판정, 추측 억제는 선행 전체 근거 통과 결과를 사용합니다.\n참고 원문:\n"+cue.Key+" · "+CaptionService.Timestamp(cue.Value.StartMs)+" · "+cue.Value.Text+(eligible?"":"\n추천 수준 미달")};
  }
 }
}
